---
name: review
description: Use when the user asks for the final acceptance of an implemented feature — "review the implementation", "проверь реализацию", "приёмка", "check the branch" — on a branch produced by ticket-to-plan:ralphex, after its revmux review came back clean.
---

# Acceptance review of an executed plan

## Agent compatibility

These instructions support Claude Code and Codex. In Claude Code, use the
`ticket-to-plan:<name>` skill names below. In Codex, invoke the installed skill
as `$<name>` (for example, `$ralphex`); when following a cross-skill reference,
read that skill's `SKILL.md` and follow it. Do not assume Claude's plugin or
Skill tool exists in Codex. A user's explicit request for the corresponding
stage counts as invocation; automatic skill discovery alone is not approval.

If the harness has no LSP tool, locate definitions, callers and implementors
with `rg`, then read the relevant ranges. Report any limits of this fallback.
Use the harness scratchpad, or a session directory created with
`mktemp -d "${TMPDIR:-/tmp}/ticket-to-plan.XXXXXX"`, for gate logs.


## Overview

revmux already reviewed the diff for defects and its loop fixed what gated; this is the independent final acceptance before merge, done by hand in this session. Review against the **plan** in `docs/plans/completed/` (ralphex moves it there when every task is done), which carries the requirements and acceptance criteria, and against the **revmux record** under `.revmux/tasks/<task>/`, which says what was already found. The deliverable is a report — findings go to the user, whose pipeline applies them.

## Steps

1. Read and follow the [shared worktree contract](../plan/references/worktree.md). Recover this task's record and verify its linked worktree and branch, even when invoked from the main checkout. Set every command's working directory to `$WT`. Locate the exact completed plan and revmux task from the record; if the latter is missing, run `revmux config | jq '.paths.tasks'` in `$WT` and match the task's branch and plan, not its recency. Use the recorded default-branch ref `$BASE_REF` as the diff base. Read the last round's `findings.json` and `report.md`: the gating findings there must be fixed on the branch, and its `open_questions` are decisions the user still owes. Unexplained changes in the task worktree stop acceptance; do not review another checkout instead.
2. **Run the project's own gates first**: the test suite and every build target the project's CI runs. Run them with the output filtered (`tail`, or `grep` for the summary and the failure lines), the full output going to the scratchpad. Report exact counts and results, not "seems fine".
3. Read **every changed file in full**, not just the diff hunks — new code is judged in the context it lives in. Under a big-file read guard (a hook that denies untargeted reads over a line threshold), read a long changed file in consecutive offset/limit chunks rather than disabling the guard: the tokens are the same, and the guard keeps protecting the untouched files of step 4.
4. Verify the load-bearing logic by hand, looking for what a diff review misses: the plan's semantics versus the implementation (boundaries such as "inclusive for the whole day", units, time zones, sorting guarantees), interactions with untouched code, and tests that would pass with the bug present (substring assertions, fixtures that never leave the happy path). For the untouched code, find the callers and implementors of what changed through the LSP tool (`findReferences`, `incomingCalls`, `goToImplementation`) and read those spots with an offset and limit; the full-read rule of step 3 is for the changed files. **Live-verify** claims where possible — run the real binary or reproduce the mechanism outside the app rather than trusting comments and tests alone.
5. Check the result against the plan's acceptance criteria and the repo's conventions doc, item by item, and confirm each gating revmux finding is actually fixed rather than worked around.
6. Report: verdict first; findings prioritized (critical / important / minor) with a concrete fix per finding, each marked new or "revmux round N, unresolved"; what was verified and how; and an explicit **"NOT verified"** list (typically manual/visual checks) — offer to run the app when the change is visual. Include the worktree, branch, plan and record paths. Record the reviewed HEAD and verdict for the merge handoff. Do not fix anything unprompted or remove the worktree; when the verdict is clean, `ticket-to-plan:merge` is the next step in this same worktree.

## Red flags

| Mistake | Consequence |
|---|---|
| Reviewing only the diff hunks | Misses interactions with surrounding code — the bugs that survive a diff review |
| Reviewing whichever checkout the invocation started in | Acceptance must read and test the recorded task worktree; the main checkout does not contain this implementation |
| Verdict without running the gates | "Tests pass" claimed from reading code is not evidence — run them |
| Repeating revmux's findings as new | Wastes the user's attention; read the round record first and report only what is unresolved or new |
| Trusting revmux's clean round as acceptance | It reviewed the diff for defects, not the plan's semantics; four models in one experiment agreed on a wrong date boundary and only the acceptance review caught it |
| Fixing findings unprompted | The user owns the branch and the fix pipeline; report, don't patch |
| Skipping the "NOT verified" list | A review that hides its blind spots overstates its confidence |
| Reading untouched files in full to find the callers of a change | LSP references answer in a few lines; a full read of every caller's file costs more than the rest of the review. Changed files are still read in full |
