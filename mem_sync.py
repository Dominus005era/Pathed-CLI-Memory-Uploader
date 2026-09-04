#!/usr/bin/env python3
"""
PathEd CLI Memory Uploader - mem_sync.py
A command-line tool that parses markdown notes, hashes their contents,
and maintains an idempotent JSON memory index for PathEd Memory Lane.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import sys
from typing import Dict, Any, Optional

# Ensure UTF-8 output encoding across platforms
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def compute_file_hash(filepath: Path) -> str:
    """
    Computes the SHA-256 hexadecimal digest of a file's raw bytes.
    Uses chunked reading (64 KB) to support arbitrarily large files efficiently.
    """
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def normalize_note_path(filepath: Path) -> str:
    """Returns a clean, forward-slash relative path when possible."""
    try:
        return filepath.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (ValueError, RuntimeError):
        return filepath.as_posix()


def extract_title_from_markdown(filepath: Path) -> str:
    """
    Extracts the first H1 header (# Title) from a markdown file,
    or falls back to the clean filename.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("# ") and not stripped.startswith("## "):
                    return stripped[2:].strip()
    except Exception:
        pass
    return filepath.stem.replace("_", " ").replace("-", " ").title()


def create_memory_entry(filepath: Path) -> Dict[str, Any]:
    """
    Constructs an in-memory memory record from a markdown file,
    capturing its normalized path, SHA-256 hash, size, title, and timestamp.
    """
    resolved_path = filepath.resolve()
    rel_path = normalize_note_path(filepath)
    sha256_hash = compute_file_hash(resolved_path)
    file_stat = resolved_path.stat()
    title = extract_title_from_markdown(resolved_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        "path": rel_path,
        "title": title,
        "sha256": sha256_hash,
        "size_bytes": file_stat.st_size,
        "updated_at": now_iso
    }


def create_parser() -> argparse.ArgumentParser:
    """Creates the top-level argument parser and subcommands."""
    parser = argparse.ArgumentParser(
        prog="mem_sync",
        description="PathEd CLI Memory Uploader: Synchronize markdown study notes with the PathEd memory index.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mem_sync.py add notes/sample_note.md
  python mem_sync.py add notes/ --index custom_memory.json
        """
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 0.2.0"
    )

    subparsers = parser.add_subparsers(
        title="subcommands",
        dest="command",
        required=True,
        help="Available commands"
    )

    # Subcommand: add
    add_parser = subparsers.add_parser(
        "add",
        help="Add and index a markdown note or directory of notes"
    )
    add_parser.add_argument(
        "path",
        type=str,
        help="Path to markdown file or directory containing markdown files"
    )
    add_parser.add_argument(
        "-i", "--index",
        type=str,
        default="memory_index.json",
        help="Path to the JSON memory index file (default: memory_index.json)"
    )

    return parser


def handle_add(args: argparse.Namespace) -> int:
    """Handles the 'add' subcommand: parses and hashes file contents."""
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}", file=sys.stderr)
        return 1

    files_to_process = []
    if target_path.is_file():
        if target_path.suffix.lower() == ".md":
            files_to_process.append(target_path)
        else:
            print(f"Warning: {target_path} is not a markdown (.md) file. Processing anyway.")
            files_to_process.append(target_path)
    elif target_path.is_dir():
        files_to_process.extend(sorted(target_path.glob("**/*.md")))

    if not files_to_process:
        print(f"No markdown files found in {target_path}")
        return 0

    print(f"Processing {len(files_to_process)} note(s)...")
    for fpath in files_to_process:
        entry = create_memory_entry(fpath)
        print(f"  [HASHED] {entry['path']}")
        print(f"           Title  : {entry['title']}")
        print(f"           SHA-256: {entry['sha256']}")
        print(f"           Size   : {entry['size_bytes']} bytes")
        print(f"           Time   : {entry['updated_at']}")

    return 0


def main() -> int:
    """Main CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "add":
        return handle_add(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
