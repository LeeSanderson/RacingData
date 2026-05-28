from xgboost import XGBRegressor

from race_analytics.algorithms.regressor import RegressorAlgorithm


class XGBoostAlgorithm(RegressorAlgorithm):
    def _create_model(self) -> XGBRegressor:
        return XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42,
            verbosity=0,
        )
