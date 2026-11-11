# ticket-to-plan

A shared skill collection for [Claude Code](https://claude.com/claude-code) and Codex that turns a feature request into a merged branch: [ralphex](https://github.com/umputun/ralphex) plans and writes the code, [revmux](https://github.com/umputun/revmux) reviews the diff, the assistant does the final acceptance by hand, the plugin lands it. Five skills, three human gates. The names below use Claude Code syntax; in Codex use `$create-ticket`, `$plan`, `$ralphex`, `$review`, and `$merge`:

**`ticket-to-plan:create-ticket`** — the assistant composes a tech-lead ticket (English prose: goal / requirements / acceptance / out of scope) from your design discussion or a one-line request, and shows it to you. Nothing is sent anywhere.

**`ticket-to-plan:plan`** — the plan alone: `ralphex --plan` is driven through a pipe (which sidesteps the terminal's canonical-mode limits); the assistant reviews each draft against the ticket and the codebase, sends Revise feedback until the plan is clean, accepts, and declines ralphex's own execution. Before planning starts, the skill creates a feature branch and a linked worktree from the repository’s default branch (`master`, `main`, etc.). The plan lands in that worktree’s `docs/plans/`; running it is a separate decision. The main checkout is left untouched.

**`ticket-to-plan:ralphex`** — the full cycle. When the ticket looks right, you invoke this (that's the first gate), or invoke it later on a plan `ticket-to-plan:plan` produced. Three stages run back to back:
- *plan* — `ticket-to-plan:plan`, skipped when a plan is already there.
- *code* — `ralphex --tasks-only` runs the plan in the background on `sonnet:high` (the design is in the accepted plan, so task execution, the bulk of the token bill, goes to the cheaper model); the skill reuses the plan’s worktree and commits only the approved plan if needed, then ralphex runs on that existing branch, commits per task, and archives the plan under `docs/plans/completed/`. the assistant watches the log and reports progress at the host assistant's required cadence.
- *review* — the project's own test/build gates first, then the branch goes to `revmux:revmux` with the plan's acceptance criteria as the goal and the ticket as context, `comprehensive` profile. revmux presents the findings and asks what to do (that's the second gate): fix through ralphex and re-review, or stop. Fixes never happen in the session: the assistant writes a short fix plan from the accepted findings, ralphex runs it on the branch, the plan is dropped again so the default branch never carries it, and the next revmux round runs on `final`. the assistant adds the gate results.

Anything that breaks the chain (a failed ralphex run, red gates, a degraded review) stops it with a report; "продолжай" resumes at the stage that failed in the same worktree, retaining partial progress.

**`ticket-to-plan:review`** — the final acceptance in the same task worktree, by hand in the session: the project's gates, every changed file read in full, the plan's semantics verified against the implementation (the class of bug a diff review misses: boundaries, units, time zones), callers in untouched code found through the LSP tool (or targeted `rg` searches when LSP is unavailable), the revmux record checked so its gating findings are really fixed and nothing is reported twice, prioritized findings, and an explicit list of what was *not* verified.

**`ticket-to-plan:merge`** — when acceptance is clean, push and open the PR from the task worktree, wait for checks, and squash-merge. Once the PR is confirmed merged, preserve review evidence in the scratchpad, remove the worktree and delete its branch locally and remotely. Fast-forward the main checkout only if it is clean and already on the default branch. Failed checks or a refused merge retain the worktree; a cleanup failure is reported separately from a successful merge. No direct pushes to the default branch or attribution footers in the PR.

## Worktree lifecycle

The ticket, workflow record, feedback and logs live in the session scratchpad.
The first planning invocation creates a linked worktree, normally at
`<parent>/<repo>.worktrees/<slug>`, on `task/<slug>` from the freshly fetched
default branch. Planning, implementation, fixes, revmux, acceptance and merge
all use this one worktree. Invoking a later skill from the main checkout still
resolves and uses the task worktree; stages report its path and the scratchpad
record at each handoff. Several tasks can therefore keep separate worktrees.

A plan-only run leaves its plan in the task worktree. Stopping or failing a
stage keeps the worktree for resumption; successful PR merge triggers cleanup.
Unrelated changes in the main checkout are never stashed, committed or copied.
An approved legacy plan can be copied into a new task worktree without changing
its original. The full contract is in
[the worktree reference](skills/plan/references/worktree.md).

This lifecycle uses `git worktree` directly. Ralphex's own `--worktree` mode
creates its worktree at execution time and normally removes it when that run
ends, so it does not cover separate planning and acceptance stages. Leave
ralphex's `use_worktree` setting disabled for this pipeline. In the tested
ralphex v1.7.0, automatic initial-plan commit is part of branch creation from
the default branch; on an existing feature branch the skill commits the
approved plan before launching tasks.

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
