"""
Attendance calculation and sustained-presence verification module.
Converts anonymous computer-vision tracks into provisional attendance records.
Adheres strictly to privacy guidelines: no automatic identity claims without operator review.
"""

from typing import List, Dict, Any, Optional
from modules.tracking import TrackedSubject
from config import MIN_FRAMES_SUSTAINED, SUSTAINED_PERCENTAGE_THRESHOLD, PARTIAL_PERCENTAGE_THRESHOLD


def evaluate_track_attendance(
    track: TrackedSubject,
    session_duration_sec: float,
    min_frames: int = MIN_FRAMES_SUSTAINED,
    sustained_ratio: float = SUSTAINED_PERCENTAGE_THRESHOLD,
    partial_ratio: float = PARTIAL_PERCENTAGE_THRESHOLD
) -> Dict[str, Any]:
    """
    Evaluates an individual tracked subject against sustained-presence thresholds.
    Filters out spurious single-frame false detections.
    """
    duration = track.duration_observed
    detections_count = track.total_frames_seen

    # Avoid division by zero
    effective_session_dur = max(session_duration_sec, 1.0)
    presence_ratio = duration / effective_session_dur

    # Sustained presence classification
    if detections_count < 2 and duration < 2.0:
        status = "Noise/Transient"
        notes = f"Filtered out: only detected in {detections_count} frame(s), likely camera artifact."
    elif detections_count >= min_frames and presence_ratio >= sustained_ratio:
        status = "Present"
        notes = f"Sustained presence confirmed ({round(presence_ratio * 100, 1)}% of session, {detections_count} frames)."
    elif presence_ratio >= partial_ratio or detections_count >= 3:
        status = "Partial"
        notes = f"Partial presence observed ({round(presence_ratio * 100, 1)}% of session, {detections_count} frames)."
    else:
        status = "Absent"
        notes = f"Below sustained attendance threshold ({round(presence_ratio * 100, 1)}% of session)."

    return {
        "track_id": f"Track-{track.track_id:03d}",
        "raw_track_id": track.track_id,
        "participant_id": None,  # Remains None until confirmed by instructor
        "first_seen_sec": round(track.first_seen_sec, 2),
        "last_seen_sec": round(track.last_seen_sec, 2),
        "duration_observed_sec": round(duration, 2),
        "frame_detections_count": detections_count,
        "presence_ratio": round(presence_ratio, 3),
        "status": status,
        "is_confirmed": 0,  # 0: Provisional, 1: Instructor Confirmed
        "notes": notes
    }


def process_attendance_from_tracks(
    tracks: List[TrackedSubject],
    session_id: str,
    session_duration_sec: float,
    filter_noise: bool = True
) -> List[Dict[str, Any]]:
    """
    Process all completed tracks into formatted attendance records for a session.
    """
    attendance_records = []

    for trk in tracks:
        record = evaluate_track_attendance(trk, session_duration_sec)
        record["session_id"] = session_id

        # Skip noise artifacts if requested
        if filter_noise and record["status"] == "Noise/Transient":
            continue

        attendance_records.append(record)

    # Sort tracks numerically by track_id
    attendance_records.sort(key=lambda x: x["raw_track_id"])
    return attendance_records


def calculate_attendance_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics for an attendance dataset.
    """
    total = len(records)
    if total == 0:
        return {
            "total_tracks": 0,
            "present_count": 0,
            "partial_count": 0,
            "absent_count": 0,
            "confirmed_count": 0,
            "attendance_rate_pct": 0.0
        }

    present = sum(1 for r in records if r.get("status") == "Present")
    partial = sum(1 for r in records if r.get("status") == "Partial")
    absent = sum(1 for r in records if r.get("status") == "Absent")
    confirmed = sum(1 for r in records if r.get("is_confirmed", 0) == 1)

    # Overall attendance rate: present + 0.5 * partial
    rate = round(((present + 0.5 * partial) / total) * 100, 1)

    return {
        "total_tracks": total,
        "present_count": present,
        "partial_count": partial,
        "absent_count": absent,
        "confirmed_count": confirmed,
        "attendance_rate_pct": rate
    }
