import re
from pathlib import Path

import requests


def stat_box(title, value, icon, color="#000", url=None):
    content = f"""
    <div style="
        background: #fff;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        padding: 20px;
        text-align: center;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform 0.2s ease;
    ">
        <div style="font-size: 2rem; color: {color}; margin-bottom: 10px;">{icon}</div>
        <div style="color: #37475E; font-weight: 600;">{title}</div>
        <div style="font-size: 1.8rem; font-weight: 700; margin-top: 10px; color: #37475E;">{value}</div>
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


if __name__ == "__main__":
    # This block is only for testing purposes
    print(f"Number of modules: {get_n_modules()}")
    print(f"Number of submitted points: {get_n_submitted_points()}")
    print(f"Number of supported tools: {get_n_supported_tools()}")
