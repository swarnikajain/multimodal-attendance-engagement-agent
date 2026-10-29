"""
Multimodal Attendance & Engagement Agent - Main Application Entrypoint & Home Dashboard.
Evaluation platform for FutureSkills Prime AI/ML.
"""

import streamlit as st
from config import DATABASE_PATH
from modules.database import init_db, get_overall_stats, list_sessions, delete_session
from modules.demo_data import seed_demo_session, seed_sample_participants_if_empty
from modules.ui_common import apply_theme, render_ethical_disclaimer, render_page_header

# Streamlit Page Config
st.set_page_config(
    page_title="Multimodal Attendance & Engagement Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema on startup
init_db()

# Apply Custom CSS styling
apply_theme()

# Top Header
render_page_header(
    title="Multimodal Attendance & Engagement Agent",
    subtitle="Privacy-first, local classroom intelligence platform combining computer vision & acoustic analytics for pedagogical insights.",
    badge_text="100% On-Device • Zero Cloud Transmission"
)

# Render Global Ethical Disclaimer
render_ethical_disclaimer(expanded=False)

# Fetch Aggregated Stats
stats = get_overall_stats()

# KPI Metric Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Analyzed Sessions</div>
        <div class="metric-value">{stats['total_sessions']}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Registered Participants</div>
        <div class="metric-value">{stats['total_participants']}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Avg Attendance Rate</div>
        <div class="metric-value">{stats['attendance_rate_pct']}%</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Avg Engagement Proxy</div>
        <div class="metric-value">{stats['average_engagement_pct']}%</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")  # Spacing

# Quick Action Toolbar
st.subheader("⚡ Quick Actions")
act_col1, act_col2, act_col3 = st.columns(3)

with act_col1:
    if st.button("🚀 Load Deterministic Demo Session", use_container_width=True, type="primary"):
        demo_id = seed_demo_session(session_id="demo_session_01")
        st.success(f"Loaded demo session '{demo_id}' with deterministic multimodal analytics!")
        st.rerun()

with act_col2:
    if st.button("👥 Seed Sample Student Roster", use_container_width=True):
        seed_sample_participants_if_empty()
        st.success("Populated registered roster with 8 sample student records!")
        st.rerun()

with act_col3:
    if st.button("🔄 Refresh Dashboard Data", use_container_width=True):
        st.rerun()

st.write("")
st.divider()

# Recent Sessions & Activity Overview
st.subheader("🕒 Session History")

sessions = list_sessions()

if not sessions:
    st.info("💡 **No sessions recorded yet.** Click **'Load Deterministic Demo Session'** above to immediately explore realistic analytics, or navigate to **Session Analysis** in the sidebar to process classroom media.")
else:
    for s in sessions:
        with st.container():
            is_demo = bool(s.get("is_demo", 0))
            demo_tag = '<span class="badge badge-demo">Simulated Demo</span>' if is_demo else '<span class="badge badge-local">Local Media</span>'
            status_tag = f'<span class="badge badge-present">{s.get("status", "completed").upper()}</span>'

            card_html = f"""
            <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.1rem; font-weight: 600; color: #f8fafc;">{s.get('title')}</span>
                    <span style="margin-left: 10px;">{demo_tag}</span>
                    <span style="margin-left: 6px;">{status_tag}</span>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">
                        Course: <b>{s.get('course_name') or 'N/A'}</b> &nbsp;|&nbsp; 
                        Date: <b>{s.get('date')}</b> &nbsp;|&nbsp; 
                        Duration: <b>{round(s.get('duration_sec', 0.0), 1)}s</b>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
            with btn_col1:
                if st.button(f"📊 View Analytics", key=f"view_{s['session_id']}"):
                    st.session_state["selected_session_id"] = s["session_id"]
                    st.switch_page("pages/1_Dashboard.py")
            with btn_col2:
                if st.button(f"🗑️ Delete", key=f"del_{s['session_id']}"):
                    delete_session(s["session_id"])
                    st.warning(f"Deleted session '{s['session_id']}'.")
                    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎓 About System")
st.sidebar.caption("""
**Multimodal Attendance & Engagement Agent**  
Local-first, privacy-conscious classroom intelligence. Built with Streamlit, OpenCV, Plotly & NumPy for FutureSkills Prime.
""")
