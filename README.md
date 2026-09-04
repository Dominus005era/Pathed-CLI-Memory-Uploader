# PathEd CLI Memory Uploader 🧠

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PathEd Verified](https://img.shields.io/badge/PathEd-Memory%20Lane-6c63ff.svg)](https://path-ed0.vercel.app/)

A high-performance, idempotent command-line tool built in pure Python that parses markdown study notes, computes cryptographic SHA-256 byte digests, and maintains an atomic, deterministic JSON memory index for **PathEd Memory Lane**.

---

## 🌟 Overview & Purpose

In the **PathEd** ecosystem:
- **The Roadmap** defines where you are going.
- **The Challenges** test what you are doing.
- **Memory Lane** preserves how far you have come.

The **CLI Memory Uploader** (`mem_sync.py`) bridges offline markdown notes, local LeetCode editorials, and system design research with the PathEd platform. It ensures every milestone note is indexed with cryptographic content verification and zero duplicate entries.

---

## 🚀 Key Features

- ⚡ **Zero Third-Party Dependencies**: Pure Python 3 standard library (`hashlib`, `json`, `argparse`, `pathlib`, `tempfile`).
- 🔐 **Cryptographic SHA-256 Content Hashing**: Hashes raw file bytes using chunked streaming (64 KB chunks) to support notes of any size.
- 🔁 **Idempotent Upserts**: Safely re-run against any directory or file. Unchanged notes remain untouched (`[UNCHANGED]`), modified notes update their hash and timestamp (`[UPDATED]`), and new files are registered (`[NEW]`).
- 🛡️ **Atomic Persistence**: Writes index files via tempfiles and `os.replace` + `fsync` to prevent index corruption during interrupted executions.
- 📋 **Deterministic JSON Index**: Output keys are sorted alphabetically with standard 2-space indentation for clean Git diffs and reproducible builds.
- 🔍 **Integrity Verification**: Built-in `verify` subcommand detects content drift or missing files between disk and index.

---

## 📦 Project Structure

```
Pathed-CLI-Memory-Uploader/
├── mem_sync.py               # Main CLI entrypoint
├── memory_index.json         # Persisted JSON memory index
├── test_mem_sync.py          # Automated unit test suite
├── notes/                    # Sample markdown study notes
│   ├── sample_note.md        # Binary Search Trees note
│   └── system_design_caching.md # Distributed Caching note
├── .gitignore                # Python and IDE ignore patterns
└── README.md                 # Complete documentation & reflection
```

---

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Dominus005era/Pathed-CLI-Memory-Uploader.git
   cd Pathed-CLI-Memory-Uploader
   ```

2. **Verify Python 3 installation:**
   ```bash
   python --version
   ```

3. **Verify CLI accessibility:**
   ```bash
   python mem_sync.py --help
   ```

---

## 💻 CLI Commands & Usage

### 1. Adding / Syncing Notes (`add`)

Index a single markdown file:
```bash
python mem_sync.py add notes/sample_note.md
```

Recursively scan and index an entire notes folder:
```bash
python mem_sync.py add notes/
```

Specify a custom memory index location:
```bash
python mem_sync.py add notes/ --index custom_index.json
```

**Sample Output:**
```text
Indexing 2 note(s) into 'memory_index.json'...
  [NEW]        notes/sample_note.md
               Title  : Binary Search Trees (BST) 🌳
               SHA-256: 3bd734c92a848366...80c80a4e
               Size   : 769 bytes
  [NEW]        notes/system_design_caching.md
               Title  : Distributed Caching Architecture ⚙️
               SHA-256: 219d50a785ee8523...7c7da435
               Size   : 907 bytes

Completed: 2 new, 0 updated, 0 unchanged.
Memory index saved: memory_index.json (total entries: 2)
```

### 2. Idempotent Re-runs

Running `add` again on unchanged notes:
```bash
python mem_sync.py add notes/
```

**Output:**
```text
Indexing 2 note(s) into 'memory_index.json'...
  [UNCHANGED]  notes/sample_note.md
               Title  : Binary Search Trees (BST) 🌳
               SHA-256: 3bd734c92a848366...80c80a4e
               Size   : 769 bytes
  [UNCHANGED]  notes/system_design_caching.md
               Title  : Distributed Caching Architecture ⚙️
               SHA-256: 219d50a785ee8523...7c7da435
               Size   : 907 bytes

Completed: 0 new, 0 updated, 2 unchanged.
Memory index saved: memory_index.json (total entries: 2)
```

### 3. Listing Indexed Memories (`list`)

```bash
python mem_sync.py list
```

**Output:**
```text
PathEd Memory Index: memory_index.json (2 total notes)
================================================================================
Path                           Title                     SHA-256 (prefix)   Size  
--------------------------------------------------------------------------------
notes/sample_note.md           Binary Search Trees (BS   3bd734c92a848366   769B  
notes/system_design_caching.md Distributed Caching Arc   219d50a785ee8523   907B  
================================================================================
```

### 4. Integrity Check (`verify`)

Validates that disk files have not been modified or corrupted outside the CLI:
```bash
python mem_sync.py verify
```

**Output:**
```text
Verifying 2 indexed files against disk...
  [OK]        notes/sample_note.md (Checksum matches: 3bd734c92a84...)
  [OK]        notes/system_design_caching.md (Checksum matches: 219d50a785ee...)

Verification SUCCESS: All files match their recorded SHA-256 signatures.
```

---

## 📄 JSON Index Schema

The persisted `memory_index.json` maintains a deterministic, key-sorted schema:

```json
{
  "entries": {
    "notes/sample_note.md": {
      "created_at": "2026-09-04T06:39:04.561829+00:00",
      "path": "notes/sample_note.md",
      "sha256": "3bd734c92a84836625292bbafcefaf801eab55079d588a22710a265280c80a4e",
      "size_bytes": 769,
      "title": "Binary Search Trees (BST) 🌳",
      "updated_at": "2026-09-04T06:39:04.561829+00:00"
    },
    "notes/system_design_caching.md": {
      "created_at": "2026-09-04T06:39:04.563049+00:00",
      "path": "notes/system_design_caching.md",
      "sha256": "219d50a785ee8523d73694e36ce7981114dc680bf1e009746d1e45dd7c7da435",
      "size_bytes": 907,
      "title": "Distributed Caching Architecture ⚙️",
      "updated_at": "2026-09-04T06:39:04.563049+00:00"
    }
  },
  "total_notes": 2,
  "updated_at": "2026-09-04T06:39:16.490410+00:00",
  "version": "1.0.0"
}
```

---

## 🧪 Automated Testing

Run the built-in test suite:

```bash
python -m unittest test_mem_sync.py
```

**Results:**
```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.018s

OK
```

The tests cover:
1. `test_compute_file_hash_determinism`: Validates that identical bytes produce the exact same 64-character SHA-256 digest.
2. `test_extract_title`: Tests markdown `# Header` parsing and fallback mechanisms.
3. `test_idempotent_upsert`: Tests state transitions (`NEW` $\to$ `UNCHANGED` $\to$ `UPDATED`) ensuring no duplication.
4. `test_atomic_persistence`: Validates temporary-file swap and deterministic dictionary key sorting.

---

## 🧠 Design Reflection (Hashing & Idempotency)

### 1. Why SHA-256 Hashing?
File metadata such as `mtime` (last modified timestamp) or `st_size` (file size) is brittle: copying a file across systems or touching a file updates the timestamp without altering the actual knowledge content. Conversely, different edits might coincidentally yield the same file size.

Using `hashlib.sha256` on raw file bytes provides a **cryptographically collision-resistant fingerprint**:
- Content-addressed verification guarantees that if the hash hasn't changed, the knowledge artifact has not changed.
- Reading in 64 KB chunks ensures low memory overhead even for large notes or rich documents with embedded base64 diagrams.
- It forms the foundational verification layer for PathEd's **audited career proofs**, ensuring candidate artifacts cannot be trivially falsified.

### 2. Why Idempotent Upserts?
In study workflows, students constantly run sync commands or integrate automated git hooks. If an uploader were non-idempotent:
- Re-running would create redundant duplicate index rows, inflating milestone metrics.
- Timestamps would get falsely updated, corrupting historical learning curves in PathEd's Memory Lane.

By keying entries by normalized relative path and comparing the computed SHA-256 against the recorded hash, `mem_sync.py` achieves strict **idempotency**:
- **Unchanged files** preserve their original `created_at` and `updated_at` timestamps.
- **Modified files** update their content signature and `updated_at` timestamp while preserving their initial creation lineage.
- **Atomic file writes** (`os.replace` + `fsync`) guarantee that an unexpected shutdown never leaves a half-written, corrupt JSON file on disk.

---

## 📄 License

MIT License © 2026 Dominus005era & PathEd
