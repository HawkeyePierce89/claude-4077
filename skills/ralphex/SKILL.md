---
name: ralphex
description: Use when the user approves the composed ticket and wants it sent to ralphex for plan creation — "отправляй в ralphex", "send it to ralphex", or an explicit invocation right after ticket-to-plan:create-ticket. Drives ralphex's interactive plan mode programmatically through the Revise loop and stops before execution.
---

# Drive ralphex to an accepted plan

## Overview

Take the approved ticket (the `ticket-<slug>.md` produced by `ticket-to-plan:create-ticket` — the user's invocation of this skill is the approval) and drive `ralphex --plan` to an accepted plan on disk, without executing it. You review the **plan drafts**; ralphex's tty prompts are driven through a pipe (no tty limits apply there). If no ticket exists in the scratchpad or the conversation, run `ticket-to-plan:create-ticket` first — never launch ralphex on an unreviewed ad-hoc description.

## Steps

1. Launch from the project repo root, in background:
   ```bash
   : > "$S/answers-N.txt"   # ALWAYS a fresh file — see red flags
   tail -n +1 -f "$S/answers-N.txt" | ralphex --plan "$(cat "$S/ticket-<slug>.md")" --no-color > "$S/run-N.log" 2>&1
   ```
   Arm a Monitor on the log: `grep -E --line-buffered '^\s+[0-9]+\) |QUESTION|docs/plans/|panic:|plan creation|rejected|failed'`. Interactive prompts (`Enter number…`, `Continue with plan…`) have **no trailing newline** and never trigger the monitor — detect them by the option lines above them, or `tail -c` the log directly.
2. Answer prompts by appending ONE line to the answers file per prompt. Clarifying questions → answer from the ticket; product-level questions → stop and ask the user.
3. Review each draft honestly against the ticket and the codebase (verify claims in the code — don't wave anything through). Remarks → send `2`, then the feedback as one line (a pipe has no 1024-byte tty limit). On the next iteration, **diff the two drafts** to verify the fix landed with no unrelated drift. Accept (`1`) only when clean; a genuinely clean first draft may be accepted — do not invent cosmetic revisions.
4. After accept: wait for `created docs/plans/<file>.md` in the log, then check the log tail for `Continue with plan implementation? [y/N]` and send `n`. NEVER `y` — execution is the user's call unless they explicitly said otherwise.
5. Cleanup: kill the `tail` keeper, confirm `pgrep -x ralphex` is empty, TaskStop the monitor. Report the plan path and a summary of the review iterations. The user runs `ralphex <plan>` themselves; afterwards `ticket-to-plan:review` runs the acceptance review.

## Red flags (each one broke a real run)

| Mistake | Consequence |
|---|---|
| Launching on a ticket the user never saw | The approval gate is `create-ticket` + the user's decision to invoke this skill — don't shortcut it |
| Reusing an old answers file | `tail -n +1` replays previous answers — the plan self-accepts instantly |
| Queueing two answers at once | ralphex's `AskYesNo` creates a *fresh* bufio reader; a queued line sits in the old reader's buffer and is lost |
| Forgetting `n` on the Continue prompt | ralphex hangs waiting (or worse, runs the implementation); the process lingers |
| Writing feedback files into the project repo unprompted | The user owns the repo; scratchpad only |
| Trusting the monitor for prompt detection | Newline-less prompt lines never fire it; the run stalls silently — check the log tail |
