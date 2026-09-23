"""UI settings for APB-backed HYE/HY quant modules.

This is plot and upload metadata, not a vendor parser. Software choices are
deliberately limited to result formats exercised with parameter-free APB rules.
"""

from __future__ import annotations

from apb_proteobench.configuration.load import load_packaged_module


_MODULE_NAMES = {
    "quant_lfq_DDA_ion_QExactive": "dda_qexactive",
    "quant_lfq_DDA_ion_Astral": "dda_astral",
    "quant_lfq_DDA_peptidoform": "dda_peptidoform",
    "quant_lfq_DIA_ion_AIF": "dia_aif",
    "quant_lfq_DIA_ion_Astral": "dia_astral",
    "quant_lfq_DIA_ion_diaPASEF": "dia_diapasef",
    "quant_lfq_DIA_ion_lowinput": "dia_singlecell",
    "quant_lfq_DIA_ion_ZenoTOF": "dia_zenotof",
}
APB_QUANT_MODULE_IDS = frozenset(_MODULE_NAMES)

# Every entry has a real ProteoBench or APB corpus result that parsed and scored
# with no parameter file. Add vendors here only with a matching regression.
_VERIFIED_INPUTS = {
    "dda_qexactive": ("Custom", "MaxQuant", "FragPipe", "MSAngel", "quantms", "WOMBAT"),
    "dda_astral": ("FragPipe",),
    "dda_peptidoform": ("WOMBAT",),
    "dia_aif": ("AlphaDIA", "MaxQuant", "FragPipe"),
    "dia_astral": ("AlphaDIA",),
    "dia_diapasef": ("PEAKS",),
    "dia_singlecell": ("AlphaDIA",),
    "dia_zenotof": ("PEAKS",),
}


class APBQuantSettingsBuilder:
    """Expose APB module ratios and verified producers to the existing quant UI."""

    supports_secondary_result_upload = False  # No fixture verifies AlphaDIA v1's two-file output yet.

    def __init__(self, parse_settings_dir: str, module_id: str) -> None:
        del parse_settings_dir  # Shared UI constructor contract; APB has packaged settings.
        self.module = load_packaged_module(_MODULE_NAMES[module_id])
        self.INPUT_FORMATS = list(_VERIFIED_INPUTS[self.module.source.name.removesuffix(".toml")])

    def build_parser(self, input_format: str) -> APBQuantSettingsBuilder:
        """Return plot settings for a producer already checked by the upload menu."""
        if input_format not in self.INPUT_FORMATS:
            raise ValueError(f"{input_format!r} is not verified for this APB quant module")
        return self

    def species_expected_ratio(self) -> dict[str, dict[str, str | float]]:
        """Return ratios and colors from APB's packaged module document."""
        return {
            species: ratio.model_dump(mode="json", by_alias=True, exclude_none=True)
            for species, ratio in self.module.settings.species_expected_ratio.items()
        }

    def get_upload_info(self, input_format: str) -> dict[str, str]:
        """Describe APB's raw-result upload without reading legacy tool TOMLs."""
        if input_format not in self.INPUT_FORMATS:
            return {}
        return {
            "datapoint_file_description": (
                f"Upload the {input_format} quantification result. APB selects its rule "
                "from the software name and file structure; search parameters are not required."
            ),
            "params_file_description": (
                "Optional for private benchmarking; upload search parameters before public submission."
            ),
        }
