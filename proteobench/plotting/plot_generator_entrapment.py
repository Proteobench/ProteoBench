from typing import Any, Dict, Tuple

import pandas as pd
import plotly.graph_objects as go

from proteobench.plotting.plot_generator_base import PlotGeneratorBase


class EntrapmentPlotGenerator(PlotGeneratorBase):
    """
    Plot generator for Entrapment modules.
    """

    def generate_in_depth_plots(
        self, performance_data: pd.DataFrame, parse_settings: Any, **kwargs
    ) -> Dict[str, go.Figure]:
        """
        Generate standard Entrapment plots.

        Parameters
        ----------
        performance_data : pd.DataFrame
            The performance data to plot
        parse_settings : ParseSettings
            The parse settings for the module
        recalculate : bool
            Whether to recalculate or use cached plots
        **kwargs : dict
            Additional module-specific parameters

        Returns
        -------
        Dict[str, go.Figure]
            Dictionary mapping plot names to plotly figures
        """
        plots = {}

        # Generate QQ plot
        plots["qq"] = self._plot_qq_plot(performance_data)

        return plots

    def get_in_depth_plot_layout(self) -> list:
        """
        Define layout for Entrapment plots.

        Returns
        -------
        list
            List of in-depth plot configurations defining how plots should be displayed
        """
        return [
            {
                "plots": ["qq"],
                "columns": 1,
                "titles": {
                    "qq": "Placeholder plot",
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
            "qq": "Placeholder for a future FDP-vs-FDR plot.",
        }

    def _plot_qq_plot(self, performance_data: pd.DataFrame) -> go.Figure:
        """
        Plot a placeholder for the future FDP-vs-FDR comparison.

        Parameters
        ----------
        performance_data : pd.DataFrame
            DataFrame containing entrapment performance results. Currently unused.

        Returns
        -------
        go.Figure
            Placeholder figure.
        """
        fig = go.Figure()
        fig.update_layout(
            xaxis_title="FDP",
            yaxis_title="FDR",
            template="plotly_white",
            height=500,
            annotations=[
                dict(
                    text="FDP vs FDR plot is not implemented yet.",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                )
            ],
        )
        return fig

    @staticmethod
    def _resolve_metric_column(metric: str) -> Tuple[str, str]:
        metric_normalized = (metric or "Combined").strip().lower()
        if metric_normalized.startswith("pair"):
            return "paired_FDP", "Paired false discovery proportion"
        return "combined_FDP", "Combined false discovery proportion"

    def plot_main_metric(
        self,
        result_df: pd.DataFrame,
        metric: str = "Combined",
        colorblind_mode: bool = False,
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
        annotation: str = "",
        **kwargs,
    ) -> go.Figure:
        """
        Generate the main performance metric scatter plot for entrapment modules.

        Parameters
        ----------
        result_df : pd.DataFrame
            DataFrame containing the results to plot.
        metric : str, optional
            Metric to plot, either "Combined" or "Paired".
        colorblind_mode : Bool, optional
            If True, use different shapes for workflows.
        software_colors : Dict[str, str]
            Mapping of software names to colors.
        software_markers : Dict[str, str]
            Mapping of software names to markers.
        mapping : Dict[str, str]
            Mapping for renaming software versions.
        highlight_color : str
            Color to use for highlighting a specific software/tool.
        label : str
            Label for the highlighted software/tool.
        legend_name_map : Dict[str, str]
            Mapping for legend names.
        hide_annot : bool
            Whether to hide annotations on the plot.
        **kwargs : dict
            Additional module-specific parameters.
        Returns
        -------
        go.Figure
            Plotly figure with the main performance metric plot.
        """
        metric_col_name, plot_title = self._resolve_metric_column(metric)

        if metric_col_name not in result_df.columns:
            raise KeyError(f"Missing metric column '{metric_col_name}' in result dataframe")
        if "nr_id_features" not in result_df.columns:
            raise KeyError("Missing 'nr_id_features' in result dataframe")

        plot_df = result_df.copy()
        plot_df[metric_col_name] = pd.to_numeric(plot_df[metric_col_name], errors="coerce")
        plot_df["nr_id_features"] = pd.to_numeric(plot_df["nr_id_features"], errors="coerce")

        hover_texts = []
        for _, row in plot_df.iterrows():
            hover_text = (
                f"ProteoBench ID: {row.get('id', '')}<br>"
                f"Software tool: {row.get('software_name', '')} {row.get('software_version', '')}<br>"
                f"{plot_title}: {row.get(metric_col_name, '')}<br>"
                f"Identified features: {row.get('nr_id_features', '')}"
            )
            if "Keyword" in plot_df.columns:
                keyword = row.get("Keyword", "")
                if isinstance(keyword, str) and keyword.strip():
                    hover_text += f"<br>Keyword: {keyword}"
            if "comments" in plot_df.columns:
                comment = row.get("comments", "")
                if isinstance(comment, str) and comment.strip():
                    hover_text += f"<br>Comment (private submission): {comment}"
            if "submission_comments" in plot_df.columns:
                comment = row.get("submission_comments", "")
                if isinstance(comment, str) and comment.strip():
                    hover_text += f"<br>Comment (public submission): {comment}"
            hover_texts.append(hover_text)

        plot_df["hover_text"] = hover_texts

        colors = [software_colors.get(software, "#000000") for software in plot_df["software_name"]]
        markers = [software_markers.get(software, "circle") for software in plot_df["software_name"]]
        if "Highlight" in plot_df.columns:
            colors = [highlight_color if highlight else color for color, highlight in zip(colors, plot_df["Highlight"])]

        plot_df["color"] = colors
        plot_df["marker"] = markers if colorblind_mode else ["circle"] * len(plot_df)

        if "old_new" in plot_df.columns:
            scatter_sizes = [mapping.get(str(item), 10) for item in plot_df["old_new"]]
        else:
            scatter_sizes = [10] * len(plot_df)
        if "Highlight" in plot_df.columns:
            scatter_sizes = [
                size * 2 if highlight else size for size, highlight in zip(scatter_sizes, plot_df["Highlight"])
            ]
        plot_df["scatter_size"] = scatter_sizes

        fig = go.Figure()

        for software_name, software_df in plot_df.groupby("software_name", dropna=False):
            software_label = legend_name_map.get(software_name, software_name)
            fig.add_trace(
                go.Scatter(
                    x=software_df[metric_col_name],
                    y=software_df["nr_id_features"],
                    mode="markers" if label == "None" else "markers+text",
                    text=software_df[label].tolist() if label != "None" and label in software_df.columns else None,
                    textposition="top center" if label != "None" else None,
                    hovertext=software_df["hover_text"].tolist(),
                    hoverinfo="text",
                    name=software_label,
                    legendgroup=software_name,
                    marker=dict(
                        color=software_df["color"].tolist(),
                        symbol=software_df["marker"].tolist(),
                        size=software_df["scatter_size"].tolist(),
                        line=dict(width=0.5, color="rgba(0,0,0,0.25)"),
                    ),
                )
            )

        fig.update_layout(
            width=None,
            height=700,
            autosize=True,
            xaxis=dict(
                title=plot_title,
                gridcolor="lightgray",
                gridwidth=1,
                linecolor="black",
            ),
            yaxis=dict(
                title="Number of identified features",
                gridcolor="lightgray",
                gridwidth=1,
                linecolor="black",
            ),
            margin=dict(l=80, r=20, t=50, b=80),
            clickmode="event+select",
        )

        if annotation:
            fig.add_annotation(
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                text=annotation,
                font=dict(size=50, color="rgba(0,0,0,0.1)"),
                showarrow=False,
            )

        return fig
