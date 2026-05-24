from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import make_pipeline

from sklearn.pipeline import Pipeline

from race_analytics.algorithms.base import BaseAlgorithm


class RidgeRegressionAlgorithm(BaseAlgorithm):
    def _create_model(self) -> Pipeline:
        return make_pipeline(
            StandardScaler(),
            PolynomialFeatures(degree=2, interaction_only=False),
            Ridge(),
        )
