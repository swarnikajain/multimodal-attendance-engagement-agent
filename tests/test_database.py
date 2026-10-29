"""
Unit tests for database CRUD, participant management, demo labeling, and export generation.
"""

import os
import json
import pytest
from pathlib import Path
from modules.database import (
    init_db, add_participant, get_participant, update_participant, delete_participant,
    list_participants, create_session, get_session, list_sessions, delete_session,
    save_attendance_records, get_attendance_records, map_track_to_participant,
    save_session_summary, get_session_summary, get_overall_stats
)
from modules.demo_data import seed_demo_session
from modules.report_generator import generate_attendance_csv, generate_session_summary_json, generate_readable_markdown_report


@pytest.fixture
def test_db(tmp_path):
    """Creates a temporary SQLite database for test isolation."""
    db_file = tmp_path / "test_intelligence.db"
    init_db(db_path=db_file)
    return db_file


def test_participant_crud(test_db):
    """Verify add, retrieve, update, delete of participants."""
    # Add
    ok = add_participant("P001", "Alice Smith", "alice@test.edu", "Physics", db_path=test_db)
    assert ok is True

    # Duplicate check
    dup = add_participant("P001", "Alice Smith", db_path=test_db)
    assert dup is False

    # Retrieve
    p = get_participant("P001", db_path=test_db)
    assert p is not None
    assert p["display_name"] == "Alice Smith"

    # Update
    up = update_participant("P001", "Alice Johnson", "alice.j@test.edu", "Physics", db_path=test_db)
    assert up is True
    p2 = get_participant("P001", db_path=test_db)
    assert p2["display_name"] == "Alice Johnson"

    # List & search
    results = list_participants("Alice", db_path=test_db)
    assert len(results) == 1

    # Delete
    del_ok = delete_participant("P001", db_path=test_db)
    assert del_ok is True
    assert get_participant("P001", db_path=test_db) is None


def test_session_and_attendance_flow(test_db):
    """Verify session creation, track saving, manual operator mapping, and summary metrics."""
    # 1. Create Session
    s_ok = create_session(
        session_id="SESS_01",
        title="Intro to Robotics",
        course_name="Robotics 101",
        date="2026-10-29",
        duration_sec=300.0,
        is_demo=0,
        db_path=test_db
    )
    assert s_ok is True

    # 2. Add Participant to map
    add_participant("STU501", "Bob Martin", "bob@test.edu", "Robotics", db_path=test_db)

    # 3. Save provisional attendance tracks
    tracks = [
        {
            "session_id": "SESS_01",
            "track_id": "Track-001",
            "participant_id": None,
            "first_seen_sec": 5.0,
            "last_seen_sec": 290.0,
            "duration_observed_sec": 280.0,
            "frame_detections_count": 270,
            "status": "Present",
            "is_confirmed": 0
        }
    ]
    save_attendance_records(tracks, db_path=test_db)

    records = get_attendance_records("SESS_01", db_path=test_db)
    assert len(records) == 1
    assert records[0]["is_confirmed"] == 0
    assert records[0]["participant_id"] is None

    # 4. Operator maps track to participant
    rec_id = records[0]["record_id"]
    map_ok = map_track_to_participant(rec_id, participant_id="STU501", is_confirmed=1, status="Present", db_path=test_db)
    assert map_ok is True

    updated_records = get_attendance_records("SESS_01", db_path=test_db)
    assert updated_records[0]["participant_id"] == "STU501"
    assert updated_records[0]["display_name"] == "Bob Martin"
    assert updated_records[0]["is_confirmed"] == 1


def test_demo_mode_tagging_and_seeding(test_db):
    """Verify that seeded demo sessions are explicitly tagged with is_demo=1."""
    sess_id = seed_demo_session(session_id="DEMO_TEST", db_path=test_db)
    sess = get_session(sess_id, db_path=test_db)
    assert sess is not None
    assert sess["is_demo"] == 1
    assert "SIMULATED" in sess["notes"]

    # Overall stats
    stats = get_overall_stats(db_path=test_db)
    assert stats["total_participants"] >= 8


def test_report_exports(test_db):
    """Verify CSV, JSON, and Markdown report generators."""
    sess_id = seed_demo_session(session_id="DEMO_REPORT", db_path=test_db)
    sess = get_session(sess_id, db_path=test_db)
    records = get_attendance_records(sess_id, db_path=test_db)
    summary = get_session_summary(sess_id, db_path=test_db)

    # 1. CSV
    csv_text = generate_attendance_csv(records)
    assert "Session ID,Track ID,Participant ID" in csv_text
    assert "Track-001" in csv_text

    # 2. JSON
    json_str = generate_session_summary_json(sess, summary, records, [])
    parsed = json.loads(json_str)
    assert parsed["metadata"]["session_id"] == sess_id
    assert parsed["metadata"]["is_demo"] is True

    # 3. Markdown
    md_text = generate_readable_markdown_report(sess, summary, records, [])
    assert "# Classroom Intelligence Session Report" in md_text
    assert "Simulated Demo Session" in md_text
