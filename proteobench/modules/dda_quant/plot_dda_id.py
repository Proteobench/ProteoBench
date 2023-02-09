import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go  
import plotly.express as px
import streamlit as st 
from streamlit_plotly_events import plotly_events

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

   
def plot_metric(meta_data): 
    """
    Plot mean metrics in a scatterplot with plotly.  
    
    x = median absolute precentage error between all meansured and expected ratio
    y = total number of precursours quantified in all raw files 
    
    Input: result_df
    
    Information in dataframe to show in hover:
    workflow identifier	software_name	software_version	match_between_runs	precursor_mass_tolerance
    fragment_mass_tolerance allowed_missed_cleavage	fixed_mods	variable_mods min_peptide_length
    max_peptide_length
  
    
    Return: Plotly figure object
    
    """
    
    # add hover text. 
    #t = f"Workflow Identifier: {meta_data.id}<br>MBR: {meta_data.MBR}<br>Precursor Mass Tolerance: {meta_data.precursor_tol} {meta_data.precursor_tol_unit}<br>Fragment Mass Tolerance: {meta_data.fragmnent_tol} {meta_data.fragment_tol_unit}"
    
    #hover_text = [t, t]   
    
    #colors = ["MaxQuant", "AlphaPept"]
    #colors = meta_data["search_engine"]
    
    x = [meta_data.weighted_sum, meta_data.weighted_sum + 15] 
    y = [meta_data.nr_prec, meta_data.nr_prec + 42] 
    
    search_engine_colors = {"MaxQuant": px.colors.qualitative.Pastel2[2], 
                            "AlphaPept": px.colors.qualitative.Dark24[22], 
                            "MSFragger": px.colors.qualitative.Pastel2[5], 
                            "WOMBAT": px.colors.qualitative.D3[5]
                           }
    
        
    #fig = go.Figure(data=[go.Scatter(
    #    x=x, 
    #    y=y,
    #    mode="markers",
    #    text = hover_text)]) #, 
    #    #marker=dict(color=meta_data.software_version))]) # , size=result_df["cv"]  
    
    
    fig = px.scatter(meta_data,
        x="weighted_sum", 
        y="nr_prec",
        color="search_engine")
        #hover_data = "hover_text") #]) #, 
    #    #marker=dict(color=meta_data.software_version))]) # , size=result_df["cv"] 
    
    selected_points = plotly_events(fig)
    
    if len(selected_points) == 0:
        st.warning('Please select a data point')
    else:
        st.write(selected_points[0])
    
    
    
    return fig 
    

