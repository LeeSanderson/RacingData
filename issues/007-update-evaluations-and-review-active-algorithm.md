# Issue 007 — Update `evaluations.md` headline numbers + review `ACTIVE_ALGORITHM`

## Parent PRD

`issues/prd.md` — Phase B.

## What to build

Close out the PRD by reflecting the broader-sample numbers in `evaluations.md`
and revisiting the `ACTIVE_ALGORITHM` choice on the new race set.

- Rewrite the headline coverage/accuracy section of `evaluations.md` so the
  numbers reflect the issue-006 run rather than the 415-race Phase-A slice:
  - XGBoost-family race counts updated to ~1,650 (or whatever the actual
    figure was).
  - Ridge race count unchanged.
  - Per-algorithm accuracy updated.
  - Production anchor (0.265 over 514 bets) stays — that is independent and
    out of scope per the PRD's Out-of-Scope.
- Re-examine `ACTIVE_ALGORITHM` against the broader race sample:
  - If `ProxyTSRXGBoostAlgorithm` remains the best per-pick choice (or its
    tuned variant overtakes it), document the decision and either leave the
    constant or update it.
  - If the broader sample changes the picture materially, capture the
    rationale and update `race_analytics/algorithms/__init__.py`'s
    `ACTIVE_ALGORITHM = ALGORITHMS[…]` line accordingly. The `# see
    evaluations.md` comment should still match the new section.
- Audit the rest of `evaluations.md` for any sentences that still describe
  the 415-race slice as authoritative; revise them so the document reads
  consistently against the new broader sample.

### HITL because

Choosing `ACTIVE_ALGORITHM` is a judgement call against the numbers and the
qualitative reasoning the document carries (e.g. coverage vs raw accuracy
trade-offs). Needs a human read and ratify, not an automated swap.

## Acceptance criteria

- [ ] `evaluations.md` headline coverage / accuracy numbers reflect the
      issue-006 run (race counts, per-algorithm accuracy).
- [ ] `evaluations.md` is internally consistent — no remaining text that
      treats the 415-race Phase-A slice as the authoritative result.
- [ ] `ACTIVE_ALGORITHM` decision is captured in `evaluations.md` against
      the new sample. Either:
      - It stays as `ProxyTSRXGBoostAlgorithm`, with the rationale spelled
        out, or
      - It changes, with the rationale spelled out, and
        `race_analytics/algorithms/__init__.py` is updated accordingly.
- [ ] Production anchor section unchanged (0.265 over 514 bets stays as-is).

## Blocked by

- Blocked by `issues/006-full-180-fold-reevaluation.md`.

## User stories addressed

- User story 1
- User story 12
- User story 13
