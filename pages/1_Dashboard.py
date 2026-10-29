"""
Analytics Dashboard and Interactive Visualizations Page.
Renders responsive Plotly charts for multimodal timelines, attendance duration,
acoustic activity distribution, and multi-session comparisons.
"""

import streamlit as st
import pandas as pd
from modules.database import (
    list_sessions, get_session, get_attendance_records,
    get_engagement_timeline, get_session_summary, get_recommendations
)
from modules.analytics import (
    create_attendance_donut_chart,
    create_track_duration_chart,
    create_engagement_timeline_chart,
    create_session_comparison_chart
)
from modules.attendance import calculate_attendance_summary
from modules.ui_common import apply_theme, render_page_header, render_ethical_disclaimer

st.set_page_config(page_title="Dashboard - Classroom Agent", page_icon="📊", layout="wide")
apply_theme()

render_page_header(
    title="Multimodal Analytics Dashboard",
    subtitle="Interactive visual intelligence across visual tracking, observable motion, and acoustic timelines."
)

render_ethical_disclaimer(expanded=False)

sessions = list_sessions()

if not sessions:
    st.info("💡 **No sessions analyzed yet.** Please navigate to **Session Analysis** or click **'Load Deterministic Demo Session'** on the Home page to explore interactive charts.")
else:
    # Session Selector
    default_sid = st.session_state.get("selected_session_id")
    sess_ids = [s["session_id"] for s in sessions]
    default_idx = sess_ids.index(default_sid) if default_sid in sess_ids else 0

    sel_col1, sel_col2 = st.columns([3, 1])
    with sel_col1:
        current_sid = st.selectbox(
            "Select Session to Display:",
            options=sess_ids,
            index=default_idx,
            format_func=lambda sid: f"{sid} - {next((s['title'] for s in sessions if s['session_id'] == sid), '')}"
        )
    with sel_col2:
        st.session_state["selected_session_id"] = current_sid
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Charts", use_container_width=True):
            st.rerun()

    session_info = get_session(current_sid)
    summary_data = get_session_summary(current_sid) or {}
    attendance_records = get_attendance_records(current_sid)
    timeline_data = get_engagement_timeline(current_sid)

    is_demo = bool(session_info.get("is_demo", 0))

    if is_demo:
        st.markdown("""
        <div style="background-color: rgba(168, 85, 247, 0.15); border: 1px solid #a855f7; border-radius: 8px; padding: 10px 16px; margin-bottom: 20px;">
            🧪 <b>Deterministic Demo Mode Active:</b> This dataset was generated deterministically to demonstrate complete platform functionality without requiring hardware cameras or private recordings.
        </div>
        """, unsafe_allow_html=True)

    # Key Session Metrics Header
    avg_eng = round(summary_data.get("average_engagement", 0.0) * 100, 1)
    peak_eng = round(summary_data.get("peak_engagement", 0.0) * 100, 1)
    speech_ratio = round(summary_data.get("speech_ratio", 0.0) * 100, 1)
    silence_ratio = round(summary_data.get("silence_ratio", 0.0) * 100, 1)
    quality_score = summary_data.get("data_quality_score", 100.0)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Avg Engagement Proxy", f"{avg_eng}%")
    with m2:
        st.metric("Peak Activity Proxy", f"{peak_eng}%")
    with m3:
        st.metric("Speech Ratio", f"{speech_ratio}%")
    with m4:
        st.metric("Silence Ratio", f"{silence_ratio}%")
    with m5:
        st.metric("Data Quality Score", f"{quality_score}/100")

    st.write("")

    # Formula & Signal Transparency Expander
    with st.expander("📐 Transparent Engagement Proxy Formula & Signal Fusion Details", expanded=False):
        st.markdown("""
        The **Multimodal Engagement Proxy Index** $E(t)$ at each discrete second $t$ is computed via a transparent, normalized linear combination:
        $$\\text{Engagement Proxy}(t) = \\frac{w_p S_p(t) + w_m S_m(t) + w_a S_a(t) + w_g S_g(t)}{\\sum w_{\\text{available}}}$$
        
        - **$S_p(t)$ Presence Signal (Weight: 35%):** Normalized visual person/face count.
        - **$S_m(t)$ Observable Motion Signal (Weight: 25%):** Normalized pixel-variance activity from frame differencing (moderate activity represents optimal engagement).
        - **$S_a(t)$ Audio Energy Signal (Weight: 25%):** Normalized RMS sound intensity and speech active flag.
        - **$S_g(t)$ Frontal Pose Proxy (Weight: 15%):** Face aspect ratio symmetry proxy.
        
        *When a modality is absent (e.g. video-only or audio-only), weights automatically re-normalize so the resulting metric remains within [0, 100%].*
        """)

    st.divider()

    # 1. Main Continuous Multimodal Timeline Chart
    st.subheader("📈 Multimodal Timeline Dynamics")
    timeline_fig = create_engagement_timeline_chart(timeline_data)
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)
    else:
        st.info("No timeline data recorded for this session.")

    st.write("")

    # 2. Attendance & Duration Row
    st.subheader("👥 Attendance Analytics & Observation Durations")
    col_donut, col_bars = st.columns([1, 2])

    with col_donut:
        att_summary = calculate_attendance_summary(attendance_records)
        donut_fig = create_attendance_donut_chart(att_summary)
        if donut_fig:
            st.plotly_chart(donut_fig, use_container_width=True)

    with col_bars:
        session_dur = session_info.get("duration_sec", 0.0)
        bar_fig = create_track_duration_chart(attendance_records, session_duration_sec=session_dur)
        if bar_fig:
            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.info("No track duration records found.")

    st.write("")
    st.divider()

    # 3. Data Quality & Diagnostic Breakdown
    st.subheader("🔍 Data Quality & Recording Diagnostics")
    dq_col1, dq_col2 = st.columns([1, 2])
    with dq_col1:
        st.markdown(f"""
        <div class="metric-card" style="padding: 24px;">
            <div class="metric-label">Session Data Quality</div>
            <div class="metric-value" style="color: {'#10b981' if quality_score >= 80 else '#f59e0b'};">{quality_score}%</div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 8px;">
                {'High Reliability' if quality_score >= 80 else 'Moderate Reliability / Review Advised'}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with dq_col2:
        notes = summary_data.get("data_quality_notes", "No quality issues detected.")
        st.markdown(f"""
        <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 18px;">
            <div style="font-size: 0.95rem; font-weight: 600; color: #f8fafc; margin-bottom: 8px;">Sensor & Environmental Audit:</div>
            <p style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.5; margin: 0;">{notes}</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.divider()

    # 4. Cross-Session Comparison
    st.subheader("📊 Cross-Session Comparative Analytics")
    all_summaries = {s["session_id"]: get_session_summary(s["session_id"]) for s in sessions}
    comp_fig = create_session_comparison_chart(sessions, all_summaries)
    if comp_fig:
        st.plotly_chart(comp_fig, use_container_width=True)
