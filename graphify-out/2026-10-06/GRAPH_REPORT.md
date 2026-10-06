# Graph Report - Academic_Advisor_Simple  (2026-10-06)

## Corpus Check
- 273 files · ~2,305,005 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 51 file(s) not represented in the graph (top: .csv 18, .log 14, .parquet 8)

## Summary
- 2510 nodes · 5727 edges · 160 communities (144 shown, 16 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 330 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- paths.py
- analyze_model_errors.py
- two_stage_artifacts.py
- enumerate_plan_indices
- test_recommendation_v2.py
- test_two_stage_artifacts.py
- build_frozen_history
- specialty_history.py
- test_modeling_v2_io.py
- AcademicPlanRecommender
- temporal_features.py
- test_clean_outliers.py
- validate_snapshot
- course_only_evaluation.py
- previous_course_status_experiment.py
- numpy
- json
- test_main_runner.py
- clean_column_names
- Storyboard — Recommendation V2 — Student 29485.111
- test_clean_student_course.py
- analyze_repeat_withdrawal_balance.py
- مسار مشروع Academic Advisor كاملًا
- What You Must Do When Invoked
- evaluation/evaluate_xml_recommendations.py
- parameters
- inputs.py
- previous_course_status_training.py
- test_two_stage_constraints.py
- GradeScale
- manifest.json
- fail
- Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب
- تحليل أخطاء مودل العلامة والخطة حسب السنة والاختصاص
- الخطة النهائية: 33 → 50 → 47 مع Balance كهدف فعلي
- train_models.py
- تحليل تشخيصي لأعمدة طلب التوصية
- تقرير أخطاء أفضل مودل Expected Points
- test_history_update.py
- test_model_artifact_isolation.py
- clean_student_status
- course_only_training.py
- test_experiments_v2_io.py
- prepare_model_matrix
- fail
- metadata
- engine.py
- project_status.py
- degree_points.py
- render_recommendation_explanation.py
- grade
- متابعة بناء Academic Advisor
- merge
- Recommendation Trace — Student 29485.111
- clean_student_diploma
- Readme.md
- modeling.py
- provenance
- تدقيق مسار البيانات والمودلات والتوصية — 2026-09-14
- to_float
- add_student_history_features
- test_previous_course_status_inference.py
- Academic Advisor — Architecture Audit before PHP/Backend integration
- PREVIOUS_COURSE_STATUS EXPERIMENT
- compute_plan_context_features
- 5. إجراءات التحسين المقترحة بالترتيب
- fail_risk_classifier
- input_sha256_at_promotion
- input_sha256
- COURSE-ONLY 33-FEATURE EXPERIMENT
- Production Contract — PHP ↔ Python Recommendation Service
- test_v2_paths.py
- key_level
- تجربة الاختصاص وتوقع النقاط المباشر
- clean_id_columns
- Data and features V2 structural migration
- levels
- student_status_course_comparison_metrics.json
- student_level
- ExperimentCacheTests
- test_filter_common_students.py
- read.md
- Repository Guidelines
- graphify reference: extra exports and benchmark
- course_history
- grade_regressor
- history_update.py
- test_two_stage_payloads.py
- توثيق Baseline قبل تنفيذ Recommendation Two-stage
- Model Artifact Isolation Audit Implementation Plan
- summarize_scored_plans
- selected_candidate
- feature_contract
- pandas
- inner_merge
- Model Artifact Isolation Audit
- التحقق من التوصية بالتراكمي المتوقع والتاريخ المجمد
- summary.md
- ابدأ من هنا — Academic Advisor
- Official Recommendation V2 migration — 2026-09-27
- graphify reference: query, path, explain
- Isolated attempt-number experiment plan
- rebuild_common_students_v2.py
- training_weights
- student_level
- مراجعة خصائص المودل — 2026-09-10
- جدول تتبع تحسينات المودل
- ImportTests
- artifacts
- training_weight
- attempt_number_training.py
- previous_course_status_inference.py
- test_recommendation_inputs_v2.py
- test_repeat_withdrawal_balance.py
- build_student_snapshot
- test_course_only_recommendation.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- load_frozen_history
- constraints.py
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- src/__init__.py
- extraction-spec.md
- 2026-09-27-course-only-recommendation.md
- student_status_course_comparison.md
- course_only_recommendation.py
- `Phase 6 — تنفيذ Benchmark وعرض نتائج المرحلتين والمفاضلات لاعتماد الاستراتيجيات بصورة مستقلة.`
- `Phase 2 — Payload Adapters, Matrix Helper, Classification & Constraints`
- `Phase 3 — History Delta والحفظ immutable والتحويل الذري`
- verification.md
- academic-advisor-simple
- `Phase 4 — تنفيذ مقاييس Balance وواجهة الاستراتيجيات ومرشحي التقييم المستقل لكل مرحلة.`
- `Phase 5 — ربط المرحلتين واختبارات Parity وOracle وتوليفات الاستراتيجيات والتقرير التاريخي والسياساتي.`
- `Phase 7 — تثبيت السياسات المعتمدة في Manifest وإعادة التحقق وتحديث الوثائق والرسم.`
- README.md
- `Phase 1 — Artifacts & Contracts`
- xml_2_json.py
- explain_recommendation.py
- test_xml_package.py
- test_build_student_course_enriched.py
- المسار العام لـ`Two-Stage`
- clean_degree_course
- importlib
- 11. Non-blocking Review Items
- recommendation_fixtures.py
- prediction_contract
- official_artifacts
- classify_candidate_status
- .as_of_part
- Data / Features V2 migration report — 2026-09-21
- 5. Which Frozen History Was Selected and Why
- شرح تنفيذ `Two-Stage Recommendation`
- analyze_course_plan_changes.py
- PredictionCounter

## God Nodes (most connected - your core abstractions)
1. `prepare_model_matrix()` - 48 edges
2. `file_sha256()` - 45 edges
3. `load_frozen_history()` - 40 edges
4. `GradeScale` - 33 edges
5. `AcademicPlanRecommender` - 33 edges
6. `clean_id_columns()` - 31 edges
7. `require_current_features()` - 31 edges
8. `enumerate_plan_indices()` - 31 edges
9. `clean_student_course()` - 30 edges
10. `clean_column_names()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `attempt_number: القرار المدعوم بالأدلة` --references--> `clean_student_course()`  [INFERRED]
  reports/..md → src/data/clean_student_course.py
- ``src/experiments/course_only_core.py` و`src/recommendation/__init__.py`` --references--> `prepare_course_matrix()`  [INFERRED]
  plan_explanation/PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md → src/experiments/course_only_core.py
- `2. قبل → بعد` --references--> `prepare_model_matrix()`  [INFERRED]
  plan_explanation/PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md → src/features/feature_contract.py
- ``src/features/feature_contract.py`` --references--> `prepare_model_matrix()`  [INFERRED]
  plan_explanation/PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md → src/features/feature_contract.py
- `11. Model Matrix and Feature Contract` --references--> `prepare_model_matrix()`  [INFERRED]
  reports/recommendation_student_29485_111_trace.md → src/features/feature_contract.py

## Import Cycles
- None detected.

## Communities (160 total, 16 thin omitted)

### Community 0 - "paths.py"
Cohesion: 0.24
Nodes (13): main(), file_sha256(), previous_academic_part(), save_frozen_history(), save_frozen_history_atomic(), validate_history_selection(), verify_legacy_course_history(), save_course_history_state() (+5 more)

### Community 1 - "analyze_model_errors.py"
Cohesion: 0.05
Nodes (52): GPA للخطط المسجلة الفعلية, attach_analysis_columns(), build_course_segments(), build_degree_analysis(), build_plan_frame(), build_plan_segments(), build_shap_importance(), build_year_analysis() (+44 more)

### Community 2 - "two_stage_artifacts.py"
Cohesion: 0.19
Nodes (11): `src/recommendation/two_stage_artifacts.py`, 10. المشاكل أو القيود المعروفة, artifact_relative_paths(), _is_sha256(), load_model_pair(), ModelPair, stage_feature_contract(), validate_archived_provenance() (+3 more)

### Community 3 - "enumerate_plan_indices"
Cohesion: 0.17
Nodes (4): enumerate_plan_indices(), visit(), resolve_credit_bounds(), EnumerationTests

### Community 4 - "test_recommendation_v2.py"
Cohesion: 0.19
Nodes (16): synthetic_candidates(), synthetic_engine(), synthetic_snapshot(), test_complete_comparison_preserves_same_request_scores_and_official_rescoring(), test_benchmark_adapter_uses_v2_inputs_with_a_tiny_synthetic_request(), test_default_top_three_returns_every_available_plan_when_fewer_exist(), test_exact_upper_bound_no_fallback_result_metadata(), test_importing_public_api_does_not_load_models() (+8 more)

### Community 5 - "test_two_stage_artifacts.py"
Cohesion: 0.11
Nodes (37): `tests/test_two_stage_artifacts.py`, artifact_root(), digest(), expected_contract(), FakeBooster, load(), mutate_manifest(), promote() (+29 more)

### Community 6 - "build_frozen_history"
Cohesion: 0.09
Nodes (16): Final output shape: Frozen History, 10. Blockers, 12. Final Decision, 1. Executive Result, 2. Pipeline Map, 3. Artifact Inventory, 5. Temporal Integrity, 7. Data Integrity (+8 more)

### Community 7 - "specialty_history.py"
Cohesion: 0.06
Nodes (38): 10. Specialty-History Support Analysis, 11. Course-Level Accuracy, 12. Bias Analysis, 13. Tail / Extreme Error Analysis, 14. Direct-Points Experiments, 15. Credit-Weighting Experiments, 16. Degree ID vs Degree History, 17. Robustness / Bootstrap (+30 more)

### Community 8 - "test_modeling_v2_io.py"
Cohesion: 0.12
Nodes (7): feature_rows(), isolated_io(), SyntheticModel, test_main_reads_v2_and_writes_only_v2_with_correct_metadata(), synthetic_fit(), test_missing_v2_input_fails_without_reading_v1_or_writing_models(), test_modeling_io_constants_resolve_to_isolated_v2_files()

### Community 9 - "AcademicPlanRecommender"
Cohesion: 0.15
Nodes (10): `src/recommendation/benchmark.py` — موجود مسبقًا, 20. Leakage and Contract Checks, طريقة الرصد وحدودها, benchmark(), main(), peak_memory_mib(), AcademicPlanRecommender, main() (+2 more)

### Community 10 - "temporal_features.py"
Cohesion: 0.18
Nodes (11): Frozen History, 4. أهم الملفات بالتفصيل المختصر, اليوم الأول: كيف تُبنى الخصائص — حوالي 4.5 ساعات, 6. Leakage Audit, build_history_keys(), build_temporal_course_history(), CourseHistoryState, _joined_key() (+3 more)

### Community 11 - "test_clean_outliers.py"
Cohesion: 0.08
Nodes (34): Appendix: 62-column outlier-filtered output inventory, `build_registration_roster.py`, `build_student_course_enriched.py`, `build_temporal_features.py`, `build_temporal_split.py`, `clean_degree_course.py`, `clean_outliers.py`, `clean_student_course.py` (+26 more)

### Community 12 - "validate_snapshot"
Cohesion: 0.15
Nodes (3): validate_snapshot(), SyntheticIntegrationTests, PlanPreservationTests

### Community 13 - "course_only_evaluation.py"
Cohesion: 0.14
Nodes (12): compare_course_sets(), distribution(), optimize_exact_credits(), plan_context_sensitivity(), compare_case(), official_plan_lookup(), run_comparisons(), save_case() (+4 more)

### Community 14 - "previous_course_status_experiment.py"
Cohesion: 0.11
Nodes (20): augment_feature_frame(), build_experimental_datasets(), build_status_history(), _distribution(), _keys(), previous_status_for_targets(), main(), _protected_paths() (+12 more)

### Community 15 - "numpy"
Cohesion: 0.16
Nodes (15): main(), save_provenance(), source_signature(), run_recommendations(), select_cases(), descriptive_analysis(), distribution(), evaluate_predictions() (+7 more)

### Community 16 - "json"
Cohesion: 0.08
Nodes (5): save_json(), show(), build_report(), table(), display()

### Community 17 - "test_main_runner.py"
Cohesion: 0.10
Nodes (17): _list_steps(), main(), _run_steps(), _select_steps(), _show_version_boundary(), Step, _record_processes(), test_all_dry_run_shows_v2_commands_without_execution() (+9 more)

### Community 18 - "clean_column_names"
Cohesion: 0.12
Nodes (11): audit_policy(), compare_tables(), main(), verify_policy_only(), compare(), describe(), main(), original_cleaner() (+3 more)

### Community 19 - "Storyboard — Recommendation V2 — Student 29485.111"
Cohesion: 0.07
Nodes (26): Delivery and continuity checks, Editable layer inventory, Evidence lock for the edit, Production preparation for Higgsfield / native compositor, Reusable animated motifs, Scene 10 — من قائمة إلى خطط, Scene 11 — سياق الخطة والمواد الأخرى, Scene 12 — 47 خاصية ومصفوفة مشتركة (+18 more)

### Community 20 - "test_clean_student_course.py"
Cohesion: 0.07
Nodes (46): A. Current semantics, B. Distribution, C. Outcome relationship, D. Experiment setup, Distribution shift, E. Overall model results, F. Repeat-only results, Fail calibration (+38 more)

### Community 21 - "analyze_repeat_withdrawal_balance.py"
Cohesion: 0.10
Nodes (23): finish_status_inventory(), grade_range_disagreements(), graph_navigation(), main(), nonstandard_history_sensitivity(), protected_manifest(), run(), sha256() (+15 more)

### Community 22 - "مسار مشروع Academic Advisor كاملًا"
Cohesion: 0.08
Nodes (26): 0. تعريف المسارات المركزي, 10. هندسة الخصائص الزمنية, 11. عقد الخصائص الرسمي, 12. التدريب الرسمي, 13. تقييم GPA للخطة الفعلية, 14. تحليل الأخطاء, 15. تجربة الاختصاص وExpected Points, 16. محرك ترشيح الخطط الحالي (+18 more)

### Community 23 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 24 - "evaluation/evaluate_xml_recommendations.py"
Cohesion: 0.20
Nodes (13): actual_metrics(), course_overlap(), course_text(), json_value(), main(), markdown_number(), observed_plan_estimate(), parse_args() (+5 more)

### Community 25 - "parameters"
Cohesion: 0.30
Nodes (23): parameters, parameters, parameters, parameters, bagging_fraction, bagging_freq, bagging_seed, data_random_seed (+15 more)

### Community 26 - "inputs.py"
Cohesion: 0.26
Nodes (11): `src/recommendation/inputs.py`, _explicitly_ineligible(), normalize_candidate_payloads(), normalize_request_payload(), normalize_student_payload(), _payload_id(), _payload_number(), _payload_part() (+3 more)

### Community 27 - "previous_course_status_training.py"
Cohesion: 0.17
Nodes (11): _input_sha256(), learn_augmented_levels(), load_variant(), prepare_augmented_folds(), prepare_augmented_matrix(), train_all_variants(), train_augmented_one(), tune_augmented_model() (+3 more)

### Community 28 - "test_two_stage_constraints.py"
Cohesion: 0.19
Nodes (23): official_run(), enumerate_feasible_plan_indices(), candidates(), policies(), request(), test_constraints_match_independent_exhaustive_oracle_and_preserve_candidates(), test_duplicate_normalized_requirement_ids_reject_even_when_values_match(), test_empty_candidate_set_has_no_feasible_plan() (+15 more)

### Community 29 - "GradeScale"
Cohesion: 0.22
Nodes (6): Constraints and review focus, Official Recommendation V2 Implementation Plan, Tasks, GradeScale, load_manifest_assets(), GradeScaleTests

### Community 30 - "manifest.json"
Cohesion: 0.15
Nodes (12): dataset_version, feature_engineering_version, grade_scale, grade_scale_sha256, grade_scale_version, path, manifest_version, ranking_approval (+4 more)

### Community 31 - "fail"
Cohesion: 0.11
Nodes (19): objective, path, sha256, target, target_definition, objective, path, sha256 (+11 more)

### Community 32 - "Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب"
Cohesion: 0.10
Nodes (20): 10. تجربة الاختصاص وتوقع النقاط, 11. الاختبارات, 12. ترتيب إعادة البناء, 1. مصادر البيانات, 2. التنظيف والدمج, 3. Roster الحمل الفصلي, 4. التقسيم الزمني, 5. هندسة الخصائص الزمنية (+12 more)

### Community 33 - "تحليل أخطاء مودل العلامة والخطة حسب السنة والاختصاص"
Cohesion: 0.15
Nodes (12): 1. التحليل حسب السنة الدراسية, 2. التحليل حسب الاختصاص, 3. الخصائص الأكثر تأثيرًا, 4. لماذا خطأ توقع العلامة مرتفع نسبيًا؟, أهم الخصائص المفردة, اختصاصات مستقرة نسبيًا, الاختصاصات الأضعف ذات العينة الكافية, التأثير حسب عائلة الخصائص (+4 more)

### Community 34 - "الخطة النهائية: 33 → 50 → 47 مع Balance كهدف فعلي"
Cohesion: 0.11
Nodes (18): 1. القرارات الثابتة والواجهات, 2. المدخلات والتاريخ والقيود, 3. تنفيذ التوقعات وBalance والترتيب, 4. التحقق وبوابتا اعتماد الاستراتيجيات, 5. ترتيب العمل وBenchmark والتسليم, 6. توثيق Baseline لهذه اللقطة, Balance components, Benchmark المعتمد (+10 more)

### Community 35 - "train_models.py"
Cohesion: 0.10
Nodes (26): fit_historical_grade_model(), original_validation(), calibration_table(), classification_metrics(), feature_importance(), _json_default(), _lightgbm(), main() (+18 more)

### Community 36 - "تحليل تشخيصي لأعمدة طلب التوصية"
Cohesion: 0.11
Nodes (18): 10. أسئلة تتطلب تأكيد backend/support, 1. الطالب والفصل المستخدمان للتحقيق, 2. صفوف الطلب الخام للطالب والفصل, 3. الجداول والمصادر التي فُحصت, 4. ربط الأعمدة واحدًا واحدًا, 5. أدلة المطابقة والتكرار على مستوى الصفوف, 6. الأعمدة الغامضة, 7. أعمدة التسرب المحتملة (+10 more)

### Community 37 - "تقرير أخطاء أفضل مودل Expected Points"
Cohesion: 0.11
Nodes (18): 1. تعريف الأخطاء, 2. الخطأ العام على تسجيلات المواد, 3. النتائج حسب فصل 2025, 4. الخطأ حسب Course, 5. الخطأ حسب Degree, 6. خطأ الخطط, 7. الاستنتاج, 8. مصادر الأرقام (+10 more)

### Community 38 - "test_history_update.py"
Cohesion: 0.13
Nodes (30): api(), delta(), hashes(), save_initial(), targets(), test_aggregate_addition_preserves_weighted_prefix_and_matches_raw_oracle(), test_bad_lineage_is_not_selected_on_restart(), test_cleanup_failure_after_publication_does_not_report_failed_update() (+22 more)

### Community 39 - "test_model_artifact_isolation.py"
Cohesion: 0.33
Nodes (6): isolation_violations(), test_artifact_namespaces(), test_dependency_checker_allows_official_and_local_imports(), test_dependency_checker_detects_forbidden_imports_and_paths(), test_official_packages_do_not_depend_on_experiments(), test_xml_recommendation_exception_does_not_allow_direct_experiment_imports()

### Community 40 - "clean_student_status"
Cohesion: 0.11
Nodes (27): C. 47 Feature Audit, count_regular_semesters_between(), is_regular_semester(), add_enrollment_features(), clean_student_status(), main(), test_count_regular_semesters_between_rejects_invalid_part_id(), test_is_regular_semester() (+19 more)

### Community 41 - "course_only_training.py"
Cohesion: 0.14
Nodes (14): prepare_course_matrix(), load_experiment(), prepare_course_folds(), train_experiment(), training_signature(), _check_saved_baseline(), evaluate_holdout(), _paired_metrics() (+6 more)

### Community 42 - "test_experiments_v2_io.py"
Cohesion: 0.13
Nodes (7): assert_preserved(), feature_rows(), isolated_io(), synthetic_train(), SyntheticModel, test_coordinator_uses_v2_baseline_cache_outputs_and_metadata_candidate(), test_missing_v2_input_fails_without_using_v1()

### Community 43 - "prepare_model_matrix"
Cohesion: 0.22
Nodes (12): Implementation Progress, Phase 1 — Artifacts & Contracts, Phase 2 — Payload Adapters, Matrix Helper, Classification & Constraints, prepare_model_matrix(), _legacy_47_matrix(), _matrix_inputs(), test_default_matrix_matches_legacy_47_exactly_without_mutating_inputs(), test_explicit_feature_order_coerces_only_the_requested_columns() (+4 more)

### Community 44 - "fail"
Cohesion: 0.12
Nodes (17): brier, calibration_error_10_bins, log_loss, pr_auc, roc_auc, experimental_test_metrics, feature_importance, final_boost_rounds (+9 more)

### Community 45 - "metadata"
Cohesion: 0.10
Nodes (21): category_levels.json, fail_risk_classifier.txt, grade_regressor.txt, artifact_sha256, created_at_utc, dataset_version, experiment, feature_engineering_version (+13 more)

### Community 46 - "engine.py"
Cohesion: 0.14
Nodes (7): 8. Feature Contract, require_current_features(), validate_history_pair(), load_recommendation_artifacts(), model_training_provenance(), FeaturePipelineTests, build()

### Community 47 - "project_status.py"
Cohesion: 0.27
Nodes (5): main(), print_model_metrics(), ProjectStage, relative(), test_stage_paths_order_and_version_boundary()

### Community 48 - "degree_points.py"
Cohesion: 0.11
Nodes (18): compare_holdout_by_degree(), load_feature_frames(), main(), run_validation(), selected_round_count(), build_metadata(), experiment_signature(), _json_default() (+10 more)

### Community 49 - "render_recommendation_explanation.py"
Cohesion: 0.38
Nodes (10): code(), context_math(), fmt(), formula(), group_name(), main(), p(), sections() (+2 more)

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
Cohesion: 0.05
Nodes (33): A. Current Production Baseline, B. Current Recommendation Rules, C. Current Ranking, D. Validated Academic Rules, E. University Term Policy, F. EXPERIMENTAL — NOT PRODUCTION, G. Production Boundary, H. Current Workstreams (+25 more)

### Community 54 - "clean_student_diploma"
Cohesion: 0.23
Nodes (9): clean_student_diploma(), main(), merge_student_course_with_diploma(), academic_info(), test_clean_student_diploma_groups_rare_types_and_fills_gpa(), test_clean_student_diploma_rejects_broken_input_contract(), test_main_writes_clean_and_merged_diploma_artifacts(), test_merge_student_course_with_diploma_preserves_unmatched_courses() (+1 more)

### Community 55 - "Readme.md"
Cohesion: 0.21
Nodes (3): Experiment boundary, Model Artifact Policy, Preserved history and migration status

### Community 56 - "modeling.py"
Cohesion: 0.23
Nodes (15): اليوم الثالث: آخر تعديلين والترشيح — حوالي 4.5 ساعات, Recommendation report only, Static dependency and writer audit, load_or_train_holdout(), aggregate_plans(), course_predictions(), evaluate_selected_holdout(), evaluate_variant() (+7 more)

### Community 57 - "provenance"
Cohesion: 0.19
Nodes (14): dataset_version_basis, metadata_path, metadata_sha256, source_artifact_sha256_at_promotion, source_evidence_sha256_at_promotion, target_basis, models/experiments/course_only_recommendation/category_levels.json, models/experiments/course_only_recommendation/fail_risk_classifier.txt (+6 more)

### Community 58 - "تدقيق مسار البيانات والمودلات والتوصية — 2026-09-14"
Cohesion: 0.14
Nodes (13): 1. ماذا حدث للطلاب الأربعة؟, 2. النتائج مرتبة بالأولوية, 3. حالة بقية مراحل المسار, 4. هل المودل الحالي مفيد؟, 5. ترتيب العمل المقترح, 6. الأدلة وإعادة الفحص, P1 — «الخطة الفعلية» في التقييم قد تكون جزءاً من التسجيل فقط, P1 — حذف تاريخ التدريب بسبب أحداث مستقبلية (+5 more)

### Community 59 - "to_float"
Cohesion: 0.26
Nodes (11): build_registration_roster(), main(), to_float(), make_plan(), make_raw_course(), roster_inputs(), test_build_registration_roster_joins_exact_status_removes_outliers_and_keeps_plan_gaps(), test_build_registration_roster_keeps_only_registered_or_enrolled() (+3 more)

### Community 60 - "add_student_history_features"
Cohesion: 0.54
Nodes (3): add_student_history_features(), semester_rows(), StudentHistoryTests

### Community 61 - "test_previous_course_status_inference.py"
Cohesion: 0.21
Nodes (7): inference(), test_augmented_scoring_clips_predictions_before_grade_conversion(), test_augmented_scoring_rejects_nonfinite_predictions(), test_course_comparison_joins_by_course_identity_and_keeps_status(), test_course_comparison_rejects_mismatched_candidate_rows(), test_plan_comparison_uses_same_memberships_and_reports_rank_changes(), test_unresolved_prior_attempt_is_unknown_in_serving_rows()

### Community 62 - "Academic Advisor — Architecture Audit before PHP/Backend integration"
Cohesion: 0.05
Nodes (38): A. Executive Summary, Academic Advisor — Architecture Audit before PHP/Backend integration, attempt_number: القرار المدعوم بالأدلة, B. Current Data Flow, Catalog ownership, Current / Projected GPA, D. Raw Data Sources, E. Backend-Provided Fields (+30 more)

### Community 63 - "PREVIOUS_COURSE_STATUS EXPERIMENT"
Cohesion: 0.15
Nodes (12): 33 مقابل 34, 47 مقابل 48, Holdout: المقاييس الإجمالية, Holdout حسب آخر حالة سابقة, PREVIOUS_COURSE_STATUS EXPERIMENT, التحقق والعزل, الملفات والأوامر, النطاق والمصدر (+4 more)

### Community 64 - "compute_plan_context_features"
Cohesion: 0.19
Nodes (9): 4. أهم الملفات بالتفصيل المختصر, 12. Grade Prediction, 9. Feature Assembly, attach_plan_context(), build_feature_tables(), main(), print_feature_summary(), compute_plan_context_features() (+1 more)

### Community 65 - "5. إجراءات التحسين المقترحة بالترتيب"
Cohesion: 0.29
Nodes (7): 5. إجراءات التحسين المقترحة بالترتيب, أولوية 1 — تقييم مرشح Expected Points على خطط بديلة, أولوية 2 — مودلات Quantile وعدم اليقين, أولوية 3 — معايرة زمنية واختصاصية, أولوية 4 — نتيجة تجربة الاختصاص, أولوية 5 — نتيجة مواءمة التدريب مع هدف الخطة, أولوية 6 — خصائص جديدة متاحة قبل التسجيل

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
Cohesion: 0.13
Nodes (13): 10. Proposed production structure (not created), 1. Baseline and deployment direction, 2. Recommendation request contract, 3. Candidate source contract, 4. Recommendation response contract, 6. Error contract, 7. Production Invariants, 8. Reference regression case (+5 more)

### Community 71 - "test_v2_paths.py"
Cohesion: 0.43
Nodes (4): versioned_path(), test_v2_artifacts_are_separate_from_originals(), test_versioned_path_preserves_parent_and_extension(), test_versioned_path_supports_artifact_extensions()

### Community 72 - "key_level"
Cohesion: 0.22
Nodes (11): key_level, key_level, both, course, course_keys, course_only, course_only_pct, status (+3 more)

### Community 73 - "تجربة الاختصاص وتوقع النقاط المباشر"
Cohesion: 0.18
Nodes (11): اعتماد المودل على تاريخ الاختصاص, السؤال, القرار المقترح, المخرجات, المقايضة على مستوى المادة, بروتوكول زمني, تجربة الاختصاص وتوقع النقاط المباشر, خصائص تاريخ الاختصاص (+3 more)

### Community 74 - "clean_id_columns"
Cohesion: 0.18
Nodes (12): cohort_counts(), main(), count(), main(), clean_id(), clean_id_columns(), extract_university_id(), one_id() (+4 more)

### Community 75 - "Data and features V2 structural migration"
Cohesion: 0.33
Nodes (5): Completion evidence, Data and features V2 structural migration, Evidence and rulings, Review focus, Tasks

### Community 76 - "levels"
Cohesion: 0.24
Nodes (10): levels, path, sha256, diploma_type_id, grade_version_id, part_semester, plan_course_type_id, plan_requirement_type_id (+2 more)

### Community 77 - "student_status_course_comparison_metrics.json"
Cohesion: 0.20
Nodes (9): classification, course, status, dependencies, legacy_script_has_v2_imports, legacy_script_uses_v1_paths, student_course_depends_on_status_keys, student_status_depends_on_course_keys (+1 more)

### Community 78 - "student_level"
Cohesion: 0.20
Nodes (10): after_common_student_policy, rows, student_level, course, status, both, course, course_only (+2 more)

### Community 80 - "test_filter_common_students.py"
Cohesion: 0.33
Nodes (6): filter_common_students(), main(), test_does_not_modify_inputs_in_place(), test_keeps_all_rows_for_common_student_despite_different_parts_and_degrees(), test_keeps_only_students_present_in_both_tables(), test_stage_reads_pre_common_and_writes_filtered_v2()

### Community 81 - "read.md"
Cohesion: 0.50
Nodes (3): الأولوية الحالية, اليوم الثاني: التدريب والتقييم — حوالي 4 ساعات, ملفات لا تعطيها وقتًا كبيرًا الآن

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

### Community 86 - "history_update.py"
Cohesion: 0.10
Nodes (11): apply_history_delta(), _apply_normalized_delta(), _canonical_number(), FrozenHistoryManager, HistoryDelta, HistorySnapshot, normalize_history_delta(), _number() (+3 more)

### Community 87 - "test_two_stage_payloads.py"
Cohesion: 0.25
Nodes (18): ملفات الاختبار الثلاثة, payloads(), prepare(), test_candidate_order_and_untrusted_features_do_not_change_prepared_rows(), test_conflicting_full_status_meanings_are_rejected(), test_cross_identity_or_invalid_part_is_rejected(), test_decimal_to_float_overflow_is_rejected(), test_duplicate_course_identity_after_normalization_is_rejected() (+10 more)

### Community 88 - "توثيق Baseline قبل تنفيذ Recommendation Two-stage"
Cohesion: 0.25
Nodes (7): Full pytest, الفشل القديم capacity_63, توثيق Baseline قبل تنفيذ Recommendation Two-stage, سلامة البيانات والـArtifacts, مراجعة Git index قبل Commit, نطاق Commit والاستثناءات المحلية, نطاق هذه اللقطة

### Community 89 - "Model Artifact Isolation Audit Implementation Plan"
Cohesion: 0.25
Nodes (7): Execution notes, Global Constraints, Model Artifact Isolation Audit Implementation Plan, Review Focus, Task 1: Inventory and protections, Task 2: Regression tests, Task 3: Policy and audit report

### Community 90 - "summarize_scored_plans"
Cohesion: 0.10
Nodes (16): 1. قائمة المواد, 2. التشغيل من مجلد المشروع, 3. المودل والنتائج, 4. الاختبارات وقياس الأداء, 5. معادلة الترتيب وحدود الإعادات, 7. إعادة تشغيل المثال المحلي السابق, 8. الربط اللاحق بالـAPI, تشغيل توصيات الخطط محلياً (+8 more)

### Community 91 - "selected_candidate"
Cohesion: 0.57
Nodes (8): selected_candidate, selected_candidate, selected_candidate, selected_candidate, candidate, folds, mean_best_iteration, mean_primary_metric

### Community 92 - "feature_contract"
Cohesion: 0.50
Nodes (8): categorical_features, feature_count, model_features, numeric_features, removed_features, feature_contract, feature_contract, feature_contract

### Community 94 - "inner_merge"
Cohesion: 0.25
Nodes (8): inner_merge, course_rows_after, course_rows_before, dropped_percentage, dropped_rows, students_after, students_before, students_completely_lost

### Community 95 - "Model Artifact Isolation Audit"
Cohesion: 0.25
Nodes (8): Auxiliary state, excluded from trained-model classification, Concise diff, Experiment results and cache, Final status, Inventory, Model Artifact Isolation Audit, Official baseline and provenance limitations, Verification

### Community 96 - "التحقق من التوصية بالتراكمي المتوقع والتاريخ المجمد"
Cohesion: 0.29
Nodes (6): إعادة التشغيل على القوائم المحفوظة, التحقق الفعلي من النسختين, التحقق من التوصية بالتراكمي المتوقع والتاريخ المجمد, المعادلة والترتيب, حدود الحساب وإعادة الإنتاج, نتائج الاختبارات

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
Cohesion: 0.60
Nodes (3): compare(), digest(), main()

### Community 103 - "training_weights"
Cohesion: 0.36
Nodes (3): training_weights(), test_training_weights_preserves_index_and_numeric_coercion(), test_training_weights_year_boundary()

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

### Community 110 - "attempt_number_training.py"
Cohesion: 0.14
Nodes (12): paired_cluster_interval(), row_fingerprint(), transform_matrix(), model_metrics(), run_training(), learn_category_levels(), save_category_levels(), test_cluster_bootstrap_resamples_students_and_retains_all_their_rows() (+4 more)

### Community 111 - "previous_course_status_inference.py"
Cohesion: 0.14
Nodes (12): prepare_course_rows(), score_courses_once(), experimental_run(), _attach_status(), _load_experimental_models(), pair_course_scores(), pair_plan_course_scores(), pair_plan_summaries() (+4 more)

### Community 112 - "test_recommendation_inputs_v2.py"
Cohesion: 0.15
Nodes (13): load_local_inputs(), SyntheticXmlEngine, test_local_loader_reads_only_cleaned_v2_and_preserves_history(), test_local_missing_v2_fails_without_legacy_fallback(), test_local_supplied_snapshot_reads_only_v2_catalog_and_attempts(), test_xml_missing_v2_fails_without_legacy_fallback(), test_xml_older_history_opt_in_applies_to_recommendation_and_observed_plan(), test_xml_older_history_requires_explicit_opt_in() (+5 more)

### Community 113 - "test_repeat_withdrawal_balance.py"
Cohesion: 0.16
Nodes (18): rows(), test_analysis_runner_preserves_inputs_and_rejects_existing_output(), test_available_credits_use_last_prior_not_current_credit_value(), test_conflicting_same_semester_attempts_are_rejected(), test_current_and_future_outcomes_cannot_change_previous_status(), test_decimal_and_zero_credit_courses_are_not_rounded(), test_exact_duplicates_are_reported_and_do_not_double_credits(), test_failed_repeated_and_not_repeated() (+10 more)

### Community 114 - "build_student_snapshot"
Cohesion: 0.22
Nodes (8): إعادة التحقق, تحقق النسخة النهائية, تحقق الوظائف, تحقق مسار توصيات الخطط المحلي — 2026-09-12, قياس الأداء السابق, 7. Student Snapshot Construction, build_student_snapshot(), test_snapshot_and_attempts_ignore_target_and_future_outcomes()

### Community 115 - "test_course_only_recommendation.py"
Cohesion: 0.18
Nodes (10): experiment(), scores(), test_course_matrix_does_not_need_plan_context_and_retains_unknown_categories(), test_course_rows_reject_target_or_future_training_history_and_stale_history(), test_exact_search_uses_every_candidate_and_risk_then_course_order_for_ties(), test_fractional_credit_search_and_zero_credit_optional_courses(), test_optimizer_rejects_invalid_scores(), test_scoring_predicts_each_candidate_once_and_clips_before_grade_conversion() (+2 more)

### Community 116 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 117 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 118 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 119 - "load_frozen_history"
Cohesion: 0.24
Nodes (13): load_frozen_history(), outcomes(), save_v2(), test_cli_defaults_to_v2_sources_and_saves_source_hashes(), test_cli_rejects_unvalidated_custom_source(), test_v2_build_rejects_old_sources_and_specialty_opt_in(), test_v2_hash_corruption_is_rejected(), test_v2_load_default_uses_isolated_root_and_missing_v2_never_falls_back() (+5 more)

### Community 120 - "constraints.py"
Cohesion: 0.16
Nodes (9): 4. أهم الملفات بالتفصيل المختصر, `src/experiments/course_only_core.py` و`src/recommendation/__init__.py`, `src/features/feature_contract.py`, `src/recommendation/constraints.py`, _credit_value(), normalize_requirement_policies(), PlanConstraints, _requirement_id() (+1 more)

### Community 123 - "src/__init__.py"
Cohesion: 0.18
Nodes (8): 4. أهم الملفات بالتفصيل المختصر, `scripts/promote_shortlist_artifacts.py`, `src/paths.py` و`.gitattributes`, build_promotion_manifest(), promote_shortlist_artifacts(), verify_training_sources(), project_file(), read_artifact_json()

### Community 127 - "course_only_recommendation.py"
Cohesion: 0.19
Nodes (7): capture_protected_files(), verify_protected_files(), main(), build_report(), plan_table(), read_json(), table()

### Community 128 - "`Phase 6 — تنفيذ Benchmark وعرض نتائج المرحلتين والمفاضلات لاعتماد الاستراتيجيات بصورة مستقلة.`"
Cohesion: 0.13
Nodes (15): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 2. قبل → بعد, 3. الملفات المنتجة أو المعدلة, 4. أهم الملفات بالتفصيل المختصر, 5. مخطط سير البيانات, 6. `Input → Processing → Output` (+7 more)

### Community 129 - "`Phase 2 — Payload Adapters, Matrix Helper, Classification & Constraints`"
Cohesion: 0.14
Nodes (14): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 2. قبل → بعد, 3. الملفات المنتجة أو المعدلة, 5. مخطط سير البيانات, 6. `Input → Processing → Output`, 7. كيف تم اختبار المرحلة؟ (+6 more)

### Community 130 - "`Phase 3 — History Delta والحفظ immutable والتحويل الذري`"
Cohesion: 0.14
Nodes (14): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 2. قبل → بعد, 3. الملفات المنتجة أو المعدلة, 5. مخطط سير البيانات, 6. `Input → Processing → Output`, 7. كيف تم اختبار المرحلة؟ (+6 more)

### Community 136 - "`Phase 4 — تنفيذ مقاييس Balance وواجهة الاستراتيجيات ومرشحي التقييم المستقل لكل مرحلة.`"
Cohesion: 0.14
Nodes (14): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 2. قبل → بعد, 3. الملفات المنتجة أو المعدلة, 5. مخطط سير البيانات, 6. `Input → Processing → Output`, 7. كيف تم اختبار المرحلة؟ (+6 more)

### Community 137 - "`Phase 5 — ربط المرحلتين واختبارات Parity وOracle وتوليفات الاستراتيجيات والتقرير التاريخي والسياساتي.`"
Cohesion: 0.14
Nodes (14): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 2. قبل → بعد, 3. الملفات المنتجة أو المعدلة, 5. مخطط سير البيانات, 6. `Input → Processing → Output`, 7. كيف تم اختبار المرحلة؟ (+6 more)

### Community 138 - "`Phase 7 — تثبيت السياسات المعتمدة في Manifest وإعادة التحقق وتحديث الوثائق والرسم.`"
Cohesion: 0.14
Nodes (14): 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 2. قبل → بعد, 3. الملفات المنتجة أو المعدلة, 5. مخطط سير البيانات, 6. `Input → Processing → Output`, 7. كيف تم اختبار المرحلة؟, 8. أهم ما أثبتته المرحلة (+6 more)

### Community 139 - "README.md"
Cohesion: 0.18
Nodes (3): ءخريطة الملفات المهمة, مسارات متوقعة وغير منفذة, مكونات موجودة قبل الخطة ستستخدمها المراحل

### Community 140 - "`Phase 1 — Artifacts & Contracts`"
Cohesion: 0.15
Nodes (13): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 3. الملفات المنتجة أو المعدلة, 5. مخطط سير البيانات, 6. `Input → Processing → Output`, 7. كيف تم اختبار المرحلة؟, 8. أهم ما أثبتته المرحلة (+5 more)

### Community 141 - "xml_2_json.py"
Cohesion: 0.31
Nodes (5): clean_xml(), get_value(), load_xml(), convert_xml_to_json(), main()

### Community 142 - "explain_recommendation.py"
Cohesion: 0.35
Nodes (10): check(), collect_term(), capture(), course_math(), main(), read_export(), records(), save() (+2 more)

### Community 144 - "test_build_student_course_enriched.py"
Cohesion: 0.29
Nodes (5): main(), enrichment_inputs(), test_main_builds_status_inner_join_and_auditable_plan_left_join(), test_main_rejects_many_to_many_enrichment_sources(), write_enrichment_inputs()

### Community 145 - "المسار العام لـ`Two-Stage`"
Cohesion: 0.24
Nodes (8): 2. قبل → بعد, 9. ما الذي لم تنفذه هذه `Phase`؟, 4. أهم الملفات بالتفصيل المختصر, المسار العام لـ`Two-Stage`, حدود القراءة الصحيحة للمخطط, مسار تحديث التاريخ المنفصل, load_two_stage_artifacts(), TwoStageArtifacts

### Community 146 - "clean_degree_course"
Cohesion: 0.33
Nodes (7): clean_degree_course(), main(), to_integer(), test_clean_degree_course_normalizes_contract_and_stable_order(), test_clean_degree_course_rejects_missing_required_columns(), test_main_writes_the_clean_degree_course_artifact(), test_to_integer_converts_numeric_inputs_to_nullable_int64()

### Community 147 - "importlib"
Cohesion: 0.28
Nodes (3): _import_targets(), test_production_packages_do_not_import_project_runner(), test_upstream_packages_do_not_import_recommendation()

### Community 148 - "11. Non-blocking Review Items"
Cohesion: 0.22
Nodes (9): 11. Non-blocking Review Items, REVIEW ITEM: Diploma preprocessing uses the full export, REVIEW ITEM: Future-dependent population selection, REVIEW ITEM: Missing history, catalog/diploma coverage, and zero credits, REVIEW ITEM: Modeling route and frozen history are separate, REVIEW ITEM: Observed joins are valid but some guards/reporting are absent, REVIEW ITEM: Official fail versus modeled fail, REVIEW ITEM: RAW temporal provenance and cumulative counters (+1 more)

### Community 149 - "recommendation_fixtures.py"
Cohesion: 0.31
Nodes (4): RecordingModel, synthetic_components(), synthetic_course_history(), synthetic_grade_scale()

### Community 150 - "prediction_contract"
Cohesion: 0.25
Nodes (8): clip, clip, expected_points_method, prediction_contract, fail, grade, reject_non_finite, reject_wrong_shape

### Community 151 - "official_artifacts"
Cohesion: 0.25
Nodes (4): 4. V1/V2 Isolation, traced(), official_artifacts(), read_parquet()

### Community 152 - "classify_candidate_status"
Cohesion: 0.38
Nodes (3): `src/recommendation/course_status.py`, classify_candidate_status(), normalize_previous_status()

### Community 153 - ".as_of_part"
Cohesion: 0.40
Nodes (4): 5. Provenance contract, 6. نسخ Frozen Historical State, 18. Production Complexity, الملفات والسبب المعماري

### Community 154 - "Data / Features V2 migration report — 2026-09-21"
Cohesion: 0.60
Nodes (4): Data / Features V2 migration report — 2026-09-21, build_temporal_split(), main(), summarize_split()

### Community 155 - "5. Which Frozen History Was Selected and Why"
Cohesion: 0.40
Nodes (5): 5. Which Frozen History Was Selected and Why, الـ bundle الفعلي المستخدم, المعنى والمواعيد الأربعة, لماذا frozen، وكيف يمنع التسرب؟, من أين بُني؟

### Community 156 - "شرح تنفيذ `Two-Stage Recommendation`"
Cohesion: 0.50
Nodes (4): أساس الحكم وحدود الأدلة, الفروق والقيود المهمة, شرح تنفيذ `Two-Stage Recommendation`, نطاق هذه المهمة

### Community 157 - "analyze_course_plan_changes.py"
Cohesion: 0.83
Nodes (3): main(), normalize_name(), print_table()

## Knowledge Gaps
- **664 isolated node(s):** `dataset_version`, `feature_engineering_version`, `grade_scale_sha256`, `grade_scale_version`, `path` (+659 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1079 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AcademicPlanRecommender` connect `AcademicPlanRecommender` to `compute_plan_context_features`, `Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب`, `paths.py`, `inputs.py`, `test_recommendation_v2.py`, `Production Contract — PHP ↔ Python Recommendation Service`, `explain_recommendation.py`, `numpy`, `json`, `render_recommendation_explanation.py`, `engine.py`, `previous_course_status_inference.py`, `recommendation_fixtures.py`, `modeling.py`, `evaluation/evaluate_xml_recommendations.py`, `summarize_scored_plans`, `pandas`, `course_only_recommendation.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `GradeScale` connect `GradeScale` to `analyze_model_errors.py`, `two_stage_artifacts.py`, `train_models.py`, `ابدأ من هنا — Academic Advisor`, `test_model_artifact_isolation.py`, ``Phase 1 — Artifacts & Contracts``, `engine.py`, `numpy`, `degree_points.py`, `المسار العام لـ`Two-Stage``, `Recommendation Trace — Student 29485.111`, `recommendation_fixtures.py`, `modeling.py`, `summarize_scored_plans`, `src/__init__.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `load_frozen_history()` connect `load_frozen_history` to `paths.py`, `build_frozen_history`, `test_history_update.py`, `temporal_features.py`, `engine.py`, `المسار العام لـ`Two-Stage``, `history_update.py`, `.as_of_part`, `5. Which Frozen History Was Selected and Why`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `prepare_model_matrix()` (e.g. with `Phase 2 — Payload Adapters, Matrix Helper, Classification & Constraints` and `Official Recommendation V2 Implementation Plan`) actually correct?**
  _`prepare_model_matrix()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `dataset_version`, `feature_engineering_version`, `grade_scale_sha256` to the rest of the system?**
  _664 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `analyze_model_errors.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05028305028305028 - nodes in this community are weakly interconnected._
- **Should `test_two_stage_artifacts.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11041229909154437 - nodes in this community are weakly interconnected._