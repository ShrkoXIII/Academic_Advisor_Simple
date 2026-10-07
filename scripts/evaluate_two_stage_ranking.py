"""Offline Phase 5 evidence from synthetic predictions and saved aggregate mixes.

This tool neither loads models/history nor recommends for real students. Full
synthetic Stage 2 outcomes are a diagnostic oracle; serving scores its shortlist
only. No strategy is approved, and the Phase 6 performance benchmark is absent.
Run from the repository root: python -m scripts.evaluate_two_stage_ranking.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import pandas as pd

from src.recommendation.balance_policy import compute_balance_components
from src.recommendation.constraints import PlanConstraints
from src.recommendation.ranking import (
    RankingStrategy, canonical_plan_identity, rank_academic_reference, rank_evaluation_plans,
)


ROOT = Path(__file__).resolve().parents[1]
STRATEGIES = ("balance_first", "pareto")
METRICS = ("projected_cumulative_gpa", "expected_plan_gpa", "expected_failed_credits",
           "failed_balance_penalty", "withdrawn_balance_penalty", "total_previous_balance_penalty")


def synthetic_fixture():
    """Ten synthetic courses give 176 exact-15-credit plans under explicit caps."""
    ids = ["F1", "F2", "F3", "W1", "W2", "N1", "N2", "N3", "N4", "N5"]
    groups = ["FAILED_RETAKE"] * 3 + ["WITHDRAWN_RETAKE"] * 2 + ["NEW"] * 5
    # Dyadic values keep sum/tie expectations exact across the independent oracle.
    candidates = pd.DataFrame({"course_id": ids, "course_credits": [3] * 10,
        "candidate_group": groups, "plan_requirement_type_id": ["R"] * 10,
        "attempt_number": [2] * 5 + [1] * 5,
        "expected_points": [3.75 - i / 4 for i in range(10)],
        "fail_probability": [1 / 16] * 3 + [1 / 8] * 2 + [1 / 4] * 5})
    return candidates, PlanConstraints(15, {"R": 15}, 6, 3)


def _metrics(frame):
    return {name: float(frame[name].mean()) for name in METRICS}


def _change(frame, reference):
    selected, original = _metrics(frame), _metrics(reference)
    return {name: selected[name] - original[name] for name in METRICS}


def _diagnostic_stage2(all_plans):
    """Fabricated plan-dependent outcomes, deliberately imperfect Stage 1 proxy.

    These values do not come from any model. All plans have 15 credits, so the
    means can equivalently be represented by synthetic course-in-plan points
    and probabilities. The Stage 1 academic last plan receives a large context
    benefit to make the absence of a global-Top-K guarantee observable.
    """
    final = all_plans.sort_values("plan_id").reset_index(drop=True).copy()
    hidden = rank_academic_reference(all_plans, stage="stage1").iloc[-1].plan_id
    for i, row in final.iterrows():
        quality = 42 + ((i * 7) % 29) / 4
        failed = (2 + ((i * 11) % 19)) / 16
        if row.plan_id == hidden:
            quality, failed = 60.0, 1 / 32
        final.at[i, "expected_quality_points"] = quality
        final.at[i, "expected_failed_credits"] = failed
        final.at[i, "expected_plan_gpa"] = quality / 15
        final.at[i, "projected_cumulative_gpa"] = (120 + quality) / 75
        final.at[i, "expected_cumulative_gpa_gain"] = (120 + quality) / 75 - 2
    return final, hidden


def _top_comparison(ranked, reference, top_k=3):
    selected, original = ranked.head(top_k), reference.head(top_k)
    return {"top_plan_ids": selected.plan_id.tolist(),
            "top_course_tuples": [list(value) for value in selected.course_tuple],
            "top_k_overlap_vs_academic": len(set(selected.plan_id) & set(original.plan_id)),
            "metric_means": _metrics(selected), "metric_change_vs_academic": _change(selected, original)}


def evaluate_synthetic():
    """Compare both stages independently, then every explicit cross-stage pair."""
    from src.recommendation.shortlist import build_stage1_shortlist
    candidates, constraints = synthetic_fixture()
    selections = {name: build_stage1_shortlist(candidates, constraints,
        stage1_shortlist_strategy=RankingStrategy(stage="stage1", name=name),
        current_gpa=2, current_gpa_credits=60, part_semester=1) for name in STRATEGIES}
    all_plans = selections["balance_first"].all_plans
    stage1_reference = rank_academic_reference(all_plans, stage="stage1")
    stage2, hidden = _diagnostic_stage2(all_plans)
    final_reference = rank_academic_reference(stage2, stage="final")
    final_index = stage2.set_index("plan_id", drop=False)
    global_candidates = {name: rank_evaluation_plans(stage2,
        strategy=RankingStrategy(stage="final", name=name)).head(3) for name in STRATEGIES}
    first_rows, combinations = {}, []
    for name, selection in selections.items():
        shortlist_ids = selection.shortlist.plan_id.tolist()
        selected = final_index.loc[shortlist_ids].reset_index(drop=True)
        mixes = selection.shortlist[["failed_retake_credits", "withdrawn_retake_credits",
                                      "new_credits", "other_previous_credits"]]
        first_rows[name] = {"approval_status": "UNAPPROVED", "version": "v1",
            "plan_ids": shortlist_ids,
            "academic_shortlist_overlap": len(set(shortlist_ids) & set(stage1_reference.head(50).plan_id)),
            "stage1_metric_means": _metrics(selection.shortlist),
            "stage1_metric_change_vs_academic": _change(selection.shortlist, stage1_reference.head(50)),
            "lost_global_academic_top_k": sorted(set(final_reference.head(3).plan_id) - set(shortlist_ids)),
            "global_final_candidate_top_k_retention": {
                final: len(set(top.plan_id) & set(shortlist_ids)) for final, top in global_candidates.items()},
            "best_component_top_k_retention": {component: len(set(shortlist_ids) & set(stage2.sort_values(
                [f"{component}_balance_penalty", "projected_cumulative_gpa", "plan_id"],
                ascending=[True, False, True]).head(3).plan_id))
                for component in ("failed", "withdrawn", "total_previous")},
            "diversity": {"distinct_courses": len({course for values in selection.shortlist.course_tuple for course in values}),
                          "distinct_credit_mixes": len(mixes.drop_duplicates())}}
        for final in STRATEGIES:
            ranked = rank_evaluation_plans(selected, strategy=RankingStrategy(stage="final", name=final))
            combinations.append({"stage1_strategy": name, "final_strategy": final,
                "stage1_approval": "UNAPPROVED", "final_approval": "UNAPPROVED",
                **_top_comparison(ranked, rank_academic_reference(selected, stage="final")),
                "overlap_with_complete_synthetic_final_candidate": len(set(ranked.head(3).plan_id)
                    & set(global_candidates[final].plan_id)),
                "lost_complete_synthetic_final_candidate_top_k": sorted(set(global_candidates[final].plan_id)
                    - set(shortlist_ids))})
    fixed_ids = stage1_reference.head(50).plan_id.tolist()
    fixed = final_index.loc[fixed_ids].reset_index(drop=True)
    fixed_reference = rank_academic_reference(fixed, stage="final")
    return {"candidate_count": len(candidates), "feasible_plan_count": len(all_plans),
        "target_credits": 15, "allowed_failed_repeat_credits": 6, "allowed_withdrawn_repeat_credits": 3,
        "top_k": 3, "shortlist_limit": 50, "prediction_source": "fabricated_synthetic_values",
        "diagnostic_stage2_scope": "all_feasible_synthetic_plans_only_outside_serving",
        "hidden_stage2_best_academic_plan_id": hidden,
        "stage1_candidates": first_rows,
        "fixed_shortlist_final_comparison": {"plan_ids": fixed_ids,
            "strategies": [{"name": name, "approval_status": "UNAPPROVED", **_top_comparison(
                rank_evaluation_plans(fixed, strategy=RankingStrategy(stage="final", name=name)), fixed_reference)}
                for name in STRATEGIES]},
        "combinations": combinations,
        "complete_synthetic_stage2": json.loads(json.dumps(stage2[["plan_id", "course_tuple", *METRICS,
            "expected_quality_points", "scope_applicable", "component_active_flags"]].to_dict("records"), allow_nan=False))}


def _mix_courses(failed, withdrawn, new, other=None):
    rows = [("F", failed, "FAILED_RETAKE"), ("W", withdrawn, "WITHDRAWN_RETAKE"), ("N", new, "NEW")]
    if other is not None:
        rows.append(("O", other, "OTHER_PREVIOUS"))
    return pd.DataFrame(rows, columns=["course_id", "course_credits", "candidate_group"])


def _synthetic_eligible(selected):
    extra = _mix_courses(3, 3, 0).assign(course_id=["extraF", "extraW", "extraN"])
    return pd.concat([selected, extra], ignore_index=True)


def evaluate_historical_policy(evidence_root):
    """Validate aggregate compositions with synthetic availability and semester.

    Aggregated credit mixes contain no semester/eligibility/backlog columns.
    Their descriptive weighted counts cannot reconstruct the policy cohort.
    """
    evidence_root = Path(evidence_root)
    paths = [evidence_root / "policy_candidates.json", evidence_root / "common_credit_mixes.csv"]
    policy = json.loads(paths[0].read_text(encoding="utf-8"))
    mixes = pd.read_csv(paths[1])
    columns = [f"registered_{name}_credits" for name in ("failed_retake", "withdrawn_retake", "new", "other_previous")]
    sums_match = bool((mixes[columns].sum(axis=1) - mixes.semester_total_registered_credits).abs().lt(1e-9).all())
    if not sums_match:
        raise ValueError("Saved aggregate credit groups disagree with the recorded denominator.")
    scope = mixes.semester_total_registered_credits.between(12, 18) & mixes.registered_other_previous_credits.eq(0)
    distributions = {name: {"zero_penalty_mix_rows": 0, "positive_penalty_mix_rows": 0,
                           "zero_penalty_cases": 0, "positive_penalty_cases": 0,
                           "weighted_mean_penalty": 0.0, "maximum_penalty": 0.0}
                     for name in ("failed", "withdrawn", "total_previous")}
    for row in mixes.loc[scope].itertuples():
        selected = _mix_courses(row.registered_failed_retake_credits, row.registered_withdrawn_retake_credits,
                                row.registered_new_credits)
        result = compute_balance_components(selected, _synthetic_eligible(selected), part_semester=1)
        for name, distribution in distributions.items():
            penalty = result[f"{name}_balance_penalty"]
            category = "zero" if penalty == 0 else "positive"
            distribution[f"{category}_penalty_mix_rows"] += 1
            distribution[f"{category}_penalty_cases"] += int(row.case_count)
            distribution["weighted_mean_penalty"] += penalty * int(row.case_count)
            distribution["maximum_penalty"] = max(distribution["maximum_penalty"], penalty)
    cases = int(mixes.loc[scope, "case_count"].sum())
    for distribution in distributions.values():
        distribution["weighted_mean_penalty"] /= cases
    return {"unique_mix_rows": len(mixes), "descriptive_cases": int(mixes.case_count.sum()),
        "all_group_sums_match_denominator": sums_match,
        "synthetic_scope_mix_rows": int(scope.sum()), "synthetic_scope_descriptive_cases": cases,
        "excluded_mix_rows": int((~scope).sum()),
        "saved_reference_cases": policy["reference_cases"], "saved_reference_students": policy["reference_students"],
        "policy_version": "B_observed_middle_v1",
        "eligibility_source": "explicit_synthetic_positive_failed_and_withdrawn",
        "semester_source": "synthetic_part_semester_1",
        "interpretation": "Descriptive weighted credit compositions only; not a reconstructed policy reference cohort or outcome improvement.",
        "penalty_distributions": distributions,
        "source_hashes": {path.name: sha256(path.read_bytes()).hexdigest() for path in paths}}


def evaluate_sensitivities():
    """Show exact boundary distances, eligibility disabling and zero-course scope."""
    specifications = [("failed_lower_boundary", 3, 0, 15, None, 1, True),
        ("failed_upper_boundary", 4, 0, 13, None, 2, True),
        ("failed_above_upper", 3.75, 0, 11.25, None, 1, True),
        ("summer", 3, 0, 12, None, 3, True),
        ("outside_load", 3, 0, 8.99, None, 1, True),
        ("zero_other", 3, 0, 12, 0, 1, True),
        ("zero_new", 3, 0, 12, None, 1, True),
        ("no_repeat_eligibility", 0, 0, 15, None, 1, False),
        ("withdrawn_upper_boundary", 3, 3, 11, None, 1, True),
        ("total_previous_upper_boundary", 2, 2, 10, None, 1, True)]
    results = []
    for name, failed, withdrawn, new, other, semester, available in specifications:
        selected = _mix_courses(failed, withdrawn, new, other)
        if name == "zero_new":
            selected = pd.concat([selected, pd.DataFrame([("zeroN", 0, "NEW")], columns=selected.columns)])
        eligible = _synthetic_eligible(selected) if available else selected
        identity = canonical_plan_identity(selected.course_id)
        results.append({"name": name, "course_tuple": list(identity.course_tuple), "plan_id": identity.plan_id,
                        **compute_balance_components(selected, eligible, part_semester=semester)})
    return results


def evaluate_mixed_scope():
    """Out-of-scope plans keep their academic positions in every candidate order."""
    rows = []
    for name, quality, failed in [("academic", 54, .1), ("outside", 51, .2), ("balanced", 48, .3)]:
        selected = _mix_courses(3 if name == "balanced" else 6, 0, 12 if name == "balanced" else 9)
        if name == "outside":
            selected = _mix_courses(3, 0, 12, 0)
        identity = canonical_plan_identity([name])
        rows.append({"plan_id": identity.plan_id, "course_tuple": identity.course_tuple,
            "expected_quality_points": quality, "expected_failed_credits": failed,
            "expected_plan_gpa": quality / 15, "projected_cumulative_gpa": (120 + quality) / 75,
            **compute_balance_components(selected, _synthetic_eligible(selected), part_semester=1)})
    frame = pd.DataFrame(rows)
    results = []
    for stage in ("stage1", "final"):
        reference = rank_academic_reference(frame, stage=stage)
        academic_names = [value[0] for value in reference.course_tuple]
        for name in STRATEGIES:
            ranked = rank_evaluation_plans(frame, strategy=RankingStrategy(stage=stage, name=name))
            names = [value[0] for value in ranked.course_tuple]
            results.append({"stage": stage, "strategy": name, "academic_course_names": academic_names,
                            "ranked_course_names": names,
                            "outside_positions_preserved": names.index("outside") == academic_names.index("outside")})
    return results


def build_evaluation_report(evidence_root=ROOT / "reports/repeat_withdrawal_analysis"):
    """Return deterministic evidence; no timing results or production approval."""
    source_paths = [Path(__file__), ROOT / "src/recommendation/shortlist.py",
                    ROOT / "src/recommendation/ranking.py", ROOT / "src/recommendation/balance_policy.py",
                    ROOT / "src/recommendation/plan_generation.py", ROOT / "src/recommendation/constraints.py",
                    ROOT / "src/recommendation/plan_scoring.py"]
    return {"phase": 5, "production_ranking_strategy": "UNAPPROVED", "benchmark_performed": False,
        "evidence_scope": "Synthetic course identities/predictions and saved aggregate credit mixes; no student records or real recommendations.",
        "source_hashes": {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest() for path in source_paths},
        "synthetic": evaluate_synthetic(), "historical_policy": evaluate_historical_policy(evidence_root),
        "sensitivity": evaluate_sensitivities(), "mixed_scope": evaluate_mixed_scope(),
        "complexity": "Existing exhaustive/pruned search is unchanged; Pareto uses quadratic pairwise dominance. Operational cost is deferred to Phase 6.",
        "correctness_note": "Exact decimal credit scaling and sums remain independent of Decimal context; "
            "Stage 1 aggregation uses exact Fraction products before float conversion. These narrow arithmetic fixes preserve the approved search algorithm and architecture.",
        "limitations": ["Synthetic predictions do not establish GPA or failure improvements for students.",
            "Saved aggregates lack historical eligible alternatives, their predictions, and all university policies.",
            "Top K is optimal only under the chosen candidate order within Stage 1 shortlist, without global guarantee.",
            "Strategies and their combination require independent review and approval; no automatic selection."]}


def save_report(report, output_dir):
    """Write the reviewable comparison evidence to the requested local directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    synthetic, historical = report["synthetic"], report["historical_policy"]
    lines = ["# Phase 5 — Two-stage candidate comparison", "",
        "Status: evaluation complete; Stage 1, Final and their combinations remain **UNAPPROVED**.", "",
        report["evidence_scope"], "", "## Synthetic complete-set evidence", "",
        f"{synthetic['candidate_count']} synthetic candidates produce {synthetic['feasible_plan_count']} exact-15-credit feasible plans. "
        "Failed cap=6; Withdrawn cap=3; shortlist cap=50; Top K=3. Predictions are fabricated, not model outputs.", "",
        "The full-set Stage 2 outcomes below are diagnostic synthetic values outside serving. The engine never uses them to score beyond its shortlist.", "",
        "| Stage 1 | Overlap with academic 50 | Distinct courses / mixes | Global academic Top-3 lost | Final candidate Top-3 retained (balance / Pareto) |", "| --- | ---: | --- | ---: | --- |"]
    for name, row in synthetic["stage1_candidates"].items():
        retained = row["global_final_candidate_top_k_retention"]
        lines.append(f"| {name} | {row['academic_shortlist_overlap']}/50 | {row['diversity']['distinct_courses']} / {row['diversity']['distinct_credit_mixes']} | "
                     f"{len(row['lost_global_academic_top_k'])} | {retained['balance_first']}/3 / {retained['pareto']}/3 |")
    lines += ["", "Stage 1 changes below are means over the selected 50 compared with the academic 50. "
              "Final changes are means over Top 3. Lower penalties express closer distance to the bands; no penalties are summed.", "",
              "| Stage 1 | GPA change | Failed-credit change | Failed penalty change | Withdrawn penalty change | Total-previous penalty change | Best-component Top-3 retained (F / W / Total) |",
              "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for name, row in synthetic["stage1_candidates"].items():
        delta, retained = row["stage1_metric_change_vs_academic"], row["best_component_top_k_retention"]
        lines.append(f"| {name} | {delta['projected_cumulative_gpa']:.6f} | {delta['expected_failed_credits']:.6f} | "
            f"{delta['failed_balance_penalty']:.6f} | {delta['withdrawn_balance_penalty']:.6f} | "
            f"{delta['total_previous_balance_penalty']:.6f} | {retained['failed']}/3 / {retained['withdrawn']}/3 / {retained['total_previous']}/3 |")
    lines += ["", "Each candidate's metrics and full identities are recorded separately in JSON.", "",
              "## Final candidates on the same fixed shortlist", "",
              "The fixed set is the academic Stage 1 Top-50. Its identity list is shared by both comparisons.", "",
              "| Final | Academic Top-3 overlap | GPA change | Failed-credit change | Failed penalty change | Withdrawn penalty change | Total-previous penalty change |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in synthetic["fixed_shortlist_final_comparison"]["strategies"]:
        delta = row["metric_change_vs_academic"]
        lines.append(f"| {row['name']} | {row['top_k_overlap_vs_academic']}/3 | {delta['projected_cumulative_gpa']:.6f} | "
            f"{delta['expected_failed_credits']:.6f} | {delta['failed_balance_penalty']:.6f} | "
            f"{delta['withdrawn_balance_penalty']:.6f} | {delta['total_previous_balance_penalty']:.6f} |")
    lines += ["", "## All four cross-stage combinations", "",
        "| Stage 1 → Final | Academic Top-3 overlap within shortlist | Overlap with full synthetic Final Top-3 | Top course tuples |", "| --- | ---: | ---: | --- |"]
    for row in synthetic["combinations"]:
        lines.append(f"| {row['stage1_strategy']} → {row['final_strategy']} | {row['top_k_overlap_vs_academic']}/3 | "
            f"{row['overlap_with_complete_synthetic_final_candidate']}/3 | {row['top_course_tuples']} |")
    lines += ["", "## Saved aggregate-policy evidence", "",
        f"Saved mixes: {historical['unique_mix_rows']} unique compositions / {historical['descriptive_cases']} descriptive cases. "
        f"All credit-group sums match denominators. Load 12–18 and no Other select {historical['synthetic_scope_mix_rows']} mixes / "
        f"{historical['synthetic_scope_descriptive_cases']} descriptive cases.", "",
        f"These are evaluated with explicit synthetic semester 1 and positive eligible Failed/Withdrawn alternatives. They are not the saved "
        f"reference cohort ({historical['saved_reference_cases']} cases / {historical['saved_reference_students']} students): the mix file does not carry semester or eligibility/backlog.", "",
        "| Component | Zero-penalty cases | Positive-penalty cases | Descriptive weighted mean | Maximum |", "| --- | ---: | ---: | ---: | ---: |"]
    for name, row in historical["penalty_distributions"].items():
        lines.append(f"| {name} | {row['zero_penalty_cases']} | {row['positive_penalty_cases']} | {row['weighted_mean_penalty']:.6f} | {row['maximum_penalty']:.6f} |")
    lines += ["", "Historical counts are descriptive composition weights, not ranking weights or evidence of student outcome improvement.", "",
              "## Boundary and scope sensitivity", "", "| Case | Scope applies | Active Failed / Withdrawn / Total | Failed / Withdrawn / Total distance |", "| --- | --- | --- | --- |"]
    for row in report["sensitivity"]:
        flags = row["component_active_flags"]
        lines.append(f"| {row['name']} | {row['scope_applicable']} | {[flags[name] for name in ('failed','withdrawn','total_previous')]} | "
                     f"{[row[f'{name}_balance_penalty'] for name in ('failed','withdrawn','total_previous')]} |")
    lines += ["", "Zero New remains a separate identity without credit-ratio changes; zero Other disables scope. "
              "Distances outside bands remain soft, and disabled components are missing rather than ideal zero.", "",
              "Mixed-scope cases in both stages and both candidates reorder [academic, outside, balanced] to "
              "[balanced, outside, academic]; the outside position stays fixed. Full results are in JSON.", "",
              "## Correctness, cost and limits", "", "Independent tests enumerate all subsets with Fraction and peel complete Pareto fronts. "
              "They compare both Stage 1 top-50 orders and all four Final top-3 selections. Complete ties and mixed scope remain covered by Phase 4 tests.", "",
              report["correctness_note"], "", report["complexity"], "", "No Phase 6 benchmark, approved strategy, model training, history/data mutation or real-student recommendation occurred.", "",
              *[f"- {item}" for item in report["limitations"]], "", "Source hashes and the complete synthetic metrics are in comparison.json.", ""]
    (output_dir / "comparison.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/two_stage_phase5")
    args = parser.parse_args(argv)
    report = build_evaluation_report()
    save_report(report, args.output_dir)
    print(f"Phase 5 evaluation saved to {args.output_dir}; strategies remain UNAPPROVED.")


if __name__ == "__main__":
    main()
