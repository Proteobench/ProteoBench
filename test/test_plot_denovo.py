"""Tests for the de novo plotting helpers that keep repeat submissions distinguishable."""

import copy
import re

import numpy as np
import pandas as pd
import pytest

from proteobench.plotting.plot_generator_denovo import (
    DIMMED_OPACITY,
    LABEL_STYLES,
    MUTED_COLOR,
    MUTED_CURVE_OPACITY,
    SHADE_LIGHTNESS_BOUNDS,
    SOFTWARE_COLORS,
    SOFTWARE_MARKERS,
    DeNovoPlotGenerator,
    _hex_to_hsl,
    _hsl_to_hex,
    build_display_labels,
    build_workflow_labels,
    datapoint_score,
    assign_datapoint_colors,
    classify_datapoint_columns,
    columns_varying_within_tool,
    default_hidden_columns,
    ordered_datapoint_columns,
    rank_within_tools,
    resolve_coloured_datapoints,
    resolve_emphasis,
    shade_within_tool,
)


def _datapoint(point_id, software, decoding=None, n_beams=None, checkpoint=None, version="1.2.2"):
    return {
        "id": point_id,
        "software_name": software,
        "software_version": version,
        "decoding_strategy": decoding,
        "n_beams": n_beams,
        "checkpoint": checkpoint,
    }


# The seven InstaNovo v1.2.2 inference modes, as they are recorded in a datapoint.
INSTANOVO_MODES = pd.DataFrame(
    [
        _datapoint("InstaNovo_1", "InstaNovo", "greedy search", 1, "instanovo-v1.2.0"),
        _datapoint("InstaNovo_2", "InstaNovo", "greedy search", 1, "instanovo-v1.2.0; instanovoplus-v1.1.0"),
        _datapoint("InstaNovo_3", "InstaNovo", "beam search", 10, "instanovo-v1.2.0"),
        _datapoint("InstaNovo_4", "InstaNovo", "beam search", 10, "instanovo-v1.2.0; instanovoplus-v1.1.0"),
        _datapoint("InstaNovo_5", "InstaNovo", "knapsack beam search", 10, "instanovo-v1.2.0"),
        _datapoint("InstaNovo_6", "InstaNovo", "knapsack beam search", 10, "instanovo-v1.2.0; instanovoplus-v1.1.0"),
        _datapoint("InstaNovo_7", "InstaNovo", "diffusion sampling", None, "instanovoplus-v1.1.0"),
    ]
)


class TestBuildWorkflowLabels:
    def test_single_submission_keeps_the_plain_tool_name(self):
        df = pd.DataFrame([_datapoint("Casanovo_1", "Casanovo", "beam search", 5, "casanovo_massivekb.ckpt")])
        assert list(build_workflow_labels(df)) == ["Casanovo"]

    def test_each_of_the_seven_modes_gets_a_distinct_label(self):
        labels = build_workflow_labels(INSTANOVO_MODES)
        assert len(set(labels)) == len(INSTANOVO_MODES)
        assert all(label.startswith("InstaNovo") for label in labels)

    def test_label_names_the_decoding_strategy_and_beam_count(self):
        labels = build_workflow_labels(INSTANOVO_MODES)
        assert "greedy search" in labels.iloc[0]
        assert "10 beams" in labels.iloc[2]

    def test_refined_and_unrefined_runs_are_separable(self):
        # These two differ only by the extra refinement checkpoint.
        labels = build_workflow_labels(INSTANOVO_MODES)
        assert labels.iloc[2] != labels.iloc[3]
        assert "instanovoplus-v1.1.0" in labels.iloc[3]
        assert "instanovoplus" not in labels.iloc[2]

    def test_refined_run_names_the_model_that_refined_it(self):
        labels = build_workflow_labels(INSTANOVO_MODES)
        assert labels.iloc[3] == (
            "InstaNovo (beam search, 10 beams, instanovo-v1.2.0) " "with InstaNovo+ refinement (instanovoplus-v1.1.0)"
        )

    def test_unrefined_run_has_no_refinement_clause(self):
        labels = build_workflow_labels(INSTANOVO_MODES)
        assert labels.iloc[2] == "InstaNovo (beam search, 10 beams, instanovo-v1.2.0)"
        assert "refinement" not in labels.iloc[2]

    def test_single_beam_reads_as_singular(self):
        labels = build_workflow_labels(INSTANOVO_MODES)
        assert "1 beam," in labels.iloc[0]
        assert "1 beams" not in labels.iloc[0]

    def test_a_standalone_refinement_model_is_named_after_itself(self):
        # diffusion-only runs InstaNovo+ on its own -- it is not a refinement of anything, and
        # it is not InstaNovo either, even though that is its recorded software_name.
        labels = build_workflow_labels(INSTANOVO_MODES)
        assert labels.iloc[6] == "InstaNovo+ (diffusion sampling, instanovoplus-v1.1.0)"
        assert "refinement" not in labels.iloc[6]

    def test_standalone_refinement_model_is_renamed_even_as_a_lone_submission(self):
        df = INSTANOVO_MODES.iloc[[6]]
        assert list(build_workflow_labels(df)) == ["InstaNovo+"]

    def test_a_refined_run_keeps_the_base_tool_name(self):
        # The base model drove the run, so the tool name stays; only the clause names InstaNovo+.
        labels = build_workflow_labels(INSTANOVO_MODES)
        assert labels.iloc[3].startswith("InstaNovo (")

    def test_an_unrecognised_lone_checkpoint_keeps_the_software_name(self):
        df = pd.DataFrame(
            [
                _datapoint("A", "Tool", "greedy search", 1, "mystery-v2.ckpt"),
                _datapoint("B", "Tool", "beam search", 5, "mystery-v2.ckpt"),
            ]
        )
        labels = build_workflow_labels(df)
        assert all(label.startswith("Tool (") for label in labels)

    def test_unknown_refinement_model_still_gets_its_own_clause(self):
        df = pd.DataFrame(
            [
                _datapoint("A", "Tool", "beam search", 5, "base.ckpt"),
                _datapoint("B", "Tool", "beam search", 5, "base.ckpt; mystery-v2.ckpt"),
            ]
        )
        labels = build_workflow_labels(df)
        assert labels.iloc[1] == "Tool (base.ckpt) with refinement (mystery-v2.ckpt)"

    def test_multiple_refinement_stages_are_all_named(self):
        df = pd.DataFrame(
            [
                _datapoint("A", "Tool", "beam search", 5, "base.ckpt"),
                _datapoint("B", "Tool", "beam search", 5, "base.ckpt; first.ckpt; second.ckpt"),
            ]
        )
        labels = build_workflow_labels(df)
        assert labels.iloc[1] == "Tool (base.ckpt) with refinement (first.ckpt) and refinement (second.ckpt)"

    def test_constant_fields_are_left_out_of_the_label(self):
        # Both rows share a checkpoint and version, so only the strategy should appear.
        df = pd.DataFrame(
            [
                _datapoint("A", "Tool", "greedy search", 1, "same.ckpt"),
                _datapoint("B", "Tool", "beam search", 1, "same.ckpt"),
            ]
        )
        labels = build_workflow_labels(df)
        assert list(labels) == ["Tool (greedy search)", "Tool (beam search)"]

    def test_blank_fields_are_skipped(self):
        # diffusion sampling records no beam count; the label must not read "nan beams".
        labels = build_workflow_labels(INSTANOVO_MODES)
        assert "nan" not in labels.iloc[6]
        assert "None" not in labels.iloc[6]

    def test_tools_are_labelled_independently(self):
        df = pd.DataFrame(
            [
                _datapoint("A", "Casanovo", "beam search", 5, "casanovo.ckpt"),
                _datapoint("B", "InstaNovo", "greedy search", 1, "instanovo.ckpt"),
                _datapoint("C", "InstaNovo", "beam search", 10, "instanovo.ckpt"),
            ]
        )
        labels = build_workflow_labels(df)
        assert labels.iloc[0] == "Casanovo"  # only submitted once
        assert labels.iloc[1] != labels.iloc[2]

    def test_identical_parameters_fall_back_to_the_proteobench_id(self):
        df = pd.DataFrame(
            [
                _datapoint("Tool_20260815_1", "Tool", "greedy search", 1, "same.ckpt"),
                _datapoint("Tool_20260815_2", "Tool", "greedy search", 1, "same.ckpt"),
            ]
        )
        labels = build_workflow_labels(df)
        assert len(set(labels)) == 2
        assert "Tool_20260815_1" in labels.iloc[0]

    def test_missing_optional_columns_do_not_raise(self):
        df = pd.DataFrame([{"software_name": "Tool"}, {"software_name": "Tool"}])
        assert len(build_workflow_labels(df)) == 2

    def test_empty_frame_returns_empty(self):
        assert len(build_workflow_labels(pd.DataFrame())) == 0

    def test_labels_align_to_a_non_default_index(self):
        df = INSTANOVO_MODES.copy()
        df.index = range(100, 100 + len(df))
        labels = build_workflow_labels(df)
        assert list(labels.index) == list(df.index)


@pytest.mark.parametrize("column", ["decoding_strategy", "n_beams", "checkpoint"])
def test_labels_stay_unique_when_one_field_is_unavailable(column):
    """Older datapoints may not carry every field; the rest must still separate them."""
    df = INSTANOVO_MODES.drop(columns=[column])
    labels = build_workflow_labels(df)
    assert len(set(labels)) == len(df)


def _scored(point_id, software, peptide_auc, aa_auc, **fields):
    """A datapoint carrying only what the ranking helpers read: a tool name and two AUC values."""
    row = _datapoint(point_id, software, **fields)
    leaf = {}
    if peptide_auc is not None:
        leaf["peptide"] = {"mass": {"auc": peptide_auc}}
    if aa_auc is not None:
        leaf.setdefault("aa", {})["mass"] = {"auc": aa_auc}
    row["results"] = leaf
    return row


class TestDatapointScore:
    def test_score_is_the_mean_of_the_two_levels(self):
        row = pd.Series(_scored("a", "Casanovo", 0.90, 0.80))
        assert datapoint_score(row) == pytest.approx(0.85)

    def test_missing_one_level_is_unscorable(self):
        # Half the evidence cannot be compared against a datapoint carrying both levels.
        assert np.isnan(datapoint_score(pd.Series(_scored("a", "Casanovo", 0.90, None))))
        assert np.isnan(datapoint_score(pd.Series(_scored("a", "Casanovo", None, 0.80))))

    def test_missing_results_block_is_unscorable(self):
        assert np.isnan(datapoint_score(pd.Series(_datapoint("a", "Casanovo"))))

    def test_evaluation_type_selects_the_leaf(self):
        row = pd.Series(
            {
                "software_name": "Casanovo",
                "results": {
                    "peptide": {"mass": {"auc": 0.9}, "exact": {"auc": 0.5}},
                    "aa": {"mass": {"auc": 0.9}, "exact": {"auc": 0.7}},
                },
            }
        )
        assert datapoint_score(row, evaluation_type="mass") == pytest.approx(0.9)
        assert datapoint_score(row, evaluation_type="exact") == pytest.approx(0.6)

    def test_ambiguity_combo_selects_the_sub_leaf(self):
        row = pd.Series(
            {
                "software_name": "Casanovo",
                "results": {
                    "peptide": {"exact": {"auc": 0.5, "ambiguity": {"il": {"auc": 0.8}}}},
                    "aa": {"exact": {"auc": 0.5, "ambiguity": {"il": {"auc": 0.6}}}},
                },
            }
        )
        assert datapoint_score(row, "exact") == pytest.approx(0.5)
        assert datapoint_score(row, "exact", ambiguity_combo="il") == pytest.approx(0.7)


class TestRankWithinTools:
    def test_ranks_restart_for_each_tool(self):
        df = pd.DataFrame(
            [
                _scored("c1", "Casanovo", 0.70, 0.70),
                _scored("i1", "InstaNovo", 0.90, 0.90),
                _scored("c2", "Casanovo", 0.80, 0.80),
                _scored("i2", "InstaNovo", 0.60, 0.60),
            ]
        )
        ranks, best = rank_within_tools(df)
        assert list(ranks) == [2, 1, 1, 2]
        assert best == {"Casanovo": 2, "InstaNovo": 1}

    def test_a_tool_submitted_once_ranks_first(self):
        df = pd.DataFrame([_scored("a", "PepNet", 0.1, 0.1)])
        ranks, best = rank_within_tools(df)
        assert list(ranks) == [1]
        assert best == {"PepNet": 0}

    def test_the_best_of_a_tool_does_not_depend_on_how_many_it_submitted(self):
        # The whole point of ranking per tool: adding weaker runs must not change who wins.
        few = pd.DataFrame([_scored("a", "Casanovo", 0.9, 0.9), _scored("b", "InstaNovo", 0.8, 0.8)])
        many = pd.DataFrame(
            [
                _scored("a", "Casanovo", 0.9, 0.9),
                _scored("b", "InstaNovo", 0.8, 0.8),
                _scored("c", "InstaNovo", 0.1, 0.1),
                _scored("d", "InstaNovo", 0.2, 0.2),
            ]
        )
        assert rank_within_tools(few)[1]["InstaNovo"] == 1
        assert rank_within_tools(many)[1]["InstaNovo"] == 1

    def test_unscorable_datapoints_rank_last_and_never_win(self):
        df = pd.DataFrame(
            [
                _scored("a", "Casanovo", None, None),
                _scored("b", "Casanovo", 0.5, 0.5),
            ]
        )
        ranks, best = rank_within_tools(df)
        assert ranks.at[1] == 1
        assert ranks.at[0] == 2
        assert best == {"Casanovo": 1}

    def test_a_tool_with_nothing_scorable_has_no_best_but_still_ranks(self):
        df = pd.DataFrame([_scored("a", "DeepNovo", None, None)])
        ranks, best = rank_within_tools(df)
        assert list(ranks) == [1]
        assert best == {}

    def test_ties_keep_submission_order(self):
        df = pd.DataFrame([_scored("a", "Casanovo", 0.5, 0.5), _scored("b", "Casanovo", 0.5, 0.5)])
        ranks, best = rank_within_tools(df)
        assert list(ranks) == [1, 2]
        assert best == {"Casanovo": 0}

    def test_empty_frame_returns_empty(self):
        ranks, best = rank_within_tools(pd.DataFrame())
        assert len(ranks) == 0
        assert best == {}

    def test_ranks_align_to_a_non_default_index(self):
        df = pd.DataFrame(
            [_scored("a", "Casanovo", 0.5, 0.5), _scored("b", "Casanovo", 0.9, 0.9)],
            index=["x", "y"],
        )
        ranks, best = rank_within_tools(df)
        assert ranks.at["y"] == 1 and ranks.at["x"] == 2
        assert best == {"Casanovo": "y"}


class TestBuildDisplayLabels:
    def _frame(self):
        return pd.DataFrame(
            [
                _scored("i1", "InstaNovo", 0.90, 0.90, decoding="beam search", n_beams=10),
                _scored("i2", "InstaNovo", 0.70, 0.70, decoding="greedy search", n_beams=1),
            ]
        )

    def test_index_style_is_the_tool_and_its_rank(self):
        assert list(build_display_labels(self._frame(), "index")) == ["InstaNovo #1", "InstaNovo #2"]

    def test_params_style_delegates_to_the_workflow_labels(self):
        df = self._frame()
        assert list(build_display_labels(df, "params")) == list(build_workflow_labels(df))

    def test_custom_style_uses_what_was_typed(self):
        labels = build_display_labels(self._frame(), "custom", custom_labels={0: "wide beam", 1: "quick"})
        assert list(labels) == ["wide beam", "quick"]

    def test_custom_style_falls_back_per_datapoint(self):
        # A partly labelled set must stay fully labelled, not half blank.
        labels = build_display_labels(self._frame(), "custom", custom_labels={0: "  "})
        assert list(labels) == ["InstaNovo #1", "InstaNovo #2"]

    def test_custom_style_without_any_labels_matches_the_index_style(self):
        df = self._frame()
        assert list(build_display_labels(df, "custom")) == list(build_display_labels(df, "index"))

    def test_precomputed_ranks_are_reused(self):
        df = self._frame()
        ranks = pd.Series([5, 6], index=df.index)
        assert list(build_display_labels(df, "index", ranks=ranks)) == ["InstaNovo #5", "InstaNovo #6"]

    def test_unknown_style_raises(self):
        with pytest.raises(ValueError, match="Unknown label style"):
            build_display_labels(self._frame(), "verbose")

    def test_empty_frame_returns_empty(self):
        assert len(build_display_labels(pd.DataFrame(), "index")) == 0

    def test_labels_align_to_a_non_default_index(self):
        df = pd.DataFrame(
            [_scored("a", "Casanovo", 0.5, 0.5), _scored("b", "Casanovo", 0.9, 0.9)],
            index=["x", "y"],
        )
        labels = build_display_labels(df, "index")
        assert labels.at["y"] == "Casanovo #1" and labels.at["x"] == "Casanovo #2"


class TestShadeWithinTool:
    BASE = "#999933"

    def test_a_lone_datapoint_keeps_the_tool_colour(self):
        assert shade_within_tool(self.BASE, 0, 1) == self.BASE

    def test_a_family_gets_distinct_shades(self):
        shades = [shade_within_tool(self.BASE, position, 11) for position in range(11)]
        assert len(set(shades)) == 11

    def test_the_first_position_is_the_darkest(self):
        first = _hex_to_hsl(shade_within_tool(self.BASE, 0, 6))[2]
        last = _hex_to_hsl(shade_within_tool(self.BASE, 5, 6))[2]
        assert first < last

    def test_shades_stay_within_the_readable_lightness_bounds(self):
        low, high = SHADE_LIGHTNESS_BOUNDS
        for count in (2, 6, 15, 40):
            for position in range(count):
                lightness = _hex_to_hsl(shade_within_tool(self.BASE, position, count))[2]
                assert low - 1e-6 <= lightness <= high + 1e-6

    def test_hue_is_preserved_so_the_tool_stays_recognisable(self):
        base_hue = _hex_to_hsl(self.BASE)[0]
        for position in range(8):
            assert _hex_to_hsl(shade_within_tool(self.BASE, position, 8))[0] == pytest.approx(base_hue, abs=0.02)

    def test_every_registered_tool_colour_round_trips(self):
        for color in SOFTWARE_COLORS.values():
            hue, saturation, lightness = _hex_to_hsl(color)
            assert _hsl_to_hex(hue, saturation, lightness) == color.lower()


def _plottable(point_id, software, auc, *, curve=True, is_temporary=False, **fields):
    """A datapoint complete enough for both main-tab figures to draw it."""
    leaf = {"precision": auc, "recall": auc, "coverage": auc, "auc": auc}
    if curve:
        leaf["curve"] = {"coverage": [0.0, 0.5, 1.0], "precision": [1.0, auc, auc * 0.8]}
    row = _datapoint(point_id, software, **fields)
    row["results"] = {
        level: {
            "mass": dict(leaf),
            "exact": dict(leaf, **{"ambiguity": {combo: dict(leaf) for combo in ("il", "deam", "both")}}),
        }
        for level in ("peptide", "aa")
    }
    row["is_temporary"] = is_temporary
    row["old_new"] = "old"
    return row


#: Three tools, one of them submitted three times: the shape the redesign exists for.
REPEATED_TOOL = pd.DataFrame(
    [
        _plottable("i_best", "InstaNovo", 0.95, decoding="knapsack beam search", n_beams=10),
        _plottable("i_mid", "InstaNovo", 0.90, decoding="beam search", n_beams=10),
        _plottable("i_low", "InstaNovo", 0.85, decoding="greedy search", n_beams=1),
        _plottable("cas", "Casanovo", 0.92),
        _plottable("ada", "AdaNovo", 0.80),
    ]
)


class TestResolveColouredDatapoints:
    def test_one_datapoint_per_tool_is_coloured_by_default(self):
        coloured = resolve_coloured_datapoints(REPEATED_TOOL)
        assert list(coloured) == [True, False, False, True, True]

    def test_the_coloured_one_is_the_tools_best(self):
        coloured = resolve_coloured_datapoints(REPEATED_TOOL)
        assert REPEATED_TOOL.loc[coloured, "id"].tolist() == ["i_best", "cas", "ada"]

    def test_colouring_is_not_biased_by_submission_count(self):
        # A tool submitted three times contributes exactly as much colour as one submitted once.
        coloured = resolve_coloured_datapoints(REPEATED_TOOL)
        by_tool = REPEATED_TOOL.loc[coloured, "software_name"].value_counts()
        assert set(by_tool) == {1}

    def test_a_muted_tool_contributes_no_colour(self):
        coloured = resolve_coloured_datapoints(REPEATED_TOOL, muted_tools=["InstaNovo"])
        assert not coloured[REPEATED_TOOL["software_name"] == "InstaNovo"].any()
        assert coloured[REPEATED_TOOL["software_name"] != "InstaNovo"].all()

    def test_selected_ids_are_coloured_regardless_of_rank(self):
        coloured = resolve_coloured_datapoints(REPEATED_TOOL, selected_ids=["i_low"])
        assert REPEATED_TOOL.loc[coloured, "id"].tolist() == ["i_best", "i_low", "cas", "ada"]

    def test_a_selection_survives_its_tool_being_muted(self):
        # Muting is about the automatic colouring; an explicit pick is still an explicit pick.
        coloured = resolve_coloured_datapoints(REPEATED_TOOL, muted_tools=["InstaNovo"], selected_ids=["i_low"])
        assert REPEATED_TOOL.loc[coloured, "id"].tolist() == ["i_low", "cas", "ada"]

    def test_empty_frame_returns_empty(self):
        assert len(resolve_coloured_datapoints(pd.DataFrame())) == 0


def _is_legend_proxy(trace) -> bool:
    """
    Whether a trace exists only to put an entry in the legend.

    Plotly takes a legend swatch from the trace's first point, so a trace whose colours vary per
    point cannot control its own swatch. Both figures therefore carry one point-free proxy per
    tool, in the tool's colour, and keep the real traces out of the legend.
    """
    return list(trace.x) == [None]


class TestLegend:
    """The legend names tools and their colours, whatever any individual datapoint is drawn in."""

    def _legend(self, fig):
        return [trace for trace in fig.data if getattr(trace, "showlegend", False)]

    def test_scatter_has_one_entry_per_tool(self):
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL)
        assert [t.name for t in self._legend(fig)] == ["InstaNovo", "Casanovo", "AdaNovo"]

    def test_curves_have_one_entry_per_tool_not_per_datapoint(self):
        # Previously one entry per curve, which on a full results set meant ninety-one rows.
        fig = DeNovoPlotGenerator().plot_precision_coverage_curves(REPEATED_TOOL)
        assert [t.name for t in self._legend(fig)] == ["InstaNovo", "Casanovo", "AdaNovo"]

    def test_scatter_swatches_are_the_tool_colour_never_the_muted_grey(self):
        # The regression this guards: InstaNovo's first row is a greyed datapoint, so a trace
        # with per-point colours advertised itself in grey.
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL)
        for trace in self._legend(fig):
            assert trace.marker.color == SOFTWARE_COLORS[trace.name]

    def test_curve_swatches_are_the_tool_colour_never_the_muted_grey(self):
        fig = DeNovoPlotGenerator().plot_precision_coverage_curves(REPEATED_TOOL)
        for trace in self._legend(fig):
            assert trace.line.color == SOFTWARE_COLORS[trace.name]

    def test_swatches_stay_the_tool_colour_when_the_tool_is_muted(self):
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL, muted_tools=["InstaNovo"])
        entry = [t for t in self._legend(fig) if t.name == "InstaNovo"][0]
        assert entry.marker.color == SOFTWARE_COLORS["InstaNovo"]

    def test_proxies_draw_nothing(self):
        for fig in (
            DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL),
            DeNovoPlotGenerator().plot_precision_coverage_curves(REPEATED_TOOL),
        ):
            assert all(_is_legend_proxy(t) for t in self._legend(fig))

    def test_the_legend_entry_shares_a_group_with_its_data(self):
        # So that clicking the entry still toggles that tool's datapoints.
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL)
        for tool in ("InstaNovo", "Casanovo", "AdaNovo"):
            group = [t for t in fig.data if getattr(t, "legendgroup", None) == tool]
            assert sum(1 for t in group if t.showlegend) == 1
            assert sum(1 for t in group if not t.showlegend) >= 1

    def test_colorblind_mode_gives_the_proxy_the_tools_symbol(self):
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL, colorblind_mode=True)
        for trace in self._legend(fig):
            assert trace.marker.symbol == SOFTWARE_MARKERS[trace.name]


class TestPlotMainMetric:
    def _scatter(self, fig):
        """The traces carrying datapoints, excluding the legend-only proxies."""
        return [trace for trace in fig.data if trace.type == "scatter" and not _is_legend_proxy(trace)]

    def test_one_trace_per_tool_not_one_per_colour(self):
        # Grouping by colour would split a partly greyed tool into two identical legend entries,
        # which is the duplication this redesign removes.
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL)
        assert len(self._scatter(fig)) == 3

    def test_no_duplicate_legend_entries(self):
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL)
        names = [trace.name for trace in fig.data if getattr(trace, "showlegend", False)]
        assert len(names) == len(set(names))

    def test_non_best_datapoints_are_greyed_but_still_drawn(self):
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL)
        colours = [c for trace in self._scatter(fig) for c in trace.marker.color]
        assert len(colours) == len(REPEATED_TOOL)
        assert colours.count(MUTED_COLOR) == 2

    def test_highlighting_a_tool_colours_all_of_its_datapoints(self):
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL, highlight_tool="InstaNovo")
        instanovo = [t for t in self._scatter(fig) if t.name == "InstaNovo"][0]
        assert MUTED_COLOR not in list(instanovo.marker.color)
        others = [t for t in self._scatter(fig) if t.name != "InstaNovo"]
        assert all(opacity == DIMMED_OPACITY for t in others for opacity in t.marker.opacity)

    def test_hover_keeps_the_proteobench_id_line(self):
        # render_metric_plot parses the clicked point's ID out of the hover text.
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL)
        for trace in self._scatter(fig):
            for hover in trace.hovertext:
                assert re.search(r"ProteoBench ID: ([^<]+)", hover)

    def test_hover_is_short_and_names_the_datapoint(self):
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL)
        hover = self._scatter(fig)[0].hovertext[0]
        assert hover.count("<br>") + 1 <= 6
        assert "InstaNovo #1" in hover

    def test_requested_hover_columns_are_appended(self):
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL, hover_columns=["decoding_strategy"])
        hover = self._scatter(fig)[0].hovertext[0]
        assert "decoding_strategy: knapsack beam search" in hover

    def test_annotations_are_drawn_with_leader_lines_at_distinct_offsets(self):
        fig = DeNovoPlotGenerator().plot_main_metric(
            REPEATED_TOOL, highlight_tool="InstaNovo", annotation_columns=["decoding_strategy"]
        )
        arrows = [a for a in fig.layout.annotations if getattr(a, "showarrow", False)]
        assert len(arrows) == 3
        assert len({(round(a.ax), round(a.ay)) for a in arrows}) == 3

    def test_the_legacy_label_kwarg_still_annotates(self):
        # Only the coloured datapoints are labelled, and only where the column has a value:
        # of the three coloured here, just InstaNovo's best records a decoding strategy.
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL, label="decoding_strategy")
        arrows = [a for a in fig.layout.annotations if getattr(a, "showarrow", False)]
        assert len(arrows) == 1
        assert arrows[0].text == "decoding_strategy: knapsack beam search"

    def test_blank_values_are_not_annotated(self):
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL, annotation_columns=["n_beams"])
        arrows = [a for a in fig.layout.annotations if getattr(a, "showarrow", False)]
        assert [a.text for a in arrows] == ["n_beams: 10"]

    def test_an_empty_frame_returns_a_figure_rather_than_raising(self):
        # Boolean-indexing an empty frame drops its columns, which used to raise KeyError here.
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL.iloc[0:0])
        assert len([t for t in fig.data if t.type == "scatter"]) == 0

    def test_a_frame_without_old_new_does_not_raise(self):
        # Datapoints that have not been through a submission carry no old_new field.
        fig = DeNovoPlotGenerator().plot_main_metric(REPEATED_TOOL.drop(columns=["old_new"]))
        assert len(self._scatter(fig)) == 3

    def test_an_unregistered_tool_falls_back_instead_of_raising(self):
        df = pd.concat([REPEATED_TOOL, pd.DataFrame([_plottable("x", "NotATool", 0.5)])], ignore_index=True)
        fig = DeNovoPlotGenerator().plot_main_metric(df, colorblind_mode=True)
        assert len(self._scatter(fig)) == 4


class TestPlotPrecisionCoverageCurves:
    def _lines(self, fig):
        """The curve traces, excluding the legend-only proxies."""
        return [trace for trace in fig.data if trace.mode == "lines" and not _is_legend_proxy(trace)]

    def test_one_curve_per_datapoint_per_panel(self):
        fig = DeNovoPlotGenerator().plot_precision_coverage_curves(REPEATED_TOOL)
        assert len(self._lines(fig)) == 2 * len(REPEATED_TOOL)

    def test_no_curve_trace_appears_in_the_legend(self):
        # The legend is per tool now; see TestLegend.
        fig = DeNovoPlotGenerator().plot_precision_coverage_curves(REPEATED_TOOL)
        assert not any(t.showlegend for t in self._lines(fig))

    def test_non_best_curves_are_greyed_and_transparent(self):
        fig = DeNovoPlotGenerator().plot_precision_coverage_curves(REPEATED_TOOL)
        legend = [t for t in self._lines(fig) if t.xaxis in (None, "x")]
        muted = [t for t in legend if t.line.color == MUTED_COLOR]
        assert len(muted) == 2
        assert all(t.opacity == MUTED_CURVE_OPACITY for t in muted)
        assert all(t.opacity > MUTED_CURVE_OPACITY for t in legend if t not in muted)

    def test_a_datapoint_without_a_curve_is_skipped(self):
        df = pd.concat(
            [REPEATED_TOOL, pd.DataFrame([_plottable("nocurve", "PepNet", 0.5, curve=False)])],
            ignore_index=True,
        )
        fig = DeNovoPlotGenerator().plot_precision_coverage_curves(df)
        assert "PepNet" not in {t.name.split(" ")[0] for t in self._lines(fig)}

    def test_muting_a_tool_greys_all_of_its_curves(self):
        fig = DeNovoPlotGenerator().plot_precision_coverage_curves(REPEATED_TOOL, muted_tools=["InstaNovo"])
        panel_one = [t for t in self._lines(fig) if t.xaxis in (None, "x")]
        instanovo = [t for t in panel_one if t.legendgroup == "InstaNovo"]
        assert len(instanovo) == 3
        assert all(t.line.color == MUTED_COLOR for t in instanovo)


def _with_in_depth(point_id, software, auc, *, shift=0.0, **fields):
    """A datapoint carrying all four in-depth blocks, as every current datapoint does."""
    row = _plottable(point_id, software, auc, **fields)
    mods = ["M-Oxidation", "Q-Deamidation", "N-Deamidation", "N-term Acetylation"]
    row["results"]["in_depth"] = {
        "PTM": {
            mod: {"counts_gt": 1000, "correct_gt": int(700 * auc), "counts_dn": 900, "correct_dn": int(600 * auc)}
            for mod in mods
        },
        "Spectrum": {
            "Peptide Length": {
                str(length): {"mass": min(1.0, auc + shift), "exact": auc * 0.8, "n_spectra": 100 * length}
                for length in (7, 8, 9)
            }
        },
        "Species": {
            species: {"mass": min(1.0, auc + shift), "exact": auc * 0.8, "n_spectra": 500}
            for species in ("H.-sapiens", "Mus-musculus")
        },
        "in_FASTA": {
            "counts": {"correct": 700, "in_fasta": 100, "not_in_fasta": 200},
            "proportions": {"correct": 0.7, "in_fasta": 0.1, "not_in_fasta": 0.2},
            "n_spectra": 1000,
        },
    }
    return row


#: A cross-tool selection: one datapoint from each of three tools.
CROSS_TOOL = pd.DataFrame(
    [
        _with_in_depth("i1", "InstaNovo", 0.95),
        _with_in_depth("c1", "Casanovo", 0.90),
        _with_in_depth("a1", "AdaNovo", 0.85),
    ]
)

#: A tool-specific selection: three runs of one tool.
ONE_TOOL = pd.DataFrame(
    [
        _with_in_depth("i1", "InstaNovo", 0.95, decoding="knapsack beam search", n_beams=10),
        _with_in_depth("i2", "InstaNovo", 0.90, decoding="beam search", n_beams=10),
        _with_in_depth("i3", "InstaNovo", 0.85, decoding="greedy search", n_beams=1),
    ]
)


class TestAssignDatapointColors:
    def test_across_tools_each_datapoint_takes_its_tool_colour(self):
        # Hue is telling tools apart here, so shading would compete with that comparison.
        colors = assign_datapoint_colors(CROSS_TOOL)
        assert list(colors) == [SOFTWARE_COLORS[t] for t in CROSS_TOOL["software_name"]]

    def test_within_one_tool_the_datapoints_are_shaded(self):
        colors = assign_datapoint_colors(ONE_TOOL)
        assert len(set(colors)) == len(ONE_TOOL)

    def test_shading_is_ordered_best_darkest(self):
        colors = assign_datapoint_colors(ONE_TOOL)
        lightness = [_hex_to_hsl(c)[2] for c in colors]
        assert lightness == sorted(lightness)

    def test_shading_preserves_the_tools_hue(self):
        base_hue = _hex_to_hsl(SOFTWARE_COLORS["InstaNovo"])[0]
        for color in assign_datapoint_colors(ONE_TOOL):
            assert _hex_to_hsl(color)[0] == pytest.approx(base_hue, abs=0.02)

    def test_a_single_datapoint_keeps_the_plain_tool_colour(self):
        colors = assign_datapoint_colors(ONE_TOOL.head(1))
        assert list(colors) == [SOFTWARE_COLORS["InstaNovo"]]

    def test_an_unregistered_tool_falls_back(self):
        df = pd.DataFrame([_with_in_depth("x", "NotATool", 0.5)])
        assert list(assign_datapoint_colors(df)) == ["gray"]

    def test_empty_frame_returns_empty(self):
        assert len(assign_datapoint_colors(pd.DataFrame())) == 0


class TestResolveEmphasis:
    def test_nothing_highlighted_emphasises_everything(self):
        assert resolve_emphasis(CROSS_TOOL).all()

    def test_across_tools_the_highlight_follows_the_software(self):
        df = pd.concat([CROSS_TOOL, ONE_TOOL.tail(2)], ignore_index=True)
        emphasised = resolve_emphasis(df, highlight_id="i1")
        assert list(df.loc[emphasised, "software_name"].unique()) == ["InstaNovo"]
        assert int(emphasised.sum()) == 3

    def test_within_one_tool_the_highlight_narrows_to_the_datapoint(self):
        # Raising every line of the software would raise the whole selection and say nothing.
        emphasised = resolve_emphasis(ONE_TOOL, highlight_id="i2")
        assert list(ONE_TOOL.loc[emphasised, "id"]) == ["i2"]

    def test_an_unknown_id_emphasises_everything(self):
        assert resolve_emphasis(CROSS_TOOL, highlight_id="nope").all()

    def test_empty_frame_returns_empty(self):
        assert len(resolve_emphasis(pd.DataFrame())) == 0


class TestInDepthPlots:
    def _plots(self, df, **kwargs):
        return DeNovoPlotGenerator().generate_in_depth_plots(df, **kwargs)

    def test_all_five_plots_are_produced(self):
        plots = self._plots(CROSS_TOOL)
        assert set(plots) == {
            "ptm_overview",
            "ptm_specific",
            "spectrum_feature",
            "species_overview",
            "in_fasta_overview",
        }

    def test_traces_are_named_per_datapoint_not_per_tool(self):
        plots = self._plots(ONE_TOOL)
        names = [trace.name for trace in plots["ptm_overview"].data]
        assert names == ["InstaNovo #1", "InstaNovo #2", "InstaNovo #3"]

    def test_in_fasta_draws_one_bar_per_datapoint(self):
        # The bug this guards: with the tool name on the x axis, several runs of one tool landed
        # on the same category and Plotly summed their bars into a single stack above 100%.
        plots = self._plots(ONE_TOOL)
        bars = plots["in_fasta_overview"].data
        assert len(bars[0].x) == len(ONE_TOOL)
        assert len(set(bars[0].x)) == len(ONE_TOOL)
        totals = [sum(trace.y[i] for trace in bars) for i in range(len(ONE_TOOL))]
        assert all(total == pytest.approx(1.0) for total in totals)

    def test_in_fasta_used_to_collapse_repeat_submissions(self):
        # Directly: three runs of one tool must not produce one bar.
        plots = self._plots(ONE_TOOL)
        assert len(plots["in_fasta_overview"].data[0].x) != 1

    def test_spectrum_feature_keeps_its_bins_in_data_order(self):
        plots = self._plots(CROSS_TOOL)
        fig = plots["spectrum_feature"]["Peptide Length"]["mass"]
        lines = [t for t in fig.data if t.type == "scatter"]
        assert list(lines[0].x) == ["7", "8", "9"]

    def test_the_spectrum_count_panel_is_present_once(self):
        plots = self._plots(CROSS_TOOL)
        fig = plots["spectrum_feature"]["Peptide Length"]["mass"]
        assert len([t for t in fig.data if t.type == "bar"]) == 1

    def test_evaluation_type_selects_the_rate(self):
        gen = DeNovoPlotGenerator()
        mass = gen.plot_species_overview(CROSS_TOOL, evaluation_type="mass")
        exact = gen.plot_species_overview(CROSS_TOOL, evaluation_type="exact")
        mass_y = [t.y for t in mass.data if t.type == "scatter"][0]
        exact_y = [t.y for t in exact.data if t.type == "scatter"][0]
        assert mass_y != exact_y

    def test_a_category_a_datapoint_lacks_breaks_its_line(self):
        df = CROSS_TOOL.copy()
        trimmed = copy.deepcopy(df.at[1, "results"])
        del trimmed["in_depth"]["Species"]["Mus-musculus"]
        df.at[1, "results"] = trimmed
        fig = DeNovoPlotGenerator().plot_species_overview(df)
        lines = [t for t in fig.data if t.type == "scatter"]
        assert None in list(lines[1].y)
        assert lines[1].connectgaps is False

    def test_highlighting_dims_the_rest(self):
        plots = self._plots(ONE_TOOL, highlight_id="i2")
        opacities = [t.opacity for t in plots["ptm_overview"].data]
        assert sum(1 for o in opacities if o > 0.9) == 1

    def test_label_style_flows_into_every_plot(self):
        plots = self._plots(ONE_TOOL, label_style="params")
        names = [trace.name for trace in plots["ptm_overview"].data]
        # The params style names the fields that differ within the tool, and stops as soon as the
        # labels are unique: decoding strategy alone separates these three, so the beam count is
        # left out rather than lengthening every label for nothing.
        assert names == [
            "InstaNovo (knapsack beam search)",
            "InstaNovo (beam search)",
            "InstaNovo (greedy search)",
        ]
        # The same labels reach the other figures, so one selection reads identically in all five.
        assert list(plots["in_fasta_overview"].data[0].x) == names
        species = [t for t in plots["species_overview"]["mass"].data if t.type == "scatter"]
        assert [t.name for t in species] == names

    def test_custom_labels_flow_into_every_plot(self):
        plots = self._plots(ONE_TOOL, label_style="custom", custom_labels={0: "my run"})
        assert plots["ptm_overview"].data[0].name == "my run"
        assert plots["in_fasta_overview"].data[0].x[0] == "my run"

    def test_an_empty_selection_builds_every_plot(self):
        plots = self._plots(CROSS_TOOL.iloc[0:0])
        assert len(plots) == 5

    def test_a_datapoint_without_in_depth_blocks_is_skipped_not_fatal(self):
        df = CROSS_TOOL.copy()
        df.at[1, "results"] = {"peptide": {}, "aa": {}, "in_depth": {}}
        plots = self._plots(df)
        assert len(plots["ptm_overview"].data) == 2
        assert len(plots["in_fasta_overview"].data[0].x) == 2

    def test_a_modification_a_datapoint_never_recorded_is_skipped(self):
        df = CROSS_TOOL.copy()
        trimmed = copy.deepcopy(df.at[1, "results"])
        del trimmed["in_depth"]["PTM"]["Q-Deamidation"]
        df.at[1, "results"] = trimmed
        plots = self._plots(df)
        assert len(plots["ptm_overview"].data[1].x) == 3


class TestClassifyDatapointColumns:
    def _frame(self):
        # decoding_strategy differs within InstaNovo; software_version differs only between
        # tools; precursor_mass_tolerance is the same everywhere; id is an identifier.
        return pd.DataFrame(
            [
                {
                    "id": "i1",
                    "intermediate_hash": "h1",
                    "software_name": "InstaNovo",
                    "software_version": "1.2.2",
                    "decoding_strategy": "beam search",
                    "precursor_mass_tolerance": "20 ppm",
                    "tokens": None,
                },
                {
                    "id": "i2",
                    "intermediate_hash": "h2",
                    "software_name": "InstaNovo",
                    "software_version": "1.2.2",
                    "decoding_strategy": "greedy search",
                    "precursor_mass_tolerance": "20 ppm",
                    "tokens": None,
                },
                {
                    "id": "c1",
                    "intermediate_hash": "h3",
                    "software_name": "Casanovo",
                    "software_version": "4.2.0",
                    "decoding_strategy": "beam search",
                    "precursor_mass_tolerance": "20 ppm",
                    "tokens": None,
                },
            ]
        )

    def test_a_column_differing_within_a_tool_is_discriminating(self):
        classes = classify_datapoint_columns(self._frame())
        assert "decoding_strategy" in classes["discriminating"]

    def test_a_column_constant_within_every_tool_is_contextual(self):
        classes = classify_datapoint_columns(self._frame())
        assert "software_version" in classes["contextual"]

    def test_a_column_with_one_value_everywhere_is_uniform(self):
        classes = classify_datapoint_columns(self._frame())
        assert "precursor_mass_tolerance" in classes["uniform"]

    def test_identifiers_are_held_apart_from_the_ranking(self):
        # They are unique by construction, so ranking them on discrimination would put the two
        # widest and least informative columns first.
        classes = classify_datapoint_columns(self._frame())
        assert set(classes["identifier"]) == {"id", "intermediate_hash"}
        assert "id" not in classes["discriminating"]

    def test_a_column_empty_everywhere_is_dropped(self):
        classes = classify_datapoint_columns(self._frame())
        assert "tokens" not in ordered_datapoint_columns(classes)

    def test_software_name_is_never_a_column(self):
        classes = classify_datapoint_columns(self._frame())
        assert "software_name" not in ordered_datapoint_columns(classes)

    def test_metric_payloads_are_never_columns(self):
        df = self._frame()
        df["results"] = [{} for _ in range(len(df))]
        df["peptide_mass_auc"] = 0.5
        classes = classify_datapoint_columns(df)
        assert "results" not in ordered_datapoint_columns(classes)
        assert "peptide_mass_auc" not in ordered_datapoint_columns(classes)

    def test_order_is_discriminating_then_context_then_uniform_then_identifiers(self):
        classes = classify_datapoint_columns(self._frame())
        order = ordered_datapoint_columns(classes)
        assert order.index("decoding_strategy") < order.index("software_version")
        assert order.index("software_version") < order.index("precursor_mass_tolerance")
        assert order.index("precursor_mass_tolerance") < order.index("id")

    def test_the_default_hides_everything_but_the_discriminating_columns(self):
        classes = classify_datapoint_columns(self._frame())
        hidden = default_hidden_columns(classes)
        assert "decoding_strategy" not in hidden
        assert {"software_version", "precursor_mass_tolerance", "id", "intermediate_hash"} <= set(hidden)

    def test_explicit_columns_are_honoured(self):
        classes = classify_datapoint_columns(self._frame(), columns=["decoding_strategy"])
        assert ordered_datapoint_columns(classes) == ["decoding_strategy"]

    def test_an_empty_frame_classifies_without_raising(self):
        classes = classify_datapoint_columns(pd.DataFrame(), columns=["id", "decoding_strategy"])
        assert classes["identifier"] == ["id"]
        assert classes["uniform"] == ["decoding_strategy"]


class TestColumnsVaryingWithinTool:
    def test_only_columns_with_two_distinct_values_count(self):
        df = pd.DataFrame(
            [
                {"software_name": "InstaNovo", "a": "x", "b": "same"},
                {"software_name": "InstaNovo", "a": "y", "b": "same"},
            ]
        )
        assert columns_varying_within_tool(df, "InstaNovo", ["a", "b"]) == ["a"]

    def test_blanks_do_not_count_as_a_second_value(self):
        df = pd.DataFrame(
            [
                {"software_name": "InstaNovo", "a": "x"},
                {"software_name": "InstaNovo", "a": None},
            ]
        )
        assert columns_varying_within_tool(df, "InstaNovo", ["a"]) == []

    def test_other_tools_are_ignored(self):
        df = pd.DataFrame(
            [
                {"software_name": "InstaNovo", "a": "x"},
                {"software_name": "Casanovo", "a": "y"},
            ]
        )
        assert columns_varying_within_tool(df, "InstaNovo", ["a"]) == []

    def test_a_missing_column_is_skipped(self):
        df = pd.DataFrame([{"software_name": "InstaNovo"}])
        assert columns_varying_within_tool(df, "InstaNovo", ["nope"]) == []
