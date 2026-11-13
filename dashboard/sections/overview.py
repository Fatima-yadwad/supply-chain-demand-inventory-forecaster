"""
dashboard/sections/overview.py
-------------------------------
Overview tab: KPI cards + summary statistics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.chart_utils import (
    kpi_card, section_header, fmt_number, bar_chart,
    line_chart, PALETTE
)


def render_overview(df: pd.DataFrame) -> None:
    """Render the Overview tab with KPI cards and summary charts."""

    # ── KPI calculations ─────────────────────────────────────────────────────
    total_units_sold    = df["Units_Sold"].sum()
    total_demand        = df["Demand"].sum()      if "Demand" in df.columns else None
    avg_inventory       = df["Inventory_Level"].mean() if "Inventory_Level" in df.columns else None
    total_units_ordered = df["Units_Ordered"].sum() if "Units_Ordered" in df.columns else None
    total_revenue       = df["Revenue"].sum()     if "Revenue" in df.columns else None
    n_stores            = df["Store"].nunique()
    n_products          = df["Product"].nunique()
    date_min            = df["Date"].min().strftime("%d %b %Y")
    date_max            = df["Date"].max().strftime("%d %b %Y")

    # ── Row 1 KPI cards ───────────────────────────────────────────────────────
    section_header("Key Performance Indicators")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            kpi_card("Total Units Sold", fmt_number(total_units_sold),
                     icon="🛒", color="blue"),
            unsafe_allow_html=True,
        )
    with c2:
        val = fmt_number(total_demand) if total_demand is not None else "N/A"
        st.markdown(
            kpi_card("Total Demand", val, icon="📈", color="green"),
            unsafe_allow_html=True,
        )
    with c3:
        val = fmt_number(avg_inventory, decimals=0) if avg_inventory is not None else "N/A"
        st.markdown(
            kpi_card("Avg Inventory Level", val, icon="🏪", color="purple"),
            unsafe_allow_html=True,
        )
    with c4:
        val = fmt_number(total_units_ordered) if total_units_ordered is not None else "N/A"
        st.markdown(
            kpi_card("Total Units Ordered", val, icon="📦", color="orange"),
            unsafe_allow_html=True,
        )

    # ── Row 2 KPI cards ───────────────────────────────────────────────────────
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        rev_str = fmt_number(total_revenue, prefix="₹", decimals=0) if total_revenue is not None else "N/A"
        st.markdown(
            kpi_card("Total Revenue", rev_str, icon="💰", color="teal"),
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            kpi_card("Number of Stores", str(n_stores), icon="🏬", color="pink"),
            unsafe_allow_html=True,
        )
    with c7:
        st.markdown(
            kpi_card("Number of Products", str(n_products), icon="📱", color="indigo"),
            unsafe_allow_html=True,
        )
    with c8:
        st.markdown(
            kpi_card("Date Coverage", f"{date_min}<br>to {date_max}",
                     icon="📅", color="blue"),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Revenue trend over time ───────────────────────────────────────────────
    section_header("Revenue Trend Over Time")

    monthly = (
        df.groupby(df["Date"].dt.to_period("M"))
          .agg(Revenue=("Revenue", "sum"), Units_Sold=("Units_Sold", "sum"))
          .reset_index()
    )
    monthly["Date"] = monthly["Date"].dt.to_timestamp()

    fig_trend = line_chart(
        monthly, x="Date", y="Revenue",
        title="Monthly Revenue Trend",
        labels={"Revenue": "Revenue (₹)", "Date": "Month"},
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Category and Region breakdown ─────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        section_header("Units Sold by Category")
        cat_df = (
            df.groupby("Category")["Units_Sold"].sum()
              .sort_values(ascending=False)
              .reset_index()
        )
        fig_cat = bar_chart(cat_df, x="Category", y="Units_Sold",
                            title="Units Sold by Category",
                            labels={"Units_Sold": "Units Sold"})
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_b:
        section_header("Revenue by Region")
        reg_df = (
            df.groupby("Region")["Revenue"].sum()
              .sort_values(ascending=False)
              .reset_index()
        )
        import plotly.express as px
        fig_reg = px.pie(
            reg_df, names="Region", values="Revenue",
            title="Revenue Share by Region",
            hole=0.45, color_discrete_sequence=PALETTE,
        )
        fig_reg.update_traces(textinfo="label+percent")
        fig_reg.update_layout(
            font=dict(family="Inter, sans-serif"),
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_reg, use_container_width=True)

    # ── Summary table ─────────────────────────────────────────────────────────
    section_header("Summary Statistics")
    summary = df[["Units_Sold", "Demand", "Units_Ordered",
                  "Inventory_Level", "Revenue"]].describe().round(2)
    st.dataframe(summary, use_container_width=True)
