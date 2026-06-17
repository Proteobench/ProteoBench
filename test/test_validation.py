"""
Unit and lightweight integration tests for the submission-validation layer
(:mod:`proteobench.validation`).
"""

import io
import os
import zipfile
from types import SimpleNamespace

import pandas as pd
import pytest

from proteobench.io.parsing.load_input import load_input_file
from proteobench.io.parsing.convert_to_intermediate import ParseSettingsBuilder
from proteobench.validation import (
    Check,
    FastaReference,
    ModuleValidationConfig,
    Severity,
    SubmissionValidationError,
    ValidationContext,
    ValidationProfile,
    ValidationReport,
    available_profiles,
    get_profile,
    register_profile,
    unregister_profile,
    validate_submission,
)
from proteobench.validation.checks import (
    check_charge_range,
    check_enzyme,
    check_fdr_psm,
    check_mass_tolerances,
    check_max_modifications,
    check_modifications,
    check_peptide_length,
    check_protein_ids,
    check_run_consistency,
)
from proteobench.validation.checks import _parse_tolerance
from proteobench.validation.config import _resolve_profile
from proteobench.validation.fasta import parse_fasta_header
from proteobench.validation.protein_ids import (
    extract_identifiers,
    is_decoy_or_contaminant,
    split_protein_groups,
)

HERE = os.path.dirname(__file__)
FASTA_FIXTURE = os.path.join(HERE, "data", "validation", "ProteoBench_validation_reference.fasta")

QEXACTIVE_DATA_DIR = os.path.join(HERE, "data", "quant", "quant_lfq_ion_DDA_QExactive")
QEXACTIVE_SETTINGS_DIR = os.path.abspath(
    os.path.join(
        HERE, "..", "proteobench", "io", "parsing", "io_parse_settings", "Quant", "lfq", "DDA", "ion", "QExactive"
    )
)
QEXACTIVE_MODULE_ID = "quant_lfq_DDA_ion_QExactive"


def make_params(**overrides):
    """Build a parameters stub with sensible defaults, overridable per test."""
    defaults = dict(
        software_name="MaxQuant",
        software_version="2.5.1.0",
        search_engine="Andromeda",
        min_precursor_charge=2,
        max_precursor_charge=4,
        min_peptide_length=6,
        max_peptide_length=30,
        enzyme="Trypsin",
        semi_enzymatic=False,
        allowed_miscleavages=2,
        fixed_mods="Carbamidomethyl (C)",
        variable_mods="Oxidation (M),Acetyl (Protein N-term)",
        max_mods=3,
        precursor_mass_tolerance="[-20.0 ppm, 20.0 ppm]",
        fragment_mass_tolerance="[-20.0 ppm, 20.0 ppm]",
        ident_fdr_psm=0.01,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_standard_df(**overrides):
    """Build a small valid standardized result DataFrame."""
    data = dict(
        Proteins=[
            "sp|P10001|AAA_HUMAN",
            "tr|P10002|BBB_YEAST",
            "P10003",
            "sp|P49327|FAS_HUMAN",
        ],
        Sequence=["PEPTIDEK", "ELVISLIVESR", "SAMPLERPEPK", "VFRRDTHK"],
        Charge=[2, 3, 2, 2],
        proforma=["PEPTIDEK", "ELVISLIVESR", "SAMPLERPEPK", "VFR[Oxidation]RDTHK"],
    )
    data["precursor ion"] = [f"{s}/{c}" for s, c in zip(data["proforma"], data["Charge"])]
    df = pd.DataFrame(data)
    for key, value in overrides.items():
        df[key] = value
    return df


@pytest.fixture
def reference_fasta():
    return FastaReference.from_path(FASTA_FIXTURE)


# --------------------------------------------------------------------------- #
# protein-id helpers and FASTA parsing
# --------------------------------------------------------------------------- #


def test_split_protein_groups_handles_separators():
    assert split_protein_groups("sp|P1|A_HUMAN;sp|P2|B_YEAST") == ["sp|P1|A_HUMAN", "sp|P2|B_YEAST"]
    assert split_protein_groups("sp|P1|A_HUMAN,sp|P2|B_YEAST") == ["sp|P1|A_HUMAN", "sp|P2|B_YEAST"]
    assert split_protein_groups("") == []
    assert split_protein_groups(None) == []


def test_extract_identifiers_uniprot_bare_and_isoform():
    assert extract_identifiers("sp|P49327|FAS_HUMAN") >= {"P49327", "FAS_HUMAN"}
    assert extract_identifiers("tr|A0A024|X_HUMAN") >= {"A0A024", "X_HUMAN"}
    assert extract_identifiers("P12345") >= {"P12345"}
    # isoform base accession is added
    assert "P49327" in extract_identifiers("P49327-2")


def test_is_decoy_or_contaminant():
    assert is_decoy_or_contaminant("Cont_keratin", contaminant_flag="Cont_")
    assert is_decoy_or_contaminant("rev_sp|P1|A_HUMAN", decoy_prefixes=("rev_",))
    assert not is_decoy_or_contaminant("sp|P1|A_HUMAN", contaminant_flag="Cont_", decoy_prefixes=("rev_",))


def test_parse_fasta_header_forms():
    assert parse_fasta_header(">sp|P49327|FAS_HUMAN Fatty acid synthase") >= {"P49327", "FAS_HUMAN"}
    assert parse_fasta_header(">P00330 ADH1") >= {"P00330"}
    assert parse_fasta_header(">") == set()


def test_fasta_reference_from_path(reference_fasta):
    assert len(reference_fasta) > 0
    assert reference_fasta.contains("P49327")
    assert reference_fasta.contains("FAS_HUMAN")
    assert reference_fasta.contains("p49327")  # case-insensitive
    assert not reference_fasta.contains("P99999")
    assert reference_fasta.contains_any(extract_identifiers("sp|P49327|FAS_HUMAN"))


def test_fasta_reference_from_zip_bytes():
    text = ">sp|P10001|AAA_HUMAN x\nMKWV\n>P10003\nMVLS\n"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("reference.fasta", text)
    ref = FastaReference.from_bytes(buffer.getvalue(), source_name="reference.zip")
    assert ref.contains("P10001")
    assert ref.contains("P10003")


# --------------------------------------------------------------------------- #
# protein-id check
# --------------------------------------------------------------------------- #


def test_protein_ids_all_present_passes(reference_fasta):
    df = make_standard_df()
    issues = check_protein_ids(df, reference_fasta, ModuleValidationConfig())
    assert not any(i.severity == Severity.ERROR for i in issues)


def test_protein_ids_missing_reports_error(reference_fasta):
    df = make_standard_df()
    df.loc[0, "Proteins"] = "sp|P99999|MISSING_HUMAN"
    issues = check_protein_ids(df, reference_fasta, ModuleValidationConfig())
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert len(errors) == 1
    assert errors[0].code == "protein_not_in_fasta"
    assert "sp|P99999|MISSING_HUMAN" in errors[0].examples
    assert errors[0].observed["n_missing"] == 1


def test_protein_groups_partial_membership(reference_fasta):
    # Group with one known + one unknown -> unknown reported, known not.
    df = make_standard_df()
    df.loc[0, "Proteins"] = "sp|P49327|FAS_HUMAN;sp|P98765|GHOST_HUMAN"
    issues = check_protein_ids(df, reference_fasta, ModuleValidationConfig())
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert len(errors) == 1
    assert errors[0].examples == ["sp|P98765|GHOST_HUMAN"]


def test_protein_ids_decoy_and_contaminant_ignored(reference_fasta):
    df = make_standard_df()
    df.loc[0, "Proteins"] = "Cont_keratin"
    df.loc[1, "Proteins"] = "rev_sp|P77777|DECOY_HUMAN"
    config = ModuleValidationConfig(contaminant_flag="Cont_")
    issues = check_protein_ids(df, reference_fasta, config)
    assert not any(i.severity == Severity.ERROR for i in issues)


# --------------------------------------------------------------------------- #
# charge / peptide-length checks
# --------------------------------------------------------------------------- #


def test_charge_out_of_range_errors():
    df = make_standard_df(Charge=[2, 3, 9, 2])
    issues = check_charge_range(df, make_params(), ModuleValidationConfig())
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert len(errors) == 1
    assert errors[0].code == "charge_out_of_range"
    assert 9 in errors[0].observed


def test_charge_within_range_passes():
    issues = check_charge_range(make_standard_df(), make_params(), ModuleValidationConfig())
    assert not any(i.severity == Severity.ERROR for i in issues)


def test_charge_missing_param_warns_not_errors():
    params = make_params(min_precursor_charge=None, max_precursor_charge="None")
    issues = check_charge_range(make_standard_df(Charge=[9, 9, 9, 9]), params, ModuleValidationConfig())
    assert not any(i.severity == Severity.ERROR for i in issues)
    assert any(i.code == "charge_range_not_parsed" and i.severity == Severity.WARNING for i in issues)


def test_peptide_length_out_of_range_errors():
    df = make_standard_df(Sequence=["AAA", "A" * 40, "PEPTIDEK", "ELVISLIVESR"])
    issues = check_peptide_length(df, make_params(), ModuleValidationConfig())
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert len(errors) == 1
    assert errors[0].code == "peptide_length_out_of_range"
    assert "AAA" in errors[0].examples


def test_peptide_length_missing_param_warns():
    params = make_params(min_peptide_length=None, max_peptide_length=None)
    issues = check_peptide_length(make_standard_df(), params, ModuleValidationConfig())
    assert not any(i.severity == Severity.ERROR for i in issues)
    assert any(i.code == "peptide_length_not_parsed" and i.severity == Severity.WARNING for i in issues)


# --------------------------------------------------------------------------- #
# enzyme / modifications / run consistency
# --------------------------------------------------------------------------- #


def test_enzyme_missed_cleavages_warning_only():
    df = make_standard_df(Sequence=["PEPKTIDKEKR", "ELVISLIVESR", "SAMPLEK", "VFRDTHK"])
    params = make_params(enzyme="Trypsin", allowed_miscleavages=0)
    issues = check_enzyme(df, params, ModuleValidationConfig())
    assert not any(i.severity == Severity.ERROR for i in issues)
    assert any(i.code == "missed_cleavages_exceeded" and i.severity == Severity.WARNING for i in issues)


def test_enzyme_chymotrypsin_is_supported():
    # Chymotrypsin is now a supported enzyme, so it is NOT skipped as unsupported.
    issues = check_enzyme(make_standard_df(), make_params(enzyme="Chymotrypsin"), ModuleValidationConfig())
    assert not any(i.code == "enzyme_check_unsupported" for i in issues)


def test_enzyme_missing_warns():
    issues = check_enzyme(make_standard_df(), make_params(enzyme=None), ModuleValidationConfig())
    assert any(i.code == "enzyme_not_parsed" and i.severity == Severity.WARNING for i in issues)


def test_modifications_missing_param_warns():
    params = make_params(fixed_mods=None, variable_mods="None")
    issues = check_modifications(make_standard_df(), params, ModuleValidationConfig())
    assert not any(i.severity == Severity.ERROR for i in issues)
    assert any(i.code == "modifications_not_parsed" and i.severity == Severity.WARNING for i in issues)


def test_modifications_declared_pass():
    issues = check_modifications(make_standard_df(), make_params(), ModuleValidationConfig())
    # 'Oxidation' is declared in the default variable_mods -> no mismatch warning.
    assert not any(i.code == "modification_not_declared" for i in issues)


def test_modifications_undeclared_warns():
    df = make_standard_df()
    df["proforma"] = ["PEP[Phospho]TIDEK", "ELVISLIVESR", "SAMPLERPEPK", "VFRDTHK"]
    issues = check_modifications(df, make_params(), ModuleValidationConfig())
    assert any(i.code == "modification_not_declared" and i.severity == Severity.WARNING for i in issues)


def test_run_consistency_software_mismatch_error():
    params = make_params(software_name="FragPipe")
    issues = check_run_consistency(make_standard_df(), params, "MaxQuant", ModuleValidationConfig())
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert any(i.code == "software_mismatch" for i in errors)


def test_run_consistency_match_no_error():
    issues = check_run_consistency(make_standard_df(), make_params(), "MaxQuant", ModuleValidationConfig())
    assert not any(i.severity == Severity.ERROR for i in issues)


# --------------------------------------------------------------------------- #
# enzyme: multiple proteolytic enzymes
# --------------------------------------------------------------------------- #


def test_enzyme_trypsin_proline_rule():
    # "PEPKPTIDER": K at index 3 is followed by P -> not a missed cleavage for Trypsin,
    # but IS one for Trypsin/P.
    df = make_standard_df(Sequence=["PEPKPTIDER", "PEPKPTIDER", "PEPKPTIDER", "PEPKPTIDER"])
    trypsin = check_enzyme(df, make_params(enzyme="Trypsin", allowed_miscleavages=0), ModuleValidationConfig())
    assert not any(i.code == "missed_cleavages_exceeded" for i in trypsin)
    trypsin_p = check_enzyme(df, make_params(enzyme="Trypsin/P", allowed_miscleavages=0), ModuleValidationConfig())
    assert any(i.code == "missed_cleavages_exceeded" for i in trypsin_p)


def test_enzyme_lysc_supported():
    # Lys-C cleaves after K only. "PEPKTIDER" has one internal K -> 1 missed cleavage.
    df = make_standard_df(Sequence=["PEPKTIDER", "SAMPLEK", "PEPTIDEK", "ELVISK"])
    issues = check_enzyme(df, make_params(enzyme="Lys-C", allowed_miscleavages=0), ModuleValidationConfig())
    assert any(i.code == "missed_cleavages_exceeded" and i.severity == Severity.WARNING for i in issues)


def test_enzyme_gluc_supported():
    # Glu-C cleaves after D/E. "PEPDTIDEK" has 4 internal D/E residues
    # (E1, D3, D6, E7; the C-terminal K is not a cleavage site) -> 4 missed cleavages.
    df = make_standard_df(Sequence=["PEPDTIDEK", "SAMPLEE", "PEPTIDE", "AAAAD"])
    issues = check_enzyme(df, make_params(enzyme="Glu-C", allowed_miscleavages=0), ModuleValidationConfig())
    exceeded = [i for i in issues if i.code == "missed_cleavages_exceeded"]
    assert exceeded
    assert any("PEPDTIDEK (4 MC)" in e for e in exceeded[0].examples)


def test_enzyme_aspn_skipped_as_info():
    # Asp-N is an N-terminal cleaver; the heuristic does not apply.
    issues = check_enzyme(make_standard_df(), make_params(enzyme="Asp-N"), ModuleValidationConfig())
    assert any(i.code == "enzyme_check_unsupported" and i.severity == Severity.INFO for i in issues)


def test_enzyme_unknown_skipped_as_info():
    issues = check_enzyme(make_standard_df(), make_params(enzyme="ProteinaseK"), ModuleValidationConfig())
    assert any(i.code == "enzyme_check_unsupported" and i.severity == Severity.INFO for i in issues)


# --------------------------------------------------------------------------- #
# maximum number of modifications
# --------------------------------------------------------------------------- #


def test_max_modifications_exceeded_warns():
    df = make_standard_df()
    df["proforma"] = [
        "PEP[Acetyl]T[Oxidation]IDE[Phospho]K",  # 3 mods
        "ELVISLIVESR",  # 0
        "SAM[Oxidation]PLERPEPK",  # 1
        "VFR[Oxidation]RDTHK",  # 1
    ]
    issues = check_max_modifications(df, make_params(max_mods=2), ModuleValidationConfig())
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    assert any(i.code == "max_modifications_exceeded" for i in warnings)
    assert any("3 mods" in str(e) for i in warnings for e in i.examples)


def test_max_modifications_within_limit_passes():
    issues = check_max_modifications(make_standard_df(), make_params(max_mods=3), ModuleValidationConfig())
    assert not any(i.code == "max_modifications_exceeded" for i in issues)


def test_max_modifications_missing_param_warns():
    issues = check_max_modifications(make_standard_df(), make_params(max_mods=None), ModuleValidationConfig())
    assert not any(i.severity == Severity.ERROR for i in issues)
    assert any(i.code == "max_mods_not_parsed" and i.severity == Severity.WARNING for i in issues)


# --------------------------------------------------------------------------- #
# precursor / fragment mass tolerances
# --------------------------------------------------------------------------- #


def test_mass_tolerances_valid_passes():
    issues = check_mass_tolerances(make_standard_df(), make_params(), ModuleValidationConfig())
    assert issues == []


def test_mass_tolerance_non_positive_warns():
    params = make_params(precursor_mass_tolerance="[0.0 ppm, 0.0 ppm]")
    issues = check_mass_tolerances(make_standard_df(), params, ModuleValidationConfig())
    assert any(i.code == "precursor_mass_tolerance_non_positive" and i.severity == Severity.WARNING for i in issues)


def test_mass_tolerance_ceilings_default_to_none():
    # The plausibility ceilings have no float/int default; they default to None.
    config = ModuleValidationConfig()
    assert config.max_plausible_ppm is None
    assert config.max_plausible_dalton is None


def test_mass_tolerance_implausible_skipped_without_ceiling():
    # With no ceiling configured (default), the implausible-value sub-check is skipped.
    params = make_params(fragment_mass_tolerance="[-5000.0 ppm, 5000.0 ppm]")
    issues = check_mass_tolerances(make_standard_df(), params, ModuleValidationConfig())
    assert not any(i.code == "fragment_mass_tolerance_implausible" for i in issues)


def test_mass_tolerance_implausible_warns():
    params = make_params(fragment_mass_tolerance="[-5000.0 ppm, 5000.0 ppm]")
    config = ModuleValidationConfig(max_plausible_ppm=1000.0, max_plausible_dalton=10.0)
    issues = check_mass_tolerances(make_standard_df(), params, config)
    assert any(i.code == "fragment_mass_tolerance_implausible" for i in issues)


def test_mass_tolerance_missing_warns():
    params = make_params(precursor_mass_tolerance=None, fragment_mass_tolerance="None")
    issues = check_mass_tolerances(make_standard_df(), params, ModuleValidationConfig())
    codes = {i.code for i in issues}
    assert "precursor_mass_tolerance_not_parsed" in codes
    assert "fragment_mass_tolerance_not_parsed" in codes
    assert not any(i.severity == Severity.ERROR for i in issues)


def test_mass_tolerance_dalton_units():
    config = ModuleValidationConfig(max_plausible_ppm=1000.0, max_plausible_dalton=10.0)
    # Plausible Dalton tolerance: no issue.
    ok = check_mass_tolerances(make_standard_df(), make_params(fragment_mass_tolerance="[-0.5 Da, 0.5 Da]"), config)
    assert not any(i.code == "fragment_mass_tolerance_implausible" for i in ok)
    # Implausible Dalton tolerance: warns.
    bad = check_mass_tolerances(make_standard_df(), make_params(fragment_mass_tolerance="[-50.0 Da, 50.0 Da]"), config)
    assert any(i.code == "fragment_mass_tolerance_implausible" for i in bad)


def test_mass_tolerance_mmu_units():
    config = ModuleValidationConfig(max_plausible_ppm=1000.0, max_plausible_dalton=10.0)
    # 5000 mmu = 5 Da: plausible (ceiling is 10000 mmu).
    ok = check_mass_tolerances(make_standard_df(), make_params(fragment_mass_tolerance="[-5000 mmu, 5000 mmu]"), config)
    assert not any(i.code == "fragment_mass_tolerance_implausible" for i in ok)
    # 50000 mmu = 50 Da: implausible.
    bad = check_mass_tolerances(
        make_standard_df(), make_params(fragment_mass_tolerance="[-50000 mmu, 50000 mmu]"), config
    )
    assert any(i.code == "fragment_mass_tolerance_implausible" for i in bad)


def test_mass_tolerance_scientific_notation():
    # "2e-3 Da" must parse as 0.002 Da, not 3 Da (regression guard for the number regex).
    magnitude, unit = _parse_tolerance("2e-3 Da")
    assert magnitude == pytest.approx(0.002)
    assert unit == "da"
    # And a normal bracketed range still parses as before.
    assert _parse_tolerance("[-20.0 ppm, 20.0 ppm]") == (pytest.approx(20.0), "ppm")


# --------------------------------------------------------------------------- #
# PSM FDR
# --------------------------------------------------------------------------- #


def test_fdr_psm_valid_passes():
    issues = check_fdr_psm(make_standard_df(), make_params(ident_fdr_psm=0.01), ModuleValidationConfig())
    assert issues == []


def test_fdr_psm_above_recommended_warns():
    issues = check_fdr_psm(make_standard_df(), make_params(ident_fdr_psm=0.05), ModuleValidationConfig())
    assert any(i.code == "fdr_psm_above_recommended" and i.severity == Severity.WARNING for i in issues)


def test_fdr_psm_out_of_range_warns():
    issues = check_fdr_psm(make_standard_df(), make_params(ident_fdr_psm=1.5), ModuleValidationConfig())
    assert any(i.code == "fdr_psm_out_of_range" for i in issues)


def test_fdr_psm_missing_warns():
    issues = check_fdr_psm(make_standard_df(), make_params(ident_fdr_psm="None"), ModuleValidationConfig())
    assert any(i.code == "fdr_psm_not_parsed" and i.severity == Severity.WARNING for i in issues)


def test_fdr_psm_recommendation_configurable():
    # Disabling the recommendation removes the above-recommended warning.
    config = ModuleValidationConfig(recommended_max_fdr_psm=None)
    issues = check_fdr_psm(make_standard_df(), make_params(ident_fdr_psm=0.05), config)
    assert not any(i.code == "fdr_psm_above_recommended" for i in issues)


# --------------------------------------------------------------------------- #
# orchestrator + report semantics
# --------------------------------------------------------------------------- #


def test_validate_submission_passes_for_valid(reference_fasta):
    report = validate_submission(
        make_standard_df(),
        parameters=make_params(),
        fasta=reference_fasta,
        config=ModuleValidationConfig(),
        input_format="MaxQuant",
    )
    assert report.passed
    assert not report.has_errors


def test_validate_submission_blocks_on_errors(reference_fasta):
    df = make_standard_df(Charge=[2, 9, 2, 2])
    df.loc[0, "Proteins"] = "sp|P99999|MISSING_HUMAN"
    report = validate_submission(
        df, parameters=make_params(), fasta=reference_fasta, config=ModuleValidationConfig(), input_format="MaxQuant"
    )
    assert not report.passed
    assert report.has_errors
    codes = {i.code for i in report.errors}
    assert "protein_not_in_fasta" in codes
    assert "charge_out_of_range" in codes


def test_validate_submission_without_fasta_skips_protein_check():
    report = validate_submission(make_standard_df(), parameters=make_params(), fasta=None)
    assert report.passed
    assert any(i.code == "no_fasta_reference" and i.severity == Severity.INFO for i in report.issues)


def test_validate_submission_without_params_warns():
    report = validate_submission(make_standard_df(), parameters=None, fasta=None)
    assert report.passed
    assert not report.has_errors
    # Each parameter-dependent check self-reports that its constraint was not parsed.
    assert any(i.code == "charge_range_not_parsed" and i.severity == Severity.WARNING for i in report.warnings)


def test_validate_submission_empty_df_errors():
    report = validate_submission(pd.DataFrame(), parameters=make_params())
    assert report.has_errors
    assert any(i.code == "empty_results" for i in report.errors)


def test_report_serialization_and_summary():
    report = ValidationReport()
    report.add_error("x", "an error", "check_a", examples=["e1"])
    report.add_warning("y", "a warning", "check_b")
    as_dict = report.to_dict()
    assert as_dict["passed"] is False
    assert as_dict["n_errors"] == 1 and as_dict["n_warnings"] == 1
    summary = report.summary()
    assert "Automated submission checks" in summary
    assert "an error" in summary and "a warning" in summary
    # Wording must stay neutral (validation does not block submission).
    assert "PASSED" not in summary and "FAILED" not in summary


def test_summary_passed_when_clean():
    report = ValidationReport()
    report.add_info("i", "just info", "check_a")
    assert "All automated checks passed." in report.summary()


def test_raise_if_errors():
    report = ValidationReport()
    report.add_error("x", "boom", "check_a")
    with pytest.raises(SubmissionValidationError):
        report.raise_if_errors()
    # No error -> no raise.
    ValidationReport().raise_if_errors()


# --------------------------------------------------------------------------- #
# profile registry / generic routing
# --------------------------------------------------------------------------- #


def test_builtin_profiles_registered():
    profiles = available_profiles()
    assert "quant_lfq" in profiles
    assert "denovo" in profiles
    assert get_profile("quant_lfq") is not None
    assert "protein_ids" in get_profile("quant_lfq").check_names


def test_default_config_uses_quant_profile():
    assert ModuleValidationConfig().validation_profile == "quant_lfq"


def test_denovo_profile_skips_quant_checks():
    # A de novo standard df has none of the quant columns.
    df = pd.DataFrame({"spectrum_id": [1, 2], "peptide_str": ["PEPTIDEK", "ELVISLIVESR"]})
    config = ModuleValidationConfig(validation_profile="denovo")
    # software_name matches input_format so the shared run_consistency check passes.
    report = validate_submission(
        df, parameters=make_params(software_name="Casanovo"), config=config, input_format="Casanovo"
    )
    assert report.passed
    assert any(i.code == "denovo_validation_pending" for i in report.infos)
    # No quant-specific errors were produced.
    assert not any(i.code in {"protein_not_in_fasta", "charge_out_of_range"} for i in report.issues)


def test_unknown_profile_warns_and_runs_nothing():
    config = ModuleValidationConfig(validation_profile="does_not_exist")
    report = validate_submission(make_standard_df(), parameters=make_params(), config=config)
    assert report.passed  # nothing ran, so no errors
    assert any(i.code == "unknown_validation_profile" and i.severity == Severity.WARNING for i in report.issues)


def test_explicit_profile_overrides_config():
    # Config says quant_lfq, but the explicit profile arg wins.
    report = validate_submission(
        make_standard_df(), parameters=make_params(), config=ModuleValidationConfig(), profile="denovo"
    )
    assert any(i.code == "denovo_validation_pending" for i in report.infos)


def test_register_and_run_custom_profile():
    def my_check(ctx: ValidationContext):
        r = ValidationReport()
        if "MyColumn" not in ctx.standard_df.columns:
            r.add_error("missing_my_column", "MyColumn is required", "my_check", field="MyColumn")
        return r.issues

    profile = ValidationProfile(name="custom_test_profile", checks=[Check("my_check", my_check)])
    register_profile(profile)
    try:
        report = validate_submission(make_standard_df(), profile="custom_test_profile")
        assert report.has_errors
        assert any(i.code == "missing_my_column" for i in report.errors)
    finally:
        unregister_profile("custom_test_profile")
    assert get_profile("custom_test_profile") is None


def test_register_duplicate_profile_raises():
    profile = ValidationProfile(name="dup_test_profile", checks=[])
    register_profile(profile)
    try:
        with pytest.raises(ValueError):
            register_profile(ValidationProfile(name="dup_test_profile", checks=[]))
        # overwrite=True succeeds.
        register_profile(ValidationProfile(name="dup_test_profile", checks=[]), overwrite=True)
    finally:
        unregister_profile("dup_test_profile")


def test_profile_resolution_from_parse_settings():
    quant_cfg = ModuleValidationConfig.from_parse_settings(QEXACTIVE_SETTINGS_DIR, QEXACTIVE_MODULE_ID, "MaxQuant")
    assert quant_cfg.validation_profile == "quant_lfq"

    denovo_dir = os.path.abspath(
        os.path.join(HERE, "..", "proteobench", "io", "parsing", "io_parse_settings", "denovo", "DDA", "HCD")
    )
    denovo_cfg = ModuleValidationConfig.from_parse_settings(denovo_dir, "denovo_DDA_HCD", "Casanovo")
    assert denovo_cfg.validation_profile == "denovo"


def test_resolve_profile_infers_from_parser_class():
    # With no declared profile, resolution falls back to MODULE_TO_CLASS inference.
    assert _resolve_profile("quant_lfq_DDA_ion_QExactive", None) == "quant_lfq"
    assert _resolve_profile("denovo_DDA_HCD", None) == "denovo"
    # Unknown module_id falls back to the default profile.
    assert _resolve_profile("does_not_exist", None) == "quant_lfq"
    # An explicit declared profile always wins.
    assert _resolve_profile("denovo_DDA_HCD", "custom_xyz") == "custom_xyz"


def test_non_string_profile_does_not_crash():
    # A malformed validation_profile must degrade gracefully, never raise.
    config = ModuleValidationConfig(validation_profile=["not", "a", "string"])
    report = validate_submission(make_standard_df(), parameters=make_params(), config=config)
    assert report.passed
    assert any(i.code == "unknown_validation_profile" for i in report.issues)


# --------------------------------------------------------------------------- #
# lightweight integration with the real parser (MaxQuant + Sage)
# --------------------------------------------------------------------------- #

REAL_TOOL_FILES = {
    "MaxQuant": "MaxQuant_evidence_sample.txt",
    "Sage": "sage_sample_input_lfq.tsv",
}


def _standard_df_for_tool(tool):
    path = os.path.join(QEXACTIVE_DATA_DIR, REAL_TOOL_FILES[tool])
    if not os.path.isfile(path):
        pytest.skip(f"Test data for {tool} not available: {path}")
    input_df = load_input_file(path, tool)
    parser = ParseSettingsBuilder(
        parse_settings_dir=QEXACTIVE_SETTINGS_DIR, module_id=QEXACTIVE_MODULE_ID
    ).build_parser(tool)
    # convert_to_standard_format now returns only the standard DataFrame
    # (replicate mapping is obtained separately via create_replicate_mapping()).
    standard_df = parser.convert_to_standard_format(input_df)
    return standard_df


def _fasta_from_standard_df(df):
    ids = set()
    for cell in df["Proteins"].dropna().unique():
        for token in split_protein_groups(cell):
            ids |= extract_identifiers(token)
    return FastaReference.from_identifiers(ids)


@pytest.mark.parametrize("tool", ["MaxQuant", "Sage"])
def test_integration_real_tool_matching_fasta_passes(tool):
    df = _standard_df_for_tool(tool)
    fasta = _fasta_from_standard_df(df)
    config = ModuleValidationConfig.from_parse_settings(QEXACTIVE_SETTINGS_DIR, QEXACTIVE_MODULE_ID, tool)
    issues = check_protein_ids(df, fasta, config)
    assert not any(i.severity == Severity.ERROR for i in issues)


@pytest.mark.parametrize("tool", ["MaxQuant", "Sage"])
def test_integration_real_tool_injected_unknown_protein_errors(tool):
    df = _standard_df_for_tool(tool)
    fasta = _fasta_from_standard_df(df)
    df = df.copy()
    df.iloc[0, df.columns.get_loc("Proteins")] = "sp|ZZZ999|NOTINFASTA_HUMAN"
    config = ModuleValidationConfig.from_parse_settings(QEXACTIVE_SETTINGS_DIR, QEXACTIVE_MODULE_ID, tool)
    issues = check_protein_ids(df, fasta, config)
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert any(i.code == "protein_not_in_fasta" for i in errors)
    assert any("ZZZ999" in str(e) for i in errors for e in i.examples)
