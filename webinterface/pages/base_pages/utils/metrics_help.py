"""
Shared "How are the metrics calculated?" popover.

The explanation itself is provided by the module's plot generator via
``get_metrics_help_markdown()``, so it lives next to the code that produces the main plot and is
automatically shared by all modules that use the same plot generator.
"""

from typing import Optional

import streamlit as st


def get_metrics_help_markdown(ionmodule, variables) -> Optional[str]:
    """
    Fetch the metrics explanation of a module from its plot generator.

    Parameters
    ----------
    ionmodule : object
        The instantiated benchmark module.
    variables : object
        The module's Variables dataclass instance, used to pass the module-specific y-axis title
        to the plot generator.

    Returns
    -------
    str or None
        The Markdown explanation, or None when the module does not provide one or the plot
        generator cannot be built.
    """
    try:
        plot_generator = ionmodule.get_plot_generator(y_axis_title=getattr(variables, "y_axis_title", None))
        return plot_generator.get_metrics_help_markdown()
    except Exception:  # noqa: BLE001 - an explanatory popover must never break the page
        return None


def render_metrics_help(ionmodule, variables) -> None:
    """
    Render the "How are the metrics calculated?" popover for a module.

    Nothing is rendered when the module's plot generator does not provide an explanation.

    Parameters
    ----------
    ionmodule : object
        The instantiated benchmark module.
    variables : object
        The module's Variables dataclass instance.
    """
    help_markdown = get_metrics_help_markdown(ionmodule, variables)
    if not help_markdown:
        return

    # st.markdown dedents and strips the body, so the indented triple-quoted strings that the
    # plot generators return can be passed through unchanged.
    with st.popover("How are the metrics calculated?", icon="ℹ️", use_container_width=True):
        st.markdown(help_markdown)
