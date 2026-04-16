import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

import pages.texts.proteobench_builder as pbb
import streamlit as st


class BaseUIModule(ABC):
    """Base class for all UI modules with common patterns."""

    def __init__(self, variables, ionmodule, parsesettingsbuilder, page_name: str = "/") -> None:
        self.variables = variables
        self.ionmodule = ionmodule
        self.parsesettingsbuilder = parsesettingsbuilder
        self.user_input: Dict[str, Any] = {}
        self.page_name = page_name
        self.submission_ready = False
        self.params_file_dict_copy: Dict[str, Any] = {}

        pbb.proteobench_page_config()

        pbb.proteobench_sidebar(current_page=self.page_name)

        if self.variables.params_file_dict not in st.session_state.keys():
            st.session_state[self.variables.params_file_dict] = {}

    def render_plot_options_expander(
        self,
        filter_callbacks: List[Callable[[], Any]],
        selector_callbacks: List[Callable[[], Any]],
        filter_cols_spec: Union[int, List[int]] = 2,
        selector_cols_spec: Union[int, List[int]] = None,
    ) -> List[Any]:
        """
        Render a standardized plot options expander with customizable content.

        This method creates a consistent layout for plot options across different modules,
        reducing code duplication while maintaining flexibility.

        Parameters
        ----------
        filter_callbacks : List[Callable[[], Any]]
            List of functions to call for each filter column. Each function should render
            its UI elements and optionally return a value.
        selector_callbacks : List[Callable[[], Any]]
            List of functions to call for each selector column. Each function should render
            its UI elements and optionally return a value.
        filter_cols_spec : Union[int, List[int]], optional
            Number of columns or list of column weights for filter row. Default is 2.
        selector_cols_spec : Union[int, List[int]], optional
            Number of columns or list of column weights for selector row.
            If None, uses [1] * len(selector_callbacks).

        Returns
        -------
        List[Any]
            List of return values from all callbacks (filter + selector callbacks).

        Examples
        --------
        >>> def render_slider():
        ...     return st.slider("Value", 0, 100)
        >>> def render_selectbox():
        ...     return st.selectbox("Option", ["A", "B"])
        >>> results = self.render_plot_options_expander(
        ...     filter_callbacks=[render_slider, render_selectbox],
        ...     selector_callbacks=[],
        ...     filter_cols_spec=2
        ... )
        """
        if selector_cols_spec is None:
            selector_cols_spec = [1] * len(selector_callbacks)

        results = []

        with st.expander("Plot options", expanded=True):
            # Render filter row if there are filter callbacks
            if filter_callbacks:
                filter_cols = st.columns(filter_cols_spec)
                for idx, callback in enumerate(filter_callbacks):
                    with filter_cols[idx]:
                        result = callback()
                        results.append(result)

            # Render selector row if there are selector callbacks
            if selector_callbacks:
                selector_cols = st.columns(selector_cols_spec)
                for idx, callback in enumerate(selector_callbacks):
                    with selector_cols[idx]:
                        result = callback()
                        results.append(result)

        return results

    @abstractmethod
    def display_all_data_results_main(self) -> None:
        """Tab 1 - Display results for all data (overview)."""
        pass

    @abstractmethod
    def display_submission_form(self) -> None:
        """Tab 2 - Create the main submission form for the Streamlit UI"""
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
