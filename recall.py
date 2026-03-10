#!/usr/bin/env python3
"""
GitHub Art Recall Script (Windows-compatible)
==============================================
Removes all commits made by github_art.py by rewriting git history.
Uses pure Python — no bash, no filter-branch. Works on Windows, Mac, Linux.

Usage:
    python github_art_recall.py                      # interactive, shows commits first
    python github_art_recall.py --confirm            # skip confirmation prompt
    python github_art_recall.py --dry-run            # show what would be removed, no changes
    python github_art_recall.py --since 2025-01-01 --until 2025-12-31
    python github_art_recall.py --pattern "commit"   # custom message pattern

WARNING:
    This rewrites git history. A force-push is required afterward.
    Anyone else with a clone will need to re-clone or hard reset.
"""

import os
import sys
import subprocess
import argparse
import re


def run(cmd, check=True, capture=True):
    """Run a command as a list and return stdout string."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"\n  [ERROR] Command failed: {' '.join(cmd)}")
        print(f"          stderr: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def get_all_commits():
    """Return list of (full_hash, date, subject) oldest-first."""
    log = run(["git", "log", "--format=%H|||%ai|||%s"])
    commits = []
    for line in log.splitlines():
        parts = line.split("|||", 2)
        if len(parts) == 3:
            commits.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return list(reversed(commits))  # oldest first


def get_matching_commits(all_commits, pattern, since=None, until=None):
    """Filter commits by message regex and optional date range."""
    matches = []
    for sha, date, msg in all_commits:
        if not re.search(pattern, msg, re.IGNORECASE):
            continue
        if since and date[:10] < since:
            continue
        if until and date[:10] > until:
            continue
        matches.append((sha, date, msg))
    return matches


def print_commits(commits):
    print(f"\n  Found {len(commits)} matching commit(s):\n")
    for sha, date, msg in commits[:30]:
        print(f"    {sha[:10]}  {date[:10]}  {msg}")
    if len(commits) > 30:
        print(f"    ... and {len(commits) - 30} more")
    print()


def check_clean_repo():
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if result.stdout.strip():
        print("  [WARNING] You have uncommitted changes. Consider stashing first: git stash\n")


def rewrite_history(commits_to_remove, dry_run=False):
    """
    Replay all history except the removed commits using cherry-pick.
    1. Find the oldest commit to remove.
    2. Detach HEAD to its parent.
    3. Cherry-pick every subsequent commit that is NOT in the remove set.
    4. Reset the branch to the new HEAD.
    """
    remove_set = set(sha for sha, _, _ in commits_to_remove)
    all_commits = get_all_commits()  # oldest first

    # Find index of first commit to remove
    first_idx = next((i for i, (sha, _, _) in enumerate(all_commits) if sha in remove_set), None)
    if first_idx is None:
        print("  Could not locate target commits in history.")
        return False

    parent_sha = all_commits[first_idx - 1][0] if first_idx > 0 else None

    # Commits from that point we want to KEEP
    keep = [sha for sha, _, _ in all_commits[first_idx:] if sha not in remove_set]

    if dry_run:
        print(f"  [DRY RUN] Branching point : {parent_sha[:10] if parent_sha else 'root'}")
        print(f"  [DRY RUN] Commits to drop : {len(remove_set)}")
        print(f"  [DRY RUN] Commits to keep : {len(keep)}")
        print("  [DRY RUN] No changes made.\n")
        return True

    branch = run(["git", "branch", "--show-current"]) or "main"
    print(f"  Branch        : {branch}")
    print(f"  Branching point: {parent_sha[:10] if parent_sha else 'root'}")
    print(f"  Dropping      : {len(remove_set)} commit(s)")
    print(f"  Replaying     : {len(keep)} commit(s)\n")

    # Detach HEAD to the parent of the first removed commit
    if parent_sha:
        run(["git", "checkout", "--detach", parent_sha])
    elif keep:
        # Removing from root: detach to first kept commit, skip it in the loop
        run(["git", "checkout", "--detach", keep[0]])
        keep = keep[1:]
    else:
        print("  Nothing to keep and no parent — aborting.")
        return False

    # Cherry-pick each kept commit
    failed = []
    for i, sha in enumerate(keep, 1):
        msg = run(["git", "log", "--format=%s", "-n", "1", sha])
        print(f"  [{i}/{len(keep)}] {sha[:10]}  {msg[:60]}")
        result = subprocess.run(["git", "cherry-pick", sha], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"           ↳ conflict — skipping")
            subprocess.run(["git", "cherry-pick", "--skip"], capture_output=True)
            failed.append(sha)

    # Move the branch label to the new HEAD
    new_head = run(["git", "rev-parse", "HEAD"])
    run(["git", "checkout", "-B", branch, new_head])

    if failed:
        print(f"\n  [WARNING] {len(failed)} commit(s) had conflicts and were skipped.")

    print(f"\n  ✓ Done. {len(remove_set)} art commit(s) removed from local history.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Remove all commits made by github_art.py from your git history."
    )
    parser.add_argument("--pattern", type=str, default=r"^commit \d+$",
                        help='Regex to match commit messages (default: "^commit \\d+$")')
    parser.add_argument("--since", type=str, default=None,
                        help="Only consider commits after this date (YYYY-MM-DD)")
    parser.add_argument("--until", type=str, default=None,
                        help="Only consider commits before this date (YYYY-MM-DD)")
    parser.add_argument("--confirm", action="store_true",
                        help="Skip confirmation prompt")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making any changes")
    parser.add_argument("--no-push", action="store_true",
                        help="Don't force-push after rewriting history")

    args = parser.parse_args()

    print("\n  ╔══════════════════════════════════════╗")
    print("  ║     GitHub Art Recall Script         ║")
    print("  ╚══════════════════════════════════════╝\n")

    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                      capture_output=True).returncode != 0:
        print("  [ERROR] Not inside a git repository.")
        sys.exit(1)

    check_clean_repo()

    print(f"  Scanning history for pattern: {args.pattern}")
    all_commits = get_all_commits()
    print(f"  Total commits in repo: {len(all_commits)}")

    matching = get_matching_commits(all_commits, args.pattern, args.since, args.until)

    if not matching:
        print("\n  No matching commits found.")
        print("  Tip: if you used a custom message in github_art.py, pass --pattern to match it.")
        return

    print_commits(matching)

    if args.dry_run:
        rewrite_history(matching, dry_run=True)
        return

    if not args.confirm:
        print(f"  ⚠️  This will permanently remove {len(matching)} commit(s) and rewrite history.")
        print("  ⚠️  A force-push will be required afterward.\n")
        answer = input("  Proceed? [y/N] ").strip().lower()
        if answer != "y":
            print("\n  Aborted. No changes made.")
            return

    success = rewrite_history(matching)
    if not success:
        return

    # Verify locally
    remaining = get_matching_commits(get_all_commits(), args.pattern, args.since, args.until)
    if remaining:
        print(f"\n  [WARNING] {len(remaining)} commit(s) still found — re-run the script.")
    else:
        print("  ✓ Verified: no art commits remain locally.")

    if not args.no_push:
        print("\n  Force-pushing to origin...")
        result = subprocess.run(
            ["git", "push", "origin", "HEAD", "--force"],
            capture_output=False
        )
        if result.returncode == 0:
            print("  ✓ Force-push successful.")
            print("  ✓ GitHub graph will update within a few minutes.\n")
        else:
            print("\n  [ERROR] Force-push failed. Try manually:")
            print("  git push origin main --force\n")
    else:
        print("\n  Skipping push. Run manually when ready:")
        print("  git push origin main --force\n")


if __name__ == "__main__":
    main()