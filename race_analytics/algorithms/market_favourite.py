import pandas as pd


class MarketFavouriteBaseline:
    def predict(self, race_ids, odds_df: pd.DataFrame) -> pd.DataFrame:
        df = odds_df[odds_df["RaceId"].isin(race_ids)][["RaceId", "HorseId", "DecimalOdds"]].copy()

        races_with_missing = df[df["DecimalOdds"].isna()]["RaceId"].unique()
        df = df[~df["RaceId"].isin(races_with_missing)]

        if df.empty:
            return pd.DataFrame(columns=["RaceId", "HorseId"])

        idx = df.groupby("RaceId")["DecimalOdds"].idxmin()
        return df.loc[idx, ["RaceId", "HorseId"]].reset_index(drop=True)
