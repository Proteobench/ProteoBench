"""
Constants for the proteobench modules.
"""

import pathlib

IO_PARSE_SETTINGS_DIR = pathlib.Path(__file__) / ".." / ".." / "io" / "parsing" / "io_parse_settings"
QUANT_LFQ_SETTINGS_DIR = (IO_PARSE_SETTINGS_DIR / "Quant" / "lfq").resolve()

MODULE_SETTINGS_DIRS = {
    "quant_lfq_ion_DIA_AIF": (QUANT_LFQ_SETTINGS_DIR / "DIA" / "ion" / "AIF").as_posix(),
    "quant_lfq_ion_DIA_diaPASEF": (QUANT_LFQ_SETTINGS_DIR / "DIA" / "ion" / "diaPASEF").as_posix(),
    "quant_lfq_ion_DDA": (QUANT_LFQ_SETTINGS_DIR / "DDA" / "ion").as_posix(),
    "quant_lfq_peptidoform_DDA": (QUANT_LFQ_SETTINGS_DIR / "DDA" / "peptidoform").as_posix(),
}
