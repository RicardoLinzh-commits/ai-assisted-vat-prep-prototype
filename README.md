# AI-Assisted Spreadsheet Records Preparation Tool for UK MTD VAT Reporting

## Overview

This repository contains a local-first Python research prototype for spreadsheet-based VAT records preparation in a UK Making Tax Digital context. The project is now positioned as a human-in-the-loop pre-submission VAT record review and correction support tool rather than a generic data-cleaning utility. The current codebase is organised around one shared Python core and several thin deployment shells.

The shared core remains in `pipeline.py` and related modules. The deployment entry points only handle launch, packaging, containerisation, and delivery. They do not own the business logic, and they do not couple evaluation code into each deployment route.

## Current Project Direction

The prototype is intended to help spreadsheet-using businesses review records before VAT submission by:

- identifying records that may be non-compliant, potentially non-compliant, or require manual review
- explaining why flagged records matter in a VAT / MTD record-preparation context
- prioritising review attention using transparent risk-oriented outputs
- supporting structured, evidence-based manual review with decision logging

The system does not replace user judgement. Its role is to surface record issues, interpret likely review significance, and support traceable pre-submission checking.

## System Boundary

This prototype is intentionally bounded. It is:

- local-first
- human-in-the-loop
- rule-driven and explanation-oriented
- focused on record review before VAT submission

It is not:

- a full accounting platform
- an HMRC submission client
- an automatic VAT filing system
- a late submission or late payment penalty tool
- a source of final legal or professional tax advice
- a guarantee of full compliance

## Target Workflow

The intended end-to-end workflow is:

```text
spreadsheet input
-> data standardisation
-> deterministic validation and risk checks
-> VAT / MTD-oriented issue categorisation
-> status and risk assignment
-> explanation of why the issue matters
-> recommended manual review action
-> human decision logging
-> pre-submission review summary
```

This means the prototype should be understood as a review-support system. Detection remains important, but the user-facing value comes from interpretation, prioritisation, and traceable manual review.

## Current Architecture

The project now follows a simplified "same Python core + five entry points" structure:

1. `main.py` for source-run / developer / dissertation reproduction use
2. `gui.py` for the main local browser GUI
3. Docker for a consistent demo/deployment shell around the same GUI service
4. PyInstaller for the Windows distributable demo package
5. A limited web demo deployment path based on the same GUI service

Core processing workflow:

```text
spreadsheet input
-> ingestion
-> preparation to canonical schema
-> deterministic validation
-> IQR anomaly flagging
-> review queue
-> exported CSV artefacts
```

Target product workflow and system boundary are documented in [docs/domain/project_direction.md](docs/domain/project_direction.md).

## Current Status Of The Five Entry Points

| Entry point | Current status | Primary use |
| --- | --- | --- |
| Python / source run | Implemented | developer use, dissertation reproduction, scripted runs |
| Local browser GUI | Implemented | main interaction entry on Windows and macOS |
| Docker | Implemented | local container demo and deployment baseline |
| Windows packaged demo | Implemented | teacher/reviewer/demo delivery |
| Web demo profile | Deployment path documented | limited public demo, not the default product form |

At the current project stage, this repository is intentionally **not** being published as a PyPI package. The codebase is still moving around a dissertation prototype and the evaluation layer is still incomplete, so source-run remains the correct Python entry for now.

## Local-First Boundary

The default shape of the project is still local-first:

- the main interaction form is the local browser GUI in `gui.py`
- Windows reviewers should primarily use the packaged demo folder / zip
- macOS local demonstration should use the same GUI from source
- the web-facing version is a limited demo profile, not the default product form

AI boundary:

- the full uploaded spreadsheet is **not** sent to AI by default
- optional AI suggestions use a compact findings snapshot only
- AI is interpretation-only and does not decide findings or rewrite the source spreadsheet
- public web demo deployments should avoid sensitive files and may disable AI controls or limit upload size

## Quick Start

### 1. Install dependencies

Windows:

```bat
venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS or Linux:

```bash
python3 -m pip install -r requirements.txt
```

### 2. Run the source entry

```bat
venv\Scripts\python.exe main.py --input data\sample_data.csv --output-dir output
```

This runs the shared pipeline directly and prints a concise summary. It is the recommended source-run path for developer checks and dissertation reproduction work.

If the input file is missing required fields, the run now still writes a minimal local diagnostic bundle in the output directory:

- `dataset_snapshot.csv`
- `input_diagnostics.csv`

The diagnostics file shows the required fields, what was mapped, which accepted aliases were available, and how to repair the upload before rerunning.

### 3. Run the local browser GUI

Windows:

```bat
venv\Scripts\python.exe gui.py --host 127.0.0.1 --port 7860
```

macOS:

```bash
./tools/run_demo_mac.command
```

Windows convenience launcher:

```bat
tools\run_demo.bat
```

### 4. Build the Windows distributable demo

```powershell
.\tools\build_demo.ps1
```

Outputs:

- `dist\VAT_Spreadsheet_Demo\`
- `dist\VAT_Spreadsheet_Demo_windows_x64.zip`

### 5. Start the Docker demo

```bash
docker compose up --build
```

Then open:

```text
http://127.0.0.1:7860
```

## Detailed Deployment Guide

Deployment and delivery details are documented in [docs/deployment.md](docs/deployment.md).

That document covers:

- how developers run from source
- how macOS local demo works
- how Windows packaged delivery works
- how Docker is launched
- how the limited web demo profile should be deployed
- what GitHub Actions now build and validate

## Data Sources

The repository contains a mix of:

- public-source raw transaction-style datasets
- adapted prototype input datasets
- controlled evaluation datasets created for testing
- supplemental synthetic realism data

These do not all have the same status. In particular:

- public raw files are open-source input material, not VAT ground truth
- adapted files are transformed convenience inputs for the prototype schema
- evaluation files are repository-authored controlled test cases
- realism outputs are synthetic supplemental datasets, not official tax truth

The full provenance and usage notes are documented in
[docs/data_sources.md](docs/data_sources.md).

## Technology And Attribution

The prototype is built on a small set of well-defined third-party tools:

- Gradio for the browser-based UI shell
- pandas for tabular processing
- openpyxl for Excel support
- Matplotlib for figure and chart generation
- PyInstaller for the Windows packaged demo
- Docker for container-based demo delivery

The most accurate short description is:

> Built with Gradio, backed by a shared Python review pipeline, with pandas for
> tabular processing and Matplotlib for figure output.

More detailed notes are documented in
[docs/technology_and_attribution.md](docs/technology_and_attribution.md).

## Main Repository Structure

- `pipeline.py` - shared orchestration entry
- `main.py` - thin source-run shell
- `gui.py` - thin browser GUI shell
- `tools/build_demo.ps1` - Windows packaging script
- `packaging/vat_spreadsheet_demo.spec` - PyInstaller spec for the Windows demo
- `tools/run_demo.bat` - Windows convenience launcher
- `tools/run_demo_mac.command` - macOS convenience launcher
- `scripts/prepare_public_datasets.py` - public dataset adaptation helper
- `docker-compose.yml` - local Docker launcher
- `Dockerfile` - single-container GUI service image
- `.github/workflows/build-windows-demo.yml` - automated Windows package build
- `.github/workflows/validate-docker-demo.yml` - Docker build validation
- `ingestion/` - spreadsheet loading and preparation
- `validation/` - deterministic checks
- `anomaly/` - anomaly detection
- `review/` - review queue and review persistence
- `export/` - CSV export outputs
- `explanation/` - local automatic explanation
- `ai/` - compact snapshot and optional AI suggestion layer
- `scripts/` - evaluation and supporting scripts
- `docs/architecture/gui_architecture.md` - justification for the current GUI shell boundary

## Notes For Ongoing Evaluation Work

The evaluation part of the dissertation is still incomplete. This deployment structure is deliberately kept separate from that work:

- deployment shells call the existing Python core instead of re-implementing pipeline steps
- packaging, Docker, and workflows do not hard-code evaluation logic
- if metrics, outputs, or evaluation scripts change later, the entry-point structure should stay stable

That separation is the main reason the repository is now organised around "one core, many thin shells" rather than separate per-platform logic.
