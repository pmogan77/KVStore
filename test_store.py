import unittest
import tempfile
import os
from store import Store, NoActiveTransaction

class TestStore(unittest.TestCase):
    def setUp(self):
        # Temporary SQLite file per test
        fd, self.sqlite_file = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.store = Store(sqlite_path=self.sqlite_file)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.sqlite_file):
            os.remove(self.sqlite_file)

    # ---------------- Basic CRUD ----------------
    def test_set_and_get(self):
        self.store.set("a", 1)
        self.assertEqual(self.store.get("a"), 1)
        self.assertIsNone(self.store.get("b"))

    def test_delete(self):
        self.store.set("a", 1)
        self.store.delete("a")
        self.assertIsNone(self.store.get("a"))

    # ---------------- Transactions ----------------
    def test_simple_transaction_commit(self):
        self.store.begin()
        self.store.set("x", 42)
        self.assertEqual(self.store.get("x"), 42)  # visible in tx
        self.store.commit()
        self.assertEqual(self.store.get("x"), 42)

    def test_simple_transaction_rollback(self):
        self.store.begin()
        self.store.set("x", 42)
        self.store.rollback()
        self.assertIsNone(self.store.get("x"))

    def test_nested_transaction_commit(self):
        self.store.begin()
        self.store.set("a", 1)
        self.store.begin()
        self.store.set("b", 2)
        self.store.commit()  # inner
        self.store.commit()  # outer
        self.assertEqual(self.store.get("a"), 1)
        self.assertEqual(self.store.get("b"), 2)

    def test_nested_transaction_rollback(self):
        self.store.begin()
        self.store.set("a", 1)
        self.store.begin()
        self.store.set("b", 2)
        self.store.rollback()  # inner
        self.store.commit()    # outer
        self.assertEqual(self.store.get("a"), 1)
        self.assertIsNone(self.store.get("b"))

    # ---------------- SQLite persistence ----------------
    def test_flush_and_reload(self):
        self.store.set("k1", "v1")
        self.store.flush_to_sqlite()
        store2 = Store(sqlite_path=self.sqlite_file)
        self.assertEqual(store2.get("k1"), "v1")
        store2.close()

    # ---------------- Snapshot helper ----------------
    def test_snapshot(self):
        self.store.set("a", 10)
        self.store.set("b", 20)
        snap = self.store.snapshot()
        self.assertEqual(snap, {"a": 10, "b": 20})
        self.store.begin()
        self.store.set("c", 30)
        snap2 = self.store.snapshot()
        self.assertEqual(snap2, {"a": 10, "b": 20, "c": 30})

    # ---------------- Edge cases ----------------
    def test_no_active_transaction_commit(self):
        with self.assertRaises(NoActiveTransaction):
            self.store.commit()

    def test_no_active_transaction_rollback(self):
        with self.assertRaises(NoActiveTransaction):
            self.store.rollback()


if __name__ == "__main__":
    unittest.main()
