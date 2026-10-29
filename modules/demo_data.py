"""
Deterministic sample data generator and simulated demo mode for Multimodal Attendance & Engagement Agent.
Provides synthetic sessions, sample rosters, and lightweight synthetic media files for testing.
All generated demo records are explicitly tagged as SIMULATED.
"""

import os
import math
import wave
import struct
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

from config import SAMPLE_DATA_DIR, DATABASE_PATH
from modules.database import (
    create_session, save_attendance_records, save_engagement_timeline,
    save_recommendations, save_session_summary, add_participant, list_participants
)
from modules.recommendation_engine import RecommendationEngine

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    OPENCV_AVAILABLE = False


# Deterministic sample roster
SAMPLE_ROSTER = [
    {"participant_id": "STU101", "display_name": "Aarav Sharma", "email": "aarav.s@college.edu", "course": "Computer Science"},
    {"participant_id": "STU102", "display_name": "Diya Patel", "email": "diya.p@college.edu", "course": "Computer Science"},
    {"participant_id": "STU103", "display_name": "Rohan Iyer", "email": "rohan.i@college.edu", "course": "Computer Science"},
    {"participant_id": "STU104", "display_name": "Ananya Gupta", "email": "ananya.g@college.edu", "course": "Computer Science"},
    {"participant_id": "STU105", "display_name": "Vikram Singh", "email": "vikram.s@college.edu", "course": "Computer Science"},
    {"participant_id": "STU106", "display_name": "Sneha Kulkarni", "email": "sneha.k@college.edu", "course": "Computer Science"},
    {"participant_id": "STU107", "display_name": "Kavya Menon", "email": "kavya.m@college.edu", "course": "Computer Science"},
    {"participant_id": "STU108", "display_name": "Farhan Ali", "email": "farhan.a@college.edu", "course": "Computer Science"}
]


def seed_sample_participants_if_empty(db_path=DATABASE_PATH):
    """Adds default sample participants if roster is empty."""
    current = list_participants(db_path=db_path)
    if not current:
        for p in SAMPLE_ROSTER:
            add_participant(
                participant_id=p["participant_id"],
                display_name=p["display_name"],
                email=p["email"],
                course=p["course"],
                db_path=db_path
            )


def seed_demo_session(session_id: str = "demo_session_01", title: str = "CS301: AI & Multimodal Intelligence (Demo)", db_path=DATABASE_PATH) -> str:
    """
    Creates a complete, deterministic simulated session with realistic metrics,
    attendance tracks, engagement timeline, and recommendations.
    All data is clearly tagged as simulated demo data.
    """
    seed_sample_participants_if_empty(db_path=db_path)

    # 1. Create Session
    duration_sec = 600.0  # 10 minute simulated session
    create_session(
        session_id=session_id,
        title=title,
        course_name="B.Tech Computer Science - Year 3",
        date="2026-10-29",
        duration_sec=duration_sec,
        is_demo=1,
        sampling_interval_sec=1.0,
        notes="SIMULATED DEMO: Generated deterministic dataset for platform evaluation.",
        db_path=db_path
    )

    # 2. Simulated Attendance Tracks
    tracks_data = [
        {
            "session_id": session_id,
            "track_id": "Track-001",
            "participant_id": "STU101",
            "first_seen_sec": 4.0,
            "last_seen_sec": 595.0,
            "duration_observed_sec": 570.0,
            "frame_detections_count": 550,
            "status": "Present",
            "is_confirmed": 1,
            "notes": "Simulated continuous attendance. Sustained presence confirmed (95.0%)."
        },
        {
            "session_id": session_id,
            "track_id": "Track-002",
            "participant_id": "STU102",
            "first_seen_sec": 10.0,
            "last_seen_sec": 585.0,
            "duration_observed_sec": 540.0,
            "frame_detections_count": 510,
            "status": "Present",
            "is_confirmed": 1,
            "notes": "Simulated continuous attendance. Sustained presence confirmed (90.0%)."
        },
        {
            "session_id": session_id,
            "track_id": "Track-003",
            "participant_id": "STU103",
            "first_seen_sec": 15.0,
            "last_seen_sec": 590.0,
            "duration_observed_sec": 520.0,
            "frame_detections_count": 490,
            "status": "Present",
            "is_confirmed": 1,
            "notes": "Simulated continuous attendance. Sustained presence confirmed (86.7%)."
        },
        {
            "session_id": session_id,
            "track_id": "Track-004",
            "participant_id": "STU104",
            "first_seen_sec": 60.0,
            "last_seen_sec": 580.0,
            "duration_observed_sec": 480.0,
            "frame_detections_count": 450,
            "status": "Present",
            "is_confirmed": 1,
            "notes": "Simulated attendance. Arrived slightly after start (80.0%)."
        },
        {
            "session_id": session_id,
            "track_id": "Track-005",
            "participant_id": "STU105",
            "first_seen_sec": 20.0,
            "last_seen_sec": 240.0,
            "duration_observed_sec": 180.0,
            "frame_detections_count": 160,
            "status": "Partial",
            "is_confirmed": 1,
            "notes": "Intermittent attendance: left session early around min 4."
        },
        {
            "session_id": session_id,
            "track_id": "Track-006",
            "participant_id": None,  # Unmapped track
            "first_seen_sec": 300.0,
            "last_seen_sec": 410.0,
            "duration_observed_sec": 95.0,
            "frame_detections_count": 85,
            "status": "Partial",
            "is_confirmed": 0,
            "notes": "Provisional track: visitor or unmapped student."
        },
        {
            "session_id": session_id,
            "track_id": "Track-007",
            "participant_id": None,
            "first_seen_sec": 120.0,
            "last_seen_sec": 145.0,
            "duration_observed_sec": 25.0,
            "frame_detections_count": 22,
            "status": "Absent",
            "is_confirmed": 0,
            "notes": "Brief walkthrough (<5% duration). Classified as Absent."
        }
    ]
    save_attendance_records(tracks_data, db_path=db_path)

    # 3. Simulated Engagement Timeline (600 seconds)
    timeline_pts = []
    np.random.seed(42)  # Deterministic seed

    for t in range(0, int(duration_sec), 2):
        t_sec = float(t)
        # Base engagement curve: higher in beginning, slight dip in middle, pickup towards end
        progress = t_sec / duration_sec
        base_eng = 0.72 - 0.25 * math.sin(progress * math.pi) + (np.random.rand() - 0.5) * 0.08
        base_eng = float(np.clip(base_eng, 0.25, 0.95))

        # Motion curve
        motion = float(np.clip(0.30 + (np.random.rand() - 0.5) * 0.15, 0.05, 0.75))

        # Audio energy and speech: simulates active lecture with 2 silence intervals
        is_silence = (180 <= t_sec <= 215) or (380 <= t_sec <= 410)
        if is_silence:
            audio_energy = float(0.04 + np.random.rand() * 0.03)
            speech_active = 0
        else:
            audio_energy = float(0.35 + np.random.rand() * 0.35)
            speech_active = 1 if audio_energy > 0.20 else 0

        # Gaze proxy
        gaze = float(np.clip(0.68 + (np.random.rand() - 0.5) * 0.20, 0.30, 0.95))

        people_count = 5 if t_sec < 240 else 4

        timeline_pts.append({
            "timestamp_sec": t_sec,
            "people_count": people_count,
            "motion_score": round(motion, 3),
            "gaze_score": round(gaze, 3),
            "audio_energy": round(audio_energy, 3),
            "speech_active": speech_active,
            "composite_engagement": round(base_eng, 3),
            "available_signals": ["presence", "motion", "audio", "gaze"]
        })

    save_engagement_timeline(session_id, timeline_pts, db_path=db_path)

    # 4. Generate Recommendations using Rule Engine
    engine = RecommendationEngine()
    dummy_att_summary = {
        "total_tracks": 7,
        "present_count": 4,
        "partial_count": 2,
        "absent_count": 1,
        "attendance_rate_pct": 71.4
    }
    dummy_audio_analysis = {
        "valid": True,
        "speech_ratio": 0.78,
        "silence_ratio": 0.22,
        "total_active_sec": 468.0,
        "silence_intervals": [
            {"start_sec": 180.0, "end_sec": 215.0, "duration_sec": 35.0},
            {"start_sec": 380.0, "end_sec": 410.0, "duration_sec": 30.0}
        ]
    }
    recs = engine.evaluate_session(
        duration_sec=duration_sec,
        attendance_summary=dummy_att_summary,
        engagement_timeline=timeline_pts,
        audio_analysis=dummy_audio_analysis,
        video_quality={"video_quality_score": 92.0, "quality_issues": []},
        audio_quality={"audio_quality_score": 90.0, "notes": []}
    )
    save_recommendations(session_id, recs, db_path=db_path)

    # 5. Session Metrics Summary
    summary_data = {
        "session_id": session_id,
        "average_engagement": 0.68,
        "peak_engagement": 0.89,
        "lowest_engagement": 0.44,
        "total_detected_tracks": 7,
        "confirmed_attendees": 5,
        "speech_ratio": 0.78,
        "silence_ratio": 0.22,
        "data_quality_score": 94.0,
        "data_quality_notes": "Optimal lighting, high landmark stability, clear audio levels without clipping."
    }
    save_session_summary(summary_data, db_path=db_path)

    return session_id


def generate_synthetic_media(target_dir: Path = SAMPLE_DATA_DIR) -> Dict[str, str]:
    """
    Creates lightweight, genuine sample video and audio files on disk (10 seconds).
    Allows running the full OpenCV and audio analysis pipeline without user media uploads.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    video_path = target_dir / "sample_classroom_10s.mp4"
    audio_path = target_dir / "sample_classroom_10s.wav"

    # 1. Generate Synthetic Audio File (10s sine wave + silence intervals)
    sample_rate = 16000
    duration_sec = 10
    total_samples = sample_rate * duration_sec

    # Audio pattern: 4s tone (speech proxy), 3s silence, 3s tone
    with wave.open(str(audio_path), "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            if (0 <= t <= 4) or (7 <= t <= 10):
                # Harmonic tone mimicking voice fundamental
                val = 0.4 * math.sin(2 * math.pi * 220 * t) + 0.2 * math.sin(2 * math.pi * 440 * t)
            else:
                # Ambient silence / low noise
                val = 0.002 * (np.random.rand() - 0.5)

            int_val = int(val * 32767.0)
            int_val = max(-32768, min(32767, int_val))
            frames.extend(struct.pack("<h", int_val))

        wav_file.writeframes(frames)

    # 2. Generate Synthetic Video File (10s at 10 fps)
    if OPENCV_AVAILABLE:
        fps = 10
        width, height = 640, 480
        total_video_frames = fps * duration_sec

        # Try mp4v or XVID codec
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

        if not out.isOpened():
            # Fallback codec
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            video_path = target_dir / "sample_classroom_10s.avi"
            out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

        if out.isOpened():
            for f in range(total_video_frames):
                t = f / float(fps)
                # Slate background
                img = np.zeros((height, width, 3), dtype=np.uint8)
                img[:] = (30, 41, 59)  # Slate dark

                # Classroom banner
                cv2.putText(img, "Multimodal Classroom Intelligence Test", (40, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (241, 245, 249), 2)
                cv2.putText(img, f"Time: {t:.1f}s / {duration_sec}s", (40, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (148, 163, 184), 1)

                # Simulated Student 1: Slight sway
                s1_x = int(180 + 15 * math.sin(t * 1.5))
                s1_y = 240
                # Face oval
                cv2.ellipse(img, (s1_x, s1_y), (45, 55), 0, 0, 360, (200, 220, 240), -1)
                # Eyes
                cv2.circle(img, (s1_x - 15, s1_y - 10), 5, (50, 50, 50), -1)
                cv2.circle(img, (s1_x + 15, s1_y - 10), 5, (50, 50, 50), -1)
                cv2.putText(img, "Student A", (s1_x - 35, s1_y + 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (226, 232, 240), 1)

                # Simulated Student 2: Appears throughout
                s2_x = 440
                s2_y = 250
                cv2.ellipse(img, (s2_x, s2_y), (42, 52), 0, 0, 360, (210, 215, 235), -1)
                cv2.circle(img, (s2_x - 14, s2_y - 10), 5, (50, 50, 50), -1)
                cv2.circle(img, (s2_x + 14, s2_y - 10), 5, (50, 50, 50), -1)
                cv2.putText(img, "Student B", (s2_x - 35, s2_y + 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (226, 232, 240), 1)

                out.write(img)

            out.release()

    return {
        "video_path": str(video_path),
        "audio_path": str(audio_path)
    }
