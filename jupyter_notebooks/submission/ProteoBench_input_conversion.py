import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import pandas as pd

    return (pd,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This Jupyter Notebook serves to prepare ProteoBench inputs from software tool outputs that have important information, needed by ProteoBench, in more than one file
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # MSAID output preparation
    """)
    return


@app.cell
def _():
    # Change paths to your local paths
    input_path = "./path/to/your/MSAID/output/dir/"  # path should contain the proteingroups.tsv and precursors.tsv files
    output_path = "./path/to/your/desired/output/dir/"  # path where the output files will be saved
    return input_path, output_path


@app.cell
def _(input_path, pd):
    # Change the path to your proteingroups.tsv and precursors.tsv files
    protein_file = pd.read_csv(input_path + "proteingroups.tsv", sep="\t")
    precursor_file = pd.read_csv(input_path + "precursors.tsv", sep="\t")
    return precursor_file, protein_file


@app.function
# Map the proteins to the precursors using the "PROTEIN_IDS" column in the precursor file
def add_fasta_headers(prec_df, protein_df):
    # Create a dictionary from the second DataFrame for fast look-up
    protein_to_header = dict(zip(protein_df["PROTEIN_IDS"], protein_df["FASTA_HEADERS"]))

    # Function to find and join headers for each PROTEIN_IDS entry
    def get_fasta_headers(protein_ids):
        ids = protein_ids.split(";")  # Split the IDs by the separator
        headers = [protein_to_header.get(protein_id.strip(), "") for protein_id in ids]
        headers = [header for header in headers if header]  # Remove empty headers
        return "; ".join(headers) if headers else None

    # Apply the function to the PROTEIN_IDS column and create a new FASTA_HEADERS column
    prec_df["FASTA_HEADERS"] = prec_df["PROTEIN_IDS"].apply(get_fasta_headers)

    return prec_df


@app.cell
def _(precursor_file, protein_file):
    prec_df_with_headers = add_fasta_headers(precursor_file, protein_file)
    return (prec_df_with_headers,)


@app.cell
def _(output_path, prec_df_with_headers):
    # Change the path to the output file
    prec_df_with_headers.to_csv(
        output_path + "precursors_with_headers.tsv", sep="\t", index=False
    )  # This file can be uploaded to ProteoBench
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # AlphaDIA output preparation
    """)
    return


@app.cell
def _():
    input_path_1 = '/path/to/your/AlphaDIA/output/dir'
    output_path_1 = '/path/to/your/desired/output/path'  # path should contain the precursors.tsv file and the precursor.matrix.tsv file  # path where the output files will be saved
    return input_path_1, output_path_1


@app.cell
def _(input_path_1, pd):
    precursors_long = pd.read_csv(input_path_1 + 'precursors.tsv', sep='\t', dtype={'mod_seq_charge_hash': str})
    precursor_matrix = pd.read_csv(input_path_1 + 'precursor.matrix.tsv', sep='\t', dtype={'mod_seq_charge_hash': str})
    return precursor_matrix, precursors_long


@app.cell
def _(pd, precursor_matrix, precursors_long):
    precursor_matrix_with_precursor_info = pd.merge(
        precursor_matrix,
        precursors_long[["genes", "decoy", "mods", "mod_sites", "sequence", "charge", "mod_seq_charge_hash"]],
        on="mod_seq_charge_hash",
    )
    precursor_matrix_with_precursor_info.drop_duplicates(inplace=True)
    return (precursor_matrix_with_precursor_info,)


@app.cell
def _(output_path_1, precursor_matrix_with_precursor_info):
    precursor_matrix_with_precursor_info.to_csv(output_path_1 + 'precursor_matrix_with_precursor_info_fixed.tsv', sep='\t', index=False)  # This file can be uploaded to ProteoBench
    return


if __name__ == "__main__":
    app.run()
