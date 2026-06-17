from collections.abc import Iterable

import pandas as pd

from race_analytics.features.market_prob import resolve_decimal_odds


class MarketFavouriteBaseline:
    def predict(
        self, race_ids: Iterable[int] | pd.Series, odds_df: pd.DataFrame
    ) -> pd.DataFrame:
        df = odds_df[odds_df["RaceId"].isin(race_ids)].copy()
        # Pick the favourite by resolved odds (forecast-when-present-else-SP) via the
        # single market-odds rule, so the baseline's notion of "the market" matches the
        # model's. On historic SP-only data resolved odds equal DecimalOdds (no-op).
        df["ResolvedOdds"] = resolve_decimal_odds(df)

        races_with_missing = df[df["ResolvedOdds"].isna()]["RaceId"].unique()
        df = df[~df["RaceId"].isin(races_with_missing)]

        if df.empty:
            return pd.DataFrame(columns=["RaceId", "HorseId"])

        idx = df.groupby("RaceId")["ResolvedOdds"].idxmin()
        return df.loc[idx, ["RaceId", "HorseId"]].reset_index(drop=True)
