from algorithms.ridge_regression import RidgeRegressionAlgorithm
from algorithms.xgboost_algorithm import XGBoostAlgorithm

ALGORITHMS = [
    RidgeRegressionAlgorithm(max_horses=10),
    XGBoostAlgorithm(max_horses=10),
]

ACTIVE_ALGORITHM = ALGORITHMS[0]
