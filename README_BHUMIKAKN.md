# Bhumika KN – Inventory + Analytics module

This folder is a drop-in implementation for the assigned paths in the team repository. It is designed to run independently with illustrative dummy data until the forecasting members publish their outputs.

## Files

Copy/merge these paths into the team repository:

- `src/inventory/safety_stock.py`
- `src/inventory/reorder_point.py`
- `src/inventory/inventory_simulation.py`
- `src/inventory/allocation.py`
- `src/analytics/spike_detection.py`
- `src/analytics/bullwhip.py`
- `notebooks/04_inventory_optimization.ipynb`
- `notebooks/05_bullwhip_analysis.ipynb`
- `reports/Inventory_Analysis.md`

The `tests/`, `data/`, and package `__init__.py` files are supporting files and can also be copied if the team repository does not already contain equivalents.

## Setup (from repository root)

```bash
python -m pip install pandas numpy matplotlib scipy scikit-learn jupyter pytest
```

## Run tests

```bash
python -m pytest tests/ -q
```

## Run notebooks

Open the notebooks in VS Code and select the project's `.venv` Python interpreter/kernel.

## Git workflow

Work only on `bhumikakn`, inspect `git status`, run tests, then commit and push. Do not push to `main`.

```bash
git status
git add src/inventory src/analytics notebooks/04_inventory_optimization.ipynb notebooks/05_bullwhip_analysis.ipynb reports/Inventory_Analysis.md tests data
 git commit -m "Add inventory optimization and supply chain analytics"
git push origin bhumikakn
```

Then create a Pull Request from `bhumikakn` into `main`. Do not force-push or overwrite another member's work. If files already exist, inspect and merge rather than blindly replacing them.

## Assumptions to confirm with the team

- Demand and lead time units are consistent (e.g. units/day and days).
- The inventory simulation currently models lost sales, not backorders.
- Bullwhip analysis needs customer demand and upstream order quantities aligned by period.
- The dummy dataset is for code testing only, not final project evidence.
