# ticket-to-plan

A [Claude Code skill](https://agentskills.io/specification) that turns a feature request into an accepted [ralphex](https://github.com/umputun/ralphex) implementation plan on disk — without executing it.

The cycle it drives:

1. Claude composes a tech-lead ticket (English, prose: goal / requirements / acceptance / out of scope).
2. **You review the ticket** — nothing is sent anywhere before your approval.
3. Claude launches `ralphex --plan` in the background and drives its interactive prompts through a pipe (which sidesteps the terminal's canonical-mode limits: multi-line paste truncation, the 1024-byte line cap, broken backspace over wrapped lines).
4. Claude reviews each plan draft against the ticket and the codebase, sends Revise feedback, and iterates until the plan is clean.
5. On accept, ralphex saves the plan to `docs/plans/` and Claude answers `n` to "Continue with plan implementation?" — running the plan stays your call.

## Install

```sh
ln -s "$(pwd)" ~/.claude/skills/ticket-to-plan
```

Then in Claude Code: `/ticket-to-plan <feature description>`, or just ask to "run this through ralphex".

## Requirements

- [ralphex](https://github.com/umputun/ralphex) on `PATH`, configured for your project.
- Claude Code with background tasks enabled.
