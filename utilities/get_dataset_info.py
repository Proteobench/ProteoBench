#!/bin/python
"""
This small script downloads the datapoint information stored in teh JSON from the GitHub
repos and writes out a small overview. Useful to cerate an overview for the datasets
provided as download.
"""

import requests

# TODO: this does not work anymore! The concatenated JSON file is not available anymore

# URLs of the JSON file
repo_jsons = {
    "DDA quantification - precursor ions": "https://raw.githubusercontent.com/Proteobench/Results_quant_ion_DDA/main/results.json",
}

# download JSON files and print out general information
for name, url in repo_jsons.items():
    # Send a GET request to the URL
    try:
        response = requests.get(url)

        # Parse the JSON content into a Python dictionary
        data = response.json()

        print("#", name)
        for datapoint in data:
            data_info = (
                datapoint["id"]
                + "\t"
                + datapoint["software_name"]
                + "\t"
                + datapoint["software_version"]
                + "\t"
                + datapoint["intermediate_hash"]
            )
            print(data_info)
    except Exception as e:
        print("# Could not get data for ", name)

# %%
