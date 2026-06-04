"""
Module for parsing results data from various de novo sequencing engines.
"""

import pandas as pd
import numpy as np
from pyteomics.mztab import MzTab
import re


def load_input_file(input_path: str, input_format: str, input_secondary: str = None) -> pd.DataFrame:
    try:
        load_function = _LOAD_FUNCTIONS[input_format]
    except KeyError as e:
        raise ValueError(f"Invalid input format: {input_format}") from e
    
    if input_format == "SMSNet" and input_secondary:
        return load_function(input_path, input_secondary)

    return load_function(input_path)


def _load_adanovo(input_mztab: str) -> pd.DataFrame:
    """
    Load an AdaNovo output file.

    Parameters
    ----------
    input_mztab: str
        The path to the AdaNovo output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = MzTab(input_mztab, encoding="utf-8")
    input_data_frame = input_data_frame.spectrum_match_table
    return input_data_frame


def _load_casanovo(input_mztab: str) -> pd.DataFrame:
    """
    Load a Casanovo output file.

    Parameters
    ----------
    input_mztab: str
        The path to the Casanovo output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = MzTab(input_mztab)
    input_data_frame = input_data_frame.spectrum_match_table
    return input_data_frame


def _load_instanovo(input_csv: str) -> pd.DataFrame:
    """
    Load an InstaNovo output file.

    Parameters
    ----------
    input_csv: str
        The path to the InstaNovo output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    return pd.read_csv(input_csv, low_memory=False)


def _load_pepnet(input_csv: str) -> pd.DataFrame:
    """
    Load a PepNet output file.

    Parameters
    ----------
    input_path: str
        The path to the PepNet output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    return pd.read_csv(input_csv, sep="\t", low_memory=False)


def _load_pihelixnovo(input_path: str) -> pd.DataFrame:
    """
    Load a Pi-HelixNovo output file.

    Parameters
    ----------
    input_path: str
        The path to the Pi-HelixNovo output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    input_data_frame = pd.read_csv(input_path, sep="\t", low_memory=False, header=None)
    return input_data_frame.rename(columns={0: "0", 1: "1", 2: "2"})


def _load_piprimenovo(input_path: str) -> pd.DataFrame:
    """
    Load a Pi-PrimeNovo output file.

    Parameters
    ----------
    input_path: str
        The path to the Pi-PrimeNovo output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    return pd.read_csv(input_path, sep="\t", low_memory=False).dropna()

def _load_deepnovo(input_csv: str) -> pd.DataFrame:
    """
    Load a DeepNovo output file.

    Parameters
    ----------
    input_csv : str
        The path to the DeepNovo output file (.tab).

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    df = pd.read_csv(input_csv, sep="\t", header=0, low_memory=False)
    df['scan'] = df['scan'].apply(lambda x: int(x)-1)
    return df

def _load_pointnovo(input_csv: str) -> pd.DataFrame:
    """
    Load a PointNovo output file.

    Parameters
    ----------
    input_csv : str
        The path to the PointNovo output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    df = pd.read_csv(input_csv, sep="\t", header=0, low_memory=False)
    df['feature_id'] = df['feature_id'].apply(lambda x: int(x)-1)
    return df


def _load_smsnet(input_csv: str, input_csv_secondary: str) -> pd.DataFrame:
    """
    Load SMSNet output files.

    Parameters
    ----------
    input_csv : str
        The path to the SMSNet peptide predictions file.
    input_csv_secondary : str
        The path to the SMSNet per-AA probability file (_prob suffix).

    Returns
    -------
    pd.DataFrame
        The loaded dataframe.
    """
    with open(input_csv) as f:
        peptides = [line.rstrip().split() for line in f]

    with open(input_csv_secondary) as g:
        aa_scores = [line.rstrip().split() for line in g]
        
    peptide_list, aa_score_list = [], []
    for peptide, aa_score in zip(peptides, aa_scores):
        peptide = [i for i in peptide if i not in ['<s>']]
        peptide_list.append(peptide)
        aa_score_list.append([float(i) for i in aa_score[:len(peptide)]])

    df = pd.DataFrame({
        "sequence_list": peptide_list,
        "aa_scores": aa_score_list,
    })
    df.index = range(0, len(df))
    df = df.reset_index()

    df = df[df['sequence_list'].apply(lambda x: '<unk>' not in x)]
    df['sequence'] = df['sequence_list'].apply(lambda x: ''.join(x))
    df['peptide_score'] = df['aa_scores'].apply(np.mean)
    return df


def _load_contranovo(input_mztab: str) -> pd.DataFrame:
    """
    Load a ContraNovo output file.

    Parameters
    ----------
    input_mztab : str
        The path to the ContraNovo mztab output file.

    Returns
    -------
    pd.DataFrame
        The loaded dataframe, with invalid N-terminal modifications filtered out
        and double N-terminal modification aa_scores collapsed.
    """
    VALID_NTERM = {"+42.011", "+43.006", "-17.027", "+43.006-17.027"}
    VALID_DOUBLE_NTERM = {("+43.006", "-17.027"), ("-17.027", "+43.006")}
    def tokenize(sequence: str):
        """Tokenize sequence into N-term tokens and AA tokens."""
        sequence = str(sequence)
        nterm_tokens = []
        remaining = sequence
        while True:
            match = re.match(r'^(\+43\.006-17\.027|[+-]\d+\.\d+)', remaining)
            if not match:
                break
            nterm_tokens.append(match.group(1))
            remaining = remaining[match.end():]
        aa_tokens = re.findall(r'[A-Z](?:[+-]\d+\.\d+)?', remaining)
        return nterm_tokens, aa_tokens

    def _is_invalid(sequence: str) -> bool:
        nterm_tokens, aa_tokens = tokenize(sequence)

        # N-term mod on non-N-terminal site
        for token in aa_tokens:
            match = re.search(r'[+-]\d+\.\d+', token)
            if match and match.group() in {"+42.011", "+43.006", "-17.027"}:
                return True

        if len(nterm_tokens) == 0:
            return False
        if len(nterm_tokens) == 1:
            return nterm_tokens[0] not in VALID_NTERM
        if len(nterm_tokens) == 2:
            return tuple(nterm_tokens) not in VALID_DOUBLE_NTERM
        return True  # 3+ always invalid

    def _fix_scores(row) -> str:
        sequence = str(row["sequence"])
        scores_str = row["opt_ms_run[1]_aa_scores"]
        nterm_tokens, aa_tokens = tokenize(sequence)
        scores = [float(x) for x in scores_str.split(",")]

        # +43.006-17.027 matched as single token but was tokenized as two
        if (
            len(nterm_tokens) == 1
            and nterm_tokens[0] == "+43.006-17.027"
            and len(scores) == len(nterm_tokens) + 1 + len(aa_tokens)
        ):
            averaged = [(scores[0] + scores[1]) / 2] + scores[2:]
            return ",".join(str(x) for x in averaged)

        # -17.027+43.006 always two tokens
        if len(nterm_tokens) == 2 and tuple(nterm_tokens) in VALID_DOUBLE_NTERM:
            averaged = [(scores[0] + scores[1]) / 2] + scores[2:]
            return ",".join(str(x) for x in averaged)

        return scores_str

    df = _load_casanovo(input_mztab=input_mztab)
    df = df[df['sequence'].apply(len) != 0]
    df = df[~df["sequence"].apply(_is_invalid)]
    df["opt_ms_run[1]_aa_scores"] = df.apply(_fix_scores, axis=1)

    return df


def _load_novob(input_csv: str) -> pd.DataFrame:
    """
    Load a NovoB output file.

    Parameters
    ----------
    input_csv : str
        The path to the NovoB output file (.tsv).

    Returns
    -------
    pd.DataFrame
        The loaded dataframe with one row per spectrum, selecting the best
        scoring prediction between forward and reverse inference.
    """
    # TODO: Still to be tested
    df = pd.read_csv(input_csv, sep="\t", header=None).rename(
        columns={
            0: "Mcount",
            1: "charge",
            2: "peptide_mass",
            3: "sequence_forward",
            4: "mass_forward",
            5: "probability_forward",
            6: "sequence_reverse",
            7: "mass_reverse",
            8: "probability_reverse",
            9: "spectrum_id",
        }
    )

    # Decode spectrum_id from b'5280' to '5280'
    df["spectrum_id"] = df["spectrum_id"].apply(
        lambda x: eval(x).decode("utf-8") if isinstance(x, str) else x
    )

    # Parse sequence lists
    df["sequence_forward"] = df["sequence_forward"].apply(lambda x: eval(x)[0])
    df["sequence_reverse"] = df["sequence_reverse"].apply(lambda x: eval(x)[0])

    # Select best prediction between forward and reverse
    def select_best(row):
        if row["probability_forward"] > row["probability_reverse"]:
            return row["sequence_forward"], row["probability_forward"]
        elif row["probability_forward"] < row["probability_reverse"]:
            return row["sequence_reverse"], row["probability_reverse"]
        elif abs(row["mass_forward"]) < abs(row["mass_reverse"]):
            return row["sequence_forward"], row["probability_forward"]
        else:
            return row["sequence_reverse"], row["probability_reverse"]

    df[["sequence", "score"]] = df.apply(
        lambda x: pd.Series(select_best(x)), axis=1
    )

    return df


def _load_custom(input_path: str) -> pd.DataFrame:
    """
    Load a de novo output file in custom (generic) format.

    Parameters
    ----------
    input_path: str
        The path to the output file

    Returns
    -------
    pd.DataFrame
        The loaded dataframe
    """
    return pd.read_csv(input_path, low_memory=False)


_LOAD_FUNCTIONS = {
    "AdaNovo": _load_adanovo,
    "Casanovo": _load_casanovo,
    "ContraNovo": _load_contranovo,
    "NovoB": _load_novob,
    "DeepNovo": _load_deepnovo,
    "InstaNovo": _load_instanovo,
    "PepNet": _load_pepnet,
    "Pi-HelixNovo": _load_pihelixnovo,
    "Pi-PrimeNovo": _load_piprimenovo,
    "PointNovo": _load_pointnovo,
    "SMSNet": _load_smsnet,
    "Custom": _load_custom,
}
