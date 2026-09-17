"""Tests for the de novo plotting helpers that keep repeat submissions distinguishable."""

import pandas as pd
import pytest

from proteobench.plotting.plot_generator_denovo import (
    DASH_CYCLE,
    build_curve_dashes,
    build_workflow_labels,
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


class TestBuildCurveDashes:
    def test_dashes_cycle_within_one_tool(self):
        dashes = build_curve_dashes(INSTANOVO_MODES)
        assert list(dashes[:3]) == list(DASH_CYCLE[:3])

    def test_dash_cycle_restarts_for_each_tool(self):
        df = pd.DataFrame(
            [
                _datapoint("A", "Casanovo", "beam search", 5),
                _datapoint("B", "InstaNovo", "greedy search", 1),
                _datapoint("C", "InstaNovo", "beam search", 10),
            ]
        )
        dashes = build_curve_dashes(df)
        assert dashes.iloc[0] == DASH_CYCLE[0]
        assert dashes.iloc[1] == DASH_CYCLE[0]
        assert dashes.iloc[2] == DASH_CYCLE[1]

    def test_more_submissions_than_dash_styles_wraps(self):
        df = pd.DataFrame([_datapoint(str(i), "Tool", f"strategy {i}") for i in range(len(DASH_CYCLE) + 2)])
        dashes = build_curve_dashes(df)
        assert dashes.iloc[len(DASH_CYCLE)] == DASH_CYCLE[0]

    def test_empty_frame_returns_empty(self):
        assert len(build_curve_dashes(pd.DataFrame())) == 0


@pytest.mark.parametrize("column", ["decoding_strategy", "n_beams", "checkpoint"])
def test_labels_stay_unique_when_one_field_is_unavailable(column):
    """Older datapoints may not carry every field; the rest must still separate them."""
    df = INSTANOVO_MODES.drop(columns=[column])
    labels = build_workflow_labels(df)
    assert len(set(labels)) == len(df)
