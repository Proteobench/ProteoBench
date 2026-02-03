import streamlit as st
from proteobench.plotting.plot_denovo import PlotDataPoint

def generate_ptm_plots(variables, df, modifications):
    st.markdown('# PTMs')
    st.markdown('### Overview PTM precision')

    fig = PlotDataPoint.plot_ptm_overview(
        self=PlotDataPoint(),
        benchmark_metrics_df=df,
        mod_labels=modifications
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=variables.fig_ptm_overview
    )

    st.markdown('### Precision per modification')
    tabs = st.tabs(modifications)
    tab_dict = {
        mod_label: tab for mod_label, tab in zip(modifications, tabs)
    }

    for mod_label, tab in tab_dict.items():
        with tab:
            st.header(mod_label)
            fig = PlotDataPoint.plot_ptm_specific(
                self=PlotDataPoint(),
                benchmark_metrics_df=df,
                mod_label=mod_label
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=variables.fig_ptm_specific + mod_label
            )


def generate_spectrum_feature_plots(variables, df, feature_names):
    st.markdown("# Spectrum features")

    exact_mode = st.toggle(
        label='Exact evaluation mode',
        value=False,
        key=variables.evaluation_mode_toggle_tab3_features
    )
    if exact_mode:
        evaluation_type = 'exact'
    else:
        evaluation_type = 'mass'

    tabs = st.tabs(feature_names)
    tab_dict = {
        feature_name: tab for feature_name, tab in zip(feature_names, tabs)
    }

    for feature_name, tab in tab_dict.items():
        with tab:
            st.header(feature_name)
            fig = PlotDataPoint.plot_spectrum_feature(
                self=PlotDataPoint(),
                benchmark_metrics_df=df,
                feature=feature_name,
                evaluation_type=evaluation_type
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=variables.fig_spectrum_feature + feature_name
            )

def generate_species_plot(variables, df):
    st.markdown("# Species")

    exact_mode = st.toggle(
        label='Exact evaluation mode',
        value=False,
        key=variables.evaluation_mode_toggle_tab3_species
    )
    if exact_mode:
        evaluation_type = 'exact'
    else:
        evaluation_type = 'mass'

    fig = PlotDataPoint.plot_species_overview(
        self=PlotDataPoint(),
        benchmark_metrics_df=df,
        evaluation_type=evaluation_type
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=variables.fig_species_overview
    )