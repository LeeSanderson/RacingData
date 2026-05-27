# Issue 005: Trim rating columns from the card builders

## Parent PRD

`issues/prd.md`

## What to build

Now that ratings flow exclusively through the per-horse stats join (issues 002,
003, 004), the rating columns in the prediction and evaluation card builders are
unused. Remove them so the data flow is unambiguous and the only rating source is
the stats join. See the PRD's "Card builders / data flow" implementation decision.

- `race_analytics/scripts/evaluate.py`: remove `OfficialRating`,
  `RacingPostRating`, `TopSpeedRating` from the `_race_card` column list.
- `race_analytics/scripts/predict.py`: remove the same three columns from
  `_RACE_CARD_COLS`.

No algorithm should regress: by this point neither `RatingsXGBoostAlgorithm` nor
`ProxyTSRXGBoostAlgorithm` reads ratings from the card. (Note: `_KEEP_COLS` in
`evaluate.py` still needs `OfficialRating`/`RacingPostRating`/`TopSpeedRating` for
training-feature engineering and the `ProxyTSRModel` regressor — only the *card*
builders are trimmed, not the feature-engineering input.)

## Acceptance criteria

- [ ] `_race_card` (evaluate.py) and `_RACE_CARD_COLS` (predict.py) no longer
      include `OfficialRating`, `RacingPostRating` or `TopSpeedRating`
- [ ] `tests/scripts/test_evaluate.py` / `tests/scripts/test_predict.py` assert
      the built card carries no rating columns and that predictions are still
      produced
- [ ] `python -m race_analytics.scripts.evaluate --folds 2 --training-months 2`
      runs end-to-end and the rating algorithms still produce predictions (ratings
      sourced from the stats join)
- [ ] `python -m race_analytics.scripts.predict --data Data` still produces
      `TodaysPredictions.csv`

## Blocked by

- Blocked by `issues/003-ratings-xgboost-previous-race-ratings.md`
- Blocked by `issues/004-proxy-tsr-xgboost-as-of-date-proxy.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 15
- User story 21 (behaviour tests for this slice)
