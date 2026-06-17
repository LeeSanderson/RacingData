from xgboost import XGBRegressor

from race_analytics.algorithms.base import OPTIONAL_PREDICTORS
from race_analytics.algorithms.regressor import RegressorAlgorithm


class XGBoostAlgorithm(RegressorAlgorithm):
    nan_tolerant_predictors = OPTIONAL_PREDICTORS

    def _create_model(self) -> XGBRegressor:
        return XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42,
            verbosity=0,
        )
