from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from proteobench.plotting.plot_generator_base import PlotGeneratorBase
from proteobench.score.entrapmentscores import EntrapmentScores


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

        # Generate QQ plot — use pre-computed curve if provided, otherwise derive it
        # from the intermediate DataFrame (e.g. for public datasets loaded from storage).
        plots["qq"] = self._plot_qq_plot(
            performance_data, fdp_curve=kwargs.get("fdp_curve"), mapping_file=kwargs.get("mapping_file")
        )

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
                    "qq": "Estimated FDP vs Q-value Threshold",
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
            "qq": (
                "Estimated false discovery proportion (FDP) bounds as a function of Q-value threshold. "
                "The grey dashed diagonal marks estimated FDP = FDR (perfect calibration). "
                "Points below the diagonal indicate conservative FDR control; "
                "points above indicate that the estimated FDP exceeds the declared threshold. "
                "The shaded band spans the estimated FDP uncertainty interval (lower bound to combined "
                "upper bound). "
                "The right axis shows the number of identified features at each threshold."
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
        return r"""
            Each point is one benchmark run. Entrapment sequences from organisms that are absent
            from the sample are added to the search database, so every entrapment identification is
            a false positive by construction. Their frequency is used to estimate the false
            discovery proportion (FDP) that the workflow actually reached, which can then be
            compared to the FDR threshold the workflow declared.

            **X-axis** - the estimated FDP bound, calculated at the selected Q-value threshold.
            Workflows further to the left estimated their FDR more accurately.

            **Y-axis** - the number of identified features at that same threshold, which reflects
            the sensitivity of the workflow.

            The two axes represent a trade-off: a workflow can identify more features by accepting a
            higher true error rate, so a point should never be judged on one axis alone.

            **Select metric to show in x axis** - which bound of the estimated FDP interval is shown:

            - **Estimated lower FDP bound** - the fraction of identified entrapment peptides among
              all identifications, `N_E / (N_T + N_E)`. It is a lower bound because entrapment
              identifications that displaced their paired target are not counted.
            - **Estimated upper FDP bound - Paired method** - additionally counts entrapment
              peptides that have no identified paired target, and counts pairs in which the
              entrapment outscores the target twice.

            Here `N_E` is the number of identified entrapment peptides and `N_T` the number of
            identified target peptides. The full formulas are given in the "Quick Intro" panel of
            this module.

            **Q-value threshold** - the confidence threshold at which both axes are evaluated. The
            stored FDP curve is re-read at the selected value, so moving it changes both the
            estimated FDP and the number of identified features. "Maximum reported" uses the highest
            threshold that the workflow reported.

            **Point colour** - the software tool.

            **Marker shape** - the verdict obtained by comparing the estimated FDP interval to the
            FDR threshold that the workflow declared:

            - circle, **valid** - both estimated bounds are below the declared threshold, so FDR
              control holds (and is conservative).
            - triangle, **inconclusive** - the estimated interval contains the declared threshold,
              so the data neither confirm nor reject the FDR calculation.
            - cross, **invalid** - both estimated bounds exceed the declared threshold, so the
              reported FDR is underestimated.

            Runs without a declared FDR threshold are evaluated against a fallback of 0.01 so that
            they are still displayed.

            **Colorblind Mode** - reassigns the marker shape to the software tool, so the verdict is
            then no longer encoded in the shape.
            """

    def _plot_qq_plot(
        self, performance_data: pd.DataFrame, fdp_curve: dict = None, mapping_file: str = None
    ) -> go.Figure:
        """
        Plot estimated FDP bounds (lower bound, combined, paired) against Q-value threshold.

        Each estimated FDP bound is shown as a line. The grey dashed diagonal marks
        perfect calibration (estimated FDP = declared FDR). The shaded band spans the
        uncertainty interval between the estimated lower and combined upper FDP bounds.
        A secondary right-hand axis shows the number of identified features at
        each threshold.

        Parameters
        ----------
        performance_data : pd.DataFrame
            Intermediate DataFrame produced by ``EntrapmentScores.generate_intermediate``.
            Must contain at least ``Q-Value``, ``Peptide``, and
            ``Target or Entrapment`` columns.
        fdp_curve : dict, optional
            Pre-computed FDP curve from ``EntrapmentScores.calculate_fdp_at_fdr_thresholds``.
            When provided the intermediate DataFrame is not re-processed. Pass this
            from the already-computed datapoint to avoid redundant computation.
        mapping_file : str, optional
            Path or URL to the entrapment peptide mapping file. Required when
            ``fdp_curve`` is not provided.

        Returns
        -------
        go.Figure
            Plotly figure with the estimated FDP calibration curve.
        """
        if fdp_curve is None:
            try:
                entrapment_scores = EntrapmentScores(mapping_file=mapping_file)
                performance_data = entrapment_scores.validate_entrapment_coverage(performance_data)
                fdp_curve = entrapment_scores.calculate_fdp_at_fdr_thresholds(performance_data)
            except Exception as exc:
                fig = go.Figure()
                fig.update_layout(
                    xaxis_title="Q-value threshold",
                    yaxis_title="Estimated FDP",
                    template="plotly_white",
                    height=500,
                    annotations=[
                        dict(
                            text=f"Could not compute FDP curve: {exc}",
                            x=0.5,
                            y=0.5,
                            xref="paper",
                            yref="paper",
                            showarrow=False,
                        )
                    ],
                )
                return fig

        if not fdp_curve:
            fig = go.Figure()
            fig.update_layout(
                template="plotly_white",
                height=500,
                annotations=[
                    dict(
                        text="No FDP curve data — intermediate DataFrame may be empty.",
                        x=0.5,
                        y=0.5,
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                    )
                ],
            )
            return fig

        fdp_curve = {float(k): v for k, v in fdp_curve.items()}
        thresholds = sorted(fdp_curve.keys())
        lower = [fdp_curve[t]["lower_bound_FDP"] for t in thresholds]
        combined = [fdp_curve[t]["combined_FDP"] for t in thresholds]
        paired = [fdp_curve[t]["paired_FDP"] for t in thresholds]
        nr_features = [fdp_curve[t]["nr_id_features"] for t in thresholds]

        hover_lower = [
            f"Q-value ≤ {t:.5f}<br>Estimated lower bound FDP: {l:.4f}<br>Nr features: {n}"
            for t, l, n in zip(thresholds, lower, nr_features)
        ]
        hover_combined = [
            f"Q-value ≤ {t:.5f}<br>Estimated combined FDP: {c:.4f}<br>Nr features: {n}"
            for t, c, n in zip(thresholds, combined, nr_features)
        ]
        hover_paired = [
            f"Q-value ≤ {t:.5f}<br>Estimated paired FDP: {p:.4f}<br>Nr features: {n}"
            for t, p, n in zip(thresholds, paired, nr_features)
        ]
        hover_nr = [f"Q-value ≤ {t:.5f}<br>Nr features: {n}" for t, n in zip(thresholds, nr_features)]

        fig = go.Figure()

        # Shaded uncertainty band: lower bound → combined upper bound
        fig.add_trace(
            go.Scatter(
                x=thresholds + thresholds[::-1],
                y=combined + lower[::-1],
                fill="toself",
                fillcolor="rgba(120,120,120,0.12)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Estimated FDP uncertainty band",
                hoverinfo="skip",
                showlegend=True,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=thresholds,
                y=lower,
                mode="lines+markers",
                name="Estimated lower bound FDP",
                line=dict(color="#2ecc71", width=2),
                marker=dict(size=7),
                hovertext=hover_lower,
                hoverinfo="text",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=thresholds,
                y=combined,
                mode="lines+markers",
                name="Estimated combined FDP (upper)",
                line=dict(color="#e74c3c", width=2),
                marker=dict(size=7),
                hovertext=hover_combined,
                hoverinfo="text",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=thresholds,
                y=paired,
                mode="lines+markers",
                name="Estimated paired FDP (upper)",
                line=dict(color="#f39c12", width=2, dash="dot"),
                marker=dict(size=7, symbol="diamond"),
                hovertext=hover_paired,
                hoverinfo="text",
            )
        )

        # Identity reference: FDP = declared FDR
        x_max = max(thresholds)
        fig.add_trace(
            go.Scatter(
                x=[0, x_max],
                y=[0, x_max],
                mode="lines",
                name="Estimated FDP bound = FDR (identity)",
                line=dict(color="gray", width=1.5, dash="dash"),
                hoverinfo="skip",
            )
        )

        # Nr. identified features on secondary right axis
        fig.add_trace(
            go.Scatter(
                x=thresholds,
                y=nr_features,
                mode="lines",
                name="Nr. identified features",
                line=dict(color="rgba(60,60,180,0.45)", width=1.5, dash="longdash"),
                yaxis="y2",
                hovertext=hover_nr,
                hoverinfo="text",
            )
        )

        fig.update_layout(
            xaxis=dict(
                title="Q-value threshold (declared FDR)",
                gridcolor="lightgray",
                linecolor="black",
            ),
            yaxis=dict(
                title="Estimated False Discovery Proportion (FDP)",
                gridcolor="lightgray",
                linecolor="black",
                rangemode="tozero",
            ),
            yaxis2=dict(
                title="Nr. identified features",
                overlaying="y",
                side="right",
                showgrid=False,
                linecolor="rgba(60,60,180,0.45)",
                rangemode="tozero",
            ),
            template="plotly_white",
            height=520,
            margin=dict(l=80, r=110, t=60, b=100),
            legend=dict(orientation="h", y=-0.28),
        )

        return fig

    def plot_forest(
        self,
        result_df: pd.DataFrame,
        sort_ascending: bool = True,
        threshold: float = None,
        **kwargs,
    ) -> go.Figure:
        """
        Plot a forest / interval plot of estimated FDP bounds per submitted workflow.

        Each row represents one submission. A thick horizontal bar spans from the
        estimated lower FDP bound to the estimated paired upper FDP bound; open circle markers at
        both endpoints make the interval limits explicit. A diamond marker shows
        the declared FDR threshold (``reported_fdr_parsed_from_input``). Bar colour indicates the
        validity category (valid / inconclusive / invalid) computed against each
        workflow's own ``reported_fdr_parsed_from_input``. Rows are sorted by the number of
        identified features.

        Parameters
        ----------
        result_df : pd.DataFrame
            DataFrame containing all datapoints (one row per workflow).
            Must include ``lower_bound_FDP``, ``paired_FDP``, ``reported_fdr_parsed_from_input``,
            ``nr_id_features``, ``software_name``, ``software_version``.
        sort_ascending : bool, optional
            Sort rows by ``nr_id_features`` ascending (True) or descending (False).
        threshold : float, optional
            When set, FDP values and ``nr_id_features`` are taken from the
            ``fdp_curve`` entry at this exact threshold (with 1% relative wiggle
            room). Rows without an entry for the threshold are dropped.
        **kwargs : dict
            Ignored; accepted for call-site compatibility.

        Returns
        -------
        go.Figure
            Plotly figure with the forest plot.
        """
        plot_df = result_df.copy()

        if threshold is not None and "fdp_curve" in plot_df.columns:
            entries = plot_df["fdp_curve"].apply(lambda c: self._get_fdp_entry_at_threshold(c, threshold))
            plot_df["lower_bound_FDP"] = entries.apply(
                lambda e: float(e["lower_bound_FDP"]) if isinstance(e, dict) and "lower_bound_FDP" in e else np.nan
            )
            plot_df["paired_FDP"] = entries.apply(
                lambda e: float(e["paired_FDP"]) if isinstance(e, dict) and "paired_FDP" in e else np.nan
            )
            plot_df["nr_id_features"] = entries.apply(
                lambda e: float(e["nr_id_features"]) if isinstance(e, dict) and "nr_id_features" in e else np.nan
            )
            plot_df["category_paired"] = entries.apply(
                lambda e: e.get("category_paired", "inconclusive") if isinstance(e, dict) and e else "inconclusive"
            )
            # drop rows that have no entry for this threshold
            plot_df = plot_df[entries.apply(bool)].reset_index(drop=True)

        for col in ("lower_bound_FDP", "paired_FDP", "reported_fdr_parsed_from_input"):
            if col in plot_df.columns:
                plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")
            else:
                plot_df[col] = np.nan
        if "nr_id_features" in plot_df.columns:
            plot_df["nr_id_features"] = pd.to_numeric(plot_df["nr_id_features"], errors="coerce")
        else:
            plot_df["nr_id_features"] = np.nan

        def _categorise_row(row):
            lower = row.get("lower_bound_FDP", np.nan)
            upper = row.get("paired_FDP", np.nan)
            fdr = row.get("reported_fdr_parsed_from_input", np.nan)
            if pd.isna(fdr) or fdr == 0:
                fdr = 0.01
            if pd.isna(lower) or pd.isna(upper):
                return "inconclusive"
            if upper <= fdr:
                return "valid"
            elif lower > fdr:
                return "invalid"
            return "inconclusive"

        if threshold is not None and "category_paired" in plot_df.columns:
            plot_df["category"] = plot_df["category_paired"]
        else:
            plot_df["category"] = plot_df.apply(_categorise_row, axis=1)

        plot_df = plot_df.sort_values("nr_id_features", ascending=sort_ascending, na_position="last").reset_index(
            drop=True
        )

        plot_df["y_label"] = plot_df["id"].astype(str)

        n = len(plot_df)
        y_pos = list(range(n))
        plot_df["y_pos"] = y_pos

        category_colors = {"valid": "#2ecc71", "inconclusive": "#f39c12", "invalid": "#e74c3c"}
        cap_half = 0.32

        hover_texts = []
        for _, row in plot_df.iterrows():
            lo = row.get("lower_bound_FDP", np.nan)
            hi = row.get("paired_FDP", np.nan)
            fdr = row.get("reported_fdr_parsed_from_input", np.nan)
            nr = row.get("nr_id_features", np.nan)
            lo_str = f"{lo:.4f}" if pd.notna(lo) else "N/A"
            hi_str = f"{hi:.4f}" if pd.notna(hi) else "N/A"
            fdr_str = f"{fdr}" if pd.notna(fdr) and fdr != 0 else "not set (0.01 used)"
            nr_str = f"{int(nr)}" if pd.notna(nr) else "N/A"
            hover_texts.append(
                f"<b>{row.get('id', '')}</b><br>"
                f"Software: {row.get('software_name', '')} {row.get('software_version', '')}<br>"
                f"Identified features: {nr_str}<br>"
                f"Estimated lower FDP bound: {lo_str}<br>"
                f"Estimated upper FDP bound (paired): {hi_str}<br>"
                f"Reported FDR (from input): {fdr_str}<br>"
                f"Category: {row.get('category', '')}"
            )
        plot_df["hover_text"] = hover_texts

        if "old_new" in plot_df.columns:
            is_new = (plot_df["old_new"] == "new").tolist()
        else:
            is_new = [False] * n

        fig = go.Figure()

        # Thick horizontal bars + end caps + endpoint markers, grouped by category
        for category in ("valid", "inconclusive", "invalid"):
            cat_df = plot_df[plot_df["category"] == category]
            if cat_df.empty:
                continue
            color = category_colors[category]
            bar_x, bar_y = [], []
            cap_x, cap_y = [], []
            ep_x, ep_y, ep_hover = [], [], []

            for _, row in cat_df.iterrows():
                lo = row["lower_bound_FDP"]
                hi = row["paired_FDP"]
                y = row["y_pos"]
                hover = row["hover_text"]
                if pd.notna(lo) and pd.notna(hi):
                    bar_x += [lo, hi, None]
                    bar_y += [y, y, None]
                    for xv in (lo, hi):
                        cap_x += [xv, xv, None]
                        cap_y += [y - cap_half, y + cap_half, None]
                    ep_x += [lo, hi]
                    ep_y += [y, y]
                    ep_hover += [hover, hover]

            if bar_x:
                fig.add_trace(
                    go.Scatter(
                        x=bar_x,
                        y=bar_y,
                        mode="lines",
                        name=category.capitalize(),
                        line=dict(color=color, width=10),
                        hoverinfo="skip",
                        legendgroup=category,
                    )
                )
            if cap_x:
                fig.add_trace(
                    go.Scatter(
                        x=cap_x,
                        y=cap_y,
                        mode="lines",
                        showlegend=False,
                        line=dict(color=color, width=3),
                        hoverinfo="skip",
                        legendgroup=category,
                    )
                )
            if ep_x:
                fig.add_trace(
                    go.Scatter(
                        x=ep_x,
                        y=ep_y,
                        mode="markers",
                        showlegend=False,
                        marker=dict(
                            symbol="circle",
                            color="white",
                            size=10,
                            line=dict(color=color, width=2.5),
                        ),
                        hovertext=ep_hover,
                        hoverinfo="text",
                        legendgroup=category,
                    )
                )

        # Diamond / star markers at declared FDR — only shown in "Maximum reported" mode
        if threshold is None:
            fdr_x = [
                (
                    r["reported_fdr_parsed_from_input"]
                    if pd.notna(r["reported_fdr_parsed_from_input"]) and r["reported_fdr_parsed_from_input"] > 0
                    else 0.01
                )
                for _, r in plot_df.iterrows()
            ]
            fdr_missing = [
                pd.isna(r["reported_fdr_parsed_from_input"]) or r["reported_fdr_parsed_from_input"] == 0
                for _, r in plot_df.iterrows()
            ]
            fdr_colors = ["rgba(100,100,100,0.6)" if m else "rgba(20,20,20,0.9)" for m in fdr_missing]
            new_border_widths = [2.5 if n_ else 1.5 for n_ in is_new]
            new_sizes = [14 if n_ else 11 for n_ in is_new]

            fig.add_trace(
                go.Scatter(
                    x=fdr_x,
                    y=y_pos,
                    mode="markers",
                    name="Declared FDR threshold",
                    marker=dict(
                        symbol=["star" if n_ else "diamond" for n_ in is_new],
                        color=fdr_colors,
                        size=new_sizes,
                        line=dict(width=new_border_widths, color="black"),
                    ),
                    hoverinfo="skip",
                )
            )

        # Secondary-axis bars: nr_id_features on right side
        nr_vals = plot_df["nr_id_features"].tolist()
        nr_colors = [category_colors.get(c, "#cccccc") for c in plot_df["category"].tolist()]
        fig.add_trace(
            go.Bar(
                x=nr_vals,
                y=y_pos,
                orientation="h",
                name="Nr. identified features",
                marker=dict(color=nr_colors, opacity=0.35),
                xaxis="x2",
                hovertemplate="%{x:,} features<extra></extra>",
                showlegend=False,
            )
        )

        row_height = 30
        fig_height = max(400, n * row_height + 140)

        fig.update_layout(
            xaxis=dict(
                title="Estimated FDP — lower bound to upper bound (paired method)",
                gridcolor="lightgray",
                linecolor="black",
                range=[-0.002, None],
                domain=[0, 0.55],
            ),
            xaxis2=dict(
                title="Nr. identified features",
                side="top",
                overlaying=None,
                domain=[0.60, 1.0],
                gridcolor="lightgray",
                linecolor="black",
                tickformat=",d",
            ),
            yaxis=dict(
                tickmode="array",
                tickvals=y_pos,
                ticktext=plot_df["y_label"].tolist(),
                gridcolor="lightgray",
                linecolor="black",
            ),
            template="plotly_white",
            height=fig_height,
            margin=dict(l=180, r=20, t=80, b=80),
        )

        if threshold is not None:
            fig.add_vline(
                x=threshold,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Q ≤ {threshold}",
                annotation_position="top right",
            )

        return fig

    @staticmethod
    def _truncate_comment(comment: str, max_length: int = 100) -> str:
        """Truncate a free-text comment for display in hover text, appending '...' only if cut."""
        comment = comment.strip()
        if len(comment) <= max_length:
            return comment
        return comment[:max_length].rstrip() + "..."

    @staticmethod
    def _get_fdp_entry_at_threshold(fdp_curve, threshold: float) -> dict:
        """Return the fdp_curve entry for the given threshold, within 1% relative tolerance."""
        if not isinstance(fdp_curve, dict) or not fdp_curve:
            return {}
        float_keys = {float(k): v for k, v in fdp_curve.items()}
        tol = threshold * 0.01
        candidates = {k: v for k, v in float_keys.items() if abs(k - threshold) <= tol}
        if not candidates:
            return {}
        # prefer the key closest to the requested threshold
        best = min(candidates, key=lambda k: abs(k - threshold))
        return candidates[best]

    def _resolve_metric_column(self, metric: str) -> Tuple[str, str]:
        """
        Resolve the metric column name and plot title based on the selected metric.

        Parameters
        ----------
        metric : str
            The selected metric to plot.

        Returns
        -------
        Tuple[str, str]
            A tuple containing the resolved metric column name and the corresponding plot title.
        """
        if metric == "Estimated lower FDP bound":
            return "lower_bound_FDP", "Estimated lower FDP bound"
        elif metric == "Estimated upper FDP bound - Combined method":
            return "combined_FDP", "Estimated upper FDP bound - Combined method"
        elif metric == "Estimated upper FDP bound - Paired method":
            return "paired_FDP", "Estimated upper FDP bound - Paired method"
        else:
            raise ValueError(f"Unsupported metric '{metric}' selected for plotting.")

    def plot_main_metric(
        self,
        result_df: pd.DataFrame,
        hide_annot: bool = False,
        metric: str = "Estimated upper FDP bound - Paired method",
        colorblind_mode: bool = False,
        threshold: float = None,
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
            Estimated bound to plot on the x axis, one of "Estimated lower FDP bound",
            "Estimated upper FDP bound - Combined method", or "Estimated upper FDP bound - Paired method".
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

        if threshold is not None and "fdp_curve" in plot_df.columns:
            entries = plot_df["fdp_curve"].apply(lambda c: self._get_fdp_entry_at_threshold(c, threshold))
            plot_df[metric_col_name] = entries.apply(
                lambda e: float(e[metric_col_name]) if isinstance(e, dict) and metric_col_name in e else np.nan
            )
            plot_df["nr_id_features"] = entries.apply(
                lambda e: float(e["nr_id_features"]) if isinstance(e, dict) and "nr_id_features" in e else np.nan
            )
            plot_df["category_paired"] = entries.apply(
                lambda e: e.get("category_paired", "inconclusive") if isinstance(e, dict) and e else "inconclusive"
            )
            # drop rows that have no entry for this exact threshold
            plot_df = plot_df[entries.apply(bool)].reset_index(drop=True)

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
                    hover_text += f"<br>Comment (private submission): {self._truncate_comment(comment)}"
            if "submission_comments" in plot_df.columns:
                comment = row.get("submission_comments", "")
                if isinstance(comment, str) and comment.strip():
                    hover_text += f"<br>Comment (public submission): {self._truncate_comment(comment)}"
            hover_texts.append(hover_text)

        plot_df["hover_text"] = hover_texts

        category_symbols = {"valid": "circle", "inconclusive": "triangle-up", "invalid": "x"}

        colors = [software_colors.get(software, "#000000") for software in plot_df["software_name"]]
        if colorblind_mode:
            markers = [software_markers.get(software, "circle") for software in plot_df["software_name"]]
        elif "category_paired" in plot_df.columns:
            markers = [category_symbols.get(str(c), "circle") for c in plot_df["category_paired"]]
        else:
            markers = ["circle"] * len(plot_df)

        if "Highlight" in plot_df.columns:
            colors = [highlight_color if highlight else color for color, highlight in zip(colors, plot_df["Highlight"])]

        plot_df["color"] = colors
        plot_df["marker"] = markers

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
                    legendgroup="software",
                    legendgrouptitle=dict(text="Software"),
                    marker=dict(
                        color=software_df["color"].tolist(),
                        symbol=software_df["marker"].tolist(),
                        size=software_df["scatter_size"].tolist(),
                        line=dict(width=0.5, color="rgba(0,0,0,0.25)"),
                    ),
                )
            )

        if not colorblind_mode and "category_paired" in plot_df.columns:
            for category, symbol in category_symbols.items():
                fig.add_trace(
                    go.Scatter(
                        x=[None],
                        y=[None],
                        mode="markers",
                        name=category.capitalize(),
                        legendgroup="category",
                        legendgrouptitle=dict(text="Category (paired)"),
                        marker=dict(color="rgba(80,80,80,0.8)", symbol=symbol, size=10),
                        showlegend=True,
                    )
                )

        fig.update_layout(
            width=None,
            height=700,
            autosize=True,
            xaxis=dict(
                title=plot_title if threshold is None else f"{plot_title} (Q ≤ {threshold})",
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

        if threshold is not None:
            fig.add_vline(
                x=threshold,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Estimated FDP bound = declared FDR ({threshold})",
                annotation_position="top right",
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
