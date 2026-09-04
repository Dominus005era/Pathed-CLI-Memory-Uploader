"""
Unit tests for PathEd CLI Memory Uploader (mem_sync.py).
Run with: python -m unittest test_mem_sync.py
"""

import json
from pathlib import Path
import tempfile
import unittest

from mem_sync import (
    compute_file_hash,
    extract_title_from_markdown,
    load_memory_index,
    save_memory_index_atomic,
    upsert_note
)


class TestMemSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_compute_file_hash_determinism(self):
        """Verify that identical content produces identical SHA-256 hash."""
        f1 = self.root / "note1.md"
        f2 = self.root / "note2.md"
        content = b"# Test Note\nHello PathEd Memory Lane!"
        f1.write_bytes(content)
        f2.write_bytes(content)

        h1 = compute_file_hash(f1)
        h2 = compute_file_hash(f2)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_extract_title(self):
        """Verify H1 header extraction and fallback behavior."""
        f = self.root / "note.md"
        f.write_text("# Graph Algorithms\nContent here...", encoding="utf-8")
        self.assertEqual(extract_title_from_markdown(f), "Graph Algorithms")

        f_no_h1 = self.root / "dynamic_programming.md"
        f_no_h1.write_text("No header here...", encoding="utf-8")
        self.assertEqual(extract_title_from_markdown(f_no_h1), "Dynamic Programming")

    def test_idempotent_upsert(self):
        """Verify that re-running upsert on unchanged files does not alter entry or duplicate."""
        f = self.root / "sample.md"
        f.write_text("# Idempotency Test\nTest body", encoding="utf-8")

        index_data = {"version": "1.0.0", "entries": {}}

        # First run: should be NEW
        status1, entry1 = upsert_note(index_data, f)
        self.assertEqual(status1, "NEW")
        created_at = entry1["created_at"]
        initial_hash = entry1["sha256"]

        # Second run with same content: should be UNCHANGED
        status2, entry2 = upsert_note(index_data, f)
        self.assertEqual(status2, "UNCHANGED")
        self.assertEqual(entry2["created_at"], created_at)
        self.assertEqual(entry2["sha256"], initial_hash)
        self.assertEqual(len(index_data["entries"]), 1)

        # Third run after content modification: should be UPDATED
        f.write_text("# Idempotency Test\nModified body content!", encoding="utf-8")
        status3, entry3 = upsert_note(index_data, f)
        self.assertEqual(status3, "UPDATED")
        self.assertEqual(entry3["created_at"], created_at)
        self.assertNotEqual(entry3["sha256"], initial_hash)

    def test_atomic_persistence(self):
        """Verify that memory index file is persisted with sorted keys deterministically."""
        index_file = self.root / "test_index.json"
        data = {
            "version": "1.0.0",
            "entries": {
                "b.md": {"title": "B"},
                "a.md": {"title": "A"}
            }
        }
        save_memory_index_atomic(index_file, data)
        self.assertTrue(index_file.exists())

        loaded = json.loads(index_file.read_text(encoding="utf-8"))
        self.assertEqual(loaded["total_notes"], 2)
        # Ensure keys are sorted deterministically
        keys = list(loaded.keys())
        self.assertEqual(keys, sorted(keys))


if __name__ == "__main__":
    unittest.main()
