"""Detect unusually high demand using rolling statistics."""
from __future__ import annotations

import pandas as pd


def detect_demand_spikes(
    data: pd.DataFrame,
    *,
    date_col: str = "date",
    sku_col: str = "sku",
    demand_col: str = "actual_demand",
    window: int = 7,
    threshold: float = 3.0,
    method: str = "zscore",
) -> pd.DataFrame:
    """Return a copy with rolling baseline, score and `is_spike` columns.

    The baseline uses only prior observations (shifted rolling window), avoiding
    leakage from the observation being tested. For a first run-in window, the
    spike flag is False because there is not enough history.
    """
    required = {date_col, demand_col}
    if sku_col in data.columns:
        required.add(sku_col)
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if window < 2 or threshold <= 0:
        raise ValueError("window must be >= 2 and threshold must be > 0")
    if method not in {"zscore", "mad"}:
        raise ValueError("method must be 'zscore' or 'mad'")

    out = data.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    out[demand_col] = pd.to_numeric(out[demand_col], errors="raise")
    if (out[demand_col] < 0).any():
        raise ValueError("Demand cannot be negative")
    out = out.sort_values(([sku_col] if sku_col in out.columns else []) + [date_col]).copy()
    group_keys = sku_col if sku_col in out.columns else None
    grouped = out.groupby(group_keys, sort=False)[demand_col] if group_keys else out[demand_col]
    out["rolling_mean"] = grouped.transform(lambda s: s.shift(1).rolling(window, min_periods=window).mean())
    if method == "zscore":
        out["rolling_std"] = grouped.transform(lambda s: s.shift(1).rolling(window, min_periods=window).std(ddof=1))
        denom = out["rolling_std"].replace(0, float("nan"))
        out["spike_score"] = (out[demand_col] - out["rolling_mean"]) / denom
    else:
        def rolling_mad(series):
            return series.shift(1).rolling(window, min_periods=window).apply(
                lambda x: (abs(x - pd.Series(x).median())).median(), raw=True
            )
        out["rolling_mad"] = grouped.transform(rolling_mad)
        denom = (1.4826 * out["rolling_mad"]).replace(0, float("nan"))
        out["spike_score"] = (out[demand_col] - out["rolling_mean"]) / denom
    out["is_spike"] = out["spike_score"].fillna(0) >= threshold
    return out.reset_index(drop=True)
def detect_spikes_by_product(prepared_df, window=7, threshold=3.0):
    """Detect demand spikes separately for each store and product."""

    required = {"date", "store_id", "product_id", "target_demand"}
    missing = required - set(prepared_df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    results = []

    for (store, product), group in prepared_df.groupby(
        ["store_id", "product_id"]
    ):
        daily = (
            group.groupby("date", as_index=False)["target_demand"]
            .sum()
            .sort_values("date")
        )

        detected = detect_demand_spikes(
            daily,
            date_col="date",
            demand_col="target_demand",
            window=window,
            threshold=threshold,
            method="zscore",
        )

        detected["store_id"] = store
        detected["product_id"] = product

        results.append(detected)

    if not results:
        return pd.DataFrame()

    return pd.concat(results, ignore_index=True)