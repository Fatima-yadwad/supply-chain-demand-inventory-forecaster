
"""
Supply Chain Demand & Inventory Forecaster
Main Streamlit dashboard application.
"""

import sys
from pathlib import Path

import streamlit as st

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Supply Chain Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Internal imports
from dashboard.data_loader import load_data, apply_filters
from dashboard.sidebar import render_sidebar
from dashboard.sections.overview import render_overview
from dashboard.sections.demand import render_demand
from dashboard.sections.sales import render_sales
from dashboard.sections.inventory import render_inventory
from dashboard.styles import inject_css

# Inject custom CSS
inject_css()

# Load dataset
df_raw = load_data()

# Sidebar filters
filters = render_sidebar(df_raw)

# Apply filters
df = apply_filters(df_raw, filters)

# Header
st.markdown(
    """
    <div class="main-header">
        <span class="header-icon">📦</span>
        <div>
            <h1 class="header-title">Supply Chain Dashboard</h1>
            <p class="header-subtitle">Demand & Inventory Intelligence Platform</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Empty state
if df.empty:
    st.warning(
        "No data matches the selected filters. "
        "Please adjust the sidebar filters."
    )
    st.stop()

# Navigation tabs
tab_overview, tab_demand, tab_sales, tab_inventory = st.tabs(
    [
        "📊 Overview",
        "📈 Demand Analysis",
        "💰 Sales Analysis",
        "🏪 Inventory Analysis",
    ]
)

with tab_overview:
    render_overview(df)

with tab_demand:
    render_demand(df)

with tab_sales:
    render_sales(df)

with tab_inventory:
    render_inventory(df)

# Footer
st.markdown(
    """
    <div class="footer">
        Supply Chain Demand &amp; Inventory Forecaster &nbsp;|&nbsp;
        Data Analytics Project &nbsp;|&nbsp; 2024
    </div>
    """,
    unsafe_allow_html=True,
)
