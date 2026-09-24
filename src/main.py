"""Run the project's existing build stages in an explicit dependency order."""

import argparse
from dataclasses import dataclass
from itertools import groupby
import subprocess
import sys

from src.paths import PROJECT_ROOT


@dataclass(frozen=True)
class Step:
    name: str
    section: str
    module: str
    description: str
    dataset: str
    standard: bool = True
    request_specific: bool = False


STANDARD_SECTIONS = ("data", "features", "modeling", "evaluation", "experiments")

# Order follows the V2 source dependencies, then the existing V1 model workflow.
# Request-specific/diagnostic steps are listed here but excluded from --all.
PIPELINE = {
    "data": (
        Step("clean_degree_course", "data", "src.data.clean_degree_course", "Clean degree catalog", "V2"),
        Step("clean_student_course", "data", "src.data.clean_student_course", "Clean course history", "V2"),
        Step("clean_student_status", "data", "src.data.clean_student_status", "Clean student status", "V2"),
        Step("filter_common_students", "data", "src.data.filter_common_students", "Synchronize common students", "V2"),
        Step("build_student_course_enriched", "data", "src.data.build_student_course_enriched", "Enrich course history", "V2"),
        Step("clean_student_diploma", "data", "src.data.clean_student_diploma", "Attach diploma data", "V2"),
        Step("clean_outliers", "data", "src.data.clean_outliers", "Apply audited outlier cleaning", "V2"),
        Step("build_temporal_split", "data", "src.data.build_temporal_split", "Build temporal train/test split", "V2"),
        Step("build_registration_roster", "data", "src.data.build_registration_roster", "Build registration rosters", "V2"),
    ),
    "features": (
        Step("build_temporal_features", "features", "src.features.build_temporal_features", "Build temporal features", "V2"),
        Step("build_frozen_history", "features", "src.features.build_frozen_history", "Build immutable history for an explicit cutoff", "explicit cutoff", False, True),
    ),
    "modeling": (
        Step("train_models", "modeling", "src.modeling.train_models", "Train baseline models", "V1"),
    ),
    "evaluation": (
        Step("evaluate_plan_gpa", "evaluation", "src.evaluation.evaluate_plan_gpa", "Evaluate observed-plan GPA", "V1"),
        Step("analyze_model_errors", "evaluation", "src.evaluation.analyze_model_errors", "Analyze model errors", "V1"),
        Step("evaluate_xml_recommendations", "evaluation", "src.evaluation.evaluate_xml_recommendations", "Evaluate request-specific XML candidates", "request", False, True),
    ),
    "experiments": (
        Step("degree_points", "experiments", "src.experiments.degree_points", "Run degree/direct-points experiment (expensive)", "V1"),
    ),
    "diagnostics": (
        Step("compare_student_status_course", "diagnostics", "src.diagnostics.compare_student_status_course", "Compare cleaned student tables", "V2", False),
        Step("analyze_course_plan_changes", "diagnostics", "src.diagnostics.analyze_course_plan_changes", "Analyze course-plan changes", "V1", False),
    ),
    "recommendation": (
        Step("recommend", "recommendation", "src.recommendation.local_cli", "Run a student-specific recommendation", "request", False, True),
        Step("benchmark_recommendation", "recommendation", "src.recommendation.benchmark", "Benchmark recommendation inference (expensive)", "request", False, True),
    ),
}

STEPS = {step.name: step for section in PIPELINE.values() for step in section}


def _select_steps(args, parser):
    if args.all:
        return tuple(step for section in STANDARD_SECTIONS for step in PIPELINE[section] if step.standard)
    if args.section:
        steps = PIPELINE[args.section]
        if args.section in STANDARD_SECTIONS:
            return tuple(step for step in steps if step.standard)
        if args.section == "recommendation":
            return (STEPS["recommend"],)
        return steps
    if args.step:
        return (STEPS[args.step],)
    if args.from_section:
        if args.to_section is None:
            parser.error("--from requires --to")
        first, last = STANDARD_SECTIONS.index(args.from_section), STANDARD_SECTIONS.index(args.to_section)
        if first > last:
            parser.error("--from must precede or equal --to")
        return tuple(step for section in STANDARD_SECTIONS[first:last + 1]
                     for step in PIPELINE[section] if step.standard)
    parser.error("Select --list, --all, --section, --step, or --from/--to")


def _show_version_boundary(steps):
    standard = [step for step in steps if step.section in STANDARD_SECTIONS and step.standard]
    if {step.dataset for step in standard} >= {"V1", "V2"}:
        print("VERSION BOUNDARY: data/features write V2; modeling/evaluation/experiments read V1.", flush=True)
        print("V2 outputs are not inputs to the current V1 training path. A full V2 model pipeline is a later task.\n", flush=True)
        return True
    return False


def _list_steps():
    print("Standard build order: " + " -> ".join(STANDARD_SECTIONS))
    print("Data/features use V2; modeling/evaluation/experiments currently use V1.\n")
    for section, steps in PIPELINE.items():
        print(f"{section}:")
        for step in steps:
            label = "standard" if step.standard else "request-specific" if step.request_specific else "optional"
            print(f"  {step.name:32} {label:16} [{step.dataset}] {step.module}:main() - {step.description}")


def _run_steps(steps, forwarded, dry_run):
    mixed_versions = _show_version_boundary(steps)
    sections = []
    for section, members in groupby(steps, key=lambda step: step.section):
        group = tuple(members)
        print("=" * 60)
        print(f"SECTION: {section}")
        print("=" * 60, flush=True)
        sections.append(section)
        for index, step in enumerate(group, 1):
            command = [sys.executable, "-m", step.module, *forwarded]
            print(f"\n[{index}/{len(group)}] {step.name} [{step.dataset}]", flush=True)
            print(f"  {step.module}:main()", flush=True)
            print(f"  {subprocess.list2cmdline(command)}", flush=True)
            if step.name == "degree_points":
                print("  This experiment can take substantial time.", flush=True)
            if dry_run:
                print(f"DRY RUN {step.name}", flush=True)
                continue
            try:
                result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
            except Exception as exc:
                print(f"FAIL {step.name}: {exc}", flush=True)
                return 1
            if result.returncode:
                print(f"FAIL {step.name} (exit {result.returncode})", flush=True)
                return result.returncode
            print(f"PASS {step.name}", flush=True)
    if dry_run:
        print("\nDry run complete; no pipeline steps executed.")
    else:
        print("\nPipeline completed successfully.")
        print("Sections:")
        for section in sections:
            print(f"  {section:12} PASS")
    if mixed_versions:
        print("VERSION BOUNDARY REMAINS: V2 feature outputs are not inputs to the V1 model stages.")
    return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--" in argv:
        boundary = argv.index("--")
        own_args, forwarded = argv[:boundary], argv[boundary + 1:]
    else:
        own_args, forwarded = argv, []

    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--list", action="store_true", help="Show ordered standard and optional steps")
    selection.add_argument("--all", action="store_true", help="Run all standard sections in order")
    selection.add_argument("--section", choices=PIPELINE, help="Run one section")
    selection.add_argument("--step", choices=STEPS, help="Run one named step")
    selection.add_argument("--from", dest="from_section", choices=STANDARD_SECTIONS, help="First standard section in an inclusive range")
    parser.add_argument("--to", dest="to_section", choices=STANDARD_SECTIONS, help="Last standard section in an inclusive range")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing steps")
    args = parser.parse_args(own_args)
    if args.to_section and not args.from_section:
        parser.error("--to requires --from")
    if args.list:
        if forwarded:
            parser.error("--list does not accept step arguments")
        _list_steps()
        return 0
    steps = _select_steps(args, parser)
    if forwarded and len(steps) != 1:
        parser.error("Arguments after -- require a single selected step")
    return _run_steps(steps, forwarded, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
