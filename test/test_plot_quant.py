import tempfile

import numpy as np
import pandas as pd

from proteobench.github.gh import GithubProteobotRepo
from proteobench.plotting.plot_quant import PlotDataPoint


class TestPlotDataPoint:
    def test_plot_metric_returns_a_figure(self):
        tmpdir = tempfile.TemporaryDirectory().name
        gpr = GithubProteobotRepo(clone_dir=tmpdir)
        gpr.clone_repo_anonymous()
        all_datapoints = gpr.read_results_json_repo()
        all_datapoints["old_new"] = "old"
        fig = PlotDataPoint().plot_metric(all_datapoints)
        assert fig is not None

    def test_plot_fold_change_histogram_returns_a_figure(self):
        np.random.seed(0)

        # Generate 1000 random values from a normal distribution with mean -1 and variance 1
        Nyeast = 1000
        Necoli = 500
        Nhuman = 2000

        yeastRatio = np.random.normal(loc=-1, scale=1, size=Nyeast)
        humanRatio = np.random.normal(loc=0, scale=1, size=Nhuman)
        ecoliRatio = np.random.normal(loc=2, scale=1, size=Necoli)
        combined_ratios = np.concatenate([yeastRatio, humanRatio, ecoliRatio])

        human_strings = ["HUMAN"] * Nhuman
        ecoli_strings = ["ECOLI"] * Necoli
        yeast_strings = ["YEAST"] * Nyeast

        # Concatenate the lists to create a single list
        combined_list = human_strings + ecoli_strings + yeast_strings

        combineddf = pd.DataFrame({"SPECIES": combined_list, "log2_A_vs_B": combined_ratios})
        combineddf["HUMAN"] = combineddf["SPECIES"] == "HUMAN"
        combineddf["ECOLI"] = combineddf["SPECIES"] == "ECOLI"
        combineddf["YEAST"] = combineddf["SPECIES"] == "YEAST"
        species_dict = {
            "YEAST": {"A_vs_B": 2.0, "color": "red"},
            "ECOLI": {"A_vs_B": 0.25, "color": "blue"},
            "HUMAN": {"A_vs_B": 1.0, "color": "green"},
        }
        fig = PlotDataPoint().plot_fold_change_histogram(combineddf, species_dict)
        assert fig is not None
