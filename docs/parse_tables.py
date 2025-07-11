# TODO: Make hook so that this file is automatically updated if the markdown file is updated.
import re

import pandas as pd


def extract_parameter_tables(md_text):
    tool_name = None
    tool_tables = {}

    # Split by tool section
    tool_sections = re.split(r"### ([^\n]+)", md_text)
    for i in range(1, len(tool_sections), 2):
        tool_name = tool_sections[i].strip()
        section_text = tool_sections[i + 1]

        # Extract the first markdown table in the section
        table_match = re.search(r"\|.*?\|\n\|[-| ]+\|\n(.*?)(\n\n|\Z)", section_text, re.S)
        if table_match:
            table_text = table_match.group(0).strip()
            lines = table_text.split("\n")
            headers = [h.strip() for h in lines[0].split("|")[1:-1]]
            rows = [line.split("|")[1:-1] for line in lines[2:] if "|" in line]
            df = pd.DataFrame([[cell.strip() for cell in row] for row in rows], columns=headers)
            df["Tool"] = tool_name
            tool_tables[tool_name] = df

    return tool_tables


def combine_tables(tool_tables):
    all_tables = list(tool_tables.values())
    combined = pd.concat(all_tables, ignore_index=True)
    pivoted = combined.pivot(index="Parameter", columns="Tool", values="Parsed value")
    pivoted.reset_index(inplace=True)
    return pivoted


def process_markdown_to_csv(filepath, output_csv_path):
    with open(filepath, "r", encoding="utf-8") as f:
        md_text = f.read()

    tables = extract_parameter_tables(md_text)
    combined_df = combine_tables(tables)
    combined_df.to_csv(output_csv_path, index=False, sep="\t")


if __name__ == "__main__":
    input_file = "available-modules/12-parsed-parameters-for-public-submission.md"
    output_file = "parsing_overview.tsv"

    process_markdown_to_csv(input_file, output_file)
