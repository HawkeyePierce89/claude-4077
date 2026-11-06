---
name: plan
description: Use when the user wants ralphex to produce the implementation plan and nothing more — "составь план", "только план", "сделай план в ralphex", "plan only" — right after ticket-to-plan:create-ticket, when running the plan is a separate decision.
---

# Drive ralphex to an accepted plan

## Agent compatibility

These instructions support Claude Code and Codex. In Claude Code, use the
`ticket-to-plan:<name>` skill names below. In Codex, invoke the installed skill
as `$<name>` (for example, `$ralphex`); when following a cross-skill reference,
read that skill's `SKILL.md` and follow it. Do not assume Claude's plugin or
Skill tool exists in Codex. A user's explicit request for the corresponding
stage counts as invocation; automatic skill discovery alone is not approval.

Use the harness scratchpad if available; otherwise create a session directory
with `mktemp -d "${TMPDIR:-/tmp}/ticket-to-plan.XXXXXX"`. Reuse the ticket's
existing directory when continuing the same workflow; `$S` below denotes it.
In Codex, run long commands through the execution tool's persistent session
and poll using its returned session ID. Monitor/TaskStop below are Claude
facilities: when unavailable, inspect the log periodically and manage only
this run's process/session IDs. Keep track of the input keeper and ralphex
process; confirm this run exited, without requiring unrelated ralphex runs
to stop. Never use a global process kill. Follow the harness's progress-update
cadence while waiting. If LSP is unavailable, use `rg` and targeted file reads.


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
3. Review each draft honestly against the ticket and the codebase (verify claims in the code — don't wave anything through). A claim about one symbol is checked through the LSP tool (definition, references, hover) or `grep`, which answer in a few lines; read a file in full only when the draft's reasoning depends on that file's structure. Remarks → send `2`, then the feedback as one line (a pipe has no 1024-byte tty limit). On the next iteration, **diff the two drafts** to verify the fix landed with no unrelated drift. Accept (`1`) only when clean; a genuinely clean first draft may be accepted — do not invent cosmetic revisions.
4. After accept: wait for `created docs/plans/<file>.md` in the log, then check the log tail for `Continue with plan implementation? [y/N]` and append `n` as one line to the answers file. NEVER `y`: `y` runs ralphex's full mode with its own review phases, which this pipeline replaces with revmux. Stop this run's `tail` keeper, confirm this run's ralphex process has exited, and stop its monitor (TaskStop in Claude Code, the owned session/process in Codex). Report the plan path and the review iterations in one short paragraph. The plan is uncommitted on the default branch, which is what `ticket-to-plan:ralphex` expects when it starts from an existing plan; that skill runs it, the review and the fix cycle when the user asks, or they run `ralphex --tasks-only <plan>` themselves.

## Red flags (each one broke a real run)

| Mistake | Consequence |
|---|---|
| Launching on a ticket the user never saw | The approval gate is `create-ticket` + the user's decision to invoke this skill — don't shortcut it |
| Reusing an old answers file | `tail -n +1` replays previous answers — the plan self-accepts instantly |
| Queueing two answers at once | ralphex's `AskYesNo` creates a *fresh* bufio reader; a queued line sits in the old reader's buffer and is lost |
| `y` on the Continue prompt | Runs ralphex's full pipeline with its own review phases; execution is a separate decision and, in this pipeline, a separate skill |
| Trusting the monitor for prompt detection | Newline-less prompt lines never fire it; the run stalls silently — check the log tail |
| Writing feedback files into the project repo | The user owns the repo; scratchpad only |
| Reading whole files to check one claim in a draft | The draft names symbols, and the LSP tool answers about a symbol in a few lines; a full read costs the session's model thousands of tokens per claim |
