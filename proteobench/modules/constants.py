import pathlib

IO_PARSE_SETTINGS_DIR = pathlib.Path(__file__) / ".." / ".." / "io" / "parsing" / "io_parse_settings"
QUANT_LFQ_SETTINGS_DIR = (IO_PARSE_SETTINGS_DIR / "Quant" / "lfq").resolve()

MODULE_SETTINGS_DIRS = {
    "quant_lfq_ion_DIA_AIF": (QUANT_LFQ_SETTINGS_DIR / "ion" / "DIA" / "AIF").as_posix(),
    "quant_lfq_ion_DIA_diaPASEF": (QUANT_LFQ_SETTINGS_DIR / "ion" / "DIA" / "diaPASEF").as_posix(),
    "quant_lfq_ion_DDA": (QUANT_LFQ_SETTINGS_DIR / "ion" / "DDA").as_posix(),
    "quant_lfq_peptidoform_DDA": (QUANT_LFQ_SETTINGS_DIR / "peptidoform" / "DDA").as_posix(),
}
