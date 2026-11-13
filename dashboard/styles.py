"""
dashboard/styles.py
-------------------
Injects custom CSS into the Streamlit app for a professional, modern look.
"""

import streamlit as st


def inject_css():
    """Inject all custom CSS styles into the page."""
    st.markdown(
        """
        <style>
        /* ── Google Font ─────────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* ── Global ──────────────────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }

        .main { background-color: #f0f4f8; }

        /* ── Hide Streamlit default chrome ───────────────────────────── */
        #MainMenu, footer, header { visibility: hidden; }

        /* ── Main header ─────────────────────────────────────────────── */
        .main-header {
            display: flex;
            align-items: center;
            gap: 16px;
            background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(37,99,235,0.3);
        }
        .header-icon { font-size: 2.8rem; }
        .header-title {
            margin: 0 !important;
            color: #ffffff !important;
            font-size: 2rem !important;
            font-weight: 700 !important;
            line-height: 1.1 !important;
        }
        .header-subtitle {
            margin: 4px 0 0 0 !important;
            color: #93c5fd !important;
            font-size: 0.95rem !important;
            font-weight: 400 !important;
        }

        /* ── KPI card ────────────────────────────────────────────────── */
        .kpi-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.07);
            border-left: 5px solid;
            margin-bottom: 8px;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        }
        .kpi-icon   { font-size: 1.6rem; margin-bottom: 6px; }
        .kpi-label  { font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
        .kpi-value  { font-size: 1.75rem; font-weight: 700; color: #1e293b; line-height: 1.1; }
        .kpi-delta  { font-size: 0.78rem; color: #64748b; margin-top: 4px; }

        /* colour presets */
        .kpi-blue   { border-left-color: #2563eb; }
        .kpi-green  { border-left-color: #16a34a; }
        .kpi-purple { border-left-color: #7c3aed; }
        .kpi-orange { border-left-color: #ea580c; }
        .kpi-teal   { border-left-color: #0d9488; }
        .kpi-pink   { border-left-color: #db2777; }
        .kpi-indigo { border-left-color: #4f46e5; }

        /* ── Section header ──────────────────────────────────────────── */
        .section-header {
            font-size: 1.1rem;
            font-weight: 700;
            color: #1e3a5f;
            padding: 10px 0 6px 0;
            border-bottom: 2px solid #2563eb;
            margin-bottom: 18px;
        }

        /* ── Sidebar ─────────────────────────────────────────────────── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e3a5f 0%, #0f1f3d 100%);
        }
        section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stMultiselect label,
        section[data-testid="stSidebar"] .stDateInput label { color: #93c5fd !important; font-weight: 600 !important; font-size: 0.8rem !important; }

        /* ── Tabs ────────────────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: #ffffff;
            border-radius: 12px;
            padding: 6px;
            box-shadow: 0 1px 6px rgba(0,0,0,0.06);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.88rem;
            padding: 8px 20px;
            color: #64748b;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
            color: #ffffff !important;
        }

        /* ── Chart cards ─────────────────────────────────────────────── */
        .chart-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.07);
            margin-bottom: 16px;
        }

        /* ── Footer ──────────────────────────────────────────────────── */
        .footer {
            text-align: center;
            color: #94a3b8;
            font-size: 0.78rem;
            padding: 20px 0 8px;
            border-top: 1px solid #e2e8f0;
            margin-top: 32px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
