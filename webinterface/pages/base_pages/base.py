from abc import ABC, abstractmethod
import streamlit as st
from typing import Any, Dict

import json
import pages.texts.proteobench_builder as pbb
import streamlit as st

class BaseUIModule(ABC):
    """Base class for all UI modules with common patterns."""

    def __init__(
            self,
            variables,
            ionmodule,
            parsesettingsbuilder,
            page_name: str = "/"
    ) -> None:
        self.variables = variables
        self.ionmodule = ionmodule
        self.parsesettingsbuilder = parsesettingsbuilder
        self.user_input: Dict[str, Any] = {}
        self.page_name = page_name
        self.submission_ready = False
        self.params_file_dict_copy: Dict[str, Any] = {}

        pbb.proteobench_page_config()

        st.markdown(
            """
            <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        pbb.proteobench_sidebar(current_page=self.page_name)

        if self.variables.params_file_dict not in st.session_state.keys():
            st.session_state[self.variables.params_file_dict] = {}
        

    @abstractmethod
    def display_all_data_results_main(self) -> None:
        """Tab 1 - Display results for all data (overview)."""
        pass

    @abstractmethod
    def display_submission_form(self) -> None:
        """Tab 2 - Create the main submission form for the Streamlit UI
        """
        pass

    @abstractmethod
    def display_indepth_plots(self) -> None:
        """Tab 3 - Display the dataset eselection dropdown and plot selected datasets."""
        pass

    @abstractmethod
    def display_all_data_results_submitted(self) -> None:
        """Tab 4 - Display the results for all data (overview) + submission"""
        pass

    @abstractmethod
    def display_public_submission_ui(self) -> None:
        """Tab 5 - Display the public submission section of the page"""
        pass