"""
Quantms is a nextflow pipeline that execution depends on the settings in an
SDRF file. It is executed using a parameters file in JSON format.

However, the version of packages are dumped to a versions yaml file. And some parameters
are taken from the SDRF file.
"""

import json
import logging
import pathlib
from typing import IO, Tuple, Union

import pandas as pd
import yaml

from proteobench.io.params import ProteoBenchParameters

logger = logging.getLogger(__name__)


def load_versions(file: IO) -> dict:
    """
    Load the versions of the tools used in the quantms pipeline.

    Parameters
    ----------
    file : IO
        File object of the quantms pipeline versions file.

    Returns
    -------
    dict
        Dictionary with the versions of the tools used in the quantms pipeline.
    """
    versions = yaml.safe_load(file)
    return versions


def load_parsed_sdrf(file: Union[str, pathlib.Path, IO]) -> pd.DataFrame:
    """
    Load the parsed SDRF file.

    Parameters
    ----------
    file : Union[str, pathlib.Path, IO]
        File path or file object of the parsed SDRF file.

    Returns
    -------
    pd.DataFrame
        Parsed SDRF file as a pandas DataFrame.
    """
    return pd.read_csv(file, sep="\t")


def load_files(file1: IO, file2: IO, file3: IO = None) -> Tuple[dict, Union[pd.DataFrame, None], dict]:
    """
    Load file independent of order they are provided in.

    SDRF file is optional.

    Parameters
    ----------
    file1 : IO
        File object of the first file.
    file2 : IO
        File object of the second file.
    file3 : IO, optional
        File object of the third file, by default None.

    Returns
    -------
    tuple[dict, pd.DataFrame | None, dict]
        Tuple with the versions, parsed SDRF and pipeline parameters.
    """
    versions = None
    sdrf = None
    pipeline_params = None
    for file in [file1, file2, file3]:
        if file is None:
            continue
        try:
            _versions = load_versions(file)
            if "Workflow" not in _versions:
                logger.debug("Loaded other file.")
                file.seek(0)
            elif versions is None:
                versions = _versions
                continue
            elif "custom_config_base" in _versions:
                logger.debug("Loaded nextflow parameters file.")
            else:
                raise ValueError("Multiple version files provided.")
        except yaml.YAMLError:
            file.seek(0)

        try:
            # file.seek(0)
            _pipeline_params = json.load(file)
            if pipeline_params is None:
                pipeline_params = _pipeline_params
                continue
            else:
                raise ValueError("Multiple parameter files provided.")
        except json.JSONDecodeError as e:
            print(e)
            file.seek(0)

        try:
            # file.seek(0)
            _sdrf = load_parsed_sdrf(file)
            if _sdrf.shape[1] == 1:
                logger.debug("Loaded version or parameter file. Skip")
                continue
            elif sdrf is None:
                sdrf = _sdrf
            else:
                raise ValueError("Multiple SDRF files provided.")
        except pd.errors.EmptyDataError:
            pass

    assert versions is not None
    assert pipeline_params is not None

    return versions, sdrf, pipeline_params


def extract_params(file1: IO, file2: IO, file3: IO = None) -> ProteoBenchParameters:
    """
    Extract parameters from the parsed SDRF and version file. We use both the parsed
    SDRF file and the yaml file of versions to extract the parameters. The function
    needs to be able to handle any order of files as the streamlit interfaces does
    allow the user to select any order.

    This might be changed in a newer quantms version with one central parameters
    file.

    Parameters
    ----------
    file1 : IO
        File object of the first file.
    file2 : IO
        File object of the second file.
    file3 : IO
        File object of the third file, by default None.

    Returns
    -------
    ProteoBenchParameters
        The extracted parameters as a ProteoBenchParameters object.
    """
    versions, sdrf, pipeline_params = load_files(file1, file2, file3)

    params = ProteoBenchParameters()
    params.software_name = "quantms"
    try:
        params.software_version = versions["Workflow"]["bigbio/quantms"]
    except KeyError:
        try:
            params.software_version = versions["Workflow"]["nf-core/quantms"]
        except KeyError:
            raise ValueError(f"Workflow version not found in versions {versions}")
    engines = list()
    engines_version = list()
    for key in versions:
        if key.startswith("SEARCHENGINE"):
            _engine = key.split("SEARCHENGINE")[-1].lower()
            engines.append(_engine)
            if _engine == "comet":
                engines_version.append(versions[key]["Comet"])
            elif _engine == "msgf":
                engines_version.append(versions[key]["msgf_plus"])
            else:
                raise ValueError(f"Unknown search engine: {_engine}")
    if engines:
        params.search_engine = ",".join(engines)
    if engines_version:
        params.search_engine_version = ",".join(engines_version)

    params.enzyme = pipeline_params["enzyme"]
    # "fdr_level": "psm_level_fdrs",
    params.ident_fdr_psm = pipeline_params["psm_level_fdr_cutoff"]
    params.ident_fdr_protein = pipeline_params["protein_level_fdr_cutoff"]
    params.variable_mods = pipeline_params["variable_mods"]
    params.fixed_mods = pipeline_params["fixed_mods"]
    params.max_mods = pipeline_params["max_mods"]
    params.min_precursor_charge = pipeline_params["min_precursor_charge"]
    params.max_precursor_charge = pipeline_params["max_precursor_charge"]
    params.max_peptide_length = pipeline_params["max_peptide_length"]
    params.min_peptide_length = pipeline_params["min_peptide_length"]
    params.precursor_mass_tolerance = "{tol} {unit}".format(
        tol=pipeline_params["precursor_mass_tolerance"], unit=pipeline_params["precursor_mass_tolerance_unit"]
    )
    params.fragment_mass_tolerance = "{tol} {unit}".format(
        tol=pipeline_params["fragment_mass_tolerance"], unit=pipeline_params["fragment_mass_tolerance_unit"]
    )
    params.allowed_miscleavages = pipeline_params["allowed_missed_cleavages"]
    params.quantification_method = pipeline_params["quantification_method"]
    params.protein_inference = pipeline_params["protein_inference_method"]

    # maybe (also) in sdrf infos?
    # params.quantification_method =
    # params.protein_inference =
    # params.abundance_normalization_ions =

    return params


if __name__ == "__main__":
    from pathlib import Path

    from IPython.display import display

    test_params_dir = Path("../../../test/params")

    fpath1 = test_params_dir / "quantms_1-3_test.json"
    fpath2 = test_params_dir / "quantms_1-3_test-versions.yml"

    # Extract parameters from the file - do not parse sdrf
    with open(fpath1, "r") as file1, open(fpath2, "r") as file2:
        params = extract_params(file1, file2)
        display(params.__dict__)

    series = pd.Series(params.__dict__)
    series.to_csv(fpath1.parent / f"{fpath1.stem}_extracted_params.csv")

    # ! in streamlit the IO object is used -> open files
    fpath1 = test_params_dir / "quantms_1-3.sdrf_config.tsv"
    fpath2 = test_params_dir / "quantms_1-3.nf_core_quantms_software_mqc_versions.yml"
    fpath3 = test_params_dir / "quantms_1-3_dev.json"

    # Extract parameters from the file - do not parse sdrf
    with open(fpath2, "r") as file2, open(fpath3, "r") as file3:
        versions, sdrf, pipeline_params = load_files(file2, file3)
        file2.seek(0), file3.seek(0)
        params = extract_params(file2, file3)
        display(params.__dict__)

    # Extract parameters from the file
    with open(fpath1, "r") as file1, open(fpath2, "r") as file2, open(fpath3, "r") as file3:
        versions, sdrf, pipeline_params = load_files(file1, file2, file3)
        file1.seek(0), file2.seek(0), file3.seek(0)
        params = extract_params(file1, file2, file3)
        display(params.__dict__)

    series = pd.Series(params.__dict__)
    series.to_csv(fpath3.parent / f"{fpath3.stem}_extracted_params.csv")

    import itertools

    permutations_fpath = list(itertools.permutations([fpath1, fpath2, fpath3]))
    for file1, file2, file3 in permutations_fpath:
        print(file1.name, file2.name, file3.name)
        with open(file1, "r") as f1, open(file2, "r") as f2, open(file3, "r") as f3:
            _versions, _sdrf, _pipeline_params = load_files(f1, f2, f3)
            f1.seek(0), f2.seek(0), f3.seek(0)
            _params = extract_params(f1, f2, f3)
            assert _versions == versions
            assert _sdrf.equals(sdrf)
            assert _pipeline_params == pipeline_params
            # display(params.__dict__)

    # Convert the extracted parameters to a dictioPnary and then to a pandas Series
    # data_dict = params.__dict__
    # series = pd.Series(data_dict)
    # # Write the Series to a CSV file
    # series.to_csv(file.with_suffix(".csv"))
