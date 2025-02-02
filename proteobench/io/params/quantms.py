"""quantms is a nextflow pipeline that execution depends on the settings in an
SDRF file. It is executed using a parameters file in JSON format.

However, the version of packages are dumped to a versions yaml file. And some parameters
are taken from the SDRF file.
"""

import json
import logging
import pathlib
from typing import IO, Union

import pandas as pd
import yaml

from proteobench.io.params import ProteoBenchParameters

logger = logging.getLogger(__name__)


def load_versions(file: IO) -> dict:
    """
    Load the versions of the tools used in the quantms pipeline.
    """
    versions = yaml.safe_load(file)
    return versions


def load_parsed_sdrf(file: Union[str, pathlib.Path, IO]) -> pd.DataFrame:
    """
    Load the parsed SDRF file.
    """
    return pd.read_csv(file, sep="\t")


def load_files(file1: IO, file2: IO, file3: IO) -> [dict, pd.DataFrame]:
    """Load file independent of order they are provided in."""
    versions = None
    sdrf = None
    pipeline_params = None
    for file in [file1, file2, file3]:
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
        except yaml.YAMLError as e:
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
        except pd.errors.EmptyDataError as e:
            pass

    assert versions is not None
    assert sdrf is not None
    assert pipeline_params is not None

    return versions, sdrf, pipeline_params


def extract_params(file1: IO, file2: IO, file3: IO) -> ProteoBenchParameters:
    """
    Extract parameters from the parsed SDRF and version file. We use both the parsed
    SDRF file and the yaml file of versions to extract the parameters. The function
    needs to be able to handle any order of files as the streamlit interfaces does
    allow the user to select any order.

    This might be changed in a newer quantms version with one central parameters
    file.
    """
    versions, sdrf, pipeline_params = load_files(file1, file2, file3)

    params = ProteoBenchParameters()
    params.software_name = "quantms"
    params.software_version = versions["Workflow"]["bigbio/quantms"]
    engines = list()
    engines_version = list()
    for key in versions:
        if key.startswith("SEARCHENGINE"):
            _engine = key.split("SEARCHENGINE")[-1].lower()
            engines.append(_engine)
            if _engine == "comet":
                engines_version.append(versions[key]["Comet"])
            elif _engine == "msgf":
                versions.append(versions[key]["msgf_plus"])
            else:
                raise ValueError(f"Unknown search engine: {_engine}")
    if engines:
        params.search_engine = ",".join(engines)
    if engines_version:
        params.search_engine_version = ",".join(engines_version)

    return (versions, sdrf, pipeline_params, params)


if __name__ == "__main__":

    from pathlib import Path

    fpath1 = Path("../../../test/params/quantms_1-3.sdrf_config.tsv")
    fpath2 = Path("../../../test/params/quantms_1-3.nf_core_quantms_software_mqc_versions.yml")
    fpath3 = Path("../../../test/params/quantms_1-3_dev.json")

    # Extract parameters from the fileP
    with open(fpath1, "r") as file1, open(fpath2, "r") as file2, open(fpath3, "r") as file3:
        versions, sdrf, pipeline_params, params = extract_params(file1, file2, file3)
        display(params.__dict__)

    import itertools

    permutations_fpath = list(itertools.permutations([fpath1, fpath2, fpath3]))
    for file1, file2, file3 in permutations_fpath:
        print(file1.name, file2.name, file3.name)
        with open(file1, "r") as f1, open(file2, "r") as f2, open(file3, "r") as f3:
            _versions, _sdrf, _pipeline_params, params = extract_params(f1, f2, f3)
            assert _versions == versions
            assert _sdrf.equals(sdrf)
            assert _pipeline_params == pipeline_params
            # display(params.__dict__)

    # Convert the extracted parameters to a dictioPnary and then to a pandas Series
    # data_dict = params.__dict__
    # series = pd.Series(data_dict)
    # # Write the Series to a CSV file
    # series.to_csv(file.with_suffix(".csv"))
