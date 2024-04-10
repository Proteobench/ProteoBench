import pathlib

import pandas as pd

from proteobench.io.params import ProteoBenchParameters


def extract_params(fname) -> ProteoBenchParameters:
    params = pd.read_csv(fname, sep="\t", header=None, index_col=0).squeeze()
    _tol_frag = "{} ({})".format(
        params.loc["spectrum, fragment monoisotopic mass error"],
        params.loc["spectrum, fragment monoisotopic mass error units"],
    )
    assert (
        params.loc["spectrum, parent monoisotopic mass error minus"]
        == params.loc["spectrum, parent monoisotopic mass error plus"]
    ), "not summetric tolerance"

    _tol_prec = "{} ({})".format(
        params.loc["spectrum, parent monoisotopic mass error minus"],
        params.loc["spectrum, parent monoisotopic mass error units"],
    )

    max_cleavage = params.loc["scoring, maximum missed cleavage sites"]
    if params.loc["refine"] == "yes":
        max_cleavage = params.loc["refine, maximum missed cleavage sites"]

    params = ProteoBenchParameters(
        software_name="i2MassChroQ",
        software_version=params.loc["i2MassChroQ_VERSION"],
        search_engine=params.loc["AnalysisSoftware_name"],
        search_engine_version=params.loc["AnalysisSoftware_version"],
        ident_fdr_psm=params.loc["psm_fdr"],
        ident_fdr_peptide=params.loc["peptide_fdr"],
        ident_fdr_protein=params.loc["protein_fdr"],
        enable_match_between_runs=params.loc["mcq_mbr"],
        precursor_mass_tolerance=_tol_prec,
        fragment_mass_tolerance=_tol_frag,
        enzyme=params.loc["protein, cleavage site"],
        allowed_miscleavages=max_cleavage,
        min_peptide_length=None,  # "spectrum, minimum fragment mz"
        max_peptide_length=None,  # not mentionded, up to 38 AA in peptides
        fixed_mods=",".join(params.loc[params.index.str.contains("residue, modification mass")].dropna()),
        variable_mods=",".join(params.loc[params.index.str.contains("residue, potential modification mass")].dropna()),
        max_mods=None,
        min_precursor_charge=1,  # fixed in software
        max_precursor_charge=params.loc["spectrum, maximum parent charge"],
    )
    return params


if __name__ == "__main__":
    for fname in [
        "../../../test/params/i2mproteobench_2pep_fdr01psm_fdr01prot.ods",
    ]:
        file = pathlib.Path(fname)
        # ! First sheet contains search settings and infos, slow to read (~4mins)
        # params = pd.read_excel(
        #     fname, engine="odf", names=["param", "value"], sheet_name=0, header=None, index_col=0
        # ).squeeze()
        # ! change for speed to text based table (needs to be done by developers)
        params = pd.read_csv(file.with_suffix(".tsv"), sep="\t", header=None, index_col=0).squeeze()
        params = extract_params(file.with_suffix(".tsv"))
        data_dict = params.__dict__
        series = pd.Series(data_dict)
        series.to_csv(file.parent / (file.stem + "_sel.csv"))
