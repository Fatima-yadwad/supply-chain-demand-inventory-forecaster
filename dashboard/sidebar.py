"""
dashboard/sidebar.py
--------------------
Renders the left-hand navigation/filter sidebar.
Returns a dict of filter values used by apply_filters().
"""

import streamlit as st
import pandas as pd
from datetime import date


def render_sidebar(df: pd.DataFrame) -> dict:
    """
    Render sidebar with dynamic filters based on dataset columns.

    Parameters
    ----------
    df : Full cleaned dataset (before filtering)

    Returns
    -------
    dict with keys: date_range, stores, regions, categories, products
    """
    with st.sidebar:
        # ── Branding ─────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center; padding: 12px 0 20px 0;">
                <div style="font-size:2.2rem;">📦</div>
                <div style="font-size:1rem; font-weight:700; color:#93c5fd; margin-top:4px;">
                    Supply Chain<br>Dashboard
                </div>
                <div style="font-size:0.72rem; color:#64748b; margin-top:2px;">
                    Demand &amp; Inventory Analytics
                </div>
            </div>
            <hr style="border-color:#1e3a5f; margin-bottom:16px;">
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p style="font-size:0.85rem; font-weight:700; color:#93c5fd; '
            'letter-spacing:0.08em; text-transform:uppercase;">FILTERS</p>',
            unsafe_allow_html=True,
        )

        # ── Date range ────────────────────────────────────────────────────────
        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()

        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        # Ensure always a tuple of two dates
        if isinstance(date_range, date):
            date_range = (date_range, max_date)
        if len(date_range) == 1:
            date_range = (date_range[0], max_date)

        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

        # ── Region ────────────────────────────────────────────────────────────
        all_regions = sorted(df["Region"].dropna().unique().tolist())
        regions = st.multiselect(
            "Region",
            options=all_regions,
            default=[],
            placeholder="All regions",
        )

        # ── Store ─────────────────────────────────────────────────────────────
        all_stores = sorted(df["Store"].dropna().unique().tolist())
        stores = st.multiselect(
            "Store",
            options=all_stores,
            default=[],
            placeholder="All stores",
        )

        # ── Category ──────────────────────────────────────────────────────────
        all_categories = sorted(df["Category"].dropna().unique().tolist())
        categories = st.multiselect(
            "Category",
            options=all_categories,
            default=[],
            placeholder="All categories",
        )

        # ── Product ───────────────────────────────────────────────────────────
        all_products = sorted(df["Product"].dropna().unique().tolist())
        products = st.multiselect(
            "Product",
            options=all_products,
            default=[],
            placeholder="All products",
        )

        st.markdown("<hr style='border-color:#1e3a5f; margin:20px 0 12px'>", unsafe_allow_html=True)

        # ── Dataset info ──────────────────────────────────────────────────────
        st.markdown(
            f"""
            <div style="font-size:0.72rem; color:#64748b; line-height:1.6;">
                <b style="color:#93c5fd">Dataset Info</b><br>
                Total Records&nbsp;: {len(df):,}<br>
                Date Coverage&nbsp;: {min_date} to {max_date}<br>
                Stores&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {df['Store'].nunique()}<br>
                Products&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {df['Product'].nunique()}<br>
                Categories&nbsp;&nbsp;&nbsp;&nbsp;: {df['Category'].nunique()}
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "date_range": date_range,
        "stores":     stores,
        "regions":    regions,
        "categories": categories,
        "products":   products,
    }
