import json
import os

from pytest import fixture

from proteobench.score.subcellprofile.subcellprofile_scores import Subcellprofile_Scores

dir = os.path.dirname(__file__)


@fixture
def sp_scores():
    """Fixture to return a Subcellprofile_Scores object with valid data."""
    settings = os.path.join(dir, "../data/subcellprofile/domqc_settings_raw_input.json")
    content = os.path.join(dir, "../data/subcellprofile/pg.matrix.tsv")
    settings = json.load(open(settings))
    content = open(content)
    sp_scores = Subcellprofile_Scores()
    sp_scores.generate_SpatialDataSet(content, settings)
    return sp_scores


def test_generate_SpatialDataset():
    """Test the SpatialDataSet is generated correctly and contains the dictionary with the right experiment name."""
    settings = os.path.join(dir, "../data/subcellprofile/domqc_settings_raw_input.json")
    content = os.path.join(dir, "../data/subcellprofile/pg.matrix.tsv")
    settings = json.load(open(settings))
    content = open(content)
    sp_scores = Subcellprofile_Scores()
    sp_scores.generate_SpatialDataSet(content, settings)
    assert list(sp_scores.sd.analysed_datasets_dict.keys()) == ["AlphaDIA 1.9.2 Lumos_predicted"]


# TODO: Parameterize this for different input formats
def test_run_SpatialDataSetComparison_noerrors(sp_scores: Subcellprofile_Scores):
    """Running the SpatialDataSetComparison should not raise errors with any input."""
    sp_scores.run_SpatialDataSetComparison()
