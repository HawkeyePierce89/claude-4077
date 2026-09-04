---
name: merge
description: Use when the user wants the reviewed branch landed — "мержи", "запушь и смержи", "сделай PR и смёрж", "ship it", "merge it" — typically right after ticket-to-plan:review, on a branch produced by running a plan from docs/plans/.
---

# Land the reviewed branch

## Overview

Push the current branch, open a PR, wait for CI if the repo has any, squash-merge, and leave the checkout on the freshly pulled default branch. The user's invocation is the merge approval — for exactly this chain. Anything that breaks the chain (dirty tree, failing checks, unmergeable PR) **stops it and is reported**; it is never worked around.

## Steps

1. **Preconditions.** `git status --porcelain` must be empty — if not, stop and show it (the user decides what enters the reviewed branch). Resolve the default branch: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`. The user may say "master" out of habit — always use the real name. The current branch must not be the default branch.
2. **Push.** `git push -u origin HEAD`.
3. **PR.** If `gh pr view --json url -q .url` prints a URL, reuse that PR. Otherwise `gh pr create --base <default> --title "<imperative one-liner of the change>" --body "<2–4 lines: what and why>"`. Title: the plan's title when the branch came from `docs/plans/completed/`, otherwise summarize the diff. Body: those lines (the why comes from the plan when there is one) plus whatever footer the harness mandates — no commit lists, no checklists.
4. **CI.** `gh pr checks --watch --fail-fast`. Exit 0 → continue. Output `no checks reported` → look at `.github/workflows/`: if it is empty, there is nothing to wait for; if it has workflows, the run has not registered yet — wait 15 s and retry, up to 4 times, before concluding. Any `fail` line or other non-zero exit → stop and report the failing check with its link.
5. **Merge.** `gh pr merge --squash` (add `--delete-branch` only when the user said to delete the branch). Confirm `gh pr view --json state -q .state` prints `MERGED`. If the merge is refused (behind base, conflicts, required reviews, protection rules) → stop and report the exact message.
6. **Local.** `git checkout <default> && git pull --ff-only`. Report: PR URL, the squash commit now at the tip of the default branch, and that the feature branch still exists locally and on the remote.

## Red flags

| Mistake | Consequence |
|---|---|
| `git merge --squash` + push to the default branch by hand when `gh pr merge` fails | Bypasses protections and the PR record; the merge state is the user's to resolve |
| Deleting the branch (`--delete-branch`, `git branch -D`, `push --delete`) unasked | Not part of the chain; `-D` on a squash-merged branch is irreversible |
| Trusting `no checks reported` seconds after the push | Workflow runs register with a delay — that is "not yet", not "no CI" |
| Merging while a check is pending or failing | The chain exists to gate on CI; a failing check ends it |
| Committing the dirty tree to get past step 1 | The user owns the branch content; report and stop |
| `git pull` without `--ff-only` on the default branch | A diverged local default branch silently gets a merge commit |
