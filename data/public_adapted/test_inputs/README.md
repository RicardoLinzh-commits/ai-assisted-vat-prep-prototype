# Test Input Guide

This folder collects the easiest-to-run input files for manual software checks.

The original source copies are still kept in their existing locations so the
project scripts and evaluation pipeline do not break. This folder exists only
to make the runnable datasets easier to find in one place.

For provenance, source status, and dataset boundaries, see:

- `docs/data_sources.md`

## Recommended Files

- `sample_data.csv`
  - small general sample for a quick end-to-end run
- `synthetic_vat_realism_dataset.csv`
  - the realism dataset based on the UCI-style transaction substrate
  - best choice when you want a more realistic manual demo
- `review_support_case.csv`
  - controlled evaluation case for explanation and usefulness checks
- `decision_logging_case.csv`
  - controlled evaluation case for review workflow and decision logging
- `deterministic_validation_case.csv`
  - controlled evaluation case for deterministic rule checks

## Supporting Files For The Realism Dataset

- `synthetic_vat_realism_summary.csv`
  - short summary of the realism dataset composition
- `synthetic_vat_realism_metadata.json`
  - generation metadata for the realism dataset

## Suggested Manual Demo Order

1. Run `sample_data.csv` to show the standard flow.
2. Run `synthetic_vat_realism_dataset.csv` to show how the prototype behaves on
   a more realistic transaction-style dataset.
3. Run `review_support_case.csv` if you want a small controlled example for
   explaining why the enhanced review output is more useful than a raw issue
   list.
