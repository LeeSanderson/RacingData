from race_analytics.algorithms.ridge_regression import RidgeRegressionAlgorithm
from race_analytics.algorithms.xgboost_algorithm import XGBoostAlgorithm
from race_analytics.algorithms.ratings_xgboost import (
    RatingsXGBoostAlgorithm,
    RatingsXGBoostUngatedAlgorithm,
)
from race_analytics.algorithms.proxy_tsr_xgboost import (
    ProxyTSRXGBoostAlgorithm,
    TunedProxyTSRXGBoostAlgorithm,
    WeightedPositionProxyTSRAlgorithm,
)
from race_analytics.algorithms.abstain_wrapper import (
    AbstainWrapperAlgorithm,
    AbstainWrapperGapAlgorithm,
    AbstainWeightedPositionAlgorithm,
)

ALGORITHMS = [
    RidgeRegressionAlgorithm(max_horses=10),
    XGBoostAlgorithm(max_horses=10),
    RatingsXGBoostAlgorithm(max_horses=10),
    RatingsXGBoostUngatedAlgorithm(max_horses=10),
    ProxyTSRXGBoostAlgorithm(max_horses=10),
    TunedProxyTSRXGBoostAlgorithm(max_horses=10),
    AbstainWrapperAlgorithm(max_horses=10),
    AbstainWrapperGapAlgorithm(max_horses=10),
    WeightedPositionProxyTSRAlgorithm(max_horses=10),
    AbstainWeightedPositionAlgorithm(max_horses=10),
]

ACTIVE_ALGORITHM = ALGORITHMS[6]  # AbstainWrapperAlgorithm — see evaluations.md
