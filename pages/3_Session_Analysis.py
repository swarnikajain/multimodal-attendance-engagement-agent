"""
Session Analysis, Media Processing & Automated Attendance Pipeline Page.
Executes local computer vision and audio signal processing on uploaded or sample media.
Provides provisional attendance tracking and operator verification interface.
"""

import os
import shutil
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

from config import UPLOADS_DIR, SAMPLE_DATA_DIR, DEFAULT_SAMPLING_INTERVAL_SEC
from modules.database import (
    create_session, update_session_status, save_attendance_records,
    get_attendance_records, save_engagement_timeline, save_recommendations,
    save_session_summary, list_participants, map_track_to_participant,
    list_sessions, get_session
)
from modules.video_processor import process_video_pipeline, get_video_metadata
from modules.audio_processor import process_audio_pipeline
from modules.attendance import process_attendance_from_tracks, calculate_attendance_summary
from modules.engagement import compute_session_engagement_timeline, calculate_data_quality_index
from modules.recommendation_engine import RecommendationEngine
from modules.demo_data import generate_synthetic_media
from modules.report_generator import generate_attendance_csv
from modules.ui_common import apply_theme, render_page_header, render_ethical_disclaimer

st.set_page_config(page_title="Session Analysis - Classroom Agent", page_icon="🎯", layout="wide")
apply_theme()

render_page_header(
    title="Session Setup & Multimodal Analysis",
    subtitle="Extract automated attendance, observable motion, and acoustic timelines locally."
)

render_ethical_disclaimer(expanded=False)

tab_setup, tab_attendance = st.tabs(["🚀 Setup & Run Analysis", "📋 Review & Confirm Attendance"])

# ---------------- TAB 1: SETUP & EXECUTION ----------------
with tab_setup:
    st.subheader("1. Session Metadata")
    meta_col1, meta_col2, meta_col3 = st.columns(3)
    with meta_col1:
        s_title = st.text_input("Session Title *", value="CS401: Multimodal Systems Lecture").strip()
    with meta_col2:
        s_course = st.text_input("Course Name / Code", value="Computer Science Dept").strip()
    with meta_col3:
        s_date = st.date_input("Session Date", value=datetime.today())

    st.subheader("2. Processing Configuration")
    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        sample_interval = st.slider(
            "Frame Sampling Interval (seconds)",
            min_value=0.5,
            max_value=3.0,
            value=float(DEFAULT_SAMPLING_INTERVAL_SEC),
            step=0.5,
            help="Higher values accelerate processing on standard laptops; 1.0s provides optimal balance."
        )
    with cfg_col2:
        use_sample_media = st.checkbox(
            "🧪 Use Built-in 10-Second Test Media Sample",
            value=False,
            help="Generates genuine video and audio test files locally for rapid pipeline testing."
        )

    st.subheader("3. Media Upload")
    if use_sample_media:
        st.info("ℹ️ Built-in test media mode selected. The system will use local test video and audio files without requiring manual file uploads.")
        video_file = None
        audio_file = None
    else:
        u_col1, u_col2 = st.columns(2)
        with u_col1:
            video_file = st.file_uploader("Upload Classroom Video (.mp4, .avi, .mov)", type=["mp4", "avi", "mov", "mkv"])
        with u_col2:
            audio_file = st.file_uploader("Upload Classroom Audio (Optional: .wav, .mp3, .ogg)", type=["wav", "mp3", "ogg", "flac"])

    st.subheader("4. Privacy Notice & Authorization")
    st.markdown("""
    <div class="disclaimer-box">
        🔒 <b>Local Privacy Assurance:</b> All computer vision, facial tracking, and acoustic signal processing are executed <b>strictly on this device</b>. No video frames, audio streams, or personal identifiers are uploaded to external cloud services or language model APIs.
    </div>
    """, unsafe_allow_html=True)

    auth_consent = st.checkbox("I confirm authorization to process this media under educational data privacy guidelines.", value=False)

    btn_run = st.button("🚀 Start Multimodal Analysis", type="primary", use_container_width=True)

    if btn_run:
        if not auth_consent:
            st.error("Please confirm privacy authorization before running analysis.")
        elif not s_title:
            st.error("Please provide a session title.")
        elif not use_sample_media and video_file is None and audio_file is None:
            st.error("Please upload a video or audio file, or check 'Use Built-in Test Media'.")
        else:
            session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            status_text.text("Initializing session environment...")
            time.sleep(0.3)

            # Determine video and audio paths
            video_path = None
            audio_path = None

            if use_sample_media:
                status_text.text("Generating synthetic media files...")
                media_paths = generate_synthetic_media(SAMPLE_DATA_DIR)
                video_path = media_paths["video_path"]
                audio_path = media_paths["audio_path"]
            else:
                if video_file is not None:
                    status_text.text("Saving uploaded video securely in local temporary storage...")
                    v_ext = Path(video_file.name).suffix
                    v_dest = UPLOADS_DIR / f"{session_id}_video{v_ext}"
                    with open(v_dest, "wb") as f:
                        f.write(video_file.getbuffer())
                    video_path = str(v_dest)

                if audio_file is not None:
                    status_text.text("Saving uploaded audio securely in local temporary storage...")
                    a_ext = Path(audio_file.name).suffix
                    a_dest = UPLOADS_DIR / f"{session_id}_audio{a_ext}"
                    with open(a_dest, "wb") as f:
                        f.write(audio_file.getbuffer())
                    audio_path = str(a_dest)

            # Create Database Record
            create_session(
                session_id=session_id,
                title=s_title,
                course_name=s_course,
                date=str(s_date),
                is_demo=0,
                video_path=video_path,
                audio_path=audio_path,
                sampling_interval_sec=sample_interval
            )

            # --- STEP 1: Video Processing Pipeline ---
            video_result = None
            session_duration = 0.0
            video_timeline = []
            tracks = []

            if video_path and os.path.exists(video_path):
                status_text.text("Running computer vision pipeline: frame extraction & face detection...")
                
                def v_progress(pct, msg):
                    progress_bar.progress(min(0.65, pct * 0.65))
                    status_text.text(msg)

                video_result = process_video_pipeline(
                    video_path=video_path,
                    sampling_interval_sec=sample_interval,
                    progress_callback=v_progress
                )

                if video_result.get("success"):
                    session_duration = video_result["metadata"]["duration_sec"]
                    video_timeline = video_result["timeline"]
                    tracks = video_result["tracks"]
                else:
                    st.warning(f"Video analysis note: {video_result.get('error')}")

            # --- STEP 2: Audio Processing Pipeline ---
            audio_result = None
            audio_timeline = None
            speech_ratio = 0.0
            silence_ratio = 0.0

            if audio_path and os.path.exists(audio_path):
                status_text.text("Running acoustic signal processing: speech activity & silence detection...")
                progress_bar.progress(0.75)

                audio_result = process_audio_pipeline(audio_path)
                if audio_result.get("success"):
                    audio_timeline = audio_result["timeline"]
                    speech_ratio = audio_result["speech_ratio"]
                    silence_ratio = audio_result["silence_ratio"]
                    if session_duration == 0.0:
                        session_duration = audio_result["duration_sec"]
                else:
                    st.warning(f"Audio analysis note: {audio_result.get('error')}")

            # Fallback if both unavailable
            if session_duration == 0.0:
                session_duration = 10.0

            # --- STEP 3: Attendance Verification & Sustained Presence ---
            status_text.text("Applying sustained presence rules to eliminate spurious detections...")
            progress_bar.progress(0.85)

            attendance_records = process_attendance_from_tracks(
                tracks=tracks,
                session_id=session_id,
                session_duration_sec=session_duration,
                filter_noise=True
            )
            save_attendance_records(attendance_records)
            att_summary = calculate_attendance_summary(attendance_records)

            # --- STEP 4: Multimodal Signal Fusion ---
            status_text.text("Fusing multimodal signals into engagement proxy timeline...")
            progress_bar.progress(0.92)

            fused_timeline = compute_session_engagement_timeline(video_timeline, audio_timeline)
            save_engagement_timeline(session_id, fused_timeline)

            # Calculate Engagement Stats
            scores = [pt["composite_engagement"] for pt in fused_timeline if pt.get("composite_engagement") is not None]
            avg_eng = float(np.mean(scores)) if scores else 0.0
            peak_eng = float(np.max(scores)) if scores else 0.0
            lowest_eng = float(np.min(scores)) if scores else 0.0

            # Data Quality Rating
            v_qual = video_result.get("quality") if video_result else None
            a_qual = audio_result.get("quality") if audio_result else None
            quality_data = calculate_data_quality_index(v_qual, a_qual)

            # --- STEP 5: AI Recommendation Engine ---
            status_text.text("Generating explainable pedagogical recommendations...")
            progress_bar.progress(0.97)

            rec_engine = RecommendationEngine()
            recs = rec_engine.evaluate_session(
                duration_sec=session_duration,
                attendance_summary=att_summary,
                engagement_timeline=fused_timeline,
                audio_analysis=audio_result,
                video_quality=v_qual,
                audio_quality=a_qual
            )
            save_recommendations(session_id, recs)

            # --- STEP 6: Save Summary Metrics ---
            summary_payload = {
                "session_id": session_id,
                "average_engagement": round(avg_eng, 3),
                "peak_engagement": round(peak_eng, 3),
                "lowest_engagement": round(lowest_eng, 3),
                "total_detected_tracks": len(attendance_records),
                "confirmed_attendees": 0,
                "speech_ratio": speech_ratio,
                "silence_ratio": silence_ratio,
                "data_quality_score": quality_data["overall_quality_score"],
                "data_quality_notes": "; ".join(quality_data["notes"]) or "Optimal multimodal recording."
            }
            save_session_summary(summary_payload)
            update_session_status(session_id, "completed", duration_sec=session_duration, total_frames=len(video_timeline))

            progress_bar.progress(1.0)
            status_text.text("✅ Multimodal Analysis Completed Successfully!")
            st.session_state["selected_session_id"] = session_id

            st.success(f"Session '{session_id}' analyzed successfully! Proceed to the 'Review & Confirm Attendance' tab or the Dashboard to inspect analytics.")
            st.rerun()


# ---------------- TAB 2: PROVISIONAL ATTENDANCE & MAPPING ----------------
with tab_attendance:
    st.subheader("Attendance Review & Identity Verification")
    st.markdown("""
    <div class="disclaimer-box">
        👤 <b>Identity Limitation Notice:</b> Computer vision detects faces and assigns anonymous track IDs (e.g. <code>Track-001</code>). It <b>never invents student identities</b>. As instructor or administrator, verify and confirm student mappings below to convert provisional records into confirmed attendance.
    </div>
    """, unsafe_allow_html=True)

    all_sessions = list_sessions()
    if not all_sessions:
        st.info("No sessions available yet. Run an analysis or load the demo session.")
    else:
        # Default to selected session in state
        default_idx = 0
        current_sess_id = st.session_state.get("selected_session_id")
        sess_ids = [s["session_id"] for s in all_sessions]
        if current_sess_id in sess_ids:
            default_idx = sess_ids.index(current_sess_id)

        selected_sid = st.selectbox(
            "Select Session to Inspect:",
            options=sess_ids,
            index=default_idx,
            format_func=lambda sid: f"{sid} - {next((s['title'] for s in all_sessions if s['session_id'] == sid), '')}"
        )

        records = get_attendance_records(selected_sid)
        participants = list_participants()

        if not records:
            st.warning("No attendance records found for this session (e.g. video had zero detected faces or audio-only).")
        else:
            # Summary Metrics for attendance
            summary_stats = calculate_attendance_summary(records)

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.metric("Total Observed Tracks", summary_stats["total_tracks"])
            with kpi2:
                st.metric("Present (Sustained)", summary_stats["present_count"])
            with kpi3:
                st.metric("Partial Presence", summary_stats["partial_count"])
            with kpi4:
                st.metric("Confirmed by Instructor", summary_stats["confirmed_count"])

            st.write("")
            st.markdown("#### Provisional Attendance Records")

            rec_df = pd.DataFrame(records)
            rec_df["Confirmation"] = rec_df["is_confirmed"].apply(lambda c: "✅ Confirmed" if c == 1 else "⚠️ Provisional")
            display_cols = ["track_id", "participant_id", "display_name", "first_seen_sec", "last_seen_sec", "duration_observed_sec", "status", "Confirmation", "notes"]
            clean_df = rec_df[display_cols].copy()
            clean_df.columns = ["Track ID", "Student ID", "Student Name", "First Seen (s)", "Last Seen (s)", "Duration (s)", "Attendance Status", "Confirmation", "Sustained Presence Note"]
            st.dataframe(clean_df, use_container_width=True, hide_index=True)

            # Manual Mapping & Confirmation Form
            st.markdown("#### 🔗 Map Anonymous Track to Student")
            with st.form(key="map_track_form"):
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    track_to_map = st.selectbox(
                        "Select Track ID:",
                        options=[r["track_id"] for r in records]
                    )
                with m_col2:
                    p_options = ["-- Unmapped / Anonymous --"] + [f"{p['participant_id']} - {p['display_name']}" for p in participants]
                    selected_p_str = st.selectbox("Assign to Registered Student:", options=p_options)
                with m_col3:
                    new_status = st.selectbox("Override Attendance Status:", ["Present", "Partial", "Absent"])

                btn_confirm_map = st.form_submit_button("✅ Save Mapping & Confirm Attendance", type="primary")

                if btn_confirm_map:
                    target_rec = next((r for r in records if r["track_id"] == track_to_map), None)
                    if target_rec:
                        mapped_pid = None
                        if selected_p_str != "-- Unmapped / Anonymous --":
                            mapped_pid = selected_p_str.split(" - ")[0].strip()

                        map_track_to_participant(
                            record_id=target_rec["record_id"],
                            participant_id=mapped_pid,
                            is_confirmed=1,
                            status=new_status
                        )
                        st.success(f"Successfully mapped {track_to_map} and confirmed attendance!")
                        st.rerun()

            # Export Attendance CSV
            st.write("")
            csv_data = generate_attendance_csv(records)
            st.download_button(
                label="📥 Download Attendance CSV",
                data=csv_data,
                file_name=f"attendance_{selected_sid}.csv",
                mime="text/csv",
                type="secondary"
            )
