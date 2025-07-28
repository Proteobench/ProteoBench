import base64
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List

import requests

SECRETS_FILE = Path(__file__).parent / ".streamlit" / "secrets.toml"
GRAPHQL_URL = "https://api.github.com/graphql"


def get_base64_image(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def stat_box(title, value, icon_path, color="#000", url=None):
    img_data = get_base64_image(icon_path)
    content = f"""
    <div style="
        background: #fff;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        padding: 12px;
        text-align: center;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: transform 0.2s ease;
    ">
        <div style="margin-bottom: 8px;">
            <img src="data:image/png;base64,{img_data}" alt="icon" style="width: 36px; height: 36px;" />
        </div>
        <div style="color: #37475E; font-weight: 600; font-size: 0.95rem; text-align: center;">{title}</div>
        <div style="font-size: 1.5rem; font-weight: 700; margin-top: 6px; color: #37475E;">{value}</div>
    </div>
    """
    if url:
        return f"""<a href="{url}" target="_blank" style="text-decoration: none;">{content}</a>"""
    return content


def get_n_modules():
    """
    Get the number of modules in ProteoBench.

    Returns
    -------
    int
        The number of modules.
    """
    # The number of modules is defined by the number of .py files in the pages directory that are not __init__.py

    pages_dir = Path(__file__).parent / "pages"
    n_modules = len([f for f in pages_dir.glob("*.py") if f.name != "__init__.py"])
    return n_modules


def get_n_submitted_points(url: str = "https://proteobench.cubimed.rub.de/datasets/"):
    """
    Get the number of submitted points in ProteoBench.

    Returns
    -------
    int
        The number of submitted points (excluding 'fasta/' and 'raw_files/').
    """
    exclude_dirs = {"fasta/", "raw_files/", "../"}

    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text

        # Find all hrefs that end in /
        dirs = re.findall(r'href="([^"]+/)"', html)

        # Remove unwanted dirs
        submitted_dirs = set(dirs) - exclude_dirs

        return len(submitted_dirs)

    except requests.RequestException as e:
        return "Error communicating with the server"


def get_n_supported_tools():
    """
    Get the number of supported tools in ProteoBench.

    Returns
    -------
    int
        The number of supported tools.
    """
    # The number of supported tools is defined by the number of .py files in the io/params/ directory that are not __init__.py
    params_dir = Path(__file__).parent.parent / "proteobench" / "io" / "params"
    n_tools = len([f for f in params_dir.glob("*.py") if f.name != "__init__.py"])
    return n_tools


# TODO: perhaps proposed modules should be parsed using the GitHub discussion but there doesnt seem to be an API endpoint for this
def parse_proteobench_index(rst_text: str) -> Dict[str, int]:
    """
    Parses the ProteoBench index.rst and counts modules by status.

    This version assumes that each module starts with '.. grid-item-card::'
    and that the badge line contains ':bdg-' followed by the status.

    Parameters
    ----------
    rst_text : str
        The text content of the index.rst file.

    Returns
    -------
    Dict[str, int]
        Dictionary mapping statuses to counts.
    """
    status_counter = Counter()

    # Split into sections by grid-item-card
    sections = rst_text.split(".. grid-item-card::")
    # First part is before first card

    for section in sections[1:]:  # Skip first part before first card
        lines = section.strip().splitlines()

        status_found = False
        for line in lines:
            line = line.strip()
            if line.startswith(":bdg-") and ":`" in line:
                # Example: :bdg-success:`active`
                try:
                    status = line.split(":`")[1].rstrip("`").strip().lower()
                    status_counter[status] += 1
                    status_found = True
                    break
                except IndexError:
                    continue

        if not status_found:
            # If no badge found, you can log or skip
            pass

    return dict(status_counter)


def get_n_modules_proposed(rst_text: str) -> int:
    """
    Computes the number of proposed modules as the sum of modules
    'in discussion' and 'in development'.

    Parameters
    ----------
    status_counts : Dict[str, int]
        A dictionary of status counts as returned by parse_proteobench_index().

    Returns
    -------
    int
        The total number of proposed modules.
    """
    status_counts = parse_proteobench_index(rst_text)
    return status_counts.get("in discussion", 0) + status_counts.get("in development", 0)


if __name__ == "__main__":
    # This block is only for testing purposes
    print(f"Number of modules: {get_n_modules()}")
    print(f"Number of submitted points: {get_n_submitted_points()}")
    print(f"Number of supported tools: {get_n_supported_tools()}")
    file_path = Path(__file__).parent.parent / "docs" / "index.rst"
    status_counts = parse_proteobench_index(file_path.read_text(encoding="utf-8"))
    print(f"Number of proposed modules: {get_n_modules_proposed(file_path.read_text(encoding='utf-8'))}")
