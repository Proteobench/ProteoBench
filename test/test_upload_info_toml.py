"""Tests that every non-custom tool parse settings TOML contains a valid [upload_info] section."""

import os
from pathlib import Path

import pytest
import toml

from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.modules.quant.apb_settings import APBQuantSettingsBuilder

_SETTINGS_ROOT = Path(__file__).resolve().parent.parent / "proteobench" / "io" / "parsing" / "io_parse_settings"

_SKIP_NAMES = {
    "module_settings.toml",
    "parse_settings_files.toml",
    "tool_metadata.toml",
    # Custom format intentionally omitted from upload_info (graceful-handling tested separately)
    "parse_settings_custom.toml",
    "parse_settings_DIA_peptidoform.toml",
}

_UPLOAD_INFO_KEYS = ("datapoint_file", "datapoint_file_description", "params_file", "params_file_description")


def _collect_tool_tomls():
    paths = []
    for dirpath, _, filenames in os.walk(_SETTINGS_ROOT):
        for fname in filenames:
            if fname.endswith(".toml") and fname not in _SKIP_NAMES:
                paths.append(os.path.join(dirpath, fname))
    return sorted(paths)


@pytest.mark.parametrize("toml_path", _collect_tool_tomls())
def test_upload_info_present_and_non_empty(toml_path):
    """Every tool TOML (except Custom) must have [upload_info] with non-empty string values."""
    data = toml.load(toml_path)
    assert "upload_info" in data, f"Missing [upload_info] section in {toml_path}"
    info = data["upload_info"]
    for key in _UPLOAD_INFO_KEYS:
        assert key in info, f"Missing key '{key}' in [upload_info] of {toml_path}"
        assert isinstance(info[key], str), f"Key '{key}' must be a string in {toml_path}"

    # datapoint_file_description must be non-empty; params fields may be empty for de novo tools
    assert info["datapoint_file_description"], f"'datapoint_file_description' is empty in {toml_path}"
    assert info["datapoint_file"], f"'datapoint_file' is empty in {toml_path}"


@pytest.mark.parametrize("module_id,parse_dir", list(MODULE_SETTINGS_DIRS.items()))
def test_get_upload_info_returns_dict_for_known_tools(module_id, parse_dir):
    """ParseSettingsBuilder.get_upload_info returns a dict for every registered tool."""
    builder = ParseSettingsBuilder(parse_settings_dir=parse_dir, module_id=module_id)
    for input_format in builder.INPUT_FORMATS:
        result = builder.get_upload_info(input_format)
        assert isinstance(
            result, dict
        ), f"get_upload_info({input_format!r}) returned {type(result)} for module {module_id}"


def test_apb_custom_upload_info_describes_parameter_free_scoring():
    """APB describes its Custom upload without a legacy tool TOML."""
    module_id = "quant_lfq_DDA_ion_QExactive"
    builder = APBQuantSettingsBuilder("", module_id)
    result = builder.get_upload_info("Custom")
    assert "APB selects its rule" in result["datapoint_file_description"]
    assert "not required" in result["datapoint_file_description"]


_DIA_MODULES_WITH_FRAGPIPE_DIANN_QUANT = [
    module_id
    for module_id, parse_dir in MODULE_SETTINGS_DIRS.items()
    if "FragPipe (DIA-NN quant)"
    in ParseSettingsBuilder(parse_settings_dir=parse_dir, module_id=module_id).INPUT_FORMATS
]


@pytest.mark.parametrize("module_id", _DIA_MODULES_WITH_FRAGPIPE_DIANN_QUANT)
def test_get_upload_info_fragpipe_diann_quant_overrides_params(module_id):
    """FragPipe (DIA-NN quant) shares parse_settings_diann.toml but must report the FragPipe .workflow as params file in every DIA module that includes it."""
    parse_dir = MODULE_SETTINGS_DIRS[module_id]
    builder = ParseSettingsBuilder(parse_settings_dir=parse_dir, module_id=module_id)

    diann_info = builder.get_upload_info("DIA-NN")
    fp_info = builder.get_upload_info("FragPipe (DIA-NN quant)")

    # Both point to the same file types, but FragPipe's report lives in a different output folder
    assert diann_info["datapoint_file"] == fp_info["datapoint_file"]
    assert "dia-quant-output" in fp_info["datapoint_file_description"]

    # But params differ: FragPipe needs a .workflow file, not a DIA-NN log
    assert ".workflow" in fp_info["params_file_description"]
    assert "log" not in fp_info["params_file_description"].lower()
