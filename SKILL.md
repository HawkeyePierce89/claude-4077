---
name: ticket-to-plan
description: Use when the user asks to turn a feature request into a ralphex implementation plan — "run this through ralphex", "make a ticket and send it to ralphex", "ticket → plan cycle". Covers composing the ticket, the user's ticket-review gate, driving ralphex's interactive plan mode programmatically, the Revise loop, and stopping before execution.
---

# Ticket → ralphex plan cycle

## Overview

Turn a feature request into an accepted ralphex plan on disk, without executing it. The user reviews the **ticket**; you review the **plan drafts**. ralphex's tty prompts are driven through a pipe (no tty limits apply there).

## Steps

1. **Compose the ticket** as a tech-lead prose ticket, in **English**: goal → requirements → acceptance criteria → out of scope → conventions. The feature comes from the invocation argument if one was given, otherwise from the **preceding conversation** (the brainstorm/design discussion) — invoking with no argument after a design chat is the normal flow. If neither gives enough to write a defensible ticket, ask before writing. No file-by-file steps and no code snippets — the plan agent knows the codebase; the ticket states WHAT and the constraints, not the mechanical HOW. Fold every already-known review remark into it. Add the line: *"Language: the plan file itself must be written in English."* Save it to the scratchpad, NOT the repo.
2. **User gate — HARD STOP.** Show the ticket to the user and wait for explicit approval before launching ralphex. Fold their edits in.
3. **Launch** from the project repo root, in background:
   ```bash
   : > "$S/answers-N.txt"   # ALWAYS a fresh file — see red flags
   tail -n +1 -f "$S/answers-N.txt" | ralphex --plan "$(cat "$S/ticket.md")" --no-color > "$S/run-N.log" 2>&1
   ```
   Arm a Monitor on the log: `grep -E --line-buffered '^\s+[0-9]+\) |QUESTION|docs/plans/|panic:|plan creation|rejected|failed'`. Interactive prompts (`Enter number…`, `Continue with plan…`) have **no trailing newline** and never trigger the monitor — detect them by the option lines above them, or `tail -c` the log directly.
4. **Answer prompts** by appending ONE line to the answers file per prompt. Clarifying questions → answer from the ticket; product-level questions → stop and ask the user.
5. **Review each draft** honestly against the ticket and the codebase (verify claims in the code — don't wave anything through). Remarks → send `2`, then the feedback as one line (a pipe has no 1024-byte tty limit). On the next iteration, **diff the two drafts** to verify the fix landed with no unrelated drift. Accept (`1`) only when clean; a genuinely clean first draft may be accepted — do not invent cosmetic revisions.
6. **After accept**: wait for `created docs/plans/<file>.md` in the log, then check the log tail for `Continue with plan implementation? [y/N]` and send `n`. NEVER `y` — execution is the user's call unless they explicitly said otherwise.
7. **Cleanup**: kill the `tail` keeper, confirm `pgrep -x ralphex` is empty, TaskStop the monitor. Report the plan path and a summary of the review iterations.

## Red flags (each one broke a real run)

| Mistake | Consequence |
|---|---|
| Reusing an old answers file | `tail -n +1` replays previous answers — the plan self-accepts instantly |
| Queueing two answers at once | ralphex's `AskYesNo` creates a *fresh* bufio reader; a queued line sits in the old reader's buffer and is lost |
| Skipping the user ticket gate | The user gets a plan for a ticket they never approved |
| Forgetting `n` on the Continue prompt | ralphex hangs waiting (or worse, runs the implementation); the process lingers |
| Writing ticket/feedback files into the project repo unprompted | The user owns the repo; scratchpad only |
| Trusting the monitor for prompt detection | Newline-less prompt lines never fire it; the run stalls silently — check the log tail |
