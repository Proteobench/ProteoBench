# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "requests",
# ]
# ///

import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import requests

    return mo, requests


@app.cell(hide_code=True)
def _(requests):
    # Module configurations with GitHub repo names
    MODULES = {
        "dda_qexactive": {
            "name": "DDAQuantIonModuleQExactive",
            "html": "DDAQuantIonModuleQExactive.html",
            "repo": "Results_quant_ion_DDA",
            "description": "Ion-level benchmarks for Q-Exactive instruments",
        },
        "dda_astral": {
            "name": "DDAQuantIonAstralModule",
            "html": "DDAQuantIonAstralModule.html",
            "repo": "Results_quant_ion_DDA_Astral",
            "description": "Ion-level benchmarks for Astral instruments",
        },
        "dda_peptidoform": {
            "name": "DDAQuantPeptidoformModule",
            "html": "DDAQuantPeptidoformModule.html",
            "repo": "Results_quant_peptidoform_DDA",
            "description": "Peptidoform-level benchmarks for DDA",
        },
        "dia_astral": {
            "name": "DIAQuantIonModuleAstral",
            "html": "DIAQuantIonModuleAstral.html",
            "repo": "Results_quant_ion_DIA_Astral",
            "description": "Ion-level benchmarks for Astral instruments (DIA mode)",
        },
        "dia_diapasef": {
            "name": "DIAQuantIonModulediaPASEF",
            "html": "DIAQuantIonModulediaPASEF.html",
            "repo": "Results_quant_ion_DIA_diaPASEF",
            "description": "Ion-level benchmarks for diaPASEF acquisition",
        },
        "dia_aif": {
            "name": "DIAQuantIonModuleAIF",
            "html": "DIAQuantIonModuleAIF.html",
            "repo": "Results_quant_ion_DIA_AIF",
            "description": "Ion-level benchmarks for All-Ion Fragmentation",
        },
        "dia_zenotof": {
            "name": "DIAQuantIonModuleZenoTOF",
            "html": "DIAQuantIonModuleZenoTOF.html",
            "repo": "Results_quant_ion_DIA_ZenoTOF",
            "description": "Ion-level benchmarks for ZenoTOF instruments",
        },
        "dia_singlecell": {
            "name": "DIAQuantIonModulediaSC",
            "html": "DIAQuantIonModulediaSC.html",
            "repo": "Results_quant_ion_DIA_singlecell",
            "description": "Ion-level benchmarks for single-cell proteomics",
        },
        "dia_peptidoform": {
            "name": "DIAQuantPeptidoformModule",
            "html": "DIAQuantPeptidoformModule.html",
            "repo": "Results_quant_peptidoform_DIA",
            "description": "Peptidoform-level benchmarks for DIA",
        },
    }

    def get_dataset_count(repo_name: str) -> int | None:
        """Query GitHub API to count JSON files in a Proteobench repo."""
        try:
            url = f"https://api.github.com/repos/Proteobench/{repo_name}/contents"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                files = response.json()
                # Count .json files (excluding any config files)
                json_count = sum(1 for f in files if f["name"].endswith(".json"))
                return json_count
            return None
        except Exception:
            return None

    # Fetch counts for all modules
    dataset_counts = {}
    for key, config in MODULES.items():
        count = get_dataset_count(config["repo"])
        dataset_counts[key] = count

    return MODULES, dataset_counts, get_dataset_count


@app.cell(hide_code=True)
def _(MODULES, dataset_counts, mo):
    def format_module_link(key: str) -> str:
        """Format a module link with dataset count."""
        config = MODULES[key]
        count = dataset_counts.get(key)
        count_str = f" ({count} datasets)" if count is not None else ""
        return f'- [**{config["name"]}**]({config["html"]}){count_str} - {config["description"]}'

    # Build DDA ion-level links
    dda_ion_links = "\n".join([
        format_module_link("dda_qexactive"),
        format_module_link("dda_astral"),
    ])

    # Build DDA peptidoform links
    dda_peptidoform_links = format_module_link("dda_peptidoform")

    # Build DIA ion-level links
    dia_ion_links = "\n".join([
        format_module_link("dia_astral"),
        format_module_link("dia_diapasef"),
        format_module_link("dia_aif"),
        format_module_link("dia_zenotof"),
        format_module_link("dia_singlecell"),
    ])

    # Build DIA peptidoform links
    dia_peptidoform_links = format_module_link("dia_peptidoform")

    mo.md(
        f"""
    # ProteoBench Benchmark Analysis Reports

    This page provides links to benchmark analysis reports for different ProteoBench modules.
    Each report analyzes benchmark metrics across proteomics software tools for a specific
    instrument type and acquisition mode.

    ---

    ## DDA (Data-Dependent Acquisition) Modules

    ### Ion-Level Analysis
    {dda_ion_links}

    ### Peptidoform-Level Analysis
    {dda_peptidoform_links}

    ---

    ## DIA (Data-Independent Acquisition) Modules

    ### Ion-Level Analysis
    {dia_ion_links}

    ### Peptidoform-Level Analysis
    {dia_peptidoform_links}

    ---

    ## About These Reports

    Each benchmark report includes:

    - **Epsilon Metrics (Accuracy)**: Deviation from expected ratio - measures how close measurements are to theoretical values
    - **Epsilon Precision Metrics (Consistency)**: Deviation from empirical center - measures how tightly grouped measurements are
    - **ROC-AUC Metrics**: Measures separation of changed vs unchanged species
    - **CV Metrics**: Coefficient of variation at different quantiles (median, Q75, Q90, Q95)
    - **Per-Species Analysis**: Accuracy vs precision breakdown, bias distribution, and reduction analysis by species

    ---

    *Generated from [ProteoBench](https://proteobench.cubimed.rub.de/) benchmark data*
    """
    )
    return (
        dda_ion_links,
        dda_peptidoform_links,
        dia_ion_links,
        dia_peptidoform_links,
        format_module_link,
    )


if __name__ == "__main__":
    app.run()
