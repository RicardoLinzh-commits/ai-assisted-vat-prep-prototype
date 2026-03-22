# AI-Assisted Spreadsheet Records Preparation Tool for UK MTD VAT Reporting

## Project Overview

This repository contains a local-first Python research prototype developed for a UK undergraduate Final Year Project. It explores spreadsheet-based VAT records preparation for Making Tax Digital (MTD) contexts through a transparent, review-oriented workflow.

The prototype is intentionally modest in scope. It focuses on loading spreadsheet data, applying deterministic validation, flagging unusual `net_amount` values with a simple IQR-based rule, recording review outcomes, and exporting traceable CSV artefacts. It is designed for demonstration, evaluation, and dissertation discussion rather than production use.

## Current Progress

The current prototype already includes:

- a reusable high-level pipeline entry point via `run_pipeline(input_path, output_dir)`
- a thin command-line demo entry point in `main.py`
- a local Gradio browser UI in `gui.py`
- a local Automatic Explanation layer that works without AI or internet access
- an optional AI Suggestions layer built on a compact findings snapshot
- offline fallback when no AI provider is configured or a provider is unavailable
- advanced BYOK support with provider-aware model selection
- a public dataset adaptation script for converting selected raw public CSV files into the prototype schema

## Current Implemented Features

- local CSV and Excel spreadsheet ingestion
- deterministic validation checks for missing values, duplicate rows, invalid date formats, and invalid numeric formats
- IQR-based anomaly flagging on `net_amount`
- review-oriented handling of validation issues and anomaly findings
- traceable export outputs:
  - `dataset_snapshot.csv`
  - `issue_report.csv`
  - `review_log.csv`
- reusable orchestration through `pipeline.py`
- local browser-based demonstration UI through Gradio
- local plain-language explanation generation after each run
- optional AI suggestions using a compact findings snapshot only

## What The Prototype Does

- loads spreadsheet data from a local file
- validates the prepared VAT-style dataset against a small expected schema
- flags unusual `net_amount` values using an IQR-based rule
- combines validation findings and anomaly findings into a review worklist
- records review outcomes
- exports CSV artefacts for traceability and later inspection
- supports local demonstration through both command-line and browser-based entry points

## What The Prototype Does Not Do

- it does not submit returns or records to HMRC
- it does not perform API filing
- it does not act as a production accounting platform
- it does not automatically correct source data
- it does not silently rewrite uploaded spreadsheets
- it does not make compliance approvals or filing decisions
- it does not use AI for detection, review decisions, or source-data modification
- it does not send the full uploaded spreadsheet to AI by default

## Core Workflow

The implemented prototype flow is:

```text
data loading
-> deterministic validation
-> IQR-based anomaly flagging
-> review-oriented workflow
-> traceable export outputs
```

The reusable orchestration function is:

```python
run_pipeline(input_path: str, output_dir: str)
```

`main.py` remains a thin demo entry point that configures logging, runs the sample input through `run_pipeline(...)`, and prints a concise summary.

## Minimum Expected Input Columns

Required columns:

- `date`
- `description`
- `net_amount`
- `vat_amount`

Optional column:

- `category`

The loader normalises headings to lower case with underscores. For example, `Net Amount` becomes `net_amount`.

## Local UI

The browser-based UI in `gui.py` is a local demonstration wrapper around the existing prototype pipeline. It does not change the system boundary. Spreadsheet ingestion, deterministic validation, IQR-based anomaly flagging, review handling, and export generation remain local operations.

The page is organised around:

1. upload and run analysis
2. results overview
3. automatic explanation
4. AI suggestions
5. visual findings
6. download outputs
7. detailed findings preview

When the UI is used, each run writes outputs to a per-run folder under:

```text
output/ui_runs/
```

Each UI run still produces the same three core artefacts:

- `dataset_snapshot.csv`
- `issue_report.csv`
- `review_log.csv`

The UI is intended for local demonstration and prototype evaluation rather than remote deployment.

## Automatic Explanation

The prototype includes a local Automatic Explanation layer in `explanation/local_explainer.py`.

This explanation layer:

- runs fully offline
- does not require an API key
- remains available even when AI suggestions are unavailable
- uses only local run outputs such as `RunResult`, `issue_report.csv`, and `review_log.csv`

This local explanation is the guaranteed baseline explanation path for the prototype.

## AI Suggestions

The AI Suggestions layer is an optional enhancement, not a dependency. The local pipeline and local Automatic Explanation remain usable without internet access.

Key characteristics of the current AI Suggestions implementation:

- uses a compact findings snapshot built locally from:
  - `RunResult`
  - `issue_report.csv`
  - `review_log.csv`
- does not send the full uploaded spreadsheet by default
- does not send `dataset_snapshot.csv` by default
- preserves a fixed boundary prompt so AI remains interpretation-only
- keeps an editable explanation prompt for user control over tone and focus
- supports offline fallback with a calm unavailable message

Current provider support in the advanced panel includes:

- Gemini
- OpenAI
- Claude
- Custom OpenAI-compatible

Advanced users can optionally choose:

- provider
- model
- API key
- optional advanced instructions

For the standard Gemini, OpenAI, and Claude routes, provider-aware model selection is available in the UI so users do not need to manually type model IDs. The default explanation path is English-first and UK-oriented, but users can still replace the editable prompt with Chinese or other instructions if they wish.

## Public Dataset Adaptation

The repository also includes a small adaptation script for selected public CSV datasets:

```text
prepare_public_datasets.py
```

This script reads raw files from:

```text
data/public_raw/
```

and writes adapted outputs to:

```text
data/public_adapted/
```

The adapted files are mapped conservatively into the prototype preparation schema:

- `date`
- `description`
- `net_amount`
- `vat_amount`
- `category`

This layer is intended to support compatibility testing and prototype evaluation against public-source spreadsheet data.

## Output Files

The prototype exports persistent CSV artefacts to the requested output directory. Typical local outputs are written under:

```text
output/
```

The three core export files are:

- `dataset_snapshot.csv`
- `issue_report.csv`
- `review_log.csv`

Output meaning:

- `dataset_snapshot.csv`: a traceable snapshot of the dataset loaded for that run; it should not be interpreted as a corrected spreadsheet
- `issue_report.csv`: deterministic validation findings plus anomaly flags for review
- `review_log.csv`: review outcomes associated with the flagged items

If follow-up items remain after review, the reporting artefacts are still exported and the run returns a stop-after-reporting status internally. This preserves the review-oriented prototype workflow without automatically correcting the source spreadsheet.

## Project Structure

- `ingestion/loader.py` - spreadsheet loading
- `validation/validator.py` - deterministic validation
- `anomaly/anomaly_detector.py` - IQR-based anomaly flagging
- `review/review_manager.py` - review handling
- `export/exporter.py` - export generation
- `pipeline.py` - reusable pipeline orchestration
- `main.py` - thin command-line demo entry point
- `gui.py` - local Gradio UI
- `explanation/local_explainer.py` - local Automatic Explanation layer
- `ai/snapshot_builder.py` - compact findings snapshot construction
- `ai/suggestions_service.py` - optional AI Suggestions service logic
- `ai/providers/` - provider adapters for Gemini, OpenAI, Claude, and compatible routes
- `prepare_public_datasets.py` - public dataset adaptation helper

## Notes For Dissertation Alignment

This repository should be described as a conservative local research prototype for spreadsheet-based VAT records preparation. Its value is in demonstrating:

- modular pipeline structure
- transparent deterministic checks
- simple statistical anomaly flagging
- explicit human review handling
- traceable export artefacts
- comparison between local explanation and optional AI-assisted interpretation

It should not be described as:

- an HMRC filing platform
- a production bookkeeping system
- fully automated accounting software
- an automated correction engine
- a compliance approval tool

## Next Steps

Realistic next steps for the project include:

- improving provider-path testing for the optional AI suggestions layer
- refining error handling and edge-case reporting in the local UI
- extending evaluation with additional public datasets
- completing dissertation analysis, write-up, and results discussion

## How To Run Locally

### Install dependencies

If you need to create or refresh the environment, install dependencies with:

```bat
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Option 1: Run the thin demo entry point

```bat
venv\Scripts\python.exe main.py
```

### Option 2: Run the local browser UI

```bat
venv\Scripts\python.exe gui.py
```

Then open the local address shown in the terminal, usually:

```text
http://127.0.0.1:7860
```

### Option 3: Prepare the public adapted datasets

```bat
venv\Scripts\python.exe prepare_public_datasets.py
```

### Current sample input

The default sample dataset used by `main.py` is:

```text
data/sample_data.csv
```
