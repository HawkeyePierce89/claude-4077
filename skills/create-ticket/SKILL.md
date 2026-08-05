---
name: create-ticket
description: Use when the user asks to compose a developer ticket for a feature — "сделай тикет", "make a ticket", "составь тикет" — typically after a design discussion, before sending anything to ralphex.
---

# Compose the ticket

## Overview

Produce a tech-lead ticket the user will review. This skill ends with the ticket on screen — it never launches ralphex: the user signals approval by invoking `ticket-to-plan:ralphex` themselves (possibly after asking for edits).

## Steps

1. Compose a tech-lead prose ticket, in **English**: goal → requirements → acceptance criteria → out of scope → conventions. No file-by-file steps, no code snippets — the plan agent knows the codebase; the ticket states WHAT and the constraints. Fold every already-known review remark into it (a remark folded here saves a Revise iteration later). Add the line: *"Language: the plan file itself must be written in English."*
2. The feature comes from the invocation argument if given, otherwise from the **preceding conversation** (the design discussion). If neither suffices for a defensible ticket, ask before writing.
3. Save the ticket to the scratchpad as `ticket-<slug>.md` (NOT into the project repo) and show it to the user in full, ending with: edits are folded in on request; when it looks right, they invoke `ticket-to-plan:ralphex`.

## Red flags

| Mistake | Consequence |
|---|---|
| Proceeding to ralphex from here | The user never approved the ticket — the invocation of `ticket-to-plan:ralphex` IS the approval |
| Writing the ticket into the project repo | The user owns the repo; scratchpad only |
| File-by-file steps or code snippets in the ticket | That is the plan agent's job; the ticket states WHAT and constraints |
