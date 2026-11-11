---
name: create-ticket
description: Use when the user asks to compose a developer ticket for a feature — "сделай тикет", "make a ticket", "составь тикет" — typically after a design discussion, before sending anything to ralphex.
---

# Compose the ticket

## Agent compatibility

These instructions support Claude Code and Codex. In Claude Code, use the
`ticket-to-plan:<name>` skill names below. In Codex, invoke the installed skill
as `$<name>` (for example, `$ralphex`); when following a cross-skill reference,
read that skill's `SKILL.md` and follow it. Do not assume Claude's plugin or
Skill tool exists in Codex. A user's explicit request for the corresponding
stage counts as invocation; automatic skill discovery alone is not approval.

Use the harness scratchpad if available. Otherwise create a session directory
with `mktemp -d "${TMPDIR:-/tmp}/ticket-to-plan.XXXXXX"`, keep its path in the
conversation, and reuse it for later stages. In Codex, tell the user to invoke
`$plan` for planning only or `$ralphex` for the full cycle when the ticket is ready.


## Overview

Produce a tech-lead ticket the user will review. This skill ends with the ticket on screen — it never launches ralphex: the user signals approval by invoking `ticket-to-plan:plan` or `ticket-to-plan:ralphex` themselves (possibly after asking for edits). Ticket creation does not create a branch or worktree. The next stage creates a separate worktree from the default branch before planning writes any project files; subsequent stages reuse it through merge.

## Steps

1. Compose a tech-lead prose ticket, in **English**: goal → requirements → acceptance criteria → out of scope → conventions. No file-by-file steps, no code snippets — the plan agent knows the codebase; the ticket states WHAT and the constraints. Fold every already-known review remark into it (a remark folded here saves a Revise iteration later). Add the line: *"Language: the plan file itself must be written in English."*
2. The feature comes from the invocation argument if given, otherwise from the **preceding conversation** (the design discussion). If neither suffices for a defensible ticket, ask before writing.
3. Save the ticket to the scratchpad as `ticket-<slug>.md` (NOT into the project repo), report its absolute path, and show it to the user in full, ending with: edits are folded in on request; when it looks right, they invoke `ticket-to-plan:plan` for planning alone or `ticket-to-plan:ralphex` to run plan, code and review back to back. Keep the target repository's absolute path with the ticket handoff so the next stage can create the correct worktree.

## Red flags

| Mistake | Consequence |
|---|---|
| Proceeding to planning or execution from here | The user never approved the ticket — their invocation of `ticket-to-plan:plan` or `ticket-to-plan:ralphex` IS the approval |
| Writing the ticket into the project repo | The user owns the repo; scratchpad only |
| File-by-file steps or code snippets in the ticket | That is the plan agent's job; the ticket states WHAT and constraints |
