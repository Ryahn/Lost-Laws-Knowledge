#!/usr/bin/env python3
"""
Scan all files and directories, renaming them to use only alphanumeric
characters and underscores. Replaces spaces and special characters with _,
collapses duplicate underscores, and trims leading/trailing underscores.
"""

import os
import re
import sys
from pathlib import Path


def sanitize_name(name: str, preserve_extension: bool = False) -> str:
    """
    Replace non-alphanumeric characters with underscore, collapse
    consecutive underscores, and strip leading/trailing underscores.
    """
    if preserve_extension and "." in name:
        stem, ext = name.rsplit(".", 1)
        sanitized_stem = _sanitize(stem)
        if not sanitized_stem:
            sanitized_stem = name  # fallback if stem becomes empty
        return f"{sanitized_stem}.{ext}"
    return _sanitize(name)


def _sanitize(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def collect_rename_plan(root: Path, script_path: Path) -> list[tuple[Path, Path]]:
    """
    Walk the tree and build a list of (old_path, new_path) for every
    file and directory that would be renamed. Deepest paths first.
    """
    renames = []
    root = root.resolve()
    script_path = script_path.resolve()

    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        base = Path(dirpath)

        for name in filenames:
            if base / name == script_path:
                continue
            new_name = sanitize_name(name, preserve_extension=True)
            if new_name and new_name != name:
                renames.append((base / name, base / new_name))

        for name in dirnames:
            new_name = sanitize_name(name, preserve_extension=False)
            if new_name and new_name != name:
                renames.append((base / name, base / new_name))

    def depth_key(p: tuple[Path, Path]) -> int:
        return -len(p[0].parts)

    renames.sort(key=depth_key)
    return renames


def apply_renames(renames: list[tuple[Path, Path]], dry_run: bool = True) -> None:
    for old_path, new_path in renames:
        if new_path.exists() and new_path != old_path:
            print(f"  SKIP (target exists): {old_path} -> {new_path}", file=sys.stderr)
            continue
        if dry_run:
            print(f"  {old_path} -> {new_path}")
        else:
            old_path.rename(new_path)
            print(f"  Renamed: {new_path}")


def main() -> None:
    root = Path(__file__).resolve().parent
    script_path = Path(__file__).resolve()

    dry_run = "--execute" not in sys.argv
    if dry_run:
        print("Dry run (no changes). Use --execute to rename.\n")

    renames = collect_rename_plan(root, script_path)
    if not renames:
        print("No files or directories need renaming.")
        return

    print(f"Planned renames ({len(renames)}):\n")
    apply_renames(renames, dry_run=dry_run)


if __name__ == "__main__":
    main()
