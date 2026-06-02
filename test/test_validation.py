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

from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.validation import (
    FastaReference,
    ModuleValidationConfig,
    Severity,
    SubmissionValidationError,
    ValidationReport,
    validate_submission,
)
from proteobench.validation.checks import (
    check_charge_range,
    check_enzyme,
    check_modifications,
    check_peptide_length,
    check_protein_ids,
    check_run_consistency,
)
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


def test_enzyme_non_trypsin_skipped_as_info():
    issues = check_enzyme(make_standard_df(), make_params(enzyme="Chymotrypsin"), ModuleValidationConfig())
    assert any(i.code == "enzyme_check_unsupported" and i.severity == Severity.INFO for i in issues)


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
    assert any(i.code == "no_parameters" and i.severity == Severity.WARNING for i in report.issues)


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
    assert "FAILED" in report.summary()


def test_raise_if_errors():
    report = ValidationReport()
    report.add_error("x", "boom", "check_a")
    with pytest.raises(SubmissionValidationError):
        report.raise_if_errors()
    # No error -> no raise.
    ValidationReport().raise_if_errors()


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
    standard_df, _ = parser.convert_to_standard_format(input_df)
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
