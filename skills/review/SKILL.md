---
name: review
description: Use when the user asks to review the implementation of an executed ralphex plan — "review the implementation", "проверь реализацию", "check the branch" — on a branch produced by running a plan from docs/plans/.
---

# Acceptance review of an executed plan

## Overview

ralphex's own loop already ran its internal reviews; this is the independent final gate before merge. Review against the **plan** (after execution ralphex moves it to `docs/plans/completed/`), which carries the requirements and acceptance criteria. The deliverable is a report — findings go to the user, whose pipeline applies them.

## Steps

1. Locate the plan (`docs/plans/completed/`, newest matching the branch name) and the diff base (the repo's default branch).
2. **Run the project's own gates first**: the test suite and every build target the project's CI runs. Report exact counts and results, not "seems fine".
3. Read **every changed file in full**, not just the diff hunks — new code is judged in the context it lives in.
4. Verify the load-bearing logic by hand: work edge cases through the actual code (boundaries, concurrency, off-by-one), and **live-verify** claims where possible — run the real underlying commands or reproduce the mechanism outside the app rather than trusting comments and tests alone.
5. Check the result against the plan's acceptance criteria and the repo's conventions doc, item by item.
6. Report: verdict first; findings prioritized (critical / important / minor) with a concrete fix per finding; what was verified and how; and an explicit **"NOT verified"** list (typically manual/visual checks) — offer to run the app when the change is visual. Do not fix anything unprompted.

## Red flags

| Mistake | Consequence |
|---|---|
| Reviewing only the diff hunks | Misses interactions with surrounding code — the bugs that survive the author's own review |
| Verdict without running the gates | "Tests pass" claimed from reading code is not evidence — run them |
| Fixing findings unprompted | The user owns the branch and the fix pipeline; report, don't patch |
| Skipping the "NOT verified" list | A review that hides its blind spots overstates its confidence |
