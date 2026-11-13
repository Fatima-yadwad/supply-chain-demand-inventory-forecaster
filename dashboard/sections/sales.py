
"""
dashboard/sections/sales.py
----------------------------
Sales Analysis tab: revenue, pricing, discounts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.chart_utils import (
    section_header, PALETTE, LAYOUT_DEFAULTS, kpi_card, fmt_number
)


def render_sales(df: pd.DataFrame) -> None:
    """Render the Sales Analysis tab."""

    has_revenue = "Revenue" in df.columns
    has_price = "Price" in df.columns
    has_discount = "Discount_Pct" in df.columns

    # Revenue is estimated using Units Sold * Price.
    # Discounts are analyzed separately and are not deducted.

    # ── KPIs ─────────────────────────────────────────────────────────────
    section_header("Sales KPIs — Estimated Gross Revenue")

    st.caption(
        "Gross revenue is estimated as Units Sold × Price. "
        "Discounts are analyzed separately and are not deducted."
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        rev = df["Revenue"].sum() if has_revenue else 0
        st.markdown(
            kpi_card(
                "Estimated Gross Revenue",
                fmt_number(rev, prefix="₹"),
                icon="💰",
                color="blue"
            ),
            unsafe_allow_html=True,
        )

    with c2:
        avg_rev = df["Revenue"].mean() if has_revenue else 0
        st.markdown(
            kpi_card(
                "Avg Revenue / Record",
                fmt_number(avg_rev, prefix="₹", decimals=0),
                icon="📋",
                color="green"
            ),
            unsafe_allow_html=True,
        )

    with c3:
        avg_disc = df["Discount_Pct"].mean() if has_discount else 0
        st.markdown(
            kpi_card(
                "Avg Discount",
                f"{avg_disc:.1f}%",
                icon="🏷️",
                color="orange"
            ),
            unsafe_allow_html=True,
        )

    with c4:
        top_cat = (
            df.groupby("Category")["Revenue"].sum().idxmax()
            if has_revenue and not df.empty
            else "N/A"
        )
        st.markdown(
            kpi_card(
                "Top Category",
                top_cat,
                icon="🏆",
                color="purple"
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Estimated Gross Revenue by Category ──────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        section_header("Estimated Gross Revenue by Category")

        cat_rev = (
            df.groupby("Category")["Revenue"].sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        fig_cat = px.bar(
            cat_rev,
            x="Category",
            y="Revenue",
            title="Estimated Gross Revenue by Category",
            color="Revenue",
            color_continuous_scale="Blues",
            labels={"Revenue": "Estimated Gross Revenue (₹)"},
        )

        fig_cat.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False
        )

        st.plotly_chart(fig_cat, use_container_width=True)

    with col_b:
        section_header("Estimated Gross Revenue by Region")

        reg_rev = (
            df.groupby("Region")["Revenue"].sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        fig_reg = px.pie(
            reg_rev,
            names="Region",
            values="Revenue",
            title="Gross Revenue Share by Region",
            hole=0.45,
            color_discrete_sequence=PALETTE,
        )

        fig_reg.update_traces(
            textinfo="label+percent+value",
            texttemplate="%{label}<br>₹%{value:,.0f}"
        )

        fig_reg.update_layout(**LAYOUT_DEFAULTS)

        st.plotly_chart(fig_reg, use_container_width=True)

    # ── Estimated Gross Revenue by Store ─────────────────────────────────
    section_header("Estimated Gross Revenue by Store")

    store_rev = (
        df.groupby("Store")["Revenue"].sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig_store = px.bar(
        store_rev,
        x="Revenue",
        y="Store",
        orientation="h",
        title="Estimated Gross Revenue by Store",
        color="Revenue",
        color_continuous_scale="Teal",
        labels={"Revenue": "Estimated Gross Revenue (₹)"},
        text="Revenue",
    )

    fig_store.update_traces(
        texttemplate="₹%{text:,.0f}",
        textposition="outside"
    )

    fig_store.update_layout(
        **LAYOUT_DEFAULTS,
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
    )

    st.plotly_chart(fig_store, use_container_width=True)

    # ── Product-wise Sales ───────────────────────────────────────────────
    section_header("Product-wise Sales")

    col_c, col_d = st.columns([3, 2])

    with col_c:
        prod_rev = (
            df.groupby("Product")
            .agg(
                Revenue=("Revenue", "sum"),
                Units_Sold=("Units_Sold", "sum")
            )
            .sort_values("Revenue", ascending=False)
            .head(10)
            .reset_index()
        )

        fig_prod = px.bar(
            prod_rev,
            x="Revenue",
            y="Product",
            orientation="h",
            title="Top 10 Products by Gross Sales Value",
            color="Revenue",
            color_continuous_scale="Purples",
            labels={"Revenue": "Estimated Gross Revenue (₹)"},
        )

        fig_prod.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
        )

        st.plotly_chart(fig_prod, use_container_width=True)

    with col_d:
        section_header("Units Sold by Product (Top 10)")

        fig_units = px.bar(
            prod_rev.sort_values("Units_Sold", ascending=False),
            x="Units_Sold",
            y="Product",
            orientation="h",
            title="Top 10 Products by Units Sold",
            color="Units_Sold",
            color_continuous_scale="Greens",
            labels={"Units_Sold": "Units Sold"},
        )

        fig_units.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
        )

        st.plotly_chart(fig_units, use_container_width=True)

    # ── Price & Discount Analysis ─────────────────────────────────────────
    section_header("Price & Discount Analysis")

    col_e, col_f = st.columns(2)

    with col_e:
        disc_rev = (
            df.groupby("Discount_Pct")
            .agg(
                Revenue=("Revenue", "sum"),
                Count=("Revenue", "count")
            )
            .reset_index()
        )

        fig_disc = px.bar(
            disc_rev,
            x="Discount_Pct",
            y="Revenue",
            title="Gross Revenue by Discount Level",
            color="Discount_Pct",
            color_continuous_scale="Oranges",
            labels={
                "Discount_Pct": "Discount (%)",
                "Revenue": "Estimated Gross Revenue (₹)"
            },
            text="Revenue",
        )

        fig_disc.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside"
        )

        fig_disc.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False
        )

        st.plotly_chart(fig_disc, use_container_width=True)

    with col_f:
        # Average price vs estimated gross revenue by product
        prod_scatter = (
            df.groupby("Product")
            .agg(
                Avg_Price=("Price", "mean"),
                Total_Revenue=("Revenue", "sum"),
                Units_Sold=("Units_Sold", "sum")
            )
            .reset_index()
        )

        fig_scat = px.scatter(
            prod_scatter,
            x="Avg_Price",
            y="Total_Revenue",
            size="Units_Sold",
            color="Total_Revenue",
            hover_name="Product",
            title="Price vs Gross Revenue (bubble = units sold)",
            color_continuous_scale="Blues",
            labels={
                "Avg_Price": "Average Price (₹)",
                "Total_Revenue": "Estimated Gross Revenue (₹)",
            },
        )

        fig_scat.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False
        )

        st.plotly_chart(fig_scat, use_container_width=True)

    # ── Monthly Gross Revenue Heatmap ────────────────────────────────────
    section_header("Monthly Gross Revenue Heatmap (by Year)")

    pivot = (
        df.assign(
            Year=df["Date"].dt.year,
            Month=df["Date"].dt.month,
        )
        .groupby(["Year", "Month"])["Revenue"]
        .sum()
        .reset_index()
    )

    pivot_table = (
        pivot.pivot(
            index="Year",
            columns="Month",
            values="Revenue"
        )
        .fillna(0)
    )

    MONTH_LABELS = {
        1: "Jan", 2: "Feb", 3: "Mar",
        4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep",
        10: "Oct", 11: "Nov", 12: "Dec"
    }

    pivot_table.columns = [
        MONTH_LABELS.get(c, c)
        for c in pivot_table.columns
    ]

    fig_heat = px.imshow(
        pivot_table,
        title="Estimated Gross Revenue Heatmap — Year × Month",
        color_continuous_scale="Blues",
        text_auto=".2s",
        aspect="auto",
        labels=dict(
            x="Month",
            y="Year",
            color="Estimated Gross Revenue (₹)"
        ),
    )

    fig_heat.update_layout(**LAYOUT_DEFAULTS)

    st.plotly_chart(fig_heat, use_container_width=True)
