"""Tab for comparing two selected workflows."""

import glob
import os
import re
import uuid
import zipfile
from typing import Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def display_workflow_comparison(variables, ionmodule) -> None:
    """
    Display the workflow comparison interface with interactive selection.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys and configuration.
    ionmodule : object
        Module for accessing data and methods.
    """
    st.header("Workflow Comparison")
    st.markdown(
        """
        **Compare two workflows side-by-side:**
        - Click on points in the plot below to select workflows for comparison
        - Select exactly two points to see detailed comparison of results and parameters
        - **Precursor overlap**: Bar plot showing number of shared and unique precursors
        - **Parameter differences**: Table highlighting what differs between workflows
        """
    )

    # Initialize data
    _initialize_comparison_data(variables, ionmodule)

    # Display the selection plot
    selected_ids = _display_selection_plot(variables, ionmodule)

    # Show selection status
    _display_selection_status(selected_ids)

    # Perform comparison if two workflows are selected
    if len(selected_ids) == 2:
        st.markdown("---")
        _compare_workflows(variables, selected_ids[0], selected_ids[1])


def _initialize_comparison_data(variables, ionmodule) -> None:
    """Initialize the datapoints for comparison if not already loaded."""
    if variables.all_datapoints_submitted not in st.session_state:
        st.session_state[variables.all_datapoints_submitted] = None
        st.session_state[variables.all_datapoints_submitted] = ionmodule.obtain_all_data_points(
            all_datapoints=st.session_state[variables.all_datapoints_submitted]
        )

    # Initialize selection state
    selection_key = f"{variables.all_datapoints_submitted}_compare_selection"
    if selection_key not in st.session_state:
        st.session_state[selection_key] = []


def _display_selection_plot(variables, ionmodule) -> List[str]:
    """
    Display the interactive plot for selecting workflows to compare.

    Returns
    -------
    List[str]
        List of selected ProteoBench IDs
    """
    all_datapoints_submitted = st.session_state.get(variables.all_datapoints_submitted)

    if all_datapoints_submitted is None or all_datapoints_submitted.empty:
        st.warning("No datapoints available for comparison. Please check Tab 1.")
        return []

    # Apply filter based on slider if available
    slider_key = variables.slider_id_uuid
    if slider_key in st.session_state:
        slider_uuid = st.session_state[slider_key]
        if slider_uuid in st.session_state:
            min_prec = st.session_state[slider_uuid]
            filtered_data = ionmodule.filter_data_point(all_datapoints_submitted, min_prec)
        else:
            filtered_data = all_datapoints_submitted
    else:
        filtered_data = all_datapoints_submitted

    if filtered_data.empty:
        st.warning("No datapoints match the current filter criteria.")
        return []

    # Get metric settings
    metric = "Median"  # Default metric
    mode = "Global"  # Default mode

    st.subheader("Select Two Workflows to Compare")
    st.markdown("Click on points in the plot below. Your selections will be highlighted.")

    # Create unique key for this plot
    plot_key = f"{variables.all_datapoints}_compare_plot"
    if plot_key not in st.session_state:
        st.session_state[plot_key] = str(uuid.uuid4())

    # Generate the plot
    plot_generator = ionmodule.get_plot_generator()
    fig_metric = plot_generator.plot_main_metric(
        filtered_data,
        metric=metric,
        mode=mode,
        label="None",
        annotation="",
    )

    # Display plot with selection enabled
    event_dict = st.plotly_chart(
        fig_metric,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key=st.session_state[plot_key],
    )

    # Get current accumulated selections from session state
    selection_key = f"{variables.all_datapoints}_compare_selection"
    accumulated_selections = st.session_state.get(selection_key, [])

    # Extract newly clicked point IDs from the current event
    newly_selected_ids = []
    if "selection" in event_dict and "points" in event_dict["selection"]:
        points = event_dict["selection"]["points"]
        for point in points:
            hover = point.get("hovertext", "")
            match = re.search(r"ProteoBench ID: ([^<]+)", hover)
            if match:
                workflow_id = match.group(1)
                if workflow_id not in newly_selected_ids:
                    newly_selected_ids.append(workflow_id)

    # If a new point was clicked, add it to accumulated selections
    if newly_selected_ids:
        for new_id in newly_selected_ids:
            if new_id not in accumulated_selections:
                accumulated_selections.append(new_id)
                # Keep only the last 2 selections
                if len(accumulated_selections) > 2:
                    accumulated_selections = accumulated_selections[-2:]

        # Update session state
        st.session_state[selection_key] = accumulated_selections

    return accumulated_selections


def _display_selection_status(selected_ids: List[str]) -> None:
    """Display the current selection status."""
    st.subheader("Selected Workflows")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown("**Workflow 1:**")
        if len(selected_ids) >= 1:
            st.success(f"✓ {selected_ids[0]}")
        else:
            st.info("Click a point in the plot above")

    with col2:
        st.markdown("**Workflow 2:**")
        if len(selected_ids) >= 2:
            st.success(f"✓ {selected_ids[1]}")
        else:
            st.info("Click another point in the plot above")

    with col3:
        if len(selected_ids) > 0:
            # Use the proper selection key based on variables
            if st.button("Clear", key="clear_comparison_btn"):
                # Find all possible selection keys and clear them
                keys_to_clear = [key for key in st.session_state.keys() if key.endswith("_compare_selection")]
                for key in keys_to_clear:
                    st.session_state[key] = []
                st.rerun()


def _compare_workflows(variables, workflow_1_id: str, workflow_2_id: str) -> None:
    """
    Compare two workflows and display results.

    Parameters
    ----------
    variables : object
        Variables object containing session state keys.
    workflow_1_id : str
        ProteoBench ID of first workflow.
    workflow_2_id : str
        ProteoBench ID of second workflow.
    """
    st.subheader("Comparison Results")

    # Load data for both workflows
    workflow_1_data = _load_workflow_data(variables, workflow_1_id)
    workflow_2_data = _load_workflow_data(variables, workflow_2_id)

    if workflow_1_data is None or workflow_2_data is None:
        st.error("❌ Could not load data for one or both workflows.")
        return

    # Create comparison tabs
    comp_tab1, comp_tab2 = st.tabs(["Precursor Overlap", "Parameter Differences"])

    with comp_tab1:
        _display_precursor_overlap(workflow_1_id, workflow_1_data, workflow_2_id, workflow_2_data)

    with comp_tab2:
        _display_parameter_differences(workflow_1_id, workflow_1_data, workflow_2_id, workflow_2_data)


def _load_workflow_data(variables, workflow_id: str) -> Optional[Dict]:
    """
    Load workflow data from all_datapoints and storage.
    Metadata = Parameters and summary metrics from the workflow submission
    Performance data = Intermediate file for workflow
    Hash = Unique identifier of workflow

    Returns
    -------
    Optional[Dict]
        Dictionary with 'metadata', 'performance_data', and 'intermediate_hash' keys
    """
    all_datapoints_submitted = st.session_state.get(variables.all_datapoints_submitted)

    if all_datapoints_submitted is None or all_datapoints_submitted.empty:
        return None

    matching_rows = all_datapoints_submitted[all_datapoints_submitted["id"] == workflow_id]
    if matching_rows.empty:
        st.error(f"Could not find workflow: {workflow_id}")
        return None

    # something has to happen here in case the selected point is the local upload
    workflow_metadata = matching_rows.iloc[0]
    intermediate_hash = workflow_metadata["intermediate_hash"]

    if workflow_metadata["old_new"] == "new":
        # Load performance data from session state for new submissions
        performance_data = st.session_state[variables.result_perf]
    else:
        # Load performance data from storage
        performance_data = _load_performance_data_from_storage(intermediate_hash)

    if performance_data is None:
        return None

    return {
        "metadata": workflow_metadata,
        "performance_data": performance_data,
        "intermediate_hash": intermediate_hash,
    }


def _load_performance_data_from_storage(intermediate_hash: str) -> Optional[pd.DataFrame]:
    """Load performance data from storage."""
    if "storage" not in st.secrets or st.secrets["storage"].get("dir") is None:
        st.warning("⚠️ Storage directory not configured.")
        return None

    dataset_path = os.path.join(st.secrets["storage"]["dir"], intermediate_hash)
    pattern = os.path.join(dataset_path, "*_data.zip")
    zip_files = glob.glob(pattern)

    if not zip_files:
        st.warning(f"⚠️ Data files not found for hash: {intermediate_hash}")
        return None

    try:
        with zipfile.ZipFile(zip_files[0]) as z:
            with z.open("result_performance.csv") as f:
                return pd.read_csv(f)
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return None


def _display_precursor_overlap(
    workflow_1_id: str, workflow_1_data: Dict, workflow_2_id: str, workflow_2_data: Dict
) -> None:
    """Display precursor overlap using stacked bar chart."""
    st.markdown("### Precursor Overlap")
    st.markdown("Shows which precursors are shared or unique to each workflow.")

    perf_1 = workflow_1_data["performance_data"]
    perf_2 = workflow_2_data["performance_data"]

    # Find precursor column
    precursor_col = "precursor ion"

    precursors_1 = set(perf_1[precursor_col].dropna().unique())
    precursors_2 = set(perf_2[precursor_col].dropna().unique())

    # until the server files are resubmitted with correct proforma, we have to catch old strings here
    precursors_1 = set(p.replace("|Z=", "/") for p in precursors_1)
    precursors_2 = set(p.replace("|Z=", "/") for p in precursors_2)

    print(list(precursors_1)[:10])
    print(list(precursors_2)[:10])

    # Calculate overlap statistics
    overlap = len(precursors_1 & precursors_2)
    unique_1 = len(precursors_1 - precursors_2)
    unique_2 = len(precursors_2 - precursors_1)

    print("Unique to workflow 1:", precursors_1 - precursors_2)

    # Create stacked bar chart using Plotly
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name=f"Unique to {workflow_1_id}",
            x=["Precursor Distribution"],
            y=[unique_1],
            text=[unique_1],
            textposition="auto",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Shared",
            x=["Precursor Distribution"],
            y=[overlap],
            text=[overlap],
            textposition="auto",
        )
    )
    fig.add_trace(
        go.Bar(
            name=f"Unique to {workflow_2_id}",
            x=["Precursor Distribution"],
            y=[unique_2],
            text=[unique_2],
            textposition="auto",
        )
    )

    fig.update_layout(
        title="Precursor Overlap Distribution",
        barmode="stack",
        yaxis_title="Number of Precursors",
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary statistics
    st.markdown("#### Summary Statistics")
    col1, col2 = st.columns(2)

    overlap = len(precursors_1 & precursors_2)
    unique_1 = len(precursors_1 - precursors_2)
    unique_2 = len(precursors_2 - precursors_1)

    with col1:
        st.metric("Workflow 1 Total", len(precursors_1))
        st.metric(f"Unique to {workflow_1_id}", unique_1)

    with col2:
        st.metric("Workflow 2 Total", len(precursors_2))
        st.metric(f"Unique to {workflow_2_id}", unique_2)


def _display_parameter_differences(
    workflow_1_id: str, workflow_1_data: Dict, workflow_2_id: str, workflow_2_data: Dict
) -> None:
    """Display parameter differences between workflows."""
    st.markdown("### Parameter Differences")
    st.markdown(
        "Parameter comparison for new points is possible after uploading the parameter files in a public submission."
    )

    metadata_1 = workflow_1_data["metadata"]
    metadata_2 = workflow_2_data["metadata"]

    # Parameter columns to compare
    param_columns = [
        "software_name",
        "software_version",
        "search_engine",
        "search_engine_version",
        "ident_fdr_psm",
        "ident_fdr_peptide",
        "ident_fdr_protein",
        "enable_match_between_runs",
        "precursor_mass_tolerance",
        "fragment_mass_tolerance",
        "enzyme",
        "allowed_miscleavages",
        "min_peptide_length",
        "max_peptide_length",
        "fixed_mods",
        "variable_mods",
        "max_mods",
        "min_precursor_charge",
        "max_precursor_charge",
        "quantification_method",
        "protein_inference",
        "abundance_normalization_ions",
    ]

    existing_params = [col for col in param_columns if col in metadata_1.index and col in metadata_2.index]

    if not existing_params:
        st.warning("⚠️ No parameter columns found for comparison.")
        return

    # Build comparison table
    comparison_data = []
    for param in existing_params:
        val_1 = str(metadata_1.get(param, "N/A")) if pd.notna(metadata_1.get(param)) else "N/A"
        val_2 = str(metadata_2.get(param, "N/A")) if pd.notna(metadata_2.get(param)) else "N/A"

        is_different = val_1 != val_2

        comparison_data.append(
            {
                "Parameter": param.replace("_", " ").title(),
                workflow_1_id: val_1,
                workflow_2_id: val_2,
                "Different": "✓" if is_different else "",
            }
        )

    comparison_df = pd.DataFrame(comparison_data)

    # Filter option
    show_all = st.checkbox("Show all parameters", value=False)
    if not show_all:
        comparison_df = comparison_df[comparison_df["Different"] == "✓"]

    if comparison_df.empty:
        st.info("✓ All compared parameters are identical.")
    else:
        if not show_all:
            st.markdown(f"**{len(comparison_df)} parameter(s) differ:**")
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    # Performance metrics comparison
    st.markdown("#### Performance Metrics Comparison")
    _display_metrics_comparison(workflow_1_id, metadata_1, workflow_2_id, metadata_2)


def _display_metrics_comparison(
    workflow_1_id: str, metadata_1: pd.Series, workflow_2_id: str, metadata_2: pd.Series
) -> None:
    """Display performance metrics comparison."""
    metric_keys = [
        ("median_abs_epsilon_global", "Median Abs Epsilon (Global)"),
        ("mean_abs_epsilon_global", "Mean Abs Epsilon (Global)"),
        ("median_abs_epsilon_eq_species", "Median Abs Epsilon (Species-weighted)"),
        ("mean_abs_epsilon_eq_species", "Mean Abs Epsilon (Species-weighted)"),
    ]

    metrics_comparison = []
    for key, label in metric_keys:
        val_1 = _extract_metric(metadata_1, key)
        val_2 = _extract_metric(metadata_2, key)

        if val_1 is not None and val_2 is not None:
            diff = val_2 - val_1
            diff_pct = (diff / val_1 * 100) if val_1 != 0 else 0

            metrics_comparison.append(
                {
                    "Metric": label,
                    workflow_1_id: f"{val_1:.4f}",
                    workflow_2_id: f"{val_2:.4f}",
                    "Difference": f"{diff:+.4f} ({diff_pct:+.1f}%)",
                }
            )

    if metrics_comparison:
        metrics_df = pd.DataFrame(metrics_comparison)
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    else:
        st.info("Metrics data not available for comparison.")


def _extract_metric(metadata: pd.Series, key: str) -> Optional[float]:
    """Extract a metric value from metadata."""
    # Check if directly available
    if key in metadata.index and pd.notna(metadata[key]):
        return float(metadata[key])

    # Try to extract from results dict (default min_prec=3)
    if "results" in metadata.index:
        results = metadata["results"]
        if isinstance(results, dict) and 3 in results and key in results[3]:
            return float(results[3][key])

    return None
