# Pinegrow branch synchronization

[![Pinegrow branch sync](https://github.com/cozymanchot/kasimentchaud/actions/workflows/pinegrow-sync.yml/badge.svg)](https://github.com/cozymanchot/kasimentchaud/actions/workflows/pinegrow-sync.yml)

[Open branch warnings and pending edits](https://github.com/cozymanchot/kasimentchaud/issues?q=is%3Aissue+is%3Aopen+label%3Apinegrow-sync)

On pushes to `main`, `pinegrow/mx`, or `pinegrow/collaborator`, the Pinegrow branch sync workflow compares both editor branches with the latest main. It can also be run manually from Actions, with an hourly fallback if a push event is missed. Start time depends on GitHub's Actions queue.

- Behind main: fast-forward to main when possible.
- Both branches have commits: merge main into the editor branch if Git finds no conflicts, preserving personal commits. A merge commit can increase its ahead count.
- Merge conflicts: leave the editor branch unchanged, show a failing check and Actions error, and open/update its `pinegrow-sync` issue with a `sync-conflict` label and the conflicting paths.
- Ahead of main: show a neutral check and Actions warning, and open/update its status issue with an `ahead-of-main` label, commit count, latest commit date with timezone, and comparison link.
- Fully synchronized: show a successful check and close any earlier status issue.

There is one status issue per branch. Updates on a changed head or status post a comment for subscribers; repeated hourly checks do not repeat notifications. Subscribe to those issues to receive GitHub notifications according to your account settings. See the Actions run summary for both branch reports. GitHub's yellow recent-push banner cannot be customized by this workflow.

The workflow never merges personal edits into main or force-pushes. Concurrent editor pushes are retried; protected branches or permission failures produce errors instead of bypassing repository rules. Git considers textual merge conflicts: a clean merge does not guarantee that combined website changes work correctly, so review and test the website before merging personal work into main.

Only GitHub branches are updated. Save and commit local Pinegrow work before pulling the updated branch (`git pull --ff-only` when clean). Unsaved/open editor pages do not update automatically. Keep `.github` files in Pinegrow publishes; if an editor removes the workflow, the hourly run from main will restore it by merging main back in.

The workflow uses the repository's temporary `GITHUB_TOKEN`, with contents, issues, and checks write permissions. No personal token is required. Bot pushes do not trigger additional push workflows or a GitHub Pages build; this workflow reports both branches in the same run to avoid recursion. See [GitHub token behavior](https://docs.github.com/en/actions/concepts/security/github_token).
