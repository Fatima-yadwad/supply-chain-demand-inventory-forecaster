
"""
dashboard/sections/inventory.py
--------------------------------
Inventory Analysis tab: levels, low-stock analysis, ordered vs sold.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from dashboard.chart_utils import (
    section_header, PALETTE, LAYOUT_DEFAULTS, kpi_card, fmt_number
)


def render_inventory(df: pd.DataFrame) -> None:
    """Render the Inventory Analysis tab."""

    required_columns = [
        "Date", "Product", "Store", "Category",
        "Inventory_Level", "Units_Sold", "Units_Ordered"
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(f"Missing columns for Inventory Analysis: {missing}")
        return

    if df.empty:
        st.warning("No inventory data available for the selected filters.")
        return

    # ── KPIs ─────────────────────────────────────────────────────────────
    section_header("Inventory KPIs")

    avg_inv = df["Inventory_Level"].mean()
    total_inv = df["Inventory_Level"].sum()
    total_ord = df["Units_Ordered"].sum()
    total_sold = df["Units_Sold"].sum()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            kpi_card(
                "Avg Inventory Level",
                fmt_number(avg_inv, decimals=0),
                icon="📦",
                color="blue"
            ),
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            kpi_card(
                "Total Inventory (sum of records)",
                fmt_number(total_inv),
                icon="🏪",
                color="green"
            ),
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            kpi_card(
                "Total Units Ordered",
                fmt_number(total_ord),
                icon="📋",
                color="purple"
            ),
            unsafe_allow_html=True,
        )

    with c4:
        ratio = (
            total_sold / total_ord * 100
            if total_ord > 0 else 0
        )

        st.markdown(
            kpi_card(
                "Units Sold / Ordered",
                f"{ratio:.1f}%",
                icon="📊",
                color="teal"
            ),
            unsafe_allow_html=True,
        )

    st.caption(
        "Inventory values are aggregated across store-product-date records. "
        "The sold-to-ordered ratio compares total units sold with total units ordered."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Inventory trend over time ───────────────────────────────────────
    section_header("Inventory Level Over Time")

    inv_time = (
        df.groupby(df["Date"].dt.to_period("W"))
        .agg(
            Inventory_Level=("Inventory_Level", "mean"),
            Units_Sold=("Units_Sold", "sum"),
            Units_Ordered=("Units_Ordered", "sum")
        )
        .reset_index()
    )

    inv_time["Date"] = inv_time["Date"].dt.to_timestamp()

    fig_inv = go.Figure()

    fig_inv.add_trace(
        go.Scatter(
            x=inv_time["Date"],
            y=inv_time["Inventory_Level"],
            name="Average Inventory",
            line=dict(color=PALETTE[0], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(37,99,235,0.08)",
        )
    )

    fig_inv.update_layout(
        title="Weekly Average Inventory Level",
        xaxis_title="Week",
        yaxis_title="Average Inventory Level",
        **LAYOUT_DEFAULTS,
    )

    st.plotly_chart(fig_inv, use_container_width=True)

    # ── Inventory by Product and Store ──────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        section_header("Inventory by Product")

        prod_inv = (
            df.groupby("Product")["Inventory_Level"]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )

        fig_prod = px.bar(
            prod_inv,
            x="Inventory_Level",
            y="Product",
            orientation="h",
            title="Average Inventory Level by Product",
            color="Inventory_Level",
            color_continuous_scale="Blues",
            labels={"Inventory_Level": "Average Inventory Level"},
        )

        fig_prod.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
        )

        st.plotly_chart(fig_prod, use_container_width=True)

    with col_b:
        section_header("Inventory by Store")

        store_inv = (
            df.groupby("Store")["Inventory_Level"]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )

        fig_store = px.bar(
            store_inv,
            x="Store",
            y="Inventory_Level",
            title="Average Inventory Level by Store",
            color="Inventory_Level",
            color_continuous_scale="Teal",
            labels={"Inventory_Level": "Average Inventory Level"},
        )

        fig_store.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False
        )

        st.plotly_chart(fig_store, use_container_width=True)

    # ── Units Sold vs Units Ordered ─────────────────────────────────────
    section_header("Units Sold vs Units Ordered by Category")

    cat_comp = (
        df.groupby("Category")
        .agg(
            Units_Sold=("Units_Sold", "sum"),
            Units_Ordered=("Units_Ordered", "sum")
        )
        .reset_index()
        .sort_values("Units_Ordered", ascending=False)
    )

    fig_comp = px.bar(
        cat_comp,
        x="Category",
        y=["Units_Sold", "Units_Ordered"],
        barmode="group",
        title="Units Sold vs Units Ordered by Category",
        color_discrete_map={
            "Units_Sold": PALETTE[1],
            "Units_Ordered": PALETTE[0]
        },
        labels={
            "value": "Units",
            "variable": "Metric"
        },
    )

    fig_comp.update_layout(**LAYOUT_DEFAULTS)

    st.plotly_chart(fig_comp, use_container_width=True)

    # ── Low Inventory Analysis ──────────────────────────────────────────
    section_header("Products with Relatively Low Inventory")

    st.caption(
        "Products whose average inventory level is at or below "
        "the 25th percentile across products. This is a relative "
        "comparison, not a confirmed stockout or reorder alert."
    )

    product_inventory = (
        df.groupby("Product")["Inventory_Level"]
        .mean()
    )

    threshold = product_inventory.quantile(0.25)

    low_inv = (
        df.groupby("Product")
        .agg(
            Avg_Inventory=("Inventory_Level", "mean"),
            Total_Sold=("Units_Sold", "sum"),
            Total_Ordered=("Units_Ordered", "sum"),
            Category=("Category", "first"),
        )
        .reset_index()
    )

    low_inv["Avg_Inventory"] = low_inv["Avg_Inventory"].round(1)

    low_inv = (
        low_inv[low_inv["Avg_Inventory"] <= threshold]
        .sort_values("Avg_Inventory")
    )

    if low_inv.empty:
        st.success("No relatively low-inventory products detected.")

    else:
        styled = (
            low_inv.style
            .background_gradient(
                subset=["Avg_Inventory"],
                cmap="Reds"
            )
            .format({
                "Avg_Inventory": "{:.1f}",
                "Total_Sold": "{:,}",
                "Total_Ordered": "{:,}"
            })
        )

        st.dataframe(styled, use_container_width=True)

        fig_low = px.bar(
            low_inv,
            x="Product",
            y="Avg_Inventory",
            title="Products with Relatively Low Average Inventory",
            color="Avg_Inventory",
            color_continuous_scale="Reds_r",
            labels={
                "Avg_Inventory": "Average Inventory Level"
            },
        )

        fig_low.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False
        )

        fig_low.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="#dc2626",
            annotation_text=f"25th percentile threshold ({threshold:.0f})",
            annotation_position="top right",
        )

        st.plotly_chart(fig_low, use_container_width=True)

    # ── Inventory Efficiency by Category ────────────────────────────────
    section_header("Inventory Efficiency by Category")

    st.caption(
        "Inventory Turnover Proxy = Total Units Sold / Average Recorded Inventory. "
        "This is an approximate comparison, not a formal accounting turnover ratio."
    )

    cat_eff = (
        df.groupby("Category")
        .agg(
            Total_Sold=("Units_Sold", "sum"),
            Avg_Inventory=("Inventory_Level", "mean"),
        )
        .reset_index()
    )

    cat_eff["Turnover"] = (
        cat_eff["Total_Sold"]
        / cat_eff["Avg_Inventory"].replace(0, np.nan)
    ).round(2)

    cat_eff = cat_eff.dropna(subset=["Turnover"])

    cat_eff = cat_eff.sort_values(
        "Turnover",
        ascending=False
    )

    if cat_eff.empty:
        st.info("Turnover cannot be calculated for the available inventory data.")

    else:
        fig_turn = px.bar(
            cat_eff,
            x="Category",
            y="Turnover",
            title="Inventory Turnover Proxy by Category",
            color="Turnover",
            color_continuous_scale="Greens",
            labels={"Turnover": "Turnover Proxy"},
            text="Turnover",
        )

        fig_turn.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )

        fig_turn.update_layout(
            **LAYOUT_DEFAULTS,
            coloraxis_showscale=False
        )

        st.plotly_chart(fig_turn, use_container_width=True)
