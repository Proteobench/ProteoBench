"""
Headless render tests for the de novo module page, against real datapoints.

``test_webinterface_smoke`` renders every page with an *empty* results frame, so it never reaches
the de novo tab's plotting and table code: that path returns early on no data. These tests feed
the page actual datapoints, including several submissions of one tool, which is the case the
display is built for and the only way to exercise the ranking, colouring and grouped table in the
app rather than in isolation.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("streamlit", reason="webinterface tests require the streamlit web stack")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from webinterface_apptest_utils import mocked_backend, new_app  # noqa: E402

DENOVO_PAGE = "pages/7_denovo_DDA_HCD.py"


def _datapoint(point_id, software, auc, **fields):
    """A datapoint complete enough for the de novo page to rank, plot and tabulate it."""
    leaf = {"precision": auc, "recall": auc, "coverage": auc, "auc": auc}
    leaf_with_curve = dict(leaf, curve={"coverage": [0.0, 0.5, 1.0], "precision": [1.0, auc, auc * 0.8]})
    results = {
        level: {
            "mass": dict(leaf_with_curve),
            "exact": dict(
                leaf_with_curve,
                ambiguity={combo: dict(leaf_with_curve) for combo in ("il", "deam", "both")},
            ),
        }
        for level in ("peptide", "aa")
    }
    results["in_depth"] = {
        "PTM": {
            mod: {"counts_gt": 100, "correct_gt": 70, "counts_dn": 90, "correct_dn": 60}
            for mod in ("M-Oxidation", "Q-Deamidation", "N-Deamidation")
        },
        "Spectrum": {
            feature: {"7": {"mass": auc, "exact": auc * 0.8, "n_spectra": 100}}
            for feature in ("Missing Fragmentation Sites", "Peptide Length", "% Explained Intensity")
        },
        "Species": {"H.-sapiens": {"mass": auc, "exact": auc * 0.8, "n_spectra": 500}},
        "in_FASTA": {
            "counts": {"correct": 700, "in_fasta": 100, "not_in_fasta": 200},
            "proportions": {"correct": 0.7, "in_fasta": 0.1, "not_in_fasta": 0.2},
            "n_spectra": 1000,
        },
    }
    row = {
        "id": point_id,
        "intermediate_hash": f"hash_{point_id}",
        "software_name": software,
        "software_version": "1.2.2",
        "results": results,
        "nr_feature": 1000,
        "is_temporary": False,
        "comments": "",
    }
    row.update(fields)
    return row


#: One tool submitted three times plus two single submissions: the shape the redesign targets.
DATAPOINTS = pd.DataFrame(
    [
        _datapoint("i1", "InstaNovo", 0.95, decoding_strategy="knapsack beam search", n_beams="10"),
        _datapoint("i2", "InstaNovo", 0.90, decoding_strategy="beam search", n_beams="10"),
        _datapoint("i3", "InstaNovo", 0.85, decoding_strategy="greedy search", n_beams="1"),
        _datapoint("c1", "Casanovo", 0.92, decoding_strategy="beam search", n_beams="5"),
        _datapoint("a1", "AdaNovo", 0.80, decoding_strategy="beam search", n_beams="5"),
    ]
)


def _run(monkeypatch, datapoints=DATAPOINTS):
    with mocked_backend(datapoints=datapoints):
        app = new_app(DENOVO_PAGE, monkeypatch)
        app.run()
    return app


def test_the_page_renders_with_repeat_submissions(monkeypatch):
    app = _run(monkeypatch)
    assert not app.exception, [e.message for e in app.exception]


def test_the_main_figures_are_drawn(monkeypatch):
    # Both the scatter and the precision-coverage view live behind the same tab switcher.
    app = _run(monkeypatch)
    assert not app.exception, [e.message for e in app.exception]
    assert len(app.get("plotly_chart")) >= 1


def test_the_results_are_one_table_not_one_widget_per_tool(monkeypatch):
    # An earlier design gave each tool its own expander holding its own editor, which cost a
    # widget per tool and collapsed itself on every rerun.
    app = _run(monkeypatch)
    assert not app.exception, [e.message for e in app.exception]
    editors = app.get("dataframe")
    # One table per view: public results, submitted results, and the in-depth tab.
    assert len(editors) == 3
    rows = len(editors[0].value)
    assert rows == len(DATAPOINTS), f"expected one row per datapoint, got {rows}"


def test_the_table_lists_every_datapoint_grouped_by_tool(monkeypatch):
    app = _run(monkeypatch)
    frame = app.get("dataframe")[0].value
    tools = [str(tool).replace(" \u2605", "") for tool in frame["Tool"]]
    # Each tool's rows sit together, which is what carries the grouping now that collapsible
    # rows are unavailable.
    assert tools == sorted(tools, key=tools.index)
    assert set(tools) == {"InstaNovo", "Casanovo", "AdaNovo"}


def test_the_results_tabs_show_every_datapoint_by_default(monkeypatch):
    # Nothing is hidden from a first-time reader of the public results; the figures separate the
    # tools' best runs from the rest by opacity instead. The in-depth tab keeps its own preset,
    # which is one datapoint per tool.
    app = _run(monkeypatch)
    public, submitted, in_depth = (table.value for table in app.get("dataframe"))
    assert int(public["Show"].sum()) == len(DATAPOINTS), "every datapoint ticked"
    assert int(submitted["Show"].sum()) == len(DATAPOINTS), "every datapoint ticked"
    assert int(in_depth["Show"].sum()) == 3, "the in-depth preset is one per tool"
    starred = [bool(show) for show, tool in zip(in_depth["Show"], in_depth["Tool"]) if "\u2605" in str(tool)]
    assert all(starred), "the starred rows are the ones the preset picked"


def test_the_first_paint_agrees_with_the_ticks_it_shows(monkeypatch):
    # The figures are drawn above the table, so on the first run no selection has been written
    # yet. Left unseeded, the figure coloured each tool's best above a table saying every row
    # was shown.
    app = _run(monkeypatch)
    state = app.session_state
    keys = [key for key in state.filtered_state if str(key).endswith("_display_table_selected_ids")]
    assert len(keys) == 2, f"one per results tab, got {keys}"
    for key in keys:
        assert set(state[key]) == set(DATAPOINTS["id"]), key


def test_the_label_and_emphasis_controls_are_present(monkeypatch):
    app = _run(monkeypatch)
    assert not app.exception, [e.message for e in app.exception]
    multiselect_labels = [ms.label for ms in app.get("multiselect")]
    assert "Grey out tools" in multiselect_labels
    assert "Add to the hover box" in multiselect_labels
    assert "Label on the plot" in multiselect_labels


def test_highlighting_a_tool_reruns_cleanly(monkeypatch):
    with mocked_backend(datapoints=DATAPOINTS):
        app = new_app(DENOVO_PAGE, monkeypatch)
        app.run()
        highlight = [s for s in app.get("selectbox") if s.label == "Highlight one tool"]
        assert highlight, "no highlight selector"
        highlight[0].set_value("InstaNovo").run()
    assert not app.exception, [e.message for e in app.exception]


def test_greying_out_a_tool_reruns_cleanly(monkeypatch):
    with mocked_backend(datapoints=DATAPOINTS):
        app = new_app(DENOVO_PAGE, monkeypatch)
        app.run()
        muted = [ms for ms in app.get("multiselect") if ms.label == "Grey out tools"]
        assert muted, "no mute control"
        muted[0].set_value(["InstaNovo"]).run()
    assert not app.exception, [e.message for e in app.exception]


def test_no_tab_lets_the_viewer_choose_how_datapoints_are_named(monkeypatch):
    # A datapoint is always named by its tool and rank. What the run actually was reaches the
    # reader as a line under that name in the hover box and as the table's Parameters column,
    # so there is nothing for a naming control to decide and none is offered on any tab.
    app = _run(monkeypatch)
    assert "Name each datapoint by" not in [radio.label for radio in app.get("radio")]


def test_the_table_offers_the_parameters_column_and_starts_with_it(monkeypatch):
    app = _run(monkeypatch)
    columns = [box for box in app.get("checkbox") if box.label == "Parameters column"]
    assert columns, "no Parameters column control"
    assert all(box.value for box in columns), "the column should start shown"


def test_turning_the_parameters_column_off_reruns_cleanly(monkeypatch):
    with mocked_backend(datapoints=DATAPOINTS):
        app = new_app(DENOVO_PAGE, monkeypatch)
        app.run()
        box = [b for b in app.get("checkbox") if b.label == "Parameters column"]
        assert box, "no Parameters column control"
        box[0].set_value(False).run()
    assert not app.exception, [e.message for e in app.exception]


def test_an_empty_results_set_still_renders(monkeypatch):
    app = _run(monkeypatch, datapoints=DATAPOINTS.iloc[0:0])
    assert not app.exception, [e.message for e in app.exception]


def test_a_legacy_datapoint_without_curves_does_not_break_the_page(monkeypatch):
    legacy = DATAPOINTS.copy()
    stripped = {level: {"mass": {"precision": 0.5}} for level in ("peptide", "aa")}
    legacy.at[0, "results"] = stripped
    app = _run(monkeypatch, datapoints=legacy)
    assert not app.exception, [e.message for e in app.exception]


def test_clicking_a_point_highlights_its_tool(monkeypatch):
    """
    ``AppTest`` cannot click a Plotly point, so the selection payload is stubbed.

    This is the only way to reach the ``on_select="rerun"`` handler. Without it the handler wrote
    the highlight selectbox's own key after that selectbox had been built, which raises
    ``StreamlitAPIException``, and acting on a selection that persists across reruns looped.
    """
    import streamlit as st

    clicked_id = DATAPOINTS.iloc[0]["id"]
    tool = DATAPOINTS.iloc[0]["software_name"]
    real_chart = st.plotly_chart

    class _Event(dict):
        @property
        def selection(self):
            return {"points": [{"customdata": [clicked_id]}]}

    def fake_chart(*args, **kwargs):
        out = real_chart(*args, **kwargs)
        return _Event() if kwargs.get("on_select") == "rerun" else out

    with mocked_backend(datapoints=DATAPOINTS):
        monkeypatch.setattr(st, "plotly_chart", fake_chart)
        app = new_app(DENOVO_PAGE, monkeypatch)
        app.run()

    assert not app.exception, [e.message for e in app.exception]
    highlight = [s for s in app.get("selectbox") if s.label == "Highlight one tool"]
    assert highlight, "no highlight selector"
    assert highlight[0].value == tool, f"expected {tool}, got {highlight[0].value}"


def test_the_figure_view_switcher_builds_one_figure_at_a_time(monkeypatch):
    with mocked_backend(datapoints=DATAPOINTS):
        app = new_app(DENOVO_PAGE, monkeypatch)
        app.run()
        # `app.get("segmented_control")` is empty in this Streamlit build; the elements are
        # reported under "button_group", which is what st.segmented_control renders as.
        views = [v for v in app.get("button_group") if v.label == "View"]
        assert len(views) >= 2, "each of the two results tabs needs its own view switcher"
        assert len(app.get("plotly_chart")) == 3
        views[0].set_value("Precision-Coverage Curves").run()
        # Still three: the public tab swapped its figure rather than adding one.
        assert len(app.get("plotly_chart")) == 3
    assert not app.exception, [e.message for e in app.exception]


def test_the_table_can_be_ticked_in_bulk(monkeypatch):
    with mocked_backend(datapoints=DATAPOINTS):
        app = new_app(DENOVO_PAGE, monkeypatch)
        app.run()
        assert int(app.get("dataframe")[0].value["Show"].sum()) == len(DATAPOINTS), "default is all"

        for label, expected in (("Tick none", 0), ("Best per tool", 3), ("Tick all", len(DATAPOINTS))):
            button = [b for b in app.get("button") if b.label == label]
            assert button, f"no '{label}' button"
            button[0].click().run()
            got = int(app.get("dataframe")[0].value["Show"].sum())
            assert got == expected, f"{label}: expected {expected} ticked, got {got}"
    assert not app.exception, [e.message for e in app.exception]


def test_the_table_rows_can_be_narrowed_to_one_tool(monkeypatch):
    with mocked_backend(datapoints=DATAPOINTS):
        app = new_app(DENOVO_PAGE, monkeypatch)
        app.run()
        tool_filter = [ms for ms in app.get("multiselect") if ms.label == "Show rows for"]
        assert tool_filter, "no tool filter"
        tool_filter[0].set_value(["InstaNovo"]).run()

        frame = app.get("dataframe")[0].value
        assert len(frame) == 3, f"InstaNovo has three submissions, got {len(frame)}"
        assert {str(t).replace(" \u2605", "") for t in frame["Tool"]} == {"InstaNovo"}

        # Clearing the filter restores every row, with the ticks untouched.
        tool_filter = [ms for ms in app.get("multiselect") if ms.label == "Show rows for"]
        tool_filter[0].set_value([]).run()
        restored = app.get("dataframe")[0].value
        assert len(restored) == len(DATAPOINTS)
        assert int(restored["Show"].sum()) == len(DATAPOINTS)
    assert not app.exception, [e.message for e in app.exception]


class TestInDepthTab:
    """The 'Compare Results' tab: presets, labelling, and the grouped table beside the figures."""

    def test_the_selection_presets_are_offered(self, monkeypatch):
        app = _run(monkeypatch)
        assert not app.exception, [e.message for e in app.exception]
        labels = [radio.label for radio in app.get("radio")]
        assert "Compare" in labels

    def test_the_cross_tool_preset_selects_one_datapoint_per_tool(self, monkeypatch):
        # Three tools, so the default in-depth selection is three datapoints, reported by the
        # summary line under the collapsed controls.
        app = _run(monkeypatch)
        captions = [caption.value for caption in app.get("caption")]
        assert "3 datapoints from 3 tools." in captions, captions

    def test_switching_to_the_within_tool_preset_reruns_cleanly(self, monkeypatch):
        with mocked_backend(datapoints=DATAPOINTS):
            app = new_app(DENOVO_PAGE, monkeypatch)
            app.run()
            compare = [r for r in app.get("radio") if r.label == "Compare"]
            assert compare, "no preset control"
            # No "Apply preset" press: moving a preset control re-picks the selection itself.
            assert not [b for b in app.get("button") if b.label == "Apply preset"]
            compare[0].set_value("tool_specific").run()
            # Switching the preset re-picked the selection on its own: "Within one tool" on the
            # default tool, which has a single submission.
            assert "1 datapoint from 1 tool." in [c.value for c in app.get("caption")]

            tool = [s for s in app.get("selectbox") if s.label == "Tool"]
            assert tool, "no tool selector"
            tool[0].set_value("InstaNovo").run()
            assert "3 datapoints from 1 tool." in [c.value for c in app.get("caption")]
        assert not app.exception, [e.message for e in app.exception]

    def test_the_emphasis_control_is_called_highlight(self, monkeypatch):
        # It was "Bring forward", which named the visual effect rather than the thing the
        # reader is trying to do, and matched nothing else on the page.
        app = _run(monkeypatch)
        labels = [box.label for box in app.get("selectbox")]
        assert "Highlight" in labels, labels
        assert "Bring forward" not in labels

    def test_resetting_the_in_depth_selection_reruns_cleanly(self, monkeypatch):
        with mocked_backend(datapoints=DATAPOINTS):
            app = new_app(DENOVO_PAGE, monkeypatch)
            app.run()
            reset = [b for b in app.get("button") if b.label == "Reset selection and labels"]
            assert reset, "no reset button"
            reset[0].click().run()
        assert not app.exception, [e.message for e in app.exception]

    def test_only_the_figures_on_screen_are_built(self, monkeypatch):
        # The point of the rewrite: generate_in_depth_plots builds sixteen figures, of which only
        # one is ever on screen, and Streamlit executes every tab body on every run. The two main
        # views sit behind a radio for the same reason, so each tab builds one figure, not two.
        app = _run(monkeypatch)
        assert not app.exception, [e.message for e in app.exception]
        charts = app.get("plotly_chart")
        # One on the public tab, one on the submitted tab, one in-depth.
        assert len(charts) == 3, f"expected 3 figures, got {len(charts)}"

    def test_the_plot_selector_names_every_in_depth_view_on_screen(self, monkeypatch):
        # A dropdown hid what this tab can show behind one label and an arrow.
        app = _run(monkeypatch)
        plot_selectors = [s for s in app.get("button_group") if s.label == "Plot"]
        assert plot_selectors, "no plot selector"
        assert len(list(plot_selectors[0].options)) == 5

    def test_the_datapoint_table_can_be_folded_away(self, monkeypatch):
        with mocked_backend(datapoints=DATAPOINTS):
            app = new_app(DENOVO_PAGE, monkeypatch)
            app.run()
            toggle = [t for t in app.get("toggle") if t.label == "Show the datapoint table"]
            assert toggle, "no table toggle"
            assert len(app.get("dataframe")) == 3
            toggle[0].set_value(False).run()
            # The in-depth table is gone; the two results tabs keep theirs.
            assert len(app.get("dataframe")) == 2
            # And the selection it held survives, so the figure is still drawn.
            captions = [caption.value for caption in app.get("caption")]
            assert "3 datapoints from 3 tools." in captions, captions
        assert not app.exception, [e.message for e in app.exception]

    def test_each_figure_carries_its_full_explanation(self, monkeypatch):
        # The long per-figure texts the tabbed layout used to show, which the one-line captions
        # replaced rather than summarised.
        app = _run(monkeypatch)
        # Asserted on the body, not the expander label: AppTest does not report an expander
        # that carries an `icon`, though it does report what the expander contains.
        bodies = [block.value for block in app.get("markdown")]
        assert any("precision of predicted post-translational modifications" in body for body in bodies), bodies


class TestSubmittedResultsTab:
    """Tab 3 renders through the same de novo renderers as tab 1, with its own state."""

    def test_the_tab_renders_with_its_own_controls(self, monkeypatch):
        app = _run(monkeypatch)
        assert not app.exception, [e.message for e in app.exception]
        # Two independent copies of each control, one per view.
        highlight = [s for s in app.get("selectbox") if s.label == "Highlight one tool"]
        assert len(highlight) >= 2

    def test_both_views_keep_separate_selections(self, monkeypatch):
        with mocked_backend(datapoints=DATAPOINTS):
            app = new_app(DENOVO_PAGE, monkeypatch)
            app.run()
            muted = [ms for ms in app.get("multiselect") if ms.label == "Grey out tools"]
            assert len(muted) >= 2, "each view needs its own mute control"
            muted[0].set_value(["InstaNovo"]).run()
            still = [ms for ms in app.get("multiselect") if ms.label == "Grey out tools"]
            assert list(still[1].value) == [], "greying out in one view must not affect the other"
        assert not app.exception, [e.message for e in app.exception]


def test_the_ranking_rule_is_stated_wherever_a_rank_is_shown(monkeypatch):
    # A clause buried in a long caption and a column tooltip does not answer the question the
    # star raises, and says nothing about the rule being fixed.
    app = _run(monkeypatch)
    notes = [block.value for block in app.get("info") if "mean AUC" in block.value]
    assert len(notes) == 3, f"one per ranked table, got {len(notes)}"
    note = notes[0]
    assert "peptide-level and amino-acid-level AUC" in note
    assert "same tool" in note, "ranking is within a tool, not global"
    assert "Precision and AUC does not move the star" in note, "the fixed half has to be stated"


def test_the_hover_box_starts_with_every_parameter(monkeypatch):
    app = _run(monkeypatch)
    hover = [ms for ms in app.get("multiselect") if ms.label == "Add to the hover box"]
    assert len(hover) == 2, "one per results tab"
    for control in hover:
        # `options` reports format_func output (the display headers) while `value` reports the
        # raw column names, so these are compared by count rather than by element.
        assert control.value, "the fixture carries parameters that differ between runs"
        assert len(control.value) == len(control.options), "every parameter ticked to begin with"
