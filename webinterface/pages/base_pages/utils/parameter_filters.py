"""
Parameter-based filtering for benchmark datapoints.

Provides both the pure filtering logic (``apply_parameter_filters``) and
the Streamlit UI rendering (``generate_parameter_filters``).
"""

import re
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from proteobench.io.params import _AUTO_CALIBRATION_LABEL

_NOT_SPECIFIED = "Not specified"

_PARAMETER_FILTERS = [
    {"col": "software_name", "label": "Software tool", "type": "multiselect"},
    {"col": "enable_match_between_runs", "label": "Match between runs", "type": "radio_bool"},
    {"col": "search_engine", "label": "Search engine", "type": "multiselect"},
    {"col": "enzyme", "label": "Enzyme", "type": "multiselect"},
    {"col": "allowed_miscleavages", "label": "Allowed miscleavages", "type": "max_slider"},
    {"col": "ident_fdr_psm", "label": "PSM FDR", "type": "max_slider"},
    {"col": "ident_fdr_peptide", "label": "Peptide FDR", "type": "max_slider"},
    {"col": "ident_fdr_protein", "label": "Protein FDR", "type": "max_slider"},
    {"col": "quantification_method", "label": "Quantification method", "type": "multiselect"},
    {"col": "precursor_mass_tolerance", "label": "Precursor mass tol.", "type": "tolerance_range"},
    {"col": "fragment_mass_tolerance", "label": "Fragment mass tol.", "type": "tolerance_range"},
    {
        "col_min": "min_peptide_length",
        "col_max": "max_peptide_length",
        "label": "Peptide length",
        "type": "combined_range",
    },
    {"col": "max_mods", "label": "Max mods per peptide", "type": "max_slider"},
    {
        "col_min": "min_precursor_charge",
        "col_max": "max_precursor_charge",
        "label": "Precursor charge",
        "type": "combined_range",
    },
    {
        "col_min": "min_precursor_mz",
        "col_max": "max_precursor_mz",
        "label": "Precursor m/z",
        "type": "combined_range",
    },
    {
        "col_min": "min_fragment_mz",
        "col_max": "max_fragment_mz",
        "label": "Fragment m/z",
        "type": "combined_range",
    },
]


def _get_unique_values(series: pd.Series) -> List[str]:
    """Return sorted unique string values from *series*, mapping NaN to _NOT_SPECIFIED."""
    values = series.fillna(_NOT_SPECIFIED).astype(str).unique()
    return sorted(values, key=lambda v: (v == _NOT_SPECIFIED, v))


# Pattern to extract numeric value + unit pairs from tolerance strings.
_TOL_VALUE_PATTERN = re.compile(
    r"([+-]?\d+(?:\.\d+)?)\s*(ppm|da|th)",
    re.IGNORECASE,
)


def _parse_tolerance(val: str) -> Optional[tuple]:
    """Parse a tolerance string and return ``(min_value, max_value, unit_lower)`` or *None*.

    For symmetric strings like ``"[-10 ppm, 10 ppm]"`` returns ``(-10.0, 10.0, "ppm")``.
    For single-value strings like ``"20 ppm"`` returns ``(-20.0, 20.0, "ppm")``.
    Returns *None* for non-parseable values (e.g. ``"Automatic calibration"``).
    """
    if not isinstance(val, str) or val == _AUTO_CALIBRATION_LABEL:
        return None
    matches = _TOL_VALUE_PATTERN.findall(val)
    if not matches:
        return None
    unit = matches[0][1].lower()
    values = sorted(float(m[0]) for m in matches)
    if len(values) == 1:
        v = abs(values[0])
        return -v, v, unit
    return values[0], values[-1], unit


def apply_parameter_filters(
    data: pd.DataFrame,
    filter_selections: Dict[str, Any],
) -> pd.DataFrame:
    """
    Apply parameter-based filters to a DataFrame of benchmark datapoints.

    Parameters
    ----------
    data : pd.DataFrame
        The benchmark datapoints to filter.
    filter_selections : dict
        Mapping of column name to the selected filter value(s).

    Returns
    -------
    pd.DataFrame
        The subset of *data* matching all active filters.
    """
    if data.empty:
        return data

    mask = pd.Series(True, index=data.index)

    for spec in _PARAMETER_FILTERS:
        if spec["type"] == "combined_range":
            col_min = spec["col_min"]
            col_max = spec["col_max"]
            filter_key = f"{col_min}__{col_max}"
            if filter_key not in filter_selections:
                continue
            selection = filter_selections[filter_key]
            if isinstance(selection, (list, tuple)) and len(selection) == 2:
                lo, hi = selection
                if col_min in data.columns:
                    mask &= pd.to_numeric(data[col_min], errors="coerce").fillna(lo) >= lo
                if col_max in data.columns:
                    mask &= pd.to_numeric(data[col_max], errors="coerce").fillna(hi) <= hi
            continue

        if spec["type"] == "tolerance_range":
            col = spec["col"]
            if col not in data.columns:
                continue
            auto_key = f"{col}__auto"
            include_auto = filter_selections.get(auto_key, True)
            row_mask = pd.Series(True, index=data.index)
            for idx_row, val in data[col].items():
                if val == _AUTO_CALIBRATION_LABEL:
                    row_mask[idx_row] = include_auto
                    continue
                parsed = _parse_tolerance(val)
                if parsed is None:
                    continue
                min_val, max_val, unit = parsed
                unit_key = f"{col}__{unit}"
                if unit_key not in filter_selections:
                    continue
                sel_lo, sel_hi = filter_selections[unit_key]
                if min_val < sel_lo or max_val > sel_hi:
                    row_mask[idx_row] = False
            mask &= row_mask
            continue

        col = spec.get("col")
        if col is None or col not in filter_selections or col not in data.columns:
            continue

        selection = filter_selections[col]

        if spec["type"] == "radio_bool":
            if selection == "Enabled":
                mask &= data[col].astype(bool)
            elif selection == "Disabled":
                mask &= ~data[col].astype(bool)

        elif spec["type"] == "multiselect":
            if isinstance(selection, list):
                str_col = data[col].fillna(_NOT_SPECIFIED).astype(str)
                mask &= str_col.isin(selection)

        elif spec["type"] == "select_slider":
            if isinstance(selection, (list, tuple)) and len(selection) == 2:
                lo, hi = selection
                mask &= data[col].fillna(lo).between(lo, hi)

        elif spec["type"] == "max_slider":
            threshold = selection
            mask &= pd.to_numeric(data[col], errors="coerce").fillna(0) <= threshold

    return data.loc[mask]


def generate_parameter_filters(
    data: pd.DataFrame,
    key_prefix: str = "param_filter",
    pinned_indices: Optional[pd.Index] = None,
) -> pd.DataFrame:
    """
    Render parameter-based filter widgets and return the filtered DataFrame.

    Parameters
    ----------
    data : pd.DataFrame
        Benchmark datapoints (already filtered by the k-slider).
    key_prefix : str, optional
        Prefix for Streamlit session-state keys to avoid collisions.
    pinned_indices : pd.Index, optional
        Row indices that must always be included in the result regardless of
        filter settings (e.g. a newly submitted datapoint in tab 4).

    Returns
    -------
    pd.DataFrame
        The subset of *data* matching all active parameter filters,
        plus any *pinned_indices* rows.
    """
    if data.empty:
        return data

    total_count = len(data)

    # Determine which filters are applicable for this dataset
    applicable: List[dict] = []
    for spec in _PARAMETER_FILTERS:
        if spec["type"] == "combined_range":
            col_min, col_max = spec["col_min"], spec["col_max"]
            has_min = col_min in data.columns and data[col_min].dropna().nunique() >= 1
            has_max = col_max in data.columns and data[col_max].dropna().nunique() >= 1
            if has_min or has_max:
                all_vals = set()
                if has_min:
                    all_vals.update(data[col_min].dropna().unique())
                if has_max:
                    all_vals.update(data[col_max].dropna().unique())
                if len(all_vals) >= 2:
                    applicable.append(spec)
        else:
            col = spec["col"]
            if col not in data.columns:
                continue
            n_unique = data[col].dropna().nunique()
            if n_unique < 2:
                continue
            applicable.append(spec)

    if not applicable:
        return data

    filter_selections: Dict[str, Any] = {}

    with st.expander("Filter by workflow parameters", expanded=False):
        # Reset button
        if st.button("Reset all filters", key=f"{key_prefix}_reset"):
            for spec in applicable:
                if spec["type"] == "combined_range":
                    sk = f"{key_prefix}_{spec['col_min']}__{spec['col_max']}"
                    for k in list(st.session_state):
                        if k == sk:
                            del st.session_state[k]
                elif spec["type"] == "tolerance_range":
                    prefix = f"{key_prefix}_{spec['col']}"
                    for k in list(st.session_state):
                        if k.startswith(prefix):
                            del st.session_state[k]
                else:
                    sk = f"{key_prefix}_{spec['col']}"
                    if sk in st.session_state:
                        del st.session_state[sk]
            st.rerun()

        # Lay out filters in a 3-column grid
        cols = st.columns(3)
        for idx, spec in enumerate(applicable):
            label = spec["label"]

            with cols[idx % 3]:
                if spec["type"] == "combined_range":
                    col_min, col_max = spec["col_min"], spec["col_max"]
                    filter_key = f"{col_min}__{col_max}"
                    sk = f"{key_prefix}_{filter_key}"
                    all_vals = set()
                    if col_min in data.columns:
                        nums = pd.to_numeric(data[col_min], errors="coerce").dropna()
                        all_vals.update(int(x) for x in nums.unique())
                    if col_max in data.columns:
                        nums = pd.to_numeric(data[col_max], errors="coerce").dropna()
                        all_vals.update(int(x) for x in nums.unique())
                    all_options = sorted(all_vals)
                    full_range = (all_options[0], all_options[-1])
                    default = st.session_state.get(sk, full_range)
                    selected = st.select_slider(
                        label,
                        options=all_options,
                        value=default,
                        key=sk,
                    )
                    filter_selections[filter_key] = selected

                elif spec["type"] == "radio_bool":
                    col_name = spec["col"]
                    sk = f"{key_prefix}_{col_name}"
                    default = st.session_state.get(sk, "All")
                    choice = st.radio(
                        label,
                        ["All", "Enabled", "Disabled"],
                        index=["All", "Enabled", "Disabled"].index(default),
                        key=sk,
                        horizontal=True,
                    )
                    filter_selections[col_name] = choice

                elif spec["type"] == "multiselect":
                    col_name = spec["col"]
                    sk = f"{key_prefix}_{col_name}"
                    all_options = _get_unique_values(data[col_name])
                    default = st.session_state.get(sk, all_options)
                    selected = st.multiselect(
                        label,
                        options=all_options,
                        default=default,
                        key=sk,
                    )
                    filter_selections[col_name] = selected

                elif spec["type"] == "select_slider":
                    col_name = spec["col"]
                    sk = f"{key_prefix}_{col_name}"
                    all_options = sorted(data[col_name].dropna().unique())
                    if len(all_options) < 2:
                        continue
                    full_range = (all_options[0], all_options[-1])
                    default = st.session_state.get(sk, full_range)
                    selected = st.select_slider(
                        label,
                        options=all_options,
                        value=default,
                        key=sk,
                    )
                    filter_selections[col_name] = selected

                elif spec["type"] == "max_slider":
                    col_name = spec["col"]
                    sk = f"{key_prefix}_{col_name}"
                    numeric_vals = pd.to_numeric(data[col_name], errors="coerce").dropna()
                    all_options = sorted(numeric_vals.unique())
                    if len(all_options) < 2:
                        continue
                    max_val = all_options[-1]
                    default = st.session_state.get(sk, max_val)
                    selected = st.select_slider(
                        f"{label} \u2264",
                        options=all_options,
                        value=default,
                        key=sk,
                    )
                    filter_selections[col_name] = selected

                elif spec["type"] == "tolerance_range":
                    col_name = spec["col"]
                    parsed = data[col_name].dropna().apply(_parse_tolerance)
                    has_auto = (data[col_name] == _AUTO_CALIBRATION_LABEL).any()

                    vals_by_unit: Dict[str, List[float]] = {}
                    for p in parsed.dropna():
                        min_val, max_val, unit = p
                        vals_by_unit.setdefault(unit, []).extend([min_val, max_val])

                    if has_auto:
                        sk_auto = f"{key_prefix}_{col_name}_auto"
                        default_auto = st.session_state.get(sk_auto, True)
                        include_auto = st.checkbox(
                            f"{label}: include auto-calibrated",
                            value=default_auto,
                            key=sk_auto,
                        )
                        filter_selections[f"{col_name}__auto"] = include_auto

                    for unit in sorted(vals_by_unit):
                        all_vals = sorted(set(vals_by_unit[unit]))
                        if len(all_vals) < 2:
                            continue
                        sk_unit = f"{key_prefix}_{col_name}_{unit}"
                        full_range = (all_vals[0], all_vals[-1])
                        default_range = st.session_state.get(sk_unit, full_range)
                        selected = st.select_slider(
                            f"{label} ({unit})",
                            options=all_vals,
                            value=default_range,
                            key=sk_unit,
                        )
                        filter_selections[f"{col_name}__{unit}"] = selected

        filtered = apply_parameter_filters(data, filter_selections)

        # Always include pinned rows (e.g. new submission in tab 4)
        if pinned_indices is not None:
            missing = pinned_indices.difference(filtered.index)
            if len(missing):
                filtered = pd.concat([filtered, data.loc[missing]])

        filtered_count = len(filtered)
        st.caption(f"Showing {filtered_count} of {total_count} datapoints")

    return filtered
