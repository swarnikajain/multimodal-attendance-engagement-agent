"""
Reports, Exports & AI Recommendations Page.
Presents prioritized pedagogical recommendations with supporting evidence and caveats.
Provides downloadable CSV, JSON, and Markdown summaries for archival and evaluation.
"""

import streamlit as st
import pandas as pd
from modules.database import (
    list_sessions, get_session, get_attendance_records,
    get_session_summary, get_recommendations, get_engagement_timeline
)
from modules.report_generator import (
    generate_attendance_csv,
    generate_session_summary_json,
    generate_readable_markdown_report
)
from modules.ui_common import apply_theme, render_page_header, render_ethical_disclaimer

st.set_page_config(page_title="Reports - Classroom Agent", page_icon="📑", layout="wide")
apply_theme()

render_page_header(
    title="Pedagogical Reports & Data Exports",
    subtitle="Explainable rule-based teaching recommendations, verifiable evidence, and multi-format reports."
)

render_ethical_disclaimer(expanded=False)

sessions = list_sessions()

if not sessions:
    st.info("💡 **No sessions available.** Run an analysis or click 'Load Deterministic Demo Session' on the Home page.")
else:
    default_sid = st.session_state.get("selected_session_id")
    sess_ids = [s["session_id"] for s in sessions]
    default_idx = sess_ids.index(default_sid) if default_sid in sess_ids else 0

    col_select, col_refresh = st.columns([3, 1])
    with col_select:
        current_sid = st.selectbox(
            "Select Session for Report Generation:",
            options=sess_ids,
            index=default_idx,
            format_func=lambda sid: f"{sid} - {next((s['title'] for s in sessions if s['session_id'] == sid), '')}"
        )
    with col_refresh:
        st.session_state["selected_session_id"] = current_sid
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    session_info = get_session(current_sid)
    summary_data = get_session_summary(current_sid) or {}
    attendance_records = get_attendance_records(current_sid)
    recs = get_recommendations(current_sid)
    timeline_data = get_engagement_timeline(current_sid)

    # ---------------- 1. AI RECOMMENDATION ENGINE SECTION ----------------
    st.subheader("💡 AI Pedagogical Suggestions & Observations")
    st.caption("Generated locally using rule-based metrics evaluation. Strictly non-punitive guidance for instructor reflection.")

    if not recs:
        st.success("✅ **Balanced Session:** All visual presence, observable motion, and acoustic signals remained within standard parameters. No intervention triggers detected.")
    else:
        for r in recs:
            prio = r.get("priority", "Medium").lower()
            prio_class = f"rec-card-{prio}"
            prio_badge_color = "#ef4444" if prio == "high" else ("#f59e0b" if prio == "medium" else "#10b981")

            html_card = f"""
            <div class="rec-card {prio_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #f8fafc; font-size: 1.05rem;">{r.get('category')}</span>
                    <span style="background-color: rgba(255,255,255,0.1); color: {prio_badge_color}; border: 1px solid {prio_badge_color}; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600;">
                        {r.get('priority').upper()} PRIORITY
                    </span>
                </div>
                <div style="color: #cbd5e1; font-size: 0.9rem; margin-bottom: 6px;">
                    <b>Trigger Observation:</b> {r.get('observation')}
                </div>
                <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 8px;">
                    <b>Supporting Evidence:</b> <code>{r.get('supporting_metric')}</code>
                </div>
                <div style="background-color: rgba(37, 99, 235, 0.15); border: 1px solid #2563eb; border-radius: 6px; padding: 10px; margin-bottom: 8px; color: #e2e8f0; font-size: 0.88rem;">
                    🎯 <b>Actionable Teaching Suggestion:</b> {r.get('suggestion')}
                </div>
                <div style="color: #94a3b8; font-size: 0.82rem; font-style: italic;">
                    ⚠️ <b>Pedagogical Caveat:</b> {r.get('limitation_caveat')}
                </div>
            </div>
            """
            st.markdown(html_card, unsafe_allow_html=True)

    st.write("")
    st.divider()

    # ---------------- 2. DOWNLOAD TOOLBAR ----------------
    st.subheader("📥 Export Reports")

    csv_str = generate_attendance_csv(attendance_records)
    json_str = generate_session_summary_json(session_info, summary_data, attendance_records, recs, timeline_data)
    md_str = generate_readable_markdown_report(session_info, summary_data, attendance_records, recs)

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.download_button(
            label="📄 Download Attendance (CSV)",
            data=csv_str,
            file_name=f"attendance_{current_sid}.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
    with col_d2:
        st.download_button(
            label="📦 Download Summary (JSON)",
            data=json_str,
            file_name=f"session_summary_{current_sid}.json",
            mime="application/json",
            use_container_width=True
        )
    with col_d3:
        st.download_button(
            label="📝 Download Report (Markdown)",
            data=md_str,
            file_name=f"pedagogical_report_{current_sid}.md",
            mime="text/markdown",
            use_container_width=True
        )

    st.write("")

    # ---------------- 3. REPORT PREVIEW TABS ----------------
    st.subheader("👁️ Live Report Preview")
    tab_md, tab_json, tab_csv = st.tabs(["📝 Formatted Executive Report", "📦 Full JSON Data Schema", "📋 Attendance Table"])

    with tab_md:
        st.markdown(md_str)

    with tab_json:
        st.json(json_str)

    with tab_csv:
        if attendance_records:
            df_att = pd.DataFrame(attendance_records)
            cols = ["track_id", "participant_id", "display_name", "first_seen_sec", "last_seen_sec", "duration_observed_sec", "status", "is_confirmed"]
            st.dataframe(df_att[cols], use_container_width=True, hide_index=True)
        else:
            st.info("No attendance records to display.")
