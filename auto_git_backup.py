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

# Master archive repo: will contain a copy of each repo’s contents
# under a subdirectory named after the repo.
MASTER_REPO = "/home/tohme/workshop/master"

# Set to True if you want to push to a remote each time (optional).
PUSH = False       # push individual repos
MASTER_PUSH = False  # push master archive repo


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
    """Commit changes in a single repo, if any."""
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
        commit_result = run_git(repo, "commit", "-m", msg,
                                check=False, capture_output=True)
        if commit_result.returncode != 0:
            print(f"[{repo}] commit returned {commit_result.returncode}: "
                  f"{commit_result.stderr.strip()}",
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


def copy_repo_to_master(repo, master_repo):
    """
    Copy the contents of `repo` (excluding .git) into a subdirectory
    of `master_repo` named after the repo directory.
    """
    repo_path = Path(repo).resolve()
    master_path = Path(master_repo).resolve()

    if not master_path.is_dir():
        print(f"[MASTER] {master_repo} is not a directory", file=sys.stderr)
        return

    if not (master_path / ".git").exists():
        print(f"[MASTER] {master_repo} is not a git repo (no .git)", file=sys.stderr)
        return

    # Avoid crazy recursion: skip if master repo is inside repo or equal
    if master_path == repo_path or master_path.is_relative_to(repo_path):
        print(f"[{repo}] master repo is inside this repo; skipping copy", file=sys.stderr)
        return

    # Destination inside master repo
    dest = master_path / repo_path.name

    # Remove old mirror to keep deletions in sync, then re-copy.
    if dest.exists():
        shutil.rmtree(dest)

    # Copy everything except .git
    shutil.copytree(
        repo_path,
        dest,
        ignore=shutil.ignore_patterns(".git"),
    )
    print(f"[MASTER] mirrored {repo} -> {dest}")


def auto_commit_master(master_repo):
    """Commit changes in the master archive repo, if any."""
    master_path = Path(master_repo)
    if not master_path.is_dir() or not (master_path / ".git").exists():
        print(f"[MASTER] {master_repo} is not a valid git repo", file=sys.stderr)
        return

    if not repo_has_changes(master_repo):
        print("[MASTER] no changes")
        return

    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    msg = f"Auto backup mirror {timestamp}"

    try:
        run_git(master_repo, "add", "-A")
        commit_result = run_git(master_repo, "commit", "-m", msg,
                                check=False, capture_output=True)
        if commit_result.returncode != 0:
            print(f"[MASTER] commit returned {commit_result.returncode}: "
                  f"{commit_result.stderr.strip()}",
                  file=sys.stderr)
            return
        print(f"[MASTER] committed master archive: {msg}")
    except subprocess.CalledProcessError as e:
        print(f"[MASTER] git commit failed: {e}", file=sys.stderr)
        return

    if MASTER_PUSH:
        push_result = run_git(master_repo, "push", check=False, capture_output=True)
        if push_result.returncode == 0:
            print("[MASTER] pushed to remote")
        else:
            print(f"[MASTER] push failed: {push_result.stderr.strip()}",
                  file=sys.stderr)


def main():
    # 1. Commit each individual repo
    for repo in REPOS:
        try:
            auto_commit_repo(repo)
        except Exception as e:
            print(f"[{repo}] unexpected error during per-repo commit: {e}", file=sys.stderr)

    # 2. Mirror each repo into master archive repo
    for repo in REPOS:
        try:
            copy_repo_to_master(repo, MASTER_REPO)
        except Exception as e:
            print(f"[{repo}] unexpected error during master copy: {e}", file=sys.stderr)

    # 3. Commit master archive repo if anything changed
    try:
        auto_commit_master(MASTER_REPO)
    except Exception as e:
        print(f"[MASTER] unexpected error during master commit: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
