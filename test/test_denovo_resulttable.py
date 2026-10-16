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
    build_group_frame,
    header_for,
    metric_value,
)

from proteobench.plotting.plot_generator_denovo import (  # noqa: E402
    build_display_labels,
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


class TestBuildGroupFrame:
    def test_rows_are_ranked_best_first(self):
        ranks, best, labels, _, visible = _assembled()
        frame = build_group_frame(DATA, "InstaNovo", visible, labels, ranks, best["InstaNovo"], set(), "mass")
        assert list(frame["Rank"]) == [1, 2, 3]
        assert list(frame["_id"]) == ["i1", "i2", "i3"]

    def test_only_the_named_tools_submissions_are_included(self):
        ranks, best, labels, _, visible = _assembled()
        frame = build_group_frame(DATA, "Casanovo", visible, labels, ranks, best["Casanovo"], set(), "mass")
        assert list(frame["_id"]) == ["c1"]

    def test_the_best_datapoint_is_marked(self):
        ranks, best, labels, _, visible = _assembled()
        frame = build_group_frame(DATA, "InstaNovo", visible, labels, ranks, best["InstaNovo"], set(), "mass")
        assert frame.iloc[0]["Datapoint"].endswith("★")
        assert not frame.iloc[1]["Datapoint"].endswith("★")

    def test_the_show_column_reflects_the_selection(self):
        ranks, best, labels, _, visible = _assembled()
        frame = build_group_frame(DATA, "InstaNovo", visible, labels, ranks, best["InstaNovo"], {"i2"}, "mass")
        assert list(frame["Show"]) == [False, True, False]

    def test_every_metric_column_is_present(self):
        ranks, best, labels, _, visible = _assembled()
        frame = build_group_frame(DATA, "InstaNovo", visible, labels, ranks, best["InstaNovo"], set(), "mass")
        for label, _spec in METRIC_COLUMNS:
            assert label in frame.columns

    def test_the_visible_parameter_columns_are_the_discriminating_ones(self):
        # decoding_strategy and n_beams differ within InstaNovo; the version and the identifiers
        # do not, so they are hidden by default and must not appear.
        _ranks, _best, _labels, _classes, visible = _assembled()
        assert set(visible) == {"decoding_strategy", "n_beams"}

    def test_hidden_columns_do_not_reach_the_frame(self):
        ranks, best, labels, _, visible = _assembled()
        frame = build_group_frame(DATA, "InstaNovo", visible, labels, ranks, best["InstaNovo"], set(), "mass")
        assert "ProteoBench ID" not in frame.columns
        assert "Hash" not in frame.columns
        assert "Decoding" in frame.columns

    def test_blank_parameter_values_render_as_empty_not_nan(self):
        df = pd.concat([DATA, pd.DataFrame([_datapoint("i4", "InstaNovo", 0.8, decoding_strategy=None)])])
        df = df.reset_index(drop=True)
        ranks, best, labels, _classes, visible = _assembled(df)
        frame = build_group_frame(df, "InstaNovo", visible, labels, ranks, best["InstaNovo"], set(), "mass")
        assert "" in list(frame["Decoding"])
        assert not any(str(v) == "nan" for v in frame["Decoding"])

    def test_the_evaluation_type_changes_the_metric_columns(self):
        df = DATA.copy()
        altered = {level: {"mass": {"auc": 0.95}, "exact": {"auc": 0.10}} for level in ("peptide", "aa")}
        df.at[0, "results"] = altered
        ranks, best, labels, _classes, visible = _assembled(df)
        mass = build_group_frame(df, "InstaNovo", visible, labels, ranks, best["InstaNovo"], set(), "mass")
        exact = build_group_frame(df, "InstaNovo", visible, labels, ranks, best["InstaNovo"], set(), "exact")
        assert mass[mass["_id"] == "i1"]["Mean AUC"].iloc[0] == pytest.approx(0.95)
        assert exact[exact["_id"] == "i1"]["Mean AUC"].iloc[0] == pytest.approx(0.10)


class TestColumnPresets:
    def test_the_default_preset_shows_only_the_discriminating_columns(self):
        key, _label, visible_classes = COLUMN_PRESETS[0]
        assert key == "default"
        assert visible_classes == ("discriminating",)

    def test_show_all_covers_every_class(self):
        _key, _label, visible_classes = COLUMN_PRESETS[-1]
        assert set(visible_classes) == {"discriminating", "contextual", "uniform", "identifier"}
