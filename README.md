# PathEd CLI Memory Uploader 🧠

A fast, lightweight Python CLI tool that hashes markdown notes and maintains a deterministic, idempotent JSON memory index for **PathEd Memory Lane**.

Part of the **PathEd** ecosystem — helping students convert daily study notes, challenge editorials, and milestone artifacts into permanent, verified learning proofs.

---

## Features

- **CLI Interface**: Intuitive subcommands powered by Python standard library (`argparse`).
- **Markdown Ingestion**: Support for single notes and recursive directory scanning.
- **Cryptographic Hashing**: SHA-256 byte-level digests via `hashlib` to verify note integrity and content drift.
- **Deterministic & Idempotent Upserts**: Predictable, key-sorted JSON index files with no duplicate entries on re-runs.
- **Zero Third-Party Dependencies**: Pure Python 3 standard library.

---

## Installation & Setup

Ensure Python 3.8+ is installed:

```bash
# Clone the repository
git clone https://github.com/Dominus005era/Pathed-CLI-Memory-Uploader.git
cd Pathed-CLI-Memory-Uploader

# Verify CLI runs
python mem_sync.py --help
```

---

## Quickstart

```bash
# View command help
python mem_sync.py add --help

# Add a note (scaffold)
python mem_sync.py add notes/example.md
```
