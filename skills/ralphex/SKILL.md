---
name: ralphex
description: Use when the user wants the feature built end to end — "отправляй в ralphex", "делай фичу", "запускай план", "build it" — right after ticket-to-plan:create-ticket, or with a plan already produced by ticket-to-plan:plan. Runs plan, code and review without further prompts until the review findings are on screen.
---

# Ticket → plan → code → review

## Overview

Take the approved ticket (the `ticket-<slug>.md` from `ticket-to-plan:create-ticket`; invoking this skill IS the approval) and run three stages back to back: **A** get an accepted plan through `ticket-to-plan:plan` (or start from one the user already has), **B** run `ralphex --tasks-only` on it in the background, **C** run the project's gates and hand the branch to `revmux:revmux` for the review. Two human gates inside this skill: the invocation at the start and revmux's findings question at the end; the acceptance review (`ticket-to-plan:review`) and the merge are separate invocations. Any stage that fails stops the chain with a report; nothing is worked around. If no ticket exists in the scratchpad or the conversation, run `ticket-to-plan:create-ticket` first.

Preconditions, checked before anything is launched: `ralphex` and `revmux` on PATH and the `revmux@revmux` plugin installed (stop with install instructions otherwise); the checkout on the repo's default branch with a clean tree apart from an uncommitted plan file (otherwise stop and say so — never checkout, stash or commit on the user's behalf). This applies to a fresh start; a resume after a failure runs on the plan's branch, see step 7.

Notation: `$S` is the session scratchpad directory; `N` is a run number you increment on every launch (a resume is a new `N`), so no log or answers file is ever reused.

## Stage A: plan

1. If the user pointed at an existing plan (a path, "запускай план", or the plan `ticket-to-plan:plan` just reported), skip to stage B with it: it must be an untouched plan in `docs/plans/` with `- [ ]` items, either uncommitted on the default branch or already committed. Otherwise invoke `ticket-to-plan:plan` and follow it to its end (ralphex stopped, `n` sent on the Continue prompt, plan path reported); its preconditions are this stage's preconditions. Then go straight to stage B.

## Stage B: code

5. The plan file is uncommitted on the default branch; ralphex creates the branch from the plan name and commits the plan itself. Launch from the repo root, in background, stdin from `/dev/null` (this mode asks nothing):
   ```bash
   ralphex --tasks-only --task-model=opus:medium --wait 1h --no-color docs/plans/<file>.md </dev/null > "$S/tasks-N.log" 2>&1
   ```
   `opus:medium` is the default for task execution (measured: same quality as default effort, faster); pass through a different `--task-model` only if the user asked for one. `--wait 1h` sleeps and retries on a subscription-limit pattern instead of exiting.
6. Arm a Monitor on the log with a 60-minute timeout: `grep -E --line-buffered 'task execution completed successfully|task execution failed|max iterations|rate limit detected|panic:|^error:'`. `rate limit detected` is informational: ralphex is sleeping for the `--wait` duration, relay it in one line and keep the monitor. Every other match is terminal: TaskStop the monitor and go to step 7. On expiry with no event, read the log tail and `.ralphex/progress/progress-*.txt`, tell the user in one line which task iteration is running, re-arm. Status questions in between are answered the same way, never guessed.
7. Completion is `task execution completed successfully` in the log. Then verify, do not assume: `git branch --show-current` is the plan's branch, `git status --porcelain` is empty, the plan is in `docs/plans/completed/` with no `- [ ]` left, `git log --oneline <default>..HEAD` shows the task commits. Report branch, commit count and elapsed time since the step 5 launch, then go straight to stage C. Any other exit (failed, max iterations, panic, error) stops the chain with the log tail. When the user says to continue, in any words, relaunch step 5 from the plan's branch (that is the intended exception to the default-branch precondition): ralphex runs in place there and resumes from the first unticked task.

## Stage C: review

8. Run the project's own gates first (the test suite and every build target its CI runs) and report exact counts. Red gates stop the chain with the output: a review of a broken branch is wasted.
9. Build the brief from the plan in `docs/plans/completed/` and the ticket, then invoke `revmux:revmux` with it as the argument, in the user's terms: review this branch against `<default>`, profile `comprehensive`; goal = the plan's acceptance criteria as a "this is correct only if…" list; context = the plan path and the ticket path; exclusions = the ticket's out-of-scope items. `comprehensive` on the first round because no other code review exists in this pipeline; never write a round-local `profile.md`. The revmux skill owns round preparation, the run and the presentation of findings; it does **not** own the fixes here (step 11).
10. While a revmux round runs, arm a Monitor on its `events.jsonl` exactly as the revmux skill says, and a heartbeat with a 15-minute timeout: on expiry with no event, one line of status from the round's stderr log, re-arm. When revmux's findings question is on screen, append the project's gate results and replace its fix options with these two: *fix through ralphex, then round N+1* (recommended when anything gates) or *stop here*. Product decisions hiding in `open_questions` or in findings are asked in the same question, not decided.
11. **Fixes go through ralphex, never through this session.** From the findings the user accepted, write `docs/plans/<slug>-fix-NN.md` in ralphex's plan format: Overview naming the revmux round it answers; the project's `## Validation Commands`; one `### Task` per accepted finding carrying its file:line, the defect as revmux stated it and the agreed fix, with a checkbox to add or fix the test that would have caught it; a last task that runs the gates. Minors that ride along with a major go into that major's task. Then step 5's command on this plan, on the feature branch (ralphex runs in place there), step 6's monitor, step 7's verification. Once ralphex has archived the plan, `git rm docs/plans/completed/<slug>-fix-NN.md` and commit `drop fix plan NN`: the merge squashes the branch, so the default branch never carries fix plans, only the original one. Then a new revmux round on the same task, profile `final`, scope = the cumulative diff against `<default>`, exclusions repeated; `comprehensive` only if the fixes spilled into structure or tests. Back to step 10; the chain stops when a round comes back with nothing gating, at five rounds, or when a gating finding repeats unchanged.
12. Once the branch is clean, `ticket-to-plan:review` is the final acceptance and `ticket-to-plan:merge` lands it.

## Red flags (each one broke a real run)

| Mistake | Consequence |
|---|---|
| Launching on a ticket the user never saw, or on a plan they never approved | The approval gate is `create-ticket` (or `plan`) + the user's decision to invoke this skill — don't shortcut it |
| `y` on the Continue prompt | Runs ralphex's full pipeline with its own review phases on top of revmux |
| Launching stage B from a feature branch | ralphex only creates the branch when on the default branch; on any other branch it silently runs the plan there |
| Editing code in the session while stage B runs | Two writers on one branch; ralphex commits whatever it finds |
| Reporting "done" from the completion line alone | Verify branch, clean tree, ticked plan in `completed/`, commits — a completion signal with `- [ ]` left is a known ralphex warning |
| Reviewing with red gates | The findings would describe a branch that does not build |
| Writing the review brief without the plan's acceptance criteria | revmux reviews the diff for bugs but not against what was asked |
| Writing feedback or brief files into the project repo | The user owns the repo; scratchpad only, revmux's `.revmux/tasks/` is the one exception and revmux owns it |
| Entering the revmux skill's own fix loop or editing files to fix a finding | Those fixes run on this session's model, the most expensive one in the pipeline; code is written by ralphex on `opus:medium`, this session only writes the fix plan |
| Leaving `<slug>-fix-NN.md` in `docs/plans/completed/` | Every round would add a plan file to the default branch; drop it right after ralphex archives it |
| Fix plan without the test that would have caught the defect | The next round finds the same class of bug one line away; revmux's own loop guidance measured two thirds of the next round's findings coming from unguarded fixes |
