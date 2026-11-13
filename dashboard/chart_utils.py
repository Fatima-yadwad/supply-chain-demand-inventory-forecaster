"""
dashboard/chart_utils.py
------------------------
Shared Plotly chart helpers used across all sections.
Keeps chart styling consistent throughout the dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Colour palette ────────────────────────────────────────────────────────────
PALETTE = [
    "#2563eb", "#16a34a", "#dc2626", "#7c3aed",
    "#ea580c", "#0d9488", "#db2777", "#ca8a04",
    "#0284c7", "#65a30d",
]

PLOTLY_TEMPLATE = "plotly_white"

LAYOUT_DEFAULTS = dict(
    template=PLOTLY_TEMPLATE,
    font=dict(family="Inter, sans-serif", size=12, color="#374151"),
    margin=dict(l=40, r=20, t=50, b=40),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#e2e8f0",
        borderwidth=1,
        font=dict(size=11),
    ),
    hoverlabel=dict(
        bgcolor="white",
        font_size=12,
        font_family="Inter, sans-serif",
    ),
)


def _apply_defaults(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply standard layout to any figure."""
    fig.update_layout(title=dict(text=title, font=dict(size=15, weight="bold"), x=0), **LAYOUT_DEFAULTS)
    fig.update_xaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0")
    fig.update_yaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0")
    return fig


def line_chart(df: pd.DataFrame, x: str, y: str | list,
               title: str = "", labels: dict = None) -> go.Figure:
    """Responsive line chart for time-series data."""
    fig = px.line(df, x=x, y=y, title=title, labels=labels or {},
                  color_discrete_sequence=PALETTE, markers=False)
    fig.update_traces(line_width=2.5)
    return _apply_defaults(fig, title)


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "",
              color: str = None, labels: dict = None,
              orientation: str = "v", color_seq=None) -> go.Figure:
    """Standard bar chart."""
    fig = px.bar(df, x=x, y=y, title=title, labels=labels or {},
                 color=color, orientation=orientation,
                 color_discrete_sequence=color_seq or PALETTE)
    fig.update_traces(marker_line_width=0)
    return _apply_defaults(fig, title)


def horizontal_bar(df: pd.DataFrame, x: str, y: str, title: str = "",
                   color_col: str = None) -> go.Figure:
    """Horizontal bar chart — useful for ranking."""
    fig = px.bar(df, x=x, y=y, orientation="h", title=title,
                 color=color_col, color_discrete_sequence=PALETTE,
                 text=x)
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                      marker_line_width=0)
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _apply_defaults(fig, title)


def pie_chart(df: pd.DataFrame, names: str, values: str,
              title: str = "", hole: float = 0.45) -> go.Figure:
    """Donut / pie chart."""
    fig = px.pie(df, names=names, values=values, title=title,
                 hole=hole, color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="label+percent", pull=[0.03] * len(df))
    return _apply_defaults(fig, title)


def scatter_chart(df: pd.DataFrame, x: str, y: str, color: str = None,
                  size: str = None, title: str = "",
                  labels: dict = None) -> go.Figure:
    """Scatter / bubble chart."""
    fig = px.scatter(df, x=x, y=y, color=color, size=size,
                     title=title, labels=labels or {},
                     color_discrete_sequence=PALETTE, opacity=0.75)
    return _apply_defaults(fig, title)


def kpi_card(label: str, value: str, icon: str = "",
             color: str = "blue", delta: str = "") -> str:
    """Return HTML for a styled KPI card."""
    return f"""
    <div class="kpi-card kpi-{color}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {"<div class='kpi-delta'>" + delta + "</div>" if delta else ""}
    </div>
    """


def section_header(text: str) -> None:
    """Render a styled section sub-header."""
    import streamlit as st
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def fmt_number(n, prefix="", suffix="", decimals=0) -> str:
    """Format a number with comma separators."""
    if decimals:
        return f"{prefix}{n:,.{decimals}f}{suffix}"
    return f"{prefix}{int(n):,}{suffix}"
