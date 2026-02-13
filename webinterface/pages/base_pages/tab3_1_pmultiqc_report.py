import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st


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


def create_pmultiqc_report_section(variables_quant) -> str:
    """
    Create a section in the Streamlit app to display the pMultiQC report.
    """
    html_content = ""
    if st.button("Create pMultiQC Report"):
        df_intermediate_results = st.session_state[variables_quant.result_perf]
        with TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            tmp_data = (tmp_dir / "data").resolve()
            tmp_data.mkdir(parents=True, exist_ok=True)
            df_intermediate_results.to_csv(tmp_data / "result_performance.csv", index=False)
            file_out = tmp_dir
            ret_code = subprocess.run(
                [
                    "multiqc",
                    "--parse_proteobench",
                    f"{tmp_data}",
                    "-o",
                    f"{file_out}",
                    "-f",
                    "--clean-up",
                ],
                check=False,
            )
            html_path = Path(file_out) / "multiqc_report.html"
            if html_path.exists() and ret_code.returncode == 0:
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                st.success("pMultiQC report generated successfully.")
            else:
                st.error("Error generating pMultiQC report. Please check the logs.")
    return html_content
