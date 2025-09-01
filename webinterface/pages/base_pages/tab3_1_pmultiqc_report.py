import streamlit as st


@st.fragment()
def show_download_button(html_content: str) -> None:
    """
    Display a download button for the pMultiQC report.
    """
    st.markdown("Download the pMultiQC report generated from the intermediate data.")
    # components.html(html_content, height=800, scrolling=True)
    st.download_button(
        label="Download pMultiQC Report",
        file_name="pMultiQC_report.html",
        data=html_content,
    )
