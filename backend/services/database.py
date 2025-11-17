import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class Database:
    """Lightweight SQLite layer for demo-ready sample data."""

    def __init__(self, db_path: str, seed_path: str):
        self.db_path = db_path
        self.seed_path = seed_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._ensure_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    avatar TEXT,
                    tagline TEXT,
                    bio TEXT,
                    career_path TEXT,
                    location TEXT
                );

                CREATE TABLE IF NOT EXISTS student_metrics (
                    student_id TEXT PRIMARY KEY,
                    lessons_completed INTEGER,
                    mastery REAL,
                    streak INTEGER,
                    focus_time INTEGER,
                    avg_time INTEGER,
                    confidence TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(id)
                );

                CREATE TABLE IF NOT EXISTS student_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    course_id TEXT,
                    track_id TEXT,
                    progress REAL,
                    mastery REAL,
                    units_completed INTEGER,
                    next_unit INTEGER,
                    FOREIGN KEY(student_id) REFERENCES students(id)
                );

                CREATE TABLE IF NOT EXISTS student_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    title TEXT,
                    summary TEXT,
                    badge TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(id)
                );

                CREATE TABLE IF NOT EXISTS lesson_history (
                    id TEXT PRIMARY KEY,
                    student_id TEXT,
                    course_id TEXT,
                    track_id TEXT,
                    unit INTEGER,
                    content TEXT,
                    questions TEXT,
                    created_at TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(id)
                );
                """
            )
        self._seed_if_needed()

    def _seed_if_needed(self):
        with self._connect() as conn:
            cur = conn.execute("SELECT COUNT(*) AS count FROM students")
            count = cur.fetchone()["count"]
            if count:
                return

        seed_file = Path(self.seed_path)
        if not seed_file.exists():
            return

        payload = json.loads(seed_file.read_text())
        students = payload.get("students", [])
        metrics = payload.get("metrics", [])
        tracks = payload.get("tracks", [])
        projects = payload.get("projects", [])

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO students (id, name, avatar, tagline, bio, career_path, location)
                VALUES (:id, :name, :avatar, :tagline, :bio, :career_path, :location)
                """,
                students,
            )
            conn.executemany(
                """
                INSERT INTO student_metrics (student_id, lessons_completed, mastery, streak, focus_time, avg_time, confidence)
                VALUES (:student_id, :lessons_completed, :mastery, :streak, :focus_time, :avg_time, :confidence)
                """,
                metrics,
            )
            conn.executemany(
                """
                INSERT INTO student_tracks (student_id, course_id, track_id, progress, mastery, units_completed, next_unit)
                VALUES (:student_id, :course_id, :track_id, :progress, :mastery, :units_completed, :next_unit)
                """,
                tracks,
            )
            conn.executemany(
                """
                INSERT INTO student_projects (student_id, title, summary, badge)
                VALUES (:student_id, :title, :summary, :badge)
                """,
                projects,
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_students(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM students ORDER BY name")
            return [dict(row) for row in cur.fetchall()]

    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_primary_student(self) -> Optional[Dict[str, Any]]:
        students = self.list_students()
        return students[0] if students else None

    def get_metrics(self, student_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM student_metrics WHERE student_id = ?", (student_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else {}

    def get_tracks(self, student_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT * FROM student_tracks
                WHERE student_id = ?
                ORDER BY mastery DESC
                """,
                (student_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_projects(self, student_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM student_projects WHERE student_id = ?",
                (student_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def store_lesson_snapshot(
        self,
        lesson_id: str,
        student_id: str,
        course_id: str,
        track_id: str,
        unit: int,
        content: str,
        questions: List[Dict[str, Any]],
    ):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lesson_history
                (id, student_id, course_id, track_id, unit, content, questions, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lesson_id,
                    student_id,
                    course_id,
                    track_id,
                    unit,
                    content,
                    json.dumps(questions),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def recent_lessons(self, student_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT * FROM lesson_history
                WHERE student_id = ?
                ORDER BY datetime(created_at) DESC
                LIMIT ?
                """,
                (student_id, limit),
            )
            return [dict(row) for row in cur.fetchall()]

    def update_career_path(self, student_id: str, career_path: str):
        if not student_id or not career_path:
            return
        with self._connect() as conn:
            conn.execute(
                "UPDATE students SET career_path = ? WHERE id = ?",
                (career_path, student_id),
            )
            conn.commit()

    def upsert_metrics(self, student_id: str, payload: Dict[str, Any]):
        if not student_id or not payload:
            return
        columns = [
            "lessons_completed",
            "mastery",
            "streak",
            "focus_time",
            "avg_time",
            "confidence",
        ]
        existing = self.get_metrics(student_id)
        data = {col: payload.get(col, existing.get(col)) for col in columns}
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO student_metrics
                (student_id, lessons_completed, mastery, streak, focus_time, avg_time, confidence)
                VALUES (:student_id, :lessons_completed, :mastery, :streak, :focus_time, :avg_time, :confidence)
                ON CONFLICT(student_id) DO UPDATE SET
                    lessons_completed=excluded.lessons_completed,
                    mastery=excluded.mastery,
                    streak=excluded.streak,
                    focus_time=excluded.focus_time,
                    avg_time=excluded.avg_time,
                    confidence=excluded.confidence
                """,
                {"student_id": student_id, **data},
            )
            conn.commit()

    def ensure_student(self, student_id: str, name: str, career_path: str = "", location: str = "") -> Dict[str, Any]:
        """Create a student row if missing with default metrics."""
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cur.fetchone()
            if row:
                return dict(row)

            conn.execute(
                """
                INSERT INTO students (id, name, avatar, tagline, bio, career_path, location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    name,
                    "pl",
                    "New PathLearn explorer",
                    "",
                    career_path,
                    location,
                ),
            )
            conn.execute(
                """
                INSERT INTO student_metrics (student_id, lessons_completed, mastery, streak, focus_time, avg_time, confidence)
                VALUES (?, 0, 0.0, 0, 0, 0, 'low')
                """,
                (student_id,),
            )
            conn.commit()
            return {
                "id": student_id,
                "name": name,
                "avatar": "pl",
                "career_path": career_path,
                "location": location,
            }
