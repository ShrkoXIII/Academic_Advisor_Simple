"""CLI entry point for the degree/points experiment."""

from pathlib import Path
import sys


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.experiments.degree_points import main


if __name__ == "__main__":
    main()
