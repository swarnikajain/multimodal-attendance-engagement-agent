"""
SQLite database management module for Multimodal Attendance & Engagement Agent.
Provides schema definition, connection handling, and CRUD operations.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from config import DATABASE_PATH


def get_connection(db_path=DATABASE_PATH) -> sqlite3.Connection:
    """Create a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DATABASE_PATH):
    """Initialize the database tables if they do not exist."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Participants table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            participant_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            email TEXT,
            course TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            course_name TEXT,
            date TEXT NOT NULL,
            duration_sec REAL DEFAULT 0.0,
            status TEXT DEFAULT 'configured',
            is_demo INTEGER DEFAULT 0,
            video_path TEXT,
            audio_path TEXT,
            sampling_interval_sec REAL DEFAULT 1.0,
            total_frames_analyzed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            notes TEXT
        )
    """)

    # Attendance records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            track_id TEXT NOT NULL,
            participant_id TEXT,
            first_seen_sec REAL DEFAULT 0.0,
            last_seen_sec REAL DEFAULT 0.0,
            duration_observed_sec REAL DEFAULT 0.0,
            frame_detections_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Provisional',
            is_confirmed INTEGER DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
            FOREIGN KEY (participant_id) REFERENCES participants (participant_id) ON DELETE SET NULL
        )
    """)

    # Engagement timeline table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS engagement_timeline (
            timeline_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp_sec REAL NOT NULL,
            people_count INTEGER DEFAULT 0,
            motion_score REAL DEFAULT 0.0,
            gaze_score REAL,
            audio_energy REAL,
            speech_active INTEGER,
            composite_engagement REAL DEFAULT 0.0,
            available_signals TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
        )
    """)

    # Session recommendations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_recommendations (
            rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            category TEXT NOT NULL,
            observation TEXT NOT NULL,
            supporting_metric TEXT NOT NULL,
            time_window TEXT,
            suggestion TEXT NOT NULL,
            limitation_caveat TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
        )
    """)

    # Session metrics summary table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_metrics_summary (
            session_id TEXT PRIMARY KEY,
            average_engagement REAL DEFAULT 0.0,
            peak_engagement REAL DEFAULT 0.0,
            lowest_engagement REAL DEFAULT 0.0,
            total_detected_tracks INTEGER DEFAULT 0,
            confirmed_attendees INTEGER DEFAULT 0,
            speech_ratio REAL DEFAULT 0.0,
            silence_ratio REAL DEFAULT 0.0,
            data_quality_score REAL DEFAULT 100.0,
            data_quality_notes TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ---------------- Participant Operations ----------------

def add_participant(participant_id: str, display_name: str, email: str = "", course: str = "", db_path=DATABASE_PATH) -> bool:
    """Add a new participant. Returns True on success, False if already exists."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """INSERT INTO participants (participant_id, display_name, email, course, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (participant_id.strip(), display_name.strip(), email.strip(), course.strip(), datetime.now().isoformat())
            )
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_participant(participant_id: str, display_name: str, email: str = "", course: str = "", db_path=DATABASE_PATH) -> bool:
    """Update participant details."""
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """UPDATE participants SET display_name = ?, email = ?, course = ? WHERE participant_id = ?""",
            (display_name.strip(), email.strip(), course.strip(), participant_id.strip())
        )
        updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_participant(participant_id: str, db_path=DATABASE_PATH) -> bool:
    """Delete a participant record."""
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute("DELETE FROM participants WHERE participant_id = ?", (participant_id.strip(),))
        deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_participant(participant_id: str, db_path=DATABASE_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve participant by ID."""
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM participants WHERE participant_id = ?", (participant_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_participants(search_query: str = "", db_path=DATABASE_PATH) -> List[Dict[str, Any]]:
    """List participants with optional search query filter."""
    conn = get_connection(db_path)
    if search_query:
        query = f"%{search_query.strip()}%"
        cursor = conn.execute(
            """SELECT * FROM participants
               WHERE participant_id LIKE ? OR display_name LIKE ? OR email LIKE ? OR course LIKE ?
               ORDER BY participant_id ASC""",
            (query, query, query, query)
        )
    else:
        cursor = conn.execute("SELECT * FROM participants ORDER BY participant_id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ---------------- Session Operations ----------------

def create_session(session_id: str, title: str, course_name: str, date: str,
                   duration_sec: float = 0.0, is_demo: int = 0, video_path: str = None,
                   audio_path: str = None, sampling_interval_sec: float = 1.0,
                   notes: str = "", db_path=DATABASE_PATH) -> bool:
    """Create a new session record."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """INSERT INTO sessions 
                   (session_id, title, course_name, date, duration_sec, status, is_demo,
                    video_path, audio_path, sampling_interval_sec, created_at, notes)
                   VALUES (?, ?, ?, ?, ?, 'configured', ?, ?, ?, ?, ?, ?)""",
                (session_id, title, course_name, date, duration_sec, is_demo,
                 video_path, audio_path, sampling_interval_sec, datetime.now().isoformat(), notes)
            )
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_session_status(session_id: str, status: str, duration_sec: float = None,
                          total_frames: int = None, db_path=DATABASE_PATH):
    """Update session processing status and summary attributes."""
    conn = get_connection(db_path)
    with conn:
        if duration_sec is not None and total_frames is not None:
            conn.execute(
                """UPDATE sessions SET status = ?, duration_sec = ?, total_frames_analyzed = ?
                   WHERE session_id = ?""",
                (status, duration_sec, total_frames, session_id)
            )
        else:
            conn.execute("UPDATE sessions SET status = ? WHERE session_id = ?", (status, session_id))
    conn.close()


def list_sessions(db_path=DATABASE_PATH) -> List[Dict[str, Any]]:
    """List all sessions ordered by creation date descending."""
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_session(session_id: str, db_path=DATABASE_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve session details by ID."""
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(session_id: str, db_path=DATABASE_PATH) -> bool:
    """Delete a session and all associated records."""
    conn = get_connection(db_path)
    with conn:
        conn.execute("DELETE FROM attendance_records WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM engagement_timeline WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM session_recommendations WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM session_metrics_summary WHERE session_id = ?", (session_id,))
        cursor = conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# ---------------- Attendance Operations ----------------

def save_attendance_records(records: List[Dict[str, Any]], db_path=DATABASE_PATH):
    """Insert batch of attendance track records."""
    conn = get_connection(db_path)
    with conn:
        for r in records:
            conn.execute(
                """INSERT INTO attendance_records 
                   (session_id, track_id, participant_id, first_seen_sec, last_seen_sec,
                    duration_observed_sec, frame_detections_count, status, is_confirmed, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.get("session_id"), r.get("track_id"), r.get("participant_id"),
                 r.get("first_seen_sec", 0.0), r.get("last_seen_sec", 0.0),
                 r.get("duration_observed_sec", 0.0), r.get("frame_detections_count", 0),
                 r.get("status", "Provisional"), r.get("is_confirmed", 0), r.get("notes", ""))
            )
    conn.close()


def get_attendance_records(session_id: str, db_path=DATABASE_PATH) -> List[Dict[str, Any]]:
    """Retrieve attendance records joined with participant display names."""
    conn = get_connection(db_path)
    cursor = conn.execute(
        """SELECT a.*, p.display_name, p.course
           FROM attendance_records a
           LEFT JOIN participants p ON a.participant_id = p.participant_id
           WHERE a.session_id = ?
           ORDER BY a.track_id ASC""",
        (session_id,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def map_track_to_participant(record_id: int, participant_id: Optional[str],
                             is_confirmed: int = 1, status: Optional[str] = None,
                             db_path=DATABASE_PATH) -> bool:
    """Manually map an anonymous track to a registered participant and confirm attendance."""
    conn = get_connection(db_path)
    with conn:
        if status:
            cursor = conn.execute(
                """UPDATE attendance_records
                   SET participant_id = ?, is_confirmed = ?, status = ?
                   WHERE record_id = ?""",
                (participant_id, is_confirmed, status, record_id)
            )
        else:
            cursor = conn.execute(
                """UPDATE attendance_records
                   SET participant_id = ?, is_confirmed = ?
                   WHERE record_id = ?""",
                (participant_id, is_confirmed, record_id)
            )
        updated = cursor.rowcount > 0
    conn.close()
    return updated


# ---------------- Engagement Timeline Operations ----------------

def save_engagement_timeline(session_id: str, timeline_points: List[Dict[str, Any]], db_path=DATABASE_PATH):
    """Batch insert engagement timeline data."""
    conn = get_connection(db_path)
    with conn:
        for pt in timeline_points:
            signals = json.dumps(pt.get("available_signals", []))
            conn.execute(
                """INSERT INTO engagement_timeline
                   (session_id, timestamp_sec, people_count, motion_score, gaze_score,
                    audio_energy, speech_active, composite_engagement, available_signals)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, pt.get("timestamp_sec", 0.0), pt.get("people_count", 0),
                 pt.get("motion_score", 0.0), pt.get("gaze_score"),
                 pt.get("audio_energy"), pt.get("speech_active"),
                 pt.get("composite_engagement", 0.0), signals)
            )
    conn.close()


def get_engagement_timeline(session_id: str, db_path=DATABASE_PATH) -> List[Dict[str, Any]]:
    """Retrieve engagement timeline points for a session."""
    conn = get_connection(db_path)
    cursor = conn.execute(
        """SELECT * FROM engagement_timeline
           WHERE session_id = ?
           ORDER BY timestamp_sec ASC""",
        (session_id,)
    )
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        if d.get("available_signals"):
            try:
                d["available_signals"] = json.loads(d["available_signals"])
            except Exception:
                d["available_signals"] = []
        rows.append(d)
    conn.close()
    return rows


# ---------------- Recommendations Operations ----------------

def save_recommendations(session_id: str, recommendations: List[Dict[str, Any]], db_path=DATABASE_PATH):
    """Insert generated recommendations for a session."""
    conn = get_connection(db_path)
    with conn:
        for rec in recommendations:
            conn.execute(
                """INSERT INTO session_recommendations
                   (session_id, rule_id, category, observation, supporting_metric,
                    time_window, suggestion, limitation_caveat, priority)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, rec.get("rule_id", "REC_GEN"), rec.get("category", "General"),
                 rec.get("observation", ""), rec.get("supporting_metric", ""),
                 rec.get("time_window", "Session-wide"), rec.get("suggestion", ""),
                 rec.get("limitation_caveat", ""), rec.get("priority", "Medium"))
            )
    conn.close()


def get_recommendations(session_id: str, db_path=DATABASE_PATH) -> List[Dict[str, Any]]:
    """Retrieve recommendations for a session."""
    conn = get_connection(db_path)
    cursor = conn.execute(
        "SELECT * FROM session_recommendations WHERE session_id = ? ORDER BY rec_id ASC",
        (session_id,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ---------------- Summary Metrics Operations ----------------

def save_session_summary(summary: Dict[str, Any], db_path=DATABASE_PATH):
    """Insert or replace session summary metrics."""
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO session_metrics_summary
               (session_id, average_engagement, peak_engagement, lowest_engagement,
                total_detected_tracks, confirmed_attendees, speech_ratio, silence_ratio,
                data_quality_score, data_quality_notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (summary.get("session_id"), summary.get("average_engagement", 0.0),
             summary.get("peak_engagement", 0.0), summary.get("lowest_engagement", 0.0),
             summary.get("total_detected_tracks", 0), summary.get("confirmed_attendees", 0),
             summary.get("speech_ratio", 0.0), summary.get("silence_ratio", 0.0),
             summary.get("data_quality_score", 100.0), summary.get("data_quality_notes", ""))
        )
    conn.close()


def get_session_summary(session_id: str, db_path=DATABASE_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve session summary metrics."""
    conn = get_connection(db_path)
    cursor = conn.execute(
        "SELECT * FROM session_metrics_summary WHERE session_id = ?",
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------- Overall Dashboard Stats ----------------

def get_overall_stats(db_path=DATABASE_PATH) -> Dict[str, Any]:
    """Retrieve aggregated KPIs across all sessions."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Total sessions
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'completed'")
    total_sessions = cursor.fetchone()[0]

    # Total participants
    cursor.execute("SELECT COUNT(*) FROM participants")
    total_participants = cursor.fetchone()[0]

    # Average engagement across all completed sessions
    cursor.execute("SELECT AVG(average_engagement) FROM session_metrics_summary")
    avg_eng = cursor.fetchone()[0]
    avg_engagement = round(avg_eng * 100, 1) if avg_eng is not None else 0.0

    # Attendance rate: (confirmed attendance records with status 'Present' / total attendance records)
    cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE status = 'Present'")
    present_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance_records")
    total_att_records = cursor.fetchone()[0]

    attendance_rate = round((present_count / total_att_records) * 100, 1) if total_att_records > 0 else 0.0

    conn.close()
    return {
        "total_sessions": total_sessions,
        "total_participants": total_participants,
        "average_engagement_pct": avg_engagement,
        "attendance_rate_pct": attendance_rate,
        "has_data": (total_sessions > 0)
    }
