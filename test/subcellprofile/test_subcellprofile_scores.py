import json
import os

from proteobench.score.subcellprofile.subcellprofile_scores import Subcellprofile_Scores

dir = os.path.dirname(__file__)


def test_generate_SpatialDataset():
    settings = os.path.join(dir, "../data/subcellprofile/domqc_settings_raw_input.json")
    content = os.path.join(dir, "../data/subcellprofile/pg.matrix.tsv")
    settings = json.load(open(settings))
    content = open(content)
    sp_scores = Subcellprofile_Scores()
    sp_scores.generate_SpatialDataSet(content, settings)
    assert list(sp_scores.sd.analysed_datasets_dict.keys()) == ["AlphaDIA 1.9.2 Lumos_predicted"]
