import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go

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





    
    
def plot_metric(result_df):  # x: [], y: [], color: [], cv: []
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
    
    """"

    # read data from input_dict (not ready)
    #df = pd.DataFrame(input_dict)
    
    
    # add hover text. 
    hover_text = [] 
    
    # add all info
    for index, row in result_df.iterrows():
        hover_text.append(f"workflow identifier: {row["workflow identifier"]} software_name: {row["software_name"]}")
        

    df["text"] = hover_text
    
        
    fig = go.Figure(data=[go.Scatter(
        x=result_df["x"], 
        y=result_df["y"],
        mode="markers",
        text = result_df["text"]
        marker=dict(color=result_df["software_name"], 
                   size=result_df["cv"]))])
    
    
    return fig 
    
    
    
    
    
    
    
    
    
    