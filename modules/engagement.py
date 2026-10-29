"""
Multimodal engagement proxy calculation and signal fusion module.
Combines observable visual presence, motion dynamics, audio energy, and frontal pose proxies
into a transparent, explainable composite index with data-quality confidence ratings.

ETHICAL DISCLAIMER:
Engagement indicators are observational proxy estimates of classroom physical activity
and sound levels. They DO NOT measure internal cognitive attention, mental comprehension,
or emotional sentiment.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from config import WEIGHT_PRESENCE, WEIGHT_MOTION, WEIGHT_AUDIO, WEIGHT_GAZE


def calculate_motion_score_normalized(raw_motion: float) -> float:
    """
    Normalizes raw motion. In a classroom, moderate physical activity (taking notes,
    looking up, natural shifting) represents active participation, whereas total immobility
    (0.0) or extreme thrashing/chaos (>0.8) are less typical of focused instruction.
    Returns value in [0.0, 1.0].
    """
    m = np.clip(raw_motion, 0.0, 1.0)
    # Bell curve peak around 0.35 - 0.5
    if m < 0.35:
        # Scale up smoothly
        return float(m / 0.35)
    else:
        # Gentle decline for high agitation
        return float(max(0.2, 1.0 - (m - 0.35) * 0.8))


def fuse_signals(
    timestamp_sec: float,
    presence_signal: Optional[float] = None,
    motion_signal: Optional[float] = None,
    audio_signal: Optional[float] = None,
    gaze_signal: Optional[float] = None,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Dynamically fuses available signals using normalized weighted linear combination.
    Gracefully re-normalizes weights if any modality is absent.
    """
    weights = custom_weights or {
        "presence": WEIGHT_PRESENCE,
        "motion": WEIGHT_MOTION,
        "audio": WEIGHT_AUDIO,
        "gaze": WEIGHT_GAZE
    }

    available_signals = []
    missing_signals = []
    weighted_sum = 0.0
    total_active_weight = 0.0

    if presence_signal is not None:
        available_signals.append("presence")
        w = weights.get("presence", 0.35)
        weighted_sum += w * np.clip(presence_signal, 0.0, 1.0)
        total_active_weight += w
    else:
        missing_signals.append("presence")

    if motion_signal is not None:
        available_signals.append("motion")
        w = weights.get("motion", 0.25)
        weighted_sum += w * np.clip(motion_signal, 0.0, 1.0)
        total_active_weight += w
    else:
        missing_signals.append("motion")

    if audio_signal is not None:
        available_signals.append("audio")
        w = weights.get("audio", 0.25)
        weighted_sum += w * np.clip(audio_signal, 0.0, 1.0)
        total_active_weight += w
    else:
        missing_signals.append("audio")

    if gaze_signal is not None:
        available_signals.append("gaze")
        w = weights.get("gaze", 0.15)
        weighted_sum += w * np.clip(gaze_signal, 0.0, 1.0)
        total_active_weight += w
    else:
        missing_signals.append("gaze")

    if total_active_weight > 0.0:
        composite_score = float(weighted_sum / total_active_weight)
    else:
        composite_score = 0.0

    return {
        "timestamp_sec": round(timestamp_sec, 2),
        "composite_engagement": round(composite_score, 3),
        "available_signals": available_signals,
        "missing_signals": missing_signals,
        "effective_weights": {
            sig: round(weights.get(sig, 0.0) / total_active_weight, 3)
            for sig in available_signals
        } if total_active_weight > 0 else {}
    }


def compute_session_engagement_timeline(
    video_timeline: List[Dict[str, Any]],
    audio_timeline: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Aligns video timeline points with audio timeline points by timestamp.
    Calculates fused engagement proxy index at each second.
    """
    fused_timeline = []

    # Index audio timeline by integer second for fast alignment
    audio_map = {}
    if audio_timeline:
        for pt in audio_timeline:
            sec_key = int(round(pt.get("timestamp_sec", 0.0)))
            audio_map[sec_key] = pt

    for v_pt in video_timeline:
        t = v_pt.get("timestamp_sec", 0.0)
        sec_key = int(round(t))

        # Presence: 1.0 if at least 1 person detected, scales with person presence
        p_count = v_pt.get("people_count", 0)
        presence_score = min(1.0, p_count / 1.0) if p_count > 0 else 0.0

        # Motion score normalized
        raw_motion = v_pt.get("motion_score", 0.0)
        norm_motion = calculate_motion_score_normalized(raw_motion)

        # Gaze / frontal pose proxy
        gaze_score = v_pt.get("gaze_score")

        # Audio alignment
        a_pt = audio_map.get(sec_key)
        audio_score = None
        speech_active = None
        if a_pt:
            audio_score = a_pt.get("rms_energy")
            speech_active = a_pt.get("speech_active", 0)

        fused = fuse_signals(
            timestamp_sec=t,
            presence_signal=presence_score,
            motion_signal=norm_motion,
            audio_signal=audio_score,
            gaze_signal=gaze_score
        )

        fused_timeline.append({
            "timestamp_sec": t,
            "people_count": p_count,
            "motion_score": round(raw_motion, 3),
            "normalized_motion": round(norm_motion, 3),
            "gaze_score": gaze_score,
            "audio_energy": audio_score,
            "speech_active": speech_active,
            "composite_engagement": fused["composite_engagement"],
            "available_signals": fused["available_signals"]
        })

    return fused_timeline


def calculate_data_quality_index(
    video_quality: Optional[Dict[str, Any]] = None,
    audio_quality: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes a transparent data quality & confidence score (0-100%).
    Accounts for missing modalities, lighting degradation, blur, and audio clipping.
    """
    score = 100.0
    breakdown = []

    # Completeness check
    has_video = video_quality is not None and video_quality.get("video_quality_score") is not None
    has_audio = audio_quality is not None and audio_quality.get("audio_quality_score") is not None

    if not has_video:
        score -= 40.0
        breakdown.append("Video modality missing: analysis limited to audio.")
    if not has_audio:
        score -= 25.0
        breakdown.append("Audio modality missing: speech/silence analysis unavailable.")

    # Quality deductions
    if has_video:
        v_score = video_quality.get("video_quality_score", 100.0)
        if v_score < 80.0:
            deduction = (80.0 - v_score) * 0.5
            score -= deduction
            breakdown.append(f"Visual quality penalties applied (-{round(deduction, 1)}%).")

    if has_audio:
        a_score = audio_quality.get("audio_quality_score", 100.0)
        if a_score < 80.0:
            deduction = (80.0 - a_score) * 0.4
            score -= deduction
            breakdown.append(f"Audio quality penalties applied (-{round(deduction, 1)}%).")

    final_score = round(max(10.0, min(100.0, score)), 1)

    if final_score >= 80.0:
        rating = "High Confidence"
    elif final_score >= 60.0:
        rating = "Moderate Confidence"
    else:
        rating = "Low Confidence / Review Advised"

    return {
        "overall_quality_score": final_score,
        "rating": rating,
        "notes": breakdown,
        "has_video": has_video,
        "has_audio": has_audio
    }
