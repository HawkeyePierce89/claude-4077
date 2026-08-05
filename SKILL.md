---
name: ticket-to-plan
description: Use when the user asks to turn a feature request into a ralphex implementation plan — "run this through ralphex", "make a ticket and send it to ralphex", "ticket → plan cycle" — or to review the result of an executed plan ("review the implementation", "проверь реализацию"). Covers composing the ticket, the user's ticket-review gate, driving ralphex's interactive plan mode, the Revise loop, stopping before execution, and the final acceptance review of the branch.
---

# Ticket → plan → review cycle for ralphex

## Overview

Three stages around ralphex, separated by the user's own actions. Stage 1 produces a ticket the **user** reviews; stage 2 drives ralphex until an accepted plan is on disk (never executing it); the user runs the execution themselves; stage 3 is the independent acceptance review of the resulting branch.

**Which stage:** a feature request (argument or preceding design discussion) → run stages 1–2. An invocation like "review the implementation" on a branch where a plan was executed → stage 3 only.

## Stage 1 — Ticket

1. Compose a tech-lead prose ticket, in **English**: goal → requirements → acceptance criteria → out of scope → conventions. No file-by-file steps, no code snippets — the plan agent knows the codebase; the ticket states WHAT and the constraints. Fold every already-known review remark into it. Add: *"Language: the plan file itself must be written in English."* Save to the scratchpad, NOT the repo. The feature comes from the invocation argument if given, otherwise from the **preceding conversation**; if neither suffices for a defensible ticket, ask before writing.
2. **User gate — HARD STOP.** Show the ticket and wait for explicit approval before launching ralphex. Fold their edits in.

## Stage 2 — Plan via ralphex

3. Launch from the project repo root, in background:
   ```bash
   : > "$S/answers-N.txt"   # ALWAYS a fresh file — see red flags
   tail -n +1 -f "$S/answers-N.txt" | ralphex --plan "$(cat "$S/ticket.md")" --no-color > "$S/run-N.log" 2>&1
   ```
   Arm a Monitor on the log: `grep -E --line-buffered '^\s+[0-9]+\) |QUESTION|docs/plans/|panic:|plan creation|rejected|failed'`. Interactive prompts (`Enter number…`, `Continue with plan…`) have **no trailing newline** and never trigger the monitor — detect them by the option lines above them, or `tail -c` the log directly.
4. Answer prompts by appending ONE line to the answers file per prompt. Clarifying questions → answer from the ticket; product-level questions → stop and ask the user.
5. Review each draft honestly against the ticket and the codebase (verify claims in the code — don't wave anything through). Remarks → send `2`, then the feedback as one line (a pipe has no 1024-byte tty limit). On the next iteration, **diff the two drafts** to verify the fix landed with no unrelated drift. Accept (`1`) only when clean; a genuinely clean first draft may be accepted — do not invent cosmetic revisions.
6. After accept: wait for `created docs/plans/<file>.md` in the log, then check the log tail for `Continue with plan implementation? [y/N]` and send `n`. NEVER `y` — execution is the user's call unless they explicitly said otherwise.
7. Cleanup: kill the `tail` keeper, confirm `pgrep -x ralphex` is empty, TaskStop the monitor. Report the plan path and a summary of the review iterations. The user runs `ralphex <plan>` themselves.

## Stage 3 — Acceptance review of the executed branch

ralphex's own loop already ran its internal reviews; this is the independent final gate before merge. Review against the **plan** (after execution ralphex moves it to `docs/plans/completed/`), not the ticket — the ticket was ephemeral, the plan carries the requirements and acceptance criteria.

8. Run the project's own gates first: the test suite and every build target the project's CI runs. Report exact counts and results, not "seems fine".
9. Read **every changed file in full** (diff against the default branch), not just the hunks — new code is judged in the context it lives in.
10. Verify the load-bearing logic by hand: work edge cases through the actual code (boundaries, concurrency, off-by-one), and **live-verify** claims where possible — run the real underlying commands or reproduce the mechanism outside the app rather than trusting comments and tests alone.
11. Check the result against the plan's acceptance criteria and the repo's conventions doc, item by item.
12. Report: verdict first; findings prioritized (critical / important / minor) with a concrete fix per finding; what was verified and how; and an explicit **"NOT verified"** list (typically manual/visual checks) — offer to run the app when the change is visual. Do not fix anything unprompted: findings go to the user, whose pipeline applies them.

## Red flags (each one broke a real run)

| Mistake | Consequence |
|---|---|
| Reusing an old answers file | `tail -n +1` replays previous answers — the plan self-accepts instantly |
| Queueing two answers at once | ralphex's `AskYesNo` creates a *fresh* bufio reader; a queued line sits in the old reader's buffer and is lost |
| Skipping the user ticket gate | The user gets a plan for a ticket they never approved |
| Forgetting `n` on the Continue prompt | ralphex hangs waiting (or worse, runs the implementation); the process lingers |
| Writing ticket/feedback files into the project repo unprompted | The user owns the repo; scratchpad only |
| Trusting the monitor for prompt detection | Newline-less prompt lines never fire it; the run stalls silently — check the log tail |
| Reviewing only the diff hunks in stage 3 | Misses interactions with surrounding code — the bugs that survive the author's own review |
| Stage-3 verdict without running the gates | "Tests pass" claimed from reading code is not evidence — run them |
