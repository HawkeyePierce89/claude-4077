# ticket-to-plan

A shared skill collection for [Claude Code](https://claude.com/claude-code) and Codex that turns a feature request into a merged branch: [ralphex](https://github.com/umputun/ralphex) plans and writes the code, [revmux](https://github.com/umputun/revmux) reviews the diff, the assistant does the final acceptance by hand, the plugin lands it. Five skills, three human gates. The names below use Claude Code syntax; in Codex use `$create-ticket`, `$plan`, `$ralphex`, `$review`, and `$merge`:

**`ticket-to-plan:create-ticket`** — the assistant composes a tech-lead ticket (English prose: goal / requirements / acceptance / out of scope) from your design discussion or a one-line request, and shows it to you. Nothing is sent anywhere.

**`ticket-to-plan:plan`** — the plan alone: `ralphex --plan` is driven through a pipe (which sidesteps the terminal's canonical-mode limits); the assistant reviews each draft against the ticket and the codebase, sends Revise feedback until the plan is clean, accepts, and declines ralphex's own execution. The plan lands in `docs/plans/`; running it is a separate decision.

**`ticket-to-plan:ralphex`** — the full cycle. When the ticket looks right, you invoke this (that's the first gate), or invoke it later on a plan `ticket-to-plan:plan` produced. Three stages run back to back:
- *plan* — `ticket-to-plan:plan`, skipped when a plan is already there.
- *code* — `ralphex --tasks-only` runs the plan in the background on `sonnet:high` (the design is in the accepted plan, so task execution, the bulk of the token bill, goes to the cheaper model); ralphex creates the branch, commits per task, and archives the plan under `docs/plans/completed/`. the assistant watches the log and reports progress at the host assistant's required cadence.
- *review* — the project's own test/build gates first, then the branch goes to `revmux:revmux` with the plan's acceptance criteria as the goal and the ticket as context, `comprehensive` profile. revmux presents the findings and asks what to do (that's the second gate): fix through ralphex and re-review, or stop. Fixes never happen in the session: the assistant writes a short fix plan from the accepted findings, ralphex runs it on the branch, the plan is dropped again so the default branch never carries it, and the next revmux round runs on `final`. the assistant adds the gate results.

Anything that breaks the chain (a failed ralphex run, red gates, a degraded review) stops it with a report; "продолжай" resumes at the stage that failed.

**`ticket-to-plan:review`** — the final acceptance, by hand in the session: the project's gates, every changed file read in full, the plan's semantics verified against the implementation (the class of bug a diff review misses: boundaries, units, time zones), callers in untouched code found through the LSP tool (or targeted `rg` searches when LSP is unavailable), the revmux record checked so its gating findings are really fixed and nothing is reported twice, prioritized findings, and an explicit list of what was *not* verified.

**`ticket-to-plan:merge`** — when the acceptance is clean, the landing chain: push the branch, open a PR, wait for the repo's checks if it has any, squash-merge and delete the branch, and leave your checkout on the freshly pulled default branch. Anything that breaks the chain (dirty tree, failing check, unmergeable PR) stops it with a report instead of being worked around, and nothing outside the chain happens — no direct pushes to the default branch, no attribution footers in the PR.

## Install

### Claude Code

```
/plugin marketplace add HawkeyePierce89/claude-4077
/plugin install ticket-to-plan@HawkeyePierce89
```

For local development, add the checkout instead:

```
/plugin marketplace add ~/git/claude-4077
```

### Codex

From this checkout, install all five skills:

```bash
python3 scripts/install-codex.py --dry-run
python3 scripts/install-codex.py
```

The installer creates symlinks in `$CODEX_HOME/skills` (default
`~/.codex/skills`), so updates to the checkout are picked up without copying
skills. Keep the checkout at this location. Re-running is safe; if any name
is occupied by a different skill or a broken link, it reports the conflict
and creates no new links. It never overwrites existing skills.
Use `--dest /path/to/skills` for a different skills directory.
The installed skills become available on the next turn; start a new session
if your client has not refreshed its skill list.

Example sequence in Codex:

```text
$create-ticket Add CSV export to the reports page
$plan
$ralphex
$review
$merge
```

`$plan` is optional: `$ralphex` can drive planning itself. Review findings
still require the user's decision before fixes. `$review` and `$merge` remain
separate requested stages. Both hosts read the same `skills/*/SKILL.md` files;
Claude's marketplace metadata remains under `.claude-plugin/`.

## Requirements

- [ralphex](https://github.com/umputun/ralphex) on `PATH`, configured for your project (tested against v1.7.0 — the prompt-driving details in the plan stage depend on its line-based input, and the code stage relies on `--tasks-only` archiving the plan).
- [revmux](https://github.com/umputun/revmux) on `PATH` **and** its skill. In Claude Code: `/plugin marketplace add umputun/revmux`, then `/plugin install revmux@revmux`. In Codex: install the revmux skill using its own Codex instructions; this repository does not bundle it. The default `comprehensive` profile also needs the `codex` CLI authenticated.
- [GitHub CLI](https://cli.github.com/) (`gh`), authenticated, for the `merge` skill.
- Claude Code with background tasks enabled, or Codex with persistent command sessions for long-running processes. Codex uses session polling instead of Claude's Monitor/TaskStop tools.
- Python 3 for the Codex installer. The host assistant and ralphex worker are separate: the existing `sonnet:high` worker setting still requires ralphex's configured backend and authentication.
