"""Build a simple bar chart from the presentation-ready evaluation results table."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLE_INPUT_PATH = PROJECT_ROOT / "output" / "synthetic_evaluation_results_table.csv"
CHART_OUTPUT_PATH = PROJECT_ROOT / "output" / "synthetic_evaluation_issue_chart.png"

COUNT_COLUMNS = [
    "missing_value_count",
    "duplicate_row_count",
    "invalid_date_count",
    "invalid_numeric_count",
    "anomaly_count",
]

COUNT_LABELS = [
    "Missing values",
    "Duplicate-row flags",
    "Invalid dates",
    "Invalid numeric values",
    "Anomaly flags",
]

DATASET_LABELS = {
    "synthetic_eval_case_a.csv": "Case A",
    "synthetic_eval_case_b.csv": "Case B",
}


def main() -> None:
    """Create a grouped bar chart of detected issue counts for each dataset."""
    results_table = pd.read_csv(TABLE_INPUT_PATH)
    chart_data = results_table.set_index("dataset_name")[COUNT_COLUMNS]

    ax = chart_data.plot(
        kind="bar",
        figsize=(9, 5),
        width=0.75,
        edgecolor="black",
    )

    ax.set_title("Detected Issue Counts by Dataset")
    ax.set_xlabel("Dataset")
    ax.set_ylabel("Count")
    ax.set_xticklabels([DATASET_LABELS.get(name, name) for name in chart_data.index], rotation=0)
    ax.legend(COUNT_LABELS, title="Issue type", frameon=False)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.7)

    plt.tight_layout()
    CHART_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(CHART_OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved chart to: {CHART_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
