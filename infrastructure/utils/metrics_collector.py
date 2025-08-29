import sqlite3
import threading
import atexit
from pathlib import Path

class MetricsCollector:
    def __init__(self, db_dir: Path, db_filename: str = "fly_app.db") -> None:
        self._lock = threading.Lock()
        db_path = db_dir / db_filename
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS download_bytes (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total INTEGER NOT NULL
            )
        """)
        self._conn.execute("INSERT OR IGNORE INTO download_bytes (id, total) VALUES (1, 0)")
        self._conn.commit()

        self._download_bytes = 0
        atexit.register(self._close)

    def add_network_bytes(self, n: int) -> None:
        self._download_bytes = n
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE download_bytes SET total = total + ? WHERE id = 1",
                (n,)
            )

    @property
    def network_bytes(self) -> int:
        cur = self._conn.execute("SELECT total FROM download_bytes WHERE id = 1")
        return cur.fetchone()[0]

    @property
    def download_bytes(self) -> int:
        return self._download_bytes

    def _close(self):
        self._conn.close()
