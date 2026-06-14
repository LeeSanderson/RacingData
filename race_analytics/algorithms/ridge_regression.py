from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from race_analytics.algorithms.regressor import RegressorAlgorithm


class RidgeRegressionAlgorithm(RegressorAlgorithm):
    def _create_model(self) -> Pipeline:
        return make_pipeline(
            StandardScaler(),
            PolynomialFeatures(degree=2, interaction_only=False),
            Ridge(),
        )
