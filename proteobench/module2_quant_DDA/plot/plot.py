import numpy as np
import plotly.figure_factory as ff

def plot_bench(result_df):
    """Plot results with Plotly Express."""

    hist_data = [
        np.array(result_df[result_df["YEAST"] == True]["1|2_ratio"]),
        np.array(result_df[result_df["HUMAN"] == True]["1|2_ratio"]),
        np.array(result_df[result_df["ECOLI"] == True]["1|2_ratio"])
    ]
    group_labels = [
        "YEAST",
        "HUMAN",
        "ECOLI",
    ]

    fig = ff.create_distplot(hist_data, group_labels,show_hist=False)

    fig.update_xaxes(range = [0,4])
    return fig
    