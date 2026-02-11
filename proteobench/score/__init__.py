"""
Score module for ProteoBench benchmarking.
"""

from proteobench.score.quantscoresHYE import QuantScoresHYE
from proteobench.score.quantscoresPYE import QuantScoresPYE
from proteobench.score.score_base import ScoreBase

__all__ = ["ScoreBase", "QuantScoresHYE"]
