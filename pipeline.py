"""High-level orchestration for the VAT spreadsheet preparation prototype.

This module keeps the end-to-end demo workflow reusable while preserving the
existing internal module boundaries. It coordinates ingestion, deterministic
validation, IQR-based anomaly flagging, review, and traceable CSV exports
without changing the underlying spreadsheet data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from anomaly.anomaly_detector import detect_anomalies
from export.exporter import export_outputs
from ingestion.loader import load_spreadsheet
from review.review_manager import ReviewManager
from validation.validator import validate_vat_data

LOGGER = logging.getLogger(__name__)

STATUS_COMPLETED = "completed"
STATUS_STOPPED_AFTER_REPORTING = "stopped_after_reporting"
STOP_REASON_REJECTED_REVIEW_ITEMS = "rejected_review_items"


@dataclass(frozen=True)
class RunResult:
    """Structured summary of a prototype pipeline run."""

    input_file: str
    rows_loaded: int
    issues_found: int
    anomalies_flagged: int
    status: str
    stop_reason: str | None
    dataset_snapshot_path: str
    issue_report_path: str
    review_log_path: str


def run_pipeline(input_path: str, output_dir: str) -> RunResult:
    """Run the research prototype pipeline and return a structured summary.

    Parameters
    ----------
    input_path : str
        Source spreadsheet path for the VAT records dataset.
    output_dir : str
        Directory where traceable CSV artefacts should be written.
    """
    resolved_input_path = Path(input_path)
    resolved_output_dir = Path(output_dir)

    LOGGER.info("Starting VAT spreadsheet preparation pipeline for %s", resolved_input_path)
    dataframe = load_spreadsheet(resolved_input_path)

    validation_results = validate_vat_data(dataframe)
    LOGGER.info("Validation stage completed with %s issues", validation_results["issue_count"])

    anomaly_results = detect_anomalies(dataframe, column="net_amount", method="iqr")
    LOGGER.info("Anomaly detection stage completed with %s flagged rows", len(anomaly_results))

    review_items = validation_results["issues"] + anomaly_results.to_dict(orient="records")
    review_log = ReviewManager().review_issues(review_items)
    rejected_items = review_log[review_log["decision"] == "reject"]

    exported_files = export_outputs(
        dataframe=dataframe,
        validation_results=validation_results,
        anomaly_results=anomaly_results,
        review_log=review_log,
        output_dir=resolved_output_dir,
    )

    if not rejected_items.empty:
        LOGGER.warning("Rejected review items found; reporting artefacts exported and pipeline stopped")
        status = STATUS_STOPPED_AFTER_REPORTING
        stop_reason = STOP_REASON_REJECTED_REVIEW_ITEMS
    else:
        LOGGER.info("Pipeline completed successfully")
        status = STATUS_COMPLETED
        stop_reason = None

    return RunResult(
        input_file=str(resolved_input_path),
        rows_loaded=len(dataframe),
        issues_found=validation_results["issue_count"],
        anomalies_flagged=len(anomaly_results),
        status=status,
        stop_reason=stop_reason,
        dataset_snapshot_path=str(exported_files["dataset_snapshot"]),
        issue_report_path=str(exported_files["issue_report"]),
        review_log_path=str(exported_files["review_log"]),
    )
