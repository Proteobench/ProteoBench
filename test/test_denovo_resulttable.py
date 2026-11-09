"""
Tests for the de novo result table's data assembly.

Only the framework-free parts are exercised here: what the table would show, not how Streamlit
draws it. The rendering function itself is covered indirectly by the webinterface smoke tests.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("streamlit", reason="the de novo result table needs the streamlit web stack")

# The webinterface package is not installed; put it on the path the way the other web tests do.
WEB_DIR = Path(__file__).resolve().parent.parent / "webinterface"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

from pages.base_pages.utils.denovo_resulttable import (  # noqa: E402
    COLUMN_PRESETS,
    METRIC_COLUMNS,
    build_table_frame,
    custom_labels_by_index,
    header_for,
    metric_value,
    row_order,
    selection_summary,
    sync_selection_from_editor,
)

from proteobench.plotting.plot_generator_denovo import (  # noqa: E402
    build_display_labels,
    build_variant_descriptions,
    classify_datapoint_columns,
    default_hidden_columns,
    ordered_datapoint_columns,
    rank_within_tools,
)


def _datapoint(point_id, software, auc, **fields):
    leaf = {"precision": auc, "recall": auc, "coverage": auc, "auc": auc}
    row = {
        "id": point_id,
        "intermediate_hash": f"hash_{point_id}",
        "software_name": software,
        "software_version": "1.2.2",
        "results": {level: {"mass": dict(leaf), "exact": dict(leaf)} for level in ("peptide", "aa")},
    }
    row.update(fields)
    return row


DATA = pd.DataFrame(
    [
        _datapoint("i1", "InstaNovo", 0.95, decoding_strategy="knapsack beam search", n_beams="10"),
        _datapoint("i2", "InstaNovo", 0.90, decoding_strategy="beam search", n_beams="10"),
        _datapoint("i3", "InstaNovo", 0.85, decoding_strategy="greedy search", n_beams="1"),
        _datapoint("c1", "Casanovo", 0.92, decoding_strategy="beam search", n_beams="5"),
    ]
)


def _assembled(df=DATA, evaluation_type="mass"):
    ranks, best = rank_within_tools(df, evaluation_type)
    labels = build_display_labels(df, style="index", ranks=ranks)
    classes = classify_datapoint_columns(df)
    visible = [c for c in ordered_datapoint_columns(classes) if c not in default_hidden_columns(classes)]
    return ranks, best, labels, classes, visible


class TestHeaderFor:
    def test_known_columns_get_a_readable_header(self):
        assert header_for("decoding_strategy") == "Decoding"
        assert header_for("intermediate_hash") == "Hash"

    def test_unknown_columns_fall_back_to_the_raw_name(self):
        assert header_for("some_new_field") == "some_new_field"


class TestMetricValue:
    def test_mean_auc_is_the_mean_of_the_two_levels(self):
        row = DATA.loc[0]
        assert metric_value(row, "mean_auc", "mass", None) == pytest.approx(0.95)

    def test_a_level_metric_is_read_from_the_results_tree(self):
        row = DATA.loc[0]
        assert metric_value(row, ("peptide", "precision"), "mass", None) == pytest.approx(0.95)

    def test_a_missing_metric_returns_none_rather_than_raising(self):
        row = pd.Series({"software_name": "X", "results": {}})
        assert metric_value(row, ("peptide", "auc"), "mass", None) is None
        assert metric_value(row, "mean_auc", "mass", None) is None


class TestRowOrder:
    def test_rows_are_grouped_by_tool(self):
        ranks, best, _labels, _classes, _visible = _assembled()
        order = row_order(DATA, ranks, best, "mass")
        tools = [DATA.at[idx, "software_name"] for idx in order]
        # Each tool's rows sit together, which is what carries the grouping.
        assert tools == sorted(tools, key=tools.index)

    def test_the_best_tool_comes_first(self):
        ranks, best, _labels, _classes, _visible = _assembled()
        order = row_order(DATA, ranks, best, "mass")
        assert DATA.at[order[0], "software_name"] == "InstaNovo"

    def test_within_a_tool_the_best_datapoint_comes_first(self):
        ranks, best, _labels, _classes, _visible = _assembled()
        order = row_order(DATA, ranks, best, "mass")
        instanovo = [DATA.at[idx, "id"] for idx in order if DATA.at[idx, "software_name"] == "InstaNovo"]
        assert instanovo == ["i1", "i2", "i3"]

    def test_an_empty_frame_orders_nothing(self):
        assert row_order(DATA.iloc[0:0], pd.Series(dtype="int64"), {}, "mass") == []


class TestBuildTableFrame:
    def test_there_is_one_row_per_datapoint(self):
        ranks, best, labels, _classes, visible = _assembled()
        frame = build_table_frame(DATA, visible, labels, ranks, best, set(), "mass")
        assert len(frame) == len(DATA)

    def test_rows_follow_the_tool_then_rank_order(self):
        ranks, best, labels, _classes, visible = _assembled()
        frame = build_table_frame(DATA, visible, labels, ranks, best, set(), "mass")
        assert list(frame["_id"]) == ["i1", "i2", "i3", "c1"]

    def test_the_best_datapoint_of_each_tool_is_starred(self):
        ranks, best, labels, _classes, visible = _assembled()
        frame = build_table_frame(DATA, visible, labels, ranks, best, set(), "mass")
        starred = [row["_id"] for _, row in frame.iterrows() if row["Tool"].endswith("\u2605")]
        assert sorted(starred) == ["c1", "i1"]

    def test_the_show_column_reflects_the_selection(self):
        ranks, best, labels, _classes, visible = _assembled()
        frame = build_table_frame(DATA, visible, labels, ranks, best, {"i2"}, "mass")
        assert dict(zip(frame["_id"], frame["Show"])) == {"i1": False, "i2": True, "i3": False, "c1": False}

    def test_every_metric_column_is_present(self):
        ranks, best, labels, _classes, visible = _assembled()
        frame = build_table_frame(DATA, visible, labels, ranks, best, set(), "mass")
        for label, _spec in METRIC_COLUMNS:
            assert label in frame.columns

    def test_the_visible_parameter_columns_are_the_discriminating_ones(self):
        _ranks, _best, _labels, _classes, visible = _assembled()
        assert set(visible) == {"decoding_strategy", "n_beams"}

    def test_hidden_columns_do_not_reach_the_frame(self):
        ranks, best, labels, _classes, visible = _assembled()
        frame = build_table_frame(DATA, visible, labels, ranks, best, set(), "mass")
        assert "ProteoBench ID" not in frame.columns
        assert "Hash" not in frame.columns
        assert "Decoding" in frame.columns

    def test_there_is_no_label_column_unless_labels_are_editable(self):
        ranks, best, labels, _classes, visible = _assembled()
        plain = build_table_frame(DATA, visible, labels, ranks, best, set(), "mass")
        editable = build_table_frame(
            DATA, visible, labels, ranks, best, set(), "mass", editable_labels=True, custom_labels={"i1": "mine"}
        )
        assert "Label" not in plain.columns
        assert list(editable[editable["_id"] == "i1"]["Label"]) == ["mine"]

    def test_blank_parameter_values_render_as_empty_not_nan(self):
        df = pd.concat([DATA, pd.DataFrame([_datapoint("i4", "InstaNovo", 0.8, decoding_strategy=None)])])
        df = df.reset_index(drop=True)
        ranks, best, labels, _classes, visible = _assembled(df)
        frame = build_table_frame(df, visible, labels, ranks, best, set(), "mass")
        assert "" in list(frame["Decoding"])
        assert not any(str(v) == "nan" for v in frame["Decoding"])

    def test_the_evaluation_type_changes_the_metric_columns(self):
        df = DATA.copy()
        altered = {level: {"mass": {"auc": 0.95}, "exact": {"auc": 0.10}} for level in ("peptide", "aa")}
        df.at[0, "results"] = altered
        ranks, best, labels, _classes, visible = _assembled(df)
        mass = build_table_frame(df, visible, labels, ranks, best, set(), "mass")
        exact = build_table_frame(df, visible, labels, ranks, best, set(), "exact")
        assert mass[mass["_id"] == "i1"]["Mean AUC"].iloc[0] == pytest.approx(0.95)
        assert exact[exact["_id"] == "i1"]["Mean AUC"].iloc[0] == pytest.approx(0.10)


class TestParametersColumn:
    """One cell naming what sets a run apart, beside the name rather than inside it."""

    def test_it_sits_between_the_name_and_the_rank(self):
        ranks, best, labels, _classes, visible = _assembled()
        frame = build_table_frame(DATA, visible, labels, ranks, best, set(), "mass")
        columns = list(frame.columns)
        assert columns.index("Datapoint") < columns.index("Parameters") < columns.index("Rank")

    def test_it_names_what_separates_a_tools_own_runs(self):
        ranks, best, labels, _classes, visible = _assembled()
        frame = build_table_frame(DATA, visible, labels, ranks, best, set(), "mass")
        row = frame[frame["_id"] == "i2"].iloc[0]
        assert "beam search" in row["Parameters"]

    def test_a_tool_submitted_once_leaves_the_cell_empty(self):
        single = DATA[DATA["software_name"] == "Casanovo"].reset_index(drop=True)
        ranks, best, labels, _classes, visible = _assembled(single)
        frame = build_table_frame(single, visible, labels, ranks, best, set(), "mass")
        assert list(frame["Parameters"]) == [""]

    def test_it_can_be_switched_off(self):
        ranks, best, labels, _classes, visible = _assembled()
        frame = build_table_frame(DATA, visible, labels, ranks, best, set(), "mass", show_variants=False)
        assert "Parameters" not in frame.columns

    def test_filtering_to_one_tool_keeps_the_descriptions_it_was_given(self):
        # The table narrows its rows with the tool filter but passes the descriptions computed
        # over every datapoint, so a run keeps naming how it differs from its tool's other runs.
        ranks, best, labels, _classes, visible = _assembled()
        variants = build_variant_descriptions(DATA)
        one_tool = DATA[DATA["software_name"] == "InstaNovo"]
        frame = build_table_frame(one_tool, visible, labels, ranks, best, set(), "mass", variants=variants)
        assert all(cell for cell in frame["Parameters"])


class TestCustomLabelsByIndex:
    def test_labels_are_keyed_by_id_not_by_index(self):
        # The index is rebuilt whenever datapoints are reloaded, which would otherwise reassign a
        # viewer's labels to different runs.
        shuffled = DATA.iloc[::-1].reset_index(drop=True)
        mapping = custom_labels_by_index(shuffled, {"i1": "mine"})
        assert len(mapping) == 1
        assert shuffled.at[list(mapping)[0], "id"] == "i1"

    def test_ids_absent_from_the_frame_are_dropped(self):
        assert custom_labels_by_index(DATA, {"nope": "x"}) == {}


class TestSelectionSummary:
    def test_it_counts_datapoints_and_tools(self):
        assert selection_summary(DATA, ["i1", "i2", "c1"]) == "3 datapoints from 2 tools."

    def test_it_uses_the_singular_for_one(self):
        assert selection_summary(DATA, ["i1"]) == "1 datapoint from 1 tool."

    def test_an_empty_selection_says_so(self):
        assert selection_summary(DATA, []) == "Nothing selected."


class TestColumnPresets:
    def test_the_default_preset_shows_only_the_discriminating_columns(self):
        key, _label, visible_classes = COLUMN_PRESETS[0]
        assert key == "default"
        assert visible_classes == ("discriminating",)

    def test_show_all_covers_every_class(self):
        _key, _label, visible_classes = COLUMN_PRESETS[-1]
        assert set(visible_classes) == {"discriminating", "contextual", "uniform", "identifier"}


class TestSyncSelectionFromEditor:
    """
    The callback that keeps a tick from arriving a run late.

    The figures on the results tabs are drawn above the table, so they are built before
    ``st.data_editor`` returns. This callback runs before the script body of the rerun a tick
    triggers, which is what makes the tick reach the figure on that same run rather than the
    next one.
    """

    EDITOR, ORDER, SELECTION = "editor", "order", "selection"

    def _run(self, edited_rows, order=("a", "b", "c"), selected=()):
        import streamlit as st

        st.session_state[self.EDITOR] = {"edited_rows": edited_rows, "added_rows": [], "deleted_rows": []}
        st.session_state[self.ORDER] = list(order)
        st.session_state[self.SELECTION] = set(selected)
        sync_selection_from_editor(self.EDITOR, self.ORDER, self.SELECTION)
        return st.session_state[self.SELECTION]

    def test_ticking_a_row_adds_its_id(self):
        assert self._run({1: {"Show": True}}, selected=["a"]) == {"a", "b"}

    def test_unticking_a_row_removes_its_id(self):
        assert self._run({0: {"Show": False}}, selected=["a", "c"]) == {"c"}

    def test_the_row_position_is_read_against_the_order_the_edit_was_made_on(self):
        assert self._run({2: {"Show": True}}, order=["x", "y", "z"]) == {"z"}

    def test_an_edit_to_another_column_leaves_the_selection_alone(self):
        assert self._run({0: {"Label": "mine"}}, selected=["b"]) == {"b"}

    def test_a_position_past_the_end_is_ignored_rather_than_raising(self):
        # The order is replaced on every run; a stale payload must not take the page down.
        assert self._run({9: {"Show": True}}, selected=["a"]) == {"a"}

    def test_several_edits_in_one_payload_all_apply(self):
        assert self._run({0: {"Show": False}, 2: {"Show": True}}, selected=["a", "b"]) == {"b", "c"}

    def test_no_edits_leaves_the_selection_untouched(self):
        assert self._run({}, selected=["a", "b"]) == {"a", "b"}
