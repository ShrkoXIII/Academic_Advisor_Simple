"""Observed peer-feature checks must isolate targets from temporal source rows."""
import hashlib
import importlib
import json

import pandas as pd
import pytest


def module():
    spec = importlib.util.find_spec("tools.recommendation_pilot_20251.feature_validation")
    assert spec is not None, "Standalone peer-feature validation is missing"
    return importlib.import_module("tools.recommendation_pilot_20251.feature_validation")


def records():
    shared = {"degree_id": "degree", "course_id": "course", "grade_version_id": "3.111",
              "start_agpa_points": 2.5, "start_total_in_credits": 60,
              "degree_credits_count": 120, "gpa_trend_delta": .1,
              "prior_total_fail_courses": 1, "part_id": 20242, "points": 3.0}
    peers = [{**shared, "student_id": f"private_peer_{i}", "student_course_id": f"prior_{i}"}
             for i in range(6)]
    peers.append({**shared, "student_id": "private_target", "student_course_id": "prior_self", "points": 0})
    peers.append({**shared, "student_id": "private_target", "student_course_id": "target_case",
                  "part_id": 20243, "points": 2.0})
    peers.append({**shared, "student_id": "private_future", "student_course_id": "future_case",
                  "part_id": 20251, "points": 0})
    return pd.DataFrame(peers)


def test_peer_and_baseline_exclude_self_target_and_future_outcomes():
    report = module().evaluate_peer_features(records(), sample_size=60)
    assert report["target_part"] == 20243
    assert report["sample_rows"] == 1
    assert report["peer_pool_rows"] == 7
    assert report["peer_pool_max_part"] == 20242
    assert report["point_in_time_checks"]["maximum_selected_peer_part"] == 20242
    assert report["peer_expected_points"]["covered_rows"] == 1
    assert report["peer_expected_points"]["mae"] == 1.0
    assert report["same_course_mean_points_baseline"]["mae"] == 1.0
    assert report["similar_peer_support"]["minimum"] == 6
    assert report["paired_comparison"]["rows"] == 1
    assert report["paired_comparison"]["peer_minus_baseline_mae"] == 0
    assert report["student_relative_course_strength"]["status"] == "NOT_AVAILABLE"
    assert "private_" not in json.dumps(report)


def test_future_points_cannot_change_feature_metrics():
    original = records()
    changed = original.copy()
    changed.loc[changed.part_id.eq(20251), "points"] = 4.0
    before = module().evaluate_peer_features(original)
    after = module().evaluate_peer_features(changed)
    assert before == after


def test_weak_support_is_counted_without_fabricated_predictions():
    data = records()
    data = data.loc[~data.student_id.isin([f"private_peer_{i}" for i in range(2, 6)])]
    report = module().evaluate_peer_features(data)
    assert report["similar_peer_support"]["minimum"] == 2
    assert report["peer_expected_points"]["covered_rows"] == 0
    assert report["peer_expected_points"]["mae"] is None
    assert report["paired_comparison"]["rows"] == 0
    assert report["paired_comparison"]["peer_minus_baseline_mae"] is None


def test_deterministic_sample_is_independent_of_source_row_order():
    original = records()
    extra = original.loc[original.part_id.eq(20243)].copy()
    extra["student_id"], extra["student_course_id"], extra["points"] = "another_target", "another_case", 3.0
    original = pd.concat([original, extra], ignore_index=True)
    first = module().evaluate_peer_features(original, sample_size=1)
    shuffled = module().evaluate_peer_features(original.sample(frac=1, random_state=13), sample_size=1)
    assert first == shuffled


def test_true_points_are_used_without_converting_mean_marks():
    data = records()
    data["final_mark"] = 99.0
    assert module().evaluate_peer_features(data)["peer_expected_points"]["mae"] == 1.0


def test_nullable_missing_trend_remains_missing_without_breaking_knn_query():
    data = records()
    data["gpa_trend_delta"] = pd.Series([pd.NA] * len(data), dtype="Float64")
    report = module().evaluate_peer_features(data)
    assert report["peer_expected_points"]["covered_rows"] == 1
    assert report["peer_expected_points"]["mae"] == 1.0


def test_missing_historical_source_field_is_explicit():
    with pytest.raises(ValueError, match="degree_credits_count"):
        module().evaluate_peer_features(records().drop(columns="degree_credits_count"))


def test_no_target_rows_produces_explicit_blocked_diagnostic():
    report = module().evaluate_peer_features(records().loc[lambda f: f.part_id.ne(20243)])
    assert report["status"] == "BLOCKED"
    assert report["sample_rows"] == 0
    assert report["peer_expected_points"]["mae"] is None


def test_runner_hashes_source_writes_only_fresh_output_and_preserves_source(tmp_path):
    source = tmp_path / "historical_individual.parquet"
    records().to_parquet(source, index=False)
    before = source.read_bytes()
    output = tmp_path / "diagnostic"
    report = module().run_feature_validation(output, source_path=source)
    assert source.read_bytes() == before
    assert report["source_sha256"] == hashlib.sha256(before).hexdigest()
    assert report["source_row_count"] == 9
    assert report["selected_20251_outcomes_used"] is False
    saved = json.loads((output / "feature_validation_report.json").read_text())
    assert saved == report
    assert set(p.name for p in output.iterdir()) == {"feature_validation_report.json"}
    with pytest.raises(FileExistsError):
        module().run_feature_validation(output, source_path=source)


def test_runner_refuses_output_under_protected_dataset_directories(tmp_path):
    from src import paths
    with pytest.raises(ValueError, match="protected"):
        module().run_feature_validation(paths.FEATURE_DIR / "forbidden_peer_output")
