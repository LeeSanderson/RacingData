from race_analytics.algorithms.win_classifier import WinClassifier


class TunedWinClassifier(WinClassifier):
    """WinClassifier with hyperparameters found via RandomizedSearchCV.

    Tuned params (40-iter search, 3-fold CV on 7-month window):
    n_estimators=500, max_depth=5, learning_rate=0.05, subsample=0.9, colsample_bytree=0.8
    """

    def __init__(self, max_horses: int = 10):
        super().__init__(
            max_horses=max_horses,
            n_estimators=500,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.8,
        )
