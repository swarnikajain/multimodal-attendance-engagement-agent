"""
Unit tests for attendance tracking and sustained-presence verification.
"""

import pytest
from modules.tracking import TrackedSubject
from modules.attendance import evaluate_track_attendance, process_attendance_from_tracks, calculate_attendance_summary


def test_sustained_presence_present():
    """Verify that a subject with sufficient frames and duration is marked Present."""
    trk = TrackedSubject(track_id=1, centroid=(100, 100), box=(80, 80, 40, 40), timestamp_sec=0.0)
    # Simulate 10 updates over 100 seconds
    for t in range(10, 110, 10):
        trk.update(centroid=(100 + t % 5, 100), box=(80, 80, 40, 40), timestamp_sec=float(t))

    res = evaluate_track_attendance(trk, session_duration_sec=200.0, min_frames=5, sustained_ratio=0.30)
    assert res["status"] == "Present"
    assert res["duration_observed_sec"] == 100.0
    assert res["frame_detections_count"] == 11
    assert res["is_confirmed"] == 0  # Provisional by default
    assert res["track_id"] == "Track-001"


def test_intermittent_partial_attendance():
    """Verify that a subject observed intermittently between partial and sustained threshold is marked Partial."""
    trk = TrackedSubject(track_id=2, centroid=(200, 200), box=(180, 180, 40, 40), timestamp_sec=10.0)
    for t in [20.0, 30.0, 40.0]:
        trk.update(centroid=(200, 200), box=(180, 180, 40, 40), timestamp_sec=t)

    # Duration = 30s out of 200s (15%, which is >= 10% and < 30%)
    res = evaluate_track_attendance(trk, session_duration_sec=200.0, min_frames=5, sustained_ratio=0.30, partial_ratio=0.10)
    assert res["status"] == "Partial"


def test_noise_filtering():
    """Verify single-frame spurious detection is flagged as noise."""
    trk = TrackedSubject(track_id=3, centroid=(300, 300), box=(280, 280, 40, 40), timestamp_sec=15.0)
    res = evaluate_track_attendance(trk, session_duration_sec=300.0)
    assert res["status"] == "Noise/Transient"
    assert res["duration_observed_sec"] == 0.0


def test_attendance_summary_calculations():
    """Verify summary metrics calculation."""
    records = [
        {"status": "Present", "is_confirmed": 1},
        {"status": "Present", "is_confirmed": 0},
        {"status": "Partial", "is_confirmed": 1},
        {"status": "Absent", "is_confirmed": 0}
    ]
    summary = calculate_attendance_summary(records)
    assert summary["total_tracks"] == 4
    assert summary["present_count"] == 2
    assert summary["partial_count"] == 1
    assert summary["absent_count"] == 1
    assert summary["confirmed_count"] == 2
    # Rate: (2 + 0.5 * 1) / 4 = 2.5 / 4 = 62.5%
    assert summary["attendance_rate_pct"] == 62.5
