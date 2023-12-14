import numpy as np
import plotly.express as px
import plotly.graph_objects as go


class ECDF:
    """
    Return the Empirical CDF of an array as a step function.

    Parameters
    ----------
    x : array_like
        Observations
    """

    def __init__(self, x):
        # Get ECDF
        x = np.array(x, copy=True)
        x.sort()
        nobs = len(x)
        y = np.linspace(1.0 / nobs, 1, nobs)

        # Make into step function
        _x = np.asarray(x)
        _y = np.asarray(y)

        if _x.shape != _y.shape:
            msg = "x and y do not have the same shape"
            raise ValueError(msg)
        if len(_x.shape) != 1:
            msg = "x and y must be 1-dimensional"
            raise ValueError(msg)

        self.x = np.r_[-np.inf, _x]
        self.y = np.r_[0.0, _y]
        self.n = self.x.shape[0]

    def __call__(self, time):
        tind = np.searchsorted(self.x, time, side="right") - 1
        return self.y[tind]


def score_histogram(psm_df):
    psm_df = psm_df.copy()
    psm_df["is_decoy"] = psm_df["is_decoy"].map({True: "decoy", False: "target"})
    fig = px.histogram(
        psm_df,
        x="score",
        color="is_decoy",
        barmode="overlay",
        histnorm="",
        labels={"is_decoy": "PSM type", "False": "target", "True": "decoy"},
        opacity=0.75,
    )
    return fig


def pp_plot(psm_df):
    """Generate PP plot for given PSM dataframe."""
    n_decoys = np.count_nonzero(psm_df["is_decoy"])
    n_targets = len(psm_df) - n_decoys
    pi_zero = n_decoys / n_targets
    if n_decoys == 0:
        raise ValueError("No decoy PSMs found in PSM file.")
    target_scores = psm_df["score"][~psm_df["is_decoy"]]
    decoy_scores = psm_df["score"][psm_df["is_decoy"]]
    if len(psm_df) > 1000:
        target_scores_quantiles = psm_df["score"][~psm_df["is_decoy"]].quantile(np.linspace(0, 1, 1000))
    else:
        target_scores_quantiles = target_scores
    target_ecdf = ECDF(target_scores)(target_scores_quantiles)
    decoy_ecdf = ECDF(decoy_scores)(target_scores_quantiles)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=decoy_ecdf,
            y=target_ecdf,
            mode="markers",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, pi_zero],
            mode="lines",
            line=go.scatter.Line(color="red"),
            showlegend=True,
            name="pi0",
        )
    )
    fig.update_layout(
        xaxis_title="Fdp",
        yaxis_title="Ftp",
        showlegend=False,
    )
    return fig


def fdr_plot(psm_df, fdr_threshold):
    """Plot number of identifications in function of FDR threshold."""
    df = psm_df[~psm_df["is_decoy"]].reset_index(drop=True).sort_values("qvalue", ascending=True).copy()
    df["count"] = (~df["is_decoy"]).cumsum()
    fig = px.line(
        df,
        x="qvalue",
        y="count",
        log_x=True,
        labels={"count": "Number of identified target PSMs", "qvalue": "FDR threshold"},
    )
    fig.add_vline(x=fdr_threshold, line=go.layout.shape.Line(color="red"))
    return fig
