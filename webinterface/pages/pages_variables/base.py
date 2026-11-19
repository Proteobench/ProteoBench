"""
Shared base for the per-module Variables dataclasses.

A module's Variables file is the single definition of a module page: its real
configuration, a ``key``, and the classes that drive the page (``ionmodule``,
``uiobjects``, optionally ``tabs`` and ``tour``). Home.py builds one ``st.Page`` per
Variables class, so no per-module page file exists. The session-state keys and
markdown paths below are derived from ``key``. This file
must not match ``*_variables.py`` (module_registry imports those) and must not
annotate ``sidebar_label`` (module_registry picks the class that does).
"""

from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Type

from pages.texts.generic_texts import WebpageTexts

# Session-state keys used by every module page. Each becomes an attribute holding
# f"{name}_{key}"; the suffix keeps keys unique per page, since session state is
# shared across all pages of one session.
SESSION_KEYS = (
    "all_datapoints",
    "all_datapoints_submission",
    "all_datapoints_submitted",
    "button_submission_uuid",
    "check_submission",
    "colorblind_mode_selector_submitted_uuid",
    "colorblind_mode_selector_uuid",
    "dataset_selector_id_uuid",
    "download_selector_id_uuid",
    "fig_metric",
    "fig_prefix",
    "input_df",
    "input_df_submission",
    "meta_data",
    "meta_data_text",
    "meta_file_uploader_uuid",
    "metric_selector_submitted_uuid",
    "params_file_dict",
    "params_json_dict",
    "placeholder_dataset_selection_container",
    "placeholder_downloads_container",
    "prefix_params",
    "result_perf",
    "result_performance_submission",
    "selectbox_id_submitted_uuid",
    "selectbox_id_uuid",
    "submit",
)

# Only for modules with a min-observations slider: the tabs probe these with hasattr().
SLIDER_SESSION_KEYS = ("slider_id_submitted_uuid", "slider_id_uuid")


@dataclass
class VariablesBase:
    """
    Shared defaults and derived session keys for a module's Variables dataclass.
    """

    has_slider: ClassVar[bool] = True
    # The page: backend module class, UIObjects class, tab list (None = DEFAULT_TABS in
    # pages/base.py) and whether the UIObjects' guided tour is offered.
    ionmodule: ClassVar[type]
    uiobjects: ClassVar[type]
    tabs: ClassVar[Optional[list]] = None
    tour: ClassVar[bool] = True

    key: str = ""
    markdown_dir: str = ""
    texts: Type[WebpageTexts] = WebpageTexts
    highlight_list_submitted: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Derive the session-state keys and markdown paths from ``key`` and ``markdown_dir``."""
        for name in SESSION_KEYS + (SLIDER_SESSION_KEYS if self.has_slider else ()):
            setattr(self, name, f"{name}_{self.key}")
        descriptions = ("input_file", "table") + (("slider",) if self.has_slider else ())
        for name in descriptions:
            setattr(self, f"description_{name}_md", f"{self.markdown_dir}/{name}_description.md")
