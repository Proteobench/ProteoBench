import inspect
import io
import json
import os
import zipfile
from collections import defaultdict

import pandas as pd
import requests
import toml
from bs4 import BeautifulSoup

from proteobench.modules.denovo.denovo_DDA_HCD import DDAHCDDeNovoModule
from proteobench.modules.quant.quant_lfq_ion_DDA_Astral import DDAQuantIonAstralModule
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import (
    DDAQuantIonModuleQExactive,
)
from proteobench.modules.quant.quant_lfq_ion_DIA_AIF import DIAQuantIonModuleAIF
from proteobench.modules.quant.quant_lfq_ion_DIA_Astral import DIAQuantIonModuleAstral
from proteobench.modules.quant.quant_lfq_ion_DIA_Plasma import DIAQuantIonModulePlasma
from proteobench.modules.quant.quant_lfq_ion_DIA_ZenoTOF import DIAQuantIonModuleZenoTOF
from proteobench.modules.quant.quant_lfq_ion_DIA_diaPASEF import (
    DIAQuantIonModulediaPASEF,
)
from proteobench.modules.quant.quant_lfq_ion_DIA_lowinput import (
    DIAQuantIonModulediaSC,
)
from proteobench.modules.quant.quant_lfq_peptidoform_DDA import (
    DDAQuantPeptidoformModule,
)
from proteobench.modules.quant.quant_lfq_peptidoform_DIA import (
    DIAQuantPeptidoformModule,
)

# Dictionary mapping module name strings to their classes
MODULE_CLASSES = {
    "DDAQuantIonModuleQExactive": DDAQuantIonModuleQExactive,
    "DDAQuantIonAstralModule": DDAQuantIonAstralModule,
    "DIAQuantIonModuleAIF": DIAQuantIonModuleAIF,
    "DIAQuantIonModuleAstral": DIAQuantIonModuleAstral,
    "DIAQuantIonModulediaPASEF": DIAQuantIonModulediaPASEF,
    "DIAQuantIonModuleZenoTOF": DIAQuantIonModuleZenoTOF,
    "DIAQuantIonModulediaSC": DIAQuantIonModulediaSC,
    "DIAQuantIonModulePlasma": DIAQuantIonModulePlasma,
    "DDAQuantPeptidoformModule": DDAQuantPeptidoformModule,
    "DIAQuantPeptidoformModule": DIAQuantPeptidoformModule,
    "DDAHCDDeNovoModule": DDAHCDDeNovoModule,
}

# Keys a caller may place in a submission_settings dict that are forwarded to the module's
# `benchmarking()` only when that module actually accepts them. The module families expose
# deliberately different knobs -- quant takes `default_cutoff_min_feature` and
# `max_nr_observed`, de novo takes `evaluation_type` -- so forwarding any of them
# unconditionally raises TypeError for whichever family the caller is not using.
OPTIONAL_BENCHMARKING_KEYS = (
    "default_cutoff_min_feature",
    "evaluation_type",
    "max_nr_observed",
    "input_file_secondary",
)

REQUIRED_SUBMISSION_KEYS = ("input_file", "input_type", "param_file")

DATASETS_BASE_URL = "https://proteobench.cubimed.rub.de/datasets/"


def download_file(url: str, local_path: str, chunk_size: int = 8192) -> str:
    """
    Download a file from URL to local path.

    Parameters
    ----------
    url : str
        URL to download from
    local_path : str
        Local path to save file
    chunk_size : int
        Size of chunks for streaming download (default: 8192)

    Returns
    -------
    str
        Path to downloaded file
    """
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    print(f"Downloading file from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)

    print(f"File downloaded to {local_path}")
    return local_path


def dataset_folder_exists(intermediate_hash: str, base_url: str = DATASETS_BASE_URL) -> bool:
    """
    Check if a dataset folder already exists on the public server for a given intermediate hash.
    First tries a direct HEAD to the folder URL, then falls back to parsing the index page.

    Args:
        intermediate_hash: The hash to check for
        base_url: Base URL of the datasets server

    Returns:
        True if the dataset folder exists, False otherwise
    """
    if not intermediate_hash:
        return False

    folder_url = f"{base_url.rstrip('/')}/{intermediate_hash.strip('/')}/"
    try:
        resp = requests.head(folder_url, allow_redirects=True, timeout=5)
        if resp.status_code == 200:
            return True
        # Some servers may redirect. If it ends in the folder, treat as exists.
        if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get("Location", "").rstrip("/").endswith(
            f"/{intermediate_hash.strip('/')}"
        ):
            return True
    except Exception:
        pass

    # Fallback: parse directory listing
    try:
        resp = requests.get(base_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        folder_links = {
            a.get("href", "").strip("/").split("/")[0] for a in soup.find_all("a") if a.get("href", "").endswith("/")
        }
        return intermediate_hash.strip("/") in folder_links
    except Exception:
        return False


def get_merged_json(
    repo_url="https://github.com/Proteobench/Results_quant_ion_DDA/archive/refs/heads/main.zip",
    write_to_file=False,
    outfile_name="combined_results.json",
):
    # Download ZIP archive from GitHub
    response = requests.get(repo_url)
    zip_bytes = io.BytesIO(response.content)

    # Extract ZIP contents to a local folder
    with zipfile.ZipFile(zip_bytes) as zip_ref:
        zip_ref.extractall(repo_url.split("/")[-5])

    # Prepare base directory
    base_path = f"{repo_url.split('/')[-5]}/{repo_url.split('/')[-5]}-main"

    # Initialize combined JSON container
    combined_json = []

    # Walk through directory and read all JSON files
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        combined_json.append(data)
                    except json.JSONDecodeError as e:
                        print(f"Error reading {file_path}: {e}")

    if write_to_file:
        # Write combined JSON to a single output file (optional)
        with open(outfile_name, "w", encoding="utf-8") as out_file:
            json.dump(combined_json, out_file, ensure_ascii=False, indent=2)

    print(f"Combined {len(combined_json)} JSON files into 'combined_results.json'.")

    df = pd.json_normalize(combined_json)
    return df


def get_raw_data(df, base_url="https://proteobench.cubimed.rub.de/datasets/", output_directory="extracted_files"):
    hash_vis_dir = {}

    # Extract the hash list from the DataFrame
    hash_list = df["intermediate_hash"].tolist()

    # Fetch folder names from the webpage
    response = requests.get(base_url)
    response.raise_for_status()  # Check for errors

    soup = BeautifulSoup(response.text, "html.parser")
    folder_links = [link["href"].strip("/") for link in soup.find_all("a") if link["href"].endswith("/")]

    # Filter folder links based on the hash list
    matching_folders = [folder for folder in folder_links if folder in hash_list]

    # Download and extract zip files from matching folders
    for folder in matching_folders:
        extract_dir = f"{output_directory}/{folder}"
        if os.path.exists(extract_dir) and os.listdir(extract_dir):
            print(f"Folder already exists and is not empty, skipping download: {extract_dir}")
            hash_vis_dir[folder] = extract_dir
            continue

        folder_url = f"{base_url}{folder}/"
        print(f"Processing folder: {folder_url}")

        # Fetch the folder page
        folder_response = requests.get(folder_url)
        folder_response.raise_for_status()

        folder_soup = BeautifulSoup(folder_response.text, "html.parser")
        zip_files = [link["href"] for link in folder_soup.find_all("a") if link["href"].endswith(".zip")]

        # Process each .zip file
        for zip_file in zip_files:
            zip_url = f"{folder_url}{zip_file}"
            print(f"Downloading: {zip_url}")

            # Download with a progress bar
            zip_response = requests.get(zip_url, stream=True)
            zip_response.raise_for_status()

            zip_filename = os.path.basename(zip_file)
            total_size = int(zip_response.headers.get("content-length", 0))
            block_size = 1024  # 1 KB

            # Save the zip file
            with open(zip_filename, "wb") as f:
                for data in zip_response.iter_content(block_size):
                    f.write(data)

            # Extract the zip file
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_filename, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
                print(f"Extracted contents to: {extract_dir}")

            # Cleanup downloaded .zip file
            os.remove(zip_filename)

            hash_vis_dir[folder] = extract_dir

    return hash_vis_dir


def _is_missing(value) -> bool:
    """
    Whether a parsed parameter value carries no information.

    `ProteoBenchParameters` coerces the string "None" to `np.nan`, so an absent parameter can
    arrive as either `None` or NaN. List-valued parameters (`isotope_error_range`) make
    `pd.isna` return an array rather than a bool, hence the guard.

    Parameters
    ----------
    value : Any
        The parsed parameter value.

    Returns
    -------
    bool
        True when the value is None or NaN.
    """
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def make_submission(
    submission_files=None,
    token: str = "",
    module_name: str = "",
    submission_source: str = "resubmission-script",
) -> list:
    """
    Run the full submission pipeline programmatically for one or more result files.

    Parameters
    ----------
    submission_files : list of dict, optional
        One dict per submission. Each must carry `input_file`, `input_type` and `param_file`.
        `user_comments` is optional. Any of `default_cutoff_min_feature`, `evaluation_type`,
        `max_nr_observed` or `input_file_secondary` is forwarded to `benchmarking()` only if
        the target module accepts it (see `OPTIONAL_BENCHMARKING_KEYS`).
    token : str
        GitHub token, used both to read the results repo and to push the pull request branch.
    module_name : str
        Key into `MODULE_CLASSES`.
    submission_source : str, optional
        Origin recorded on the pull request, which decides its labels. Defaults to
        "resubmission-script" (label `batch-resubmission`); "local" additionally applies
        `do-not-merge`.

    Returns
    -------
    list of str
        The URL of every pull request created, in submission order.

    Raises
    ------
    ValueError
        If `module_name` is not a known module.
    KeyError
        If a submission dict is missing a required key.
    """
    if module_name not in MODULE_CLASSES:
        raise ValueError(f"Module {module_name} not recognized. Available modules: {list(MODULE_CLASSES.keys())}")
    module_class = MODULE_CLASSES[module_name]

    pull_request_urls = []
    for submission_settings in submission_files or []:
        missing = [key for key in REQUIRED_SUBMISSION_KEYS if key not in submission_settings]
        if missing:
            raise KeyError(f"Submission is missing {missing}; got keys {sorted(submission_settings)}.")

        input_file = submission_settings["input_file"]
        input_type = submission_settings["input_type"]
        user_comments = submission_settings.get("user_comments", "no comments")

        module_obj = module_class(token=token)

        # Parse the metadata file first and seed the user input from it. Doing this before
        # benchmarking rather than after means the datapoint is built with its real software
        # version, checkpoint and decoding strategy instead of empty strings. Those values go
        # into the datapoint id and from there into the pull request branch name, so a
        # submission made without them is hard to tell apart from any other run of the same
        # tool -- which is exactly the case when submitting several decoding variants.
        # Neither datapoint's `intermediate_hash` depends on this input, so seeding it does
        # not change deduplication.
        param_obj = module_obj.load_params_file([submission_settings["param_file"]], input_type)
        user_input = defaultdict(
            lambda: "",
            {key: value for key, value in vars(param_obj).items() if not _is_missing(value)},
        )
        user_input["comments_for_plotting"] = user_comments

        accepted = inspect.signature(module_obj.benchmarking).parameters
        benchmarking_kwargs = {
            key: submission_settings[key]
            for key in OPTIONAL_BENCHMARKING_KEYS
            if key in submission_settings and key in accepted
        }

        all_datapoints = module_obj.obtain_all_data_points(all_datapoints=None)
        _, all_datapoints, _ = module_obj.benchmarking(
            input_file,
            input_type,
            user_input,
            all_datapoints,
            **benchmarking_kwargs,
        )

        pull_request_urls.append(
            module_obj.clone_pr(
                all_datapoints,
                param_obj,
                remote_git="",
                submission_comments=user_comments,
                submission_source=submission_source,
            )
        )

    return pull_request_urls
