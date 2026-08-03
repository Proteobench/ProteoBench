"""
Plot generator for LFQ PYE (Plasma-Yeast-Ecoli) quantification modules.
"""

import textwrap
from typing import Dict, List, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.figure_factory import create_distplot

from proteobench.plotting.plot_generator_base import PlotGeneratorBase


#: Species present in the PYE (Plasma/Yeast/E. coli) sample, plasma background first.
PYE_SPECIES_ORDER = ("HUMAN", "YEAST", "ECOLI")

#: Human-readable explanation of the human-plasma dynamic range metric. Used both as the
#: tooltip of the main overview plot and in the in-depth plot descriptions.
DYNAMIC_RANGE_EXPLANATION = (
    "Dynamic range of the human plasma background: for each condition the log10-transformed "
    "mean precursor intensities of the HUMAN precursors are taken, and the difference between "
    "their 90th and 10th percentile is computed. The two condition-wise values (A and B) are "
    "then averaged. The value is therefore expressed in orders of magnitude (log10 units): a "
    "dynamic range of 3.0 means that the central 80% of the quantified plasma precursors span "
    "three orders of magnitude in intensity. Larger values indicate that a workflow quantifies "
    "both high-abundant and low-abundant plasma precursors."
)

#: Opacity range used to encode human-plasma quantification accuracy in the overview plot.
#: The most accurate workflow in the loaded set is drawn fully opaque, the least accurate one
#: at OPACITY_MIN, so differences remain visible regardless of the absolute error range.
OPACITY_MIN = 0.2
OPACITY_MAX = 1.0


class LFQPYEPlotGenerator(PlotGeneratorBase):
    """
    Plot generator for LFQ PYE (Plasma-Yeast-Ecoli) quantification modules.
    Used by plasma benchmarking modules that use human plasma, yeast, and E. coli species.
    """

    def __init__(self, y_axis_title: str = "Number of quantified spike-in precursors"):
        self.y_axis_title = y_axis_title

    def generate_in_depth_plots(
        self, performance_data: pd.DataFrame, parse_settings: any, **kwargs
    ) -> Dict[str, go.Figure]:
        """
        Generate standard LFQ PYE plots from intermediate data.

        Parameters
        ----------
        performance_data : pd.DataFrame
            The intermediate performance data to plot
        parse_settings : ParseSettings
            The parse settings for the module
        **kwargs : dict
            Additional module-specific parameters

        Returns
        -------
        Dict[str, go.Figure]
            Dictionary mapping plot names to plotly figures
        """
        plots = {}

        # Get expected ratios from parse settings if available
        try:
            species_expected_ratio = parse_settings.species_expected_ratio()
        except:
            species_expected_ratio = {}

        # Generate fold change histogram
        plots["logfc"] = self._plot_fold_change_histogram(performance_data, species_expected_ratio)

        # Generate CV violin plot
        plots["cv"] = self._plot_cv_violinplot(performance_data)

        plots["ma_plot"] = self._plot_ma_plot(performance_data, species_expected_ratio)

        plots["dynamic_range_plot"] = self._plot_dynamic_range(performance_data, species_expected_ratio)

        plots["missing_values_plot"] = self._plot_missing_values(performance_data)

        plots["signed_epsilon_plot"] = self._plot_signed_epsilon(performance_data, species_expected_ratio)

        return plots

    def get_in_depth_plot_layout(self) -> list:
        """
        Define layout for LFQ PYE plots.

        Returns
        -------
        list
            List of in-depth plot configurations defining how plots should be displayed
        """
        return [
            {
                "plots": ["dynamic_range_plot", "missing_values_plot"],
                "columns": 2,
                "titles": {
                    "dynamic_range_plot": "Abundance range per species (Condition A and B combined).",
                    "missing_values_plot": "Missing Values Distribution across runs.",
                },
            },
            {
                "plots": ["logfc", "cv"],
                "columns": 2,
                "titles": {
                    "logfc": "Log2 Fold Change distributions by species (Human plasma, Yeast, E. coli).",
                    "cv": "Coefficient of variation distribution in Condition A and B.",
                },
            },
            {
                "plots": ["signed_epsilon_plot"],
                "columns": 1,
                "titles": {
                    "signed_epsilon_plot": "Over- and underestimation of the log2 fold change (signed epsilon).",
                },
            },
            {
                "plots": ["ma_plot"],
                "columns": 1,
                "titles": {
                    "ma_plot": "MA Plot",
                },
            },
        ]

    def get_in_depth_plot_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for each plot.

        Returns
        -------
        Dict[str, str]
            Dictionary mapping plot names to their descriptions
        """
        return {
            "logfc": "log2 fold changes calculated from the intermediate data",
            "cv": "CVs calculated from the intermediate data",
            "ma_plot": "MA plot (M vs A plot) showing log2 fold changes against mean abundance",
            "dynamic_range_plot": (
                "Precursor intensities ranked within each species, next to the rolling median of the "
                "absolute epsilon. "
            ),
            "missing_values_plot": "Distribution of missing values (%) of quantified human precursors",
            "signed_epsilon_plot": (
                "Distribution of the signed epsilon (measured minus expected log2 fold change) per species. "
                "Values below zero indicate that the log2 fold change is underestimated, values above zero "
                "that it is overestimated. A distribution centred on zero indicates an unbiased workflow. "
                "Note that ratio compression shifts the two spike-in species in opposite directions, "
                "because YEAST is expected below zero (log2FC = -1.585) and ECOLI above zero (log2FC = 1)."
            ),
        }

    def get_metrics_help_markdown(self) -> str:
        """
        Return a Markdown explanation of how the metrics of the main plot are calculated.

        Returns
        -------
        str
            The Markdown explanation shown in the "How are the metrics calculated?" popover.
        """
        return """
            **X-axis** - absolute log2 fold-change error of the spike-ins (YEAST and ECOLI),
            reported as median or mean, either globally or as an equally weighted average per
            species.

            **Y-axis** - number of quantified spike-in precursor ions (YEAST plus ECOLI). The
            counts per individual species (HUMAN, YEAST, ECOLI) are listed in the hover text of
            each point and in the results table.

            **Marker size** - dynamic range of the human plasma background. For each condition
            the mean intensities of the HUMAN precursors are log10-transformed, and the
            difference between the 90th and the 10th percentile is calculated. The values of
            condition A and B are then averaged:

            `dynamic_range = mean( P90(log10 I_A) - P10(log10 I_A), P90(log10 I_B) - P10(log10 I_B) )`

            The value is expressed in orders of magnitude: a dynamic range of 3.0 means that the
            central 80% of the quantified plasma precursors span three orders of magnitude in
            intensity. Larger markers therefore indicate that a workflow quantifies both
            high-abundant and low-abundant plasma precursors.

            **Marker opacity** - median or mean absolute epsilon of the HUMAN plasma precursors.
            Darker markers indicate a more accurate quantification of the plasma background.

            Marker size and marker opacity are min-max normalised over the datapoints that are
            currently loaded, so the visual differences reflect the ranking within the displayed
            set rather than an absolute scale. The hover text always reports the raw values.
            """

    def get_in_depth_metrics_help_markdown(self) -> str:
        """
        Return a Markdown explanation of how the in-depth plots are calculated.

        Returns
        -------
        str
            The Markdown explanation shown in the "How are the metrics calculated?" popover on the
            in-depth tab.
        """
        return """
            The plots on this tab describe **one single benchmark run** instead of comparing runs,
            and every point in them is one precursor ion rather than one workflow. They are computed
            from the intermediate table shown further down this page, which can be downloaded for
            your own analysis.

            All of them start from the same per-precursor quantities. For each condition, the
            intensities of a precursor over the six raw files of that condition are summarised as:

            - `Intensity_mean` and `Intensity_std` - mean and standard deviation of the raw
              intensities.
            - `log_Intensity_mean` - mean of the log2-transformed intensities.
            - `CV = Intensity_std / Intensity_mean` - the coefficient of variation, computed on the
              raw (not log-transformed) intensities.
            - `nr_observed` - in how many of the 12 raw files the precursor was quantified. Missing
              values are never imputed, they are simply left out of these summaries.

            The measured fold change is then the difference of the two condition means on the log2
            scale, and the deviation from the ground truth is epsilon:

            `log2_A_vs_B = log_Intensity_mean_A - log_Intensity_mean_B`

            `epsilon = log2_A_vs_B - log2(expected ratio A/B)`

            The expected ratios are 1:1 for HUMAN plasma, 1:3 for YEAST (log2FC = -1.585) and 2:1 for
            ECOLI (log2FC = 1).

            **Abundance range per species** - precursors are ranked by their mean intensity over both
            conditions, and their intensity is normalised against the highest intensity over all
            species. The rank is assigned within the species selected in the dropdown, so the x-axis
            runs from 1 to the number of precursors quantified for that species. The dashed line on
            the right-hand axis is the rolling median of the absolute epsilon over that ranking, which
            shows how the quantification error grows towards the low-abundance end. This is the plot
            behind the dynamic-range metric encoded in the marker size of the overview plot.

            **Missing values distribution** - HUMAN precursors ranked by mean abundance against their
            percentage of missing values, computed as `(1 - nr_observed / 12) * 100`. The solid line
            is the rolling median. In a plasma background missingness concentrates at the
            low-abundance end, so this shows how deep into the background a workflow quantifies
            consistently.

            **Log2 fold change distribution** - a kernel density estimate of `log2_A_vs_B` per
            species, shown over a fixed x-range of -4 to 4, with dashed vertical lines at the expected
            ratios. Because these are densities, each is normalised to an area of one, so the curve
            heights say nothing about how many precursors each species contributed.

            **Coefficient of variation** - a violin plot of the `CV_A` and `CV_B` values, with the
            embedded box showing the quartiles. Infinite values (a precursor quantified in only one
            run of a condition, so without a defined standard deviation) are dropped. This measures
            technical reproducibility within a condition, independently of the ground truth.

            **Signed epsilon** - the same epsilon values as above, but keeping their sign instead of
            taking the absolute value, shown per species as a violin with an embedded box plot and a
            reference line at zero. Negative values mean the log2 fold change is underestimated,
            positive values that it is overestimated. Each species is annotated with its median signed
            epsilon and the percentage of precursors on either side of zero. Note that ratio
            compression moves the two spike-in species in opposite directions, because YEAST is
            expected below zero and ECOLI above zero.

            **MA plot** - each precursor is drawn with its measured fold change on the x-axis and its
            mean abundance on the y-axis, calculated as the average of `log_Intensity_mean_A` and
            `log_Intensity_mean_B`. This shows whether the quantification error depends on abundance.

            Unlike the overview plot, these plots use all precursors of the run: they are not filtered
            by the minimal-quantifications slider.
            """

    def _plot_fold_change_histogram(
        self, performance_data: pd.DataFrame, species_expected_ratio: Dict[str, Dict[str, Union[float, str]]]
    ) -> go.Figure:
        """
        Generate fold change histogram plot.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Intermediate data containing log2_A_vs_B column
        species_expected_ratio : Dict[str, Dict[str, Union[float, str]]]
            Dictionary with expected ratios for each species, and colors

        Returns
        -------
        go.Figure
            Plotly figure with fold change distributions
        """
        species_list = list(species_expected_ratio.keys())

        # Filter to rows where at least one species is present
        species_cols = [s for s in species_list if s in performance_data.columns]
        if not species_cols:
            # If no species columns, create empty figure
            fig = go.Figure()
            fig.add_annotation(
                text="No species data available for fold change plot",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        performance_data_filtered = performance_data[performance_data[species_cols].any(axis=1)].copy()
        performance_data_filtered["species"] = performance_data_filtered[species_cols].apply(
            lambda x: species_cols[np.argmax(x)], axis=1
        )

        # Prepare plot data
        hist_data = []
        group_labels = []
        colors = []

        for species in species_list:
            if species in performance_data_filtered.columns or species in species_expected_ratio:
                species_data = (
                    performance_data_filtered.loc[performance_data_filtered["species"] == species, "log2_A_vs_B"]
                    .dropna()
                    .tolist()
                )
                if species_data:
                    hist_data.append(species_data)
                    group_labels.append(species)
                    if species_expected_ratio and species in species_expected_ratio:
                        colors.append(species_expected_ratio[species].get("color", "#000000"))
                    else:
                        colors.append("#000000")

        # Create distribution plot
        if hist_data:
            fig = create_distplot(
                hist_data,
                group_labels,
                show_hist=False,
                show_rug=False,
                colors=colors,
            )

            for trace in fig.data:
                if trace.mode == "lines":
                    trace.update(fill="tozeroy", opacity=0.4)

            fig.update_layout(
                xaxis=dict(
                    title="Log2(Condition A / Condition B)",
                    color="black",
                    gridwidth=1,
                    gridcolor="lightgray",
                    range=[-4, 4],
                ),
                yaxis=dict(title="Density", color="black", gridwidth=1, gridcolor="lightgray"),
            )

            # Add expected ratio lines if available
            if species_expected_ratio:
                ratio_map = {species: np.log2(data["A_vs_B"]) for species, data in species_expected_ratio.items()}
                for species, ratio in ratio_map.items():
                    fig.add_vline(
                        x=ratio,
                        line_dash="dash",
                        line_color=species_expected_ratio[species].get("color", "#000000"),
                        annotation_text=f"Expected {species}",
                    )
        else:
            # Create empty figure if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for fold change plot",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )

        return fig

    def _plot_cv_violinplot(self, performance_data: pd.DataFrame) -> go.Figure:
        """
        Generate coefficient of variation violin plot.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Intermediate data containing CV_A and CV_B columns

        Returns
        -------
        go.Figure
            Plotly figure with CV violin plots
        """
        # Prepare data for violin plot
        cv_data = []
        conditions = []

        # Add CV data for Condition A
        if "CV_A" in performance_data.columns:
            cv_a = performance_data["CV_A"].replace([np.inf, -np.inf], np.nan).dropna()
            cv_data.extend(cv_a)
            conditions.extend(["Condition A"] * len(cv_a))

        # Add CV data for Condition B
        if "CV_B" in performance_data.columns:
            cv_b = performance_data["CV_B"].replace([np.inf, -np.inf], np.nan).dropna()
            cv_data.extend(cv_b)
            conditions.extend(["Condition B"] * len(cv_b))

        # Create violin plot
        if cv_data:
            df_plot = pd.DataFrame({"CV": cv_data, "Condition": conditions})

            fig = px.violin(df_plot, y="CV", x="Condition", box=True, points=False)
        else:
            # Create empty figure if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No CV data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )

        return fig

    def _plot_ma_plot(
        self, performance_data: pd.DataFrame, species_expected_ratio: Dict[str, Dict[str, Union[float, str]]]
    ) -> go.Figure:
        """
        Generate MA plot (M vs A plot) but with A on the y-axis and M on the x-axis.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Performance data containing log2_A_vs_B and mean abundance columns
        species_expected_ratio : Dict[str, Dict[str, Union[float, str]]]
            Expected ratios for each species and their colors

        Returns
        -------
        go.Figure
            Plotly figure with MA plot (M on x, A on y)
        """
        fig = go.Figure()

        # Define colors for species
        color_map = {species: data["color"] for species, data in species_expected_ratio.items()}

        performance_data["logIntensityMean"] = (
            performance_data["log_Intensity_mean_A"] + performance_data["log_Intensity_mean_B"]
        ) / 2

        fig = px.scatter(
            performance_data,
            x="log2_A_vs_B",
            y="logIntensityMean",
            color="species",
            color_discrete_map=color_map,
            labels={"log2_A_vs_B": "M (Log2 Fold Change(A:B))", "logIntensityMean": "A (Mean Abundance)"},
            title="MA Plot",
            size_max=10,
            opacity=0.2,
        )

        # Add vertical lines for expected M values (since M is on x-axis) across the A range
        if fig.data:
            ratio_map = {species: np.log2(data["A_vs_B"]) for species, data in species_expected_ratio.items()}
            for species, ratio in ratio_map.items():
                fig.add_vline(
                    x=ratio,
                    line_dash="dash",
                    line_color=species_expected_ratio[species].get("color", "#000000"),
                    annotation_text=f"Expected {species}",
                )

            fig.update_traces(marker=dict(size=6))
        else:
            fig.add_annotation(
                text="No data available for MA plot",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        return fig

    def _plot_dynamic_range(self, performance_data: pd.DataFrame, species_expected_ratio: any) -> go.Figure:
        """
        Generate the abundance range plot, with a smoothed epsilon trend on a secondary y-axis.

        Precursors are ranked by their mean intensity across conditions A and B. The rank is
        assigned **within each species**, so the count axis of the selected species always runs
        from 1 to the number of precursors quantified for that species. The intensities remain
        normalised against the highest intensity over all species, so that the species can still
        be compared on a common intensity scale.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Performance data containing the mean intensities per condition, the species
            annotation and the epsilon column.
        species_expected_ratio : any
            Expected ratios for each species and their colors, used for the trace colors.

        Returns
        -------
        go.Figure
            Plotly figure with the abundance range per species and the epsilon trend.
        """
        fig = go.Figure()

        # Process data for both conditions
        conditions_data = []

        if len(performance_data) > 0:
            # Calculate mean intensity across both conditions
            performance_data_copy = performance_data.copy()
            performance_data_copy["mean_intensity"] = performance_data_copy[
                ["Intensity_mean_A", "Intensity_mean_B"]
            ].mean(axis=1, skipna=True)

            if performance_data_copy["mean_intensity"].max() > 0:
                performance_data_copy["normalized_intensity"] = (
                    performance_data_copy["mean_intensity"] / performance_data_copy["mean_intensity"].max() * 100
                )
                performance_data_copy = performance_data_copy.sort_values(by="normalized_intensity", ascending=False)
                # Rank within species: only one species is shown at a time, so the count axis
                # must run from 1 to the number of precursors of that species instead of
                # carrying the ranks of the pooled set.
                performance_data_copy["rank"] = performance_data_copy.groupby("species").cumcount() + 1

                conditions_data.append(performance_data_copy[["rank", "normalized_intensity", "epsilon", "species"]])

        if conditions_data:
            plot_df = conditions_data[0]

            # Get colors from species_expected_ratio if available
            if species_expected_ratio:
                color_map = {species: data.get("color", "#000000") for species, data in species_expected_ratio.items()}
            else:
                # Fallback colors if not provided
                color_map = {}

            # Create figure with dropdown for species selection
            fig = go.Figure()

            # Only keep the species that are actually present, plasma background first so that
            # HUMAN is the default selection.
            species_present = set(plot_df["species"].dropna())
            species_order = [s for s in PYE_SPECIES_ORDER if s in species_present]
            species_order += [s for s in sorted(species_present) if s not in PYE_SPECIES_ORDER]

            # Track which trace indices belong to which species, so the dropdown stays correct
            # even when a species is absent from the data.
            species_trace_indices = {}

            for idx, species in enumerate(species_order):
                species_df = plot_df[plot_df["species"] == species].copy()
                if len(species_df) == 0:
                    continue

                species_trace_indices[species] = [len(fig.data), len(fig.data) + 1]

                # Add scatter trace for this species
                fig.add_trace(
                    go.Scattergl(
                        x=species_df["rank"],
                        y=species_df["normalized_intensity"],
                        mode="markers",
                        marker=dict(
                            color=color_map.get(species, "#000000"),
                            size=6,
                            opacity=0.3,
                            line=dict(width=0.5, color="white"),
                        ),
                        name=f"{species} precursors",
                        visible=(idx == 0),  # Only first (HUMAN) visible by default
                        hovertemplate=(
                            f"<b>{species}</b><br>{species} rank: %{{x}}<br>Intensity: %{{y:.2f}}%<extra></extra>"
                        ),
                    )
                )

                # Calculate epsilon trend for this species
                eps_df = species_df[["rank", "epsilon"]].copy()
                eps_df["absolute_eps"] = eps_df["epsilon"].abs()
                eps_df = eps_df.sort_values("rank")

                # window ~1% of points, minimum 5
                window = max(5, len(eps_df) // 10 if len(eps_df) >= 100 else 5)
                eps_df["epsilon_trend"] = (
                    eps_df["absolute_eps"].rolling(window=window, center=True, min_periods=1).median()
                )

                # Add epsilon trend line for this species
                fig.add_trace(
                    go.Scatter(
                        x=eps_df["rank"],
                        y=eps_df["epsilon_trend"],
                        mode="lines",
                        name=f"{species} epsilon trend",
                        yaxis="y2",
                        line=dict(dash="dash", color=color_map.get(species, "#000000"), width=2),
                        visible=(idx == 0),  # Only first (HUMAN) visible by default
                        hovertemplate=(
                            f"<b>{species} epsilon trend</b><br>{species} rank: %{{x}}<br>"
                            "Epsilon: %{y:.3f}<extra></extra>"
                        ),
                    )
                )

            # Create dropdown buttons for species selection
            buttons = []
            nr_traces = len(fig.data)
            for species, trace_indices in species_trace_indices.items():
                visibility = [False] * nr_traces
                for trace_index in trace_indices:
                    visibility[trace_index] = True

                buttons.append(
                    dict(
                        label=species,
                        method="update",
                        args=[{"visible": visibility}],
                    )
                )

            fig.update_xaxes(
                title="Intensity rank within species (1 = highest intensity of the selected species)",
                gridcolor="lightgray",
                showgrid=True,
            )
            fig.update_yaxes(
                title="Normalized Intensity (%)",
                type="log",
                dtick="1",
                gridcolor="lightgray",
                showgrid=True,
            )

            # Update layout with dropdown menu. The secondary axis shows the absolute epsilon,
            # so its range is derived from the absolute values.
            epsilon_q85 = plot_df["epsilon"].abs().quantile(0.85)
            if pd.isna(epsilon_q85) or epsilon_q85 <= 0:
                epsilon_q85 = 1.0

            fig.update_layout(
                updatemenus=[
                    dict(
                        buttons=buttons,
                        direction="down",
                        pad={"r": 10, "t": 10},
                        showactive=True,
                        x=0.15,
                        xanchor="left",
                        y=1.15,
                        yanchor="top",
                    )
                ],
                annotations=[
                    dict(
                        text="Species:",
                        showarrow=False,
                        x=0.02,
                        xref="paper",
                        y=1.13,
                        yref="paper",
                        align="left",
                    )
                ],
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1.0,
                ),
                yaxis2=dict(
                    title="Absolute epsilon (rolling median)",
                    overlaying="y",
                    side="right",
                    range=[0, epsilon_q85],
                ),
                margin=dict(l=60, r=80, t=80, b=60),  # Reduce top margin to fill space
                hovermode="closest",
            )

        else:
            # No data available
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for dynamic range plot",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )

        return fig

    def _plot_missing_values(self, performance_data: pd.DataFrame, max_observations=12) -> go.Figure:
        """
        Generate missing values plot with smoothed trend line and color gradient.

        This plot shows how missingness increases with lower abundance precursors.
        High-abundance precursors (low rank) typically have low missingness,
        while low-abundance precursors (high rank) have higher missingness.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Performance data containing missing values information
        max_observations : int
            Maximum number of observations possible (default 12)

        Returns
        -------
        go.Figure
            Plotly figure with missing values plot, trend line, and reference lines
        """
        fig = go.Figure()

        # Filter and prepare data
        human_slice = performance_data[performance_data["species"] == "HUMAN"].copy()

        if len(human_slice) == 0:
            fig.add_annotation(
                text="No human plasma data available for missing values plot",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        # Compute logIntensityMean locally to avoid hidden dependency on _plot_ma_plot
        human_slice["logIntensityMean"] = (
            human_slice["log_Intensity_mean_A"] + human_slice["log_Intensity_mean_B"]
        ) / 2

        human_slice = human_slice.sort_values(by="logIntensityMean", ascending=False)  # Across conditions
        human_slice["rank"] = range(1, len(human_slice) + 1)
        human_slice["missingness"] = (1 - human_slice["nr_observed"] / max_observations) * 100

        # Calculate smoothed trend line (rolling median)
        window = max(5, len(human_slice) // 20)  # ~5% of points, minimum 5
        human_slice["missingness_trend"] = (
            human_slice["missingness"].rolling(window=window, center=True, min_periods=1).median()
        )

        # Create scatter plot with color gradient based on missingness
        fig.add_trace(
            go.Scatter(
                x=human_slice["rank"],
                y=human_slice["missingness"],
                mode="markers",
                marker=dict(
                    size=4,
                    color=human_slice["missingness"],
                    colorscale="Reds",
                    showscale=True,
                    colorbar=dict(title="Missing<br>Values (%)", thickness=15, len=0.7),
                    cmin=0,
                    cmax=100,
                    opacity=0.6,
                ),
                name="Precursors",
                hovertemplate="Rank: %{x}<br>Missing: %{y:.1f}%<extra></extra>",
            )
        )

        # Add smoothed trend line
        fig.add_trace(
            go.Scatter(
                x=human_slice["rank"],
                y=human_slice["missingness_trend"],
                mode="lines",
                line=dict(color="darkred", width=3),
                name="Trend (rolling median)",
                hovertemplate="Rank: %{x}<br>Trend: %{y:.1f}%<extra></extra>",
            )
        )

        # Update layout
        fig.update_layout(
            xaxis=dict(
                title="Intensity Rank (1 = highest intensity)",
                gridcolor="lightgray",
                showgrid=True,
            ),
            yaxis=dict(
                title="Missing Values (%)",
                gridcolor="lightgray",
                showgrid=True,
                range=[-5, 105],  # Give some padding
            ),
            hovermode="closest",
            showlegend=True,
            legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)"),
            margin=dict(l=60, r=20, t=20, b=60),  # Reduce margins to fill space
        )

        return fig

    def _plot_signed_epsilon(
        self, performance_data: pd.DataFrame, species_expected_ratio: Dict[str, Dict[str, Union[float, str]]]
    ) -> go.Figure:
        """
        Generate a signed epsilon plot showing over- and underestimation of the log2 fold change.

        For each species the distribution of the signed epsilon (measured minus expected log2
        fold change) is shown as a horizontal violin with an embedded box plot. Values below
        zero mean that the log2 fold change is underestimated, values above zero that it is
        overestimated. The fraction of precursors on either side of zero is annotated per
        species so that a systematic bias is directly visible.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Intermediate data containing the ``epsilon`` and ``species`` columns.
        species_expected_ratio : Dict[str, Dict[str, Union[float, str]]]
            Expected ratios for each species and their colors.

        Returns
        -------
        go.Figure
            Plotly figure with the signed epsilon distributions per species.
        """
        fig = go.Figure()

        if "epsilon" not in performance_data.columns or "species" not in performance_data.columns:
            fig.add_annotation(
                text="No epsilon data available for the signed epsilon plot",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        color_map = {species: data.get("color", "#000000") for species, data in (species_expected_ratio or {}).items()}

        # Keep the plasma background first, then the spike-ins, and append any other species.
        species_present = [s for s in PYE_SPECIES_ORDER if s in set(performance_data["species"].dropna())]
        species_present += [s for s in sorted(set(performance_data["species"].dropna())) if s not in PYE_SPECIES_ORDER]

        annotations = []
        plotted_any = False

        for species in species_present:
            epsilon = performance_data.loc[performance_data["species"] == species, "epsilon"]
            epsilon = epsilon.replace([np.inf, -np.inf], np.nan).dropna()
            if len(epsilon) == 0:
                continue

            plotted_any = True
            color = color_map.get(species, "#000000")

            fig.add_trace(
                go.Violin(
                    x=epsilon,
                    y=[species] * len(epsilon),
                    orientation="h",
                    name=species,
                    box_visible=True,
                    meanline_visible=True,
                    points=False,
                    spanmode="hard",
                    line_color=color,
                    fillcolor=color,
                    opacity=0.5,
                    hovertemplate=(f"<b>{species}</b><br>Signed epsilon: %{{x:.3f}}<extra></extra>"),
                )
            )

            # Annotate the direction of the bias: fraction of precursors above / below zero
            # and the median signed epsilon.
            fraction_over = (epsilon > 0).mean() * 100
            fraction_under = (epsilon < 0).mean() * 100
            annotations.append(
                dict(
                    xref="paper",
                    yref="y",
                    x=1.0,
                    xanchor="right",
                    y=species,
                    yanchor="bottom",
                    text=(
                        f"median {epsilon.median():+.3f} | " f"{fraction_under:.0f}% under / {fraction_over:.0f}% over"
                    ),
                    showarrow=False,
                    font=dict(size=10, color="gray"),
                )
            )

        if not plotted_any:
            fig.add_annotation(
                text="No epsilon data available for the signed epsilon plot",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        # Symmetric x-range based on the bulk of the data, so single outliers do not
        # compress the informative part of the distributions.
        epsilon_all = performance_data["epsilon"].replace([np.inf, -np.inf], np.nan).dropna()
        limit = np.nanmax(np.abs(epsilon_all.quantile([0.01, 0.99]).values)) if len(epsilon_all) > 0 else 1.0
        if not np.isfinite(limit) or limit <= 0:
            limit = 1.0
        limit *= 1.1

        fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=1)

        fig.update_layout(
            xaxis=dict(
                title="Signed epsilon (measured - expected log2 fold change)",
                range=[-limit, limit],
                gridcolor="lightgray",
                showgrid=True,
                zeroline=False,
            ),
            yaxis=dict(title="Species", gridcolor="lightgray", showgrid=False),
            annotations=annotations,
            showlegend=False,
            hovermode="closest",
            margin=dict(l=80, r=20, t=40, b=60),
        )

        # Label the two halves of the plot so the direction of the bias is unambiguous.
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.02,
            y=1.06,
            text="← underestimated log2 fold change",
            showarrow=False,
            font=dict(size=11, color="gray"),
        )
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.98,
            y=1.06,
            text="overestimated log2 fold change →",
            showarrow=False,
            font=dict(size=11, color="gray"),
        )

        return fig

    def plot_main_metric(
        self,
        result_df: pd.DataFrame,
        metric: str = "Median",
        mode: str = "Species-weighted",
        software_colors: Dict[str, str] = {
            "MaxQuant": "#88ccef",
            "AlphaPept": "#cc6777",
            "ProlineStudio": "#ddcc77",
            "MSAngel": "#147733",
            "FragPipe": "#342288",
            "i2MassChroQ": "#aa4599",
            "Sage": "#671100",
            "WOMBAT": "#44aa9a",
            "DIA-NN": "#999934",
            "AlphaDIA": "#1D2732",
            "Custom": "#000000",
            "Spectronaut": "#007548",
            "FragPipe (DIA-NN quant)": "#F89008",
            "MSAID": "#bfef45",
            "MetaMorpheus": "#637C7A",
            "Proteome Discoverer": "#911eb4",
            "PEAKS": "#f032e6",
            "quantms": "#f5e830",
        },
        software_markers: Dict[str, str] = {
            "MaxQuant": "circle",
            "AlphaPept": "square",
            "ProlineStudio": "diamond",
            "MSAngel": "cross",
            "FragPipe": "x",
            "i2MassChroQ": "triangle-up",
            "Sage": "triangle-down",
            "WOMBAT": "pentagon",
            "DIA-NN": "star",
            "AlphaDIA": "star-triangle-up",
            "Custom": "star-square",
            "Spectronaut": "diamond-tall",
            "FragPipe (DIA-NN quant)": "circle-x",
            "MSAID": "square-cross",
            "MetaMorpheus": "asterisk",
            "Proteome Discoverer": "hash",
            "PEAKS": "diamond-wide",
            "quantms": "hexagram",
        },
        mapping: Dict[str, str] = {"old": 10, "new": 20},
        highlight_color: str = "#d30067",
        label: str = "",
        legend_name_map: Dict[str, str] = {"AlphaPept": "AlphaPept (legacy tool)"},
        hide_annot: bool = False,
        colorblind_mode: bool = False,
        default_cutoff_min_feature: int = 3,
        min_nr_observed: int = None,
        annotation: str = "",
        **kwargs,
    ) -> go.Figure:
        """
        Generate the main plasma benchmarking scatterplot.

        This method returns the plasma performance scatterplot for comparing multiple methods.

        Parameters
        ----------
        result_df : pd.DataFrame
            DataFrame containing the results to plot, must have 'results' column with metrics.
        metric : str, optional
            Metric to use for calculations: "Median" or "Mean". Defaults to "Median".
        mode : str, optional
            Mode for metric calculation: "Global" or "Species-weighted". Currently both modes
            use the same metrics for plasma. Defaults to "Species-weighted".
        software_colors : Dict[str, str]
            Mapping of software names to colors.
        mapping : Dict[str, str]
            Mapping for marker sizes.
        highlight_color : str
            Color to use for highlighting specific software.
        label : str
            Label for plot annotations.
        legend_name_map : Dict[str, str]
            Mapping for legend names.
        hide_annot : bool
            Whether to hide annotations on the plot.
        default_cutoff_min_feature : int
            Default min precursor threshold for extracting metrics.
        min_nr_observed : int, optional
            Override the cutoff level with this value if provided.
        annotation : str, optional
            Text annotation to display on the plot (e.g., "-Alpha-", "-Beta-").
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        go.Figure
            Plotly figure with the plasma scatterplot.
        """
        # Use min_nr_observed if provided, otherwise use default_cutoff_min_feature
        cutoff_level = min_nr_observed if min_nr_observed is not None else default_cutoff_min_feature
        return self._plot_plasma_scatterplot(
            result_df,
            metric=metric,
            mode=mode,
            software_colors=software_colors,
            software_markers=software_markers,
            mapping=mapping,
            highlight_color=highlight_color,
            label=label,
            legend_name_map=legend_name_map,
            hide_annot=hide_annot,
            colorblind_mode=colorblind_mode,
            default_cutoff_min_feature=cutoff_level,
            annotation=annotation,
            **kwargs,
        )

    def _plot_plasma_scatterplot(
        self,
        result_df: pd.DataFrame,
        metric: str = "Median",
        mode: str = "Species-weighted",
        # TODO: move software_colors to constants
        software_colors: Dict[str, str] = {
            "MaxQuant": "#88ccef",
            "AlphaPept": "#cc6777",
            "ProlineStudio": "#ddcc77",
            "MSAngel": "#147733",
            "FragPipe": "#342288",
            "i2MassChroQ": "#aa4599",
            "Sage": "#671100",
            "WOMBAT": "#44aa9a",
            "DIA-NN": "#999934",
            "AlphaDIA": "#1D2732",
            "Custom": "#000000",
            "Spectronaut": "#007548",
            "FragPipe (DIA-NN quant)": "#F89008",
            "MSAID": "#bfef45",
            "MetaMorpheus": "#637C7A",
            "Proteome Discoverer": "#911eb4",
            "PEAKS": "#f032e6",
            "quantms": "#f5e830",
        },
        software_markers: Dict[str, str] = {
            "MaxQuant": "circle",
            "AlphaPept": "square",
            "ProlineStudio": "diamond",
            "MSAngel": "cross",
            "FragPipe": "x",
            "i2MassChroQ": "triangle-up",
            "Sage": "triangle-down",
            "WOMBAT": "pentagon",
            "DIA-NN": "star",
            "AlphaDIA": "star-triangle-up",
            "Custom": "star-square",
            "Spectronaut": "diamond-tall",
            "FragPipe (DIA-NN quant)": "circle-x",
            "MSAID": "square-cross",
            "MetaMorpheus": "asterisk",
            "Proteome Discoverer": "hash",
            "PEAKS": "diamond-wide",
            "quantms": "hexagram",
        },
        mapping: Dict[str, str] = {"old": 10, "new": 20},
        highlight_color: str = "#d30067",
        label: str = "",
        legend_name_map: Dict[str, str] = {"AlphaPept": "AlphaPept (legacy tool)"},
        hide_annot: bool = False,
        colorblind_mode: bool = False,
        default_cutoff_min_feature: int = 3,
        annotation: str = "",
        **kwargs,
    ) -> go.Figure:
        """
        Generate the main plasma benchmarking scatterplot.

        The plot uses four visual dimensions to represent the benchmarking results:
        - X-axis: Absolute log2 fold-change error for yeast and E. coli spike-ins (median or mean based on metric)
        - Y-axis: Number of quantified yeast and E. coli spike-in precursors
        - Dot size: Dynamic range of human plasma precursors (quantification breadth)
        - Dot opacity: Quantification accuracy for human plasma (median or mean absolute epsilon)

        Both dot size and dot opacity are min-max normalised over the datapoints that are
        currently loaded, so that the available visual range is used in full and small
        differences between workflows remain distinguishable. The hover text reports the raw
        values, together with the number of quantified precursors per species.

        Parameters
        ----------
        result_df : pd.DataFrame
            DataFrame containing the results to plot.
        metric : str, optional
            Metric to use: "Median" or "Mean". Defaults to "Median".
        mode : str, optional
            Mode for metric calculation: "Global" or "Species-weighted". Currently both modes
            use the same metrics for plasma. Defaults to "Species-weighted".
        software_colors : Dict[str, str]
            Mapping of software names to colors.
        mapping : Dict[str, str]
            Mapping for marker sizes.
        highlight_color : str
            Color to use for highlighting specific software.
        label : str
            Label for plot annotations.
        legend_name_map : Dict[str, str]
            Mapping for legend names.
        hide_annot : bool
            Whether to hide annotations on the plot.
        default_cutoff_min_feature : int
            Default min precursor threshold for extracting metrics.
        annotation : str, optional
            Text annotation to display on the plot (e.g., "-Alpha-", "-Beta-").
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        go.Figure
            Plotly figure with the plasma scatterplot.
        """
        fig = go.Figure()

        # Determine which metric keys to use based on selected metric and mode
        metric_lower = metric.lower()
        mode_suffix = "global" if mode == "Global" else "eq_species"

        # Construct metric keys with mode suffix
        x_metric_key = f"{metric_lower}_abs_log2_fc_error_spike_ins_{mode_suffix}"
        # Fallback to legacy key (without suffix) for backwards compatibility with old datapoints
        x_metric_key_legacy = f"{metric_lower}_abs_log2_fc_error_spike_ins"

        # Human plasma metrics don't have mode variants (single species)
        opacity_metric_key = f"{metric_lower}_abs_epsilon_human_plasma"

        # Pre-pass: collect raw dynamic-range and human-plasma accuracy values for
        # data-driven normalization of marker size and marker opacity. This ensures the
        # full visual range is used regardless of where the values cluster, maximising
        # visual separation for small differences.
        raw_size_vals = []
        raw_opacity_vals = []
        for _, row in result_df.iterrows():
            m = self._get_metrics_at_cutoff(row.get("results"), default_cutoff_min_feature)
            if m is not None:
                sv = m.get("dynamic_range_human_plasma_mean", 0.0)
                if sv > 0:
                    raw_size_vals.append(sv)
                ov = m.get(opacity_metric_key)
                if ov is not None and not pd.isna(ov):
                    raw_opacity_vals.append(ov)
        size_min = min(raw_size_vals) if raw_size_vals else 0.0
        size_max = max(raw_size_vals) if raw_size_vals else 1.0
        size_data_range = size_max - size_min if size_max > size_min else 1.0

        # Opacity is min-max normalised over the loaded datapoints and inverted (lowest
        # human-plasma error = fully opaque), so that the contrast between workflows is as
        # pronounced as the data allows instead of being compressed by a fixed slope.
        opacity_min_val = min(raw_opacity_vals) if raw_opacity_vals else 0.0
        opacity_max_val = max(raw_opacity_vals) if raw_opacity_vals else 1.0
        opacity_data_range = opacity_max_val - opacity_min_val

        # Create scatter plot with all four visual dimensions
        # Group by software to create separate traces (allows colorblind markers)
        software_data = {}
        for idx, row in result_df.iterrows():
            metrics = self._get_metrics_at_cutoff(row.get("results"), default_cutoff_min_feature)
            if metrics is None:
                continue

            software = row["software_name"]
            if software not in software_data:
                software_data[software] = {
                    "x": [],
                    "y": [],
                    "sizes": [],
                    "opacities": [],
                    "colors": [],
                    "markers": [],
                    "hover_texts": [],
                }

            # Try new mode-specific key first, fall back to legacy key
            x_val = metrics.get(x_metric_key)
            if x_val is None:
                x_val = metrics.get(x_metric_key_legacy, 0.0)

            y_val = metrics.get("nr_quantified_spike_ins", 0)
            size_val = metrics.get("dynamic_range_human_plasma_mean", 0.0)
            opacity_val = metrics.get(opacity_metric_key)

            software_data[software]["x"].append(x_val)
            software_data[software]["y"].append(y_val)

            # Size scaling: min-max normalise across the loaded data so the full
            # [8, 40] range is always used, making even small differences visible.
            if size_val > 0:
                normalized_size = 8 + ((size_val - size_min) / size_data_range) * 10
            else:
                normalized_size = 8
            software_data[software]["sizes"].append(normalized_size)

            # Opacity: lower error = higher opacity (higher alpha). Min-max normalised over
            # the loaded datapoints so the full [OPACITY_MIN, OPACITY_MAX] range is used.
            if opacity_val is None or pd.isna(opacity_val) or opacity_data_range <= 0:
                opacity = OPACITY_MAX
            else:
                relative_error = (opacity_val - opacity_min_val) / opacity_data_range
                opacity = OPACITY_MAX - relative_error * (OPACITY_MAX - OPACITY_MIN)
            software_data[software]["opacities"].append(opacity)

            # Get software color
            color = software_colors.get(software, "#000000")
            if "Highlight" in result_df.columns and result_df.loc[idx, "Highlight"]:
                color = highlight_color
            software_data[software]["colors"].append(color)

            # Get marker
            marker = software_markers.get(software, "circle")
            software_data[software]["markers"].append(marker)

            # Build hover text, including the per-species identification counts so that
            # plasma-background and spike-in depth can be inspected separately.
            mode_label = "global" if mode == "Global" else "species-weighted"
            opacity_text = "not available" if opacity_val is None or pd.isna(opacity_val) else f"{opacity_val:.3f}"
            species_count_lines = ""
            for species in PYE_SPECIES_ORDER:
                species_count = metrics.get(f"nr_quantified_{species}")
                if species_count is not None:
                    species_count_lines += f"&nbsp;&nbsp;{species}: {species_count}<br>"
            if species_count_lines:
                species_count_lines = "Quantified precursors per species:<br>" + species_count_lines

            hover_text = (
                f"<b>{software} {row['software_version']}</b><br>"
                f"Spike-in error ({metric_lower}, {mode_label}): {x_val:.3f}<br>"
                f"Quantified spike-ins: {y_val}<br>"
                f"{species_count_lines}"
                f"Plasma dynamic range (log10 P90-P10, mean of A and B): {size_val:.2f}<br>"
                f"Plasma accuracy error ({metric_lower}): {opacity_text}<br>"
                f"ProteoBench ID: {row['id']}"
            )
            software_data[software]["hover_texts"].append(hover_text)

        # Add traces for each software
        for software, data in software_data.items():
            # Get unique marker for this software
            marker_symbol = data["markers"][0] if colorblind_mode else "circle"

            fig.add_trace(
                go.Scatter(
                    x=data["x"],
                    y=data["y"],
                    mode="markers",
                    marker=dict(
                        size=data["sizes"],
                        color=data["colors"],
                        opacity=data["opacities"],
                        symbol=marker_symbol,
                        line=dict(width=1, color="white"),
                    ),
                    text=data["hover_texts"],
                    hovertemplate="%{text}<extra></extra>",
                    name=legend_name_map.get(software, software),
                )
            )

        # Update layout
        mode_description = "global" if mode == "Global" else "species-weighted"
        fig.update_layout(
            width=800,
            height=700,
            xaxis=dict(
                title=f"{metric} absolute log2 fold-change error (spike-ins, {mode_description})",
                gridcolor="lightgray",
                gridwidth=1,
                linecolor="black",
                showgrid=True,
            ),
            yaxis=dict(
                title=self.y_axis_title,
                gridcolor="lightgray",
                gridwidth=1,
                linecolor="black",
                showgrid=True,
            ),
        )

        # Add annotation explaining the visual dimensions. The annotation carries a tooltip
        # with the full definition of the dynamic range metric (hover the text to read it).
        annotation_text = (
            "Dot size = dynamic range of quantified human precursors in plasma "
            "(hover for definition) | Opacity = plasma quantification accuracy (darker = better)"
        )
        fig.add_annotation(
            text=annotation_text if not hide_annot else "",
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.15,
            showarrow=False,
            font=dict(size=10, color="gray"),
            hovertext=self._wrap_tooltip_text(DYNAMIC_RANGE_EXPLANATION),
            hoverlabel=dict(bgcolor="white", bordercolor="gray", font=dict(size=11, color="black")),
        )

        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text=annotation if not hide_annot else "",
            font=dict(size=50, color="rgba(0,0,0,0.1)"),
            showarrow=False,
        )

        fig.update_layout(clickmode="event+select")

        return fig

    @staticmethod
    def _wrap_tooltip_text(text: str, width: int = 70) -> str:
        """
        Wrap a long text into HTML line breaks for use in a plotly tooltip.

        Parameters
        ----------
        text : str
            The text to wrap.
        width : int, optional
            Maximum number of characters per line. Defaults to 70.

        Returns
        -------
        str
            The text with ``<br>`` inserted at the line breaks.
        """
        return "<br>".join(textwrap.wrap(text, width=width))

    @staticmethod
    def _get_metrics_at_cutoff(results: dict, cutoff: int) -> dict | None:
        """Get metrics for a given cutoff level from results with int or string keys."""
        if not isinstance(results, dict):
            return None

        if cutoff in results and isinstance(results[cutoff], dict):
            return results[cutoff]

        cutoff_str = str(cutoff)
        if cutoff_str in results and isinstance(results[cutoff_str], dict):
            return results[cutoff_str]

        return None

    def _get_metric_column_name(self, metric: str, mode: str) -> Tuple[str, str, str]:
        """
        Get the appropriate metric column names based on the specified metric and mode.

        Note: For plasma (PYE) modules, this is primarily for compatibility with the UI
        which offers metric and mode selectors. The plasma plot uses different metrics
        (spike-in errors, quantification depth, dynamic range) rather than the
        epsilon-based metrics used in HYE modules.

        Parameters
        ----------
        metric : str
            The metric to plot: "Median" or "Mean".
        mode : str
            The mode for filtering: "Global" or "Species-weighted".

        Returns
        -------
        Tuple[str, str, str]
            A tuple containing (metric_lower, mode_suffix, plot_title).
        """
        metric_lower = metric.lower()
        mode_suffix = "global" if mode == "Global" else "eq_species"
        mode_description = "globally" if mode == "Global" else "using equally weighted species averages"

        plot_title = (
            f"{metric} absolute difference between measured and expected log2-transformed fold change "
            f"(calculated {mode_description})"
        )

        return metric_lower, mode_suffix, plot_title

    def _filter_datapoints_with_metric(self, benchmark_metrics_df: pd.DataFrame, metric_col_name: str) -> pd.DataFrame:
        """
        Filter datapoints to only include those that have the specified metric calculated.

        For plasma modules, this ensures consistency with HYE module behavior when
        filtering for species-weighted metrics.

        Parameters
        ----------
        benchmark_metrics_df : pd.DataFrame
            DataFrame containing benchmark metrics for datapoints.
        metric_col_name : str
            The name of the metric column to filter on.

        Returns
        -------
        pd.DataFrame
            Filtered DataFrame containing only datapoints with the specified metric.
        """

        def has_metric(results_dict):
            """Check if the results dictionary contains the specified metric."""
            try:
                for threshold_dict in results_dict.values():
                    if metric_col_name in threshold_dict:
                        return True
            except (TypeError, AttributeError):
                pass
            return False

        # Filter to only datapoints that have the specified metric calculated
        return benchmark_metrics_df[benchmark_metrics_df["results"].apply(has_metric)].copy()
