"""
Report generation and export module for Multimodal Attendance & Engagement Agent.
Produces downloadable CSV attendance files, comprehensive JSON summaries,
and structured markdown pedagogical reports.
"""

import io
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional


def generate_attendance_csv(records: List[Dict[str, Any]]) -> str:
    """
    Generates CSV string for attendance records.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Session ID",
        "Track ID",
        "Participant ID",
        "Display Name",
        "Course",
        "First Seen (s)",
        "Last Seen (s)",
        "Duration Observed (s)",
        "Frame Detections",
        "Attendance Status",
        "Confirmed By Instructor",
        "Notes"
    ])

    for r in records:
        writer.writerow([
            r.get("session_id", ""),
            r.get("track_id", ""),
            r.get("participant_id") or "Unmapped",
            r.get("display_name") or "Anonymous Track",
            r.get("course") or "",
            r.get("first_seen_sec", 0.0),
            r.get("last_seen_sec", 0.0),
            r.get("duration_observed_sec", 0.0),
            r.get("frame_detections_count", 0),
            r.get("status", "Provisional"),
            "Yes" if r.get("is_confirmed", 0) == 1 else "No (Provisional)",
            r.get("notes", "")
        ])

    return output.getvalue()


def generate_session_summary_json(
    session: Dict[str, Any],
    summary: Dict[str, Any],
    records: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    timeline: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Produces complete JSON data structure of session analysis.
    """
    report_dict = {
        "metadata": {
            "session_id": session.get("session_id"),
            "title": session.get("title"),
            "course": session.get("course_name"),
            "date": session.get("date"),
            "duration_sec": session.get("duration_sec"),
            "is_demo": bool(session.get("is_demo")),
            "generated_at": datetime.now().isoformat(),
            "pipeline_version": "1.0.0-local"
        },
        "summary_metrics": summary,
        "attendance_records": records,
        "recommendations": recommendations,
        "timeline_sample": timeline[:60] if timeline else [],  # First 60s sample for compact JSON
        "privacy_compliance": {
            "local_execution": True,
            "biometric_templates_stored": False,
            "identity_matching_mode": "operator_verified"
        }
    }
    return json.dumps(report_dict, indent=2)


def generate_readable_markdown_report(
    session: Dict[str, Any],
    summary: Dict[str, Any],
    records: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    quality_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    Constructs an executive markdown summary of the session.
    """
    total_tracks = len(records)
    present_cnt = sum(1 for r in records if r.get("status") == "Present")
    partial_cnt = sum(1 for r in records if r.get("status") == "Partial")
    absent_cnt = sum(1 for r in records if r.get("status") == "Absent")
    confirmed_cnt = sum(1 for r in records if r.get("is_confirmed", 0) == 1)

    avg_eng = round(summary.get("average_engagement", 0.0) * 100, 1)
    peak_eng = round(summary.get("peak_engagement", 0.0) * 100, 1)
    speech_ratio = round(summary.get("speech_ratio", 0.0) * 100, 1)
    silence_ratio = round(summary.get("silence_ratio", 0.0) * 100, 1)
    quality_score = summary.get("data_quality_score", 100.0)

    demo_badge = " *(Simulated Demo Session)*" if session.get("is_demo") else ""

    md = f"""# Classroom Intelligence Session Report{demo_badge}

**Session Title:** {session.get('title', 'Class Session')}  
**Course:** {session.get('course_name', 'N/A')}  
**Date:** {session.get('date', 'N/A')}  
**Duration:** {round(session.get('duration_sec', 0.0), 1)} seconds ({round(session.get('duration_sec', 0.0)/60, 1)} minutes)  
**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

---

## 1. Executive Summary & KPIs

| Metric | Measured Value | Benchmark Context |
| :--- | :--- | :--- |
| **Total Tracked Attendees** | {total_tracks} | Detected distinct continuous visual tracks |
| **Confirmed Present** | {present_cnt} ({round((present_cnt/total_tracks*100) if total_tracks else 0, 1)}%) | Sustained presence >= 30% of session |
| **Partial / Intermittent** | {partial_cnt} ({round((partial_cnt/total_tracks*100) if total_tracks else 0, 1)}%) | Observed between 10% and 30% of session |
| **Instructor Confirmed** | {confirmed_cnt} of {total_tracks} | Verified mappings by authorized operator |
| **Avg Engagement Proxy** | {avg_eng}% | Multimodal observational index |
| **Peak Engagement Proxy** | {peak_eng}% | Maximum measured activity interval |
| **Speech Activity Ratio** | {speech_ratio}% | Active speech sound candidate intervals |
| **Silence Ratio** | {silence_ratio}% | Non-speech / ambient sound intervals |
| **Data Quality Score** | {quality_score}/100 | Lighting, sharpness, audio clarity index |

---

## 2. AI Pedagogical Recommendations & Observations

"""
    if recommendations:
        for idx, rec in enumerate(recommendations, 1):
            md += f"""### Recommendation {idx}: {rec.get('category', 'Pedagogical')} `[{rec.get('priority', 'Medium')} Priority]`
- **Observation:** {rec.get('observation')}
- **Supporting Metric:** {rec.get('supporting_metric')}
- **Actionable Suggestion:** {rec.get('suggestion')}
- **Pedagogical Caveat:** *{rec.get('limitation_caveat')}*

"""
    else:
        md += "_No anomalous triggers detected. The session exhibited consistent multimodal indicators._\n\n"

    md += """---

## 3. Attendance Roster Breakdown

| Track ID | Participant ID | Display Name | Duration Observed | Status | Confirmed |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in records:
        pid = r.get("participant_id") or "Unmapped"
        name = r.get("display_name") or "Anonymous Track"
        dur = f"{r.get('duration_observed_sec', 0.0)}s"
        st = r.get("status", "Provisional")
        conf = "Confirmed" if r.get("is_confirmed", 0) == 1 else "Provisional"
        md += f"| {r.get('track_id')} | {pid} | {name} | {dur} | {st} | {conf} |\n"

    md += """
---

## 4. Privacy, Transparency & Limitation Disclaimers

1. **Local Execution:** All computer vision and acoustic signal processing ran 100% locally on-device. No visual frames, audio clips, or biometric data were uploaded to cloud servers.
2. **Identity Boundaries:** Face detection alone does not identify individuals. Tracks remain anonymous until manually mapped and verified by an authorized instructor.
3. **Observational Nature:** Engagement proxy metrics assess observable movement and audio dynamics. They do not constitute an evaluation of cognitive attention, emotional state, or learning comprehension.
"""
    return md
