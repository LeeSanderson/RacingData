---
name: work-on-next-issue
description: Pick the next AFK issue from issues/ and implement it end-to-end via TDD, then commit. Use when the user wants to advance the ralph queue, asks to "work on the next issue", or runs this in a /loop.
---

# Work On The Next Issue

Work on a single AFK issue: pick it, implement it via TDD, run the feedback loops, commit, and close it. 

## 1. Gather context

Run this to see what shipped recently — it prevents you re-doing work that just landed:

```
git log -n 5 --format="%H%n%ad%n%B---" --date=short
```

Then list `issues/` (skip the `issues/done/` subdirectory) and read the issue files.

You work on **AFK** issues only — never HITL.

If every AFK issue is already in `issues/done/`, output exactly:

```
<promise>NO MORE TASKS</promise>
```

and stop. (The sentinel is what the surrounding `/loop` looks for to know the queue is drained.)

## 2. Task selection

Pick **one** issue. Prioritize, highest first:

1. Critical bugfixes
2. Development infrastructure (tests, types, dev scripts) — precursors to feature work
3. Tracer bullets for new features — a tiny, end-to-end slice through every layer, then expand
4. Polish and quick wins
5. Refactors

## 3. Explore

Read the files the chosen issue touches before changing anything.

## 4. Implementation

Use the `tdd` skill to drive the change red-green-refactor.

## 5. Feedback loops

Before committing, run and fix any failures:

### After C# changes
```powershell
dotnet build && dotnet test
```

### After Python utility changes
```powershell
python -m pytest Data/utils/ Data/algorithms/ Data/scripts/
```

## 6. Close the issue

- If complete: move the issue file to `issues/done/`.
- If incomplete: append a note to the issue file describing what was done and what's left.


## 7. Commit

Make one git commit. The message must include:

1. Key decisions made
2. Files changed
3. Blockers or notes for the next iteration

## Rules

- ONLY WORK ON A SINGLE TASK per invocation.
- Never touch HITL issues.
