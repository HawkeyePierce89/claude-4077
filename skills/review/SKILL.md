---
name: review
description: Use when the user asks for the final acceptance of an implemented feature — "review the implementation", "проверь реализацию", "приёмка", "check the branch" — on a branch produced by ticket-to-plan:ralphex, after its revmux review came back clean.
---

# Acceptance review of an executed plan

## Overview

revmux already reviewed the diff for defects and its loop fixed what gated; this is the independent final acceptance before merge, done by hand in this session. Review against the **plan** in `docs/plans/completed/` (ralphex moves it there when every task is done), which carries the requirements and acceptance criteria, and against the **revmux record** under `.revmux/tasks/<task>/`, which says what was already found. The deliverable is a report — findings go to the user, whose pipeline applies them.

## Steps

1. Locate the plan (`docs/plans/completed/`, newest matching the branch name), the diff base (the repo's default branch), and the revmux task for this branch (`revmux config | jq '.paths.tasks'`, match on `branch`). Read the last round's `findings.json` and `report.md`: the gating findings there must be fixed on the branch, and its `open_questions` are decisions the user still owes.
2. **Run the project's own gates first**: the test suite and every build target the project's CI runs. Report exact counts and results, not "seems fine".
3. Read **every changed file in full**, not just the diff hunks — new code is judged in the context it lives in.
4. Verify the load-bearing logic by hand, looking for what a diff review misses: the plan's semantics versus the implementation (boundaries such as "inclusive for the whole day", units, time zones, sorting guarantees), interactions with untouched code, and tests that would pass with the bug present (substring assertions, fixtures that never leave the happy path). **Live-verify** claims where possible — run the real binary or reproduce the mechanism outside the app rather than trusting comments and tests alone.
5. Check the result against the plan's acceptance criteria and the repo's conventions doc, item by item, and confirm each gating revmux finding is actually fixed rather than worked around.
6. Report: verdict first; findings prioritized (critical / important / minor) with a concrete fix per finding, each marked new or "revmux round N, unresolved"; what was verified and how; and an explicit **"NOT verified"** list (typically manual/visual checks) — offer to run the app when the change is visual. Do not fix anything unprompted; when the verdict is clean, `ticket-to-plan:merge` is the next step.

## Red flags

| Mistake | Consequence |
|---|---|
| Reviewing only the diff hunks | Misses interactions with surrounding code — the bugs that survive a diff review |
| Verdict without running the gates | "Tests pass" claimed from reading code is not evidence — run them |
| Repeating revmux's findings as new | Wastes the user's attention; read the round record first and report only what is unresolved or new |
| Trusting revmux's clean round as acceptance | It reviewed the diff for defects, not the plan's semantics; four models in one experiment agreed on a wrong date boundary and only the acceptance review caught it |
| Fixing findings unprompted | The user owns the branch and the fix pipeline; report, don't patch |
| Skipping the "NOT verified" list | A review that hides its blind spots overstates its confidence |
