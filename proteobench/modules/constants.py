"""
Constants for the proteobench modules.
"""

import pathlib

IO_PARSE_SETTINGS_DIR = pathlib.Path(__file__) / ".." / ".." / "io" / "parsing" / "io_parse_settings"
QUANT_LFQ_SETTINGS_DIR = (IO_PARSE_SETTINGS_DIR / "Quant" / "lfq").resolve()

MODULE_SETTINGS_DIRS = {
    "quant_lfq_DIA_ion_AIF": (QUANT_LFQ_SETTINGS_DIR / "DIA" / "ion" / "AIF").as_posix(),
    "quant_lfq_DIA_ion_diaPASEF": (QUANT_LFQ_SETTINGS_DIR / "DIA" / "ion" / "diaPASEF").as_posix(),
    "quant_lfq_DIA_ion_singlecell": (QUANT_LFQ_SETTINGS_DIR / "DIA" / "ion" / "singlecell").as_posix(),
    "quant_lfq_DDA_ion_QExactive": (QUANT_LFQ_SETTINGS_DIR / "DDA" / "ion" / "QExactive").as_posix(),
    "quant_lfq_DDA_peptidoform": (QUANT_LFQ_SETTINGS_DIR / "DDA" / "peptidoform").as_posix(),
    "quant_lfq_DIA_ion_Astral": (QUANT_LFQ_SETTINGS_DIR / "DIA" / "ion" / "Astral").as_posix(),
    "quant_lfq_DDA_ion_Astral": (QUANT_LFQ_SETTINGS_DIR / "DDA" / "ion" / "Astral").as_posix(),
}
