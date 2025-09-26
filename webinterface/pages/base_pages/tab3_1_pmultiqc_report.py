import subprocess
from pathlib import Path

import streamlit as st


@st.fragment
def show_download_button(html_content: str, disabled: bool) -> None:
    """
    Display a download button for the pMultiQC report.
    """
    st.markdown("Download the pMultiQC report generated from the intermediate data.")
    # components.html(html_content, height=800, scrolling=True)
    st.download_button(
        label="Download pMultiQC Report",
        file_name="pMultiQC_report.html",
        data=html_content,
        disabled=disabled,
        mime="text/html",
    )


@st.fragment
def create_pmultiqc_report_section(variables_quant) -> None:
    """
    Create a section in the Streamlit app to display the pMultiQC report.
    """
    if st.button("Create pMultiQC Report"):
        tmp = st.session_state[variables_quant.result_perf]
        tmp_path = Path("tmp_pmultiqc")
        tmp_path.mkdir(parents=True, exist_ok=True)
        tmp.to_csv(tmp_path / "result_performance.csv", index=False)
        ret_code = subprocess.run(
            [
                "multiqc",
                "--parse_proteobench",
                "./tmp_pmultiqc",
                "-o",
                "./report",
                "-f",
                "--clean-up",
            ],
            check=False,
        )
        if ret_code.returncode == 0:
            st.success("pMultiQC report generated successfully.")
        else:
            st.error("Error generating pMultiQC report. Please check the logs.")
