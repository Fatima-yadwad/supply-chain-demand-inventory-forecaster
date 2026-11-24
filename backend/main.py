
import io
import time
import uuid
from pathlib import Path
from threading import RLock

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.data.preprocessing import NUMERIC_COLUMNS, prepare_dataset, standardize_columns

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "raw" / "sales_data.csv"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_UPLOAD_ROWS = 250_000
UPLOAD_TTL_SECONDS = 60 * 60
MAX_UPLOADED_DATASETS = 8
uploaded_datasets = {}
dataset_lock = RLock()

app = FastAPI(
    title="Supply Chain Demand & Inventory API",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _prune_uploaded_datasets():
    now = time.monotonic()
    expired = [
        dataset_id
        for dataset_id, entry in uploaded_datasets.items()
        if entry["expires_at"] <= now
    ]
    for dataset_id in expired:
        del uploaded_datasets[dataset_id]


def _uploaded_dataset_entry(dataset_id):
    with dataset_lock:
        _prune_uploaded_datasets()
        entry = uploaded_datasets.get(dataset_id)
        if entry is None:
            raise HTTPException(
                status_code=404,
                detail="Uploaded dataset not found or its session has expired. Upload it again.",
            )
        entry["expires_at"] = time.monotonic() + UPLOAD_TTL_SECONDS
        return entry


def get_dataset_metadata(dataset_id):
    if not dataset_id:
        return {
            "dataset_id": None,
            "name": "Historical dataset",
            "is_uploaded": False,
            "date_start": "2022-01-01",
            "date_end": "2024-01-30",
        }

    entry = _uploaded_dataset_entry(dataset_id)
    return {
        key: value
        for key, value in entry.items()
        if key not in {"data", "expires_at"}
    }


def load_data(dataset_id=None):
    if dataset_id:
        entry = _uploaded_dataset_entry(dataset_id)
        df = entry["data"].copy()
        df.attrs["dataset_version"] = dataset_id
        return df

    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    required = ["date", "store_id", "product_id"]
    missing = [col for col in required if col not in df.columns]

    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing dataset columns: {missing}"
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).copy()

    for col in ["store_id", "product_id", "category", "region"]:
        if col in df.columns:
            df[col] = (
                df[col].fillna("Unknown").astype(str).str.strip()
            )

    numeric_columns = [
        "demand",
        "units_sold",
        "inventory_level",
        "units_ordered",
        "price",
        "discount",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            ).fillna(0)

    stat = DATA_FILE.stat()
    df.attrs["dataset_version"] = (
        f"historical:{stat.st_mtime_ns}:{stat.st_size}"
    )
    return df


def apply_filters(
    df,
    product="All",
    category="All",
    store="All",
    region="All",
):
    filters = {
        "product_id": product,
        "category": category,
        "store_id": store,
        "region": region,
    }

    for column, selected in filters.items():
        selected_values = [
            value.strip()
            for value in str(selected).split(",")
            if value.strip()
        ]

        if selected_values == ["__NONE__"]:
            return df.iloc[0:0].copy()

        if not selected_values or selected_values == ["All"]:
            continue

        if "All" in selected_values:
            continue

        if column not in df.columns:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot filter by {column}: this dataset does not contain that column.",
            )

        df = df[df[column].astype(str).isin(selected_values)]

    return df


def get_filtered_data(
    product="All",
    category="All",
    store="All",
    region="All",
    dataset_id=None,
):
    df = load_data(dataset_id)
    filtered = apply_filters(df, product, category, store, region)
    filtered.attrs["dataset_version"] = df.attrs.get(
        "dataset_version", dataset_id or "historical"
    )
    return filtered


@app.post("/api/datasets/upload", status_code=201)
async def upload_dataset(file: UploadFile = File(...)):
    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    if Path(filename).suffix.lower() != ".csv":
        raise HTTPException(
            status_code=415,
            detail="Upload a .csv file.",
        )

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="CSV exceeds the 20 MB upload limit.",
        )
    if not content:
        raise HTTPException(status_code=400, detail="The CSV file is empty.")

    try:
        raw = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
        raw = standardize_columns(raw)
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=f"Unable to read or normalize the CSV: {error}",
        ) from error

    if len(raw) > MAX_UPLOAD_ROWS:
        raise HTTPException(
            status_code=413,
            detail="CSV exceeds the 250,000 row limit.",
        )

    required = ["date", "store_id", "product_id"]
    missing_columns = [column for column in required if column not in raw]
    target_column = "demand" if "demand" in raw else (
        "units_sold" if "units_sold" in raw else None
    )
    if target_column is None:
        missing_columns.append("Demand (or Units Sold)")
    if missing_columns:
        column_labels = {
            "date": "Date",
            "store_id": "Store ID",
            "product_id": "Product ID",
        }
        raise HTTPException(
            status_code=422,
            detail=(
                "CSV is missing required columns: "
                + ", ".join(
                    column_labels.get(column, column)
                    for column in missing_columns
                )
                + ". Supported headers include Date, Store ID, Product ID, "
                "Category, Region, Demand, Units Sold, and Inventory Level."
            ),
        )

    data = raw.copy()
    parsed_dates = pd.to_datetime(data["date"], errors="coerce")
    invalid_dates = int(parsed_dates.isna().sum())
    if invalid_dates:
        raise HTTPException(
            status_code=422,
            detail=f"CSV contains {invalid_dates} missing or invalid date value(s).",
        )
    data["date"] = parsed_dates.dt.normalize()

    for column in ["store_id", "product_id"]:
        values = data[column].astype("string").str.strip()
        invalid_ids = int((values.isna() | values.eq("")).sum())
        if invalid_ids:
            raise HTTPException(
                status_code=422,
                detail=f"CSV contains {invalid_ids} missing {column} value(s).",
            )
        data[column] = values.astype(str)

    for column in ["category", "region"]:
        if column in data:
            values = data[column].astype("string").str.strip()
            data[column] = values.mask(values.isna() | values.eq(""), "Unknown")

    missing_values = {
        str(column): int(count)
        for column, count in data.isna().sum().items()
        if count
    }
    for column in NUMERIC_COLUMNS:
        if column not in data:
            continue
        original = data[column]
        numeric = pd.to_numeric(original, errors="coerce")
        invalid_numeric = original.notna() & numeric.isna()
        non_finite = numeric.notna() & ~np.isfinite(numeric)
        if invalid_numeric.any() or non_finite.any():
            invalid_count = int((invalid_numeric | non_finite).sum())
            raise HTTPException(
                status_code=422,
                detail=f"CSV column {column} contains {invalid_count} invalid numeric value(s).",
            )
        data[column] = numeric

    target = data[target_column]
    if target.isna().any():
        raise HTTPException(
            status_code=422,
            detail=f"CSV column {target_column} contains {int(target.isna().sum())} missing demand value(s).",
        )
    if (target < 0).any():
        raise HTTPException(
            status_code=422,
            detail=f"CSV column {target_column} contains negative demand values.",
        )
    if target_column == "units_sold":
        data["demand"] = target

    if "inventory_level" in data:
        stock = data["inventory_level"]
        if (stock.dropna() < 0).any():
            raise HTTPException(
                status_code=422,
                detail="CSV column inventory_level contains negative stock values.",
            )
        inventory_available = not stock.isna().any()
        inventory_issue = (
            None
            if inventory_available
            else f"Inventory Level is missing in {int(stock.isna().sum())} row(s); inventory calculations are unavailable."
        )
    else:
        inventory_available = False
        inventory_issue = (
            "CSV does not contain Inventory Level; stock estimates and replenishment cannot be calculated."
        )

    duplicate_rows_removed = int(data.duplicated().sum())
    if duplicate_rows_removed:
        data = data.drop_duplicates().reset_index(drop=True)
    if data.empty:
        raise HTTPException(status_code=422, detail="CSV contains no usable records.")

    try:
        prepared = prepare_dataset(data)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=f"CSV preprocessing failed: {error}",
        ) from error

    if prepared.empty:
        raise HTTPException(
            status_code=422,
            detail="CSV contains no records after preprocessing.",
        )

    unique_days = int(prepared["date"].nunique())
    forecast_ready = unique_days >= 14
    forecast_issue = (
        None
        if forecast_ready
        else f"At least 14 distinct historical dates are required; this CSV has {unique_days}."
    )
    dataset_id = uuid.uuid4().hex
    safe_name = filename or "uploaded.csv"
    now = time.monotonic()
    metadata = {
        "dataset_id": dataset_id,
        "name": safe_name,
        "is_uploaded": True,
        "records": int(len(prepared)),
        "date_start": prepared["date"].min().strftime("%Y-%m-%d"),
        "date_end": prepared["date"].max().strftime("%Y-%m-%d"),
        "target_column": target_column,
        "inventory_available": inventory_available,
        "inventory_issue": inventory_issue,
        "forecast_ready": forecast_ready,
        "forecast_issue": forecast_issue,
        "duplicate_rows_removed": duplicate_rows_removed,
        "missing_values": missing_values,
        "columns": [str(column) for column in prepared.columns],
    }

    with dataset_lock:
        _prune_uploaded_datasets()
        if len(uploaded_datasets) >= MAX_UPLOADED_DATASETS:
            raise HTTPException(
                status_code=429,
                detail="The upload session limit has been reached. Try again after an earlier upload expires.",
            )
        uploaded_datasets[dataset_id] = {
            **metadata,
            "data": prepared,
            "expires_at": now + UPLOAD_TTL_SECONDS,
        }

    return metadata


@app.get("/api/datasets/{dataset_id}")
def uploaded_dataset_metadata(dataset_id: str):
    return get_dataset_metadata(dataset_id)


def records_by_group(df, group_column, value_column, output_name):
    if group_column not in df.columns or value_column not in df.columns:
        return []

    result = (
        df.groupby(group_column, as_index=False)[value_column]
        .sum()
        .sort_values(value_column, ascending=False)
    )

    return [
        {
            "name": str(row[group_column]),
            output_name: float(row[value_column]),
        }
        for _, row in result.iterrows()
    ]


@app.get("/")
def home():
    return {
        "message": "Supply Chain API is running",
        "dataset": DATA_FILE.exists(),
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "dataset_available": DATA_FILE.exists(),
    }


@app.get("/api/filters")
def filters(dataset_id: str | None = Query(None)):
    df = load_data(dataset_id)

    def options(column):
        if column not in df.columns:
            return []
        return sorted(df[column].dropna().astype(str).unique().tolist())

    return {
        "products": options("product_id"),
        "categories": options("category"),
        "stores": options("store_id"),
        "regions": options("region"),
    }


@app.get("/api/overview")
def overview(
    product: str = Query("All"),
    category: str = Query("All"),
    store: str = Query("All"),
    region: str = Query("All"),
    dataset_id: str | None = Query(None),
):
    df = get_filtered_data(
        product, category, store, region, dataset_id=dataset_id
    )

    if df.empty:
        return {
            "total_records": 0,
            "stores": 0,
            "products": 0,
            "categories": 0,
            "date_start": None,
            "date_end": None,
            "total_units_sold": 0,
            "total_demand": 0,
            "average_inventory": 0,
            "total_units_ordered": 0,
            "inventory_available": False,
            "inventory_issue": "No matching records are available.",
            "data_source": get_dataset_metadata(dataset_id)["name"],
        }

    inventory_available = (
        "inventory_level" in df.columns
        and not df["inventory_level"].isna().any()
    )
    inventory_issue = (
        None
        if inventory_available
        else (
            "Inventory Level is missing or incomplete in the selected data."
        )
    )

    return {
        "total_records": int(len(df)),
        "stores": int(df["store_id"].nunique()),
        "products": int(df["product_id"].nunique()),
        "categories": int(df["category"].nunique())
            if "category" in df.columns else 0,
        "date_start": df["date"].min().strftime("%Y-%m-%d"),
        "date_end": df["date"].max().strftime("%Y-%m-%d"),
        "total_units_sold": float(df["units_sold"].sum())
            if "units_sold" in df.columns else None,
        "total_demand": float(df["demand"].sum())
            if "demand" in df.columns else 0,
        "average_inventory": round(
            float(df["inventory_level"].mean()), 2
        ) if inventory_available else None,
        "total_units_ordered": float(df["units_ordered"].sum())
            if "units_ordered" in df.columns else None,
        "inventory_available": inventory_available,
        "inventory_issue": inventory_issue,
        "data_source": get_dataset_metadata(dataset_id)["name"],
    }


@app.get("/api/demand")
def demand(
    product: str = Query("All"),
    category: str = Query("All"),
    store: str = Query("All"),
    region: str = Query("All"),
    dataset_id: str | None = Query(None),
):
    df = get_filtered_data(
        product, category, store, region, dataset_id=dataset_id
    )

    if "demand" not in df.columns:
        raise HTTPException(400, "Demand column not found")

    result = (
        df.groupby("date", as_index=False)["demand"]
        .sum()
        .sort_values("date")
    )

    return [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "demand": float(row["demand"]),
        }
        for _, row in result.iterrows()
    ]


@app.get("/api/sales")
def sales(
    product: str = Query("All"),
    category: str = Query("All"),
    store: str = Query("All"),
    region: str = Query("All"),
    dataset_id: str | None = Query(None),
):
    df = get_filtered_data(
        product, category, store, region, dataset_id=dataset_id
    )

    if "units_sold" not in df.columns:
        raise HTTPException(400, "Units Sold column not found")

    result = (
        df.groupby("date", as_index=False)["units_sold"]
        .sum()
        .sort_values("date")
    )

    return [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "units_sold": float(row["units_sold"]),
        }
        for _, row in result.iterrows()
    ]


@app.get("/api/inventory")
def inventory(
    product: str = Query("All"),
    category: str = Query("All"),
    store: str = Query("All"),
    region: str = Query("All"),
    dataset_id: str | None = Query(None),
):
    df = get_filtered_data(
        product, category, store, region, dataset_id=dataset_id
    )

    if "inventory_level" not in df.columns:
        raise HTTPException(
            422,
            "Inventory Level is not present in the selected dataset.",
        )
    if df["inventory_level"].isna().any():
        raise HTTPException(
            422,
            "Inventory Level is missing in the selected data; inventory estimates are unavailable.",
        )

    aggregations = {
        "average_inventory": ("inventory_level", "mean"),
    }

    if "demand" in df.columns:
        aggregations["total_demand"] = ("demand", "sum")

    if "category" in df.columns:
        aggregations["category"] = ("category", "first")

    result = (
        df.groupby("product_id")
        .agg(**aggregations)
        .reset_index()
        .sort_values("product_id")
    )

    return [
        {
            "product_id": str(row["product_id"]),
            "average_inventory": round(float(row["average_inventory"]), 2),
            "total_demand": float(row["total_demand"])
                if "total_demand" in result.columns else 0,
            "category": str(row["category"])
                if "category" in result.columns else "Not provided",
        }
        for _, row in result.iterrows()
    ]


@app.get("/api/analytics")
def analytics(
    product: str = Query("All"),
    category: str = Query("All"),
    store: str = Query("All"),
    region: str = Query("All"),
    dataset_id: str | None = Query(None),
):
    df = get_filtered_data(
        product, category, store, region, dataset_id=dataset_id
    )

    if df.empty:
        return {
            "region_demand": [],
            "region_sales": [],
            "category_sales": [],
            "store_sales": [],
            "product_demand": [],
            "monthly_trend": [],
            "top_products": [],
            "bottom_products": [],
        }

    region_demand = records_by_group(
        df, "region", "demand", "demand"
    )
    region_sales = records_by_group(
        df, "region", "units_sold", "units_sold"
    )
    category_sales = records_by_group(
        df, "category", "units_sold", "units_sold"
    )
    store_sales = records_by_group(
        df, "store_id", "units_sold", "units_sold"
    )
    product_demand = records_by_group(
        df, "product_id", "demand", "demand"
    )

    monthly = df.copy()
    monthly["month"] = monthly["date"].dt.to_period("M").astype(str)

    monthly_columns = [
        col for col in ["demand", "units_sold"]
        if col in monthly.columns
    ]

    if monthly_columns:
        monthly_result = (
            monthly.groupby("month", as_index=False)[monthly_columns]
            .sum()
            .sort_values("month")
        )
        monthly_trend = monthly_result.to_dict(orient="records")
    else:
        monthly_trend = []

    return {
        "region_demand": region_demand,
        "region_sales": region_sales,
        "category_sales": category_sales,
        "store_sales": store_sales,
        "product_demand": product_demand,
        "monthly_trend": monthly_trend,
        "top_products": product_demand[:5],
        "bottom_products": list(reversed(product_demand[-5:])),
    }
from backend.ai_routes import create_ai_router

app.include_router(create_ai_router(get_filtered_data))
