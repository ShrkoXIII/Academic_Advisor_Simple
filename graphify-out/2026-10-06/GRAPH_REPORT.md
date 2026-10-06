# Graph Report - Academic_Advisor_Simple  (2026-10-05)

## Corpus Check
- 256 files · ~2,289,470 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 51 file(s) not represented in the graph (top: .csv 18, .log 14, .parquet 8)

## Summary
- 2201 nodes · 4954 edges · 136 communities (118 shown, 18 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 216 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- paths.py
- analyze_model_errors.py
- two_stage_artifacts.py
- engine.py
- test_recommendation_v2.py
- test_two_stage_artifacts.py
- test_recommendation_inputs_v2.py
- add_specialty_history_features
- test_modeling_v2_io.py
- pathlib
- test_temporal_features.py
- test_clean_outliers.py
- evaluation/evaluate_xml_recommendations.py
- previous_course_status_inference.py
- previous_course_status_experiment.py
- attempt_number_training.py
- numpy
- test_main_runner.py
- clean_id_columns
- Storyboard — Recommendation V2 — Student 29485.111
- test_clean_student_course.py
- analyze_repeat_withdrawal_balance.py
- مسار مشروع Academic Advisor كاملًا
- What You Must Do When Invoked
- test_repeat_withdrawal_balance.py
- parameters
- train_models.py
- previous_course_status_training.py
- تحليل وتجربة `attempt_number` المعزولة
- GradeScale
- manifest.json
- fail
- Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب
- تحليل أخطاء مودل العلامة والخطة حسب السنة والاختصاص
- الخطة النهائية: 33 → 50 → 47 مع Balance كهدف فعلي
- test_train_models.py
- تحليل تشخيصي لأعمدة طلب التوصية
- تقرير أخطاء أفضل مودل Expected Points
- test_v2_pipeline.py
- test_model_artifact_isolation.py
- clean_student_status
- course_only_training.py
- test_experiments_v2_io.py
- explain_recommendation.py
- fail
- metadata
- previous_course_status_evaluation.py
- clean_student_status.py
- experiment_io.py
- pandas
- grade
- متابعة بناء Academic Advisor
- merge
- Recommendation Trace — Student 29485.111
- clean_student_diploma
- Readme.md
- modeling.py
- provenance
- تدقيق مسار البيانات والمودلات والتوصية — 2026-09-14
- test_build_registration_roster.py
- degree_points.py
- test_previous_course_status_inference.py
- Academic Advisor — Architecture Audit before PHP/Backend integration
- PREVIOUS_COURSE_STATUS EXPERIMENT
- compute_plan_context_features
- course_only_recommendation.py
- fail_risk_classifier
- input_sha256_at_promotion
- input_sha256
- COURSE-ONLY 33-FEATURE EXPERIMENT
- Production Contract — PHP ↔ Python Recommendation Service
- C. 47 Feature Audit
- key_level
- تجربة الاختصاص وتوقع النقاط المباشر
- test_clean_utils.py
- levels
- student_status_course_comparison_metrics.json
- student_level
- test_feature_pipeline.py
- test_filter_common_students.py
- repeat_withdrawal_balance.py
- Repository Guidelines
- graphify reference: extra exports and benchmark
- course_history
- grade_regressor
- Project State — Productization Baseline
- course_only_report.py
- توثيق Baseline قبل تنفيذ Recommendation Two-stage
- Model Artifact Isolation Audit Implementation Plan
- تشغيل توصيات الخطط محلياً
- selected_candidate
- feature_contract
- J. Candidate & Requirement Policy Contract
- inner_merge
- Model Artifact Isolation Audit
- التحقق من التوصية بالتراكمي المتوقع والتاريخ المجمد
- summary.md
- ابدأ من هنا — Academic Advisor
- Official Recommendation V2 migration — 2026-09-27
- graphify reference: query, path, explain
- Isolated attempt-number experiment plan
- rebuild_common_students_v2.py
- pytest
- student_level
- مراجعة خصائص المودل — 2026-09-10
- جدول تتبع تحسينات المودل
- ImportTests
- artifacts
- training_weight
- F. Precomputed Serving State
- Data / Features V2 migration report — 2026-09-21
- I. Semester Update Lifecycle
- H. Frozen History Analysis
- تحقق مسار توصيات الخطط المحلي — 2026-09-12
- 18. Top 3 Output
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- artifact_sha256
- D. Raw Data Sources
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- extraction-spec.md
- 2026-09-27-course-only-recommendation.md
- student_status_course_comparison.md
- .apply
- 13. GradeScale Conversion
- 1. Executive Summary
- 21. Risks / Edge Cases
- verification.md
- academic-advisor-simple

## God Nodes (most connected - your core abstractions)
1. `file_sha256()` - 41 edges
2. `prepare_model_matrix()` - 35 edges
3. `clean_id_columns()` - 31 edges
4. `require_current_features()` - 31 edges
5. `load_frozen_history()` - 31 edges
6. `AcademicPlanRecommender` - 31 edges
7. `clean_student_course()` - 30 edges
8. `clean_column_names()` - 29 edges
9. `GradeScale` - 29 edges
10. `build_frozen_history()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `attempt_number: القرار المدعوم بالأدلة` --references--> `clean_student_course()`  [INFERRED]
  reports/..md → src/data/clean_student_course.py
- `11. Model Matrix and Feature Contract` --references--> `prepare_model_matrix()`  [INFERRED]
  reports/recommendation_student_29485_111_trace.md → src/features/feature_contract.py
- `2. Pipeline Map` --references--> `build_frozen_history()`  [INFERRED]
  reports/pre_modeling_v2_audit.md → src/features/frozen_history.py
- `6. Leakage Audit` --references--> `build_temporal_course_history()`  [INFERRED]
  reports/pre_modeling_v2_audit.md → src/features/temporal_features.py
- `أين وصل المشروع الآن؟` --references--> `GradeScale`  [INFERRED]
  START_HERE.md → src/grade_scale.py

## Import Cycles
- None detected.

## Communities (136 total, 18 thin omitted)

### Community 0 - "paths.py"
Cohesion: 0.07
Nodes (44): Final output shape: Frozen History, 18. Production Complexity, 9. Tests, 5. Which Frozen History Was Selected and Why, الـ bundle الفعلي المستخدم, المعنى والمواعيد الأربعة, لماذا frozen، وكيف يمنع التسرب؟, من أين بُني؟ (+36 more)

### Community 1 - "analyze_model_errors.py"
Cohesion: 0.05
Nodes (52): GPA للخطط المسجلة الفعلية, attach_analysis_columns(), build_course_segments(), build_degree_analysis(), build_plan_frame(), build_plan_segments(), build_shap_importance(), build_year_analysis() (+44 more)

### Community 2 - "two_stage_artifacts.py"
Cohesion: 0.06
Nodes (31): Completion evidence, Data and features V2 structural migration, Evidence and rulings, Review focus, Tasks, build_promotion_manifest(), promote_shortlist_artifacts(), verify_training_sources() (+23 more)

### Community 3 - "engine.py"
Cohesion: 0.08
Nodes (20): 6. Error contract, 8. Reference regression case, 8. الربط اللاحق بالـAPI, I. Recommendation impact, run_recommendations(), observed_plan_estimate(), model_training_provenance(), AcademicPlanRecommender (+12 more)

### Community 4 - "test_recommendation_v2.py"
Cohesion: 0.08
Nodes (31): load_recommendation_artifacts(), RecordingModel, synthetic_candidates(), synthetic_components(), synthetic_course_history(), synthetic_engine(), synthetic_grade_scale(), synthetic_snapshot() (+23 more)

### Community 5 - "test_two_stage_artifacts.py"
Cohesion: 0.11
Nodes (36): artifact_root(), digest(), expected_contract(), FakeBooster, load(), mutate_manifest(), promote(), promoted_files() (+28 more)

### Community 6 - "test_recommendation_inputs_v2.py"
Cohesion: 0.05
Nodes (37): 10. Blockers, 11. Non-blocking Review Items, 12. Final Decision, 1. Executive Result, 2. Pipeline Map, 3. Artifact Inventory, 4. V1/V2 Isolation, 5. Temporal Integrity (+29 more)

### Community 7 - "add_specialty_history_features"
Cohesion: 0.06
Nodes (35): 10. Specialty-History Support Analysis, 11. Course-Level Accuracy, 12. Bias Analysis, 13. Tail / Extreme Error Analysis, 14. Direct-Points Experiments, 15. Credit-Weighting Experiments, 16. Degree ID vs Degree History, 17. Robustness / Bootstrap (+27 more)

### Community 8 - "test_modeling_v2_io.py"
Cohesion: 0.07
Nodes (14): clean_xml(), get_value(), load_xml(), convert_xml_to_json(), main(), xml_rows(), feature_rows(), isolated_io() (+6 more)

### Community 9 - "pathlib"
Cohesion: 0.08
Nodes (13): تحقق النسخة النهائية, طريقة الرصد وحدودها, cohort_counts(), main(), count(), main(), benchmark(), main() (+5 more)

### Community 10 - "test_temporal_features.py"
Cohesion: 0.10
Nodes (19): الأولوية الحالية, اليوم الأول: كيف تُبنى الخصائص — حوالي 4.5 ساعات, اليوم الثاني: التدريب والتقييم — حوالي 4 ساعات, ملفات لا تعطيها وقتًا كبيرًا الآن, attach_plan_context(), build_feature_tables(), main(), print_feature_summary() (+11 more)

### Community 11 - "test_clean_outliers.py"
Cohesion: 0.08
Nodes (34): Appendix: 62-column outlier-filtered output inventory, `build_registration_roster.py`, `build_student_course_enriched.py`, `build_temporal_features.py`, `build_temporal_split.py`, `clean_degree_course.py`, `clean_outliers.py`, `clean_student_course.py` (+26 more)

### Community 12 - "evaluation/evaluate_xml_recommendations.py"
Cohesion: 0.14
Nodes (22): 6. Input Parsing, select_cases(), clean_column_names(), clean_id(), actual_metrics(), course_overlap(), course_text(), json_value() (+14 more)

### Community 13 - "previous_course_status_inference.py"
Cohesion: 0.09
Nodes (18): compare_course_sets(), distribution(), optimize_exact_credits(), plan_context_sensitivity(), prepare_course_rows(), score_courses_once(), compare_case(), experimental_run() (+10 more)

### Community 14 - "previous_course_status_experiment.py"
Cohesion: 0.11
Nodes (20): augment_feature_frame(), build_experimental_datasets(), build_status_history(), _distribution(), _keys(), previous_status_for_targets(), main(), _protected_paths() (+12 more)

### Community 15 - "attempt_number_training.py"
Cohesion: 0.12
Nodes (18): main(), save_provenance(), source_signature(), capture_protected(), paired_cluster_interval(), protected_manifest(), row_fingerprint(), transform_matrix() (+10 more)

### Community 16 - "numpy"
Cohesion: 0.07
Nodes (4): save_json(), show(), table(), display()

### Community 17 - "test_main_runner.py"
Cohesion: 0.11
Nodes (17): _list_steps(), main(), _run_steps(), _select_steps(), _show_version_boundary(), Step, _record_processes(), test_all_dry_run_shows_v2_commands_without_execution() (+9 more)

### Community 18 - "clean_id_columns"
Cohesion: 0.13
Nodes (10): audit_policy(), compare_tables(), main(), verify_policy_only(), compare(), describe(), main(), original_cleaner() (+2 more)

### Community 19 - "Storyboard — Recommendation V2 — Student 29485.111"
Cohesion: 0.07
Nodes (26): Delivery and continuity checks, Editable layer inventory, Evidence lock for the edit, Production preparation for Higgsfield / native compositor, Reusable animated motifs, Scene 10 — من قائمة إلى خطط, Scene 11 — سياق الخطة والمواد الأخرى, Scene 12 — 47 خاصية ومصفوفة مشتركة (+18 more)

### Community 20 - "test_clean_student_course.py"
Cohesion: 0.18
Nodes (24): clean_student_course(), main(), _course_row(), test_all_course_id_columns_use_safe_id_normalization(), test_any_exclusion_flag_n_removes_the_course(), test_attempts_are_numbered_per_student_and_course_after_chronological_sort(), test_both_critical_keys_missing_on_same_row_yields_empty_clean_frame(), test_clean_student_course_basic_contract_and_input_immutability() (+16 more)

### Community 21 - "analyze_repeat_withdrawal_balance.py"
Cohesion: 0.15
Nodes (18): finish_status_inventory(), grade_range_disagreements(), graph_navigation(), main(), nonstandard_history_sensitivity(), protected_manifest(), run(), sha256() (+10 more)

### Community 22 - "مسار مشروع Academic Advisor كاملًا"
Cohesion: 0.08
Nodes (26): 0. تعريف المسارات المركزي, 10. هندسة الخصائص الزمنية, 11. عقد الخصائص الرسمي, 12. التدريب الرسمي, 13. تقييم GPA للخطة الفعلية, 14. تحليل الأخطاء, 15. تجربة الاختصاص وExpected Points, 16. محرك ترشيح الخطط الحالي (+18 more)

### Community 23 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 24 - "test_repeat_withdrawal_balance.py"
Cohesion: 0.14
Nodes (19): policy_candidates(), rows(), test_analysis_runner_preserves_inputs_and_rejects_existing_output(), test_available_credits_use_last_prior_not_current_credit_value(), test_conflicting_same_semester_attempts_are_rejected(), test_current_and_future_outcomes_cannot_change_previous_status(), test_decimal_and_zero_credit_courses_are_not_rounded(), test_exact_duplicates_are_reported_and_do_not_double_credits() (+11 more)

### Community 25 - "parameters"
Cohesion: 0.30
Nodes (23): parameters, parameters, parameters, parameters, bagging_fraction, bagging_freq, bagging_seed, data_random_seed (+15 more)

### Community 26 - "train_models.py"
Cohesion: 0.21
Nodes (17): fit_historical_grade_model(), original_validation(), learn_category_levels(), prepare_model_matrix(), calibration_table(), classification_metrics(), _json_default(), _lightgbm() (+9 more)

### Community 27 - "previous_course_status_training.py"
Cohesion: 0.17
Nodes (11): _input_sha256(), learn_augmented_levels(), load_variant(), prepare_augmented_folds(), prepare_augmented_matrix(), train_all_variants(), train_augmented_one(), tune_augmented_model() (+3 more)

### Community 28 - "تحليل وتجربة `attempt_number` المعزولة"
Cohesion: 0.10
Nodes (20): A. Current semantics, B. Distribution, C. Outcome relationship, D. Experiment setup, Distribution shift, E. Overall model results, F. Repeat-only results, Fail calibration (+12 more)

### Community 29 - "GradeScale"
Cohesion: 0.17
Nodes (10): Constraints and review focus, Official Recommendation V2 Implementation Plan, Tasks, descriptive_analysis(), distribution(), evaluate_predictions(), save_table(), subsets() (+2 more)

### Community 30 - "manifest.json"
Cohesion: 0.10
Nodes (19): dataset_version, clip, feature_engineering_version, clip, expected_points_method, grade_scale, grade_scale_sha256, grade_scale_version (+11 more)

### Community 31 - "fail"
Cohesion: 0.11
Nodes (20): objective, path, sha256, target, target_definition, objective, path, sha256 (+12 more)

### Community 32 - "Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب"
Cohesion: 0.10
Nodes (20): 10. تجربة الاختصاص وتوقع النقاط, 11. الاختبارات, 12. ترتيب إعادة البناء, 1. مصادر البيانات, 2. التنظيف والدمج, 3. Roster الحمل الفصلي, 4. التقسيم الزمني, 5. هندسة الخصائص الزمنية (+12 more)

### Community 33 - "تحليل أخطاء مودل العلامة والخطة حسب السنة والاختصاص"
Cohesion: 0.10
Nodes (19): 1. التحليل حسب السنة الدراسية, 2. التحليل حسب الاختصاص, 3. الخصائص الأكثر تأثيرًا, 4. لماذا خطأ توقع العلامة مرتفع نسبيًا؟, 5. إجراءات التحسين المقترحة بالترتيب, أهم الخصائص المفردة, أولوية 1 — تقييم مرشح Expected Points على خطط بديلة, أولوية 2 — مودلات Quantile وعدم اليقين (+11 more)

### Community 34 - "الخطة النهائية: 33 → 50 → 47 مع Balance كهدف فعلي"
Cohesion: 0.11
Nodes (18): 1. القرارات الثابتة والواجهات, 2. المدخلات والتاريخ والقيود, 3. تنفيذ التوقعات وBalance والترتيب, 4. التحقق وبوابتا اعتماد الاستراتيجيات, 5. ترتيب العمل وBenchmark والتسليم, 6. توثيق Baseline لهذه اللقطة, Balance components, Benchmark المعتمد (+10 more)

### Community 35 - "test_train_models.py"
Cohesion: 0.12
Nodes (12): feature_importance(), FakeImportanceModel, temporal_frame(), test_calibration_table_returns_only_populated_bins_with_correct_aggregates(), test_classification_metrics_clips_endpoint_probabilities(), test_classification_metrics_known_ranking_and_probabilities(), test_feature_importance_returns_top_25_without_renormalizing(), test_feature_importance_sorts_descending_and_normalizes_gain() (+4 more)

### Community 36 - "تحليل تشخيصي لأعمدة طلب التوصية"
Cohesion: 0.11
Nodes (18): 10. أسئلة تتطلب تأكيد backend/support, 1. الطالب والفصل المستخدمان للتحقيق, 2. صفوف الطلب الخام للطالب والفصل, 3. الجداول والمصادر التي فُحصت, 4. ربط الأعمدة واحدًا واحدًا, 5. أدلة المطابقة والتكرار على مستوى الصفوف, 6. الأعمدة الغامضة, 7. أعمدة التسرب المحتملة (+10 more)

### Community 37 - "تقرير أخطاء أفضل مودل Expected Points"
Cohesion: 0.11
Nodes (18): 1. تعريف الأخطاء, 2. الخطأ العام على تسجيلات المواد, 3. النتائج حسب فصل 2025, 4. الخطأ حسب Course, 5. الخطأ حسب Degree, 6. خطأ الخطط, 7. الاستنتاج, 8. مصادر الأرقام (+10 more)

### Community 38 - "test_v2_pipeline.py"
Cohesion: 0.14
Nodes (9): clean_degree_course(), main(), raw_degree_courses(), test_clean_degree_course_normalizes_contract_and_stable_order(), test_clean_degree_course_rejects_missing_required_columns(), test_main_writes_the_clean_degree_course_artifact(), valid_course_frame(), valid_course_row() (+1 more)

### Community 39 - "test_model_artifact_isolation.py"
Cohesion: 0.17
Nodes (9): isolation_violations(), test_artifact_namespaces(), test_dependency_checker_allows_official_and_local_imports(), test_dependency_checker_detects_forbidden_imports_and_paths(), test_official_packages_do_not_depend_on_experiments(), test_xml_recommendation_exception_does_not_allow_direct_experiment_imports(), _import_targets(), test_production_packages_do_not_import_project_runner() (+1 more)

### Community 40 - "clean_student_status"
Cohesion: 0.31
Nodes (16): clean_student_status(), main(), make_status_row(), test_add_enrollment_features_tracks_only_observed_history(), test_business_filters_remove_only_the_matching_row(), test_clean_student_status_preserves_columns_and_normalizes_ids_and_text(), test_enrolled_optional_semester_updates_last_enrolled_gpa(), test_every_excluded_permanent_status_id_is_filtered() (+8 more)

### Community 41 - "course_only_training.py"
Cohesion: 0.18
Nodes (8): prepare_course_matrix(), load_experiment(), prepare_course_folds(), train_experiment(), training_signature(), load_category_levels(), save_category_levels(), FeatureContractResponsibilitiesTests

### Community 42 - "test_experiments_v2_io.py"
Cohesion: 0.14
Nodes (7): assert_preserved(), feature_rows(), isolated_io(), synthetic_train(), SyntheticModel, test_coordinator_uses_v2_baseline_cache_outputs_and_metadata_candidate(), test_missing_v2_input_fails_without_using_v1()

### Community 43 - "explain_recommendation.py"
Cohesion: 0.26
Nodes (13): check(), collect_term(), capture(), course_math(), main(), read_export(), records(), save() (+5 more)

### Community 44 - "fail"
Cohesion: 0.12
Nodes (17): brier, calibration_error_10_bins, log_loss, pr_auc, roc_auc, experimental_test_metrics, feature_importance, final_boost_rounds (+9 more)

### Community 45 - "metadata"
Cohesion: 0.12
Nodes (17): created_at_utc, dataset_version, experiment, feature_engineering_version, holdout_history_protocol, model_family, seed, targets (+9 more)

### Community 46 - "previous_course_status_evaluation.py"
Cohesion: 0.18
Nodes (9): write_json(), _check_saved_baseline(), evaluate_holdout(), _paired_metrics(), _predict(), _retake_sample(), status_slices(), _load_tables() (+1 more)

### Community 47 - "clean_student_status.py"
Cohesion: 0.24
Nodes (8): count_regular_semesters_between(), is_regular_semester(), add_enrollment_features(), test_count_regular_semesters_between_rejects_invalid_part_id(), test_is_regular_semester(), test_is_regular_semester_rejects_invalid_part_id(), test_regular_semesters_between(), enrollment_features()

### Community 48 - "experiment_io.py"
Cohesion: 0.17
Nodes (8): build_metadata(), experiment_signature(), _json_default(), save_results(), test_metadata_retains_protocol_and_artifact_contract(), test_save_results_preserves_parquet_and_json_outputs(), test_signature_hashes_current_dependencies_deterministically(), test_experiment_saves_preserve_official_v2_and_legacy_hashes()

### Community 49 - "pandas"
Cohesion: 0.30
Nodes (11): code(), context_math(), fmt(), formula(), group_name(), main(), p(), sections() (+3 more)

### Community 50 - "grade"
Cohesion: 0.13
Nodes (15): mae, rmse, within_10, within_5, experimental_test_metrics, feature_importance, final_boost_rounds, official_cv_mean_saved (+7 more)

### Community 51 - "متابعة بناء Academic Advisor"
Cohesion: 0.13
Nodes (15): التشغيل المستمر, التكامل, الحالة الحالية, المتابعة السريعة من الطرفية, المرحلة 1 — تجهيز البيانات, المرحلة 2 — التقسيم والحمل الفصلي, المرحلة 3 — هندسة الخصائص, المرحلة 4 — التدريب (+7 more)

### Community 52 - "merge"
Cohesion: 0.13
Nodes (15): merge, course_coverage_pct, course_rows_after, course_rows_before, course_rows_matched, course_rows_unmatched, course_students_after, course_students_before (+7 more)

### Community 53 - "Recommendation Trace — Student 29485.111"
Cohesion: 0.13
Nodes (15): 11. Model Matrix and Feature Contract, 12. Grade Prediction, 14. Fail Prediction, 15. Plan Generation, 16. Plan Scoring, 17. Plan Ranking, 19. Important Intermediate Tables, 20. Leakage and Contract Checks (+7 more)

### Community 54 - "clean_student_diploma"
Cohesion: 0.23
Nodes (9): clean_student_diploma(), main(), merge_student_course_with_diploma(), academic_info(), test_clean_student_diploma_groups_rare_types_and_fills_gpa(), test_clean_student_diploma_rejects_broken_input_contract(), test_main_writes_clean_and_merged_diploma_artifacts(), test_merge_student_course_with_diploma_preserves_unmatched_courses() (+1 more)

### Community 55 - "Readme.md"
Cohesion: 0.23
Nodes (3): Experiment boundary, Model Artifact Policy, Preserved history and migration status

### Community 56 - "modeling.py"
Cohesion: 0.34
Nodes (11): اليوم الثالث: آخر تعديلين والترشيح — حوالي 4.5 ساعات, aggregate_plans(), course_predictions(), evaluate_selected_holdout(), evaluate_variant(), feature_columns(), fit_experiment_model(), fit_weights() (+3 more)

### Community 57 - "provenance"
Cohesion: 0.19
Nodes (14): dataset_version_basis, metadata_path, metadata_sha256, source_artifact_sha256_at_promotion, source_evidence_sha256_at_promotion, target_basis, models/experiments/course_only_recommendation/category_levels.json, models/experiments/course_only_recommendation/fail_risk_classifier.txt (+6 more)

### Community 58 - "تدقيق مسار البيانات والمودلات والتوصية — 2026-09-14"
Cohesion: 0.14
Nodes (13): 1. ماذا حدث للطلاب الأربعة؟, 2. النتائج مرتبة بالأولوية, 3. حالة بقية مراحل المسار, 4. هل المودل الحالي مفيد؟, 5. ترتيب العمل المقترح, 6. الأدلة وإعادة الفحص, P1 — «الخطة الفعلية» في التقييم قد تكون جزءاً من التسجيل فقط, P1 — حذف تاريخ التدريب بسبب أحداث مستقبلية (+5 more)

### Community 59 - "test_build_registration_roster.py"
Cohesion: 0.29
Nodes (10): build_registration_roster(), main(), to_integer(), make_plan(), make_raw_course(), roster_inputs(), test_build_registration_roster_joins_exact_status_removes_outliers_and_keeps_plan_gaps(), test_build_registration_roster_keeps_only_registered_or_enrolled() (+2 more)

### Community 60 - "degree_points.py"
Cohesion: 0.26
Nodes (10): compare_holdout_by_degree(), load_feature_frames(), main(), run_validation(), selected_round_count(), print_summary(), degree_metrics(), select_variant() (+2 more)

### Community 61 - "test_previous_course_status_inference.py"
Cohesion: 0.21
Nodes (7): inference(), test_augmented_scoring_clips_predictions_before_grade_conversion(), test_augmented_scoring_rejects_nonfinite_predictions(), test_course_comparison_joins_by_course_identity_and_keeps_status(), test_course_comparison_rejects_mismatched_candidate_rows(), test_plan_comparison_uses_same_memberships_and_reports_rank_changes(), test_unresolved_prior_attempt_is_unknown_in_serving_rows()

### Community 62 - "Academic Advisor — Architecture Audit before PHP/Backend integration"
Cohesion: 0.15
Nodes (12): A. Executive Summary, Academic Advisor — Architecture Audit before PHP/Backend integration, B. Current Data Flow, E. Backend-Provided Fields, G. Runtime Features, K. Train/Serve Skew Risks, L. Questions for Backend Team, Leakage classification لجميع مصادر الـ 47 (+4 more)

### Community 63 - "PREVIOUS_COURSE_STATUS EXPERIMENT"
Cohesion: 0.15
Nodes (12): 33 مقابل 34, 47 مقابل 48, Holdout: المقاييس الإجمالية, Holdout حسب آخر حالة سابقة, PREVIOUS_COURSE_STATUS EXPERIMENT, التحقق والعزل, الملفات والأوامر, النطاق والمصدر (+4 more)

### Community 64 - "compute_plan_context_features"
Cohesion: 0.18
Nodes (4): 9. Feature Assembly, compute_plan_context_features(), SyntheticIntegrationTests, PlanContextTests

### Community 65 - "course_only_recommendation.py"
Cohesion: 0.21
Nodes (6): capture_protected_files(), PredictionCounter, run_comparisons(), save_case(), verify_protected_files(), main()

### Community 66 - "fail_risk_classifier"
Cohesion: 0.17
Nodes (12): all_candidates, final_boost_rounds, test_2025_calibration, test_2025_metrics, top_feature_importance, uses_class_weights, fail_risk_classifier, brier (+4 more)

### Community 67 - "input_sha256_at_promotion"
Cohesion: 0.17
Nodes (12): data/artifacts/category_levels_v2.json, data/features/temporal_test_features_v2.parquet, data/features/temporal_train_features_v2.parquet, models/fail_risk_classifier_v2.txt, models/grade_regressor_v2.txt, models/model_metadata_v2.json, src/experiments/course_only_core.py, src/experiments/course_only_training.py (+4 more)

### Community 68 - "input_sha256"
Cohesion: 0.17
Nodes (12): data/artifacts/category_levels_v2.json, data/features/temporal_test_features_v2.parquet, data/features/temporal_train_features_v2.parquet, models/fail_risk_classifier_v2.txt, models/grade_regressor_v2.txt, models/model_metadata_v2.json, src/experiments/course_only_core.py, src/experiments/course_only_training.py (+4 more)

### Community 69 - "COURSE-ONLY 33-FEATURE EXPERIMENT"
Cohesion: 0.17
Nodes (11): Batch distributions, COURSE-ONLY 33-FEATURE EXPERIMENT, Decision evidence, Direct plan-context sensitivity, Grade and Fail holdout comparisons, Isolation, provenance and validation, Official Top 3 versus experimental Top 10, Requested final summary (+3 more)

### Community 70 - "Production Contract — PHP ↔ Python Recommendation Service"
Cohesion: 0.18
Nodes (11): 10. Proposed production structure (not created), 1. Baseline and deployment direction, 2. Recommendation request contract, 3. Candidate source contract, 4. Recommendation response contract, 5. Provenance contract, 7. Production Invariants, 9. Offline Build Pipeline vs Online Serving Pipeline (+3 more)

### Community 71 - "C. 47 Feature Audit"
Cohesion: 0.25
Nodes (6): C. 47 Feature Audit, main(), enrichment_inputs(), test_main_builds_status_inner_join_and_auditable_plan_left_join(), test_main_rejects_many_to_many_enrichment_sources(), write_enrichment_inputs()

### Community 72 - "key_level"
Cohesion: 0.22
Nodes (11): key_level, key_level, both, course, course_keys, course_only, course_only_pct, status (+3 more)

### Community 73 - "تجربة الاختصاص وتوقع النقاط المباشر"
Cohesion: 0.18
Nodes (11): اعتماد المودل على تاريخ الاختصاص, السؤال, القرار المقترح, المخرجات, المقايضة على مستوى المادة, بروتوكول زمني, تجربة الاختصاص وتوقع النقاط المباشر, خصائص تاريخ الاختصاص (+3 more)

### Community 74 - "test_clean_utils.py"
Cohesion: 0.25
Nodes (9): extract_university_id(), to_float(), test_clean_column_names_normalizes_whitespace_without_mutating_input(), test_clean_id_columns_cleans_multiple_selected_columns_and_copies_input(), test_clean_id_preserves_meaningful_dots_and_normalizes_nulls(), test_extract_university_id_extracts_after_final_dot_without_inventing_validation(), test_numeric_converters_keep_current_invalid_value_failure(), test_to_float_converts_numeric_and_decimal_inputs_to_nullable_float64() (+1 more)

### Community 76 - "levels"
Cohesion: 0.24
Nodes (10): levels, path, sha256, diploma_type_id, grade_version_id, part_semester, plan_course_type_id, plan_requirement_type_id (+2 more)

### Community 77 - "student_status_course_comparison_metrics.json"
Cohesion: 0.20
Nodes (9): classification, course, status, dependencies, legacy_script_has_v2_imports, legacy_script_uses_v1_paths, student_course_depends_on_status_keys, student_status_depends_on_course_keys (+1 more)

### Community 78 - "student_level"
Cohesion: 0.20
Nodes (10): after_common_student_policy, rows, student_level, course, status, both, course, course_only (+2 more)

### Community 79 - "test_feature_pipeline.py"
Cohesion: 0.24
Nodes (6): Recommendation report only, Static dependency and writer audit, load_or_train_holdout(), load_cached_validation(), test_validation_cache_reuses_only_matching_signature(), ExperimentCacheTests

### Community 80 - "test_filter_common_students.py"
Cohesion: 0.33
Nodes (6): filter_common_students(), main(), test_does_not_modify_inputs_in_place(), test_keeps_all_rows_for_common_student_despite_different_parts_and_degrees(), test_keeps_only_students_present_in_both_tables(), test_stage_reads_pre_common_and_writes_filtered_v2()

### Community 81 - "repeat_withdrawal_balance.py"
Cohesion: 0.24
Nodes (4): credit_bins(), prepare_attempts(), semantic_status(), student_totals()

### Community 82 - "Repository Guidelines"
Cohesion: 0.22
Nodes (8): Build, Test, and Development Commands, Coding Style & Naming Conventions, Commit & Pull Request Guidelines, Data & Temporal Integrity, graphify, Project Structure & Module Organization, Repository Guidelines, Testing Guidelines

### Community 83 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 84 - "course_history"
Cohesion: 0.22
Nodes (9): initial_history_cutoff, smoothing_k, test_history_cutoffs, test_protocol, training_walk_forward, update_after_finalized_outcomes, course_history, 20251 (+1 more)

### Community 85 - "grade_regressor"
Cohesion: 0.22
Nodes (9): all_candidates, final_boost_rounds, test_2025_metrics, top_feature_importance, grade_regressor, mae, rmse, within_10 (+1 more)

### Community 86 - "Project State — Productization Baseline"
Cohesion: 0.22
Nodes (9): A. Current Production Baseline, B. Current Recommendation Rules, C. Current Ranking, D. Validated Academic Rules, E. University Term Policy, F. EXPERIMENTAL — NOT PRODUCTION, G. Production Boundary, H. Current Workstreams (+1 more)

### Community 87 - "course_only_report.py"
Cohesion: 0.33
Nodes (4): build_report(), plan_table(), read_json(), table()

### Community 88 - "توثيق Baseline قبل تنفيذ Recommendation Two-stage"
Cohesion: 0.25
Nodes (7): Full pytest, الفشل القديم capacity_63, توثيق Baseline قبل تنفيذ Recommendation Two-stage, سلامة البيانات والـArtifacts, مراجعة Git index قبل Commit, نطاق Commit والاستثناءات المحلية, نطاق هذه اللقطة

### Community 89 - "Model Artifact Isolation Audit Implementation Plan"
Cohesion: 0.25
Nodes (7): Execution notes, Global Constraints, Model Artifact Isolation Audit Implementation Plan, Review Focus, Task 1: Inventory and protections, Task 2: Regression tests, Task 3: Policy and audit report

### Community 90 - "تشغيل توصيات الخطط محلياً"
Cohesion: 0.25
Nodes (8): 1. قائمة المواد, 2. التشغيل من مجلد المشروع, 3. المودل والنتائج, 4. الاختبارات وقياس الأداء, 5. معادلة الترتيب وحدود الإعادات, 6. نسخ Frozen Historical State, 7. إعادة تشغيل المثال المحلي السابق, تشغيل توصيات الخطط محلياً

### Community 91 - "selected_candidate"
Cohesion: 0.57
Nodes (8): selected_candidate, selected_candidate, selected_candidate, selected_candidate, candidate, folds, mean_best_iteration, mean_primary_metric

### Community 92 - "feature_contract"
Cohesion: 0.50
Nodes (8): categorical_features, feature_count, model_features, numeric_features, removed_features, feature_contract, feature_contract, feature_contract

### Community 93 - "J. Candidate & Requirement Policy Contract"
Cohesion: 0.25
Nodes (8): Catalog ownership, Current / Projected GPA, J. Candidate & Requirement Policy Contract, Requested credit hours والمواد ذات الساعات الصفرية, الحد الأدنى للمرشحين, الخطة الكاملة والمواد المسجلة مسبقًا, المتطلبات والساعات الاختيارية, جرد السياسات

### Community 94 - "inner_merge"
Cohesion: 0.25
Nodes (8): inner_merge, course_rows_after, course_rows_before, dropped_percentage, dropped_rows, students_after, students_before, students_completely_lost

### Community 95 - "Model Artifact Isolation Audit"
Cohesion: 0.25
Nodes (8): Auxiliary state, excluded from trained-model classification, Concise diff, Experiment results and cache, Final status, Inventory, Model Artifact Isolation Audit, Official baseline and provenance limitations, Verification

### Community 96 - "التحقق من التوصية بالتراكمي المتوقع والتاريخ المجمد"
Cohesion: 0.25
Nodes (7): إعادة التشغيل على القوائم المحفوظة, التحقق الفعلي من النسختين, التحقق من التوصية بالتراكمي المتوقع والتاريخ المجمد, المعادلة والترتيب, الملفات والسبب المعماري, حدود الحساب وإعادة الإنتاج, نتائج الاختبارات

### Community 97 - "summary.md"
Cohesion: 0.25
Nodes (7): Actual availability-conditioned behavior, Data quality and outliers, Limitations, Most common plan mixes, Reproduction and preserved artifacts, Status meaning and source evidence, Suggested candidate balance

### Community 98 - "ابدأ من هنا — Academic Advisor"
Cohesion: 0.25
Nodes (8): أين أجد نتيجة كل نسخة من التجربة؟, أين وصل المشروع الآن؟, ابدأ من هنا — Academic Advisor, المسار الرسمي للتدريب, سجل التجارب ونتائجها, قاعدة إضافة تجربة جديدة, كيف أتنقل في المشروع؟, مسار تجربة Expected Points والاختصاص

### Community 99 - "Official Recommendation V2 migration — 2026-09-27"
Cohesion: 0.29
Nodes (7): Artifact hashes and preservation, Files changed and concise diff, New immutable histories, Official Recommendation V2 migration — 2026-09-27, Official serving contract, V2 local inputs and temporal integrity, Validation

### Community 100 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 101 - "Isolated attempt-number experiment plan"
Cohesion: 0.33
Nodes (5): Constraints and decisions fixed before fitting, Execution rulings, Isolated attempt-number experiment plan, Review focus, Tasks

### Community 102 - "rebuild_common_students_v2.py"
Cohesion: 0.47
Nodes (3): compare(), digest(), main()

### Community 104 - "student_level"
Cohesion: 0.33
Nodes (6): student_level, both_students, course_only_students, course_students, status_only_students, status_students

### Community 105 - "مراجعة خصائص المودل — 2026-09-10"
Cohesion: 0.33
Nodes (5): التحقق, بقية الحسابات التي روجعت, حالة إعادة الإنتاج, ما تغيّر, مراجعة خصائص المودل — 2026-09-10

### Community 106 - "جدول تتبع تحسينات المودل"
Cohesion: 0.33
Nodes (6): 1. جميع النسخ المجربة, 2. الأثر المعزول لكل إضافة, 3. تحقق 2025 للنسخة الفائزة فقط, 4. القرار الحالي, جدول تتبع تحسينات المودل, حسب فصل 2025

### Community 108 - "artifacts"
Cohesion: 0.40
Nodes (5): category_levels, fail_model, grade_model, model_metadata, artifacts

### Community 109 - "training_weight"
Cohesion: 0.40
Nodes (5): training_weight, applied_only_during_fit, before_2022, fit_only, from_2022

### Community 110 - "F. Precomputed Serving State"
Cohesion: 0.40
Nodes (5): attempt_number: القرار المدعوم بالأدلة, F. Precomputed Serving State, GPA history: المتشابهات ليست مترادفات, observed_gap_semesters, Student totals و Leakage

### Community 111 - "Data / Features V2 migration report — 2026-09-21"
Cohesion: 0.60
Nodes (4): Data / Features V2 migration report — 2026-09-21, build_temporal_split(), main(), summarize_split()

### Community 112 - "I. Semester Update Lifecycle"
Cohesion: 0.40
Nodes (5): Gaps يجب حلها قبل تغليف التدريب الحالي, I. Semester Update Lifecycle, التوصية أثناء 20261 غير المكتمل, بعد إغلاق الفصل أو وصول تصحيح, صلاحيات الأدمن والـ Jobs المقترحة

### Community 113 - "H. Frozen History Analysis"
Cohesion: 0.40
Nodes (4): H. Frozen History Analysis, التحقق، اكتمال المصدر والتصحيحات, المدخلات والمجاميع المخزنة, الملفات الموجودة فعليًا وحدودها

### Community 114 - "تحقق مسار توصيات الخطط المحلي — 2026-09-12"
Cohesion: 0.40
Nodes (4): إعادة التحقق, تحقق الوظائف, تحقق مسار توصيات الخطط المحلي — 2026-09-12, قياس الأداء السابق

### Community 115 - "18. Top 3 Output"
Cohesion: 0.40
Nodes (5): 18. Top 3 Output, Rank 1 — plan 797, Rank 2 — plan 2173, Rank 3 — plan 1080, Schema الفعلي

### Community 116 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 117 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 118 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 119 - "artifact_sha256"
Cohesion: 0.50
Nodes (4): category_levels.json, fail_risk_classifier.txt, grade_regressor.txt, artifact_sha256

### Community 120 - "D. Raw Data Sources"
Cohesion: 0.50
Nodes (4): D. Raw Data Sources, Schemas الفعلية كاملة, أمثلة Provenance من Raw إلى Model, ما أثبتته القيم الفعلية

## Knowledge Gaps
- **582 isolated node(s):** `dataset_version`, `feature_engineering_version`, `grade_scale_sha256`, `grade_scale_version`, `path` (+577 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 957 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GradeScale` connect `GradeScale` to `13. GradeScale Conversion`, `analyze_model_errors.py`, `two_stage_artifacts.py`, `train_models.py`, `test_recommendation_v2.py`, `ابدأ من هنا — Academic Advisor`, `test_model_artifact_isolation.py`, `json`, `experiment_io.py`, `تشغيل توصيات الخطط محلياً`, `degree_points.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `AcademicPlanRecommender` connect `engine.py` to `Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب`, `course_only_recommendation.py`, `paths.py`, `test_recommendation_v2.py`, `Production Contract — PHP ↔ Python Recommendation Service`, `pathlib`, `explain_recommendation.py`, `evaluation/evaluate_xml_recommendations.py`, `previous_course_status_inference.py`, `numpy`, `pandas`, `modeling.py`, `degree_points.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `normalize_candidates()` connect `evaluation/evaluate_xml_recommendations.py` to `engine.py`, `Production Contract — PHP ↔ Python Recommendation Service`, `C. 47 Feature Audit`, `pathlib`, `explain_recommendation.py`, `ImportTests`, `numpy`, `pandas`, `clean_id_columns`, `تحليل وتجربة `attempt_number` المعزولة`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **What connects `dataset_version`, `feature_engineering_version`, `grade_scale_sha256` to the rest of the system?**
  _582 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `paths.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06597819850831899 - nodes in this community are weakly interconnected._
- **Should `analyze_model_errors.py` be split into smaller, more focused modules?**
  _Cohesion score 0.050580997949419004 - nodes in this community are weakly interconnected._
- **Should `two_stage_artifacts.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05734767025089606 - nodes in this community are weakly interconnected._