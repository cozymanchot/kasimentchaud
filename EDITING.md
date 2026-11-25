# Editing together with Pinegrow

Repository: https://github.com/cozymanchot/kasimentchaud

Both branches contain the complete plain HTML website. The gallery is `vitrine/index.html`, and each product has its own `vitrine/<product-id>/index.html` page.

| Editor | Git branch |
| --- | --- |
| MXUMX | `pinegrow/mx` |
| Other collaborator | `pinegrow/collaborator` |

Each person needs their own local checkout. Open that checkout's folder with **Open project** in Pinegrow. Keep each page's full HTML together, with shared styles in `styles.css` and interactions in `site.js`.

## Your existing folder

The folder already open in Pinegrow is now a Git checkout on `pinegrow/mx`. Save your changes in Pinegrow before committing or publishing them. Unsaved editor changes are not in Git.

## The other person's setup

Run this once on their computer:

```sh
git clone --branch pinegrow/collaborator https://github.com/cozymanchot/kasimentchaud.git cozy-manchot
```

Open the resulting `cozy-manchot` folder as a Pinegrow project.

## Send changes to GitHub

Save the files locally in Pinegrow first (use **Save local** on MXUMX's configured installation). Then use Git in a terminal inside your own checkout. Avoid Pinegrow's GitHub Publish target: its current preview excludes hidden files and proposes deleting `.github/` and `.gitignore` from the remote branch.

```sh
git status
git add --all
git commit -m "Describe the website edits"
git push
```

Review `git status` before adding files. Do not commit passwords, tokens, or other private files.

Before starting another session, if your checkout has no uncommitted changes, run `git pull --ff-only` on your own branch. If it refuses, leave the files as they are and ask for help merging.

## Combine the work

You can edit at the same time on your own computers. Changes appear in GitHub when each person saves, commits, and pushes; this is not a shared live canvas. Ask Codex to review and merge the two branches when ready. Do not merge or publish to `main` until that is intended.

After a merge, both editors should save and commit their local work before updating their checkouts. Shared CSS edits can conflict even when you edited different pages; Git keeps both branches available for review.
