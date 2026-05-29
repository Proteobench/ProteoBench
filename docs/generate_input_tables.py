"""Generate input files tables in module documentation from [upload_info] TOML data.

Run from the docs/ directory:
    python generate_input_tables.py
"""

from pathlib import Path

import toml

SETTINGS_ROOT = Path(__file__).resolve().parent.parent / "proteobench" / "io" / "parsing" / "io_parse_settings"
PARSE_SETTINGS_FILES_TOML = SETTINGS_ROOT / "parse_settings_files.toml"
DOCS_ROOT = Path(__file__).resolve().parent / "available-modules" / "active-modules"

# Relative paths under SETTINGS_ROOT — mirrors proteobench/modules/constants.py
_MODULE_SETTINGS_SUBDIRS = {
    "quant_lfq_DDA_ion_QExactive": "Quant/lfq/DDA/ion/QExactive",
    "quant_lfq_DDA_ion_Astral": "Quant/lfq/DDA/ion/Astral",
    "quant_lfq_DDA_peptidoform": "Quant/lfq/DDA/peptidoform",
    "quant_lfq_DIA_ion_diaPASEF": "Quant/lfq/DIA/ion/diaPASEF",
    "quant_lfq_DIA_ion_Astral": "Quant/lfq/DIA/ion/Astral",
    "quant_lfq_DIA_ion_ZenoTOF": "Quant/lfq/DIA/ion/ZenoTOF",
    "quant_lfq_DIA_ion_singlecell": "Quant/lfq/DIA/ion/singlecell",
    "quant_lfq_DIA_ion_plasma": "Quant/lfq/DIA/ion/plasma",
    "denovo_DDA_HCD": "denovo/DDA/HCD",
}

MODULE_DOC_CONFIG = {
    "quant_lfq_DDA_ion_QExactive": {
        "doc_file": "2-quant-lfq-ion-dda.md",
        "table_marker": "Table 2. Overview of input files",
        "col_input": "Input file",
        "col_params": "Parameter File",
    },
    "quant_lfq_DDA_ion_Astral": {
        "doc_file": "8-quant-lfq-ion-dda-Astral.md",
        "table_marker": "Table 2. Overview of input files",
        "col_input": "Input file",
        "col_params": "Parameter File",
    },
    "quant_lfq_DDA_peptidoform": {
        "doc_file": "3-quant-lfq-peptidoform-dda.md",
        "table_marker": "Table 2. Overview of input files",
        "col_input": "Input file",
        "col_params": "Parameter File",
    },
    "quant_lfq_DIA_ion_diaPASEF": {
        "doc_file": "5-quant-lfq-ion-dia-diapasef.md",
        "table_marker": "Table 2. Overview of input files",
        "col_input": "Input file",
        "col_params": "Parameter File",
    },
    "quant_lfq_DIA_ion_Astral": {
        "doc_file": "7-quant-lfq-ion-dia-Astral_2Th.md",
        "table_marker": "Table 2. Overview of input files",
        "col_input": "Input file",
        "col_params": "Parameter File",
    },
    "quant_lfq_DIA_ion_ZenoTOF": {
        "doc_file": "10-quant-lfq-ion-dia-ZenoTOF.md",
        "table_marker": "Table 2. Overview of input files",
        "col_input": "Input file",
        "col_params": "Parameter File",
    },
    "quant_lfq_DIA_ion_singlecell": {
        "doc_file": "9-quant-lfq-ion-dia-singlecell.md",
        "table_marker": "Table 2. Overview of input files",
        "col_input": "Input file",
        "col_params": "Parameter File",
    },
    "quant_lfq_DIA_ion_plasma": {
        "doc_file": "12-quant-lfq-ion-dia-plasma.md",
        "table_marker": "Tool-specific input files",
        "col_input": "Quantification input",
        "col_params": "Metadata / parameter file",
    },
    "denovo_DDA_HCD": {
        "doc_file": "11-denovo-dda-hcd.md",
        "table_marker": "Table 2. Overview of input files",
        "col_input": "Input file",
        "col_params": "Parameter File",
    },
}


def get_upload_info(tool_name: str, toml_path: Path) -> dict:
    data = toml.load(toml_path)
    base = data.get("upload_info", {})
    override = data.get("upload_info_overrides", {}).get(tool_name, {})
    return {**base, **override}


def generate_table(tools_data: list, col_input: str, col_params: str) -> str:
    header = f"| Tool | {col_input} | {col_params} |"
    separator = "|---|---|---|"
    rows = [f"| {name} | {inp} | {par} |" for name, inp, par in tools_data if inp]
    return "\n".join([header, separator] + rows)


def replace_table_in_markdown(md_text: str, table_marker: str, new_table: str) -> str:
    lines = md_text.split("\n")

    marker_idx = next((i for i, line in enumerate(lines) if table_marker in line), None)
    if marker_idx is None:
        raise ValueError(f"Table marker '{table_marker}' not found")

    table_start = next((i for i in range(marker_idx + 1, len(lines)) if lines[i].startswith("|")), None)
    if table_start is None:
        raise ValueError(f"No table found after marker '{table_marker}'")

    table_end = table_start
    for i in range(table_start, len(lines)):
        if lines[i].startswith("|"):
            table_end = i
        else:
            break

    new_lines = lines[:table_start] + new_table.split("\n") + lines[table_end + 1 :]
    return "\n".join(new_lines)


def main() -> None:
    parse_settings_files = toml.load(PARSE_SETTINGS_FILES_TOML)

    for module_id, config in MODULE_DOC_CONFIG.items():
        tool_to_toml = parse_settings_files.get(module_id, {})
        settings_dir = SETTINGS_ROOT / _MODULE_SETTINGS_SUBDIRS[module_id]

        tools_data = []
        for tool_name in sorted(tool_to_toml.keys()):
            toml_filename = tool_to_toml[tool_name]
            toml_path = settings_dir / toml_filename
            info = get_upload_info(tool_name, toml_path)
            tools_data.append((tool_name, info.get("datapoint_file", ""), info.get("params_file", "")))

        new_table = generate_table(tools_data, config["col_input"], config["col_params"])

        doc_path = DOCS_ROOT / config["doc_file"]
        original = doc_path.read_text(encoding="utf-8")
        updated = replace_table_in_markdown(original, config["table_marker"], new_table)

        if updated != original:
            doc_path.write_text(updated, encoding="utf-8")
            print(f"Updated: {config['doc_file']}")
        else:
            print(f"Unchanged: {config['doc_file']}")


if __name__ == "__main__":
    main()
