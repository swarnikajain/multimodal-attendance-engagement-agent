"""
Plotly interactive visualization and comparative analytics module.
Generates polished, responsive visual charts for attendance, engagement timelines,
audio distribution, and cross-session comparisons.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Plotly imports
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    go = None
    px = None
    PLOTLY_AVAILABLE = False


# Theme styling constants
PRIMARY_COLOR = "#2563EB"     # Royal Blue
ACCENT_GREEN = "#10B981"      # Emerald Green
ACCENT_AMBER = "#F59E0B"      # Amber
ACCENT_RED = "#EF4444"        # Crimson Red
BACKGROUND_CARD = "#1E293B"   # Slate 800
GRID_COLOR = "rgba(148, 163, 184, 0.15)"


def create_attendance_donut_chart(summary: Dict[str, Any]) -> Any:
    """
    Renders an interactive donut chart of attendance status distribution.
    """
    if not PLOTLY_AVAILABLE:
        return None

    labels = ["Present", "Partial", "Absent"]
    values = [
        summary.get("present_count", 0),
        summary.get("partial_count", 0),
        summary.get("absent_count", 0)
    ]
    colors = [ACCENT_GREEN, ACCENT_AMBER, ACCENT_RED]

    if sum(values) == 0:
        # Empty state figure
        fig = go.Figure()
        fig.add_annotation(
            text="No attendance records available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#94A3B8")
        )
        fig.update_layout(template="plotly_dark", height=280, margin=dict(l=20, r=20, t=30, b=20))
        return fig

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors),
        textinfo="label+percent",
        hoverinfo="label+value+percent",
        textfont=dict(size=13, color="#FFFFFF")
    )])

    fig.update_layout(
        title=dict(text="Attendance Status Distribution", font=dict(size=16, color="#F8FAFC")),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )
    return fig


def create_track_duration_chart(records: List[Dict[str, Any]], session_duration_sec: float) -> Any:
    """
    Horizontal bar chart showing observed duration per track vs total session time.
    """
    if not PLOTLY_AVAILABLE or not records:
        return None

    df = pd.DataFrame(records)
    # Sort by duration
    df = df.sort_values(by="duration_observed_sec", ascending=True)

    # Determine colors by status
    status_color_map = {
        "Present": ACCENT_GREEN,
        "Partial": ACCENT_AMBER,
        "Absent": ACCENT_RED
    }
    bar_colors = [status_color_map.get(s, "#64748B") for s in df["status"]]

    fig = go.Figure()

    # Observed duration bars
    fig.add_trace(go.Bar(
        y=df["track_id"] + df["participant_id"].apply(lambda p: f" ({p})" if p else ""),
        x=df["duration_observed_sec"],
        orientation="h",
        marker=dict(color=bar_colors),
        hovertemplate="<b>%{y}</b><br>Observed: %{x:.1f}s<br>Status: %{customdata}<extra></extra>",
        customdata=df["status"],
        name="Observed Duration"
    ))

    # Reference line for total session duration
    if session_duration_sec > 0:
        fig.add_vline(
            x=session_duration_sec,
            line_dash="dash",
            line_color="#94A3B8",
            annotation_text=f"Total ({int(session_duration_sec)}s)",
            annotation_position="top right"
        )

    fig.update_layout(
        title=dict(text="Observation Duration per Track", font=dict(size=16, color="#F8FAFC")),
        xaxis=dict(title="Observed Duration (seconds)", gridcolor=GRID_COLOR),
        yaxis=dict(title="Track ID / Participant", tickfont=dict(size=11)),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(320, len(df) * 32),
        margin=dict(l=20, r=30, t=45, b=30),
        showlegend=False
    )
    return fig


def create_engagement_timeline_chart(
    timeline: List[Dict[str, Any]],
    silence_intervals: Optional[List[Dict[str, float]]] = None
) -> Any:
    """
    Multimodal continuous line chart showing Composite Engagement, Motion, and Audio Energy.
    """
    if not PLOTLY_AVAILABLE or not timeline:
        return None

    df = pd.DataFrame(timeline)

    fig = go.Figure()

    # 1. Composite Engagement Proxy
    if "composite_engagement" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["timestamp_sec"],
            y=df["composite_engagement"] * 100.0,
            mode="lines",
            name="Engagement Proxy",
            line=dict(color=PRIMARY_COLOR, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.12)",
            hovertemplate="Time: %{x:.1f}s<br>Proxy Score: %{y:.1f}%<extra></extra>"
        ))

    # 2. Observable Motion Score
    if "motion_score" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["timestamp_sec"],
            y=df["motion_score"] * 100.0,
            mode="lines",
            name="Observable Motion",
            line=dict(color="#10B981", width=1.5, dash="dot"),
            hovertemplate="Time: %{x:.1f}s<br>Motion: %{y:.1f}%<extra></extra>"
        ))

    # 3. Audio Energy (if available)
    if "audio_energy" in df.columns and df["audio_energy"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["timestamp_sec"],
            y=df["audio_energy"] * 100.0,
            mode="lines",
            name="Audio Energy",
            line=dict(color="#F59E0B", width=1.5),
            hovertemplate="Time: %{x:.1f}s<br>Audio Energy: %{y:.1f}%<extra></extra>"
        ))

    # Mark prolonged silence intervals if provided
    if silence_intervals:
        for s in silence_intervals:
            fig.add_vrect(
                x0=s["start_sec"],
                x1=s["end_sec"],
                fillcolor="rgba(239, 68, 68, 0.10)",
                layer="below",
                line_width=1,
                line_dash="dash",
                line_color="rgba(239, 68, 68, 0.4)",
                annotation_text="Prolonged Silence",
                annotation_position="top left",
                annotation_font=dict(size=10, color="#EF4444")
            )

    fig.update_layout(
        title=dict(text="Multimodal Engagement & Activity Dynamics Timeline", font=dict(size=16, color="#F8FAFC")),
        xaxis=dict(title="Session Timeline (seconds)", gridcolor=GRID_COLOR),
        yaxis=dict(title="Normalized Index (%)", range=[0, 105], gridcolor=GRID_COLOR),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_session_comparison_chart(sessions: List[Dict[str, Any]], summaries: Dict[str, Dict[str, Any]]) -> Any:
    """
    Compares metrics across multiple completed sessions.
    Shows empty state if fewer than 2 valid sessions.
    """
    if not PLOTLY_AVAILABLE:
        return None

    # Filter to completed sessions with summary data
    valid_sessions = []
    for s in sessions:
        sid = s["session_id"]
        if sid in summaries and summaries[sid]:
            valid_sessions.append({
                "title": s.get("title", sid),
                "date": s.get("date", ""),
                "avg_engagement": round(summaries[sid].get("average_engagement", 0.0) * 100, 1),
                "speech_ratio": round(summaries[sid].get("speech_ratio", 0.0) * 100, 1),
                "data_quality": summaries[sid].get("data_quality_score", 100.0)
            })

    if len(valid_sessions) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for cross-session comparison.<br>At least 2 completed sessions are required.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#94A3B8"),
            align="center"
        )
        fig.update_layout(template="plotly_dark", height=280, margin=dict(l=20, r=20, t=30, b=20))
        return fig

    df = pd.DataFrame(valid_sessions)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["title"],
        y=df["avg_engagement"],
        name="Avg Engagement Proxy (%)",
        marker_color=PRIMARY_COLOR
    ))
    fig.add_trace(go.Bar(
        x=df["title"],
        y=df["speech_ratio"],
        name="Speech Ratio (%)",
        marker_color="#10B981"
    ))
    fig.add_trace(go.Bar(
        x=df["title"],
        y=df["data_quality"],
        name="Data Quality (%)",
        marker_color="#8B5CF6"
    ))

    fig.update_layout(
        title=dict(text="Cross-Session Pedagogical Metrics Comparison", font=dict(size=16, color="#F8FAFC")),
        barmode="group",
        xaxis=dict(title="Sessions", gridcolor=GRID_COLOR),
        yaxis=dict(title="Score / Percentage (%)", range=[0, 105], gridcolor=GRID_COLOR),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=360,
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig
