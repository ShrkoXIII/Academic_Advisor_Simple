"""Temporal and schema boundaries for the isolated B/C experiments."""
import numpy as np
import pandas as pd
import pytest

from tools.recommendation_pilot_20251 import modeling


def peer_row(student, part, points, *, mark=70., credits=3., **values):
    return dict(student_id=student, student_course_id=f"{student}_{part}",
                degree_id="D", course_id="C", part_id=part,
                grade_version_id="1", points=points, final_mark=mark,
                course_credits=credits, start_agpa_points=2.,
                start_total_in_credits=30., degree_credits_count=120.,
                gpa_trend_delta=np.nan, prior_total_fail_courses=1., **values)


def test_peers_exclude_target_future_same_student_and_keep_latest_prior_attempt():
    reference = pd.DataFrame([
        peer_row("a", 20231, 0.), peer_row("a", 20241, 2.),
        peer_row("b", 20241, 4.), peer_row("target", 20241, 0.),
        peer_row("same_part", 20243, 0.), peer_row("future", 20251, 0.),
    ])
    query = pd.DataFrame([peer_row("target", 20243, 99.)])
    actual = modeling.research_features(query, reference, min_support=2)
    assert actual.peer_expected_points.iloc[0] == pytest.approx(3.)
    assert actual.similar_peer_support.iloc[0] == 2
    assert actual.peer_max_source_part.iloc[0] == 20241


def test_peer_estimate_is_missing_when_support_is_weak_without_inventing_points():
    reference = pd.DataFrame([peer_row("a", 20241, 4.)])
    query = pd.DataFrame([peer_row("target", 20243, 0.)])
    actual = modeling.research_features(query, reference)
    assert pd.isna(actual.peer_expected_points.iloc[0])
    assert actual.similar_peer_support.iloc[0] == 1


def test_difficulty_gap_uses_only_actual_prior_student_marks_and_credit_weights():
    reference = pd.DataFrame([
        peer_row("target", 20231, 0., mark=40., credits=1.),
        peer_row("target", 20241, 4., mark=80., credits=3.),
        peer_row("target", 20243, 0., mark=0., credits=3.),
        peer_row("other", 20241, 4., mark=100.),
    ])
    query = pd.DataFrame([peer_row("target", 20243, 0.), peer_row("new", 20243, 4.)])
    query["course_history_avg_mark"] = 60.
    actual = modeling.research_features(query, reference)
    assert actual.course_difficulty_gap.iloc[0] == pytest.approx(10.)
    assert pd.isna(actual.course_difficulty_gap.iloc[1])


def test_feature_matrix_rejects_original_attempt_contract_and_preserves_missingness():
    frame = pd.DataFrame({name: [None] for name in modeling.B_FEATURES})
    frame["course_history_fail_rate"] = .25
    levels = {name: ["__MISSING__", "__UNKNOWN__"] for name in modeling.CATEGORICAL_FEATURES}
    actual = modeling.model_matrix(frame, levels, modeling.B_FEATURES)
    assert actual.shape == (1, 44)
    assert actual.course_history_fail_rate.iloc[0] == .25
    assert pd.isna(actual.course_history_avg_mark.iloc[0])
    with pytest.raises(ValueError, match="Unsupported"):
        modeling.model_matrix(frame, levels, [*modeling.B_FEATURES, "course_history_avg_attempt"])


def test_temporal_split_does_not_train_on_validation_or_20251_outcomes():
    frame = pd.DataFrame({"part_id": [20242, 20243, 20251]})
    fit, validation = modeling.temporal_split(frame)
    assert fit.part_id.tolist() == [20242]
    assert validation.part_id.tolist() == [20243]


def test_loading_rejects_model_bundle_with_47_feature_serving_contract(tmp_path):
    import json
    (tmp_path / "manifest.json").write_text(json.dumps({
        "training_as_of_part": 20243, "experiments": {"B": {
            "features": [*modeling.B_FEATURES, "course_history_avg_attempt"],
        }},
    }))
    with pytest.raises(ValueError, match="contract"):
        modeling.load_model_bundle(tmp_path)


def test_serving_research_features_reuse_identical_course_context_across_plans():
    reference = pd.DataFrame([peer_row("a", 20241, 2.), peer_row("b", 20241, 4.)])
    query = pd.DataFrame([peer_row("target", 20243, 0.), peer_row("target", 20243, 0.)])
    query["plan_id"] = [0, 1]
    query["course_history_avg_mark"] = 60.
    actual = modeling.serving_research_features(query, reference, min_support=2)
    assert actual.peer_expected_points.tolist() == [3., 3.]
    assert actual.similar_peer_support.tolist() == [2, 2]
    assert len(actual) == 2


def test_actual_reduced_boosters_score_real_serving_history_without_attempt_averages():
    from tests.recommendation_fixtures import synthetic_engine
    from tests.test_pilot_20251_history import row
    fit = pd.DataFrame({name: np.arange(160, dtype=float) % 4 for name in modeling.B_FEATURES})
    for name in modeling.CATEGORICAL_FEATURES:
        fit[name] = "1"
    fit["part_id"] = 20241
    fit["final_mark"] = np.tile([40., 80.], 80)
    fit["is_fail"] = np.tile([1, 0], 80)
    models, levels, _ = modeling._fit_pair(fit, None, modeling.B_FEATURES, rounds=2)
    models["levels"] = levels
    frame = fit.iloc[:1].copy()
    frame["student_id"], frame["degree_id"], frame["course_id"] = "target", "D", "C"
    frame["part_id"], frame["plan_id"], frame["course_credits"] = 20251, 0, 3.
    frame["course_history_avg_mark"] = 999.
    frame["course_history_avg_attempt"] = 999.
    bundle = {"history": modeling.UniversityHistory([row(20241, DEGREE_ID="D", COURSE_ID="C")]),
              "models": {"B": models}, "manifest": {"experiments": {"B": {"features": modeling.B_FEATURES}}},
              "grade_scale": synthetic_engine().grade_scale}
    scored = modeling.predict_course_rows(frame, "B", bundle=bundle)
    assert scored.course_history_avg_mark.iloc[0] == pytest.approx(60.)
    assert scored.plan_total_credits.iloc[0] == 3.
    assert scored.peer_course_count.iloc[0] == 0
    assert scored.predicted_mark.between(0, 100).all()
    assert scored.fail_probability.between(0, 1).all()
    assert np.isfinite(scored.expected_points).all()
    assert models["grade"].num_feature() == 44


def test_inspection_cli_reports_absent_models_without_training_or_writing(tmp_path, capsys):
    import json
    assert modeling.main(["--inspect", "--root", str(tmp_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["B"]["status"] == report["C"]["status"] == "BLOCKED"
    assert list(tmp_path.iterdir()) == []


def test_training_context_retains_withdrawn_unlabeled_roster_course():
    from tests.test_pilot_20251_history import row
    labels = pd.DataFrame([peer_row("target", 20243, 3.)])
    roster = labels[["student_course_id", "student_id", "degree_id", "course_id", "part_id", "course_credits"]].copy()
    withdrawn = roster.iloc[0].to_dict()
    withdrawn.update(student_course_id="withdrawn", course_id="other", course_credits=2.)
    roster = pd.concat([roster, pd.DataFrame([withdrawn])], ignore_index=True)
    history = modeling.UniversityHistory([
        row(20241, DEGREE_ID="D", COURSE_ID="C"),
        row(20241, DEGREE_ID="D", COURSE_ID="other", SUM_MARKS="1600"),
    ])
    actual, report = modeling.prepare_training_rows(labels, roster, history)
    assert len(actual) == 1
    assert actual.plan_course_count.iloc[0] == 2
    assert actual.plan_total_credits.iloc[0] == 5.
    assert actual.peer_course_count.iloc[0] == 1
    assert actual.peer_total_credits.iloc[0] == 2.
    assert actual.peer_credit_weighted_avg_mark.iloc[0] == pytest.approx(43.333333333333336)
    assert report["roster_only_rows"] == 1
    assert report["roster_outcomes_used"] is False


def test_training_context_rejects_missing_or_mismatched_roster_identity():
    from tests.test_pilot_20251_history import row
    labels = pd.DataFrame([peer_row("target", 20243, 3.)])
    roster = labels[["student_course_id", "student_id", "degree_id", "course_id", "part_id", "course_credits"]].copy()
    roster["course_id"] = "different"
    history = modeling.UniversityHistory([row(20241, DEGREE_ID="D", COURSE_ID="C")])
    with pytest.raises(ValueError, match="identity"):
        modeling.prepare_training_rows(labels, roster, history)
    with pytest.raises(ValueError, match="missing"):
        modeling.prepare_training_rows(labels, roster.iloc[:0], history)


def test_inspection_sanitizes_native_booster_error_and_preserves_independent_model(monkeypatch):
    from lightgbm.basic import LightGBMError
    broken = modeling.ExperimentalModels()
    monkeypatch.setattr(broken, "_load", lambda: (_ for _ in ()).throw(LightGBMError("private-path")))
    result = broken.inspect()
    assert result["B"]["status"] == result["C"]["status"] == "BLOCKED"
    assert "private-path" not in str(result)
    independent = modeling.ExperimentalModels()
    independent._bundle = {
        "path": "local-bundle", "manifest_sha256": "manifest-hash",
        "model_errors": {"B": "MODEL_ARTIFACT_UNAVAILABLE_OR_INCOMPATIBLE"},
        "manifest": {"experiments": {"B": {}, "C": {"features": modeling.C_FEATURES}},
                     "history": {"source_manifest_sha256": "source-hash", "usable_rows_sha256": "rows-hash",
                                 "source_hashes": {"20241.json": "source-file-hash"},
                                 "history_policy_version": "audited-row-policy", "validated_row_count": 10},
                     "history_sha256": "history-file-hash", "reference_sha256": "reference-hash",
                     "roster_source_sha256": "roster-hash", "grade_scale_sha256": "scale-hash"},
    }
    result = independent.inspect()
    assert result["B"]["status"] == "BLOCKED"
    assert result["C"]["status"] == "READY"
    assert result["C"]["manifest_sha256"] == "manifest-hash"
    assert result["C"]["history_provenance"]["usable_rows_sha256"] == "rows-hash"


def test_training_rejects_root_under_original_models_before_writing(tmp_path, monkeypatch):
    original_models = tmp_path / "original_models"
    monkeypatch.setattr(modeling.paths, "MODEL_DIR", original_models)
    with pytest.raises(ValueError, match="protected"):
        modeling.train_experiments(root=original_models)
    assert not original_models.exists()
