
"""
dashboard/sections/demand.py
-----------------------------
Demand Analysis tab: trends, patterns, breakdowns.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.chart_utils import (
    section_header, PALETTE, LAYOUT_DEFAULTS,
    fmt_number, kpi_card
)


def render_demand(df: pd.DataFrame) -> None:
    """Render the Demand Analysis tab."""

    required_columns = [
        "Date", "Week", "Day_Name", "Demand",
        "Units_Sold", "Category", "Region", "Product"
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(f"Missing columns for Demand Analysis: {missing}")
        return

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    # ── KPIs ─────────────────────────────────────────────────────────────
    section_header("Demand KPIs")

    total_demand = df["Demand"].sum()
    total_sold = df["Units_Sold"].sum()

    # Demand is the expected quantity; Units Sold is the actual quantity sold.
    # Positive difference represents demand not fulfilled.
    unfulfilled = max(total_demand - total_sold, 0)

    fulfilment_rate = (
        total_sold / total_demand * 100
        if total_demand > 0 else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            kpi_card(
                "Total Demand",
                fmt_number(total_demand),
                icon="📈",
                color="blue"
            ),
            unsafe_allow_html=True,
        )

    with c2:
        avg_d = df["Demand"].mean()

        st.markdown(
            kpi_card(
                "Average Demand / Record",
                fmt_number(avg_d, decimals=1),
                icon="📊",
                color="green"
            ),
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            kpi_card(
                "Unfulfilled Demand",
                fmt_number(unfulfilled),
                icon="⚠️",
                color="orange"
            ),
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            kpi_card(
                "Fulfillment Rate",
                f"{fulfilment_rate:.1f}%",
                icon="✅",
                color="teal"
            ),
            unsafe_allow_html=True,
        )

    st.caption(
        "Fulfillment rate is calculated as Units Sold ÷ Demand × 100. "
        "Unfulfilled demand is the positive difference between demand and units sold."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Demand vs Units Sold over time ───────────────────────────────────
    section_header("Demand Trends Over Time")

    weekly = (
        df.groupby("Week")
        .agg(
            Demand=("Demand", "sum"),
            Units_Sold=("Units_Sold", "sum")
        )
        .reset_index()
    )

    weekly["Week"] = pd.to_datetime(weekly["Week"])

    fig_trend = go.Figure()

    fig_trend.add_trace(
        go.Scatter(
            x=weekly["Week"],
            y=weekly["Demand"],
            name="Demand",
            line=dict(color=PALETTE[0], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(37,99,235,0.08)",
        )
    )

    fig_trend.add_trace(
        go.Scatter(
            x=weekly["Week"],
            y=weekly["Units_Sold"],
            name="Units Sold",
            line=dict(color=PALETTE[1], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(22,163,74,0.08)",
        )
    )

    fig_trend.update_layout(
        title="Weekly Demand vs Units Sold",
        xaxis_title="Week",
        yaxis_title="Units",
        **LAYOUT_DEFAULTS,
    )

    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Monthly & daily patterns ────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        section_header("Monthly Demand Pattern")

        # Group by year AND month to avoid mixing January across years.
        monthly = (
            df.groupby(["Year", "Month"])["Demand"]
            .sum()
            .reset_index()
        )

        monthly["Month_Name"] = pd.to_datetime(
            monthly["Year"].astype(str) + "-"
            + monthly["Month"].astype(str) + "-01"
        ).dt.strftime("%b %Y")

        fig_m = px.bar(
            monthly,
            x="Month_Name",
            y="Demand",
            title="Total Demand by Month",
            color="Demand",
            color_continuous_scale="Blues",
            labels={
                "Demand": "Total Demand",
                "Month_Name": "Month"
            },
        )

        fig_m.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False,
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig_m, use_container_width=True)

    with col_b:
        section_header("Daily Demand Pattern")

        day_order = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]

        daily = (
            df.groupby("Day_Name")["Demand"]
            .mean()
            .reindex(day_order)
            .dropna()
            .reset_index()
        )

        daily.columns = ["Day", "Avg_Demand"]

        fig_d = px.bar(
            daily,
            x="Day",
            y="Avg_Demand",
            title="Average Demand by Day of Week",
            color="Avg_Demand",
            color_continuous_scale="Teal",
            labels={"Avg_Demand": "Average Demand"},
        )

        fig_d.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False
        )

        st.plotly_chart(fig_d, use_container_width=True)

    # ── Demand by Category and Region ───────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        section_header("Demand by Category")

        cat_d = (
            df.groupby("Category")[["Demand", "Units_Sold"]]
            .sum()
            .sort_values("Demand", ascending=False)
            .reset_index()
        )

        fig_cat = px.bar(
            cat_d,
            x="Demand",
            y="Category",
            orientation="h",
            title="Demand by Category",
            color="Demand",
            color_continuous_scale="Blues",
            labels={"Demand": "Total Demand"},
        )

        fig_cat.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed")
        )

        st.plotly_chart(fig_cat, use_container_width=True)

    with col_d:
        section_header("Demand by Region")

        reg_d = (
            df.groupby("Region")[["Demand", "Units_Sold"]]
            .sum()
            .reset_index()
        )

        fig_reg = px.bar(
            reg_d,
            x="Region",
            y=["Demand", "Units_Sold"],
            barmode="group",
            title="Demand vs Units Sold by Region",
            color_discrete_sequence=[PALETTE[0], PALETTE[1]],
            labels={
                "value": "Units",
                "variable": "Metric"
            },
        )

        fig_reg.update_layout(**LAYOUT_DEFAULTS)

        st.plotly_chart(fig_reg, use_container_width=True)

    # ── Top 10 products by demand ───────────────────────────────────────
    section_header("Top 10 Products by Demand")

    prod_d = (
        df.groupby("Product")["Demand"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig_prod = px.bar(
        prod_d,
        x="Product",
        y="Demand",
        title="Top 10 Products by Total Demand",
        color="Demand",
        color_continuous_scale="Purples",
        labels={"Demand": "Total Demand"},
    )

    fig_prod.update_layout(
        **LAYOUT_DEFAULTS,
        coloraxis_showscale=False
    )

    st.plotly_chart(fig_prod, use_container_width=True)
