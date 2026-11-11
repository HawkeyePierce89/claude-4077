---
name: ralphex
description: Use when the user wants the feature built end to end — "отправляй в ralphex", "делай фичу", "запускай план", "build it" — right after ticket-to-plan:create-ticket, or with a plan already produced by ticket-to-plan:plan. Runs plan, code and review without further prompts until the review findings are on screen.
---

# Ticket → plan → code → review

## Agent compatibility

These instructions support Claude Code and Codex. In Claude Code, use the
`ticket-to-plan:<name>` skill names below. In Codex, invoke the installed skill
as `$<name>` (for example, `$ralphex`); when following a cross-skill reference,
read that skill's `SKILL.md` and follow it. Do not assume Claude's plugin or
Skill tool exists in Codex. A user's explicit request for the corresponding
stage counts as invocation; automatic skill discovery alone is not approval.

In Codex, the revmux dependency is an installed `revmux` skill (invoked as
`$revmux`), not a Claude marketplace plugin. Read its instructions before
launching any stage; if absent, stop and ask for it to be installed using
revmux's Codex installation instructions. Do not invent its CLI workflow.
Use the harness scratchpad, or a session directory created with
`mktemp -d "${TMPDIR:-/tmp}/ticket-to-plan.XXXXXX"`; reuse the ticket's directory.
Monitor/TaskStop below are Claude facilities. In Codex, keep long commands in
persistent execution sessions, poll their returned IDs, inspect the logs,
and stop only monitors owned by this run. Follow the harness's progress-update
cadence even when the monitoring intervals below are longer. No background
session capability means reporting that limitation before launching the run.
The task model below configures ralphex's worker, not the host assistant;
using Codex does not remove ralphex's configured backend/authentication needs.


## Overview

Take the approved ticket (the `ticket-<slug>.md` from `ticket-to-plan:create-ticket`; invoking this skill IS the approval) and run three stages back to back: **A** get an accepted plan through `ticket-to-plan:plan` (or start from one the user already has), **B** run `ralphex --tasks-only` on it in the background, **C** run the project's gates and hand the branch to `revmux:revmux` for the review. Two human gates inside this skill: the invocation at the start and revmux's findings question at the end; the acceptance review (`ticket-to-plan:review`) and the merge are separate invocations. Any stage that fails stops the chain with a report; nothing is worked around. If no ticket exists in the scratchpad or the conversation, run `ticket-to-plan:create-ticket` first.

Preconditions, checked before anything is launched: `ralphex` and `revmux` on PATH and the revmux skill available (`revmux@revmux` plugin in Claude Code, installed `revmux` skill in Codex) (stop with install instructions otherwise). Read and follow the [shared worktree contract](../plan/references/worktree.md). Every stage runs in the task's recorded linked worktree on its existing feature branch; the main checkout is left untouched. Recover an existing plan's worktree before any command, even if this skill was invoked from the main checkout. Check for unrelated changes in the task worktree; inspect and retain owned partial changes when resuming a failed execution.

Notation: `$S`, `$WT`, `$BRANCH`, `$BASE` and `$BASE_REF` come from the worktree contract; `N` is a run number you increment on every launch (a resume is a new `N`), so no log or answers file is ever reused. Explicitly set each command's working directory to `$WT`, including gates, revmux and fixes.

## Stage A: plan

1. If the user pointed at an existing approved plan (a path, "запускай план", or the plan `ticket-to-plan:plan` just reported), locate its worktree and skip to stage B: a fresh execution needs an untouched plan in that worktree's `docs/plans/` with `- [ ]` items. Import a legacy plan only as described in the shared contract; never execute it in the main checkout. A resume uses the partially completed plan in the same worktree. Otherwise invoke `ticket-to-plan:plan`, which creates the worktree before planning, and follow it to its end (ralphex stopped, `n` sent on the Continue prompt, worktree/plan paths recorded); then go straight to stage B in that same worktree.

## Stage B: code

5. Verify `$WT` is still on `$BRANCH`. For a fresh feature or fix plan, commit only the approved plan if needed, following the shared contract; do not rely on ralphex to create a branch or auto-commit a plan when already on a feature branch. Launch with working directory `$WT`, in background, stdin from `/dev/null` (this mode asks nothing):
   ```bash
   ralphex --tasks-only --task-model=sonnet:high --wait 1h --no-color docs/plans/<file>.md </dev/null > "$S/tasks-N.log" 2>&1
   ```
   `sonnet:high` is the default for task execution, feature plans and fix plans alike: the tasks come from an accepted plan (or, for a fix plan, carry the file:line, the defect and the agreed fix), so the design decisions are already made, and task execution is the bulk of the pipeline's token bill. This default is not yet measured on this pipeline; the previous one, `opus:medium` (measured on Opus alone before Sonnet 5.5 existed: same quality as default effort, faster), is the fallback if a run's revmux round shows a quality drop. Pass through a different `--task-model` only if the user asked for one. `--wait 1h` sleeps and retries on a subscription-limit pattern instead of exiting.
6. Arm a Monitor on the log with a 60-minute timeout: `grep -E --line-buffered 'task execution completed successfully|task execution failed|max iterations|rate limit detected|panic:|^error:'`. `rate limit detected` is informational: ralphex is sleeping for the `--wait` duration, relay it in one line and keep the monitor. Every other match is terminal: TaskStop the monitor and go to step 7. On expiry with no event, read the log tail and `.ralphex/progress/progress-*.txt`, tell the user in one line which task iteration is running, re-arm. Status questions in between are answered the same way, never guessed.
7. Completion is `task execution completed successfully` in the log. Then verify, do not assume: the worktree identity still matches the record, `git branch --show-current` is `$BRANCH`, `git status --porcelain` is empty, the plan is in `$WT/docs/plans/completed/` with no `- [ ]` left, and `git log --oneline "$BASE_REF"..HEAD` shows the task commits. Update the archived plan path in the record. Report worktree, branch, commit count and elapsed time since the step 5 launch, then go straight to stage C. Any other exit (failed, max iterations, panic, error) stops the chain with the log tail and retained worktree path. When the user says to continue, in any words, inspect the partial state and relaunch step 5 in this same worktree: ralphex runs in place and resumes from the first unticked task. Never create another branch or remove the worktree on failure.

## Stage C: review

8. Run the project's own gates first (the test suite and every build target its CI runs) and report exact counts. Run them with the output filtered (`tail`, or `grep` for the summary and the failure lines), the full output going to `$S/gates-N.log`: a complete test log is thousands of lines the session never needs. Red gates stop the chain with the failing lines: a review of a broken branch is wasted.
9. Build the brief from the plan in `$WT/docs/plans/completed/` and the ticket, then invoke `revmux:revmux` from `$WT` with it as the argument, in the user's terms: review `$BRANCH` against `$BASE_REF`, profile `comprehensive`; goal = the plan's acceptance criteria as a "this is correct only if…" list; context = the absolute worktree, plan and ticket paths; exclusions = the ticket's out-of-scope items. Record the revmux task path in `$S/workflow.json`. `comprehensive` on the first round because no other code review exists in this pipeline; never write a round-local `profile.md`. The revmux skill owns round preparation, the run and the presentation of findings; it does **not** own the fixes here (step 11).
10. While a revmux round runs, arm a Monitor on its `events.jsonl` exactly as the revmux skill says, and a heartbeat with a 15-minute timeout: on expiry with no event, one line of status from the round's stderr log, re-arm. When revmux's findings question is on screen, append the project's gate results and replace its fix options with these two: *fix through ralphex, then round N+1* (recommended when anything gates) or *stop here*. Product decisions hiding in `open_questions` or in findings are asked in the same question, not decided.
11. **Fixes go through ralphex, never through this session.** From the findings the user accepted, write `$WT/docs/plans/<slug>-fix-NN.md` in ralphex's plan format, from the findings record alone (`findings.json` carries the file:line, the defect and the evidence; ralphex reads the files when it executes, so this session does not read them to write the plan): Overview naming the revmux round it answers; the project's `## Validation Commands`; one `### Task` per accepted finding carrying its file:line, the defect as revmux stated it and the agreed fix, with a checkbox to add or fix the test that would have caught it; a last task that runs the gates. Minors that ride along with a major go into that major's task. Then step 5's command on this plan, in the same `$WT` on `$BRANCH` (ralphex runs in place there), step 6's monitor, step 7's verification. Once ralphex has archived the plan, `git rm docs/plans/completed/<slug>-fix-NN.md` and commit `drop fix plan NN`: the merge squashes the branch, so the default branch never carries fix plans, only the original one. Then a new revmux round on the same task, profile `final`, scope = the cumulative diff against `$BASE_REF`, exclusions repeated; `comprehensive` only if the fixes spilled into structure or tests. Back to step 10; the chain stops when a round comes back with nothing gating, at five rounds, or when a gating finding repeats unchanged.
12. Once the branch is clean, report the worktree, branch, original completed plan and record paths. Keep the worktree: `ticket-to-plan:review` does final acceptance there, and `ticket-to-plan:merge` lands it and then removes it.

## Red flags (each one broke a real run)

| Mistake | Consequence |
|---|---|
| Launching on a ticket the user never saw, or on a plan they never approved | The approval gate is `create-ticket` (or `plan`) + the user's decision to invoke this skill — don't shortcut it |
| `y` on the Continue prompt | Runs ralphex's full pipeline with its own review phases on top of revmux |
| Launching from the main checkout or an arbitrary feature branch | Execution must run on the recorded task branch inside its linked worktree |
| Expecting ralphex to create the branch or commit the initial plan | This workflow already created the branch before planning; commit only the approved plan before execution |
| Editing code in the session while stage B runs | Two writers on one branch; ralphex commits whatever it finds |
| Reporting "done" from the completion line alone | Verify branch, clean tree, ticked plan in `completed/`, commits — a completion signal with `- [ ]` left is a known ralphex warning |
| Reviewing with red gates | The findings would describe a branch that does not build |
| Writing the review brief without the plan's acceptance criteria | revmux reviews the diff for bugs but not against what was asked |
| Writing feedback or brief files into the project repo | The user owns the repo; scratchpad only, revmux's `.revmux/tasks/` is the one exception and revmux owns it |
| Entering the revmux skill's own fix loop or editing files to fix a finding | Those fixes run on this session's model, the most expensive one in the pipeline; code is written by ralphex on `sonnet:high`, this session only writes the fix plan |
| Reading the changed files in the session to write a fix plan | The findings record already carries file:line, defect and evidence; every file read here is paid on the session's model and read again by ralphex |
| Dumping full gate output into the session | A test log is thousands of lines of context the session never needs; filter to the summary and the failures, keep the full log in the scratchpad |
| Leaving `<slug>-fix-NN.md` in `docs/plans/completed/` | Every round would add a plan file to the default branch; drop it right after ralphex archives it |
| Fix plan without the test that would have caught the defect | The next round finds the same class of bug one line away; revmux's own loop guidance measured two thirds of the next round's findings coming from unguarded fixes |
