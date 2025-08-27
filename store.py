from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import sqlite3

class NoActiveTransaction(Exception):
    pass

class WriteConflict(Exception):
    pass

class Store:
    """
    MVCC key-value store with nested transactions and SQLite persistence.
    """

    def __init__(self, initial: Optional[Dict[Any, Any]] = None, sqlite_path: Optional[str] = None) -> None:
        self._versions: Dict[Any, List[Tuple[int, Any]]] = {}
        self._tx_stack: List[Dict[Any, Any]] = []
        self._snapshots: List[int] = []
        self._clock: int = 0
        self._DELETED = object()
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._sqlite_path = sqlite_path

        # Load SQLite if path provided
        if sqlite_path:
            self._sqlite_conn = sqlite3.connect(sqlite_path, check_same_thread=False)
            cur = self._sqlite_conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)")
            self._sqlite_conn.commit()

            # Load existing values into _versions
            for row in cur.execute("SELECT key, value FROM kv"):
                key, val = row
                self._clock += 1
                self._versions.setdefault(key, []).append((self._clock, val))

        # Seed initial state
        if initial:
            for k, v in initial.items():
                self._clock += 1
                self._versions.setdefault(k, []).append((self._clock, v))

    # ---------------- MVCC Helpers ----------------
    def _latest_committed(self, key: Any) -> Optional[Tuple[int, Any]]:
        chain = self._versions.get(key)
        return chain[-1] if chain else None

    def _committed_at_or_before(self, key: Any, ts: int) -> Optional[Any]:
        chain = self._versions.get(key)
        if not chain:
            return None
        for vts, val in reversed(chain):
            if vts <= ts:
                return None if val is self._DELETED else val
        return None

    def _merge_overlay_into(self, src: Dict[Any, Any], dst: Dict[Any, Any]) -> None:
        for k, v in src.items():
            dst[k] = v

    # ---------------- KV API ----------------
    def set(self, key: Any, value: Any) -> None:
        if self._tx_stack:
            self._tx_stack[-1][key] = value
        else:
            self._clock += 1
            self._versions.setdefault(key, []).append((self._clock, value))

    def get(self, key: Any, default: Any = None) -> Any:
        for overlay in reversed(self._tx_stack):
            if key in overlay:
                val = overlay[key]
                return default if val is self._DELETED else val
        if self._tx_stack:
            snap_ts = self._snapshots[-1]
            val = self._committed_at_or_before(key, snap_ts)
            return default if val is None else val
        latest = self._latest_committed(key)
        if latest is None:
            return default
        _, val = latest
        return default if val is self._DELETED else val

    def delete(self, key: Any) -> None:
        if self._tx_stack:
            self._tx_stack[-1][key] = self._DELETED
        else:
            self._clock += 1
            self._versions.setdefault(key, []).append((self._clock, self._DELETED))

    # ---------------- Transactions ----------------
    def begin(self) -> None:
        self._tx_stack.append({})
        self._snapshots.append(self._clock)

    def commit(self) -> None:
        if not self._tx_stack:
            raise NoActiveTransaction()
        top = self._tx_stack.pop()
        snap_ts = self._snapshots.pop()
        if self._tx_stack:
            parent = self._tx_stack[-1]
            self._merge_overlay_into(top, parent)
            return
        # Outermost commit
        for k in top.keys():
            latest = self._latest_committed(k)
            if latest is not None:
                latest_ts, _ = latest
                if latest_ts > snap_ts:
                    raise WriteConflict(f"Conflict on key={k}")
        for k, v in top.items():
            self._clock += 1
            self._versions.setdefault(k, []).append((self._clock, v))

    def rollback(self) -> None:
        if not self._tx_stack:
            raise NoActiveTransaction()
        self._tx_stack.pop()
        self._snapshots.pop()

    # ---------------- Helpers ----------------
    def in_transaction(self) -> bool:
        return bool(self._tx_stack)

    def snapshot(self) -> Dict[Any, Any]:
        result: Dict[Any, Any] = {}
        if self._tx_stack:
            snap_ts = self._snapshots[-1]
            for k, chain in self._versions.items():
                val = self._committed_at_or_before(k, snap_ts)
                if val is not None:
                    result[k] = val
        else:
            for k, chain in self._versions.items():
                ts, val = chain[-1]
                if val is not self._DELETED:
                    result[k] = val
        for overlay in self._tx_stack:
            for k, v in overlay.items():
                if v is self._DELETED:
                    result.pop(k, None)
                else:
                    result[k] = v
        return result

    def flush_to_sqlite(self) -> None:
        if not self._sqlite_conn:
            return
        cur = self._sqlite_conn.cursor()
        for k, chain in self._versions.items():
            val = chain[-1][1]
            if val is self._DELETED:
                cur.execute("DELETE FROM kv WHERE key=?", (k,))
            else:
                cur.execute("REPLACE INTO kv (key, value) VALUES (?, ?)", (k, val))
        self._sqlite_conn.commit()

    def close(self) -> None:
        if self._sqlite_conn:
            self._sqlite_conn.close()
            self._sqlite_conn = None

    def __repr__(self) -> str:
        return f"Store(keys={len(self._versions)}, clock={self._clock}, tx_depth={len(self._tx_stack)})"
