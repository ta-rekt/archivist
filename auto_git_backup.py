#!/usr/bin/env python3
import subprocess
import sys
import datetime
from pathlib import Path

# List of folders you want to auto-archive.
# Each must already be a git repo (run git init there once).
REPOS = [
    "/home/tohme/workshop/dummy-folder",
]

# Set to True if you want to push to a remote each time (optional).
PUSH = False


def run_git(repo, *args, check=True, capture_output=False):
    """Run a git command in a given repo and return the CompletedProcess."""
    cmd = ["git", "-C", repo, *args]
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def repo_has_changes(repo):
    """Return True if there are uncommitted changes in the repo."""
    result = run_git(repo, "status", "--porcelain",
                     check=False, capture_output=True)
    if result.returncode != 0:
        print(f"[{repo}] git status failed: {result.stderr.strip()}", file=sys.stderr)
        return False
    return bool(result.stdout.strip())


def auto_commit_repo(repo):
    repo_path = Path(repo)

    if not repo_path.is_dir():
        print(f"[{repo}] not a directory, skipping", file=sys.stderr)
        return

    if not (repo_path / ".git").exists():
        print(f"[{repo}] not a git repo (no .git), skipping", file=sys.stderr)
        return

    if not repo_has_changes(repo):
        print(f"[{repo}] no changes")
        return

    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    msg = f"Auto backup {timestamp}"

    try:
        run_git(repo, "add", "-A")
        # check=False so we don't crash on "nothing to commit" races, etc.
        commit_result = run_git(repo, "commit", "-m", msg, check=False, capture_output=True)
        if commit_result.returncode != 0:
            # Could be "nothing to commit" if state changed; just log and continue.
            print(f"[{repo}] commit returned {commit_result.returncode}: {commit_result.stderr.strip()}",
                  file=sys.stderr)
            return
        print(f"[{repo}] committed changes: {msg}")
    except subprocess.CalledProcessError as e:
        print(f"[{repo}] git commit failed: {e}", file=sys.stderr)
        return

    if PUSH:
        push_result = run_git(repo, "push", check=False, capture_output=True)
        if push_result.returncode == 0:
            print(f"[{repo}] pushed to remote")
        else:
            print(f"[{repo}] push failed: {push_result.stderr.strip()}",
                  file=sys.stderr)


def main():
    for repo in REPOS:
        try:
            auto_commit_repo(repo)
        except Exception as e:
            # Robustness: one broken repo shouldn't kill the whole run.
            print(f"[{repo}] unexpected error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
