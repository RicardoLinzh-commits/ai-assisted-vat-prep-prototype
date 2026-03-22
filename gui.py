"""Local Gradio interface for the VAT spreadsheet preparation prototype."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import gradio as gr
import pandas as pd
from matplotlib.figure import Figure

from ai.provider_catalog import (
    DEFAULT_PROVIDER,
    get_default_model,
    get_provider_choices,
    get_standard_model_options,
)
from ai.prompts import DEFAULT_EDITABLE_EXPLANATION_PROMPT
from ai.snapshot_builder import build_issue_snapshot
from ai.suggestions_service import generate_advanced_ai_suggestions, try_generate_default_ai_suggestions
from explanation.local_explainer import ISSUE_TYPE_LABELS, generate_automatic_explanation
from export.exporter import ISSUE_REPORT_COLUMNS
from pipeline import STATUS_STOPPED_AFTER_REPORTING, run_pipeline

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
UI_OUTPUT_ROOT = BASE_DIR / "output" / "ui_runs"
ISSUE_PREVIEW_ROWS = 50
EMPTY_REVIEW_LOG_COLUMNS = ["row_index", "issue_type", "decision", "notes"]
NO_FINDINGS_MESSAGE = "No findings to plot."
NO_ANOMALIES_MESSAGE = "No anomaly findings were recorded for this run."


def _read_output_csv(file_path: str, default_columns: list[str] | None = None) -> pd.DataFrame:
    """Read an exported CSV safely, including header-only files."""
    try:
        return pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=default_columns or [])


def _build_run_output_dir() -> Path:
    """Create a distinct per-run output directory for the local UI."""
    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    output_dir = UI_OUTPUT_ROOT / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _normalise_issue_label(issue_type: str) -> str:
    """Return a readable label for a finding type."""
    return ISSUE_TYPE_LABELS.get(issue_type, issue_type.replace("_", " "))


def _format_user_status(status: str) -> str:
    """Convert the internal run status into a user-facing label."""
    if status == STATUS_STOPPED_AFTER_REPORTING:
        return "Follow-up needed"
    return "Analysis completed"


def _format_user_stop_reason(status: str, stop_reason: str | None) -> str | None:
    """Return a restrained follow-up note for the overview area."""
    if status == STATUS_STOPPED_AFTER_REPORTING or stop_reason:
        return "Some records need further attention. Reports were created successfully."
    return None


def _format_results_overview(
    input_name: str,
    rows_loaded: int,
    issues_found: int,
    anomalies_flagged: int,
    status: str,
    stop_reason: str | None,
) -> str:
    """Return a compact, scannable overview in markdown card format."""
    overview_lines = [
        f"## {_format_user_status(status)}",
        "",
        f"**Input file:** `{input_name}`",
        "",
        f"**Rows loaded:** {rows_loaded}  ",
        f"**Issues found:** {issues_found}  ",
        f"**Anomaly flags:** {anomalies_flagged}",
    ]

    follow_up_note = _format_user_stop_reason(status, stop_reason)
    if follow_up_note:
        overview_lines.extend(["", f"> {follow_up_note}"])

    return "\n".join(overview_lines)


def _build_message_figure(title: str, message: str) -> Figure:
    """Create a simple placeholder figure for empty states."""
    figure = Figure(figsize=(5.0, 3.0), layout="constrained")
    axes = figure.subplots()
    axes.axis("off")
    axes.set_title(title, fontsize=11, pad=10)
    axes.text(0.5, 0.5, message, ha="center", va="center", fontsize=10, color="#4b5563")
    return figure


def _build_issue_type_counts_plot(issue_report_df: pd.DataFrame) -> Figure:
    """Create a compact bar chart of finding counts by issue type."""
    if issue_report_df.empty or "issue_type" not in issue_report_df.columns:
        return _build_message_figure("Issue Type Counts", NO_FINDINGS_MESSAGE)

    issue_counts = (
        issue_report_df["issue_type"]
        .dropna()
        .astype(str)
        .value_counts()
        .sort_values(ascending=False)
    )
    if issue_counts.empty:
        return _build_message_figure("Issue Type Counts", NO_FINDINGS_MESSAGE)

    labels = [_normalise_issue_label(issue_type) for issue_type in issue_counts.index]
    values = issue_counts.tolist()

    figure = Figure(figsize=(5.0, 3.2), layout="constrained")
    axes = figure.subplots()
    axes.barh(labels[::-1], values[::-1], color="#5b7083")
    axes.set_title("Issue Type Counts", fontsize=11, pad=10)
    axes.set_xlabel("Count")
    axes.grid(axis="x", color="#d9dee3", linewidth=0.8)
    axes.set_axisbelow(True)
    return figure


def _build_anomaly_amount_plot(issue_report_df: pd.DataFrame) -> Figure:
    """Create a compact anomaly amount overview using ranked flagged values."""
    if issue_report_df.empty or "issue_type" not in issue_report_df.columns:
        return _build_message_figure("Anomaly Amount Overview", NO_ANOMALIES_MESSAGE)

    anomaly_rows = issue_report_df[issue_report_df["issue_type"] == "anomaly"].copy()
    if anomaly_rows.empty:
        return _build_message_figure("Anomaly Amount Overview", NO_ANOMALIES_MESSAGE)

    anomaly_rows["observed_value"] = pd.to_numeric(anomaly_rows["observed_value"], errors="coerce")
    anomaly_rows = anomaly_rows.dropna(subset=["observed_value"])
    if anomaly_rows.empty:
        return _build_message_figure("Anomaly Amount Overview", NO_ANOMALIES_MESSAGE)

    lower_bound = pd.to_numeric(anomaly_rows["lower_bound"], errors="coerce").dropna()
    upper_bound = pd.to_numeric(anomaly_rows["upper_bound"], errors="coerce").dropna()
    lower_value = lower_bound.iloc[0] if not lower_bound.empty else None
    upper_value = upper_bound.iloc[0] if not upper_bound.empty else None

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

    figure = Figure(figsize=(5.0, 3.2), layout="constrained")
    axes = figure.subplots()
    x_values = list(range(1, len(anomaly_rows) + 1))
    axes.bar(x_values, anomaly_rows["observed_value"], color="#c06b2c", width=0.65)

    if lower_value is not None:
        axes.axhline(lower_value, color="#718096", linestyle="--", linewidth=1.2, label="Lower bound")
    if upper_value is not None:
        axes.axhline(upper_value, color="#4a5568", linestyle="--", linewidth=1.2, label="Upper bound")

    axes.set_title("Anomaly Amount Overview", fontsize=11, pad=10)
    axes.set_xlabel("Flagged values ranked by deviation")
    axes.set_ylabel("Flagged net amount")
    axes.set_xticks(x_values)
    axes.grid(axis="y", color="#d9dee3", linewidth=0.8)
    axes.set_axisbelow(True)
    if lower_value is not None or upper_value is not None:
        axes.legend(loc="best", fontsize=8)
    return figure


def _format_amount(value: float) -> str:
    """Format a numeric amount for user-facing notes."""
    return f"£{value:,.2f}"


def _build_anomaly_note(issue_report_df: pd.DataFrame) -> str:
    """Return a short plain-language note for the anomaly chart."""
    if issue_report_df.empty or "issue_type" not in issue_report_df.columns:
        return "No anomaly findings were recorded for this run."

    anomaly_rows = issue_report_df[issue_report_df["issue_type"] == "anomaly"].copy()
    if anomaly_rows.empty:
        return "No anomaly findings were recorded for this run."

    anomaly_count = len(anomaly_rows)
    lower_bound = pd.to_numeric(anomaly_rows.get("lower_bound"), errors="coerce").dropna()
    upper_bound = pd.to_numeric(anomaly_rows.get("upper_bound"), errors="coerce").dropna()

    note_lines = [
        f"{anomaly_count} value(s) were flagged because they fall outside the usual amount range for this file.",
        "The rule uses IQR-derived lower and upper bounds from the `net_amount` values.",
    ]

    if not lower_bound.empty and not upper_bound.empty:
        note_lines.append(
            f"For this run, the lower bound was {_format_amount(lower_bound.iloc[0])} and the upper bound was {_format_amount(upper_bound.iloc[0])}."
        )

    note_lines.append("These flags are prompts for review, not automatic proof of error.")
    return " ".join(note_lines)


def _build_issue_report_preview(issue_report_df: pd.DataFrame) -> pd.DataFrame:
    """Return a lighter on-page preview of the issue report."""
    preview_df = issue_report_df.copy()
    if "value" not in preview_df.columns:
        preview_df["value"] = pd.NA
    if "observed_value" in preview_df.columns:
        preview_df["value"] = preview_df["value"].where(preview_df["value"].notna(), preview_df["observed_value"])
    if "message" not in preview_df.columns:
        preview_df["message"] = pd.NA
    if "reason" in preview_df.columns:
        preview_df["message"] = preview_df["message"].where(preview_df["message"].notna(), preview_df["reason"])

    preview_df = preview_df.reindex(columns=["row_index", "issue_type", "column", "value", "message"])
    if "issue_type" in preview_df.columns:
        preview_df["issue_type"] = preview_df["issue_type"].fillna("").astype(str).map(
            lambda value: _normalise_issue_label(value) if value else value
        )
    return preview_df.head(ISSUE_PREVIEW_ROWS)


def run_analysis(
    uploaded_file,
    editable_explanation_prompt: str,
    advanced_instructions: str | None,
) -> tuple[str, str, str, dict, Figure, Figure, str, str, str, str, pd.DataFrame]:
    """Execute the existing pipeline for an uploaded file and prepare UI outputs."""
    if uploaded_file is None:
        raise gr.Error("Please upload a CSV or Excel file before running the analysis.")

    input_path = Path(uploaded_file)
    output_dir = _build_run_output_dir()
    LOGGER.info("Running local UI analysis for %s", input_path)

    result = run_pipeline(str(input_path), str(output_dir))
    issue_report_df = _read_output_csv(result.issue_report_path, default_columns=ISSUE_REPORT_COLUMNS)
    review_log_df = _read_output_csv(result.review_log_path, default_columns=EMPTY_REVIEW_LOG_COLUMNS)
    issue_report_preview = _build_issue_report_preview(issue_report_df)
    explanation = generate_automatic_explanation(result, issue_report_df, review_log_df)
    ai_snapshot = build_issue_snapshot(result, issue_report_df, review_log_df)
    LOGGER.info(
        "Stored findings snapshot for AI suggestions: input_file=%s rows_loaded=%s issues_found=%s anomalies_flagged=%s",
        input_path.name,
        result.rows_loaded,
        result.issues_found,
        result.anomalies_flagged,
    )
    ai_suggestions = try_generate_default_ai_suggestions(
        ai_snapshot,
        editable_explanation_prompt,
        advanced_instructions,
    )
    results_overview = _format_results_overview(
        input_name=input_path.name,
        rows_loaded=result.rows_loaded,
        issues_found=result.issues_found,
        anomalies_flagged=result.anomalies_flagged,
        status=result.status,
        stop_reason=result.stop_reason,
    )
    issue_type_counts_plot = _build_issue_type_counts_plot(issue_report_df)
    anomaly_amount_plot = _build_anomaly_amount_plot(issue_report_df)
    anomaly_note = _build_anomaly_note(issue_report_df)

    return (
        results_overview,
        explanation,
        ai_suggestions,
        ai_snapshot,
        issue_type_counts_plot,
        anomaly_amount_plot,
        anomaly_note,
        result.issue_report_path,
        result.review_log_path,
        result.dataset_snapshot_path,
        issue_report_preview,
    )


def request_enhanced_ai_suggestions(
    snapshot: dict | None,
    provider: str,
    model: str,
    custom_model: str,
    base_url: str,
    api_key: str,
    editable_explanation_prompt: str,
    advanced_instructions: str | None,
) -> str:
    """Request optional enhanced AI suggestions using current findings only."""
    selected_model = custom_model.strip() if provider == "custom_openai_compatible" else model.strip()
    LOGGER.info("Advanced AI button handler entered")
    LOGGER.info("Advanced AI button selected provider: %s", provider or "<none>")
    LOGGER.info("Advanced AI button selected model: %s", selected_model or "<none>")
    LOGGER.info("Advanced AI button snapshot available: %s", bool(snapshot))
    return generate_advanced_ai_suggestions(
        snapshot,
        provider,
        model,
        custom_model,
        base_url,
        api_key,
        editable_explanation_prompt,
        advanced_instructions,
    )


def update_provider_configuration(provider: str):
    """Update provider-aware model and custom field visibility."""
    if provider == "custom_openai_compatible":
        return (
            gr.update(choices=[], value=None, visible=False),
            gr.update(value="", visible=True),
            gr.update(value="", visible=True),
        )

    model_options = get_standard_model_options(provider)
    default_model = get_default_model(provider)
    if default_model not in model_options and model_options:
        default_model = model_options[0]

    return (
        gr.update(choices=model_options, value=default_model, visible=True),
        gr.update(value="", visible=False),
        gr.update(value="", visible=False),
    )


def build_interface() -> gr.Blocks:
    """Construct the local browser-based research prototype interface."""
    with gr.Blocks(title="VAT Spreadsheet Preparation Prototype") as demo:
        gr.Markdown(
            """
            # VAT Spreadsheet Preparation Prototype
            Upload a local CSV or Excel file and run the existing review-oriented analysis pipeline.
            """
        )

        with gr.Row():
            uploaded_file = gr.File(
                label="Spreadsheet File",
                file_types=[".csv", ".xlsx", ".xls"],
                type="filepath",
            )
            run_button = gr.Button("Run Analysis", variant="primary")
        ai_snapshot_state = gr.State(value=None)

        gr.Markdown("### Results Overview")
        results_overview_output = gr.Markdown()

        gr.Markdown("### Automatic Explanation")
        automatic_explanation_output = gr.Markdown()

        gr.Markdown("### AI Suggestions")
        editable_explanation_prompt_input = gr.Textbox(
            label="Explanation Prompt",
            value=DEFAULT_EDITABLE_EXPLANATION_PROMPT,
            lines=4,
            interactive=True,
        )
        ai_suggestions_output = gr.Markdown(
            "Enhanced AI suggestions are currently unavailable. The local explanation is still available."
        )
        with gr.Accordion("Advanced AI suggestions (optional)", open=False):
            advanced_instructions_input = gr.Textbox(
                label="Advanced Instructions",
                lines=4,
                placeholder="Optional extra guidance for tone, focus, detail, or examples",
            )
            gr.Markdown(
                "Use your own provider, model, and API key for the current findings snapshot only. "
                "The uploaded spreadsheet is not sent in full."
            )
            advanced_provider_input = gr.Dropdown(
                label="Provider",
                choices=get_provider_choices(),
                value=DEFAULT_PROVIDER,
                allow_custom_value=False,
            )
            advanced_model_input = gr.Dropdown(
                label="Model",
                choices=get_standard_model_options(DEFAULT_PROVIDER),
                value=get_default_model(DEFAULT_PROVIDER),
            )
            advanced_custom_model_input = gr.Textbox(
                label="Custom Model",
                placeholder="Enter a custom model ID",
                visible=False,
            )
            advanced_base_url_input = gr.Textbox(
                label="Base URL",
                placeholder="Optional base URL for a custom OpenAI-compatible route",
                visible=False,
            )
            advanced_api_key_input = gr.Textbox(
                label="API Key",
                type="password",
                placeholder="Used only for this request",
            )
            advanced_generate_button = gr.Button("Generate Enhanced Suggestions")

        gr.Markdown("### Visual Findings")
        with gr.Row():
            with gr.Column(min_width=320):
                issue_type_counts_plot = gr.Plot(label="Issue Type Counts")
            with gr.Column(min_width=320):
                anomaly_amount_plot = gr.Plot(label="Anomaly Amount Overview")
                anomaly_note_output = gr.Markdown()

        gr.Markdown("### Download Outputs")
        with gr.Row():
            issue_report_file = gr.File(label="Issue Report", interactive=False)
            review_log_file = gr.File(label="Review Log", interactive=False)
            dataset_snapshot_file = gr.File(label="Dataset Snapshot", interactive=False)

        gr.Markdown("### Detailed Findings Preview")
        issue_report_preview = gr.Dataframe(
            label="Issue Report Preview",
            interactive=False,
            max_height=280,
            wrap=True,
            show_search="search",
        )

        run_button.click(
            fn=run_analysis,
            inputs=[
                uploaded_file,
                editable_explanation_prompt_input,
                advanced_instructions_input,
            ],
            outputs=[
                results_overview_output,
                automatic_explanation_output,
                ai_suggestions_output,
                ai_snapshot_state,
                issue_type_counts_plot,
                anomaly_amount_plot,
                anomaly_note_output,
                issue_report_file,
                review_log_file,
                dataset_snapshot_file,
                issue_report_preview,
            ],
        )
        advanced_provider_input.change(
            fn=update_provider_configuration,
            inputs=[advanced_provider_input],
            outputs=[
                advanced_model_input,
                advanced_custom_model_input,
                advanced_base_url_input,
            ],
        )
        advanced_generate_button.click(
            fn=request_enhanced_ai_suggestions,
            inputs=[
                ai_snapshot_state,
                advanced_provider_input,
                advanced_model_input,
                advanced_custom_model_input,
                advanced_base_url_input,
                advanced_api_key_input,
                editable_explanation_prompt_input,
                advanced_instructions_input,
            ],
            outputs=[ai_suggestions_output],
        )

    return demo


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    build_interface().launch(inbrowser=True)
