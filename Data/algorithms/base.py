from typing import Protocol
import pandas as pd


class AlgorithmProtocol(Protocol):
    max_horses: int

    def fit(self, train_df: pd.DataFrame) -> None: ...

    def predict(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
    ) -> pd.DataFrame: ...
