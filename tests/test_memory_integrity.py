"""Regression checks for repeated sleep, provenance, and schema upgrades."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from anima.store import MemoryStore, SCHEMA


class MemoryIntegrityTest(unittest.TestCase):
    def test_decay_is_independent_of_sleep_frequency(self):
        now = [1_000_000.0]
        stores = [MemoryStore(":memory:", lambda _: [1.0], lambda: now[0]) for _ in range(2)]
        try:
            ids = [s.remember("semantic", "Weather changes", importance=0.5) for s in stores]
            for _ in range(10):
                now[0] += 86400
                stores[0].decay_and_forget()
            stores[1].decay_and_forget()
            self.assertAlmostEqual(stores[0].get(ids[0]).strength, stores[1].get(ids[1]).strength)
            before = stores[0].get(ids[0]).strength
            stores[0].decay_and_forget()
            self.assertEqual(before, stores[0].get(ids[0]).strength)
        finally:
            for s in stores:
                s.close()

    def test_fiction_is_excluded_from_waking_recall(self):
        store = MemoryStore(":memory:", lambda _: [1.0])
        try:
            dream = store.remember("dream", "Birds speak", epistemic="fiction")
            store.remember("episodic", "Birds sing", epistemic="observation")
            self.assertNotIn(dream, [m.id for m in store.recall("Birds")])
            self.assertIsNotNone(store.get(dream))
        finally:
            store.close()

    def test_similar_claims_with_different_provenance_do_not_merge(self):
        store = MemoryStore(":memory:", lambda _: [1.0])
        try:
            observed = store.remember("semantic", "A storm arrived", source="sensor", epistemic="observation")
            imagined = store.remember("semantic", "A storm might arrive", source="self", epistemic="hypothesis")
            self.assertNotEqual(observed, imagined)
        finally:
            store.close()

    def test_legacy_database_upgrades_and_preserves_self_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mind.db"
            db = sqlite3.connect(path)
            db.executescript(SCHEMA)
            db.execute("INSERT INTO self_model VALUES (1, 'Before migration', 7, 100)")
            db.commit()
            db.close()
            store = MemoryStore(path, lambda _: [1.0])
            try:
                self.assertEqual(store.set_self_model("After migration"), 8)
                rows = store.db.execute("SELECT text FROM self_model_history ORDER BY version").fetchall()
                self.assertEqual([r[0] for r in rows], ["Before migration", "After migration"])
                self.assertIn("last_decay_ts", {r[1] for r in store.db.execute("PRAGMA table_info(memories)")})
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
