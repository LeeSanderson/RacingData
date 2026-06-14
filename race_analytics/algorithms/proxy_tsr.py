import numpy as np
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor

PROXY_TSR_FEATURES = [
    "Speed",
    "DistanceInMeters",
    "WeightInPounds",
    "HorseCount",
    "Surface_AllWeather",
    "Surface_Dirt",
    "Surface_Turf",
    "Going_Firm",
    "Going_Good",
    "Going_Good_To_Firm",
    "Going_Good_To_Soft",
    "Going_Heavy",
    "Going_Soft",
    "RaceType_Flat",
    "RaceType_Hurdle",
    "RaceType_Other",
    "RaceType_SteepleChase",
    "CourseNameEncoded",
    "FinishingPosition",
    "OverallBeatenDistance",
]


class ProxyTSRModel:
    """XGBoost regressor that predicts Racing Post TopSpeedRating from race outcomes.

    The regressor is fitted only on rows that have a real TopSpeedRating. From its
    per-race predictions two leak-free proxy views are derived:

    * ``compute_as_of_proxy`` — per-row "last prior proxy": each row gets the proxy
      of that horse's most recent race *strictly before* it (NaN for the first
      race). Used for training, so a row never sees its own or future races.
    * ``compute_horse_proxy_tsr`` — per-horse "last proxy" as of today: the proxy of
      the horse's most recent race. Used for serving.
    """

    def __init__(self):
        self._regressor = XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
            verbosity=0,
        )
        self._course_encoder = LabelEncoder()
        self._feature_cols: list[str] = []

    def _encode_courses(self, df: pd.DataFrame) -> pd.Series:
        known = set(self._course_encoder.classes_)
        return (
            df["CourseName"]
            .fillna("Unknown")
            .apply(
                lambda x: (
                    int(self._course_encoder.transform([x])[0]) if x in known else -1
                )
            )
        )

    def tune(
        self,
        train_df: pd.DataFrame,
        n_iter: int = 20,
        cv: int = 3,
        random_state: int = 42,
    ) -> None:
        """Search for better XGBRegressor hyperparameters using RandomizedSearchCV.

        Call before fit(). Updates self._regressor with an unfitted instance using
        the best found parameters. Silently skips if there are fewer than cv*2 labelled rows.
        """
        labelled = train_df[train_df["TopSpeedRating"].notna()].copy()
        if len(labelled) < cv * 2:
            return

        self._course_encoder.fit(train_df["CourseName"].fillna("Unknown"))
        labelled["CourseNameEncoded"] = self._encode_courses(labelled)
        feature_cols = [f for f in PROXY_TSR_FEATURES if f in labelled.columns]
        data = labelled[[*feature_cols, "TopSpeedRating"]].dropna(
            subset=["TopSpeedRating"]
        )
        if len(data) < cv * 2:
            return

        param_dist = {
            "n_estimators": [100, 200, 300, 500],
            "max_depth": [3, 4, 5, 6, 8],
            "learning_rate": [0.01, 0.03, 0.05, 0.1, 0.2],
            "subsample": [0.6, 0.7, 0.8, 0.9, 1.0],
            "colsample_bytree": [0.6, 0.7, 0.8, 0.9, 1.0],
        }
        search = RandomizedSearchCV(
            XGBRegressor(random_state=42, verbosity=0),
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=cv,
            scoring="neg_mean_squared_error",
            random_state=random_state,
            n_jobs=-1,
        )
        search.fit(data[feature_cols], data["TopSpeedRating"])
        self._regressor = XGBRegressor(
            **search.best_params_, random_state=42, verbosity=0
        )

    def fit(self, train_df: pd.DataFrame) -> None:
        labelled = train_df[train_df["TopSpeedRating"].notna()].copy()
        if len(labelled) == 0:
            raise ValueError(
                "No rows with TopSpeedRating found in training data — cannot fit ProxyTSRModel"
            )

        self._course_encoder.fit(train_df["CourseName"].fillna("Unknown"))
        labelled["CourseNameEncoded"] = self._encode_courses(labelled)

        self._feature_cols = [f for f in PROXY_TSR_FEATURES if f in labelled.columns]
        data = labelled[[*self._feature_cols, "TopSpeedRating"]].copy()
        self._regressor.fit(data[self._feature_cols], data["TopSpeedRating"])

    def _predict_proxy(self, df: pd.DataFrame) -> np.ndarray:
        """Per-race proxy TSR for every row of df."""
        df = df.copy()
        df["CourseNameEncoded"] = self._encode_courses(df)
        for col in self._feature_cols:
            if col not in df.columns:
                df[col] = np.nan
        return self._regressor.predict(df[self._feature_cols])

    def compute_as_of_proxy(self, df: pd.DataFrame) -> pd.Series:
        """Per-row as-of-date proxy, aligned to df.index.

        Each row gets the proxy of that horse's most recent race STRICTLY BEFORE
        it (NaN for the horse's first race). This is leak-free: a training row can
        never see its own or the horse's future races.
        """
        work = pd.DataFrame(
            {
                "HorseId": df["HorseId"].values,
                "Off": df["Off"].values,
                "_ProxyTSR": self._predict_proxy(df),
            },
            index=df.index,
        )
        work = work.sort_values(["HorseId", "Off"], kind="stable")
        work["LastProxyTSR"] = work.groupby("HorseId")["_ProxyTSR"].shift(1)
        return work["LastProxyTSR"].reindex(df.index)

    def compute_horse_proxy_tsr(self, train_df: pd.DataFrame) -> pd.DataFrame:
        """Per-horse proxy as of today: the proxy of the horse's most recent race.

        One row per horse with column ``LastProxyTSR`` — the as-of-"today" value
        serving uses for prediction.
        """
        work = pd.DataFrame(
            {
                "HorseId": train_df["HorseId"].values,
                "Off": train_df["Off"].values,
                "_ProxyTSR": self._predict_proxy(train_df),
            }
        )
        work = work.sort_values(["HorseId", "Off"], kind="stable")
        last = work.groupby("HorseId", as_index=False).tail(1)
        return (
            last[["HorseId", "_ProxyTSR"]]
            .rename(columns={"_ProxyTSR": "LastProxyTSR"})
            .reset_index(drop=True)
        )
