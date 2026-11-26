from pathlib import Path

from proteobench.io.parsing.parse_peptidoform import load_input_file

TESTDATA_DIR = Path(__file__).parent / "data" / "quant" / "quant_lfq_peptidoform_DDA"


def test_load_proteome_discoverer_unmodified_peptides():
    df = load_input_file(TESTDATA_DIR / "ProteomeDIscoverer_PeptideGroups_trimmed.txt", "Proteome Discoverer")
    unmodified = df["Modifications"] == ""
    assert unmodified.any()
    assert (df.loc[unmodified, "proforma"] == df.loc[unmodified, "Sequence"]).all()
    assert "NM[Oxidation]GGPYGGGNYGPGGSGGSGGYGGR" in set(df["proforma"])
