"""
Plot generator for LFQ PYE (Plasma-Yeast-Ecoli) quantification modules.
"""

from typing import Dict, List, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.figure_factory import create_distplot

from proteobench.plotting.plot_generator_base import PlotGeneratorBase


class LFQPYEPlotGenerator(PlotGeneratorBase):
    """
    Plot generator for LFQ PYE (Plasma-Yeast-Ecoli) quantification modules.
    Used by plasma benchmarking modules that use human plasma, yeast, and E. coli species.
    """

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
                    "dynamic_range_plot": "Dynamic Range in Condition A and B.",
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
            # TODO: improve
            "dynamic_range_plot": "Dynamic range of human precursor intensities in Condition A and B",
            "missing_values_plot": "Distribution of missing values (%) of quantified human precursors",
        }

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
        Generate dynamic range plot for both conditions A and B, with a smoothed
        epsilon trend on a secondary y-axis.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Performance data containing dynamic range information

        Returns
        -------
        go.Figure
            Plotly figure with dynamic range plots for both conditions
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
                performance_data_copy["rank"] = range(1, len(performance_data_copy) + 1)

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

            species_order = ["HUMAN", "YEAST", "ECOLI"]  # Human first as default

            # Create traces for each species (all hidden initially except first)
            for idx, species in enumerate(species_order):
                species_df = plot_df[plot_df["species"] == species].copy()
                if len(species_df) > 0:
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
                            hovertemplate=f"<b>{species}</b><br>Rank: %{{x}}<br>Intensity: %{{y:.2f}}%<extra></extra>",
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
                            hovertemplate=f"<b>{species} epsilon trend</b><br>Rank: %{{x}}<br>Epsilon: %{{y:.3f}}<extra></extra>",
                        )
                    )

            # Create dropdown buttons for species selection
            buttons = []
            for idx, species in enumerate(species_order):
                # Create visibility array: each species has 2 traces (scatter + epsilon line)
                visibility = [False] * (len(species_order) * 2)
                visibility[idx * 2] = True  # Show scatter for this species
                visibility[idx * 2 + 1] = True  # Show epsilon line for this species

                buttons.append(
                    dict(
                        label=species,
                        method="update",
                        args=[{"visible": visibility}],
                    )
                )

            fig.update_xaxes(
                title="Intensity Rank (1 = highest intensity)",
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

            # Update layout with dropdown menu
            epsilon_q85 = plot_df["epsilon"].quantile(0.85)
            if pd.isna(epsilon_q85) or epsilon_q85 == 0:
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

    def plot_main_metric(
        self,
        result_df: pd.DataFrame,
        metric: str = "Median",
        mode: str = "Global",
        software_colors: Dict[str, str] = {
            "MaxQuant": "#8bc6fd",
            "AlphaPept": "#17212b",
            "ProlineStudio": "#8b26ff",
            "MSAngel": "#C0FA7D",
            "FragPipe": "#F89008",
            "i2MassChroQ": "#108E2E",
            "Sage": "#E43924",
            "WOMBAT": "#663200",
            "DIA-NN": "#d42f2f",
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
        mapping: Dict[str, str] = {"old": 10, "new": 20},
        highlight_color: str = "#d30067",
        label: str = "",
        legend_name_map: Dict[str, str] = {"AlphaPept": "AlphaPept (legacy tool)"},
        hide_annot: bool = False,
        default_cutoff_min_prec: int = 3,
        min_nr_observed: int = None,
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
            use the same metrics for plasma. Defaults to "Global".
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
        default_cutoff_min_prec : int
            Default min precursor threshold for extracting metrics.
        min_nr_observed : int, optional
            Override the cutoff level with this value if provided.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        go.Figure
            Plotly figure with the plasma scatterplot.
        """
        # Use min_nr_observed if provided, otherwise use default_cutoff_min_prec
        cutoff_level = min_nr_observed if min_nr_observed is not None else default_cutoff_min_prec
        return self._plot_plasma_scatterplot(
            result_df,
            metric=metric,
            mode=mode,
            software_colors=software_colors,
            mapping=mapping,
            highlight_color=highlight_color,
            label=label,
            legend_name_map=legend_name_map,
            hide_annot=hide_annot,
            default_cutoff_min_prec=cutoff_level,
            **kwargs,
        )

    def _plot_plasma_scatterplot(
        self,
        result_df: pd.DataFrame,
        metric: str = "Median",
        mode: str = "Global",
        # TODO: move software_colors to constants
        software_colors: Dict[str, str] = {
            "MaxQuant": "#8bc6fd",
            "AlphaPept": "#17212b",
            "ProlineStudio": "#8b26ff",
            "MSAngel": "#C0FA7D",
            "FragPipe": "#F89008",
            "i2MassChroQ": "#108E2E",
            "Sage": "#E43924",
            "WOMBAT": "#663200",
            "DIA-NN": "#d42f2f",
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
        mapping: Dict[str, str] = {"old": 10, "new": 20},
        highlight_color: str = "#d30067",
        label: str = "",
        legend_name_map: Dict[str, str] = {"AlphaPept": "AlphaPept (legacy tool)"},
        hide_annot: bool = False,
        default_cutoff_min_prec: int = 3,
        **kwargs,
    ) -> go.Figure:
        """
        Generate the main plasma benchmarking scatterplot.

        The plot uses four visual dimensions to represent the benchmarking results:
        - X-axis: Absolute log2 fold-change error for yeast and E. coli spike-ins (median or mean based on metric)
        - Y-axis: Number of quantified yeast and E. coli spike-in precursors
        - Dot size: Dynamic range of human plasma precursors (quantification breadth)
        - Dot opacity: Quantification accuracy for human plasma (alpha based on error, median or mean)

        Parameters
        ----------
        result_df : pd.DataFrame
            DataFrame containing the results to plot.
        metric : str, optional
            Metric to use: "Median" or "Mean". Defaults to "Median".
        mode : str, optional
            Mode for metric calculation: "Global" or "Species-weighted". Currently both modes
            use the same metrics for plasma. Defaults to "Global".
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
        default_cutoff_min_prec : int
            Default min precursor threshold for extracting metrics.
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

        # Extract plasma-specific metrics from results dictionary
        x_values = []  # abs_log2_fc_error_spike_ins (median or mean, global or species-weighted)
        y_values = []  # nr_quantified_spike_ins
        sizes = []  # dynamic_range_human_plasma
        opacities = []  # abs_epsilon_human_plasma (median or mean)
        colors_list = []
        hover_texts = []

        for idx, row in result_df.iterrows():
            # Get metrics from the results dictionary at default cutoff level
            results_dict = row["results"]
            if default_cutoff_min_prec in results_dict:
                metrics = results_dict[default_cutoff_min_prec]

                # Try new mode-specific key first, fall back to legacy key
                x_val = metrics.get(x_metric_key)
                if x_val is None:
                    x_val = metrics.get(x_metric_key_legacy, 0.0)

                y_val = metrics.get("nr_quantified_spike_ins", 0)
                size_val = metrics.get("dynamic_range_human_plasma_mean", 0.0)
                opacity_val = metrics.get(opacity_metric_key, 0.0)

                x_values.append(x_val)
                y_values.append(y_val)

                # Size scaling: normalize dynamic range to reasonable marker sizes (5-30)
                # Larger dynamic range = larger dots
                if size_val > 0:
                    normalized_size = 5 + (size_val / 3) * 25  # Scale to 5-30 range
                else:
                    normalized_size = 8
                sizes.append(min(normalized_size, 30))

                # Opacity: lower error = higher opacity (higher alpha)
                # Scale error to opacity: 0 error = 0.9 opacity, 1.0+ error = 0.2 opacity
                opacity = max(0.2, 0.9 - (opacity_val * 0.7))
                opacities.append(opacity)

                # Get software color
                software = row["software_name"]
                color = software_colors.get(software, "#000000")
                if "Highlight" in result_df.columns and result_df.loc[idx, "Highlight"]:
                    color = highlight_color
                colors_list.append(color)

                # Build hover text
                mode_label = "global" if mode == "Global" else "species-weighted"
                hover_text = (
                    f"<b>{software} {row['software_version']}</b><br>"
                    f"Spike-in error ({metric_lower}, {mode_label}): {x_val:.3f}<br>"
                    f"Quantified spike-ins: {y_val}<br>"
                    f"Plasma dynamic range: {size_val:.2f}<br>"
                    f"Plasma accuracy error ({metric_lower}): {opacity_val:.3f}<br>"
                    f"ID: {row['id']}"
                )
                hover_texts.append(hover_text)

        # Create scatter plot with all four visual dimensions
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="markers",
                marker=dict(
                    size=sizes,
                    color=colors_list,
                    opacity=opacities,
                    line=dict(width=1, color="white"),
                ),
                text=hover_texts,
                hovertemplate="%{text}<extra></extra>",
                name="Results",
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
                title="Number of quantified spike-in precursors",
                gridcolor="lightgray",
                gridwidth=1,
                linecolor="black",
                showgrid=True,
            ),
        )

        # Add annotation explaining visual dimensions
        # TODO: improve
        annotation_text = (
            "Dot size = dynamic range of quantified human precursors in plasma | "
            "Opacity = plasma quantification accuracy (darker = better)"
        )
        fig.add_annotation(
            text=annotation_text if not hide_annot else "",
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.15,
            showarrow=False,
            font=dict(size=10, color="gray"),
        )

        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text="-Beta-" if not hide_annot else "",
            font=dict(size=50, color="rgba(0,0,0,0.1)"),
            showarrow=False,
        )

        fig.update_layout(clickmode="event+select")

        return fig

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
