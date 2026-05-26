import pandas as pd
import tests.utils.test_data as td

from race_analytics.features.pipeline import FeaturePipeline


def _make_batch(*race_results):
    df = pd.DataFrame(list(race_results))
    df["RaceTimeInSeconds"] = df["DistanceInMeters"] / df["Speed"]
    return df


def _batch1():
    return _make_batch(
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, FinishingPosition=2),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.DuckAndVanish, td.PhilipDonovan, FinishingPosition=1),
    )


def _batch2():
    return _make_batch(
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, FinishingPosition=1),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.DuckAndVanish, td.PhilipDonovan, FinishingPosition=2),
    )


def test_process_returns_expected_stat_columns():
    pipeline = FeaturePipeline()
    result = pipeline.process(_batch1())
    for col in [
        "NumberOfPriorRaces",
        "JockeyNumberOfPriorRaces",
        "TrainerNumberOfPriorRaces",
        "KnownHorseAndJockey",
        "Surface_Turf",
        "Going_Good",
        "RaceType_Flat",
    ]:
        assert col in result.columns, f"Missing column: {col}"


def test_state_accumulates_across_calls():
    pipeline = FeaturePipeline()
    pipeline.process(_batch1())
    result2 = pipeline.process(_batch2())
    secret = result2[result2["HorseId"] == td.SecretSecret.HorseId].iloc[0]
    assert secret["NumberOfPriorRaces"] == 1


def test_save_methods_write_non_empty_csvs(tmp_path):
    pipeline = FeaturePipeline()
    pipeline.process(_batch1())
    pipeline.save_race_features(str(tmp_path / "Race_Features.csv"))
    pipeline.save_horse_stats(str(tmp_path / "Horse_Stats.csv"))
    pipeline.save_jockey_stats(str(tmp_path / "Jockey_Stats.csv"))
    pipeline.save_trainer_stats(str(tmp_path / "Trainer_Stats.csv"))
    for name in ["Race_Features.csv", "Horse_Stats.csv", "Jockey_Stats.csv", "Trainer_Stats.csv"]:
        df = pd.read_csv(tmp_path / name)
        assert len(df) > 0, f"{name} is empty"
