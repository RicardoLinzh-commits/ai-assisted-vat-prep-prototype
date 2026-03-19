"""Build a compact presentation-ready table from the synthetic evaluation summary.

This script keeps the raw summary unchanged and creates a smaller output table
that is easier to reuse in later reporting or dissertation write-up work.
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_INPUT_PATH = PROJECT_ROOT / "output" / "synthetic_evaluation_summary.csv"
TABLE_OUTPUT_PATH = PROJECT_ROOT / "output" / "synthetic_evaluation_results_table.csv"

PRESENTATION_COLUMNS = [
    "dataset_name",
    "row_count",
    "validation_issue_count",
    "count_missing_value",
    "count_duplicate_row",
    "count_invalid_date_format",
    "count_invalid_numeric_format",
    "count_anomaly",
    "has_reject_decision",
    "has_confirm_decision",
]

PRESENTATION_RENAMES = {
    "dataset_name": "dataset_name",
    "row_count": "row_count",
    "validation_issue_count": "validation_issue_count",
    "count_missing_value": "missing_value_count",
    "count_duplicate_row": "duplicate_row_count",
    "count_invalid_date_format": "invalid_date_count",
    "count_invalid_numeric_format": "invalid_numeric_count",
    "count_anomaly": "anomaly_count",
    "has_reject_decision": "has_reject_decision",
    "has_confirm_decision": "has_confirm_decision",
}


def main() -> None:
    """Create a compact presentation table from the raw evaluation summary."""
    summary_dataframe = pd.read_csv(SUMMARY_INPUT_PATH)
    presentation_table = summary_dataframe[PRESENTATION_COLUMNS].rename(columns=PRESENTATION_RENAMES)

    TABLE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    presentation_table.to_csv(TABLE_OUTPUT_PATH, index=False)

    print("Evaluation Results Table")
    print("------------------------")
    print(presentation_table.to_string(index=False))
    print()
    print(f"Saved presentation table to: {TABLE_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
