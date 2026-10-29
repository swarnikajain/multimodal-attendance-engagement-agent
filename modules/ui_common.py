"""
Common UI components, custom styling, and layout helpers for Streamlit.
"""

import streamlit as st
from config import BASE_DIR

CUSTOM_CSS = """
<style>
    /* Global Font and Container Styling */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
    }
    
    /* Header Card */
    .agent-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    .agent-title {
        color: #f8fafc;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    
    .agent-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        line-height: 1.4;
    }
    
    /* Metric Card */
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .metric-card:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 4px;
    }
    .metric-label {
        font-size: 0.82rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Recommendation Card */
    .rec-card {
        background-color: #1e293b;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
        border-top: 1px solid #334155;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
    }
    .rec-card-high {
        border-left-color: #ef4444;
    }
    .rec-card-medium {
        border-left-color: #f59e0b;
    }
    .rec-card-low {
        border-left-color: #10b981;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-present { background-color: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }
    .badge-partial { background-color: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
    .badge-absent { background-color: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }
    .badge-demo { background-color: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #a855f7; }
    .badge-local { background-color: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; }
    
    /* Ethical Notice Box */
    .disclaimer-box {
        background-color: rgba(30, 41, 59, 0.85);
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.85rem;
        color: #cbd5e1;
        margin-bottom: 20px;
        line-height: 1.45;
    }
</style>
"""


def apply_theme():
    """Injects custom CSS theme into the active Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_ethical_disclaimer(expanded: bool = False):
    """
    Renders standardized transparency and limitations disclosure.
    Ensures ethical boundaries are clearly communicated throughout the app.
    """
    with st.expander("ℹ️ Ethical Transparency & Observational Metric Limitations", expanded=expanded):
        st.markdown("""
        **Crucial Methodological Limitations:**
        - **Observational Proxy Only:** Engagement metrics are calculated from observable physical activity, head orientation proxies, and acoustic energy. They **do not measure internal mental states, cognitive attention, understanding, or emotional affect**.
        - **Non-Consequential:** These analytics are designed exclusively to assist instructors with pacing and curriculum reflection. They must **never** be used to grade, discipline, or penalize students.
        - **Privacy by Design:** Face detection identifies bounding coordinates; it does **not** perform automatic identity recognition without operator verification. All computation runs 100% on your local machine.
        """)


def render_page_header(title: str, subtitle: str, badge_text: str = "Local AI Engine"):
    """Renders a standardized page header."""
    st.markdown(f"""
    <div class="agent-header">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div class="agent-title">{title}</div>
                <div class="agent-subtitle">{subtitle}</div>
            </div>
            <span class="badge badge-local">🔒 {badge_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
