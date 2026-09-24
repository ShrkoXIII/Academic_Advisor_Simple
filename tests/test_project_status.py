"""Project status reflects the outputs of the current pipeline entry points."""

from src import paths, project_status


def test_stage_paths_order_and_version_boundary(monkeypatch, capsys):
    stages = project_status.STAGES
    assert [stage.number for stage in stages] == list(range(1, 10))
    assert [stage.name for stage in stages] == [
        "Clean and merge data (V2)",
        "Temporal split (V2)",
        "Full registration roster (V2)",
        "Temporal feature engineering (V2)",
        "LightGBM model training (V1)",
        "Observed-plan GPA evaluation (V1)",
        "Error analysis by year, degree, and SHAP (V1)",
        "Degree and direct-points experiments (V1)",
        "Plan recommendation engine (V1)",
    ]
    assert stages[0].artifacts == (
        paths.STUDENT_COURSE_WITHOUT_OUTLIERS_PATH_V2,
        paths.OUTLIER_STUDENTS_AUDIT_PATH_V2,
    )
    assert stages[1].artifacts == (
        paths.TEMPORAL_TRAIN_PATH_V2,
        paths.TEMPORAL_TEST_PATH_V2,
    )
    assert stages[2].artifacts == (
        paths.TEMPORAL_TRAIN_ROSTER_PATH_V2,
        paths.TEMPORAL_TEST_ROSTER_PATH_V2,
    )
    assert stages[3].artifacts == (
        paths.TEMPORAL_TRAIN_FEATURES_PATH_V2,
        paths.TEMPORAL_TEST_FEATURES_PATH_V2,
        paths.COURSE_HISTORY_STATE_PATH_V2,
    )
    assert stages[4].artifacts == (
        paths.GRADE_MODEL_PATH,
        paths.FAIL_MODEL_PATH,
        paths.MODEL_METADATA_PATH,
        paths.CATEGORY_LEVELS_PATH,
    )

    monkeypatch.setattr(project_status, "print_model_metrics", lambda: None)
    project_status.main()
    output = capsys.readouterr().out
    assert "VERSION BOUNDARY: data/features write V2; " in output
    assert "modeling/evaluation/experiments/recommendation use V1 artifacts." in output
