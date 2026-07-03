import os

import pandas as pd
import pytest

from proteobench.io.parsing.parse_ion import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.entrapment.entrapment_base_module import EntrapmentModule
from proteobench.score.entrapmentscores import EntrapmentScores

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data/entrapment")
TESTDATA_FILE = os.path.join(TESTDATA_DIR, "entrapment_test_subset.parquet")
MAPPING_FILE = os.path.join(TESTDATA_DIR, "entrapment_mapping_subset.txt")
PARSE_SETTINGS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "proteobench",
        "io",
        "parsing",
        "io_parse_settings",
        "entrapment",
        "DIA",
        "ion",
        "Astral",
    )
)

# Ground truth baked into the fixture: a 100-row DIA-NN report subset built so that
# the target/entrapment composition, and the pairing of entrapments to their real
# target counterpart, are known exactly. See testfolder/aaaaah.ipynb for how it was
# generated from a full DIA-NN report and the ProteoBench entrapment mapping file.
N_TARGETS_UNPAIRED = 85  # targets with no identified entrapment counterpart
N_ENTRAP_NO_PAIR = 5  # entrapments with no identified paired target
N_ENTRAP_LOWER = 2  # entrapments whose paired target has a lower (better) score, i.e. the target wins
N_ENTRAP_HIGHER = 3  # entrapments whose paired target has a higher (worse) score, i.e. the entrapment wins
N_TARGETS_PAIRED = N_ENTRAP_LOWER + N_ENTRAP_HIGHER  # paired targets included alongside

NR_TARGETS = N_TARGETS_UNPAIRED + N_TARGETS_PAIRED
NR_ENTRAPMENTS = N_ENTRAP_NO_PAIR + N_ENTRAP_LOWER + N_ENTRAP_HIGHER


def _build_intermediate() -> pd.DataFrame:
    """Run the fixture through the real entrapment parsing/mapping/scoring pipeline."""
    input_df = load_input_file(TESTDATA_FILE, "DIA-NN")

    parse_settings = ParseSettingsBuilder(
        parse_settings_dir=PARSE_SETTINGS_DIR, module_id="entrapment_DIA_ion_Astral"
    ).build_parser("DIA-NN")
    standard_format = parse_settings.convert_to_standard_format(input_df)

    # Bypass EntrapmentModule.__init__ (GitHub clone, remote mapping-file download)
    # and point at the small local mapping fixture instead.
    module = EntrapmentModule.__new__(EntrapmentModule)
    module.mapping_file = MAPPING_FILE
    mapped_df = module._apply_mapping(standard_format)

    return EntrapmentScores().generate_intermediate(mapped_df)


class TestEntrapmentFDPCalculation:
    @pytest.fixture(autouse=True)
    def _init(self):
        self.intermediate = _build_intermediate()
        self.scores = EntrapmentScores()

    def test_target_and_entrapment_counts_match_fixture_design(self):
        counts = self.intermediate["Target or Entrapment"].value_counts()
        assert counts["target"] == NR_TARGETS
        assert counts["entrapment"] == NR_ENTRAPMENTS

    def test_combined_fdp_matches_expected_upper_bound(self):
        combined_fdp = self.scores.calculate_upper_bound_combined_fdp(self.intermediate)
        expected = (NR_ENTRAPMENTS * 2) / (NR_TARGETS + NR_ENTRAPMENTS)
        assert combined_fdp == pytest.approx(expected)
        assert combined_fdp == pytest.approx(0.2)

    def test_lower_bound_fdp_matches_expected_value(self):
        lower_fdp = self.scores.calculate_lower_bound_fdp(self.intermediate)
        expected = NR_ENTRAPMENTS / (NR_TARGETS + NR_ENTRAPMENTS)
        assert lower_fdp == pytest.approx(expected)
        assert lower_fdp == pytest.approx(0.1)

    def test_paired_fdp_matches_independently_computed_value(self):
        paired_fdp = self.scores.calculate_paired_fdp(self.intermediate)

        # Independent re-derivation of the paired FDP (Wen et al. 2025, eq. 2), written
        # separately from EntrapmentScores._paired_fdp_from_merged so this is a genuine
        # correctness check rather than calling the same implementation twice.
        entraps = self.intermediate[self.intermediate["Target or Entrapment"] == "entrapment"]
        targets = self.intermediate[self.intermediate["Target or Entrapment"] == "target"]
        entraps_best = entraps.groupby("peptide_pair_index")["Score"].max()
        targets_best = targets.groupby("peptide_pair_index")["Score"].max()
        merged = entraps_best.to_frame("Score_entrap").join(targets_best.rename("Score_target"), how="left")

        nr_e_s_t = int(merged["Score_target"].isna().sum())
        paired = merged.dropna(subset=["Score_target"])
        # Score_entrap < Score_target: the entrapment has a better (lower-rank) score
        # than its paired target, i.e. the entrapment out-competed the target.
        nr_e_t_s = int((paired["Score_entrap"] < paired["Score_target"]).sum())

        # These two counts are guaranteed by how the fixture was constructed.
        assert nr_e_s_t == N_ENTRAP_NO_PAIR
        assert nr_e_t_s == N_ENTRAP_HIGHER

        expected = (NR_ENTRAPMENTS + nr_e_s_t + 2 * nr_e_t_s) / (NR_TARGETS + NR_ENTRAPMENTS)
        assert paired_fdp == pytest.approx(expected)
        assert paired_fdp == pytest.approx(0.21)
