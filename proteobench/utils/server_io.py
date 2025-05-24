import io
import json
import os
import zipfile
from collections import defaultdict

import pandas as pd
import requests
import toml
from bs4 import BeautifulSoup
from tqdm import tqdm

from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import DDAQuantIonModuleQExactive
from proteobench.modules.quant.quant_lfq_ion_DDA_Astral import DDAQuantIonAstralModule
from proteobench.modules.quant.quant_lfq_ion_DIA_AIF import DIAQuantIonModule
from proteobench.modules.quant.quant_lfq_ion_DIA_Astral import DIAQuantIonModuleAstral
from proteobench.modules.quant.quant_lfq_ion_DIA_diaPASEF import (
    DIAQuantIonModulediaPASEF,
)
from proteobench.modules.quant.quant_lfq_ion_DIA_singlecell import (
    DIAQuantIonModulediaSC,
)
from proteobench.modules.quant.quant_lfq_peptidoform_DDA import (
    DDAQuantPeptidoformModule,
)
from proteobench.modules.quant.quant_lfq_peptidoform_DIA import (
    DIAQuantPeptidoformModule,
)
import re
from github import Github


# Dictionary mapping module name strings to their classes
MODULE_CLASSES = {
    "DDAQuantIonAstralModule": DDAQuantIonAstralModule,
    "DDAQuantIonModuleQExactive": DDAQuantIonModuleQExactive,
    "DIAQuantIonModule": DIAQuantIonModule,
    "DIAQuantIonModuleAstral": DIAQuantIonModuleAstral,
    "DIAQuantIonModulediaPASEF": DIAQuantIonModulediaPASEF,
    "DIAQuantIonModulediaSC": DIAQuantIonModulediaSC,
    "DDAQuantPeptidoformModule": DDAQuantPeptidoformModule,
    "DIAQuantPeptidoformModule": DIAQuantPeptidoformModule,
}


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
        zip_ref.extractall("Results_quant_ion_DDA")

    # Prepare base directory
    base_path = "Results_quant_ion_DDA/Results_quant_ion_DDA-main"

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
            with (
                open(zip_filename, "wb") as f,
                tqdm(
                    desc=f"Downloading {zip_filename}",
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as progress,
            ):
                for data in zip_response.iter_content(block_size):
                    f.write(data)
                    progress.update(len(data))

            # Extract the zip file
            extract_dir = f"{output_directory}/{folder}"

            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_filename, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
                print(f"Extracted contents to: {extract_dir}")

            # Cleanup downloaded .zip file
            os.remove(zip_filename)

            hash_vis_dir[folder] = extract_dir

    return hash_vis_dir


def make_submission(submission_files=[], token="", module_name=""):
    for submission_settings in submission_files:
        # TODO change to the correct module
        # Dictionary mapping module name strings to their classes
        if module_name not in MODULE_CLASSES:
            raise ValueError(f"Module {module_name} not recognized. Available modules: {list(MODULE_CLASSES.keys())}")

        module_class = MODULE_CLASSES[module_name]
        module_obj = module_class(token="")
        results_df = module_obj.obtain_all_data_points(all_datapoints=None)

        param_file = submission_settings["param_file"]
        input_file = submission_settings["input_file"]
        input_type = submission_settings["input_type"]
        default_cutoff_min_prec = submission_settings["default_cutoff_min_prec"]
        user_comments = submission_settings["user_comments"]

        user_config = defaultdict(lambda: "")

        results_intermediates, results_df_new, parsed_input = module_obj.benchmarking(
            input_file,
            input_type,
            user_config,
            results_df,
            default_cutoff_min_prec=default_cutoff_min_prec,
        )

        results_df_new.tail(5)

        try:
            param_obj = module_obj.load_params_file([param_file], input_type)
        except:
            continue

        pr_url = module_obj.clone_pr(
            results_df_new,
            param_obj,
            remote_git="",
            submission_comments=user_comments,
        )

        return pr_url


class GithubPRParser:
    def __init__(self, token: str = ""):
        self.github = Github(token) if token else Github()

    def get_repo(self, repo_name: str):
        return self.github.get_repo(repo_name)

    @staticmethod
    def clean_key(key: str) -> str:
        """Clean string to valid key format."""
        return re.sub(r"[^a-zA-Z0-9_]+", "", key.strip())

    @staticmethod
    def extract_identifier(title: str) -> str:
        """Extract unique identifier from PR title."""
        match = re.search(r"([A-Za-z0-9]+_\d{8}_\d{6})", title)
        return match.group(0) if match else None

    @staticmethod
    def parse_parameter_changes(body: str) -> dict:
        """
        Parse the parameter changes from the pull request body.
        Returns a dictionary with keys and [old_val, new_val] lists.
        """
        param_dict = {}
        match = re.search(r"Parameter changes Detected:\s*(.*)", body, re.DOTALL)
        if not match:
            return param_dict

        section_text = body[match.start() :]
        lines = section_text.splitlines()

        param_lines = []
        found_header = False
        for line in lines:
            if found_header:
                if line.strip() == "" or line.strip().endswith(":") or line.strip().startswith("Dataset URL"):
                    break
                param_lines.append(line.strip())
            elif line.strip() == "Parameter changes Detected:":
                found_header = True

        for line in param_lines:
            m = re.match(r"([^:]+):\s*(.*?)\s*→\s*(.*)", line)
            if m:
                key = GithubPRParser.clean_key(m.group(1))
                old_val = m.group(2).strip(" `")
                new_val = m.group(3).strip(" `")
                param_dict[key] = [old_val, new_val]
        return param_dict

    def collect_pulls_info(self, repo_name: str):
        repo = self.get_repo(repo_name)
        pulls = repo.get_pulls(state="all", sort="created", direction="desc")
        pulls_dict_params = {}
        pulls_dict_all = {}

        for pull in pulls:
            title = pull.title
            body = pull.body or ""
            param_changes = self.parse_parameter_changes(body)
            identifier = self.extract_identifier(title)

            pulls_dict_all[identifier] = {
                "pr_number": pull.number,
                "title": title,
                "body": body,
                "param_changes": param_changes,
            }
            if param_changes:
                pulls_dict_params[identifier] = pulls_dict_all[identifier]
        return pulls_dict_all, pulls_dict_params
