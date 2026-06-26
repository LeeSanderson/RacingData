---
name: implementation
description: Fully implement a PRD's issues in dependency order — parallel worktrees, each merged to main as it passes, HITL issues left for a human. Use after write-a-prd + prd-to-issues, when the user wants to "implement the PRD", run the whole issue queue, or run /implementation.
---

# Implementation

Drive an entire PRD's backlog to completion. This is the dependency-aware, parallel successor to looping `work-on-next-issue`: it reads the issue DAG, runs every independent AFK issue at once in isolated worktrees, merges each green issue to `main` so its dependents can start, and stops cleanly at the HITL boundary with a precise hand-off.

It pairs with the `issue-implementer` agent (`.claude/agents/issue-implementer.md`), which does the per-issue work. The orchestration runs via the **Workflow** tool — invoking it from this skill is sanctioned.

> **Before running:** confirm `issue-implementer` appears in your available agent list. Agent files are loaded at session start, so if it was just created, start a fresh session first — otherwise `agentType: 'issue-implementer'` won't resolve.

## Invocation

- `/implementation` — target every issue in `issues/` not already in `issues/done/`.
- `/implementation issues/prd.md` — target only issues whose **Parent PRD** matches that file.
- `--max-parallel N` — override the default of 4 concurrent implementers.
- `--yes` — skip the plan confirmation (for unattended / `/loop` runs).

## 1. Build the plan (main loop — you have file access)

1. **Gather context.** Run `git log -n 5 --format="%H%n%ad%n%B---" --date=short` so you don't redo work that just landed.
2. **Collect issues.** List `issues/*.md`, excluding `issues/done/**`, `issues/prd.md`, and `issues/todo.md`. If a PRD path was given, keep only issues whose `Parent PRD` line matches it. The contents of `issues/done/` are the **completed set** — this is how re-runs resume.
3. **Parse each issue:**
   - `id` — the `NNN` prefix of the filename.
   - `title` — the first `#` heading.
   - `deps` — every `issues/NNN-….md` referenced under **Blocked by** ("None …" ⇒ no deps).
   - `type` — `HITL` if the file has a `**Type:** HITL` (or `Type: HITL`) marker, else `AFK`. Most existing issues have no marker; treat those as **AFK** and note the assumption in the plan.
4. **Validate.** Abort with a clear message if:
   - the primary working tree is **dirty**, or HEAD isn't on `main` — the serialized integrator merges here, so it must start clean on `main` (run `git status --porcelain` and `git branch --show-current`);
   - a `Blocked by` reference points to a file that doesn't exist and isn't in `done/`;
   - the dependency graph has a **cycle** (print the cycle).
5. **Resolve dependencies already satisfied.** A dep that is in `issues/done/` is satisfied — drop it from that issue's `deps`.
6. **Compute the frontier.**
   - Mark every `HITL` issue as **blocked-on-human**.
   - Propagate: any issue with a transitive dependency that is HITL or blocked-on-human is itself **blocked-on-human** (record which HITL ancestor blocks it).
   - The **runnable set** = the remaining AFK issues (not in `done/`, no HITL ancestor). Topologically sort it (dependencies before dependents).
7. **Edge case — nothing to run.** If the runnable set is empty, skip straight to the report in step 4: list what's done and the exact HITL action(s) the human must take, then stop. Do not launch the Workflow.

## 2. Show the plan and confirm

Print, grouped by topological level:

```
PLAN for <scope>  (<N> issues: <d> done, <r> to run, <s> blocked-on-human)
  L0: 001 add-staking            (AFK) run
  L1: 002 kelly-summary  -> 001  (AFK) run
  L2: 003 per-fold       -> 002  (AFK) run
  SKIP (needs human): 006 design-review (HITL); 007 -> 006
  ALREADY DONE: <ids in issues/done/>
  max-parallel: 4   integration target: main
  (issues with no Type marker assumed AFK: <ids>)
```

Wait for the user's go-ahead. Skip this prompt only if `--yes` was passed.

## 3. Run the Workflow

Compute the arguments, then call the **Workflow** tool with the script below and these `args`:

- `issues` — the runnable set in topological order, each `{ id, file, title, deps }` where `deps` is the intersection of its blockers with the runnable set (done/HITL stripped).
- `repoRoot` — the absolute repo path (e.g. `C:/Dev/Personal/RacingData`).
- `worktreeRoot` — `<repoRoot>` with `.worktrees` appended as a **sibling** (e.g. `C:/Dev/Personal/RacingData.worktrees`).
- `maxParallel` — 4, or the `--max-parallel` override.

Pass `args` as a real JSON object, not a string. The script returns an `outcome` map (`{ id: { status, reason? } }`) — keep it for the report.

```javascript
export const meta = {
  name: 'implement-prd',
  description: 'Implement AFK issues in dependency order across parallel worktrees, merging each green issue to main',
  phases: [
    { title: 'Implement' },
    { title: 'Verify' },
    { title: 'Integrate' },
  ],
}

const { issues, repoRoot, worktreeRoot, maxParallel = 4 } = args

const RESULT = {
  type: 'object',
  required: ['status', 'issueId', 'summary'],
  additionalProperties: false,
  properties: {
    status: { type: 'string', enum: ['success', 'failed'] },
    issueId: { type: 'string' },
    branch: { type: 'string' },
    summary: { type: 'string' },
    filesChanged: { type: 'array', items: { type: 'string' } },
    failureReason: { type: 'string' },
  },
}
const VERDICT = {
  type: 'object',
  required: ['allMet'],
  additionalProperties: false,
  properties: {
    allMet: { type: 'boolean' },
    unmet: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
}
const MERGE = {
  type: 'object',
  required: ['merged'],
  additionalProperties: false,
  properties: {
    merged: { type: 'boolean' },
    reason: { type: 'string' },
  },
}

// cap concurrent (heavy) implementer builds
function semaphore(n) {
  let active = 0
  const q = []
  const pump = () => { while (active < n && q.length) { active++; q.shift()() } }
  return fn => new Promise((resolve, reject) => {
    q.push(() => fn().then(resolve, reject).finally(() => { active--; pump() }))
    pump()
  })
}
const slot = semaphore(maxParallel)

// only one merge to main at a time
let mergeChain = Promise.resolve()
function serialized(fn) {
  const run = mergeChain.then(fn, fn)
  mergeChain = run.then(() => {}, () => {})
  return run
}

const meta_ = i => [
  `REPO_ROOT = ${repoRoot}`,
  `WORKTREE = ${worktreeRoot}/${i.id}`,
  `BRANCH = impl/${i.id}`,
  `ISSUE_FILE = ${i.file}`,
  `ISSUE_ID = ${i.id}`,
].join('\n')

const implementPrompt = i =>
  `MODE = implement\n${meta_(i)}\n\nYou are the issue-implementer. Implement issue ${i.id} (${i.title}) end-to-end per your agent procedure: set up the worktree (+.venv junction), TDD the change, run the AGENTS.md gate for the layer(s) you touch, move the issue into issues/done/, commit on your branch, and return the structured result. Do NOT merge to main.`

const repairPrompt = (i, v) =>
  `MODE = repair\n${meta_(i)}\nREPAIR_NOTES:\n${(v.unmet || []).map(u => '- ' + u).join('\n')}\n${v.notes ? 'Verifier notes: ' + v.notes : ''}\n\nThe worktree and branch impl/${i.id} already exist with your first attempt. cd into the worktree, close the unmet criteria above, re-run the gate, commit the fixes on the same branch, return the structured result. Do NOT recreate the worktree or re-move the issue file.`

const verifyPrompt = (i, impl) =>
  `Read-only acceptance check — do NOT modify any file. Issue ${i.id} was implemented on branch impl/${i.id}.\nIssue file (its 'Acceptance criteria' checklist is the contract): ${i.file}\nImplementer summary: ${impl.summary}\n\nInspect the real change:\n  git -C ${repoRoot} diff main...impl/${i.id}\nGo through EVERY acceptance criterion and adversarially hunt for one not genuinely met by the diff — including hard-to-test ones ("no diagnostic label", "byte-for-byte unchanged", "imports from X with no local math", "shows n/a not 0"). Return allMet=false with the specific failing criteria in 'unmet' if any fails; else allMet=true.`

const integratePrompt = i =>
  `Integrate issue ${i.id} into main. You run in ${repoRoot} (the primary checkout); merges are serialized so only you are merging now.\n` +
  `1. git -C ${repoRoot} switch main\n` +
  `2. git -C ${repoRoot} merge --no-ff -m "Merge issue ${i.id}: ${i.title}" impl/${i.id}\n` +
  `3. On conflict: resolve faithfully (you have both sides + full repo), git add -A, git commit --no-edit.\n` +
  `4. Run the AGENTS.md gate for the layer(s) this issue touched (C#: dotnet build && dotnet test; Python: .venv/Scripts/pre-commit run --all-files then .venv/Scripts/python -m pytest tests/).\n` +
  `5. GREEN -> git worktree remove --force ${worktreeRoot}/${i.id} (ignore errors); git branch -d impl/${i.id}; return merged=true.\n` +
  `6. RED or unresolvable conflict -> keep main green: git merge --abort if mid-conflict else git reset --hard HEAD~1; leave impl/${i.id} + its worktree for inspection; return merged=false with a specific reason.`

const outcome = {}
const done = {}

for (const issue of issues) {
  done[issue.id] = (async () => {
    await Promise.resolve()   // let every done[] entry register before reading deps
    const deps = await Promise.all((issue.deps || []).map(d => done[d]))
    if (deps.some(ok => ok === false)) {
      outcome[issue.id] = { status: 'skipped', reason: 'a dependency failed' }
      log(`SKIP ${issue.id}: a dependency failed`)
      return false
    }

    const impl = await slot(() => agent(implementPrompt(issue), {
      label: `impl:${issue.id}`, phase: 'Implement', agentType: 'issue-implementer', schema: RESULT,
    }))
    if (!impl || impl.status !== 'success') {
      outcome[issue.id] = { status: 'failed', reason: impl?.failureReason || 'implementer did not finish' }
      log(`FAIL ${issue.id}: ${outcome[issue.id].reason}`)
      return false
    }

    let verdict = await agent(verifyPrompt(issue, impl), {
      label: `verify:${issue.id}`, phase: 'Verify', schema: VERDICT,
    })
    if (verdict && verdict.allMet === false) {
      log(`REPAIR ${issue.id}: ${(verdict.unmet || []).length} unmet criteria`)
      const repaired = await slot(() => agent(repairPrompt(issue, verdict), {
        label: `repair:${issue.id}`, phase: 'Implement', agentType: 'issue-implementer', schema: RESULT,
      }))
      if (!repaired || repaired.status !== 'success') {
        outcome[issue.id] = { status: 'failed', reason: 'repair pass did not finish' }
        log(`FAIL ${issue.id}: repair pass did not finish`)
        return false
      }
      verdict = await agent(verifyPrompt(issue, repaired), {
        label: `reverify:${issue.id}`, phase: 'Verify', schema: VERDICT,
      })
    }
    if (!verdict || verdict.allMet !== true) {
      outcome[issue.id] = { status: 'failed', reason: 'acceptance criteria unmet after repair: ' + ((verdict?.unmet || []).join('; ') || 'unknown') }
      log(`FAIL ${issue.id}: ${outcome[issue.id].reason}`)
      return false
    }

    const merge = await serialized(() => agent(integratePrompt(issue), {
      label: `merge:${issue.id}`, phase: 'Integrate', schema: MERGE,
    }))
    if (!merge || merge.merged !== true) {
      outcome[issue.id] = { status: 'failed', reason: merge?.reason || 'merge/gate failed' }
      log(`FAIL ${issue.id}: ${outcome[issue.id].reason}`)
      return false
    }
    outcome[issue.id] = { status: 'done' }
    log(`DONE ${issue.id} merged to main`)
    return true
  })()
}

await Promise.all(Object.values(done))
return outcome
```

### How the script behaves (so you can read its result)

- Each issue waits on **its own** dependencies' promises, so an issue starts the instant its blockers have merged — independent issues run in parallel up to `maxParallel`.
- Per issue: **implement** (issue-implementer in its worktree) → **verify** (read-only adversarial AC check) → **one repair pass** if any AC is unmet → re-verify → **integrate** (serialized merge to main + layer-scoped gate).
- `main` only advances on a green gate, so it stays green by construction. A failed/red/unresolvable issue is **isolated**: not merged, not marked done, and its transitive dependents resolve to `skipped` — independent work keeps running.
- The returned `outcome` map tells you each issue's fate: `done`, `failed` (with `reason`), or `skipped` (dependency failed).

## 4. Finalise

1. **Final full sweep.** On `main`, run the complete gate as the last safety net:
   ```bash
   dotnet build && dotnet test
   .venv/Scripts/pre-commit run --all-files
   .venv/Scripts/python -m pytest tests/
   ```
   Report the result; if it's red, say so loudly — something merged green individually but interacts badly.
2. **Report.** Print, leading with any human action:
   ```
   === /implementation report ===
   NEXT HUMAN ACTION: <HITL issue(s) to do, or "none — all targeted issues done">
   DONE (merged to main): <ids>
   FAILED / SKIPPED: <id — reason> ...
   BLOCKED ON HUMAN: <HITL ids + their blocked dependents>
   final full sweep: GREEN | RED (<detail>)
   ```
3. **Clean up stray state** from any failed issue only if the user asks — leftover `impl/<id>` branches and `…​.worktrees/<id>` dirs are deliberately kept for inspection.
4. **Suggest clean-up.** If — and only if — every targeted issue is now in `issues/done/` with nothing failed/skipped/blocked, suggest running `/clean-up-prd`. Never run it automatically; it deletes the PRD and issues and needs explicit approval.
5. **Resuming.** After the user handles the HITL work (and moves/marks those issues done), re-running `/implementation` picks up automatically: `issues/done/` is the state, so completed issues are skipped and the now-unblocked frontier runs.

## Rules

- Never implement HITL issues, and never implement an issue with a HITL ancestor. The run ends at that boundary with a hand-off.
- The orchestrator (this skill) never edits source — it parses, plans, runs the Workflow, runs the final sweep, and reports. All code changes happen inside worktrees via `issue-implementer`; all merges happen in the serialized integrator.
- One Workflow run per invocation.
