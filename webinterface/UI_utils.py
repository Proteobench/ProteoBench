import base64
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Optional

import requests
import streamlit as st

SECRETS_FILE = Path(__file__).parent / ".streamlit" / "secrets.toml"
GRAPHQL_URL = "https://api.github.com/graphql"


def get_base64_image(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def stat_box(title, value, icon_path, url=None):
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
    n_modules = len(
        [f for f in pages_dir.glob("*.py") if not f.name == "__init__.py" and not f.name.startswith("base")]
    )
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

    except requests.RequestException:
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


def get_monthly_visitors(api_endpoint: str, token: str, id_site: int) -> Optional[int]:
    """
    Gets the monthly visitors count from the Matomo API.

    Parameters
    ----------
    api_endpoint : str
        The API endpoint URL of the Matomo installation
    token : str
        The authentication token (from Matomo)
    id_site : int
        The site ID (from Matomo)

    Returns
    -------
    Optional[int]
        The number of monthly visitors (nb_uniq_visitors of last 30 days), or
        ``None`` if retrieval/parsing failed.
    """

    # data to be sent to api
    data = {
        "module": "API",
        "method": "VisitsSummary.get",
        "idSite": id_site,
        "period": "range",
        "date": "last30",
        "format": "json",
        "token_auth": token,
    }

    try:
        r = requests.post(url=api_endpoint, data=data)
        r.raise_for_status()
        response_data = r.json()

        return int(response_data.get("nb_uniq_visitors", 0))

    except requests.RequestException:
        print("Failed to retrieve monthly visitors from Matomo API")
        return None

    except (ValueError, KeyError):
        print("Error parsing Matomo API response")
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_module_submission_data() -> Dict[str, Dict[str, int]]:
    """
    Fetch submission data per module by downloading repo archives.
    Returns per-tool submission counts for each module.
    Requests are made concurrently to minimize latency.

    Returns
    -------
    Dict[str, Dict[str, int]]
        Mapping of results_repo name to {software_name: count} dict.
    """
    import io
    import json
    import tarfile
    from collections import Counter
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from pages.utils.module_registry import get_all_modules

    modules_by_category = get_all_modules()

    headers = {}
    try:
        token = st.secrets["gh"]["token"]
        headers["Authorization"] = f"token {token}"
    except Exception:
        pass

    repo_names = [
        module.results_repo
        for modules in modules_by_category.values()
        for module in modules
        if module.results_repo
    ]

    def _fetch_tool_breakdown(repo_name: str) -> tuple:
        import logging

        logger = logging.getLogger(__name__)

        try:
            url = f"https://api.github.com/repos/Proteobench/{repo_name}/tarball/main"
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
        except requests.RequestException:
            logger.warning("Failed to download archive for %s", repo_name, exc_info=True)
            return repo_name, {}

        tools = Counter()
        try:
            with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:gz") as tar:
                for member in tar.getmembers():
                    if member.name.endswith(".json") and member.isfile():
                        try:
                            f = tar.extractfile(member)
                            data = json.loads(f.read())
                            tools[data.get("software_name", "Unknown")] += 1
                        except (json.JSONDecodeError, KeyError, OSError):
                            logger.warning(
                                "Skipping malformed file %s in %s", member.name, repo_name, exc_info=True
                            )
        except tarfile.TarError:
            logger.warning("Failed to read archive for %s", repo_name, exc_info=True)
            return repo_name, {}

        return repo_name, dict(tools)

    if not repo_names:
        return {}

    result: Dict[str, Dict[str, int]] = {}
    with ThreadPoolExecutor(max_workers=min(len(repo_names), 10)) as executor:
        futures = {executor.submit(_fetch_tool_breakdown, name): name for name in repo_names}
        for future in as_completed(futures):
            repo_name, tool_counts = future.result()
            result[repo_name] = tool_counts

    return result


def build_submissions_figure():
    """
    Build a Plotly figure with faceted vertical bar charts showing submissions per module,
    one subplot per category (DDA, DIA, etc.). Excludes archived modules.
    Each bar stores its results_repo name in customdata for click-based pie chart interaction.

    Returns
    -------
    tuple(plotly.graph_objects.Figure, Dict[str, Dict[str, int]]) or (None, None)
        The bar figure and a mapping of module title to per-tool counts.
    """
    from plotly import graph_objects as go
    from plotly.subplots import make_subplots

    from pages.utils.module_registry import get_all_modules

    modules_by_category = get_all_modules()
    submission_data = get_module_submission_data()

    # Build per-category data, excluding archived modules
    category_data: Dict[str, list] = {}
    tool_data_by_title: Dict[str, Dict[str, int]] = {}
    for category, modules in modules_by_category.items():
        rows = []
        for module in modules:
            if module.release_stage == "archived":
                continue
            if module.results_repo and module.results_repo in submission_data:
                tool_counts = submission_data[module.results_repo]
                total = sum(tool_counts.values())
                rows.append({"label": module.title, "count": total})
                tool_data_by_title[module.title] = tool_counts
        if rows:
            rows.sort(key=lambda r: r["count"], reverse=True)
            category_data[category] = rows

    if not category_data:
        return None, None

    categories = sorted(category_data.keys())
    n_cats = len(categories)

    palette = ["#F4A582", "#92C5DE", "#B2DF8A", "#CAB2D6", "#FDBF6F", "#FB9A99"]
    color_map = {cat: palette[i % len(palette)] for i, cat in enumerate(categories)}

    fig = make_subplots(
        rows=1,
        cols=n_cats,
        subplot_titles=[f"{cat} Modules" for cat in categories],
        shared_yaxes=False,
        horizontal_spacing=0.08,
    )

    for col_idx, cat in enumerate(categories, start=1):
        rows = category_data[cat]
        labels = [r["label"] for r in rows]
        values = [r["count"] for r in rows]

        fig.add_trace(
            go.Bar(
                x=labels,
                y=values,
                marker_color=color_map[cat],
                name=cat,
                hovertemplate="<b>%{x}</b><br>Submissions: %{y}<br><i>Click for tool breakdown</i><extra></extra>",
                showlegend=False,
            ),
            row=1,
            col=col_idx,
        )

        fig.update_xaxes(tickangle=-45, row=1, col=col_idx)
        fig.update_yaxes(title_text="# public workflow results" if col_idx == 1 else "", row=1, col=col_idx)

    max_modules = max(len(v) for v in category_data.values())
    fig.update_layout(
        height=max(350, 200 + max_modules * 25),
        margin=dict(l=40, r=20, t=40, b=120),
    )

    return fig, tool_data_by_title


def build_tool_pie_chart(module_title: str, tool_counts: Dict[str, int]):
    """
    Build a Plotly pie chart showing tool breakdown for a given module.

    Parameters
    ----------
    module_title : str
        The module title for the chart heading.
    tool_counts : Dict[str, int]
        Mapping of software_name to submission count.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    from plotly import graph_objects as go

    labels = list(tool_counts.keys())
    values = list(tool_counts.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hovertemplate="<b>%{label}</b><br>Submissions: %{value}<br>(%{percent})<extra></extra>",
                textinfo="label+value",
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title=dict(text=f"Tool breakdown: {module_title}", font=dict(size=14)),
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )

    return fig


if __name__ == "__main__":
    # This block is only for testing purposes
    print(f"Number of modules: {get_n_modules()}")
    print(f"Number of submitted points: {get_n_submitted_points()}")
    print(f"Number of supported tools: {get_n_supported_tools()}")
    file_path = Path(__file__).parent.parent / "docs" / "index.rst"
    status_counts = parse_proteobench_index(file_path.read_text(encoding="utf-8"))
    print(f"Number of proposed modules: {get_n_modules_proposed(file_path.read_text(encoding='utf-8'))}")
