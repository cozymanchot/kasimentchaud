"""Preserve branch history, merge main when clean, report through GitHub."""

import json
import os
import subprocess

BRANCHES = ("pinegrow/mx", "pinegrow/collaborator")


def git(*args, check=True):
    return subprocess.run(
        ["git", *args], text=True, capture_output=True, check=check
    )


def counts(base, head):
    behind, ahead = git("rev-list", "--left-right", "--count", f"{base}...{head}").stdout.split()
    return int(behind), int(ahead)


def sync_branch(branch):
    # Retry if another editor pushes while a merge is being prepared.
    # Ordinary pushes reject stale updates; no force push or history rewrite.
    for _ in range(3):
        git("fetch", "origin", "+refs/heads/main:refs/remotes/origin/main",
            f"+refs/heads/{branch}:refs/remotes/origin/{branch}")
        main = git("rev-parse", "origin/main").stdout.strip()
        head = git("rev-parse", f"origin/{branch}").stdout.strip()
        behind, ahead = counts(main, head)
        if behind == 0:
            return {"state": "ahead" if ahead else "current", "head": head,
                    "main": main, "behind": behind, "ahead": ahead}
        git("checkout", "--detach", head)
        result = git("-c", "user.name=github-actions[bot]", "-c",
                     "user.email=41898282+github-actions[bot]@users.noreply.github.com",
                     "merge", "--no-edit", main, check=False)
        if result.returncode:
            files = git("diff", "--name-only", "--diff-filter=U").stdout.splitlines()
            git("merge", "--abort", check=False)
            if not files:
                raise RuntimeError(f"Merge failed: {result.stderr or result.stdout}")
            return {"state": "conflict", "head": head, "main": main,
                    "behind": behind, "ahead": ahead, "files": files}
        pushed = git("push", "origin", f"HEAD:refs/heads/{branch}", check=False)
        if pushed.returncode == 0:
            head = git("rev-parse", "HEAD").stdout.strip()
            behind, ahead = counts(main, head)
            return {"state": "ahead" if ahead else "current", "head": head,
                    "main": main, "behind": behind, "ahead": ahead}
    raise RuntimeError(f"Could not update {branch}; branch moved or GitHub rejected the push")


def api(method, path, payload=None):
    args = ["gh", "api", "--method", method, path]
    if payload is not None:
        args += ["--input", "-"]
    response = subprocess.run(args, input=json.dumps(payload) if payload is not None else None,
                              text=True, capture_output=True, check=True)
    return json.loads(response.stdout) if response.stdout.strip() else None


def report(branch, status):
    repo = os.environ["GH_REPO"]
    root = f"repos/{repo}"
    latest = git("show", "-s", "--format=%cI", status["head"]).stdout.strip()
    main_date = git("show", "-s", "--format=%cI", status["main"]).stdout.strip()
    state = status["state"]
    heading = {"current": "Up to date", "ahead": "Edits waiting to merge",
               "conflict": "Merge conflicts — manual action needed", "error": "Sync failed"}[state]
    title = f"{branch}: {heading} ({status['ahead']} ahead, {status['behind']} behind main)"
    compare = f"https://github.com/{repo}/compare/main...{branch}"
    body = f"""<!-- pinegrow-sync:{branch} -->
## {heading}

| Branch | Commits ahead of main | Commits behind main | Latest commit date (with timezone) |
| --- | ---: | ---: | --- |
| `{branch}` | {status['ahead']} | {status['behind']} | {latest} |

Main latest commit: {main_date} (`{status['main'][:7]}`).
Branch head: `{status['head'][:7]}`.

[Compare changes / create a pull request]({compare}) · [Sync workflow](https://github.com/{repo}/actions/workflows/pinegrow-sync.yml)

Main is merged automatically only when Git can merge without conflicts. Pinegrow edits are never automatically merged into main. Ahead counts include merge commits; they describe history, not how many files changed.
"""
    if status.get("files"):
        body += "\nConflicting files (branch was left unchanged):\n" + "\n".join(
            f"- `{file}`" for file in status["files"])
    if status.get("error"):
        body += "\nSync could not complete. Inspect the linked workflow logs.\n"
    # Find only the bot-owned status issue for this branch, including closed ones.
    issues = []
    page = 1
    while True:
        batch = api("GET", f"{root}/issues?state=all&labels=pinegrow-sync&per_page=100&page={page}")
        issues += batch
        if len(batch) < 100:
            break
        page += 1
    marker = f"<!-- pinegrow-sync:{branch} -->"
    existing = next((i for i in issues if not i.get("pull_request")
                     and i["user"]["type"] == "Bot" and i.get("body", "").startswith(marker)), None)
    labels = ["pinegrow-sync"] + (["sync-conflict"] if state in ("conflict", "error")
                                  else ["ahead-of-main"] if state == "ahead" else [])
    if existing:
        changed = existing["body"] != body or existing["state"] != ("closed" if state == "current" else "open")
        if changed:
            api("PATCH", f"{root}/issues/{existing['number']}", {
                "title": title, "body": body, "labels": labels,
                "state": "closed" if state == "current" else "open"})
            # Notify subscribers once per new branch/main head or state, not on hourly rechecks.
            api("POST", f"{root}/issues/{existing['number']}/comments", {
                "body": f"{title}\n\nLatest branch commit: {latest}. [Compare changes]({compare})."})
    elif state != "current":
        api("POST", f"{root}/issues", {"title": title, "body": body, "labels": labels})
    run_url = f"https://github.com/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    api("POST", f"{root}/check-runs", {
        "name": f"Pinegrow sync / {branch}", "head_sha": status["head"],
        "status": "completed", "conclusion": "failure" if state in ("conflict", "error")
        else "neutral" if state == "ahead" else "success", "details_url": run_url,
        "output": {"title": title, "summary": body}})
    if state != "current":
        print(f"::{'error' if state in ('conflict', 'error') else 'warning'}::{title}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as file:
            file.write(body + "\n\n---\n\n")


def main():
    root = f"repos/{os.environ['GH_REPO']}"
    labels = api("GET", f"{root}/labels?per_page=100")
    for name, color in (("pinegrow-sync", "1d76db"), ("sync-conflict", "d73a4a"),
                        ("ahead-of-main", "fbca04")):
        if not any(label["name"] == name for label in labels):
            api("POST", f"{root}/labels", {"name": name, "color": color})
    failed = False
    for branch in BRANCHES:
        try:
            status = sync_branch(branch)
        except Exception as error:
            print(f"::error::Sync failed for {branch}: {error}")
            # Fetch normally creates these refs even when a protected branch rejects the push.
            head = git("rev-parse", f"origin/{branch}").stdout.strip()
            base = git("rev-parse", "origin/main").stdout.strip()
            behind, ahead = counts(base, head)
            status = {"state": "error", "error": True, "head": head,
                      "main": base, "behind": behind, "ahead": ahead}
        try:
            report(branch, status)
        except Exception as error:
            print(f"::error::Reporting failed for {branch}: {error}")
            failed = True
        failed |= status["state"] in ("conflict", "error")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
