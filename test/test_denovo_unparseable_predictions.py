"""Unparseable de novo predictions are counted and reported, not dropped silently.

A prediction the tool wrote but ProteoBench cannot parse is scored as no prediction, like a blank
one. These tests pin that the two are told apart: the unparseable ones are logged with examples,
labelled in ``prediction_status``, and counted in the datapoint's ``results["predictions"]``.
"""

import logging

import numpy as np
import pandas as pd
import pytest

from proteobench.datapoint.denovo_datapoint import summarize_prediction_status
from proteobench.io.parsing.parse_settings import ParseSettingsDeNovo, parse_peptidoform_or_none


class _Settings(ParseSettingsDeNovo):
    """ParseSettingsDeNovo without the TOML plumbing; only the row-level helpers are exercised."""

    def __init__(self):
        pass


PREDICTIONS = pd.DataFrame(
    {
        "spectrum_id": [1, 2, 3, 4, 5, 6, 7],
        "proforma": [
            "PEPTIDEK",  # valid
            "[UNIMOD:1]-PEPTIDEK",  # valid
            "",  # blank: the tool made no prediction
            None,  # missing: the tool made no prediction
            "PEP[not a modification]K",  # unresolvable modification
            "[UNIMOD:1]-",  # tags but no residues
            "PEP)TIDEK",  # not ProForma at all
        ],
    }
)
UNPARSEABLE = {5: "PEP[not a modification]K", 6: "[UNIMOD:1]-", 7: "PEP)TIDEK"}


@pytest.fixture
def settings():
    return _Settings()


def test_only_parsed_rows_are_kept(settings):
    kept = settings.drop_unparseable_rows(PREDICTIONS)
    assert kept["spectrum_id"].tolist() == [1, 2]
    assert kept["peptidoform"].notna().all()


def test_unparseable_rows_are_recorded_but_blank_ones_are_not(settings):
    settings.drop_unparseable_rows(PREDICTIONS)
    assert settings.unparseable_predictions == UNPARSEABLE


def test_unparseable_rows_are_logged_with_examples(settings, caplog):
    with caplog.at_level(logging.WARNING):
        settings.drop_unparseable_rows(PREDICTIONS)
    assert "3 of 7 predictions" in caplog.text
    assert "'PEP[not a modification]K'" in caplog.text


def test_nothing_is_logged_when_everything_parses(settings, caplog):
    with caplog.at_level(logging.WARNING):
        settings.drop_unparseable_rows(PREDICTIONS.iloc[:4])
    assert caplog.text == ""
    assert settings.unparseable_predictions == {}


def test_unscorable_rows_are_recorded(settings):
    settings.max_unscorable_fraction = 1.0
    df = pd.DataFrame({"spectrum_id": [1, 2], "proforma": ["PEPK", "PEPTIDEK"]})
    df["peptidoform"] = df["proforma"].apply(parse_peptidoform_or_none)
    df["aa_scores"] = [[0.1, 0.2, 0.3, 0.4], [0.1, 0.2]]  # the second has too few scores
    kept = settings.drop_unscorable_rows(df)
    assert kept["spectrum_id"].tolist() == [1]
    assert settings.unscorable_predictions == {2: "PEPTIDEK"}


def _joined(settings, ground_truth_ids):
    """What the ground-truth join produces: one row per ground-truth spectrum, NaN where nothing was kept."""
    kept = settings.drop_unparseable_rows(PREDICTIONS)
    settings.unscorable_predictions = {2: "[UNIMOD:1]-PEPTIDEK"}
    kept = kept[kept["spectrum_id"] != 2]  # as drop_unscorable_rows would
    ground_truth = pd.DataFrame({"spectrum_id": ground_truth_ids})
    return pd.merge(ground_truth, kept, on="spectrum_id", how="left")


def test_every_spectrum_gets_a_status(settings):
    df = settings.mark_prediction_status(_joined(settings, [1, 2, 3, 4, 5, 6, 7, 8]))
    assert df.set_index("spectrum_id")["prediction_status"].to_dict() == {
        1: "scored",
        2: "unscorable",
        3: "no prediction",
        4: "no prediction",
        5: "unparseable",
        6: "unparseable",
        7: "unparseable",
        8: "no prediction",  # in the ground truth, absent from the submission
    }
    unscored = df.set_index("spectrum_id")["unscored_prediction"]
    assert unscored[5] == "PEP[not a modification]K"
    assert unscored[2] == "[UNIMOD:1]-PEPTIDEK"
    assert unscored[[1, 3, 4, 8]].isna().all()


def test_status_does_not_change_what_is_scored(settings):
    df = settings.mark_prediction_status(_joined(settings, [1, 2, 3, 4, 5, 6, 7, 8]))
    scored = df["prediction_status"] == "scored"
    assert np.array_equal(scored.to_numpy(), df["peptidoform"].notna().to_numpy())


def test_summary_counts_and_examples(settings):
    df = settings.mark_prediction_status(_joined(settings, [1, 2, 3, 4, 5, 6, 7, 8]))
    assert summarize_prediction_status(df, n_examples=2) == {
        "n_spectra": 8,
        "n_scored": 1,
        "n_no_prediction": 3,
        "n_unparseable": 3,
        "n_unscorable": 1,
        "unparseable_examples": ["PEP[not a modification]K", "[UNIMOD:1]-"],
    }
