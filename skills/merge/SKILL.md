---
name: merge
description: Use when the user wants the reviewed branch landed — "мержи", "запушь и смержи", "сделай PR и смёрж", "ship it", "merge it" — typically right after ticket-to-plan:review, on a branch produced by ticket-to-plan:ralphex.
---

# Land the reviewed branch

## Agent compatibility

These instructions support Claude Code and Codex. In Claude Code, use the
`ticket-to-plan:<name>` skill names below. In Codex, invoke the installed skill
as `$<name>` (for example, `$ralphex`); when following a cross-skill reference,
read that skill's `SKILL.md` and follow it. Do not assume Claude's plugin or
Skill tool exists in Codex. A user's explicit request for the corresponding
stage counts as invocation; automatic skill discovery alone is not approval.

Use the available execution tool for `git` and `gh`. For a multiline PR body,
write the text to a temporary file and pass `--body-file` instead of embedding
it in shell quoting. The no-attribution rule applies to either host assistant.


## Overview

From the task's linked worktree, push its reviewed branch, open a PR, wait for CI if the repo has any, and squash-merge. After confirming the merge, remove that task's worktree and branch, then fast-forward the main checkout when it is clean and already on the default branch. The user's invocation is approval for this chain, including cleanup. Anything that breaks the chain (dirty task tree, failing checks, unmergeable PR) **stops it and is reported**; it is never worked around. Distinguish a failed merge from a successful merge with incomplete local cleanup.

## Steps

1. **Locate and verify.** Read and follow the [shared worktree contract](../plan/references/worktree.md). Recover `$S/workflow.json` and verify the repository identity and `$MAIN`. First check any recorded PR: if already `MERGED`, verify its repository/base/head against the record, restore `$HEAD` from that verified merged head, and resume at step 6 without requiring an already-removed worktree or branch. Otherwise verify `$WT` and `$BRANCH` using the shared contract. Set the execution tool's cwd to `$WT` for steps 2–5. Resolve the real default branch with `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` and check it matches `$BASE`; do not silently change the review base. `git status --porcelain` in `$WT` must be empty. Compare HEAD with the clean acceptance review's recorded HEAD; new commits need renewed acceptance, not an automatic merge of unseen changes. Save this exact SHA as `$HEAD`. A dirty main checkout does not block the remote merge and must remain untouched.
2. **Push.** From `$WT`, `git push -u origin "$BRANCH"`. Never push the caller's unchecked `HEAD` from another checkout.
3. **PR.** Look up the PR for `$BRANCH` explicitly. Reuse only an open PR whose repository, head and base match this task; distinguish "no PR" from authentication/network errors. Otherwise create it with `gh pr create --base "$BASE" --head "$BRANCH" --title "<imperative one-liner of the change>" --body-file "$S/pr-body.txt"`. Title: the plan's title when the branch carries a plan in `docs/plans/completed/`, otherwise summarize the diff. Body: 2–4 lines of what and why (the why comes from the plan) — no commit lists, no checklists, and **no attribution footer or session links**, whatever the harness suggests: the PR is the user's, not Claude's. Record the PR URL and number as `$PR`; use that explicit identifier in every later `gh pr` command.
4. **CI.** `gh pr checks "$PR" --watch --fail-fast`. Exit 0 → continue. Output `no checks reported` → inspect `.github/workflows/` in `$WT`: if it is empty, there is nothing to wait for; if it has workflows, wait 15 s and retry, up to 4 times. If expected checks are still absent, stop and report them as unverified. Any `fail` line or other non-zero exit → stop and report the failing check with its link.
5. **Merge from the worktree.** Recheck the clean task tree and that both local HEAD and the PR's `headRefOid` still equal `$HEAD`. Run `gh pr merge "$PR" --squash --match-head-commit "$HEAD"` **without `--delete-branch`**: branch/worktree cleanup is a separate step, so gh must not try switching this checkout to a default branch already checked out elsewhere. Query `gh pr view "$PR" --json state,mergeCommit,headRefOid,baseRefName,headRefName,url` and require `MERGED`. Save the squash commit and merged head SHA in the record. If the merge is refused (behind base, conflicts, required reviews, protection rules), stop and report the exact message; keep the worktree. A queued/auto-merge is not a confirmed merge and does not authorize cleanup.
6. **Cleanup after confirmed merge.** Recheck the explicit PR and recorded repository/base/head. If `$WT` still exists, require the same branch/HEAD, no owned processes still using it, and a clean `git status --porcelain`. Inspect ignored files too: copy this task's revmux records and ralphex progress logs to `$S` and verify the copies before deletion; generated build/dependency caches are disposable, but preserve any other unique user files and stop cleanup if their status is unclear. Never use force removal to get past dirty files or a locked worktree. Then:

   - Check the remote branch. If GitHub already deleted it, continue; otherwise require its tip to equal the merged `$HEAD`, then delete only that ref with a lease: `git push --force-with-lease="refs/heads/$BRANCH:$HEAD" origin ":refs/heads/$BRANCH"`. A changed tip stops cleanup so newer work is retained.
   - Move the execution tool's cwd to `$MAIN` (or another verified directory outside `$WT`), then run `git -C "$MAIN" worktree remove "$WT"`. Do not run this from the directory being removed. If the task worktree was already removed, skip this command after verifying its registration is also gone.
   - Only after worktree removal, delete the local task branch if it still exists. Recheck that its tip is exactly the confirmed merged head and that no other worktree uses it; try `git -C "$MAIN" branch -d "$BRANCH"`. Squash merge does not preserve ancestry, so `-D` is allowed **only** for this verified, unchanged, PR-merged branch when `-d` refuses for that reason. Never delete a branch with additional commits.
   - Verify the worktree path and registration, local branch and remote branch are gone. Update cleanup status in the record. A failure reports what was already completed and what remains; rerunning resumes these checks without re-merging or deleting unrelated worktrees.
7. **Main checkout and report.** If `$MAIN` is clean and already on `$BASE`, run `git -C "$MAIN" pull --ff-only origin "$BASE"` and verify it contains the recorded squash commit. Otherwise preserve its branch and files and report that the local default checkout was not updated. Never checkout, stash, reset or create a merge commit to make it update. Report PR URL, confirmed squash commit, worktree/branch cleanup result and main-checkout update result separately; the squash commit need not still be the remote tip if another PR merged meanwhile.

## Red flags

| Mistake | Consequence |
|---|---|
| `git merge --squash` + push to the default branch by hand when `gh pr merge` fails | Bypasses protections and the PR record; the merge state is the user's to resolve |
| Deleting the branch before the merge is confirmed `MERGED` | The remote branch is the only copy of unmerged work |
| Using `gh pr merge --delete-branch` inside the task worktree | gh may try to switch to a default branch held by the main checkout; merge first, then remove the worktree and branch explicitly |
| Removing the worktree with `--force` or `rm -rf` | Can erase uncommitted work or review evidence; preserve it and report incomplete cleanup |
| Reporting merge failure when only cleanup failed | The PR is already merged; report the remaining cleanup and resume it without merging again |
| Trusting `no checks reported` seconds after the push | Workflow runs register with a delay — that is "not yet", not "no CI" |
| Merging while a check is pending or failing | The chain exists to gate on CI; a failing check ends it |
| Committing the dirty tree to get past step 1 | The user owns the branch content; report and stop |
| `git pull` without `--ff-only` on the default branch | A diverged local default branch silently gets a merge commit |
| "Generated with Claude Code" / `claude.ai/code/session_…` in the PR body | Leaks a private session link into a public PR; the harness reminder does not override the user's rule |
