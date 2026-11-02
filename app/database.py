"""SQLite database for task tracking, notes, and configuration."""
import sqlite3
import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from contextlib import contextmanager

from app.config import DB_PATH, BACKUP_DIR, ensure_dirs


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        ensure_dirs()
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    @contextmanager
    def _cursor(self):
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _create_tables(self):
        with self._cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    day INTEGER PRIMARY KEY,
                    phase INTEGER NOT NULL,
                    phase_name TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    concepts TEXT NOT NULL,
                    exercise TEXT NOT NULL,
                    resources TEXT NOT NULL,
                    estimated_minutes INTEGER NOT NULL,
                    deliverable TEXT NOT NULL,
                    advanced_task TEXT NOT NULL DEFAULT '',
                    reflection_prompt TEXT NOT NULL DEFAULT '',
                    starter_code TEXT NOT NULL DEFAULT '',
                    solution_code TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'pending',
                    completed_at TEXT,
                    scheduled_date TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    day INTEGER PRIMARY KEY,
                    text TEXT NOT NULL DEFAULT '',
                    tags TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS weekly_reviews (
                    week INTEGER PRIMARY KEY,
                    reflection TEXT NOT NULL DEFAULT '',
                    learnings TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                )
            """)

    # ── Config ─────────────────────────────────────────

    def get_config(self, key: str, default: str = "") -> str:
        row = self._conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_config(self, key: str, value: str):
        with self._cursor() as cur:
            cur.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (key, value),
            )

    def get_start_date(self) -> str:
        d = self.get_config("start_date", "")
        if not d:
            d = date.today().isoformat()
            self.set_config("start_date", d)
        return d

    def get_today_day_number(self) -> int:
        start = date.fromisoformat(self.get_start_date())
        delta = (date.today() - start).days + 1
        if delta < 1:
            return 0
        if delta > 90:
            return 91
        return delta

    # ── Tasks ──────────────────────────────────────────

    def populate_tasks(self, curriculum: list[dict]):
        start = date.fromisoformat(self.get_start_date())
        with self._cursor() as cur:
            for item in curriculum:
                scheduled = (start + timedelta(days=item["day"] - 1)).isoformat()
                cur.execute(
                    """INSERT OR IGNORE INTO tasks
                       (day, phase, phase_name, topic, concepts, exercise,
                        resources, estimated_minutes, deliverable,
                        advanced_task, reflection_prompt,
                        starter_code, solution_code, scheduled_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item["day"],
                        item["phase"],
                        item["phase_name"],
                        item["topic"],
                        json.dumps(item["concepts"], ensure_ascii=False),
                        item["exercise"],
                        json.dumps(item["resources"], ensure_ascii=False),
                        item["estimated_minutes"],
                        item["deliverable"],
                        item.get("advanced_task", ""),
                        item.get("reflection_prompt", ""),
                        item.get("starter_code", ""),
                        item.get("solution_code", ""),
                        scheduled,
                    ),
                )

    def _row_to_dict(self, row) -> dict:
        if row is None:
            return {}
        d = dict(row)
        if "concepts" in d:
            try:
                d["concepts"] = json.loads(d["concepts"])
            except (json.JSONDecodeError, TypeError):
                d["concepts"] = []
        if "resources" in d:
            try:
                d["resources"] = json.loads(d["resources"])
            except (json.JSONDecodeError, TypeError):
                d["resources"] = []
        return d

    def get_task(self, day: int) -> dict:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE day = ?", (day,)
        ).fetchone()
        return self._row_to_dict(row)

    def get_all_tasks(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM tasks ORDER BY day").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_tasks_by_status(self, status: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY day", (status,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_tasks_in_range(self, start_day: int, end_day: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE day BETWEEN ? AND ? ORDER BY day",
            (start_day, end_day),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_task_status(self, day: int, status: str):
        ts = datetime.now().isoformat() if status == "completed" else None
        with self._cursor() as cur:
            cur.execute(
                "UPDATE tasks SET status = ?, completed_at = ? WHERE day = ?",
                (status, ts, day),
            )

    def reschedule_task(self, from_day: int, to_day: int):
        start = date.fromisoformat(self.get_start_date())
        new_date = (start + timedelta(days=to_day - 1)).isoformat()
        with self._cursor() as cur:
            cur.execute(
                "UPDATE tasks SET scheduled_date = ? WHERE day = ?",
                (new_date, from_day),
            )

    def get_overdue_tasks(self) -> list[dict]:
        today_num = self.get_today_day_number()
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE day < ? AND status = 'pending' ORDER BY day",
            (today_num,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ── Progress ───────────────────────────────────────

    def get_progress_stats(self) -> dict:
        stats = {"completed": 0, "postponed": 0, "skipped": 0, "pending": 0, "total": 90}
        rows = self._conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ).fetchall()
        for r in rows:
            stats[r["status"]] = r["cnt"]
        return stats

    def get_streak(self) -> int:
        today_num = self.get_today_day_number()
        streak = 0
        for d in range(today_num, 0, -1):
            task = self.get_task(d)
            if task.get("status") == "completed":
                streak += 1
            else:
                if d == today_num:
                    continue
                break
        return streak

    def get_weekly_stats(self, week: int) -> dict:
        start_day = (week - 1) * 7 + 1
        end_day = min(week * 7, 90)
        tasks = self.get_tasks_in_range(start_day, end_day)
        stats = {"completed": 0, "postponed": 0, "skipped": 0, "pending": 0}
        for t in tasks:
            s = t.get("status", "pending")
            stats[s] = stats.get(s, 0) + 1
        return stats

    # ── Notes ──────────────────────────────────────────

    def save_note(self, day: int, text: str, tags: str = ""):
        with self._cursor() as cur:
            cur.execute(
                """INSERT OR REPLACE INTO notes (day, text, tags, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (day, text, tags, datetime.now().isoformat()),
            )

    def get_note(self, day: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM notes WHERE day = ?", (day,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_notes(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM notes ORDER BY day").fetchall()
        return [dict(r) for r in rows]

    def search_notes(self, query: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM notes WHERE text LIKE ? OR tags LIKE ? ORDER BY day",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Weekly Reviews ─────────────────────────────────

    def save_weekly_review(self, week: int, reflection: str, learnings: str):
        with self._cursor() as cur:
            cur.execute(
                """INSERT OR REPLACE INTO weekly_reviews
                   (week, reflection, learnings, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (week, reflection, learnings, datetime.now().isoformat()),
            )

    def get_weekly_review(self, week: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM weekly_reviews WHERE week = ?", (week,)
        ).fetchone()
        return dict(row) if row else None

    # ── Backup / Export ────────────────────────────────

    def backup(self, path: str = ""):
        if not path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = str(BACKUP_DIR / f"planner_backup_{ts}.db")
        self._conn.execute("VACUUM")
        shutil.copy2(str(self.db_path), path)
        return path

    def export_json(self, path: str):
        data = {
            "tasks": self.get_all_tasks(),
            "notes": self.get_all_notes(),
            "weekly_reviews": [],
            "progress": self.get_progress_stats(),
            "start_date": self.get_start_date(),
        }
        for w in range(1, 14):
            rev = self.get_weekly_review(w)
            if rev:
                data["weekly_reviews"].append(rev)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def close(self):
        if self._conn:
            self._conn.close()
