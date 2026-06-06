from race_analytics.algorithms.ridge_regression import RidgeRegressionAlgorithm
from race_analytics.algorithms.xgboost_algorithm import XGBoostAlgorithm
from race_analytics.algorithms.ratings_xgboost import (
    RatingsXGBoostAlgorithm,
    RatingsXGBoostUngatedAlgorithm,
)
from race_analytics.algorithms.proxy_tsr_xgboost import (
    ProxyTSRXGBoostAlgorithm,
    RecencyWeightedProxyTSRAlgorithm,
    TunedProxyTSRXGBoostAlgorithm,
    WeightedPositionProxyTSRAlgorithm,
)
from race_analytics.algorithms.abstain_wrapper import (
    AbstainRecencyWeightedAlgorithm,
    AbstainWrapperAlgorithm,
    AbstainWrapperGapAlgorithm,
    AbstainWeightedPositionAlgorithm,
)
from race_analytics.algorithms.ltr_proxy_tsr import (
    LTRProxyTSRAlgorithm,
    AbstainWrapperLTRAlgorithm,
)
from race_analytics.algorithms.split_race_type import (
    SplitRaceTypeAlgorithm,
    AbstainWrapperSplitAlgorithm,
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
    LTRProxyTSRAlgorithm(max_horses=10),
    AbstainWrapperLTRAlgorithm(max_horses=10),
    RecencyWeightedProxyTSRAlgorithm(max_horses=10),
    AbstainRecencyWeightedAlgorithm(max_horses=10),
    SplitRaceTypeAlgorithm(max_horses=10),
    AbstainWrapperSplitAlgorithm(max_horses=10),
]

ACTIVE_ALGORITHM = ALGORITHMS[6]  # AbstainWrapperAlgorithm — see evaluations.md
