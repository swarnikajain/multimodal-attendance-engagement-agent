"""
Local Explainable Recommendation Engine for Multimodal Attendance & Engagement Agent.
Generates constructive, actionable pedagogical suggestions based on computed metrics.
Every recommendation includes trigger observations, concrete metrics, practical teaching ideas,
and vital pedagogical caveats.
"""

from typing import List, Dict, Any, Optional
import numpy as np


class RecommendationEngine:
    """
    Rule-based, explainable teaching suggestion generator.
    Strictly assists instructors; never makes punitive or consequential decisions about students.
    """

    def __init__(self):
        pass

    def evaluate_session(
        self,
        duration_sec: float,
        attendance_summary: Dict[str, Any],
        engagement_timeline: List[Dict[str, Any]],
        audio_analysis: Optional[Dict[str, Any]] = None,
        video_quality: Optional[Dict[str, Any]] = None,
        audio_quality: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Runs rule evaluations across multimodal session data and produces prioritized recommendations.
        """
        recommendations = []

        # ---------------- Rule 1: Prolonged Silence Intervals ----------------
        if audio_analysis and audio_analysis.get("silence_intervals"):
            long_silences = [s for s in audio_analysis["silence_intervals"] if s["duration_sec"] >= 20.0]
            if long_silences:
                total_long_silence = sum(s["duration_sec"] for s in long_silences)
                first_s = long_silences[0]
                recommendations.append({
                    "rule_id": "REC_SILENCE_PROLONGED",
                    "category": "Interactivity & Pacing",
                    "priority": "Medium",
                    "observation": f"Detected {len(long_silences)} prolonged silence period(s) totaling {int(total_long_silence)}s.",
                    "supporting_metric": f"Longest silence of {int(first_s['duration_sec'])}s occurred between {int(first_s['start_sec'])}s and {int(first_s['end_sec'])}s.",
                    "suggestion": "If this was an intended silent reading or quiz period, no change is needed. Otherwise, consider embedding a quick formative poll, think-pair-share, or open-ended check-in question during extended quiet intervals.",
                    "limitation_caveat": "Classroom silence often reflects intense individual contemplation, writing, or exam solving. It must not be interpreted as lack of attention."
                })

        # ---------------- Rule 2: Continuous Monologue / Speech Saturation ----------------
        if audio_analysis:
            speech_ratio = audio_analysis.get("speech_ratio", 0.0)
            if speech_ratio > 0.80 and duration_sec >= 300.0:
                recommendations.append({
                    "rule_id": "REC_CONTINUOUS_LECTURE",
                    "category": "Session Pacing",
                    "priority": "Medium",
                    "observation": f"Uninterrupted verbal presentation observed for {int(speech_ratio * 100)}% of the recorded session.",
                    "supporting_metric": f"Speech active ratio was {round(speech_ratio, 2)} over {int(duration_sec/60)} minutes.",
                    "suggestion": "Pacing research suggests student retention improves when 15-minute lecture blocks are punctuated with 2-minute active retrieval exercises or student-led summaries.",
                    "limitation_caveat": "High speaking ratio does not identify speaker identity; both instructor speech and lively group dialogue produce high audio activity."
                })
            elif speech_ratio < 0.20 and audio_analysis.get("valid", True):
                recommendations.append({
                    "rule_id": "REC_LOW_AUDIO_ACTIVITY",
                    "category": "Audio Signal Dynamics",
                    "priority": "Low",
                    "observation": f"Unusually low audio activity measured ({int(speech_ratio * 100)}% of session).",
                    "supporting_metric": f"Active audio accounted for only {int(audio_analysis.get('total_active_sec', 0))}s of {int(duration_sec)}s.",
                    "suggestion": "Verify that microphone placement captures both instructor speech and classroom room sound adequately.",
                    "limitation_caveat": "Low audio may simply denote a self-paced computer lab, written assessment, or video screening session."
                })

        # ---------------- Rule 3: Mid-Session Engagement Drop ----------------
        if engagement_timeline and len(engagement_timeline) >= 20:
            scores = [pt["composite_engagement"] for pt in engagement_timeline if pt.get("composite_engagement") is not None]
            if len(scores) >= 20:
                half = len(scores) // 2
                first_half_avg = float(np.mean(scores[:half]))
                second_half_avg = float(np.mean(scores[half:]))
                delta = first_half_avg - second_half_avg

                if delta >= 0.18:
                    recommendations.append({
                        "rule_id": "REC_ENGAGEMENT_DIP",
                        "category": "Attention & Energy Curve",
                        "priority": "High",
                        "observation": "Observable activity and visual engagement proxy showed a noticeable downward trend in the latter half of the session.",
                        "supporting_metric": f"Average engagement proxy dropped by {int(delta * 100)} percentage points (from {round(first_half_avg*100, 1)}% in early session to {round(second_half_avg*100, 1)}% later).",
                        "suggestion": "Consider scheduling a 3-minute physical stretch, concept checkpoint, or interactive quiz halfway through longer class periods to reinvigorate classroom dynamics.",
                        "limitation_caveat": "Physical stillness in later session phases can indicate settled focus during detailed technical explanations rather than fatigue."
                    })
                elif (second_half_avg - first_half_avg) >= 0.18:
                    recommendations.append({
                        "rule_id": "REC_ENGAGEMENT_SURGE",
                        "category": "Attention & Energy Curve",
                        "priority": "Low",
                        "observation": "Observable activity increased significantly in the second half of the session.",
                        "supporting_metric": f"Engagement proxy rose from {round(first_half_avg*100, 1)}% to {round(second_half_avg*100, 1)}%.",
                        "suggestion": "Review the teaching modality used in the later portion (e.g. live demo, problem solving) as it prompted higher observable engagement.",
                        "limitation_caveat": "Surges can also be triggered by end-of-class packing or student movement toward the exit."
                    })

        # ---------------- Rule 4: Attendance & Track Persistence ----------------
        total_tracks = attendance_summary.get("total_tracks", 0)
        present_count = attendance_summary.get("present_count", 0)
        partial_count = attendance_summary.get("partial_count", 0)

        if total_tracks > 0 and (partial_count / total_tracks) > 0.35:
            recommendations.append({
                "rule_id": "REC_TRANSIENT_ATTENDANCE",
                "category": "Attendance & Camera Coverage",
                "priority": "Medium",
                "observation": f"A notable portion ({partial_count} of {total_tracks}) of detected attendees had intermittent presence.",
                "supporting_metric": f"{round((partial_count / total_tracks) * 100, 1)}% of detected tracks were classified as Partial.",
                "suggestion": "Check whether camera occlusion, peripheral seating outside the lens angle, or students moving in and out caused visual drop-outs.",
                "limitation_caveat": "Camera field-of-view limitations and head-turning naturally lead to temporary detection losses."
            })

        # ---------------- Rule 5: Recording Quality Diagnostics ----------------
        if video_quality and video_quality.get("quality_issues"):
            for issue in video_quality["quality_issues"]:
                recommendations.append({
                    "rule_id": "REC_VIDEO_QUALITY_ALERT",
                    "category": "Data Quality & Recording Setup",
                    "priority": "High",
                    "observation": f"Video quality compromise detected: {issue}",
                    "supporting_metric": f"Video quality index: {video_quality.get('video_quality_score', 100)}/100.",
                    "suggestion": "Improve ambient lighting and position the camera steadily on a tripod to prevent motion blur and false negative detections.",
                    "limitation_caveat": "Visual analytics reliability is constrained when frames are blurry or underlit; metrics should be interpreted with caution."
                })

        if audio_quality and audio_quality.get("notes"):
            for note in audio_quality["notes"]:
                recommendations.append({
                    "rule_id": "REC_AUDIO_QUALITY_ALERT",
                    "category": "Data Quality & Recording Setup",
                    "priority": "Medium",
                    "observation": f"Audio recording artifact: {note}",
                    "supporting_metric": f"Audio quality score: {audio_quality.get('audio_quality_score', 100)}/100.",
                    "suggestion": "Adjust recording microphone input gain or reposition the mic closer to the primary speaker to avoid distortion.",
                    "limitation_caveat": "Clipped or degraded audio impairs speech-to-silence discrimination accuracy."
                })

        # Default fallback recommendation if session ran smoothly without anomalies
        if not recommendations:
            recommendations.append({
                "rule_id": "REC_BALANCED_SESSION",
                "category": "General Dynamics",
                "priority": "Low",
                "observation": "Session exhibited balanced multimodal dynamics with consistent presence and stable audio/video metrics.",
                "supporting_metric": f"Session duration: {int(duration_sec)}s, Attendance rate: {attendance_summary.get('attendance_rate_pct', 100)}%.",
                "suggestion": "Maintain the current instructional balance between lecture presentation and observation intervals.",
                "limitation_caveat": "Metrics represent sensor observations and provide supportive context rather than comprehensive pedagogical evaluation."
            })

        return recommendations
