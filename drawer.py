#!/usr/bin/env python3
"""
GitHub Contribution Graph Text Painter
=======================================
Usage:
    python github_art.py --year 2024 --text "HI"
    python github_art.py --year 2025 --text "LOL" --commits-per-cell 5

How it works:
  - GitHub's contribution graph has 7 rows (Sun–Sat) and ~53 columns (weeks).
  - The first column starts on the weekday of Jan 1 of the given year.
  - Each "cell" in the font maps to one day; we make commits on that day to light it up.
"""

import os
import argparse
from datetime import datetime, timedelta
import random

# --------------------------------------------------------------------------
# 5x7 pixel font (each letter is 5 columns wide, 7 rows tall)
# Row 0 = top row (Sunday in GitHub graph), Row 6 = bottom (Saturday)
# 1 = filled cell, 0 = empty cell
# --------------------------------------------------------------------------
FONT = {
    'A': [
        [0,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,1,1,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
    ],
    'B': [
        [1,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,1,1,0,0],
    ],
    'C': [
        [0,1,1,1,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [0,1,1,1,0],
    ],
    'D': [
        [1,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,1,1,0,0],
    ],
    'E': [
        [1,1,1,1,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,1,1,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,1,1,1,0],
    ],
    'F': [
        [1,1,1,1,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,1,1,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
    ],
    'G': [
        [0,1,1,1,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,1,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [0,1,1,1,0],
    ],
    'H': [
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,1,1,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
    ],
    'I': [
        [0,1,1,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,1,1,1,0],
    ],
    'J': [
        [0,0,1,1,0],
        [0,0,0,1,0],
        [0,0,0,1,0],
        [0,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [0,1,1,0,0],
    ],
    'K': [
        [1,0,0,1,0],
        [1,0,1,0,0],
        [1,1,0,0,0],
        [1,1,0,0,0],
        [1,0,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
    ],
    'L': [
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,1,1,1,0],
    ],
    'M': [
        [1,0,0,0,1],
        [1,1,0,1,1],
        [1,0,1,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
    ],
    'N': [
        [1,0,0,1,0],
        [1,1,0,1,0],
        [1,0,1,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
    ],
    'O': [
        [0,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [0,1,1,0,0],
    ],
    'P': [
        [1,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,1,1,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
    ],
    'Q': [
        [0,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,1,1,0],
        [1,0,0,1,0],
        [0,1,1,0,1],
    ],
    'R': [
        [1,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,1,1,0,0],
        [1,0,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
    ],
    'S': [
        [0,1,1,1,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [0,1,1,0,0],
        [0,0,0,1,0],
        [0,0,0,1,0],
        [1,1,1,0,0],
    ],
    'T': [
        [1,1,1,1,1],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
    ],
    'U': [
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [0,1,1,0,0],
    ],
    'V': [
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [0,1,0,1,0],
        [0,1,0,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
    ],
    'W': [
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,1,0,1],
        [1,0,1,0,1],
        [1,1,0,1,1],
        [1,0,0,0,1],
    ],
    'X': [
        [1,0,0,0,1],
        [0,1,0,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,1,0,1,0],
        [1,0,0,0,1],
        [1,0,0,0,1],
    ],
    'Y': [
        [1,0,0,0,1],
        [0,1,0,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
    ],
    'Z': [
        [1,1,1,1,0],
        [0,0,0,1,0],
        [0,0,1,0,0],
        [0,1,0,0,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,1,1,1,0],
    ],
    '0': [
        [0,1,1,0,0],
        [1,0,0,1,0],
        [1,0,1,1,0],
        [1,1,0,1,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [0,1,1,0,0],
    ],
    '1': [
        [0,1,0,0,0],
        [1,1,0,0,0],
        [0,1,0,0,0],
        [0,1,0,0,0],
        [0,1,0,0,0],
        [0,1,0,0,0],
        [1,1,1,0,0],
    ],
    '2': [
        [0,1,1,0,0],
        [1,0,0,1,0],
        [0,0,0,1,0],
        [0,0,1,0,0],
        [0,1,0,0,0],
        [1,0,0,0,0],
        [1,1,1,1,0],
    ],
    '3': [
        [1,1,1,0,0],
        [0,0,0,1,0],
        [0,0,0,1,0],
        [0,1,1,0,0],
        [0,0,0,1,0],
        [0,0,0,1,0],
        [1,1,1,0,0],
    ],
    '4': [
        [0,0,1,1,0],
        [0,1,0,1,0],
        [1,0,0,1,0],
        [1,1,1,1,0],
        [0,0,0,1,0],
        [0,0,0,1,0],
        [0,0,0,1,0],
    ],
    '5': [
        [1,1,1,1,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,1,1,0,0],
        [0,0,0,1,0],
        [0,0,0,1,0],
        [1,1,1,0,0],
    ],
    '6': [
        [0,1,1,1,0],
        [1,0,0,0,0],
        [1,0,0,0,0],
        [1,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [0,1,1,0,0],
    ],
    '7': [
        [1,1,1,1,0],
        [0,0,0,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,1,0,0,0],
        [0,1,0,0,0],
        [0,1,0,0,0],
    ],
    '8': [
        [0,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [0,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [0,1,1,0,0],
    ],
    '9': [
        [0,1,1,0,0],
        [1,0,0,1,0],
        [1,0,0,1,0],
        [0,1,1,1,0],
        [0,0,0,1,0],
        [0,0,0,1,0],
        [0,1,1,0,0],
    ],
    ' ': [
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
    ],
    '!': [
        [0,1,0,0,0],
        [0,1,0,0,0],
        [0,1,0,0,0],
        [0,1,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,1,0,0,0],
    ],
    '?': [
        [0,1,1,0,0],
        [1,0,0,1,0],
        [0,0,0,1,0],
        [0,0,1,0,0],
        [0,1,0,0,0],
        [0,0,0,0,0],
        [0,1,0,0,0],
    ],
}


def text_to_grid(text):
    """
    Convert a string to a 7-row grid of columns.
    Returns a list of columns, where each column is a list of 7 ints (0 or 1).
    Letters are separated by a 1-column gap.
    """
    text = text.upper()
    columns = []
    for i, ch in enumerate(text):
        glyph = FONT.get(ch, FONT[' '])
        # Each glyph is 7 rows x 5 cols; transpose to get list of columns
        for col_idx in range(5):
            col = [glyph[row][col_idx] for row in range(7)]
            columns.append(col)
        # 1-column gap between characters (except after last)
        if i < len(text) - 1:
            columns.append([0] * 7)
    return columns


def get_commit_days(year, text, offset_weeks=1):
    """
    Returns a list of datetime objects on which commits should be made.

    GitHub's grid:
      - Row 0 = Sunday, Row 6 = Saturday
      - Column 0 starts on the weekday of Jan 1
      - The grid shows Sun=0 ... Sat=6
    """
    jan1 = datetime(year, 1, 1)
    # GitHub uses Sunday=0 ... Saturday=6
    # Python's weekday(): Mon=0 ... Sun=6  →  convert:
    jan1_dow = (jan1.weekday() + 1) % 7  # Sun=0, Mon=1, ..., Sat=6

    grid_columns = text_to_grid(text)
    commit_dates = []

    for col_idx, col in enumerate(grid_columns):
        week = col_idx + offset_weeks  # shift right by offset_weeks
        for row in range(7):
            if col[row] == 1:
                # day_offset from Jan 1:
                day_offset = week * 7 + row - jan1_dow
                target_date = jan1 + timedelta(days=day_offset)
                if target_date.year == year:
                    commit_dates.append(target_date)

    return commit_dates


def preview_grid(year, text, offset_weeks=1):
    """Print an ASCII preview of what will be drawn."""
    jan1 = datetime(year, 1, 1)
    jan1_dow = (jan1.weekday() + 1) % 7
    grid_columns = text_to_grid(text)

    total_weeks = len(grid_columns) + offset_weeks + 1
    grid = [[' '] * total_weeks for _ in range(7)]

    for col_idx, col in enumerate(grid_columns):
        week = col_idx + offset_weeks
        for row in range(7):
            if col[row] == 1:
                day_offset = week * 7 + row - jan1_dow
                target_date = jan1 + timedelta(days=day_offset)
                if target_date.year == year and week < total_weeks:
                    grid[row][week] = '█'

    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    print(f"\n  Preview for '{text}' in {year}:")
    print("  " + "─" * (total_weeks + 2))
    for row in range(7):
        print(f"  {days[row]}│{''.join(grid[row])}│")
    print("  " + "─" * (total_weeks + 2))
    print()


def make_commits(year, text, offset_weeks=1, commits_per_cell=3, fp="text_art", dry_run=False):
    commit_dates = get_commit_days(year, text, offset_weeks)

    if not commit_dates:
        print("No valid commit dates found! Text might be out of range for the year.")
        return

    print(f"  Will make commits on {len(commit_dates)} unique days ({len(commit_dates) * commits_per_cell} total commits).")

    if dry_run:
        print("  [DRY RUN] No actual commits made.")
        return

    commit_num = 0
    for date in sorted(commit_dates):
        for _ in range(commits_per_cell):
            commit_num += 1
            hour = random.randint(9, 20)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            comdate = date.replace(hour=hour, minute=minute, second=second)
            comdate_str = comdate.strftime("%Y-%m-%dT%H:%M:%S")

            with open(fp, "a") as f:
                f.write(f"commit {commit_num}\n")

            os.system("git add .")
            os.environ["GIT_AUTHOR_DATE"] = comdate_str
            os.environ["GIT_COMMITTER_DATE"] = comdate_str
            os.system(f'git commit -m "commit {commit_num}" --date="{comdate_str}"')
            print(f"  [{commit_num}] Committed on {comdate_str}")

    print("\n  Pushing to origin main...")
    os.system("git push origin main")
    print("  Done! Check your GitHub profile in a few minutes.")


def main():
    parser = argparse.ArgumentParser(
        description="Draw text on your GitHub contribution graph by making commits on the right days."
    )
    parser.add_argument("--year", type=int, default=datetime.now().year,
                        help="Target year (default: current year)")
    parser.add_argument("--text", type=str, required=True,
                        help="Text to draw (A-Z, 0-9, spaces supported)")
    parser.add_argument("--offset", type=int, default=1,
                        help="How many weeks to offset from the left edge (default: 1)")
    parser.add_argument("--commits-per-cell", type=int, default=3,
                        help="Number of commits per highlighted cell (default: 3, more = darker green)")
    parser.add_argument("--file", type=str, default="text_art",
                        help="Filename to write dummy content to (default: text_art)")
    parser.add_argument("--preview", action="store_true",
                        help="Only show a preview, don't make any commits")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without committing")

    args = parser.parse_args()

    preview_grid(args.year, args.text, args.offset)

    if args.preview:
        print("  Preview-only mode. Use --dry-run or remove --preview to commit.")
        return

    make_commits(
        year=args.year,
        text=args.text,
        offset_weeks=args.offset,
        commits_per_cell=args.commits_per_cell,
        fp=args.file,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()