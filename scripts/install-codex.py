#!/usr/bin/env python3
"""Link this checkout's skills into Codex without replacing existing skills."""

import argparse
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest", type=Path,
        default=Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "skills",
        help="skills directory (default: $CODEX_HOME/skills or ~/.codex/skills)",
    )
    parser.add_argument("--dry-run", action="store_true", help="show changes without writing")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent.parent / "skills"
    destination = args.dest.expanduser().resolve()
    skills = sorted(path.parent for path in source.glob("*/SKILL.md"))
    if not skills:
        parser.error(f"No skills found in {source}")

    pending = []
    conflicts = []
    for skill in skills:
        target = destination / skill.name
        if target.is_symlink() and target.resolve() == skill:
            print(f"Already linked: {target}")
        elif target.exists() or target.is_symlink():
            conflicts.append(target)
        else:
            pending.append((skill, target))
    if conflicts:
        for target in conflicts:
            print(f"Conflict (left untouched): {target}", file=sys.stderr)
        return 1

    if not args.dry_run:
        destination.mkdir(parents=True, exist_ok=True)
    for skill, target in pending:
        print(f"{'Would link' if args.dry_run else 'Link'}: {target} -> {skill}")
        if not args.dry_run:
            target.symlink_to(skill, target_is_directory=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
