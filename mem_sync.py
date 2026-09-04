#!/usr/bin/env python3
"""
PathEd CLI Memory Uploader - mem_sync.py
A command-line tool that parses markdown notes, hashes their contents,
and maintains an idempotent, atomic JSON memory index for PathEd Memory Lane.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Dict, Any, List, Tuple, Optional

# Ensure UTF-8 output encoding across platforms (handles emoji on Windows stdout)
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
    or falls back to a title-cased clean filename.
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


def load_memory_index(index_path: Path) -> Dict[str, Any]:
    """
    Loads an existing JSON memory index, or initializes an empty schema.
    """
    if not index_path.exists():
        return {
            "version": "1.0.0",
            "updated_at": None,
            "total_notes": 0,
            "entries": {}
        }

    try:
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "entries" not in data or not isinstance(data["entries"], dict):
                data["entries"] = {}
            return data
    except Exception as e:
        print(f"Warning: Corrupted index at {index_path} ({e}). Initializing clean index.", file=sys.stderr)
        return {
            "version": "1.0.0",
            "updated_at": None,
            "total_notes": 0,
            "entries": {}
        }


def save_memory_index_atomic(index_path: Path, data: Dict[str, Any]) -> None:
    """
    Persists the memory index deterministically and atomically.
    1. Sorts all dictionary keys deterministically.
    2. Writes to a temporary file in the target directory.
    3. Forces disk sync via fsync.
    4. Atomically replaces the target file via os.replace.
    """
    index_path = index_path.resolve()
    target_dir = index_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    # Update summary metadata
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    data["total_notes"] = len(data["entries"])

    # Deterministic JSON string with sorted keys and trailing newline
    serialized_json = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    # Write atomically via tempfile in the same folder
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=target_dir,
        prefix=".mem_sync_tmp_",
        suffix=".json"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(serialized_json)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, index_path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def upsert_note(
    index_data: Dict[str, Any],
    filepath: Path
) -> Tuple[str, Dict[str, Any]]:
    """
    Idempotently upserts a note into the index.
    Returns (status, entry), where status is 'NEW', 'UPDATED', or 'UNCHANGED'.
    """
    resolved_path = filepath.resolve()
    rel_path = normalize_note_path(filepath)
    new_hash = compute_file_hash(resolved_path)
    file_stat = resolved_path.stat()
    title = extract_title_from_markdown(resolved_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    entries = index_data["entries"]
    existing = entries.get(rel_path)

    if existing is not None:
        if existing.get("sha256") == new_hash:
            # File content is completely identical -> Idempotent no-op
            return "UNCHANGED", existing

        # File content was modified -> Update hash, stats, timestamp while preserving created_at
        existing["sha256"] = new_hash
        existing["size_bytes"] = file_stat.st_size
        existing["title"] = title
        existing["updated_at"] = now_iso
        return "UPDATED", existing

    # Brand new entry
    new_entry = {
        "path": rel_path,
        "title": title,
        "sha256": new_hash,
        "size_bytes": file_stat.st_size,
        "created_at": now_iso,
        "updated_at": now_iso
    }
    entries[rel_path] = new_entry
    return "NEW", new_entry


def create_parser() -> argparse.ArgumentParser:
    """Creates the top-level argument parser and subcommands."""
    parser = argparse.ArgumentParser(
        prog="mem_sync",
        description="PathEd CLI Memory Uploader: Synchronize markdown study notes with the PathEd memory index.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  add       Add and index a markdown note or directory of notes
  list      List all indexed memory notes
  verify    Verify integrity of indexed files against on-disk hashes

Examples:
  python mem_sync.py add notes/sample_note.md
  python mem_sync.py add notes/
  python mem_sync.py list
  python mem_sync.py verify
        """
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 0.3.0"
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

    # Subcommand: list
    list_parser = subparsers.add_parser(
        "list",
        help="List all memory notes currently stored in the index"
    )
    list_parser.add_argument(
        "-i", "--index",
        type=str,
        default="memory_index.json",
        help="Path to the JSON memory index file (default: memory_index.json)"
    )

    # Subcommand: verify
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify on-disk file checksums against index hashes"
    )
    verify_parser.add_argument(
        "-i", "--index",
        type=str,
        default="memory_index.json",
        help="Path to the JSON memory index file (default: memory_index.json)"
    )

    return parser


def handle_add(args: argparse.Namespace) -> int:
    """Handles the 'add' subcommand: parses, hashes, and persists notes."""
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}", file=sys.stderr)
        return 1

    files_to_process: List[Path] = []
    if target_path.is_file():
        if target_path.suffix.lower() == ".md":
            files_to_process.append(target_path)
        else:
            print(f"Warning: '{target_path}' is not a .md file. Processing as markdown.", file=sys.stderr)
            files_to_process.append(target_path)
    elif target_path.is_dir():
        files_to_process.extend(sorted(target_path.glob("**/*.md")))

    if not files_to_process:
        print(f"No markdown (.md) files found in {target_path}")
        return 0

    index_path = Path(args.index)
    index_data = load_memory_index(index_path)

    stats = {"NEW": 0, "UPDATED": 0, "UNCHANGED": 0}
    print(f"Indexing {len(files_to_process)} note(s) into '{index_path}'...")

    for fpath in files_to_process:
        status, entry = upsert_note(index_data, fpath)
        stats[status] += 1

        badge = f"[{status}]"
        print(f"  {badge:<12} {entry['path']}")
        print(f"               Title  : {entry['title']}")
        print(f"               SHA-256: {entry['sha256'][:16]}...{entry['sha256'][-8:]}")
        print(f"               Size   : {entry['size_bytes']} bytes")

    # Persist atomically
    save_memory_index_atomic(index_path, index_data)

    print(f"\nCompleted: {stats['NEW']} new, {stats['UPDATED']} updated, {stats['UNCHANGED']} unchanged.")
    print(f"Memory index saved: {index_path} (total entries: {len(index_data['entries'])})")
    return 0


def handle_list(args: argparse.Namespace) -> int:
    """Displays formatted list of all indexed notes."""
    index_path = Path(args.index)
    if not index_path.exists():
        print(f"No index file found at: {index_path}")
        return 0

    index_data = load_memory_index(index_path)
    entries = index_data.get("entries", {})

    if not entries:
        print(f"Memory index '{index_path}' is empty.")
        return 0

    print(f"PathEd Memory Index: {index_path} ({len(entries)} total notes)")
    print("=" * 80)
    print(f"{'Path':<30} {'Title':<25} {'SHA-256 (prefix)':<18} {'Size':<6}")
    print("-" * 80)
    for path, data in sorted(entries.items()):
        short_title = data.get("title", "")[:23]
        short_hash = data.get("sha256", "")[:16]
        size = f"{data.get('size_bytes', 0)}B"
        print(f"{path:<30} {short_title:<25} {short_hash:<18} {size:<6}")
    print("=" * 80)
    return 0


def handle_verify(args: argparse.Namespace) -> int:
    """Verifies each indexed file against its on-disk SHA-256 digest."""
    index_path = Path(args.index)
    if not index_path.exists():
        print(f"Error: Index file not found at: {index_path}", file=sys.stderr)
        return 1

    index_data = load_memory_index(index_path)
    entries = index_data.get("entries", {})

    if not entries:
        print(f"Memory index '{index_path}' is empty. Nothing to verify.")
        return 0

    print(f"Verifying {len(entries)} indexed files against disk...")
    all_valid = True

    for path_str, data in sorted(entries.items()):
        disk_path = Path(path_str)
        if not disk_path.exists():
            print(f"  [MISSING]   {path_str} (File deleted or moved from disk)")
            all_valid = False
            continue

        disk_hash = compute_file_hash(disk_path)
        recorded_hash = data.get("sha256")

        if disk_hash == recorded_hash:
            print(f"  [OK]        {path_str} (Checksum matches: {disk_hash[:12]}...)")
        else:
            print(f"  [DRIFTED]   {path_str}")
            print(f"              Index hash: {recorded_hash}")
            print(f"              Disk  hash: {disk_hash}")
            all_valid = False

    if all_valid:
        print("\nVerification SUCCESS: All files match their recorded SHA-256 signatures.")
        return 0
    else:
        print("\nVerification WARNING: One or more files have drifted or are missing.", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "add":
        return handle_add(args)
    elif args.command == "list":
        return handle_list(args)
    elif args.command == "verify":
        return handle_verify(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
