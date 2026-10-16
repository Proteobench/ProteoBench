"""
Constants for the proteobench modules.
"""

import pathlib

IO_PARSE_SETTINGS_DIR = pathlib.Path(__file__) / ".." / ".." / "io" / "parsing" / "io_parse_settings"
QUANT_LFQ_SETTINGS_DIR = (IO_PARSE_SETTINGS_DIR / "Quant" / "lfq").resolve()
DENOVO_SETTINGS_DIR = (IO_PARSE_SETTINGS_DIR / "denovo").resolve()
ENTRAPMENT_SETTINGS_DIR = (IO_PARSE_SETTINGS_DIR / "entrapment").resolve()

MODULE_SETTINGS_DIRS = {
    "denovo_DDA_HCD": (DENOVO_SETTINGS_DIR / "DDA" / "HCD").as_posix(),
    "quant_lfq_DIA_ion_plasma": (QUANT_LFQ_SETTINGS_DIR / "DIA" / "ion" / "plasma").as_posix(),
    "entrapment_DIA_ion_Astral": (ENTRAPMENT_SETTINGS_DIR / "DIA" / "ion" / "Astral").as_posix(),
}
