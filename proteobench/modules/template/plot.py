import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events


def plot_bench1(result_df):
    """Plot results with Plotly Express."""
    # TODO create (plotly) figure object
    fig = go.Figure()

    return fig


def plot_bench2(result_df):
    """Plot results with Plotly Express."""
    # TODO create (plotly) figure object
    fig = go.Figure()

    return fig

# ? Should we define two function to implement instead of an ABC?
# def plot_bench(result_df: pd.DataFrame) -> go.Figure:
#     raise NotImplementedError()


# def plot_metric(benchmark_metrics_df: pd.DataFrame) -> go.Figure:
#     raise NotImplementedError()
