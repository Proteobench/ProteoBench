from abc import ABC, abstractmethod

import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events


class PlotDataPointInterface(ABC):
    @abstractmethod
    def plot_bench(self):
        """Plot the data points of the module.."""
        pass


class PlotDataPoint(PlotDataPointInterface):
    def plot_bench(self, result_df):
        """Plot results with Plotly Express."""

        hist_data = [
            np.array(result_df[result_df["YEAST"] == True]["1|2_ratio"]),
            np.array(result_df[result_df["HUMAN"] == True]["1|2_ratio"]),
            np.array(result_df[result_df["ECOLI"] == True]["1|2_ratio"]),
        ]
        group_labels = [
            "YEAST",
            "HUMAN",
            "ECOLI",
        ]

        fig = ff.create_distplot(hist_data, group_labels, show_hist=False)

        fig.update_layout(
            title="Distplot",
            xaxis=dict(
                title="1|2_ratio",
                color="white",
                gridwidth=2,
            ),
            yaxis=dict(
                title="Density",
                color="white",
                gridwidth=2,
            ),
        )

        fig.update_xaxes(range=[0, 4])

        return fig

    def plot_metric(self, meta_data):
        """
        Plot mean metrics in a scatterplot with plotly.

        x = median absolute precentage error between all meansured and expected ratio
        y = total number of precursours quantified in all raw files

        Input: meta_data

        Information in dataframe to show in hover:
        workflow identifier	software_name	software_version	match_between_runs	precursor_mass_tolerance
        fragment_mass_tolerance allowed_missed_cleavage	fixed_mods	variable_mods min_peptide_length
        max_peptide_length


        Return: Plotly figure object


        color list :
        aliceblue, antiquewhite, aqua, aquamarine, azure,
                beige, bisque, black, blanchedalmond, blue,
                blueviolet, brown, burlywood, cadetblue,
                chartreuse, chocolate, coral, cornflowerblue,
                cornsilk, crimson, cyan, darkblue, darkcyan,
                darkgoldenrod, darkgray, darkgrey, darkgreen,
                darkkhaki, darkmagenta, darkolivegreen, darkorange,
                darkorchid, darkred, darksalmon, darkseagreen,
                darkslateblue, darkslategray, darkslategrey,
                darkturquoise, darkviolet, deeppink, deepskyblue,
                dimgray, dimgrey, dodgerblue, firebrick,
                floralwhite, forestgreen, fuchsia, gainsboro,
                ghostwhite, gold, goldenrod, gray, grey, green,
                greenyellow, honeydew, hotpink, indianred, indigo,
                ivory, khaki, lavender, lavenderblush, lawngreen,
                lemonchiffon, lightblue, lightcoral, lightcyan,
                lightgoldenrodyellow, lightgray, lightgrey,
                lightgreen, lightpink, lightsalmon, lightseagreen,
                lightskyblue, lightslategray, lightslategrey,
                lightsteelblue, lightyellow, lime, limegreen,
                linen, magenta, maroon, mediumaquamarine,
                mediumblue, mediumorchid, mediumpurple,
                mediumseagreen, mediumslateblue, mediumspringgreen,
                mediumturquoise, mediumvioletred, midnightblue,
                mintcream, mistyrose, moccasin, navajowhite, navy,
                oldlace, olive, olivedrab, orange, orangered,
                orchid, palegoldenrod, palegreen, paleturquoise,
                palevioletred, papayawhip, peachpuff, peru, pink,
                plum, powderblue, purple, red, rosybrown,
                royalblue, rebeccapurple, saddlebrown, salmon,
                sandybrown, seagreen, seashell, sienna, silver,
                skyblue, slateblue, slategray, slategrey, snow,
                springgreen, steelblue, tan, teal, thistle, tomato,
                turquoise, violet, wheat, white, whitesmoke,
                yellow, yellowgreen

        """

        # add hover text.
        # t = f"Workflow Identifier: {meta_data.id}<br>MBR: {meta_data.MBR}<br>Precursor Mass Tolerance: {meta_data.precursor_tol} {meta_data.precursor_tol_unit}<br>Fragment Mass Tolerance: {meta_data.fragmnent_tol} {meta_data.fragment_tol_unit}"

        # hover_text = [t, t]

        search_engine_colors = {
            "MaxQuant": "midnightblue",
            "AlphaPept": "grey",
            "MSFragger": "orange",
            "WOMBAT": "firebrick",
        }

        colors = [search_engine_colors[engine] for engine in meta_data["search_engine"]]

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=meta_data["weighted_sum"],
                    y=meta_data["nr_prec"],
                    mode="markers",
                    # text = ,
                    marker=dict(color=colors, showscale=True, size=20),
                )
            ]
        )

        fig.update_layout(
            title="Metric",
            xaxis=dict(
                title="Weighted sum",
                gridcolor="white",
                gridwidth=2,
            ),
            yaxis=dict(
                title="Numper of precursors",
                gridcolor="white",
                gridwidth=2,
            ),
        )

        # selected_points = plotly_events(
        #    fig,
        #    select_event=True,
        #    key='Smth'
        # )

        # if len(selected_points) == 0:
        #    st.warning('Please select a data point')
        # else:
        #    st.write(selected_points)

        return fig
