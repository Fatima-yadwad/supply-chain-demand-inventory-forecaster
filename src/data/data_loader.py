from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def load_dataset(file_path=None):
    """Load the Kaggle retail inventory dataset."""
    if file_path is None:
        csv_files = list(RAW_DIR.glob("*.csv"))

        if not csv_files:
            raise FileNotFoundError(f"No CSV found in {RAW_DIR}")

        if len(csv_files) > 1:
            raise ValueError(
                "Multiple CSV files found. Specify the file path explicitly."
            )

        file_path = csv_files[0]

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)
    df.columns = [str(col).strip() for col in df.columns]

    if df.empty:
        raise ValueError("Dataset is empty.")

    print(f"Dataset loaded: {file_path.name}")
    print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
    print("Columns:", df.columns.tolist())

    return df


def inspect_dataset(df):
    """Display basic dataset information."""
    print("\n--- DATASET INFORMATION ---")
    df.info()

    print("\n--- FIRST FIVE ROWS ---")
    print(df.head())

    print("\n--- MISSING VALUES ---")
    print(df.isnull().sum())

    print("\n--- DUPLICATE ROWS ---")
    print(df.duplicated().sum())

    print("\n--- NUMERICAL SUMMARY ---")
    print(df.describe(include="number").T)

    return df.describe(include="all").T
