---
name: plan
description: Use when the user wants ralphex to produce the implementation plan and nothing more — "составь план", "только план", "сделай план в ralphex", "plan only" — right after ticket-to-plan:create-ticket, when running the plan is a separate decision.
---

# Drive ralphex to an accepted plan

## Overview

Take the approved ticket (the `ticket-<slug>.md` from `ticket-to-plan:create-ticket`; invoking this skill IS the approval) and drive `ralphex --plan` to an accepted plan on disk, without executing it. You review the **plan drafts**; ralphex's tty prompts are driven through a pipe (no tty limits apply there). If no ticket exists in the scratchpad or the conversation, run `ticket-to-plan:create-ticket` first — never launch ralphex on an unreviewed ad-hoc description.

Preconditions: `ralphex` on PATH; the checkout on the repo's default branch with a clean tree (otherwise stop and say so — never checkout, stash or commit on the user's behalf). Notation: `$S` is the session scratchpad directory; `N` is a run number you increment on every launch, so no log or answers file is ever reused.

## Steps

1. Launch from the project repo root, in background:
   ```bash
   : > "$S/answers-N.txt"   # ALWAYS a fresh file — see red flags
   tail -n +1 -f "$S/answers-N.txt" | ralphex --plan "$(cat "$S/ticket-<slug>.md")" --no-color > "$S/plan-N.log" 2>&1
   ```
   Arm a Monitor on the log: `grep -E --line-buffered '^\s+[0-9]+\) |QUESTION|docs/plans/|panic:|plan creation|rejected|failed'`. Interactive prompts (`Enter number…`, `Continue with plan…`) have **no trailing newline** and never trigger the monitor — detect them by the option lines above them, or `tail -c` the log directly.
2. Answer prompts by appending ONE line to the answers file per prompt. Clarifying questions → answer from the ticket; product-level questions → stop and ask the user.
3. Review each draft honestly against the ticket and the codebase (verify claims in the code — don't wave anything through). Remarks → send `2`, then the feedback as one line (a pipe has no 1024-byte tty limit). On the next iteration, **diff the two drafts** to verify the fix landed with no unrelated drift. Accept (`1`) only when clean; a genuinely clean first draft may be accepted — do not invent cosmetic revisions.
4. After accept: wait for `created docs/plans/<file>.md` in the log, then check the log tail for `Continue with plan implementation? [y/N]` and append `n` as one line to the answers file. NEVER `y`: `y` runs ralphex's full mode with its own review phases, which this pipeline replaces with revmux. Kill the `tail` keeper, confirm `pgrep -x ralphex` is empty, TaskStop the monitor. Report the plan path and the review iterations in one short paragraph. The plan is uncommitted on the default branch, which is what `ticket-to-plan:ralphex` expects when it starts from an existing plan; that skill runs it, the review and the fix cycle when the user asks, or they run `ralphex --tasks-only <plan>` themselves.

## Red flags (each one broke a real run)

| Mistake | Consequence |
|---|---|
| Launching on a ticket the user never saw | The approval gate is `create-ticket` + the user's decision to invoke this skill — don't shortcut it |
| Reusing an old answers file | `tail -n +1` replays previous answers — the plan self-accepts instantly |
| Queueing two answers at once | ralphex's `AskYesNo` creates a *fresh* bufio reader; a queued line sits in the old reader's buffer and is lost |
| `y` on the Continue prompt | Runs ralphex's full pipeline with its own review phases; execution is a separate decision and, in this pipeline, a separate skill |
| Trusting the monitor for prompt detection | Newline-less prompt lines never fire it; the run stalls silently — check the log tail |
| Writing feedback files into the project repo | The user owns the repo; scratchpad only |
