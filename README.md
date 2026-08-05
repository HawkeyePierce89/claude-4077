# ticket-to-plan

A [Claude Code](https://claude.com/claude-code) plugin that wraps [ralphex](https://github.com/umputun/ralphex) into a full feature cycle. Two skills:

**`ticket-to-plan:plan`** — feature request → accepted plan on disk:

1. Claude composes a tech-lead ticket (English prose: goal / requirements / acceptance / out of scope) from your discussion or a one-line request.
2. **You review the ticket** — nothing is sent anywhere before your approval.
3. Claude launches `ralphex --plan` in the background and drives its interactive prompts through a pipe (which sidesteps the terminal's canonical-mode limits: multi-line paste truncation, the 1024-byte line cap, broken backspace over wrapped lines).
4. Claude reviews each plan draft against the ticket and the codebase, sends Revise feedback, and iterates until the plan is clean.
5. On accept, ralphex saves the plan to `docs/plans/` and Claude answers `n` to "Continue with plan implementation?" — running the plan stays your call.

**`ticket-to-plan:review`** — after you run the plan yourself (`ralphex docs/plans/<plan>.md`), the independent acceptance review of the resulting branch: the project's test/build gates first, every changed file read in full, load-bearing logic verified by hand against the plan's acceptance criteria, prioritized findings, and an explicit list of what was *not* verified.

## Install

```
/plugin marketplace add HawkeyePierce89/ticket-to-plan
/plugin install ticket-to-plan@ticket-to-plan
```

For local development, add the checkout instead:

```
/plugin marketplace add ~/git/ticket-to-plan
```

## Requirements

- [ralphex](https://github.com/umputun/ralphex) on `PATH`, configured for your project (tested against v1.5.0 — the prompt-driving details in the `plan` skill depend on its line-based input).
- Claude Code with background tasks enabled.
