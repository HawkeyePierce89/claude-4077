# ticket-to-plan

A [Claude Code](https://claude.com/claude-code) plugin that turns a feature request into a merged branch: [ralphex](https://github.com/umputun/ralphex) plans and writes the code, [revmux](https://github.com/umputun/revmux) reviews the diff, Claude does the final acceptance by hand, the plugin lands it. Four skills, three human gates:

**`ticket-to-plan:create-ticket`** — Claude composes a tech-lead ticket (English prose: goal / requirements / acceptance / out of scope) from your design discussion or a one-line request, and shows it to you. Nothing is sent anywhere.

**`ticket-to-plan:ralphex`** — when the ticket looks right, you invoke this (that's the first gate). Three stages run back to back:
- *plan* — `ralphex --plan` is driven through a pipe (which sidesteps the terminal's canonical-mode limits); Claude reviews each draft against the ticket and the codebase, sends Revise feedback until the plan is clean, accepts, and declines ralphex's own execution.
- *code* — `ralphex --tasks-only` runs the plan in the background on `opus:medium`; ralphex creates the branch, commits per task, and archives the plan under `docs/plans/completed/`. Claude watches the log and reports once an hour if nothing terminal happened.
- *review* — the project's own test/build gates first, then the branch goes to `revmux:revmux` with the plan's acceptance criteria as the goal and the ticket as context, `comprehensive` profile. revmux presents the findings and asks what to do (that's the second gate): fix through ralphex and re-review, or stop. Fixes never happen in the session: Claude writes a short fix plan from the accepted findings, ralphex runs it on the branch, the plan is dropped again so the default branch never carries it, and the next revmux round runs on `final`. Claude adds the gate results.

Anything that breaks the chain (a failed ralphex run, red gates, a degraded review) stops it with a report; "продолжай" resumes at the stage that failed.

**`ticket-to-plan:review`** — the final acceptance, by hand in the session: the project's gates, every changed file read in full, the plan's semantics verified against the implementation (the class of bug a diff review misses: boundaries, units, time zones), the revmux record checked so its gating findings are really fixed and nothing is reported twice, prioritized findings, and an explicit list of what was *not* verified.

**`ticket-to-plan:merge`** — when the acceptance is clean, the landing chain: push the branch, open a PR, wait for the repo's checks if it has any, squash-merge and delete the branch, and leave your checkout on the freshly pulled default branch. Anything that breaks the chain (dirty tree, failing check, unmergeable PR) stops it with a report instead of being worked around, and nothing outside the chain happens — no direct pushes to the default branch, no attribution footers in the PR.

## Install

```
/plugin marketplace add HawkeyePierce89/claude-4077
/plugin install ticket-to-plan@HawkeyePierce89
```

For local development, add the checkout instead:

```
/plugin marketplace add ~/git/claude-4077
```

## Requirements

- [ralphex](https://github.com/umputun/ralphex) on `PATH`, configured for your project (tested against v1.7.0 — the prompt-driving details in the plan stage depend on its line-based input, and the code stage relies on `--tasks-only` archiving the plan).
- [revmux](https://github.com/umputun/revmux) on `PATH` **and** its skill: `/plugin marketplace add umputun/revmux`, then `/plugin install revmux@revmux`. The default `comprehensive` profile also needs the `codex` CLI authenticated.
- [GitHub CLI](https://cli.github.com/) (`gh`), authenticated, for the `merge` skill.
- Claude Code with background tasks enabled.
