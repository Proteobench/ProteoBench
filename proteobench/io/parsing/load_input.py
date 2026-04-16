"""
Load vendor tool output files into raw DataFrames.

Each ``_load_*`` function handles one tool's output format.
``load_input_file()`` dispatches to the correct loader based on the format string.
"""

import os
import re
import warnings

import pandas as pd

from .proforma import aggregate_modification_column, aggregate_modification_sites_column


def load_input_file(input_csv: str, input_format: str, input_csv_secondary: str = None) -> pd.DataFrame:
    """
    Load a dataframe from a CSV file depending on its format.

    Parameters
    ----------
    input_csv : str
        The path to the CSV file.
    input_format : str
        The format of the input file (e.g., "MaxQuant", "AlphaPept", etc.).
    input_csv_secondary : str, optional
        The path to a secondary CSV file (used for some formats like AlphaDIA).

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    try:
        if input_format == "MaxQuant":
            warnings.warn(
                """
                WARNING: MaxQuant proforma parsing does not take into account fixed modifications\n
                because they are implicit. Only after providing the appropriate parameter file,\n
                fixed modifications will be added correctly.
                """
            )
        load_function = _LOAD_FUNCTIONS[input_format]
    except KeyError as e:
        raise ValueError(f"Invalid input format: {input_format}") from e

    # For AlphaDIA, pass the secondary file if provided
    if input_format == "AlphaDIA" and input_csv_secondary:
        return load_function(input_csv, input_csv_secondary)

    return load_function(input_csv)


def _load_maxquant(input_csv: str) -> pd.DataFrame:
    """
    Load a MaxQuant output file.

    Parameters
    ----------
    input_csv : str
        The path to the MaxQuant output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    return pd.read_csv(input_csv, sep="\t", low_memory=False)


def _load_alphapept(input_csv: str) -> pd.DataFrame:
    """
    Load a AlphaPept output file.

    Parameters
    ----------
    input_csv : str
        The path to the AlphaPept output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    return pd.read_csv(input_csv, low_memory=False, dtype={"charge": int})


def _load_sage(input_csv: str) -> pd.DataFrame:
    """
    Load a Sage output file.

    Parameters
    ----------
    input_csv : str
        The path to the Sage output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    return pd.read_csv(input_csv, sep="\t", low_memory=False)


def _load_fragpipe(input_csv: str) -> pd.DataFrame:
    """
    Load a FragPipe output file.

    Parameters
    ----------
    input_csv : str
        The path to the FragPipe output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    input_data_frame["Protein"] = input_data_frame["Protein"] + "," + input_data_frame["Mapped Proteins"].fillna("")
    return input_data_frame


def _load_wombat(input_csv: str) -> pd.DataFrame:
    """
    Load a WOMBAT output file.

    Parameters
    ----------
    input_csv : str
        The path to the WOMBAT output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep=",")
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()

    non_strings = input_data_frame["protein_group"][
        ~input_data_frame["protein_group"].apply(lambda x: isinstance(x, str))
    ]

    input_data_frame["protein_group"] = input_data_frame["protein_group"].map(
        lambda x: ";".join([mapper[protein] if protein in mapper.keys() else protein for protein in x.split(",")])
    )
    input_data_frame["proforma"] = input_data_frame["modified_peptide"]
    return input_data_frame


def _load_prolinestudio_msangel(input_csv: str) -> pd.DataFrame:
    """
    Load a MSAngel/ProlineStudio output file.

    Parameters
    ----------
    input_csv : str
        The path to the MSAngel/ProlineStudio output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_excel(
        input_csv, sheet_name="Quantified peptide ions", header=0, index_col=None, engine="calamine"
    )
    input_data_frame["modifications"] = input_data_frame["modifications"].fillna("")
    input_data_frame["subsets_accessions"] = input_data_frame["subsets_accessions"].fillna("")
    input_data_frame["proforma"] = input_data_frame.apply(
        lambda x: aggregate_modification_column(x.sequence, x.modifications),
        axis=1,
    )
    # combine the sameset and subset accessions:
    # first combine the accessions:
    input_data_frame["proteins"] = input_data_frame["samesets_accessions"] + input_data_frame[
        "subsets_accessions"
    ].apply(lambda x: "; " + x if len(x) > 0 else "")
    # then sort the unique accessions:
    input_data_frame["proteins"] = input_data_frame["proteins"].apply(lambda x: "; ".join(sorted(x.split("; "))))
    # drop the duplicates:
    input_data_frame.drop_duplicates(subset=["proforma", "master_quant_peptide_ion_charge", "proteins"], inplace=True)
    # combine the duplicated precursor ions because proline reports one row per precursor + accession:
    group_cols = ["proforma", "master_quant_peptide_ion_charge"]
    agg_funcs = {col: "first" for col in input_data_frame.columns if col not in group_cols + ["proteins"]}
    input_data_frame = (
        input_data_frame.groupby(group_cols).agg({"proteins": lambda x: "; ".join(x), **agg_funcs}).reset_index()
    )
    return input_data_frame


def _load_i2masschroq(input_csv: str) -> pd.DataFrame:
    """
    Load a i2MassChroQ output file.

    Parameters
    ----------
    input_csv : str
        The path to the i2MassChroQ output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    input_data_frame["proforma"] = input_data_frame["ProForma"]
    return input_data_frame


def _load_custom(input_csv: str) -> pd.DataFrame:
    """
    Load a custom output file.

    Parameters
    ----------
    input_csv : str
        The path to the custom output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    input_data_frame["proforma"] = input_data_frame["Modified sequence"]
    return input_data_frame


def _load_diann(input_csv: str) -> pd.DataFrame:
    """
    Load a DIA-NN output file.

    Parameters
    ----------
    input_csv : str
        The path to the DIA-NN output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    if isinstance(input_csv, str):
        filename = input_csv
    else:  # streamlit OpenedFile object
        filename = input_csv.name
    if filename.endswith(".parquet"):
        input_data_frame = pd.read_parquet(input_csv)
    else:
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")

    # Map gene names to descriptions
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()

    input_data_frame["Protein.Ids"] = input_data_frame["Protein.Ids"].map(
        lambda x: ";".join([mapper[protein] if protein in mapper.keys() else protein for protein in x.split(";")])
    )
    return input_data_frame


def _merge_alphadia_files(
    input_csv: str, input_csv_secondary: str, file1_sample: pd.DataFrame, file2_sample: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge two AlphaDIA files (precursor.matrix.tsv and precursors.tsv).

    This function automatically detects which file is the matrix (wide format) and which is
    the long format based on the presence of required metadata columns.

    Parameters
    ----------
    input_csv : str
        The path to the first AlphaDIA output file.
    input_csv_secondary : str
        The path to the second AlphaDIA output file.
    file1_sample : pd.DataFrame
        A sample (first few rows) of the first file for column detection.
    file2_sample : pd.DataFrame
        A sample (first few rows) of the second file for column detection.

    Returns
    -------
    pd.DataFrame
        The merged dataframe with precursor information.

    Raises
    ------
    ValueError
        If the files cannot be identified or merged correctly.
    """
    # Required columns for the merge
    required_merge_columns = [
        "genes",
        "decoy",
        "mods",
        "mod_sites",
        "sequence",
        "charge",
        "mod_seq_charge_hash",
    ]

    # Detect which file is the matrix (wide format) and which is long format
    file1_cols = set(file1_sample.columns)
    file2_cols = set(file2_sample.columns)

    # Check which file has the required columns for merge
    file1_has_required = all(col in file1_cols for col in required_merge_columns)
    file2_has_required = all(col in file2_cols for col in required_merge_columns)

    # Determine which file is the long format
    if file1_has_required and not file2_has_required:
        # file1 is long format (precursors.tsv), file2 is matrix
        precursors_long = pd.read_csv(
            input_csv, low_memory=False, sep="\t", dtype={"mod_seq_charge_hash": str}, header=0
        )
        precursor_matrix = pd.read_csv(
            input_csv_secondary, low_memory=False, sep="\t", dtype={"mod_seq_charge_hash": str}, header=0
        )
    elif file2_has_required:
        # file2 is long format (precursors.tsv), file1 is matrix
        precursor_matrix = pd.read_csv(
            input_csv, low_memory=False, sep="\t", dtype={"mod_seq_charge_hash": str}, header=0
        )
        precursors_long = pd.read_csv(
            input_csv_secondary, low_memory=False, sep="\t", dtype={"mod_seq_charge_hash": str}, header=0
        )
    else:
        # Neither file has the required columns
        raise ValueError(
            f"Cannot identify the correct AlphaDIA files. Neither file contains all required columns: "
            f"{', '.join(required_merge_columns)}. "
            f"File 1 columns: {', '.join(sorted(file1_cols)[:10])}... "
            f"File 2 columns: {', '.join(sorted(file2_cols)[:10])}... "
            f"Please ensure you are uploading both precursor.matrix.tsv and precursors.tsv files from AlphaDIA output."
        )

    # Select only the columns that exist in precursors_long
    available_merge_columns = [col for col in required_merge_columns if col in precursors_long.columns]

    if not available_merge_columns or "mod_seq_charge_hash" not in available_merge_columns:
        raise ValueError(
            f"Cannot merge AlphaDIA files. The long format file is missing required columns. "
            f"Required: {', '.join(required_merge_columns)}. "
            f"Available in long format: {', '.join(available_merge_columns)}. "
            f"All columns in long format: {', '.join(list(precursors_long.columns)[:20])}. "
            f"Please ensure you are uploading the correct precursors.tsv file."
        )

    # Merge the matrix with precursor info
    merged_df = pd.merge(
        precursor_matrix, precursors_long[available_merge_columns], on="mod_seq_charge_hash", how="left"
    )
    # Remove duplicates that might result from the merge
    merged_df.drop_duplicates(inplace=True)

    return merged_df


def _load_alphadia(input_csv: str, input_csv_secondary: str = None) -> pd.DataFrame:
    """
    Load AlphaDIA output files.

    Parameters
    ----------
    input_csv : str
        The path to one of the AlphaDIA output files.
    input_csv_secondary : str, optional
        The path to the second AlphaDIA output file.
        If provided, the system will automatically detect which file is the precursor.matrix.tsv
        and which is the precursors.tsv (long format), then merge them.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    v1 = False
    # If secondary file is provided, detect which is which and merge
    if input_csv_secondary:
        # Read samples from both files to detect their structure
        file1_sample = pd.read_csv(
            input_csv, low_memory=False, sep="\t", dtype={"mod_seq_charge_hash": str}, nrows=5, header=0
        )
        file2_sample = pd.read_csv(
            input_csv_secondary, low_memory=False, sep="\t", dtype={"mod_seq_charge_hash": str}, nrows=5, header=0
        )

        # Reset file pointers to beginning (only if they're file objects, not path strings)
        if hasattr(input_csv, "seek"):
            input_csv.seek(0)
        if hasattr(input_csv_secondary, "seek"):
            input_csv_secondary.seek(0)

        # Merge the two files using the helper function
        input_data_frame = _merge_alphadia_files(input_csv, input_csv_secondary, file1_sample, file2_sample)
    else:
        # Use the single file directly if no secondary file provided
        # Check file extension first for parquet
        if isinstance(input_csv, str) and input_csv.lower().endswith(".parquet"):
            input_data_frame = pd.read_parquet(input_csv)
        else:
            try:
                input_data_frame = pd.read_csv(
                    input_csv,
                    low_memory=False,
                    sep="\t",
                    dtype={"mod_seq_charge_hash": str, "precursor.mod_seq_charge_hash": str},
                    header=0,
                )
            except UnicodeDecodeError:  # Parquet input, possible from AlphaDIA v2
                input_data_frame = pd.read_parquet(input_csv)

    # Map gene names to descriptions
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()
    if "pg.genes" not in input_data_frame.columns:  # AlphaDIA v1
        v1 = True
        gene_column = "genes"
    else:
        gene_column = "pg.genes"

    input_data_frame["genes"] = input_data_frame[gene_column].map(
        lambda x: ";".join([mapper[protein] if protein in mapper.keys() else protein for protein in x.split(";")])
    )

    if not v1:
        # AlphaDIA v2: Rename columns first
        input_data_frame.rename(
            columns={
                "precursor.sequence": "sequence",
                "precursor.mods": "mods",
                "precursor.mod_sites": "mod_sites",
                "precursor.charge": "charge",
                "precursor.intensity": "Intensity",
            },
            inplace=True,
        )
        input_data_frame = input_data_frame.dropna(subset=["Intensity"])

        # If data is in long format (has raw.name column), convert to wide format
        if "raw.name" in input_data_frame.columns:
            # Define columns to keep as identifiers (not pivot)
            id_columns = ["sequence", "mods", "mod_sites", "charge", "genes"]

            # Pivot from long to wide format
            input_data_frame = input_data_frame.pivot_table(
                index=id_columns,
                columns="raw.name",
                values="Intensity",
                aggfunc="first",  # Use first value if duplicates exist
            ).reset_index()

            # Flatten column names after pivot
            input_data_frame.columns.name = None

    # For v1 or v2 TSV (already in wide format), generate proforma notation
    input_data_frame["proforma"] = input_data_frame.apply(
        lambda x: aggregate_modification_sites_column(x.sequence, x.mods, x.mod_sites),
        axis=1,
    )

    return input_data_frame


def _load_fragpipe_diann_quant(input_csv: str) -> pd.DataFrame:
    """
    Load a FragPipe (DIA-NN) output file.

    Parameters
    ----------
    input_csv : str
        The path to the FragPipe (DIA-NN) output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    if "All Mapped Proteins" in input_data_frame.columns:
        input_data_frame["Protein.Ids"] = input_data_frame["All Mapped Proteins"]
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()
    # Map Protein.Ids (gene names) to species-suffixed descriptions (e.g. "sp|Q86U42|PABP2_HUMAN").
    input_data_frame["Protein.Ids"] = input_data_frame["Protein.Ids"].map(
        lambda x: ";".join([mapper.get(p, p) for p in x.split(";")]) if isinstance(x, str) else x
    )
    return input_data_frame


def _load_spectronaut(input_csv: str) -> pd.DataFrame:
    """
    Load a Spectronaut output file.

    Parameters
    ----------
    input_csv : str
        The path to the Spectronaut output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")

    if input_data_frame["FG.Quantity"].dtype == object:
        try:
            input_csv.seek(0)
        except AttributeError:
            # if input_csv is a PathPosix object, it does not have a seek method
            # This can occur when the io util functions are used.
            # Should probably be fixed some way in the future
            pass
        input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t", decimal=",")
    input_data_frame["FG.LabeledSequence"] = input_data_frame["FG.LabeledSequence"].str.strip("_")
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()
    input_data_frame["PG.ProteinGroups"] = input_data_frame["PG.ProteinGroups"].str.split(";")
    input_data_frame["PG.ProteinGroups"] = input_data_frame["PG.ProteinGroups"].map(
        lambda x: [mapper[protein] if protein in mapper.keys() else protein for protein in x]
    )
    input_data_frame["PG.ProteinGroups"] = input_data_frame["PG.ProteinGroups"].str.join(";")
    return input_data_frame


def _load_metamorpheus(input_csv: str) -> pd.DataFrame:
    """
    Load a MetaMorpheus output file (FlashLFQ: AllQuantifiedPeaks.tsv).

    Parameters
    ----------
    input_csv : str
        The path to the MetaMorpheus output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    mapper_path = os.path.join(os.path.dirname(__file__), "io_parse_settings/mapper.csv")
    mapper_df = pd.read_csv(mapper_path).set_index("gene_name")
    mapper = mapper_df["description"].to_dict()
    input_data_frame["Proteins"] = input_data_frame["Protein Group"].map(
        lambda x: ";".join([mapper.get(protein, protein) for protein in x.split(";")])
    )
    # TODO: discuss how to handle multiple mapped precursors
    input_data_frame = input_data_frame[input_data_frame["Full Sequences Mapped"] == 1]
    return input_data_frame


def _load_msaid(input_csv: str) -> pd.DataFrame:
    """
    Load a MSAID output file.

    Parameters
    ----------
    input_csv : str
        The path to the MSAID output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    return pd.read_csv(input_csv, low_memory=False, sep="\t")


def _load_peaks(input_csv: str) -> pd.DataFrame:
    """
    Load a PEAKS output file.

    Parameters
    ----------
    input_csv : str
        The path to the PEAKS output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    df = pd.read_csv(input_csv, low_memory=False, sep=",")
    # Strip .raw or .mzML suffixes that PEAKS may add to sample names (e.g. "Sample.raw Normalized Area")
    df.columns = [re.sub(r"\.(raw|mzML)(\s)", r"\2", c) for c in df.columns]
    return df


def _load_quantms(input_csv: str) -> pd.DataFrame:
    """
    Load a QuantMS output file.

    Parameters
    ----------
    input_csv : str
        The path to the QuantMS output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False)
    input_data_frame = input_data_frame.assign(
        proforma=input_data_frame["PeptideSequence"].str.replace(
            r"\(([^)]+)\)",
            r"",
            regex=True,
        ),
    )
    input_data_frame["Sequence"] = input_data_frame["PeptideSequence"].str.replace(r"\(([^)]+)\)", r"", regex=True)
    return input_data_frame


def _load_proteome_discoverer(input_csv: str) -> pd.DataFrame:
    """
    Load a Proteome Discoverer output file.

    Parameters
    ----------
    input_csv : str
        The path to the Proteome Discoverer output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_csv, low_memory=False, sep="\t")
    input_data_frame["Modifications"].fillna("", inplace=True)
    input_data_frame["proforma"] = input_data_frame.apply(
        lambda x: aggregate_modification_column(x["Sequence"], x["Modifications"]),
        axis=1,
    )
    return input_data_frame


_LOAD_FUNCTIONS = {
    "MaxQuant": _load_maxquant,
    "AlphaPept": _load_alphapept,
    "Sage": _load_sage,
    "FragPipe": _load_fragpipe,
    "WOMBAT": _load_wombat,
    "ProlineStudio": _load_prolinestudio_msangel,
    "MSAngel": _load_prolinestudio_msangel,
    "i2MassChroQ": _load_i2masschroq,
    "Custom": _load_custom,
    "DIA-NN": _load_diann,
    "AlphaDIA": _load_alphadia,
    "FragPipe (DIA-NN quant)": _load_fragpipe_diann_quant,
    "Spectronaut": _load_spectronaut,
    "MSAID": _load_msaid,
    "PEAKS": _load_peaks,
    "quantms": _load_quantms,
    "MetaMorpheus": _load_metamorpheus,
    "Proteome Discoverer": _load_proteome_discoverer,
}
