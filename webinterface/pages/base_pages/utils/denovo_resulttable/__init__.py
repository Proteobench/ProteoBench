"""
Result table for the de novo module.

The quant modules render their datapoints as one flat ag-grid row each (see ``resulttable.py``,
which is shared by every quant tab and is deliberately left alone). That works when a tool appears
once. A de novo tool can be submitted many times, one datapoint per decoding strategy or
checkpoint, and then a flat table repeats the tool name down the page while the differences sit in
scattered parameter columns, most of which are identical across the very rows being compared.

This table is still one flat table, but it earns its shape differently: rows are ordered tool by
tool and best first within each tool, a ``Show`` checkbox decides what the figures draw, and only
the columns that actually differ within some tool are shown by default.

Why not grouped, collapsible rows, which is what the information really wants: AG Grid's row
grouping and master/detail are Enterprise features, and ProteoBench is Apache-2.0 and enables
neither. An earlier version of this module faked grouping with one ``st.expander`` per tool, each
holding its own small editor. That gave the machinery of grouping without its benefit, cost a
widget per tool, and collapsed itself on every rerun because the expander labels carried live
counts. One sortable table is the honest option in this stack.

Selection lives in the ``Show`` column rather than in a widget's own selection state, because
``st.dataframe``'s row selection cannot be set programmatically and the presets have to be able to
write a selection.

Nothing here is imported by the quant tabs; the de novo page calls it instead of
``tab1.render_results_table``.
"""

from pages.base_pages.utils.denovo_resulttable.controls import (  # noqa: F401
    COLUMN_PRESETS,
    table_height,
)
from pages.base_pages.utils.denovo_resulttable.frame import (  # noqa: F401
    METRIC_COLUMNS,
    build_table_frame,
    header_for,
    metric_value,
    row_order,
)
from pages.base_pages.utils.denovo_resulttable.selection import (  # noqa: F401
    selection_summary,
    sync_selection_from_editor,
)
from pages.base_pages.utils.denovo_resulttable.table import render_denovo_result_table  # noqa: F401
