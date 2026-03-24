"""
Score module for ProteoBench benchmarking.
"""

from proteobench.score.quant.quantscores import QuantScoresHYE
from proteobench.score.score_base import ScoreBase

__all__ = ["ScoreBase", "QuantScoresHYE"]
