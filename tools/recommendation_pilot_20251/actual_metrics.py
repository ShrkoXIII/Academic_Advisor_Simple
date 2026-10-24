"""Post-prediction metrics for isolated actual-course injection diagnostics.

Outcome labels are consumed only here, after independent observed-plan scores
exist. Recommendation overlap and observed-plan prediction errors have separate
denominators. Repeated candidate/load scenarios never multiply label weight.
"""
from collections import defaultdict
from decimal import Decimal, InvalidOperation
import json
import math
from statistics import mean


MODELS = "ABC"
DIAGNOSTIC_WARNINGS = [
    "DIAGNOSTIC_ACTUAL_COURSE_INJECTION",
    "INCREASED_ACTUAL_OVERLAP_IS_NOT_PROVEN_RECOMMENDATION_IMPROVEMENT",
    "OBSERVED_PLAN_PREDICTION_IS_SEPARATE_FROM_RECOMMENDATION_QUALITY",
    "HISTORICAL_CANDIDATE_ELIGIBILITY_NOT_VERIFIABLE",
    "STUDENT_SNAPSHOT_TEMPORAL_EQUIVALENCE_UNVERIFIED_TOTAL_VALUES_UNCHANGED",
]


def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _course_id(value):
    if value is None or isinstance(value, bool):
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        number = Decimal(value)
        return format(number.normalize(), "f") if number.is_finite() else None
    except InvalidOperation:
        return value


def _credits_equal(first, second):
    first, second = _number(first), _number(second)
    return first is not None and second is not None and first > 0 and first == second


def _credit_sum(courses):
    # Credit matching uses decimal units in the plan generator too.
    return float(sum((Decimal(str(course["course_credits"])) for course in courses), Decimal(0)))


def _course_map(courses):
    """Reject ambiguous identities instead of taking an arbitrary duplicate."""
    indexed, ambiguous = {}, set()
    for course in courses:
        key = _course_id(course.get("course_id"))
        if key is None:
            continue
        if key in indexed:
            ambiguous.add(key)
        indexed[key] = course
    return indexed, ambiguous


def _actual_registration(observed):
    if not isinstance(observed, dict) or observed.get("status") not in {"AVAILABLE", "PARTIAL"}:
        return None
    indexed, ambiguous = _course_map(observed.get("courses", []))
    if (not indexed or ambiguous or len(indexed) != len(observed.get("courses", [])) or
            any((_number(course.get("course_credits")) or 0) <= 0 for course in indexed.values())):
        return None
    return indexed


def _exact_actual(plan, actual):
    courses, ambiguous = _course_map(plan.get("courses", []))
    if ambiguous or set(courses) != set(actual):
        return False
    if not all(_credits_equal(courses[key].get("course_credits"), actual[key].get("course_credits"))
               for key in actual):
        return False
    total = _credit_sum(courses.values())
    provided_total = plan.get("total_credits")
    return provided_total is None or _credits_equal(total, provided_total)


def _ranking_key(plan):
    balance = plan.get("plan_difficulty_balance") or {}
    return (-(_number(plan.get("expected_plan_gpa")) or 0),
            _number(plan.get("expected_failed_credits")) or 0,
            _number(balance.get("max_fail_probability")) or 0,
            _number(plan.get("plan_id")) or 0)


def attach_recommendation_metrics(result, observed=None, *, models=None):
    """Attach coverage after scoring, without altering plans or their ordering."""
    observed = result.get("observed_plan") if observed is None else observed
    actual = _actual_registration(observed)
    actual_ids = set(actual or {})
    actual_load = _credit_sum(actual.values()) if actual else None
    target = _number(result.get("target_credits"))
    search = result.get("search") or {}
    for name in MODELS if models is None else models:
        experiment = result.setdefault("experiments", {}).setdefault(name, {})
        plans = experiment.get("diagnostic_plans") or []
        top = experiment.get("analytical_plans") or []
        available = (actual is not None and bool(plans) and
                     experiment.get("prediction_status", experiment.get("status")) == "PREDICTION_AVAILABLE")
        possible_load = (target == actual_load) if actual_load is not None and target is not None else None
        metrics = {
            "status": "AVAILABLE" if available else "UNAVAILABLE",
            "actual_course_count": len(actual) if actual else None,
            "actual_total_credits": actual_load, "target_credits": target,
            "top1_actual_overlap": None, "top3_union_actual_overlap": None,
            "top1_actual_overlap_fraction": None, "top3_union_actual_overlap_fraction": None,
            "actual_plan_possible_by_load": possible_load,
            "actual_plan_examined": None, "actual_plan_rank": None,
            "actual_plan_top3_rank": None, "actual_plan_expected_gpa": None,
            "best_examined_expected_gpa": None,
            "evaluated_plan_count": len(plans) if available else 0,
            "visited_search_states": search.get("visited_search_states", 0),
            "search_truncated": bool(search.get("truncated", search.get("search_truncated", False))),
            "search_budget_exhausted": bool(search.get("search_budget_exhausted", False)),
            "actual_course_exposure": {},
        }
        if available:
            first = set(_course_map(top[0].get("courses", []))[0]) if top else set()
            union = set().union(*[set(_course_map(plan.get("courses", []))[0]) for plan in top[:3]])
            metrics.update(top1_actual_overlap=len(first & actual_ids),
                           top3_union_actual_overlap=len(union & actual_ids),
                           top1_actual_overlap_fraction=len(first & actual_ids) / len(actual_ids),
                           top3_union_actual_overlap_fraction=len(union & actual_ids) / len(actual_ids),
                           actual_plan_examined=bool(possible_load and any(_exact_actual(plan, actual) for plan in plans)))
            scores = [_number(plan.get("expected_plan_gpa")) for plan in plans]
            metrics["best_examined_expected_gpa"] = max((score for score in scores if score is not None), default=None)
            for rank, plan in enumerate(sorted(plans, key=_ranking_key), 1):
                if possible_load and _exact_actual(plan, actual):
                    metrics.update(actual_plan_rank=rank,
                                   actual_plan_expected_gpa=_number(plan.get("expected_plan_gpa")))
                    break
            for rank, plan in enumerate(top[:3], 1):
                if possible_load and _exact_actual(plan, actual):
                    metrics["actual_plan_top3_rank"] = rank
                    break
            examined_ids = [set(_course_map(plan.get("courses", []))[0]) for plan in plans]
            metrics["actual_course_exposure"] = {
                key: {"examined_plan_count": sum(key in ids for ids in examined_ids),
                      "examined_plan_frequency": sum(key in ids for ids in examined_ids) / len(plans)}
                for key in sorted(actual_ids)}
        experiment["recommendation_metrics"] = metrics
    return result


def _auc(labels, probabilities):
    """Mann-Whitney ROC AUC with average ranks for exact probability ties."""
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        return None
    ordered = sorted(zip(probabilities, labels))
    positive_ranks, index = 0., 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        average_rank = (index + 1 + end) / 2
        positive_ranks += average_rank * sum(label for _, label in ordered[index:end])
        index = end
    return (positive_ranks - positives * (positives + 1) / 2) / (positives * negatives)


def _error_statistics(courses):
    errors = [course["error"] for course in courses]
    failure = [course for course in courses if course.get("fail_label") is not None and
               course.get("fail_probability") is not None]
    labels = [course["fail_label"] for course in failure]
    probabilities = [course["fail_probability"] for course in failure]
    clipped = [min(max(value, 1e-15), 1 - 1e-15) for value in probabilities]
    return {"course_count": len(errors),
            "mae": mean(abs(value) for value in errors) if errors else None,
            "rmse": math.sqrt(mean(value * value for value in errors)) if errors else None,
            "bias": mean(errors) if errors else None,
            "fail_count": len(labels), "actual_fail_count": sum(labels),
            "fail_brier": mean((label - probability) ** 2 for label, probability in zip(labels, probabilities)) if labels else None,
            "fail_log_loss": -mean(label * math.log(probability) + (1 - label) * math.log(1 - probability)
                                   for label, probability in zip(labels, clipped)) if labels else None,
            "fail_roc_auc": _auc(labels, probabilities)}


def _prediction_metrics(observed, forecast):
    result = {"status": "UNAVAILABLE", "context": "actual_registered_plan_only",
              "course_errors": [], "rejected_courses": [], "missing_prediction_count": 0}
    actual = _actual_registration(observed)
    if actual is None:
        return {**result, **_error_statistics([])}
    forecast = forecast or {}
    predicted, duplicates = _course_map(forecast.get("course_predictions", []))
    ready = forecast.get("prediction_status", forecast.get("status")) == "PREDICTION_AVAILABLE"
    errors, rejected, missing = [], [], 0
    for key, course in actual.items():
        if course.get("result_status") != "AVAILABLE":
            continue
        mark = _number(course.get("actual_mark"))
        if mark is None or not 0 <= mark <= 100:
            rejected.append({"course_id": key, "reason": "INVALID_ACTUAL_MARK"})
            continue
        if not ready or key not in predicted:
            missing += 1
            continue
        row = predicted[key]
        reason = None
        if key in duplicates:
            reason = "AMBIGUOUS_PREDICTION"
        elif not _credits_equal(course.get("course_credits"), row.get("course_credits")):
            reason = "CREDIT_MISMATCH"
        elif (course.get("grade_version_id") is not None and row.get("grade_version_id") is not None and
              str(course["grade_version_id"]) != str(row["grade_version_id"])):
            reason = "GRADE_VERSION_MISMATCH"
        predicted_mark = _number(row.get("predicted_mark"))
        if reason is None and (predicted_mark is None or not 0 <= predicted_mark <= 100):
            reason = "INVALID_PREDICTED_MARK"
        if reason:
            rejected.append({"course_id": key, "reason": reason})
            continue
        probability = _number(row.get("fail_probability"))
        probability = probability if probability is not None and 0 <= probability <= 1 else None
        label = {"pass": 0, "fail": 1}.get(course.get("course_outcome_status"))
        errors.append({"course_id": key, "course_credits": _number(course["course_credits"]),
                       "actual_mark": mark, "predicted_mark": predicted_mark, "error": predicted_mark - mark,
                       "fail_label": label, "fail_probability": probability})
    return {**result, **_error_statistics(errors), "status": "AVAILABLE" if errors else "UNAVAILABLE",
            "course_errors": errors, "rejected_courses": rejected, "missing_prediction_count": missing}


def attach_prediction_metrics(result, observed=None, prediction=None, *, models=None):
    """Evaluate only separately predicted full actual plans against outcomes."""
    observed = result.get("observed_plan") if observed is None else observed
    prediction = result.get("observed_plan_prediction", {}) if prediction is None else prediction
    result["prediction_metrics"] = {}
    for name in MODELS if models is None else models:
        metrics = _prediction_metrics(observed, (prediction or {}).get("experiments", {}).get(name))
        result["prediction_metrics"][name] = metrics
        result.setdefault("experiments", {}).setdefault(name, {})["observed_prediction_metrics"] = metrics
    return result


def _average(values):
    usable = [number for number in map(_number, values) if number is not None]
    return mean(usable) if usable else None


def _percentile(values, quantile):
    values = sorted(number for number in map(_number, values) if number is not None)
    if not values:
        return None
    position = (len(values) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def _groups(row):
    summary = row.get("student_summary") or {}
    archived = _number(summary.get("start_agpa_points"))
    cohort = _number(row.get("cohort_previous_gpa", row.get("previous_gpa", summary.get("cohort_previous_gpa"))))
    return {"all": True, "low_archived_gpa": archived is not None and archived < 2,
            "low_cohort_gpa": cohort is not None and cohort < 2}


def summarize_results(results):
    """Summarize scenarios and deduplicated actual-plan forecasts separately."""
    results = list(results)
    recommendation_groups, latency_groups = defaultdict(list), defaultdict(list)
    observed_forecasts, conflicting = {}, set()
    warnings = list(DIAGNOSTIC_WARNINGS)
    for row in results:
        attach_recommendation_metrics(row)
        attach_prediction_metrics(row)
        mode, credit = row.get("candidate_mode"), row.get("credit_experiment")
        for name in MODELS:
            experiment = row["experiments"][name]
            key = (mode, credit, name)
            recommendation_groups[key].append(experiment["recommendation_metrics"])
            latency_groups[key].append({**(row.get("latency") or {}), **(experiment.get("latency") or {})})
            observation_key = (row.get("sample_id"), name)
            metrics = row["prediction_metrics"][name]
            signature = json.dumps(metrics, sort_keys=True, separators=(",", ":"), allow_nan=False)
            if observation_key in observed_forecasts and observed_forecasts[observation_key][0] != signature:
                conflicting.add(observation_key)
            else:
                observed_forecasts[observation_key] = (signature, metrics, _groups(row))
    for sample, name in sorted(conflicting):
        warnings.append(f"OBSERVED_FORECAST_DIFFERS_ACROSS_SCENARIOS:{sample}:{name}")
        observed_forecasts.pop((sample, name), None)
    recommendation_summary = []
    for (mode, credit, name), group in sorted(recommendation_groups.items(), key=lambda item: str(item[0])):
        available = [value for value in group if value["status"] == "AVAILABLE"]
        load_compatible = [value for value in available if value["actual_plan_possible_by_load"]]
        recommendation_summary.append({
            "candidate_mode": mode, "credit_experiment": credit, "model": name,
            "student_count": len(group), "available_student_count": len(available),
            "unavailable_student_count": len(group) - len(available),
            "mean_top1_actual_overlap": _average(value["top1_actual_overlap"] for value in available),
            "mean_top3_union_actual_overlap": _average(value["top3_union_actual_overlap"] for value in available),
            "mean_top1_actual_overlap_fraction": _average(value["top1_actual_overlap_fraction"] for value in available),
            "mean_top3_union_actual_overlap_fraction": _average(value["top3_union_actual_overlap_fraction"] for value in available),
            "zero_top1_overlap_student_count": sum(value["top1_actual_overlap"] == 0 for value in available),
            "zero_top3_overlap_student_count": sum(value["top3_union_actual_overlap"] == 0 for value in available),
            "load_compatible_available_student_count": len(load_compatible),
            "actual_plan_examined_student_count": sum(bool(value["actual_plan_examined"]) for value in load_compatible),
            "actual_plan_top3_student_count": sum(value["actual_plan_top3_rank"] is not None for value in load_compatible),
            "evaluated_plan_count": sum(value["evaluated_plan_count"] for value in group),
            "visited_search_states": sum(value["visited_search_states"] or 0 for value in group),
            "search_truncated_student_count": sum(value["search_truncated"] for value in group),
        })
    prediction_summary = []
    for name in MODELS:
        for group_name in ["all", "low_archived_gpa", "low_cohort_gpa"]:
            selected = [metrics for (_, model), (_, metrics, groups) in observed_forecasts.items()
                        if model == name and groups[group_name]]
            available = [metrics for metrics in selected if metrics["status"] == "AVAILABLE"]
            courses = [course for metrics in available for course in metrics["course_errors"]]
            micro = _error_statistics(courses)
            prediction_summary.append({
                "model": name, "group": group_name, "gpa_threshold": 2 if group_name != "all" else None,
                "selected_student_count": len(selected), "student_count": len(available),
                "course_count": micro["course_count"],
                **{f"micro_{key}": value for key, value in micro.items() if key != "course_count"},
                **{f"macro_{key}": _average(metrics[key] for metrics in available)
                   for key in ["mae", "rmse", "bias", "fail_brier", "fail_log_loss", "fail_roc_auc"]},
                "missing_prediction_count": sum(metrics["missing_prediction_count"] for metrics in selected),
                "rejected_course_count": sum(len(metrics["rejected_courses"]) for metrics in selected),
                "deduplication_key": "sample_id + model; identical full observed-plan forecasts across scenarios",
            })
    latency_summary = []
    fields = ["candidate_preparation_seconds", "plan_generation_seconds", "feature_extraction_seconds",
              "prediction_seconds", "ranking_seconds", "total_seconds", "total_request_seconds"]
    for (mode, credit, name), group in sorted(latency_groups.items(), key=lambda item: str(item[0])):
        summary = {"candidate_mode": mode, "credit_experiment": credit, "model": name,
                   "measurement_count": len(group)}
        for field in fields:
            values = [row.get(field) for row in group]
            summary.update({field + "_mean": _average(values), field + "_p95": _percentile(values, .95),
                            field + "_measurement_count": sum(_number(value) is not None for value in values)})
        latency_summary.append(summary)
    paired_groups = defaultdict(dict)
    for row in results:
        mode = row.get("candidate_mode")
        if mode not in {"original", "augmented"}:
            continue
        for name in MODELS:
            key = (row.get("credit_experiment"), name)
            sample = row.get("sample_id")
            paired_groups[key].setdefault(sample, {})[mode] = row["experiments"][name]["recommendation_metrics"]
    paired_summary = []
    for (credit, name), samples in sorted(paired_groups.items(), key=lambda item: str(item[0])):
        selected = [pair for pair in samples.values() if set(pair) == {"original", "augmented"}]
        available = [pair for pair in selected if all(value["status"] == "AVAILABLE" for value in pair.values())]
        paired_summary.append({
            "credit_experiment": credit, "model": name, "paired_selected_student_count": len(selected),
            "paired_student_count": len(available),
            "became_available_student_count": sum(pair["original"]["status"] != "AVAILABLE" and
                                                   pair["augmented"]["status"] == "AVAILABLE" for pair in selected),
            "augmentation_is_post_choice_diagnostic": True,
            **{f"{mode}_mean_{metric}": _average(pair[mode][metric] for pair in available)
               for mode in ["original", "augmented"]
               for metric in ["top1_actual_overlap", "top3_union_actual_overlap"]},
            **{f"mean_{metric}_delta": _average(pair["augmented"][metric] - pair["original"][metric]
                                                for pair in available)
               for metric in ["top1_actual_overlap", "top3_union_actual_overlap"]},
        })
    return {"recommendation_summary": recommendation_summary,
            "paired_recommendation_summary": paired_summary,
            "prediction_summary": prediction_summary, "latency_summary": latency_summary,
            "warnings": warnings,
            "counts": {"result_count": len(results), "student_count": len({row.get("sample_id") for row in results}),
                       "scenario_count": len({(row.get("candidate_mode"), row.get("credit_experiment")) for row in results}),
                       "unique_observed_forecast_count": len(observed_forecasts),
                       "conflicting_observed_forecast_count": len(conflicting)}}
