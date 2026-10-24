"""The isolated union experiment preserves original search and scoring contracts."""
import importlib.util

import pandas as pd
import pytest

from tests.test_pilot_20251_engine import bridge, payloads


def experiment_module():
    name = "tools.recommendation_pilot_20251.actual_experiment"
    assert importlib.util.find_spec(name) is not None, "Isolated actual-candidate runner is missing"
    return __import__(name, fromlist=["ActualCandidateEngine"])


class Sources:
    metadata = {"history_as_of_part": 20243}

    def augment(self, original, student, registrations, **kwargs):
        from tools.recommendation_pilot_20251.actual_candidates import augment_candidates
        return augment_candidates(original, student, registrations, self.catalog, self.history, **kwargs)


@pytest.fixture
def diagnostic(bridge):
    module = experiment_module()
    _, old, student, sp, cp, save = bridge
    sources = Sources()
    sources.catalog = old._catalog.copy()
    sources.catalog["course_name_sl"] = ["Course " + c for c in "ABCD"]
    sources.history = pd.DataFrame(columns=["student_id", "course_id", "part_id", "attempt_number"])
    engine = module.ActualCandidateEngine(root=old.root, sources=sources)
    engine._baseline, engine._catalog = old._baseline, sources.catalog

    class Experiments:
        def inspect(self):
            return {n: {"status": "READY", "feature_count": 44 if n == "B" else 47} for n in "BC"}

        def predict_course_rows(self, frame, name):
            assert not {"actual_mark", "final_mark", "finish_status", "points"} & set(frame)
            return frame.assign(predicted_mark=70, expected_points=3, expected_grade="B", fail_probability=.2,
                                course_history_fallback_level=6, course_history_effective_support=0)

    engine._experimental = Experiments()
    return engine, old, student, sp, cp, save, sources


def test_original_mode_matches_existing_engine(diagnostic):
    engine, old, student, *_ = diagnostic
    expected = old.evaluate_student(student, target_credits=6)
    actual = engine.evaluate_case(student, registrations=[{"course_id": "A", "course_credits": 3}],
                                  candidate_mode="original", target_credits=6)
    for key in ("plan_set_sha256", "visited_search_states", "truncated"):
        assert actual["search"][key] == expected["search"][key]
    assert actual["experiments"]["A"]["course_predictions"] == expected["experiments"]["A"]["course_predictions"]
    assert actual["candidate_count"] == expected["candidate_count"]


def test_union_has_same_space_for_abc_without_forcing_actual_into_top3(diagnostic):
    engine, _, student, sp, cp, save, _ = diagnostic
    cp["data"]["availableCourses"] = cp["data"]["availableCourses"][:2]
    save(sp, cp)
    result = engine.evaluate_case(student, registrations=[{"course_id": "C", "course_credits": 3, "final_mark": 100}],
                                  candidate_mode="augmented", target_credits=6)
    assert result["candidate_count"] == 3
    assert result["candidate_coverage"]["injected_course_count"] == 1
    assert result["search"]["evaluated_plan_count"] == 3
    hashes = {e["plan_set_sha256"] for e in result["experiments"].values()}
    assert hashes == {result["search"]["plan_set_sha256"]}
    sets = [[tuple(c["course_id"] for c in p["courses"]) for p in e["diagnostic_plans"]]
            for e in result["experiments"].values()]
    assert sets[0] == sets[1] == sets[2]
    assert "DIAGNOSTIC_ACTUAL_COURSE_INJECTION" in result["warnings"]
    for name in "ABC":
        injected = [c for c in result["experiments"][name]["course_predictions"] if c["course_id"] == "C"]
        assert injected and all(c["candidate_source"] == "ACTUAL_INJECTED" for c in injected)
        assert all(c["historical_eligibility_unverified"] for c in injected)
    assert cp["data"]["availableCourses"][-1]["COURSE_ID"] == "B"


def test_original_denied_present_actual_is_never_injected(diagnostic):
    engine, _, student, sp, cp, save, _ = diagnostic
    cp["data"]["availableCourses"][0]["STATUS_REASON_CODE"] = "DEAN"
    save(sp, cp)
    result = engine.evaluate_case(student, registrations=[{"course_id": "A", "course_credits": 3}],
                                  candidate_mode="augmented", target_credits=3)
    assert result["candidate_coverage"]["injected_course_count"] == 0
    assert all(c["course_id"] != "A" for c in result["experiments"]["A"]["course_predictions"])


def test_credit_limits_apply_to_augmented_case(diagnostic):
    engine, _, student, sp, cp, save, _ = diagnostic
    cp["data"]["registserRule"]["MAX_CREDITS"] = "3"
    save(sp, cp)
    result = engine.evaluate_case(student, registrations=[{"course_id": "A", "course_credits": 3}],
                                  candidate_mode="augmented", target_credits=6)
    assert result["status"] == "NO_MATCHING_PLAN"
    assert "REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS" in result["issues"]


def test_future_original_api_attempt_stays_blocked(diagnostic):
    engine, _, student, sp, cp, save, _ = diagnostic
    cp["data"]["availableCourses"][0]["LAST_REGISTER_SEMESTER_ID"] = "20251"
    save(sp, cp)
    result = engine.evaluate_case(student, registrations=[{"course_id": "A", "course_credits": 3}],
                                  candidate_mode="augmented", target_credits=6)
    assert result["status"] == "BLOCKED"
    assert "FUTURE_COURSE_SOURCE" in result["issues"]


def test_evaluation_never_writes_models_archived_inputs_or_trains(diagnostic, monkeypatch):
    engine, _, student, sp, cp, save, _ = diagnostic
    from tools.recommendation_pilot_20251 import modeling
    def forbidden(*args, **kwargs):
        raise AssertionError("Training is outside the diagnostic experiment")
    monkeypatch.setattr(modeling, "train_experiments", forbidden)
    sentinel = engine.root / "models" / "immutable_model.txt"
    sentinel.parent.mkdir()
    sentinel.write_bytes(b"immutable saved model")
    protected = [sentinel, *(engine.root / "snapshots/after_backend_fix/api_data").rglob("*.json")]
    before = {p: p.read_bytes() for p in protected}
    for mode in ("original", "augmented"):
        engine.evaluate_case(student, registrations=[{"course_id": "A", "course_credits": 3}],
                             candidate_mode=mode, target_credits=6)
    assert before == {p: p.read_bytes() for p in protected}
    assert not (engine.root / "experiments").exists()


def test_200_and_2000_are_deterministic_prefixes(diagnostic):
    engine, _, student, sp, cp, save, sources = diagnostic
    sp, cp = payloads(14)
    save(sp, cp)
    template = sources.catalog.iloc[0].to_dict()
    sources.catalog = engine._catalog = pd.DataFrame([{**template, "course_id": chr(65+i),
        "course_name_sl": "Course " + chr(65+i)} for i in range(14)])
    kwargs = dict(registrations=[{"course_id": "A", "course_credits": 3}], candidate_mode="original", target_credits=18)
    a = engine.evaluate_case(student, max_plans=200, **kwargs)
    b = engine.evaluate_case(student, max_plans=2000, **kwargs)
    c = engine.evaluate_case(student, max_plans=200, **kwargs)
    assert a["search"]["plan_set_sha256"] == c["search"]["plan_set_sha256"]
    assert a["search"]["truncated"] and b["search"]["truncated"]
    for name in "ABC":
        assert a["experiments"][name]["diagnostic_plans"] == b["experiments"][name]["diagnostic_plans"][:200]


def test_request_rejects_duplicate_modes_and_unknown_credit_experiment(tmp_path):
    runner = experiment_module().ActualCandidateRunner(tmp_path)
    try:
        with pytest.raises(ValueError):
            runner.start(["s"], candidate_modes=["augmented", "augmented"])
        with pytest.raises(ValueError):
            runner.start(["s"], credit_experiments=["lower_policy_silently"])
    finally:
        runner.executor.shutdown()


def test_scenario_csv_is_unambiguous_and_portable_outputs_omit_injected_rows(tmp_path):
    import csv
    import json
    module = experiment_module()
    store = module.ScenarioRunStore(tmp_path / "experiments" / "actual_candidate_injection")
    results = []
    for mode in ("original", "augmented"):
        results.append({"sample_id": "s", "candidate_mode": mode, "credit_experiment": "fixed_18", "target_credits": 18,
            "experiments": {"A": {"status": "PREDICTION_AVAILABLE", "diagnostic_plans": [{"plan_id": 0}],
                "course_predictions": [{"course_id": "injected-private", "plan_id": 0}]}},
            "candidate_coverage": {"injected_courses": [{"course_id": "injected-private"}], "injected_course_count": 1}})
    store.save("run_test", {}, results, {})
    assert (store.directory("run_test") / "dashboard_results.json").exists()
    with (store.directory("run_test") / "course_predictions.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["candidate_mode"] for row in rows] == ["original", "augmented"]
    keys = ("run_id", "created_at", "experiment", "diagnostic_only", "student_count", "result_case_count", "part_id",
            "history_as_of_part", "git", "generation_settings", "candidate_sources", "students_csv_sha256", "models",
            "pilot_code_sha256", "latency_definition", "warnings", "protection_status")
    module.portable_exports(store.directory("run_test"), dict.fromkeys(keys), results, {"latency_summary": []})
    assert "injected-private" not in (store.directory("run_test") / "portable_results" / "student_summary.csv").read_text(encoding="utf-8-sig")


def test_retired_model_registry_is_found_outside_new_run_root(tmp_path):
    import json
    module = experiment_module()
    store = module.ScenarioRunStore(tmp_path / "experiments" / "actual_candidate_injection")
    registry = tmp_path / "experiments" / "model_versions"
    registry.mkdir()
    (registry / "retired_bundles.json").write_text(json.dumps({"retired-v1": {}}), encoding="utf-8")
    row = {"sample_id": "s", "candidate_mode": "augmented", "credit_experiment": "fixed_18", "target_credits": 18,
           "experiments": {"B": {"status": "PREDICTION_AVAILABLE", "course_predictions": [{"course_id": "c"}]}}}
    store.save("run_test", {"model_versions": {"B": "retired-v1"}}, [row], {})
    actual = store.load("run_test")["student_results"][0]["experiments"]["B"]
    assert actual["reason"] == "RETIRED_EXPERIMENTAL_MODEL" and not actual["course_predictions"]
    assert store.load_dashboard("run_test")["student_results"][0]["experiments"]["B"]["reason"] == "RETIRED_EXPERIMENTAL_MODEL"


def test_dashboard_projection_keeps_top3_and_full_search_counts(tmp_path):
    store = experiment_module().ScenarioRunStore(tmp_path)
    plans = [{"plan_id": i, "courses": [{"course_id": str(i)}]} for i in range(20)]
    row = {"sample_id": "s", "candidate_mode": "augmented", "credit_experiment": "fixed_18", "target_credits": 18,
           "search": {"evaluated_plan_count": 20}, "experiments": {"A": {"status": "PREDICTION_AVAILABLE",
               "analytical_plans": plans[:3], "diagnostic_plans": plans,
               "course_predictions": [{"plan_id": i, "course_id": str(i)} for i in range(20)]}}}
    store.save("run_test", {}, [row], {})
    projected = store.load_dashboard("run_test")["student_results"][0]
    assert projected["search"]["evaluated_plan_count"] == 20
    assert len(projected["experiments"]["A"]["diagnostic_plans"]) == 3
    assert len(projected["experiments"]["A"]["course_predictions"]) == 3
    assert len(store.load("run_test")["student_results"][0]["experiments"]["A"]["diagnostic_plans"]) == 20


def test_branch_guard_rejects_unapproved_non_main_branch(monkeypatch):
    module = experiment_module()
    monkeypatch.setattr(module.subprocess, "check_output", lambda *a, **kw: "release\n")
    with pytest.raises(ValueError, match="approved experiment branch"):
        module.git_provenance()
