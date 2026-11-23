"""Generate input files tables in module documentation from [upload_info] TOML data.

Run from the docs/ directory:
    python generate_input_tables.py
"""

from pathlib import Path

import toml

SETTINGS_ROOT = Path(__file__).resolve().parent.parent / "proteobench" / "io" / "parsing" / "io_parse_settings"
PARSE_SETTINGS_FILES_TOML = SETTINGS_ROOT / "parse_settings_files.toml"
DOCS_ROOT = Path(__file__).resolve().parent / "modules"

DEFAULT_MARKER = "**Table: input files required for metric calculation and public submission**"

# Relative paths under SETTINGS_ROOT — mirrors proteobench/modules/constants.py
_MODULE_SETTINGS_SUBDIRS = {
    "quant_lfq_DDA_ion_QExactive": "Quant/lfq/DDA/ion/QExactive",
    "quant_lfq_DDA_ion_Astral": "Quant/lfq/DDA/ion/Astral",
    "quant_lfq_DDA_peptidoform": "Quant/lfq/DDA/peptidoform",
    "quant_lfq_DIA_ion_AIF": "Quant/lfq/DIA/ion/AIF",
    "quant_lfq_DIA_ion_diaPASEF": "Quant/lfq/DIA/ion/diaPASEF",
    "quant_lfq_DIA_ion_Astral": "Quant/lfq/DIA/ion/Astral",
    "quant_lfq_DIA_ion_ZenoTOF": "Quant/lfq/DIA/ion/ZenoTOF",
    "quant_lfq_DIA_ion_lowinput": "Quant/lfq/DIA/ion/lowinput",
    "quant_lfq_DIA_ion_plasma": "Quant/lfq/DIA/ion/plasma",
    "denovo_DDA_HCD": "denovo/DDA/HCD",
    "entrapment_DIA_ion_Astral": "entrapment/DIA/ion/Astral",
}

# doc_file is relative to DOCS_ROOT (docs/modules/). table_marker defaults to
# DEFAULT_MARKER; only the archived AIF page uses different wording ("used" instead
# of "required", matching its "(historical reference)" section heading).
MODULE_DOC_CONFIG = {
    "quant_lfq_DDA_ion_QExactive": {"doc_file": "dda/dda-ion-qexactive.md"},
    "quant_lfq_DDA_ion_Astral": {"doc_file": "dda/dda-ion-astral.md"},
    "quant_lfq_DDA_peptidoform": {"doc_file": "dda/dda-peptidoform.md"},
    "quant_lfq_DIA_ion_AIF": {
        "doc_file": "dia/dia-ion-aif.md",
        "table_marker": "**Table: input files used for metric calculation and public submission**",
    },
    "quant_lfq_DIA_ion_diaPASEF": {"doc_file": "dia/dia-ion-diapasef.md"},
    "quant_lfq_DIA_ion_Astral": {"doc_file": "dia/dia-ion-astral.md"},
    "quant_lfq_DIA_ion_ZenoTOF": {"doc_file": "dia/dia-ion-zenotof.md"},
    "quant_lfq_DIA_ion_lowinput": {"doc_file": "dia/dia-ion-lowinput.md"},
    "quant_lfq_DIA_ion_plasma": {"doc_file": "dia/dia-ion-plasma.md"},
    "denovo_DDA_HCD": {"doc_file": "dda/denovo-dda-hcd.md"},
    # Entrapment has an extra "Parsed FDR column" between Input file and Parameter file —
    # the raw column each tool reports Q-values in, i.e. the [mapper] key renamed to "Q-Value".
    "entrapment_DIA_ion_Astral": {"doc_file": "dia/entrapment-dia-astral.md", "extra_column": "Parsed FDR column"},
}


def get_upload_info(tool_name: str, toml_path: Path) -> dict:
    data = toml.load(toml_path)
    base = data.get("upload_info", {})
    override = data.get("upload_info_overrides", {}).get(tool_name, {})
    return {**base, **override}


def get_parsed_fdr_column(toml_path: Path) -> str:
    """Return the raw [mapper] source column renamed to "Q-Value" (entrapment modules only)."""
    data = toml.load(toml_path)
    mapper = data.get("mapper", {})
    return next((src for src, dst in mapper.items() if dst == "Q-Value"), "")


def _cell(value: str) -> str:
    """Backtick-wrap a non-empty cell value; render missing values as an em dash."""
    return f"`{value}`" if value else "—"


def generate_table(tools_data: list, extra_column: str = None) -> str:
    if extra_column:
        header = f"| Tool | Input file | {extra_column} | Parameter file |"
        separator = "|---|---|---|---|"
        rows = [f"| {name} | {_cell(inp)} | {extra} | {_cell(par)} |" for name, inp, extra, par in tools_data if inp]
    else:
        header = "| Tool | Input file | Parameter file |"
        separator = "|---|---|---|"
        rows = [f"| {name} | {_cell(inp)} | {_cell(par)} |" for name, inp, par in tools_data if inp]
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
        extra_column = config.get("extra_column")

        tools_data = []
        for tool_name in sorted(tool_to_toml.keys()):
            toml_filename = tool_to_toml[tool_name]
            toml_path = settings_dir / toml_filename
            info = get_upload_info(tool_name, toml_path)
            if extra_column:
                extra_value = get_parsed_fdr_column(toml_path)
                tools_data.append((tool_name, info.get("datapoint_file", ""), extra_value, info.get("params_file", "")))
            else:
                tools_data.append((tool_name, info.get("datapoint_file", ""), info.get("params_file", "")))

        new_table = generate_table(tools_data, extra_column=extra_column)

        doc_path = DOCS_ROOT / config["doc_file"]
        table_marker = config.get("table_marker", DEFAULT_MARKER)
        original = doc_path.read_text(encoding="utf-8")
        updated = replace_table_in_markdown(original, table_marker, new_table)

        if updated != original:
            doc_path.write_text(updated, encoding="utf-8")
            print(f"Updated: {config['doc_file']}")
        else:
            print(f"Unchanged: {config['doc_file']}")


if __name__ == "__main__":
    main()
