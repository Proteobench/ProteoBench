from pathlib import Path

import pandas as pd
import pytest
import yaml

from proteobench.modules.denovo.denovo_base import DeNovoModule

PARAMS_DIR = Path(__file__).parent / "params" / "denovo"


@pytest.mark.parametrize(
    "tool, config, min_len, max_len, decoding",
    [
        ("AdaNovo", "adanovo/config.yaml", 6, 100, "beam search"),
        ("Casanovo", "casanovo/casanovo.yaml", 5, 100, "beam search"),
        ("ContraNovo", "contranovo/config.yaml", None, 50, "beam search"),
        ("Pi-HelixNovo", "pihelixnovo/config.yaml", None, 100, "greedy search"),
        ("Pi-PrimeNovo", "piprimenovo/config.yaml", None, 40, "beam search + PMC [0.1 Da]"),
    ],
)
def test_extract_yaml_params(tool, config, min_len, max_len, decoding):
    params = DeNovoModule.EXTRACT_PARAMS_DICT[tool](PARAMS_DIR / config)
    assert params.software_name == tool
    assert params.max_peptide_length == max_len
    assert params.decoding_strategy == decoding
    if min_len is None:
        assert pd.isna(params.min_peptide_length)
    else:
        assert params.min_peptide_length == min_len
    if tool == "Pi-PrimeNovo":
        assert params.checkpoint == "./NON351/epoch=5-step=65000.ckpt"


@pytest.mark.parametrize(
    "tool, n_beams, expected",
    [
        ("Casanovo", 0, "beam search"),
        ("Casanovo", 1, "greedy search"),
        ("Pi-PrimeNovo", 0, "greedy search"),
        ("Pi-PrimeNovo", 1, "greedy search"),
        ("Pi-HelixNovo", 5, "greedy search"),  # config sets decoding: 'greedy'
    ],
)
def test_decoding_strategy_per_tool(tmp_path, tool, n_beams, expected):
    config = {"Casanovo": "casanovo/casanovo.yaml", "Pi-PrimeNovo": "piprimenovo/config.yaml"}.get(
        tool, "pihelixnovo/config.yaml"
    )
    settings = yaml.safe_load((PARAMS_DIR / config).read_text())
    settings.update(n_beams=n_beams, PMC_enable=False)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(settings))
    assert DeNovoModule.EXTRACT_PARAMS_DICT[tool](path).decoding_strategy == expected
