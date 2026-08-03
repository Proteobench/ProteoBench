"""
Shared "How are the metrics calculated?" popover.

The explanation itself is provided by the module's plot generator, so it lives next to the code that
produces the plots and is automatically shared by all modules that use the same plot generator.

The tab that shows the in-depth plots of a single benchmark run does not display the main plot, so
it gets its own explanation. Which of the two is used is decided by the ``context`` argument.
"""

from typing import Optional

import streamlit as st

#: Context of the tab that shows the main (cross-workflow) plot.
CONTEXT_MAIN = "main"

#: Context of the tab that shows the in-depth plots of a single benchmark run.
CONTEXT_IN_DEPTH = "in_depth"

#: Name of the UIObjects method that renders the in-depth plots. The tabs are dispatched by method
#: name, so this is what identifies the in-depth tab across all module pages.
IN_DEPTH_TAB_METHOD = "display_indepth_plots"


def context_for_tab_method(method_name: Optional[str]) -> str:
    """
    Map the UIObjects method that renders a tab onto a metrics-help context.

    Parameters
    ----------
    method_name : str or None
        The name of the UIObjects method rendering the tab.

    Returns
    -------
    str
        ``CONTEXT_IN_DEPTH`` for the in-depth tab, ``CONTEXT_MAIN`` otherwise.
    """
    return CONTEXT_IN_DEPTH if method_name == IN_DEPTH_TAB_METHOD else CONTEXT_MAIN


def get_metrics_help_markdown(ionmodule, variables, context: str = CONTEXT_MAIN) -> Optional[str]:
    """
    Fetch the metrics explanation of a module from its plot generator.

    Parameters
    ----------
    ionmodule : object
        The instantiated benchmark module.
    variables : object
        The module's Variables dataclass instance, used to pass the module-specific y-axis title
        to the plot generator.
    context : str, optional
        Which explanation to fetch: ``CONTEXT_MAIN`` for the main plot (default) or
        ``CONTEXT_IN_DEPTH`` for the in-depth plots.

    Returns
    -------
    str or None
        The Markdown explanation, or None when the module does not provide one for this context or
        the plot generator cannot be built.
    """
    try:
        plot_generator = ionmodule.get_plot_generator(y_axis_title=getattr(variables, "y_axis_title", None))
        if context == CONTEXT_IN_DEPTH:
            return plot_generator.get_in_depth_metrics_help_markdown()
        return plot_generator.get_metrics_help_markdown()
    except Exception:  # noqa: BLE001 - an explanatory popover must never break the page
        return None


def render_metrics_help(ionmodule, variables, context: str = CONTEXT_MAIN) -> None:
    """
    Render the "How are the metrics calculated?" popover for a module.

    Nothing is rendered when the module's plot generator does not provide an explanation for the
    given context.

    Parameters
    ----------
    ionmodule : object
        The instantiated benchmark module.
    variables : object
        The module's Variables dataclass instance.
    context : str, optional
        Which explanation to show: ``CONTEXT_MAIN`` for the main plot (default) or
        ``CONTEXT_IN_DEPTH`` for the in-depth plots.
    """
    help_markdown = get_metrics_help_markdown(ionmodule, variables, context=context)
    if not help_markdown:
        return

    # st.markdown dedents and strips the body, so the indented triple-quoted strings that the
    # plot generators return can be passed through unchanged.
    with st.popover("How are the metrics calculated?", icon="ℹ️", use_container_width=True):
        st.markdown(help_markdown)
