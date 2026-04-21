# Contributing

Thanks for contributing to this project.

This repository is an undergraduate research prototype, so the goal is to keep changes small, reviewable, and reproducible rather than to optimize for rapid feature churn.

## Before You Start

- Read [README.md](README.md) for the project purpose, setup, and run modes.
- Keep changes tightly scoped to the problem you are solving.
- Prefer local-first behaviour and avoid introducing hosted-service assumptions unless the task explicitly requires it.

## Development Setup

Use Python `3.14` to match the current GitHub Actions environment.

Windows:

```bat
python -m venv venv
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

macOS or Linux:

```bash
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip install -r requirements-dev.txt
```

## Running Locally

Source pipeline run:

Windows:

```bat
venv\Scripts\python.exe main.py --input data\demo\sample_data.csv --output-dir output
```

macOS or Linux:

```bash
venv/bin/python main.py --input data/demo/sample_data.csv --output-dir output
```

Local GUI:

Windows:

```bat
venv\Scripts\python.exe gui.py --host 127.0.0.1 --port 7860
```

macOS or Linux:

```bash
venv/bin/python gui.py --host 127.0.0.1 --port 7860
```

## Testing

Run the test suite before opening a pull request.

Windows:

```bat
venv\Scripts\python.exe -m pytest -q
```

macOS or Linux:

```bash
venv/bin/python -m pytest -q
```

If you change packaging or container-related files, also validate the relevant demo path when practical.

## Branch And Commit Guidance

- Create a focused branch for each change.
- Prefer branch names like `codex/short-description` or another short descriptive name.
- Keep commit messages short and specific.
- Avoid mixing unrelated refactors with bug fixes or docs work.

## Pull Requests

Please make pull requests easy to review:

- explain what changed
- explain why it changed
- mention how you tested it
- call out any follow-up work or known limitations

Draft PRs are encouraged when the change is still being checked.

## Scope And Style Expectations

- Match the existing code and documentation style.
- Do not silently change unrelated files.
- Prefer the minimum change that solves the stated problem.
- Keep research, evaluation, and demo claims honest and reproducible.

## AI-Related Changes

This repository supports optional AI suggestions, but the default product posture is still local-first and human-in-the-loop.

When changing AI-related behaviour:

- do not imply AI output is authoritative
- do not assume full spreadsheet uploads are sent to AI by default
- document any new environment variables or provider requirements in `README.md`

## Questions And Proposals

If a change is large, ambiguous, or changes project scope, open a discussion in the PR description before pushing the implementation too far.
