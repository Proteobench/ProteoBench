"""Tab for exploring how workflow parameter choices affect benchmarking performance."""

import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from scipy import stats as _scipy_stats

from pages.base_pages.tabs.tab1_view_public_results import initialize_main_data_points
from pages.base_pages.utils.resulttable import PARAMETER_COLS, TECHNICAL_COLS, configure_aggrid, render_aggrid
from proteobench.plotting.plot_constants import QUANT_SOFTWARE_COLORS

_DEFAULT_SCATTER_PARAM = "ident_fdr_psm"

# Columns that are excluded from metric inference even though they are numeric.
_NON_METRIC_COLS = PARAMETER_COLS | TECHNICAL_COLS | {
    "id", "results", "open_source", "selected",
    # Tolerance string columns and their derived numeric splits are parameters.
    "precursor_mass_tolerance_min", "precursor_mass_tolerance_max",
    "fragment_mass_tolerance_min", "fragment_mass_tolerance_max",
    # Column name used in some tool outputs; JSON defines it as 'semi_enzymatic'.
    "semi_specific",
}


_TOL_COLS = ("precursor_mass_tolerance", "fragment_mass_tolerance")

# These are submission identity fields, not tunable workflow parameters.
_PARETO_EXCLUDED_PARAMS = frozenset({
    "software_name", "software_version", "search_engine", "search_engine_version",
})

# Matches "[<num> <unit>, <num> <unit>]" or a bare "<num> <unit>" / "<num>"
_TOL_RANGE_RE = re.compile(
    r"\[\s*(-?[\d.]+(?:e[+-]?\d+)?)\s*[a-zA-Z]*\s*,\s*(-?[\d.]+(?:e[+-]?\d+)?)\s*[a-zA-Z]*\s*\]",
    re.IGNORECASE,
)
_TOL_SINGLE_RE = re.compile(r"^(-?[\d.]+(?:e[+-]?\d+)?)\s*[a-zA-Z]*$", re.IGNORECASE)


def _parse_tolerance(val) -> tuple:
    """Return ``(min_val, max_val)`` floats from a tolerance string, or ``(None, None)``."""
    if pd.isna(val):
        return None, None
    s = str(val).strip()
    m = _TOL_RANGE_RE.match(s)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = _TOL_SINGLE_RE.match(s)
    if m:
        v = float(m.group(1))
        return -abs(v), abs(v)
    return None, None


def _expand_tolerance_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Split tolerance string columns into numeric min/max columns (local to this tab only).

    For example, ``precursor_mass_tolerance = "[-2.8 ppm, 2.8 ppm]"`` becomes
    ``precursor_mass_tolerance_min = -2.8`` and ``precursor_mass_tolerance_max = 2.8``.
    The original string columns are not modified.
    """
    df = df.copy()
    for col in _TOL_COLS:
        if col not in df.columns:
            continue
        parsed = df[col].apply(_parse_tolerance)
        df[f"{col}_min"] = parsed.apply(lambda t: t[0]).astype(float)
        df[f"{col}_max"] = parsed.apply(lambda t: t[1]).astype(float)
    return df


def display_parameter_performance(variables, ionmodule) -> None:
    """
    Display the post-hoc analysis tab (sub-tabs: Parameter vs Performance, Versioning analysis).

    Parameters
    ----------
    variables : object
        Variables object containing session state keys and configuration.
    ionmodule : object
        Module instance providing data access methods.
    """
    st.header("Post-hoc Analysis")

    df = _load_data(variables, ionmodule)

    if df is None or df.empty:
        st.info("No datapoints available. Load data in the 'View Public Results' tab first.")
        return

    df = _expand_tolerance_cols(df)

    param_cols = _get_parameter_columns(df)
    numeric_param_cols = _get_numeric_parameter_columns(df)
    metric_cols = _get_metric_columns(df)

    if not param_cols or not metric_cols:
        st.info("Not enough parameter or metric columns available to render plots.")
        return

    sidebar_path = getattr(variables, "sidebar_path", "default")

    subtab_params, subtab_versioning = st.tabs(["Parameter vs Performance", "Versioning analysis"])

    with subtab_params:
        _display_parameter_vs_performance(df, param_cols, numeric_param_cols, metric_cols, sidebar_path)

    with subtab_versioning:
        _display_versioning_analysis(df, metric_cols, sidebar_path)


def _display_parameter_vs_performance(df, param_cols, numeric_param_cols, metric_cols, sidebar_path):
    """Render the correlation heatmap, parameter-slice scatter, and Pareto front."""
    st.markdown(
        """
        Explore how workflow parameter choices correlate with benchmarking performance.

        - **Correlation heatmap**: Spearman correlation between each parameter (rows) and each
          performance metric (columns). Blue = negative correlation, red = positive.
          Asterisks indicate significance: `*` p < 0.05, `**` p < 0.01.
          Rows are sorted by mean |r| across all metrics.
        - **Parameter slice**: Scatter of one parameter (x-axis) against the chosen performance
          metric, colored by software tool.
        """
    )

    scatter_x_key = f"_tab7_scatter_x_{sidebar_path}"
    metric_key = f"_tab7_metric_{sidebar_path}"
    corr_params_key = f"_tab7_param_cols_{sidebar_path}"

    # Scatter uses the tolerance _min/_max splits, not the original string columns.
    scatter_param_cols = [c for c in param_cols if c not in _TOL_COLS]

    # Default scatter pair: metric-parameter with highest absolute Spearman correlation.
    default_metric = next((c for c in metric_cols if "median_abs_epsilon" in c), metric_cols[0])
    default_scatter_x = (
        _DEFAULT_SCATTER_PARAM if _DEFAULT_SCATTER_PARAM in scatter_param_cols else scatter_param_cols[0]
    )
    _numeric_scatter = [c for c in numeric_param_cols if c not in _TOL_COLS]
    if _numeric_scatter and metric_cols:
        _qcorr, _, _ = _compute_spearman(df, _numeric_scatter, metric_cols)
        _abs = _qcorr.abs()
        if _abs.notna().any().any():
            _best_param = _abs.max(axis=1).idxmax()
            _best_metric = _abs.loc[_best_param].idxmax()
            default_scatter_x = _best_param if _best_param in scatter_param_cols else default_scatter_x
            default_metric = _best_metric
    default_corr_params = numeric_param_cols

    st.subheader("Parameter–Performance Correlation")
    with st.expander("Correlation controls", expanded=True):
        saved_corr = st.session_state.get(corr_params_key, default_corr_params)
        valid_saved = [c for c in saved_corr if c in numeric_param_cols] or default_corr_params
        selected_corr_params = st.multiselect(
            "Parameters to include",
            options=numeric_param_cols,
            default=valid_saved,
            key=corr_params_key,
            help="Only numeric parameters are included. Use the scatter plot below to explore categorical parameters.",
        )
    if not selected_corr_params:
        st.info("Select at least one parameter above to render the correlation heatmap.")
    else:
        corr_fig = _build_correlation_heatmap(df, selected_corr_params, metric_cols)
        st.plotly_chart(corr_fig, use_container_width=True)
        st.caption(
            "Spearman *r* between parameter values and each metric across all submitted datapoints. "
            "Requires ≥ 5 non-null paired observations per cell."
        )

    st.subheader("Parameter Slice")
    with st.expander("Scatter controls", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_metric = st.selectbox(
                "Performance metric",
                options=metric_cols,
                index=metric_cols.index(default_metric) if default_metric in metric_cols else 0,
                key=metric_key,
            )
        with col2:
            selected_scatter_x = st.selectbox(
                "x-axis parameter",
                options=scatter_param_cols,
                index=scatter_param_cols.index(default_scatter_x) if default_scatter_x in scatter_param_cols else 0,
                key=scatter_x_key,
                help="Includes categorical parameters. Tolerance values are split into min/max.",
            )
    scatter_fig = _build_scatter(df, selected_scatter_x, selected_metric)
    st.plotly_chart(scatter_fig, use_container_width=True)

    # --- Pareto front section ---
    st.subheader("Pareto Front")
    st.markdown(
        "Pareto-optimal workflows are not dominated by any other submission: "
        "no other workflow simultaneously achieves a lower value on the minimized metric "
        "and a higher value on the maximized metric. "
        "These represent the efficient frontier of the accuracy–coverage trade-off."
    )

    pareto_min_key = f"_tab7_pareto_min_{sidebar_path}"
    pareto_max_key = f"_tab7_pareto_max_{sidebar_path}"
    pareto_per_tool_key = f"_tab7_pareto_per_tool_{sidebar_path}"

    default_pareto_min = next((c for c in metric_cols if "epsilon" in c.lower()), metric_cols[0])
    _coverage_candidates = ("nr_prec", "nr_feature")
    default_pareto_max = next(
        (c for c in _coverage_candidates if c in metric_cols),
        metric_cols[1] if len(metric_cols) > 1 else metric_cols[0],
    )

    with st.expander("Pareto controls", expanded=True):
        pcol1, pcol2, pcol3 = st.columns([2, 2, 1])
        with pcol1:
            pareto_minimize = st.selectbox(
                "Minimize (lower is better)",
                options=metric_cols,
                index=metric_cols.index(default_pareto_min) if default_pareto_min in metric_cols else 0,
                key=pareto_min_key,
            )
        with pcol2:
            pareto_maximize = st.selectbox(
                "Maximize (higher is better)",
                options=metric_cols,
                index=metric_cols.index(default_pareto_max) if default_pareto_max in metric_cols else 0,
                key=pareto_max_key,
            )
        with pcol3:
            per_tool_mode = st.checkbox(
                "Per-tool fronts",
                value=False,
                key=pareto_per_tool_key,
                help="Compute a separate Pareto front within each software tool, removing the tool-choice confound.",
            )

    if per_tool_mode:
        per_tool_fronts = _compute_per_tool_pareto_fronts(df, pareto_minimize, pareto_maximize)
        pareto_ids = set().union(*per_tool_fronts.values()) if per_tool_fronts else set()
    else:
        per_tool_fronts = None
        pareto_ids = _compute_pareto_front(df, pareto_minimize, pareto_maximize)

    n_total = int(
        df[[pareto_minimize, pareto_maximize]]
        .apply(pd.to_numeric, errors="coerce")
        .dropna()
        .shape[0]
    )

    pareto_fig = _build_pareto_scatter(
        df, pareto_minimize, pareto_maximize, pareto_ids, per_tool_fronts=per_tool_fronts
    )
    st.plotly_chart(pareto_fig, use_container_width=True)
    if per_tool_mode:
        n_tools = len(per_tool_fronts) if per_tool_fronts else 0
        st.caption(
            f"{len(pareto_ids)} of {n_total} submitted workflows are on their tool's Pareto front "
            f"(across {n_tools} tool(s) with ≥ 2 submissions)."
        )
    else:
        st.caption(f"{len(pareto_ids)} of {n_total} submitted workflows are on the Pareto front.")

    if pareto_ids:
        tdf = _pareto_table_df(df, pareto_ids, pareto_minimize, pareto_maximize)
        grid_opts = configure_aggrid(tdf)
        render_aggrid(tdf, grid_opts, key=f"pareto_table_{sidebar_path}")

        st.markdown("**Recommended parameter settings** (based on Pareto-optimal submissions)")
        if per_tool_mode and per_tool_fronts:
            tools_with_front = sorted(per_tool_fronts.keys())
            selected_tool = st.selectbox(
                "Show recommendations for",
                options=["All Pareto workflows"] + tools_with_front,
                key=f"_tab7_rec_tool_{sidebar_path}",
            )
            rec_ids = (
                pareto_ids
                if selected_tool == "All Pareto workflows"
                else per_tool_fronts[selected_tool]
            )
        else:
            rec_ids = pareto_ids

        rec_df = _build_recommendation_summary(df, rec_ids)
        if rec_df.empty:
            st.info("Not enough parameter data among Pareto-optimal submissions to generate recommendations.")
        else:
            st.dataframe(rec_df, use_container_width=True, hide_index=True)
            st.caption(
                "Recommended value: median (numeric) or most common value (categorical). "
                "Pareto support: for categorical parameters, how often the recommended value is observed / total Pareto workflows; "
                "for numeric parameters, the observed range across Pareto workflows. "
                "Recommendations are confounded by tool choice unless per-tool mode is enabled."
            )


def _parse_version_key(v: str) -> tuple:
    """Return a sortable tuple from a version string.

    Tries semver (``1.2.3[-suffix]``) first, then falls back to extracting
    any sequence of integers (e.g. ``"v2b4"`` → ``(2, 4)``).
    """
    s = str(v).strip()
    m = re.match(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", s)
    if m:
        return tuple(int(x) if x else 0 for x in m.groups())
    nums = re.findall(r"\d+", s)
    return tuple(int(n) for n in nums) if nums else (0,)


def _display_versioning_analysis(df: pd.DataFrame, metric_cols: list, sidebar_path: str) -> None:
    """Render the versioning analysis sub-tab."""
    st.markdown(
        "Track how each tool's performance evolves across submitted software versions. "
        "Green segments indicate improvement, red indicate regression."
    )

    if "software_version" not in df.columns or "software_name" not in df.columns:
        st.info("No software version information available in this dataset.")
        return

    ver_metric_key = f"_tab7_ver_metric_{sidebar_path}"
    ver_dir_key = f"_tab7_ver_direction_{sidebar_path}"
    ver_minv_key = f"_tab7_ver_min_versions_{sidebar_path}"

    default_metric = next((c for c in metric_cols if "median_abs_epsilon" in c), metric_cols[0])

    with st.expander("Versioning controls", expanded=True):
        vc1, vc2, vc3 = st.columns([3, 2, 1])
        with vc1:
            ver_metric = st.selectbox(
                "Metric",
                options=metric_cols,
                index=metric_cols.index(default_metric) if default_metric in metric_cols else 0,
                key=ver_metric_key,
            )
        with vc2:
            ver_direction = st.radio(
                "Direction",
                options=["Lower is better", "Higher is better"],
                index=0,
                key=ver_dir_key,
                horizontal=True,
            )
        with vc3:
            ver_min_versions = st.number_input(
                "Min versions",
                min_value=2,
                value=2,
                step=1,
                key=ver_minv_key,
                help="Minimum number of distinct versions a tool must have to appear in the chart.",
            )

    lower_is_better = ver_direction == "Lower is better"

    tool_version_data = _prepare_version_data(df, ver_metric, int(ver_min_versions))

    if not tool_version_data:
        st.info(
            "No tools have multiple distinct versions in the current data. "
            "Try relaxing the minimum precursor filter in Tab 1."
        )
        return

    ver_fig = _build_version_evolution_chart(tool_version_data, ver_metric, lower_is_better)
    st.plotly_chart(ver_fig, use_container_width=True)

    change_df = _build_version_change_table(tool_version_data, ver_metric, lower_is_better)
    if not change_df.empty:
        st.markdown("**Version-to-version changes**")

        def _color_pct(col):
            styles = []
            for v in col:
                if pd.isna(v) or abs(v) < 0.5:
                    styles.append("")
                else:
                    improved = (v < 0) if lower_is_better else (v > 0)
                    if improved:
                        styles.append("background-color: #c3e6cb; color: #155724")
                    else:
                        styles.append("background-color: #f5c6cb; color: #721c24")
            return styles

        styled = (
            change_df.style
            .format({"% change": lambda x: f"{x:+.1f}%" if not np.isnan(x) else "N/A"})
            .apply(_color_pct, subset=["% change"])
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)


def _prepare_version_data(df: pd.DataFrame, metric_col: str, min_versions: int) -> dict:
    """Build per-tool version summary needed for the versioning chart.

    Returns
    -------
    dict
        ``{tool_name: {"sorted_versions": [...], "medians": {v: float},
           "individuals": {v: [float, ...]}}}``.
        Only tools with >= *min_versions* distinct versions are included.
    """
    dfc = df[["software_name", "software_version", "id", metric_col]].copy()
    dfc[metric_col] = pd.to_numeric(dfc[metric_col], errors="coerce")
    dfc = dfc.dropna(subset=["software_name", "software_version", metric_col])
    dfc["software_version"] = dfc["software_version"].astype(str)

    result = {}
    for tool, group in dfc.groupby("software_name"):
        versions = group["software_version"].unique().tolist()
        if len(versions) < min_versions:
            continue
        sorted_versions = sorted(versions, key=_parse_version_key)
        medians = {v: float(group.loc[group["software_version"] == v, metric_col].median()) for v in sorted_versions}
        individuals = {
            v: list(zip(
                group.loc[group["software_version"] == v, metric_col].values,
                group.loc[group["software_version"] == v, "id"].values,
            ))
            for v in sorted_versions
        }
        result[str(tool)] = {
            "sorted_versions": sorted_versions,
            "medians": medians,
            "individuals": individuals,
        }
    return result


def _build_version_evolution_chart(tool_version_data: dict, metric_col: str, lower_is_better: bool) -> go.Figure:
    """Build per-tool subplot grid showing metric evolution across versions.

    Each tool gets its own x-axis so version strings are never mixed between tools.
    """
    tools = sorted(tool_version_data.keys())
    n_tools = len(tools)

    if n_tools == 0:
        return go.Figure()

    n_cols = min(n_tools, 3)
    n_rows = (n_tools + n_cols - 1) // n_cols

    # Compute global y range across all tools so subplots are directly comparable.
    all_vals = [
        val
        for data in tool_version_data.values()
        for v_list in data["individuals"].values()
        for val, _ in v_list
    ]
    if all_vals:
        y_min, y_max = min(all_vals), max(all_vals)
        y_pad = (y_max - y_min) * 0.08 or abs(y_max) * 0.08 or 0.05
        y_range = [y_min - y_pad, y_max + y_pad]
    else:
        y_range = None

    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=tools,
        shared_yaxes=False,
        horizontal_spacing=0.10,
        vertical_spacing=0.20,
    )

    for idx, tool in enumerate(tools):
        row = idx // n_cols + 1
        col = idx % n_cols + 1
        data = tool_version_data[tool]
        color = QUANT_SOFTWARE_COLORS.get(tool, "#888888")
        sorted_versions = data["sorted_versions"]
        medians = data["medians"]
        individuals = data["individuals"]

        # Individual submission dots (semi-transparent background).
        ind_x, ind_y, ind_hover = [], [], []
        for v in sorted_versions:
            for val, pid in individuals[v]:
                ind_x.append(v)
                ind_y.append(val)
                ind_hover.append(f"<b>{tool}</b> {v}<br>{metric_col}: {val:.4f}<br>ID: {pid}")
        if ind_x:
            fig.add_trace(
                go.Scatter(
                    x=ind_x, y=ind_y, mode="markers",
                    name=tool, legendgroup=tool, showlegend=False,
                    marker=dict(color=color, size=7, opacity=0.25),
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=ind_hover,
                ),
                row=row, col=col,
            )

        # Version medians line.
        med_y = [medians[v] for v in sorted_versions]
        n_per_v = [len(individuals[v]) for v in sorted_versions]
        med_hover = [
            f"<b>{tool}</b><br>Version: {v}<br>{metric_col}: {m:.4f}<br>n={n}"
            for v, m, n in zip(sorted_versions, med_y, n_per_v)
        ]
        fig.add_trace(
            go.Scatter(
                x=sorted_versions, y=med_y, mode="lines+markers",
                name=tool, legendgroup=tool, showlegend=False,
                line=dict(color=color, width=2),
                marker=dict(color=color, size=10, line=dict(width=1, color="#333333")),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=med_hover,
            ),
            row=row, col=col,
        )

        # Improvement/regression segments between consecutive version medians.
        for i in range(len(sorted_versions) - 1):
            v0, v1 = sorted_versions[i], sorted_versions[i + 1]
            m0, m1 = medians[v0], medians[v1]
            delta = m1 - m0
            improved = (delta < 0) if lower_is_better else (delta > 0)
            seg_color = "#2ca02c" if improved else "#d62728"
            fig.add_trace(
                go.Scatter(
                    x=[v0, v1], y=[m0, m1], mode="lines",
                    line=dict(color=seg_color, width=4),
                    legendgroup=tool, showlegend=False,
                    hoverinfo="skip",
                ),
                row=row, col=col,
            )

        # Each subplot gets its own categorical x-axis ordered by this tool's versions.
        fig.update_xaxes(
            type="category",
            categoryorder="array",
            categoryarray=sorted_versions,
            tickangle=-35,
            row=row, col=col,
        )
        fig.update_yaxes(
            title_text=metric_col if col == 1 else "",
            range=y_range,
            row=row, col=col,
        )

    fig.update_layout(
        height=max(350, 320 * n_rows),
        margin=dict(l=60, r=20, t=60, b=80),
        showlegend=False,
    )
    return fig


def _build_version_change_table(
    tool_version_data: dict, metric_col: str, lower_is_better: bool
) -> pd.DataFrame:
    """Return a DataFrame summarising consecutive version-to-version metric changes.

    ``% change`` is stored as a numeric float so the caller can apply colour styling.
    """
    rows = []
    for tool, data in sorted(tool_version_data.items()):
        sorted_versions = data["sorted_versions"]
        medians = data["medians"]
        for i in range(len(sorted_versions) - 1):
            v0, v1 = sorted_versions[i], sorted_versions[i + 1]
            m0, m1 = medians[v0], medians[v1]
            delta = m1 - m0
            pct = (delta / abs(m0) * 100) if m0 != 0 else float("nan")
            rows.append({
                "Tool": tool,
                "From version": v0,
                "To version": v1,
                f"{metric_col} (from)": round(m0, 4),
                f"{metric_col} (to)": round(m1, 4),
                "Absolute change": round(delta, 4),
                "% change": pct,
            })
    return pd.DataFrame(rows)


def _load_data(variables, ionmodule) -> pd.DataFrame | None:
    """Load and filter datapoints, reusing the session state populated by Tab 1."""
    initialize_main_data_points(variables, ionmodule)
    raw = st.session_state.get(variables.all_datapoints)
    if raw is None or (isinstance(raw, pd.DataFrame) and raw.empty):
        return None

    # Mirror the slider-value resolution used in tab5_compare_results.
    filter_value = getattr(variables, "default_val_slider", 3)
    if hasattr(variables, "slider_id_uuid"):
        slider_key = variables.slider_id_uuid
        if slider_key in st.session_state:
            slider_uuid = st.session_state[slider_key]
            if slider_uuid in st.session_state:
                filter_value = st.session_state[slider_uuid]

    return ionmodule.filter_data_point(raw, filter_value)


def _get_parameter_columns(df) -> list:
    """Return parameter columns (including derived tolerance splits) with ≥ 2 distinct non-null values."""
    param_set = PARAMETER_COLS | {
        "precursor_mass_tolerance_min", "precursor_mass_tolerance_max",
        "fragment_mass_tolerance_min", "fragment_mass_tolerance_max",
    }
    return [col for col in df.columns if col in param_set and df[col].dropna().nunique() >= 2]


def _get_numeric_parameter_columns(df) -> list:
    """Return numeric parameter columns (includes derived tolerance splits) with ≥ 2 distinct non-null values."""
    return [
        col for col in _get_parameter_columns(df)
        if pd.to_numeric(df[col], errors="coerce").notna().sum() > 0
    ]


def _get_metric_columns(df) -> list:
    """Infer numeric metric columns: any numeric column not classified as a parameter or technical column.

    Epsilon columns are sorted first; remaining metrics are sorted alphabetically.
    """
    candidates = [
        col for col in df.columns
        if col not in _NON_METRIC_COLS
        and pd.to_numeric(df[col], errors="coerce").dropna().shape[0] > 0
    ]
    epsilon = sorted(c for c in candidates if "epsilon" in c.lower())
    other = sorted(c for c in candidates if "epsilon" not in c.lower())
    return epsilon + other


def _compute_spearman(df, param_cols, metric_cols):
    """Return (corr_df, pval_df, nobs_df) DataFrames indexed param_cols × metric_cols."""
    corr = pd.DataFrame(np.nan, index=param_cols, columns=metric_cols, dtype=float)
    pval = pd.DataFrame(np.nan, index=param_cols, columns=metric_cols, dtype=float)
    nobs = pd.DataFrame(0, index=param_cols, columns=metric_cols, dtype=int)

    for metric in metric_cols:
        y = pd.to_numeric(df[metric], errors="coerce")
        for param in param_cols:
            x = pd.to_numeric(df[param], errors="coerce")
            mask = x.notna() & y.notna()
            n = int(mask.sum())
            if n < 5:
                continue
            r, p = _scipy_stats.spearmanr(x[mask].values, y[mask].values)
            corr.loc[param, metric] = float(r)
            pval.loc[param, metric] = float(p)
            nobs.loc[param, metric] = n

    return corr, pval, nobs


def _build_correlation_heatmap(df, param_cols, metric_cols) -> go.Figure:
    """Build Spearman correlation heatmap: parameters (rows) × metrics (columns).

    Parameters
    ----------
    df : pd.DataFrame
        Datapoints DataFrame (after filter_data_point + _expand_tolerance_cols).
    param_cols : list of str
        Parameters to correlate.
    metric_cols : list of str
        Performance metrics to correlate against.

    Returns
    -------
    go.Figure
    """
    if not param_cols or not metric_cols:
        fig = go.Figure()
        fig.add_annotation(text="Not enough columns to compute correlations.", showarrow=False)
        return fig

    corr, pval, nobs = _compute_spearman(df, param_cols, metric_cols)

    valid_params = corr.index[corr.notna().any(axis=1)].tolist()
    if not valid_params:
        fig = go.Figure()
        fig.add_annotation(
            text="Could not compute any correlations — need ≥ 5 datapoints per cell.",
            showarrow=False,
        )
        return fig

    # Sort params by mean |r| across all metrics (ascending so strongest correlations are at top).
    sort_key = corr.loc[valid_params].abs().mean(axis=1)
    sorted_params = sort_key.sort_values(ascending=True).index.tolist()

    z = corr.loc[sorted_params, metric_cols].values.astype(float)

    text_matrix = []
    hover_matrix = []
    for param in sorted_params:
        row_text = []
        row_hover = []
        for metric in metric_cols:
            r = corr.loc[param, metric]
            p = pval.loc[param, metric]
            n = nobs.loc[param, metric]
            if np.isnan(r):
                row_text.append("N/A")
                row_hover.append(f"<b>{param}</b> × {metric}<br>r: N/A (< 5 obs.)")
            else:
                sig = "**" if p < 0.01 else ("*" if p < 0.05 else "")
                row_text.append(f"{r:.2f}{sig}")
                row_hover.append(
                    f"<b>{param}</b> × {metric}<br>"
                    f"r = {r:.3f}{sig}<br>"
                    f"p = {p:.3g}<br>"
                    f"n = {n}"
                )
        text_matrix.append(row_text)
        hover_matrix.append(row_hover)

    height = max(300, min(800, len(sorted_params) * 32 + 140))

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=metric_cols,
            y=sorted_params,
            text=text_matrix,
            texttemplate="%{text}",
            customdata=hover_matrix,
            hovertemplate="%{customdata}<extra></extra>",
            colorscale="RdBu",
            zmid=0,
            zmin=-1,
            zmax=1,
            showscale=True,
            colorbar=dict(
                title=dict(text="Spearman r", side="right"),
                tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=["-1", "-0.5", "0", "+0.5", "+1"],
            ),
        )
    )
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=160, t=80, b=20),
        xaxis=dict(side="top", tickangle=-45),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig


def _build_scatter(df, x_col, metric_col) -> go.Figure:
    """Build a scatter plot of *x_col* vs. *metric_col*, colored by software tool.

    Parameters
    ----------
    df : pd.DataFrame
        Full datapoints DataFrame (after filter_data_point).
    x_col : str
        Parameter column for the x-axis.
    metric_col : str
        Performance metric column for the y-axis.

    Returns
    -------
    go.Figure
        Plotly figure with one trace per software tool.
    """
    metric_numeric = pd.to_numeric(df[metric_col], errors="coerce")
    valid = metric_numeric.notna() & df[x_col].notna()
    dfc = df[valid].copy()

    if dfc.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data for this parameter/metric combination.", showarrow=False)
        return fig

    x_numeric = pd.to_numeric(dfc[x_col], errors="coerce")
    x_is_numeric = x_numeric.notna().all() and not pd.api.types.is_bool_dtype(dfc[x_col])

    if x_is_numeric:
        x_vals = x_numeric
    else:
        x_vals = dfc[x_col].fillna("Not specified").astype(str)

    sw_col = dfc["software_name"].fillna("Unknown") if "software_name" in dfc.columns else pd.Series(
        ["Unknown"] * len(dfc), index=dfc.index
    )
    met_vals = pd.to_numeric(dfc[metric_col], errors="coerce")
    id_col = dfc["id"] if "id" in dfc.columns else pd.Series(["N/A"] * len(dfc), index=dfc.index)

    fig = go.Figure()
    for sw_name in sorted(sw_col.unique()):
        mask = sw_col == sw_name
        sw_x = x_vals[mask].values
        sw_y = met_vals[mask].values
        sw_xraw = dfc.loc[mask, x_col].values
        sw_ids = id_col[mask].values

        hover = []
        for xv, yv, pid in zip(sw_xraw, sw_y, sw_ids):
            y_str = f"{yv:.4f}" if pd.notna(yv) else "N/A"
            hover.append(f"<b>{sw_name}</b><br>{x_col}: {xv}<br>{metric_col}: {y_str}<br>ID: {pid}")

        fig.add_trace(
            go.Scatter(
                x=sw_x,
                y=sw_y,
                mode="markers",
                name=sw_name,
                marker=dict(color=QUANT_SOFTWARE_COLORS.get(sw_name, "#888888"), size=8, opacity=0.8),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hover,
            )
        )

    fig.update_layout(
        xaxis=dict(title=x_col),
        yaxis=dict(title=metric_col),
        height=420,
        margin=dict(l=60, r=20, t=30, b=60),
        legend=dict(title="Software"),
    )

    return fig


def _compute_pareto_front(df: pd.DataFrame, minimize_col: str, maximize_col: str) -> set:
    """Return the set of ``id`` values on the Pareto front.

    A point is Pareto-optimal if no other point is at least as good on both
    axes and strictly better on at least one.

    Parameters
    ----------
    df : pd.DataFrame
    minimize_col : str
        Metric to minimize (lower is better, e.g. median_abs_epsilon).
    maximize_col : str
        Metric to maximize (higher is better, e.g. nr_prec).

    Returns
    -------
    set
        Set of ``id`` strings that are not dominated.
    """
    dfc = df[["id", minimize_col, maximize_col]].copy()
    dfc[minimize_col] = pd.to_numeric(dfc[minimize_col], errors="coerce")
    dfc[maximize_col] = pd.to_numeric(dfc[maximize_col], errors="coerce")
    dfc = dfc.dropna()
    if dfc.empty:
        return set()
    vals = dfc[[minimize_col, maximize_col]].values
    ids = dfc["id"].values
    pareto_ids = []
    for i in range(len(vals)):
        dominated = False
        for j in range(len(vals)):
            if i == j:
                continue
            if vals[j, 0] <= vals[i, 0] and vals[j, 1] >= vals[i, 1]:
                if vals[j, 0] < vals[i, 0] or vals[j, 1] > vals[i, 1]:
                    dominated = True
                    break
        if not dominated:
            pareto_ids.append(ids[i])
    return set(pareto_ids)


def _compute_per_tool_pareto_fronts(
    df: pd.DataFrame, minimize_col: str, maximize_col: str
) -> dict:
    """Compute a Pareto front within each software tool's submissions.

    Parameters
    ----------
    df : pd.DataFrame
    minimize_col : str
    maximize_col : str

    Returns
    -------
    dict
        Mapping ``{software_name: set_of_ids}`` for tools with ≥ 2 submissions.
    """
    result = {}
    if "software_name" not in df.columns:
        return result
    for tool, group in df.groupby("software_name"):
        if len(group) < 2:
            continue
        ids = _compute_pareto_front(group, minimize_col, maximize_col)
        if ids:
            result[str(tool)] = ids
    return result


def _build_pareto_scatter(
    df: pd.DataFrame,
    minimize_col: str,
    maximize_col: str,
    pareto_ids: set,
    per_tool_fronts: dict = None,
) -> go.Figure:
    """Build a scatter showing all submissions with the Pareto front highlighted.

    Parameters
    ----------
    df : pd.DataFrame
    minimize_col : str
        Column on the x-axis (to minimize).
    maximize_col : str
        Column on the y-axis (to maximize).
    pareto_ids : set
        IDs of Pareto-optimal submissions (global front, used when *per_tool_fronts* is None).
    per_tool_fronts : dict, optional
        Mapping ``{software_name: set_of_ids}`` from ``_compute_per_tool_pareto_fronts``.
        When provided the plot shows per-tool frontiers instead of the global one.

    Returns
    -------
    go.Figure
    """
    dfc = df.copy()
    dfc[minimize_col] = pd.to_numeric(dfc[minimize_col], errors="coerce")
    dfc[maximize_col] = pd.to_numeric(dfc[maximize_col], errors="coerce")
    valid = dfc[minimize_col].notna() & dfc[maximize_col].notna()
    dfc = dfc[valid]

    if dfc.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data for this metric combination.", showarrow=False)
        return fig

    sw_col = (
        dfc["software_name"].fillna("Unknown")
        if "software_name" in dfc.columns
        else pd.Series(["Unknown"] * len(dfc), index=dfc.index)
    )
    id_col = (
        dfc["id"]
        if "id" in dfc.columns
        else pd.Series(["N/A"] * len(dfc), index=dfc.index)
    )

    fig = go.Figure()

    if per_tool_fronts is not None:
        # Per-tool mode: all points colored by tool; front points are larger/opaque.
        for sw_name in sorted(sw_col.unique()):
            tool_mask = sw_col == sw_name
            tool_df = dfc[tool_mask]
            tool_ids = id_col[tool_mask]
            tool_front_ids = per_tool_fronts.get(str(sw_name), set())
            color = QUANT_SOFTWARE_COLORS.get(sw_name, "#888888")

            front_mask = tool_ids.isin(tool_front_ids)
            bg_rows = tool_df[~front_mask]
            fg_rows = tool_df[front_mask]

            if not bg_rows.empty:
                bg_ids = tool_ids[~front_mask]
                fig.add_trace(
                    go.Scatter(
                        x=bg_rows[minimize_col].values,
                        y=bg_rows[maximize_col].values,
                        mode="markers",
                        name=sw_name,
                        showlegend=fg_rows.empty,
                        legendgroup=sw_name,
                        marker=dict(color=color, size=7, opacity=0.25),
                        hovertemplate="%{customdata}<extra></extra>",
                        customdata=[
                            f"<b>{sw_name}</b><br>{minimize_col}: {x:.4f}<br>{maximize_col}: {y}<br>ID: {pid}"
                            for x, y, pid in zip(
                                bg_rows[minimize_col].values,
                                bg_rows[maximize_col].values,
                                bg_ids.values,
                            )
                        ],
                    )
                )

            if not fg_rows.empty:
                fg_ids = tool_ids[front_mask]
                hover = [
                    f"<b>{sw_name}</b> ★<br>{minimize_col}: {x:.4f}<br>{maximize_col}: {y}<br>ID: {pid}"
                    for x, y, pid in zip(
                        fg_rows[minimize_col].values, fg_rows[maximize_col].values, fg_ids.values
                    )
                ]
                fig.add_trace(
                    go.Scatter(
                        x=fg_rows[minimize_col].values,
                        y=fg_rows[maximize_col].values,
                        mode="markers",
                        name=sw_name,
                        legendgroup=sw_name,
                        showlegend=True,
                        marker=dict(
                            color=color, size=11, opacity=1.0, line=dict(width=1, color="#333333")
                        ),
                        hovertemplate="%{customdata}<extra></extra>",
                        customdata=hover,
                    )
                )
                # Per-tool step-line.
                frontier = fg_rows.sort_values(minimize_col)
                fig.add_trace(
                    go.Scatter(
                        x=frontier[minimize_col].values,
                        y=frontier[maximize_col].values,
                        mode="lines",
                        line=dict(color=color, width=1.5, dash="dot"),
                        legendgroup=sw_name,
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

    else:
        # Global mode: non-Pareto gray cloud, Pareto colored by tool.
        non_pareto = dfc[~id_col.isin(pareto_ids)]
        pareto_df = dfc[id_col.isin(pareto_ids)]

        if not non_pareto.empty:
            np_sw = (
                sw_col[non_pareto.index].values if "software_name" in dfc.columns else ["Unknown"] * len(non_pareto)
            )
            fig.add_trace(
                go.Scatter(
                    x=non_pareto[minimize_col].values,
                    y=non_pareto[maximize_col].values,
                    mode="markers",
                    name="Other submissions",
                    marker=dict(color="#cccccc", size=7, opacity=0.4),
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=[
                        f"<b>{sw}</b><br>{minimize_col}: {x:.4f}<br>{maximize_col}: {y}<br>ID: {pid}"
                        for sw, x, y, pid in zip(
                            np_sw,
                            non_pareto[minimize_col].values,
                            non_pareto[maximize_col].values,
                            non_pareto["id"].values if "id" in non_pareto.columns else ["N/A"] * len(non_pareto),
                        )
                    ],
                )
            )

        if not pareto_df.empty:
            pareto_sw = sw_col[pareto_df.index]
            pareto_id_vals = id_col[pareto_df.index]
            for sw_name in sorted(pareto_sw.unique()):
                mask = pareto_sw == sw_name
                rows = pareto_df[mask]
                ids_sw = pareto_id_vals[mask]
                hover = [
                    f"<b>{sw_name}</b><br>{minimize_col}: {x:.4f}<br>{maximize_col}: {y}<br>ID: {pid}"
                    for x, y, pid in zip(rows[minimize_col].values, rows[maximize_col].values, ids_sw.values)
                ]
                fig.add_trace(
                    go.Scatter(
                        x=rows[minimize_col].values,
                        y=rows[maximize_col].values,
                        mode="markers",
                        name=sw_name,
                        marker=dict(
                            color=QUANT_SOFTWARE_COLORS.get(sw_name, "#888888"),
                            size=11,
                            opacity=1.0,
                            line=dict(width=1, color="#333333"),
                        ),
                        hovertemplate="%{customdata}<extra></extra>",
                        customdata=hover,
                    )
                )

            frontier = pareto_df.sort_values(minimize_col)
            fig.add_trace(
                go.Scatter(
                    x=frontier[minimize_col].values,
                    y=frontier[maximize_col].values,
                    mode="lines",
                    line=dict(color="#333333", width=1.5, dash="dot"),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    fig.update_layout(
        xaxis=dict(title=minimize_col),
        yaxis=dict(title=maximize_col),
        height=460,
        margin=dict(l=60, r=20, t=30, b=60),
        legend=dict(title="Software"),
    )
    return fig


def _build_recommendation_summary(df: pd.DataFrame, pareto_ids: set) -> pd.DataFrame:
    """Build a parameter recommendation table from Pareto-optimal submissions.

    For each key parameter, reports the most common value (categorical) or
    median with range (numeric) among Pareto-optimal workflows, along with a
    support count (how many of the Pareto workflows have that value set).

    Parameters
    ----------
    df : pd.DataFrame
    pareto_ids : set

    Returns
    -------
    pd.DataFrame
        Columns: Parameter, Recommended value, Support.
        Empty if no Pareto workflows have usable parameter values.
    """
    id_col = df["id"] if "id" in df.columns else pd.Series(dtype=str)
    pareto_df = df[id_col.isin(pareto_ids)].copy()
    n_pareto = len(pareto_df)

    _tol_splits = frozenset(f"{c}_{s}" for c in _TOL_COLS for s in ("min", "max"))
    params_present = [
        c for c in pareto_df.columns
        if (c in PARAMETER_COLS or c in _tol_splits)
        and c not in _TOL_COLS
        and c not in _PARETO_EXCLUDED_PARAMS
        and pareto_df[c].notna().any()
    ]

    rows = []
    for col in params_present:
        series = pareto_df[col].dropna()
        n_obs = len(series)
        if n_obs == 0:
            continue
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() >= n_obs * 0.8 and not pd.api.types.is_bool_dtype(pareto_df[col]):
            med = numeric.median()
            lo, hi = numeric.min(), numeric.max()
            rec = f"{med:.4g}"
            support = f"{lo:.4g} – {hi:.4g}" if lo != hi else ""
        else:
            mode_val = series.astype(str).mode()
            if mode_val.empty:
                continue
            top = mode_val.iloc[0]
            count = (series.astype(str) == top).sum()
            rec = top
            support = f"{count}/{n_pareto}"

        rows.append({"Parameter": col, "Recommended value": rec, "Pareto support": support})

    return pd.DataFrame(rows)


def _pareto_table_df(
    df: pd.DataFrame, pareto_ids: set, minimize_col: str, maximize_col: str
) -> pd.DataFrame:
    """Return a display-ready DataFrame of Pareto-optimal submissions.

    Parameters
    ----------
    df : pd.DataFrame
    pareto_ids : set
        IDs of Pareto-optimal submissions.
    minimize_col : str
    maximize_col : str

    Returns
    -------
    pd.DataFrame
        Sorted ascending by *minimize_col*.
    """
    id_col = df["id"] if "id" in df.columns else pd.Series(dtype=str)
    pareto_df = df[id_col.isin(pareto_ids)].copy()

    fixed_cols = [c for c in ["id", "software_name", "software_version", minimize_col, maximize_col] if c in pareto_df.columns]
    _tol_splits = frozenset(f"{c}_{s}" for c in _TOL_COLS for s in ("min", "max"))
    param_cols = [
        c for c in pareto_df.columns
        if (c in PARAMETER_COLS or c in _tol_splits)
        and c not in _TOL_COLS
        and c not in _PARETO_EXCLUDED_PARAMS
        and pareto_df[c].notna().any()
        and c not in fixed_cols
    ]
    cols = fixed_cols + [c for c in param_cols if c not in fixed_cols]

    result = pareto_df[cols].copy()
    for col in [minimize_col, maximize_col]:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").round(4)

    if minimize_col in result.columns:
        result = result.sort_values(minimize_col)

    return result.reset_index(drop=True)
