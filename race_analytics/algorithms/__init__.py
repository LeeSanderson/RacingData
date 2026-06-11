from race_analytics.algorithms.ridge_regression import RidgeRegressionAlgorithm
from race_analytics.algorithms.xgboost_algorithm import XGBoostAlgorithm
from race_analytics.algorithms.ratings_xgboost import (
    RatingsXGBoostAlgorithm,
    RatingsXGBoostUngatedAlgorithm,
)
from race_analytics.algorithms.win_classifier import WinClassifier
from race_analytics.algorithms.position_weighted_win_classifier import PositionWeightedWinClassifier
from race_analytics.algorithms.recency_weighted_win_classifier import RecencyWeightedWinClassifier
from race_analytics.algorithms.tuned_win_classifier import TunedWinClassifier
from race_analytics.algorithms.split_discipline_win_classifier import SplitDisciplineWinClassifier
from race_analytics.algorithms.ranking_classifier import RankingClassifier
from race_analytics.algorithms.gated_classifier import GatedClassifier


class GatedWinClassifier(GatedClassifier):
    def __init__(self, max_horses: int = 10, metric: str = "top_prob", coverage: float = 0.7):
        super().__init__(WinClassifier(max_horses=max_horses), metric=metric, coverage=coverage)


class GatedGapWinClassifier(GatedClassifier):
    def __init__(self, max_horses: int = 10, metric: str = "gap", coverage: float = 0.5):
        super().__init__(WinClassifier(max_horses=max_horses), metric=metric, coverage=coverage)


class GatedPositionWeightedWinClassifier(GatedClassifier):
    def __init__(self, max_horses: int = 10, metric: str = "top_prob", coverage: float = 0.7):
        super().__init__(PositionWeightedWinClassifier(max_horses=max_horses), metric=metric, coverage=coverage)


class GatedRecencyWeightedWinClassifier(GatedClassifier):
    def __init__(self, max_horses: int = 10, metric: str = "top_prob", coverage: float = 0.7):
        super().__init__(RecencyWeightedWinClassifier(max_horses=max_horses), metric=metric, coverage=coverage)


class GatedSplitDisciplineWinClassifier(GatedClassifier):
    def __init__(self, max_horses: int = 10, metric: str = "top_prob", coverage: float = 0.7):
        super().__init__(SplitDisciplineWinClassifier(max_horses=max_horses), metric=metric, coverage=coverage)


class GatedRankingClassifier(GatedClassifier):
    def __init__(self, max_horses: int = 10, metric: str = "gap", coverage: float = 0.7):
        super().__init__(RankingClassifier(max_horses=max_horses), metric=metric, coverage=coverage)


ALGORITHMS = [
    RidgeRegressionAlgorithm(max_horses=10),
    XGBoostAlgorithm(max_horses=10),
    RatingsXGBoostAlgorithm(max_horses=10),
    RatingsXGBoostUngatedAlgorithm(max_horses=10),
    WinClassifier(max_horses=10),
    TunedWinClassifier(max_horses=10),
    GatedWinClassifier(max_horses=10),
    GatedGapWinClassifier(max_horses=10),
    PositionWeightedWinClassifier(max_horses=10),
    GatedPositionWeightedWinClassifier(max_horses=10),
    RankingClassifier(max_horses=10),
    GatedRankingClassifier(max_horses=10),
    RecencyWeightedWinClassifier(max_horses=10),
    GatedRecencyWeightedWinClassifier(max_horses=10),
    SplitDisciplineWinClassifier(max_horses=10),
    GatedSplitDisciplineWinClassifier(max_horses=10),
]

ACTIVE_ALGORITHM = ALGORITHMS[13]  # GatedRecencyWeightedWinClassifier — see evaluations.md
