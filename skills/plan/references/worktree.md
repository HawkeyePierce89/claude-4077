# One worktree per task

Read this contract before `plan`, `ralphex`, `review`, or `merge`. The ticket
stays in the scratchpad. Create the task's branch and linked worktree **before
launching planning**, so even the first saved draft belongs to that worktree.
Planning, execution, gates, fixes, both reviews, push and PR merge all use the
same worktree. Keep it through failures and pauses; remove it only after a
confirmed merge, following the merge skill. On a retry after a confirmed merge,
the merge skill may resume cleanup even if the worktree was already removed.

## Identity and handoff

Use these names throughout the workflow:

- `$S`: this task's scratchpad directory, outside every project worktree. If the
  harness scratchpad already holds another task's record, use a new child
  directory and retain the absolute ticket path; never overwrite another task's record.
- `$MAIN`: the original/main checkout, resolved from `git worktree list --porcelain`.
- `$WT`: the absolute path to this task's linked worktree.
- `$TICKET`: the absolute path to the approved ticket, which may be in a parent scratchpad.
- `$BRANCH`: this task's feature branch, for example `task/<slug>`.
- `$BASE`: the repository's real default branch (`master`, `main`, etc.).
- `$BASE_REF`: `origin/$BASE` when origin is available, otherwise the local `$BASE`.

Keep a plain data record at `$S/workflow.json` with the repository's absolute
common Git directory (`git rev-parse --path-format=absolute --git-common-dir`),
`main`, `worktree`, `branch`, `base`, `base_ref`, the initial `base_commit`,
absolute `ticket` path, and the plan's worktree-relative path. Update the plan
path when it moves to `docs/plans/completed/`; keep the original feature plan
separate from the active fix-plan path so dropping a fix plan cannot lose the
acceptance criteria. Add the revmux task path, reviewed HEAD, PR URL/number and
merge/cleanup status as those become known. Read this as
data; do not source it as shell code. Report the absolute worktree, branch,
plan and record paths at stage handoffs so a later invocation can find them.

The record is a locator, not proof. At every stage, check the repository common
directory, `git worktree list --porcelain`, `git -C "$WT" rev-parse --show-toplevel`
and `git -C "$WT" branch --show-current` against it. `$WT` must be a linked
worktree, distinct from `$MAIN`, on `$BRANCH`, and `$BRANCH` must not be `$BASE`.
Use an explicit execution-tool working directory for **every** command; a `cd`
in a previous call is not persistent. Resolve project files relative to `$WT`.
Give the same cwd and paths to ralphex, revmux and any delegated workers.

If the record is unavailable, recover it from the explicit plan/worktree path,
conversation and registered worktrees. Reuse an existing worktree only when its
branch and task match. If multiple candidates remain, ask which task to use;
never select the newest plan or the caller's current branch as a guess. A
missing worktree on resume is a recovery issue, not a reason to start a fresh
branch and lose uncommitted progress.

## Create once, before planning

1. Identify the repository and `$MAIN` without switching its branch. Resolve
   `$BASE` with `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
   or the verified origin HEAD. For a local-only repository, use its known
   default branch; ask if ambiguous. Never assume the current branch is the base.
2. With origin, fetch the base branch into its remote-tracking ref and use that
   as `$BASE_REF` (`git fetch origin "refs/heads/$BASE:refs/remotes/origin/$BASE"`).
   A fetch failure stops creation; do not silently use a stale ref. Without a
   remote use the local base. Record the resolved base commit. Do not pull,
   checkout, stash, reset or commit anything in `$MAIN`; unrelated dirty files
   there do not block creating an isolated worktree from the base commit.
3. Choose an unused branch and path, normally `$BRANCH=task/<slug>` and
   `$WT=<parent>/<repo>.worktrees/<slug>`. Keep `$WT` outside `$MAIN` and outside
   the temporary scratchpad. Respect a project/user worktree location if given.
   Check registered worktrees, branch names and existing directories before
   creating anything. A collision is not permission to overwrite or repurpose
   another task; resume a verified match or choose a new suffix for a new task.
4. Create the parent directory, then run:
   ```bash
   git -C "$MAIN" worktree add -b "$BRANCH" "$WT" "$BASE_REF"
   ```
   Verify the identity above and that the new HEAD equals the recorded base
   commit. Save the record immediately, before launching ralphex. If setup
   partially fails, report the branch/path that exists; do not delete it blindly.

Do not use ralphex's `--worktree`: that worktree has a per-run lifecycle, while
this one must survive planning, execution and review until merge. Check that
the effective ralphex configuration has `use_worktree = false` (the default).
If it is enabled, report the conflicting configuration before launching;
do not silently edit shared configuration or create a nested worktree.

## Existing plans and resumes

- A plan produced by this workflow already has a worktree: reuse it, including
  when invoked from `$MAIN`. Never create another branch between stages.
- For an approved, untouched plan from the old workflow on the default branch
  or in the scratchpad, create the worktree as above, then copy just that plan
  into `$WT/docs/plans/` if needed. Preserve its exact approved contents and the
  original file; report the authoritative new path. Never import other dirty
  files or overwrite a different plan at the destination. A matching committed
  plan already present in the new worktree needs no copy.
- An implementation already on a feature branch must retain that branch's
  commits. Locate its linked worktree; if the branch is not checked out anywhere,
  attach it with `git worktree add "$WT" "$BRANCH"` after verifying task identity.
  If it is checked out in the main checkout, report that migration is needed;
  do not switch the user's checkout or restart from the default branch.
- A plan-only run may leave its accepted plan uncommitted in `$WT`. Before
  execution, inspect the index and working tree. When the selected approved
  plan is the only change, stage **only that path** and commit it on `$BRANCH`.
  This applies to fix plans too: ralphex running on an existing feature branch
  must not be relied on to auto-commit the plan. Never use `git add .` or include
  unrelated files. If the plan is already committed and the tree clean, proceed.
- A failed execution stays in this same worktree with its logs and partial
  changes. Inspect them before resuming; continue the owned interrupted run
  without stashing, resetting or sweeping changes into a preparatory commit.
  Unrelated or unexplained changes stop the resume with a concrete report.

Do not remove the worktree after `plan`, successful execution, a clean review,
a rejected plan, cancellation or any failure. The merge skill owns normal
cleanup; an explicit user request to discard a task is a separate operation.
