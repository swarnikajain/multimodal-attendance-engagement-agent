"""
Unit tests for multimodal engagement scoring, dynamic signal fusion, and data quality metrics.
"""

import pytest
from modules.engagement import (
    calculate_motion_score_normalized,
    fuse_signals,
    calculate_data_quality_index,
    compute_session_engagement_timeline
)


def test_motion_normalization_bounds():
    """Ensure normalized motion scores stay bounded between 0.0 and 1.0."""
    for val in [-0.5, 0.0, 0.2, 0.35, 0.7, 1.0, 2.0]:
        score = calculate_motion_score_normalized(val)
        assert 0.0 <= score <= 1.0


def test_signal_fusion_multimodal():
    """Verify fusion with all 4 signals present produces valid bounded result."""
    res = fuse_signals(
        timestamp_sec=10.0,
        presence_signal=1.0,
        motion_signal=0.5,
        audio_signal=0.8,
        gaze_signal=0.7
    )
    assert 0.0 <= res["composite_engagement"] <= 1.0
    assert set(res["available_signals"]) == {"presence", "motion", "audio", "gaze"}
    assert len(res["missing_signals"]) == 0
    # Sum of effective weights should equal 1.0
    assert pytest.approx(sum(res["effective_weights"].values()), 0.01) == 1.0


def test_signal_fusion_audio_missing():
    """Verify graceful re-normalization when audio modality is missing."""
    res = fuse_signals(
        timestamp_sec=20.0,
        presence_signal=1.0,
        motion_signal=0.6,
        audio_signal=None,
        gaze_signal=0.8
    )
    assert 0.0 <= res["composite_engagement"] <= 1.0
    assert "audio" in res["missing_signals"]
    assert "audio" not in res["available_signals"]
    assert pytest.approx(sum(res["effective_weights"].values()), 0.01) == 1.0


def test_signal_fusion_video_missing():
    """Verify graceful fallback when video signals are missing (audio-only mode)."""
    res = fuse_signals(
        timestamp_sec=30.0,
        presence_signal=None,
        motion_signal=None,
        audio_signal=0.65,
        gaze_signal=None
    )
    assert pytest.approx(res["composite_engagement"], 0.01) == 0.65
    assert res["available_signals"] == ["audio"]
    assert res["effective_weights"]["audio"] == 1.0


def test_data_quality_index():
    """Verify quality score calculations and penalty deductions."""
    # Full high quality
    full_q = calculate_data_quality_index(
        video_quality={"video_quality_score": 95.0},
        audio_quality={"audio_quality_score": 90.0}
    )
    assert full_q["overall_quality_score"] == 100.0
    assert full_q["rating"] == "High Confidence"

    # Missing audio deduction
    no_audio = calculate_data_quality_index(
        video_quality={"video_quality_score": 90.0},
        audio_quality=None
    )
    assert no_audio["overall_quality_score"] <= 75.0
    assert "Audio modality missing" in no_audio["notes"][0]
