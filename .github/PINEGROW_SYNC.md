# Pinegrow branch synchronization

[![Pinegrow branch sync](https://github.com/cozymanchot/kasimentchaud/actions/workflows/pinegrow-sync.yml/badge.svg)](https://github.com/cozymanchot/kasimentchaud/actions/workflows/pinegrow-sync.yml)

[Open branch warnings and pending edits](https://github.com/cozymanchot/kasimentchaud/issues?q=is%3Aissue+is%3Aopen+label%3Apinegrow-sync)

On pushes to `main`, `pinegrow/mx`, or `pinegrow/collaborator`, the Pinegrow branch sync workflow compares both editor branches with the latest main. It can also be run manually from Actions, with an hourly fallback if a push event is missed. Start time depends on GitHub's Actions queue.

- Behind main: fast-forward to main when possible.
- Both branches have commits: merge main into the editor branch if Git finds no conflicts, preserving personal commits. A merge commit can increase its history count without creating pending file changes.
- Merge conflicts: leave the editor branch unchanged, show a failing check and Actions error, and open/update its `pinegrow-sync` issue with a `sync-conflict` label and the conflicting paths.
- Files different from main after synchronization: show a neutral check and Actions warning, and open/update its status issue with an `ahead-of-main` label, changed paths, file count, history counts, latest commit date with timezone, and comparison link.
- Files identical to main: show a successful check and close any earlier status issue, even if the branch has extra commits from synchronization, reverted edits, or previously squashed PRs. No history is rewritten.

There is one status issue per branch. Updates on a changed head or status post a comment for subscribers; repeated hourly checks do not repeat notifications. Subscribe to those issues to receive GitHub notifications according to your account settings. See the Actions run summary for both branch reports. GitHub's yellow recent-push banner cannot be customized by this workflow.

The workflow never merges personal edits into main or force-pushes. Concurrent editor pushes are retried; protected branches or permission failures produce errors instead of bypassing repository rules. Git considers textual merge conflicts: a clean merge does not guarantee that combined website changes work correctly, so review and test the website before merging personal work into main.

## Keep main's history readable

PRs into `main` must use **Squash and merge**, enforced by the repository's main-branch ruleset. GitHub's default squash message uses the PR title with no commit-list body. Write a title describing the actual changes. This creates one new commit on main for the PR's final file changes; it does not import the editor branch's automatic sync commits or their messages.

After a squash merge, the workflow merges the updated main back into both editor branches. Their original commits remain available, and their history-ahead count may grow. Identical files still count as up to date. Old main commits remain unchanged. Never replace squash merging with a local merge pushed to main or rewrite an editor branch to clear its counts.

Only GitHub branches are updated. Save and commit local Pinegrow work before pulling the updated branch (`git pull --ff-only` when clean). Unsaved/open editor pages do not update automatically. The workflow restores its own files and the root `.gitignore` from main if a Pinegrow publish removes or changes them, even when main has no newer commits. These shared infrastructure files should be changed through a PR to main. Website edits are preserved. If the branch's workflow file was removed, the hourly fallback on main performs the repair.

The workflow uses the repository's temporary `GITHUB_TOKEN`, with contents, issues, and checks write permissions. No personal token is required. Bot pushes do not trigger additional push workflows or a GitHub Pages build; this workflow reports both branches in the same run to avoid recursion. See [GitHub token behavior](https://docs.github.com/en/actions/concepts/security/github_token).
