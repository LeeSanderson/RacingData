from xgboost import XGBRegressor

from xgboost import XGBRegressor

from algorithms.base import BaseAlgorithm


class XGBoostAlgorithm(BaseAlgorithm):
    def _create_model(self) -> XGBRegressor:
        return XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42,
            verbosity=0,
        )
