# Repository Guidelines

## Project Structure & Module Organization

This Python project builds academic course recommendations using pandas, Parquet, and LightGBM. Production code lives in `src/`: `data/` handles cleaning and splits, `features/` builds temporal history, `modeling/` trains baseline models, `evaluation/` measures results, `experiments/` contains optional research, and `recommendation/` generates and ranks plans. Centralize artifact paths in `src/paths.py`.

Tests live in `tests/`; maintenance tools are in `scripts/` and `debugging/`. Local datasets and history bundles reside in `data/`, trained artifacts in `models/`, and documentation in root Markdown files, `docs/`, and `reports/`. Start with `START_HERE.md`, `PIPELINE_README.md`, and `LOCAL_RECOMMENDATION.md`.

## Build, Test, and Development Commands

Use Python 3.10+ and the project virtual environment. Run commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.main --list
.\.venv\Scripts\python.exe -m src.main --all --dry-run
.\.venv\Scripts\python.exe -m src.main --section modeling
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.recommend_local --help
```

These list stages, preview execution, train baseline models, run the complete test suite, and display recommendation arguments, respectively. Training requires existing feature artifacts. Data/features currently write V2 outputs; modeling/evaluation/experiments read V1. Check this boundary before rebuilding.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` for modules/functions/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Follow surrounding code and document public contracts with concise docstrings. Keep cleaning logic separate from file I/O. Base `features/` and `modeling/` must remain independent of `experiments/`. No formatter or linter is currently configured.

## Testing Guidelines

Use pytest, which also collects existing `unittest.TestCase` suites. Name files `tests/test_<module>.py` and functions `test_<behavior>`. Run focused checks with `-m pytest tests/test_training_config.py -q`, then the full suite for code changes. Cover temporal cutoffs, schema/key validation, and artifact compatibility using synthetic frames and temporary directories. No numeric coverage threshold is configured; report failures and skipped artifact-dependent checks explicitly.

## Commit & Pull Request Guidelines

History mixes short descriptive subjects and `feat:` prefixes; no strict convention is established. Write clear, action-oriented subjects such as `fix: validate history cutoff`. Keep changes scoped. PRs should describe the problem, resulting behavior, validation commands/results, and any artifact or dataset-version impact; link relevant issues when available.

## Data & Temporal Integrity

Keep student records and credentials out of commits. Preserve raw data, V1 artifacts, models, and immutable `data/artifacts/history/as_of_<part>/` bundles during cleanup. Require explicit history cutoffs and derive target-semester features only from earlier finalized outcomes.
