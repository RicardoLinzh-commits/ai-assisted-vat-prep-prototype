"""Build compact findings snapshots for optional AI interpretation."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from explanation.local_explainer import ISSUE_TYPE_LABELS
from pipeline import RunResult, STATUS_STOPPED_AFTER_REPORTING

REPRESENTATIVE_FINDINGS_LIMIT = 5
ANOMALY_SAMPLE_LIMIT = 3


def _normalise_issue_type(issue_type: str) -> str:
    """Return a user-facing label for an issue type."""
    return ISSUE_TYPE_LABELS.get(issue_type, issue_type.replace("_", " "))


def _normalise_decision(decision: str) -> str:
    """Return a user-facing label for a review outcome."""
    decision_labels = {
        "reject": "marked for follow-up",
        "confirm": "retained for review",
        "ignore": "not escalated",
    }
    return decision_labels.get(decision, decision.replace("_", " "))


def _format_user_status(status: str) -> str:
    """Return a restrained user-facing outcome label."""
    if status == STATUS_STOPPED_AFTER_REPORTING:
        return "Follow-up needed"
    return "Analysis completed"


def _format_follow_up_note(run_result: RunResult) -> str | None:
    """Return a user-facing follow-up note when relevant."""
    if run_result.status == STATUS_STOPPED_AFTER_REPORTING or run_result.stop_reason:
        return "Some records need further attention. Reports were created successfully."
    return None


def _summarise_issue_counts(issue_report_df: pd.DataFrame) -> dict[str, int]:
    """Return counts by issue type using user-facing labels."""
    if issue_report_df.empty or "issue_type" not in issue_report_df.columns:
        return {}

    issue_counts = Counter(issue_report_df["issue_type"].dropna().astype(str))
    return {_normalise_issue_type(issue_type): count for issue_type, count in issue_counts.most_common()}


def _summarise_review_counts(review_log_df: pd.DataFrame) -> dict[str, int]:
    """Return counts by review outcome using user-facing labels."""
    if review_log_df.empty or "decision" not in review_log_df.columns:
        return {}

    decision_counts = Counter(review_log_df["decision"].dropna().astype(str))
    return {_normalise_decision(decision): count for decision, count in decision_counts.most_common()}


def _build_representative_findings(issue_report_df: pd.DataFrame) -> list[dict]:
    """Return a small set of representative findings for AI interpretation."""
    if issue_report_df.empty or "issue_type" not in issue_report_df.columns:
        return []

    findings: list[dict] = []
    issue_counts = issue_report_df["issue_type"].dropna().astype(str).value_counts()

    for issue_type in issue_counts.index:
        matching_rows = issue_report_df[issue_report_df["issue_type"] == issue_type].head(2)
        for _, row in matching_rows.iterrows():
            value = row.get("value")
            if pd.isna(value):
                value = row.get("observed_value")

            note = row.get("message")
            if pd.isna(note):
                note = row.get("reason")

            findings.append(
                {
                    "row_index": row.get("row_index"),
                    "issue_type": _normalise_issue_type(issue_type),
                    "column": row.get("column"),
                    "value": None if pd.isna(value) else str(value),
                    "note": None if pd.isna(note) else str(note),
                }
            )
            if len(findings) >= REPRESENTATIVE_FINDINGS_LIMIT:
                return findings

    return findings


def _build_anomaly_context(issue_report_df: pd.DataFrame) -> dict:
    """Return a small anomaly-specific context block when anomaly findings exist."""
    if issue_report_df.empty or "issue_type" not in issue_report_df.columns:
        return {}

    anomaly_rows = issue_report_df[issue_report_df["issue_type"] == "anomaly"].copy()
    if anomaly_rows.empty:
        return {}

    anomaly_rows["observed_value"] = pd.to_numeric(anomaly_rows.get("observed_value"), errors="coerce")
    anomaly_rows = anomaly_rows.dropna(subset=["observed_value"])
    if anomaly_rows.empty:
        return {
            "anomaly_flags": 0,
            "interpretation_note": "Anomaly flags are prompts for review, not proof of error.",
        }

    lower_bound = pd.to_numeric(anomaly_rows.get("lower_bound"), errors="coerce").dropna()
    upper_bound = pd.to_numeric(anomaly_rows.get("upper_bound"), errors="coerce").dropna()
    lower_value = None if lower_bound.empty else float(lower_bound.iloc[0])
    upper_value = None if upper_bound.empty else float(upper_bound.iloc[0])

    if lower_value is not None or upper_value is not None:
        deviation = pd.Series(0.0, index=anomaly_rows.index)
        if lower_value is not None:
            deviation = deviation.where(anomaly_rows["observed_value"] >= lower_value, lower_value - anomaly_rows["observed_value"])
        if upper_value is not None:
            deviation = deviation.where(anomaly_rows["observed_value"] <= upper_value, anomaly_rows["observed_value"] - upper_value)
        anomaly_rows["deviation"] = deviation.abs()
        anomaly_rows = anomaly_rows.sort_values("deviation", ascending=False)
    else:
        anomaly_rows = anomaly_rows.sort_values("observed_value", ascending=False)

    flagged_amounts = [float(value) for value in anomaly_rows["observed_value"].head(ANOMALY_SAMPLE_LIMIT).tolist()]
    return {
        "anomaly_flags": int(len(anomaly_rows)),
        "lower_bound": lower_value,
        "upper_bound": upper_value,
        "sample_flagged_amounts": flagged_amounts,
        "interpretation_note": "Anomaly flags are prompts for review, not proof of error.",
    }


def build_issue_snapshot(run_result: RunResult, issue_report_df: pd.DataFrame, review_log_df: pd.DataFrame) -> dict:
    """Build a compact local snapshot for optional AI interpretation."""
    return {
        "input_file": run_result.input_file.rsplit("\\", 1)[-1].rsplit("/", 1)[-1],
        "rows_loaded": run_result.rows_loaded,
        "issues_found": run_result.issues_found,
        "anomalies_flagged": run_result.anomalies_flagged,
        "outcome": _format_user_status(run_result.status),
        "follow_up_note": _format_follow_up_note(run_result),
        "issue_type_counts": _summarise_issue_counts(issue_report_df),
        "review_outcome_counts": _summarise_review_counts(review_log_df),
        "representative_findings": _build_representative_findings(issue_report_df),
        "anomaly_context": _build_anomaly_context(issue_report_df),
        "scope_note": "This snapshot was built from current findings only. The full uploaded spreadsheet was not included.",
    }
