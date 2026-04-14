# /// script
# dependencies = ["blinker"]
# ///

import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Methionine Excision Analysis Across ProteoBench Submissions

    **Related issue:** [#504 - To explore: parameter methionine excision during search](https://github.com/Proteobench/ProteoBench/issues/504)

    Some search engines remove the initiator methionine from the N-terminus of protein sequences,
    because N-terminal methionine excision (NME) is a common co-translational modification.

    This notebook analyzes all publicly submitted ProteoBench datasets to determine:
    1. Which submissions contain peptides starting with methionine at position 1 (i.e., NME was **not** applied)?
    2. Which submissions appear to have removed initiator methionines (NME **was** applied)?
    3. Is there a systematic difference between software tools?

    **Data source:** https://proteobench.cubimed.rub.de/datasets/
    """)
    return


@app.cell
def _():
    # packages added via marimo's package management: blinker !pip install blinker
    return


@app.cell
def _():
    import glob
    import io
    import os
    import zipfile
    from collections import defaultdict

    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    import requests
    from bs4 import BeautifulSoup
    from tqdm.notebook import tqdm

    from proteobench.utils.server_io import get_merged_json

    return (
        BeautifulSoup,
        defaultdict,
        get_merged_json,
        io,
        os,
        pd,
        px,
        requests,
        tqdm,
        zipfile,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Load all submission metadata

    We load the JSON results from all modules to get the mapping between `intermediate_hash`, `software_name`, and other metadata.
    """)
    return


@app.cell
def _(get_merged_json, pd):
    # Load results from all ion-level modules
    repos = {
        "DDA_ion": "https://github.com/Proteobench/Results_quant_ion_DDA/archive/refs/heads/main.zip",
        "DDA_Astral_ion": "https://github.com/Proteobench/Results_quant_ion_DDA_Astral/archive/refs/heads/main.zip",
        "DIA_AIF_ion": "https://github.com/Proteobench/Results_quant_ion_DIA/archive/refs/heads/main.zip",
        "DIA_diaPASEF_ion": "https://github.com/Proteobench/Results_quant_ion_DIA_diaPASEF/archive/refs/heads/main.zip",
        "DIA_Astral_ion": "https://github.com/Proteobench/Results_quant_ion_DIA_Astral/archive/refs/heads/main.zip",
        "DIA_ZenoTOF_ion": "https://github.com/Proteobench/Results_quant_ion_DIA_ZenoTOF/archive/refs/heads/main.zip",
    }

    all_metadata = []
    for module_name, repo_url in repos.items():
        try:
            df = get_merged_json(repo_url, write_to_file=False)
            df["module"] = module_name
            all_metadata.append(df)
            print(f"{module_name}: {len(df)} datapoints")
        except Exception as e:
            print(f"{module_name}: FAILED - {e}")

    metadata = pd.concat(all_metadata, ignore_index=True)
    print(f"\nTotal: {len(metadata)} datapoints across {metadata['module'].nunique()} modules")
    print(f"Unique hashes: {metadata['intermediate_hash'].nunique()}")
    print(f"Software tools: {sorted(metadata['software_name'].unique())}")
    return (metadata,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Download performance data from the server

    Each dataset folder on `proteobench.cubimed.rub.de/datasets/` contains a zip with `result_performance.csv`.
    The `precursor ion` column contains sequences in ProForma notation (e.g., `AAAM[Oxidation]PEPTIDEK/2`).

    We extract the bare peptide sequence and check for N-terminal methionine patterns.
    """)
    return


@app.cell
def _(BeautifulSoup, metadata, requests):
    DATASETS_BASE_URL = "https://proteobench.cubimed.rub.de/datasets/"

    def get_available_hashes():
        """Get all dataset hashes available on the server."""
        resp = requests.get(DATASETS_BASE_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return [
            a["href"].strip("/")
            for a in soup.find_all("a")
            if a["href"].endswith("/") and a["href"] != "../"
        ]

    server_hashes = get_available_hashes()
    print(f"Datasets available on server: {len(server_hashes)}")

    # Find which metadata entries have data on the server
    metadata_with_data = metadata[metadata["intermediate_hash"].isin(server_hashes)]
    print(f"Metadata entries with server data: {len(metadata_with_data)}")
    return DATASETS_BASE_URL, metadata_with_data


@app.cell
def _():
    import re

    def extract_bare_sequence(precursor_ion: str) -> str:
        """Extract the bare amino acid sequence from a ProForma precursor ion string.
    
        Examples:
            'AAAM[Oxidation]PEPTIDEK/2' -> 'AAAMEPTIDEK'  (charge removed, but keep sequence)
            'M[Acetyl]-PEPTIDEK/3'      -> 'MPEPTIDEK'
            '[Acetyl]-MPEPTIDEK/2'      -> 'MPEPTIDEK'
        """
        if not isinstance(precursor_ion, str):
            return ""
        # Remove charge state (e.g., /2, |Z=2)
        seq = re.split(r'[/|]', precursor_ion)[0]
        # Remove modifications in brackets
        seq = re.sub(r'\[.*?\]', '', seq)
        # Remove leading/trailing dashes (from N-term/C-term mods)
        seq = seq.strip('-')
        # Keep only uppercase letters (amino acids)
        seq = ''.join(c for c in seq if c.isupper())
        return seq

    # Test
    test_cases = [
        "AAAAAAALQAK/2",
        "M[Oxidation]AAAPEPTIDEK/3",
        "[Acetyl]-MPEPTIDEK/2",
        "MPEPTIDEK|Z=2",
        "AAAM[Oxidation]PEPTIDEK/2",
    ]
    for tc in test_cases:
        print(f"  {tc:40s} -> {extract_bare_sequence(tc)}")
    return (extract_bare_sequence,)


@app.cell
def _(BeautifulSoup, DATASETS_BASE_URL, io, pd, requests, zipfile):
    def load_performance_data(intermediate_hash: str) -> pd.DataFrame:
        """Download and extract result_performance.csv from the server."""
        folder_url = f"{DATASETS_BASE_URL}{intermediate_hash}/"
    
        # Find the zip file
        resp = requests.get(folder_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        zip_files = [a["href"] for a in soup.find_all("a") if a["href"].endswith(".zip")]
    
        if not zip_files:
            return None
    
        # Download the zip
        zip_url = f"{folder_url}{zip_files[0]}"
        zip_resp = requests.get(zip_url, timeout=60)
        zip_resp.raise_for_status()
    
        # Extract result_performance.csv
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z:
            if "result_performance.csv" in z.namelist():
                with z.open("result_performance.csv") as f:
                    return pd.read_csv(f)
        return None

    return (load_performance_data,)


@app.cell
def _(defaultdict, extract_bare_sequence, pd):
    def analyze_methionine_excision(perf_df: pd.DataFrame, precursor_col: str='precursor ion') -> dict:
        """Analyze a single dataset for methionine excision patterns.
    
        We look at peptides that map to the N-terminus of proteins.
        Since we don't have protein position info in the intermediate file,
        we use a heuristic: check the proportion of peptides starting with M.
    
        If NME is applied, we expect FEWER peptides starting with M
        (because the M was cleaved and the peptide starts with the 2nd residue).
    
        We also look for [Acetyl] N-term modifications, which are common
        on the residue exposed after NME.
        """
        if precursor_col not in perf_df.columns:
            for alt in ['peptidoform', 'proforma']:  # Try alternative column names
                if alt in perf_df.columns:
                    precursor_col = alt
                    break
            else:
                return None
        precursors = perf_df[precursor_col].dropna().unique()
        total = len(precursors)
        if total == 0:
            return None
        sequences = [extract_bare_sequence(p) for p in precursors]
        sequences = [s for s in sequences if len(s) > 0]
        starts_with_m = sum((1 for s in sequences if s.startswith('M')))
        pct_starts_m = starts_with_m / len(sequences) * 100 if sequences else 0
        has_nterm_acetyl = sum((1 for p in precursors if isinstance(p, str) and (p.startswith('[Acetyl]') or p.startswith('[acetyl]') or '[Acetyl]-' in p[:15])))
        pct_nterm_acetyl = has_nterm_acetyl / total * 100 if total else 0
        first_aa_counts = defaultdict(int)
        for s in sequences:  # Count sequences starting with M
            if s:
                first_aa_counts[s[0]] = first_aa_counts[s[0]] + 1
        return {'total_precursors': total, 'unique_sequences': len(sequences), 'starts_with_M': starts_with_m, 'pct_starts_M': round(pct_starts_m, 2), 'n_nterm_acetyl': has_nterm_acetyl, 'pct_nterm_acetyl': round(pct_nterm_acetyl, 2), 'first_aa_distribution': dict(first_aa_counts)}  # Count N-terminal acetylation (indicator of NME processing)  # Amino acid frequency at position 1

    return (analyze_methionine_excision,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Analyze all available datasets

    This downloads each dataset's performance CSV and checks for methionine excision patterns.
    This may take a few minutes depending on your connection.
    """)
    return


@app.cell
def _(
    analyze_methionine_excision,
    load_performance_data,
    metadata_with_data,
    pd,
    tqdm,
):
    results = []
    errors = []

    hashes_to_process = metadata_with_data["intermediate_hash"].unique()
    print(f"Processing {len(hashes_to_process)} datasets...\n")

    for h in tqdm(hashes_to_process):
        # Get metadata for this hash
        meta_row = metadata_with_data[metadata_with_data["intermediate_hash"] == h].iloc[0]
    
        try:
            perf_df = load_performance_data(h)
            if perf_df is None:
                errors.append({"hash": h, "error": "No performance data found"})
                continue
        
            analysis = analyze_methionine_excision(perf_df)
            if analysis is None:
                errors.append({"hash": h, "error": "No precursor column found"})
                continue
        
            results.append({
                "intermediate_hash": h,
                "software_name": meta_row.get("software_name", "unknown"),
                "software_version": meta_row.get("software_version", "unknown"),
                "module": meta_row.get("module", "unknown"),
                "id": meta_row.get("id", "unknown"),
                **analysis,
            })
        except Exception as e:
            errors.append({"hash": h, "error": str(e)[:100]})

    print(f"\nSuccessfully analyzed: {len(results)}")
    print(f"Errors: {len(errors)}")

    results_df = pd.DataFrame(results)
    results_df.head()
    return errors, results_df


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Results: Methionine excision across tools
    """)
    return


@app.cell
def _(display, results_df):
    # Summary by software tool
    if not results_df.empty:
        summary = results_df.groupby("software_name").agg(
            n_submissions=("id", "count"),
            mean_pct_starts_M=("pct_starts_M", "mean"),
            std_pct_starts_M=("pct_starts_M", "std"),
            min_pct_starts_M=("pct_starts_M", "min"),
            max_pct_starts_M=("pct_starts_M", "max"),
            mean_pct_nterm_acetyl=("pct_nterm_acetyl", "mean"),
        ).round(2).sort_values("mean_pct_starts_M", ascending=False)
    
        print("Percentage of precursors starting with Methionine by tool:")
        print("(Higher = more M-starting peptides = NME likely NOT applied or not relevant)")
        print()
        display(summary)
    else:
        print("No results to display.")
    return


@app.cell
def _(px, results_df):
    # Visualization: box plot of % M-starting peptides per tool
    if not results_df.empty:
        fig = px.box(
            results_df,
            x="software_name",
            y="pct_starts_M",
            color="module",
            title="Percentage of Precursors Starting with Methionine by Software Tool",
            labels={
                "pct_starts_M": "% precursors starting with M",
                "software_name": "Software Tool",
                "module": "Module",
            },
            hover_data=["id", "software_version", "total_precursors"],
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=True,
        )
        fig.show()
    return


@app.cell
def _(px, results_df):
    # Visualization: scatter of % M-starting vs total precursors
    if not results_df.empty:
        fig_1 = px.scatter(results_df, x='unique_sequences', y='pct_starts_M', color='software_name', symbol='module', title='% M-Starting Precursors vs Total Unique Sequences', labels={'unique_sequences': 'Unique Sequences', 'pct_starts_M': '% starting with M', 'software_name': 'Software Tool'}, hover_data=['id', 'software_version'], size='total_precursors', size_max=15)
        fig_1.update_layout(height=500)
        fig_1.show()
    return


@app.cell
def _(pd, px, results_df):
    # Visualization: N-terminal amino acid distribution across tools
    if not results_df.empty:
        aa_data = []  # Aggregate first AA distributions
        for _, row in results_df.iterrows():
            dist = row['first_aa_distribution']
            total = sum(dist.values())
            for aa, count in dist.items():
                aa_data.append({'software_name': row['software_name'], 'amino_acid': aa, 'percentage': count / total * 100})
        aa_df = pd.DataFrame(aa_data)
        aa_summary = aa_df.groupby(['software_name', 'amino_acid'])['percentage'].mean().reset_index()
        key_aas = ['M', 'A', 'S', 'T', 'V', 'G', 'L', 'K']
        aa_filtered = aa_summary[aa_summary['amino_acid'].isin(key_aas)]
        fig_2 = px.bar(aa_filtered, x='software_name', y='percentage', color='amino_acid', barmode='group', title='N-terminal Amino Acid Distribution by Tool (avg across submissions)', labels={'percentage': '% of sequences', 'software_name': 'Software Tool', 'amino_acid': 'First AA'})
        fig_2.update_layout(xaxis_tickangle=-45, height=500)
        fig_2.show()  # Focus on key amino acids: M (methionine), A (alanine - common after NME), S (serine)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Detailed comparison: Same module, different tools

    Let's compare tools within the same module to control for dataset effects.
    """)
    return


@app.cell
def _(display, results_df):
    if not results_df.empty:
        for module in results_df["module"].unique():
            module_df = results_df[results_df["module"] == module]
            if len(module_df) < 2:
                continue
        
            print(f"\n{'='*60}")
            print(f"Module: {module} ({len(module_df)} submissions)")
            print(f"{'='*60}")
        
            module_summary = module_df.groupby("software_name").agg(
                n=("id", "count"),
                mean_pct_M=("pct_starts_M", "mean"),
                mean_nterm_acetyl=("pct_nterm_acetyl", "mean"),
                mean_precursors=("total_precursors", "mean"),
            ).round(2).sort_values("mean_pct_M", ascending=False)
        
            display(module_summary)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. Statistical test: Is there a significant difference between tools?

    We use a Kruskal-Wallis test (non-parametric) to check if the percentage of M-starting
    peptides differs significantly between software tools.
    """)
    return


@app.cell
def _(results_df):
    from scipy import stats

    if not results_df.empty and results_df["software_name"].nunique() > 1:
        groups = [group["pct_starts_M"].values for _, group in results_df.groupby("software_name") if len(group) >= 2]
    
        if len(groups) >= 2:
            stat, p_value = stats.kruskal(*groups)
            print(f"Kruskal-Wallis test: H={stat:.2f}, p={p_value:.4e}")
            if p_value < 0.05:
                print("=> Significant difference between tools (p < 0.05)")
                print("   This suggests methionine excision handling varies across tools.")
            else:
                print("=> No significant difference between tools (p >= 0.05)")
                print("   Tools handle methionine excision similarly.")
        else:
            print("Not enough groups with >= 2 submissions for statistical test.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7. Conclusions & Recommendations

    Based on this analysis:

    1. **If tools show similar % M-starting peptides:** NME handling is consistent, and it may not need to be a tracked parameter.

    2. **If tools differ significantly:** NME should be added as a parsed parameter in ProteoBench, and users should be informed during submission.

    3. **If N-terminal acetylation patterns differ:** This could indicate that some tools are reporting NME-related modifications while others are not, which would affect quantification comparisons.

    ### Action items for issue #504:
    - [ ] If heterogeneous: add "methionine excision" as a parameter in `ProteoBenchParameters`
    - [ ] Update parameter JSON files (`quant_lfq_DDA_ion.json`, etc.)
    - [ ] Add parsing logic for each tool's parameter file
    - [ ] Consider flagging submissions where NME handling is ambiguous
    """)
    return


@app.cell
def _(errors, os, pd, results_df):
    # Save results for further analysis
    if not results_df.empty:
        output_path = "temp_results/methionine_excision_results.csv"
        os.makedirs("temp_results", exist_ok=True)
        results_df.drop(columns=["first_aa_distribution"]).to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")
    
        # Also save errors
        if errors:
            pd.DataFrame(errors).to_csv("temp_results/methionine_excision_errors.csv", index=False)
            print(f"Errors saved to temp_results/methionine_excision_errors.csv")
    return


if __name__ == "__main__":
    app.run()
