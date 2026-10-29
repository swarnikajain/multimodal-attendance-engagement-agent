"""
Unit tests for explainable recommendation engine triggers and supporting evidence.
"""

import pytest
from modules.recommendation_engine import RecommendationEngine


def test_silence_trigger():
    """Verify recommendation triggered by prolonged silence interval."""
    engine = RecommendationEngine()
    audio_analysis = {
        "valid": True,
        "speech_ratio": 0.5,
        "silence_intervals": [
            {"start_sec": 120.0, "end_sec": 165.0, "duration_sec": 45.0}
        ]
    }
    recs = engine.evaluate_session(
        duration_sec=300.0,
        attendance_summary={"total_tracks": 5, "present_count": 5},
        engagement_timeline=[],
        audio_analysis=audio_analysis
    )

    silence_rec = next((r for r in recs if r["rule_id"] == "REC_SILENCE_PROLONGED"), None)
    assert silence_rec is not None
    assert "45s" in silence_rec["supporting_metric"]
    assert "limitation_caveat" in silence_rec
    assert "suggestion" in silence_rec
    assert len(silence_rec["suggestion"]) > 10


def test_engagement_drop_trigger():
    """Verify recommendation triggered by significant engagement drop in 2nd half."""
    engine = RecommendationEngine()
    # 30 seconds: 15 high (0.85), 15 low (0.35)
    timeline = []
    for t in range(15):
        timeline.append({"composite_engagement": 0.85})
    for t in range(15, 30):
        timeline.append({"composite_engagement": 0.35})

    recs = engine.evaluate_session(
        duration_sec=30.0,
        attendance_summary={"total_tracks": 4, "present_count": 4},
        engagement_timeline=timeline
    )

    drop_rec = next((r for r in recs if r["rule_id"] == "REC_ENGAGEMENT_DIP"), None)
    assert drop_rec is not None
    assert drop_rec["priority"] == "High"
    assert "dropped by" in drop_rec["supporting_metric"]


def test_monologue_trigger():
    """Verify continuous lecture triggers pacing recommendation."""
    engine = RecommendationEngine()
    audio_analysis = {
        "valid": True,
        "speech_ratio": 0.90,  # 90% speech over 600s
        "total_active_sec": 540.0,
        "silence_intervals": []
    }
    recs = engine.evaluate_session(
        duration_sec=600.0,
        attendance_summary={"total_tracks": 5, "present_count": 5},
        engagement_timeline=[],
        audio_analysis=audio_analysis
    )

    monologue_rec = next((r for r in recs if r["rule_id"] == "REC_CONTINUOUS_LECTURE"), None)
    assert monologue_rec is not None
    assert "90%" in monologue_rec["observation"]


def test_quality_issues_trigger():
    """Verify video and audio quality issues generate diagnostic recommendations."""
    engine = RecommendationEngine()
    video_q = {
        "video_quality_score": 60.0,
        "quality_issues": ["Suboptimal lighting conditions detected in 45% of frames."]
    }
    recs = engine.evaluate_session(
        duration_sec=100.0,
        attendance_summary={"total_tracks": 3, "present_count": 3},
        engagement_timeline=[],
        video_quality=video_q
    )

    q_rec = next((r for r in recs if r["rule_id"] == "REC_VIDEO_QUALITY_ALERT"), None)
    assert q_rec is not None
    assert "Suboptimal lighting" in q_rec["observation"]
