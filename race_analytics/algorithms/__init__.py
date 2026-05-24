from race_analytics.algorithms.ridge_regression import RidgeRegressionAlgorithm
from race_analytics.algorithms.xgboost_algorithm import XGBoostAlgorithm

ALGORITHMS = [
    RidgeRegressionAlgorithm(max_horses=10),
    XGBoostAlgorithm(max_horses=10),
]

ACTIVE_ALGORITHM = ALGORITHMS[0]
