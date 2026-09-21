---
name: ralphex
description: Use when the user approves the composed ticket and wants the feature built — "отправляй в ralphex", "send it to ralphex", "запускай", or an explicit invocation right after ticket-to-plan:create-ticket. Runs the whole cycle from ticket to reviewed branch without further prompts until the review findings are on screen.
---

# Ticket → plan → code → review

## Overview

Take the approved ticket (the `ticket-<slug>.md` from `ticket-to-plan:create-ticket`; invoking this skill IS the approval) and run three stages back to back: **A** drive `ralphex --plan` to an accepted plan, **B** run `ralphex --tasks-only` on it in the background, **C** run the project's gates and hand the branch to `revmux:revmux` for the review. Two human gates inside this skill: the invocation at the start and revmux's findings question at the end; the acceptance review (`ticket-to-plan:review`) and the merge are separate invocations. Any stage that fails stops the chain with a report; nothing is worked around. If no ticket exists in the scratchpad or the conversation, run `ticket-to-plan:create-ticket` first.

Preconditions, checked before anything is launched: `ralphex` and `revmux` on PATH and the `revmux@revmux` plugin installed (stop with install instructions otherwise); the checkout on the repo's default branch with a clean tree (otherwise stop and say so — never checkout, stash or commit on the user's behalf). This applies to a fresh start; a resume after a failure runs on the plan's branch, see step 7.

Notation: `$S` is the session scratchpad directory; `N` is a run number you increment on every launch (a resume is a new `N`), so no log or answers file is ever reused.

## Stage A: plan

1. Launch from the project repo root, in background:
   ```bash
   : > "$S/answers-N.txt"   # ALWAYS a fresh file — see red flags
   tail -n +1 -f "$S/answers-N.txt" | ralphex --plan "$(cat "$S/ticket-<slug>.md")" --no-color > "$S/plan-N.log" 2>&1
   ```
   Arm a Monitor on the log: `grep -E --line-buffered '^\s+[0-9]+\) |QUESTION|docs/plans/|panic:|plan creation|rejected|failed'`. Interactive prompts (`Enter number…`, `Continue with plan…`) have **no trailing newline** and never trigger the monitor — detect them by the option lines above them, or `tail -c` the log directly.
2. Answer prompts by appending ONE line to the answers file per prompt. Clarifying questions → answer from the ticket; product-level questions → stop and ask the user.
3. Review each draft honestly against the ticket and the codebase (verify claims in the code — don't wave anything through). Remarks → send `2`, then the feedback as one line (a pipe has no 1024-byte tty limit). On the next iteration, **diff the two drafts** to verify the fix landed with no unrelated drift. Accept (`1`) only when clean; a genuinely clean first draft may be accepted — do not invent cosmetic revisions.
4. After accept: wait for `created docs/plans/<file>.md` in the log, then check the log tail for `Continue with plan implementation? [y/N]` and append `n` as one line to the answers file. NEVER `y`: `y` runs ralphex's full mode with its own review phases, which this pipeline replaces with revmux. Kill the `tail` keeper, confirm `pgrep -x ralphex` is empty, TaskStop the monitor. Report the plan path and the review iterations in one short paragraph, then go straight to stage B.

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
9. Build the brief from the plan in `docs/plans/completed/` and the ticket, then invoke `revmux:revmux` with it as the argument, in the user's terms: review this branch against `<default>`, profile `comprehensive`; goal = the plan's acceptance criteria as a "this is correct only if…" list; context = the plan path and the ticket path; exclusions = the ticket's out-of-scope items. `comprehensive` on the first round because no other code review exists in this pipeline; never write a round-local `profile.md`. The revmux skill owns everything from there: round preparation, the run, presenting findings, the fix/loop/stop question, later rounds on `final`.
10. While a revmux round runs, arm a Monitor on its `events.jsonl` exactly as the revmux skill says, and a heartbeat with a 15-minute timeout: on expiry with no event, one line of status from the round's stderr log, re-arm. When revmux's findings question is on screen, append the project's gate results. The user's answer to that question ends the chain; once the branch is clean, `ticket-to-plan:review` is the final acceptance and `ticket-to-plan:merge` lands it.

## Red flags (each one broke a real run)

| Mistake | Consequence |
|---|---|
| Launching on a ticket the user never saw | The approval gate is `create-ticket` + the user's decision to invoke this skill — don't shortcut it |
| Reusing an old answers file | `tail -n +1` replays previous answers — the plan self-accepts instantly |
| Queueing two answers at once | ralphex's `AskYesNo` creates a *fresh* bufio reader; a queued line sits in the old reader's buffer and is lost |
| `y` on the Continue prompt | Runs ralphex's full pipeline with its own review phases on top of revmux |
| Trusting the monitor for prompt detection | Newline-less prompt lines never fire it; the run stalls silently — check the log tail |
| Launching stage B from a feature branch | ralphex only creates the branch when on the default branch; on any other branch it silently runs the plan there |
| Editing code in the session while stage B runs | Two writers on one branch; ralphex commits whatever it finds |
| Reporting "done" from the completion line alone | Verify branch, clean tree, ticked plan in `completed/`, commits — a completion signal with `- [ ]` left is a known ralphex warning |
| Reviewing with red gates | The findings would describe a branch that does not build |
| Writing the review brief without the plan's acceptance criteria | revmux reviews the diff for bugs but not against what was asked |
| Writing feedback or brief files into the project repo | The user owns the repo; scratchpad only, revmux's `.revmux/tasks/` is the one exception and revmux owns it |
| Fixing findings yourself outside revmux's loop | The user decides on findings; the loop commits without pushing and re-reviews, ad-hoc fixes do neither |
