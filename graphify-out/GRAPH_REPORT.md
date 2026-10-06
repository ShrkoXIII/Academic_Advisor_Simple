# Graph Report - Academic_Advisor_Simple  (2026-10-06)

## Corpus Check
- 261 files · ~2,293,068 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 51 file(s) not represented in the graph (top: .csv 18, .log 14, .parquet 8)

## Summary
- 2296 nodes · 5250 edges · 123 communities (111 shown, 12 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 221 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- paths.py
- analyze_model_errors.py
- two_stage_artifacts.py
- enumerate_plan_indices
- test_recommendation_v2.py
- test_two_stage_artifacts.py
- Pre-Modeling Data V2 and Features V2 Audit
- Experiment Winner Decision Audit V2
- test_modeling_v2_io.py
- pathlib
- test_temporal_features.py
- test_clean_outliers.py
- test_local_recommendation.py
- previous_course_status_inference.py
- previous_course_status_experiment.py
- attempt_number_training.py
- numpy
- test_main_runner.py
- verify_cleaning_policy_v2.py
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
- add_specialty_history_features
- test_model_artifact_isolation.py
- clean_student_status
- feature_contract.py
- test_experiments_v2_io.py
- pytest
- fail
- metadata
- test_feature_pipeline.py
- project_status.py
- degree_points.py
- render_recommendation_explanation.py
- grade
- متابعة بناء Academic Advisor
- merge
- Recommendation Trace — Student 29485.111
- test_clean_student_diploma.py
- Readme.md
- modeling.py
- provenance
- تدقيق مسار البيانات والمودلات والتوصية — 2026-09-14
- test_build_registration_roster.py
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
- pandas
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
- توثيق Baseline قبل تنفيذ Recommendation Two-stage
- Model Artifact Isolation Audit Implementation Plan
- تشغيل توصيات الخطط محلياً
- selected_candidate
- feature_contract
- inner_merge
- Model Artifact Isolation Audit
- التحقق من التوصية بالتراكمي المتوقع والتاريخ المجمد
- summary.md
- ابدأ من هنا — Academic Advisor
- Official Recommendation V2 migration — 2026-09-27
- graphify reference: query, path, explain
- Isolated attempt-number experiment plan
- src/__init__.py
- specialty_history.py
- student_level
- مراجعة خصائص المودل — 2026-09-10
- جدول تتبع تحسينات المودل
- ImportTests
- artifacts
- training_weight
- تحقق النسخة النهائية
- 18. Top 3 Output
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- artifact_sha256
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- extraction-spec.md
- 2026-09-27-course-only-recommendation.md
- student_status_course_comparison.md
- verification.md
- academic-advisor-simple

## God Nodes (most connected - your core abstractions)
1. `prepare_model_matrix()` - 44 edges
2. `file_sha256()` - 41 edges
3. `clean_id_columns()` - 31 edges
4. `require_current_features()` - 31 edges
5. `load_frozen_history()` - 31 edges
6. `AcademicPlanRecommender` - 31 edges
7. `clean_student_course()` - 30 edges
8. `clean_column_names()` - 29 edges
9. `GradeScale` - 29 edges
10. `enumerate_plan_indices()` - 29 edges

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

## Communities (123 total, 12 thin omitted)

### Community 0 - "paths.py"
Cohesion: 0.05
Nodes (49): Final output shape: Frozen History, 18. Production Complexity, 9. Tests, 5. Which Frozen History Was Selected and Why, الـ bundle الفعلي المستخدم, المعنى والمواعيد الأربعة, لماذا frozen، وكيف يمنع التسرب؟, من أين بُني؟ (+41 more)

### Community 1 - "analyze_model_errors.py"
Cohesion: 0.05
Nodes (52): GPA للخطط المسجلة الفعلية, attach_analysis_columns(), build_course_segments(), build_degree_analysis(), build_plan_frame(), build_plan_segments(), build_shap_importance(), build_year_analysis() (+44 more)

### Community 2 - "two_stage_artifacts.py"
Cohesion: 0.13
Nodes (17): build_promotion_manifest(), promote_shortlist_artifacts(), verify_training_sources(), artifact_relative_paths(), _is_sha256(), load_manifest_assets(), load_model_pair(), load_two_stage_artifacts() (+9 more)

### Community 3 - "enumerate_plan_indices"
Cohesion: 0.09
Nodes (9): 6. Error contract, 8. الربط اللاحق بالـAPI, CandidateImportError, enumerate_plan_indices(), visit(), resolve_credit_bounds(), empty_summaries(), EnumerationTests (+1 more)

### Community 4 - "test_recommendation_v2.py"
Cohesion: 0.06
Nodes (47): RecordingModel, synthetic_candidates(), synthetic_components(), synthetic_course_history(), synthetic_engine(), synthetic_grade_scale(), synthetic_snapshot(), experiment() (+39 more)

### Community 5 - "test_two_stage_artifacts.py"
Cohesion: 0.11
Nodes (36): artifact_root(), digest(), expected_contract(), FakeBooster, load(), mutate_manifest(), promote(), promoted_files() (+28 more)

### Community 6 - "Pre-Modeling Data V2 and Features V2 Audit"
Cohesion: 0.07
Nodes (23): 10. Blockers, 11. Non-blocking Review Items, 12. Final Decision, 1. Executive Result, 2. Pipeline Map, 3. Artifact Inventory, 4. V1/V2 Isolation, 5. Temporal Integrity (+15 more)

### Community 7 - "Experiment Winner Decision Audit V2"
Cohesion: 0.10
Nodes (19): 10. Specialty-History Support Analysis, 11. Course-Level Accuracy, 12. Bias Analysis, 13. Tail / Extreme Error Analysis, 14. Direct-Points Experiments, 15. Credit-Weighting Experiments, 16. Degree ID vs Degree History, 17. Robustness / Bootstrap (+11 more)

### Community 8 - "test_modeling_v2_io.py"
Cohesion: 0.07
Nodes (14): clean_xml(), get_value(), load_xml(), convert_xml_to_json(), main(), xml_rows(), feature_rows(), isolated_io() (+6 more)

### Community 9 - "pathlib"
Cohesion: 0.11
Nodes (9): 8. Reference regression case, benchmark(), main(), peak_memory_mib(), AcademicPlanRecommender, main(), save_recommendations(), write_json() (+1 more)

### Community 10 - "test_temporal_features.py"
Cohesion: 0.34
Nodes (5): build_temporal_course_history(), CourseHistoryState, load_course_history_state(), course_rows(), CourseHistoryTests

### Community 11 - "test_clean_outliers.py"
Cohesion: 0.08
Nodes (34): Appendix: 62-column outlier-filtered output inventory, `build_registration_roster.py`, `build_student_course_enriched.py`, `build_temporal_features.py`, `build_temporal_split.py`, `clean_degree_course.py`, `clean_outliers.py`, `clean_student_course.py` (+26 more)

### Community 12 - "test_local_recommendation.py"
Cohesion: 0.15
Nodes (13): 6. Input Parsing, طريقة الرصد وحدودها, select_cases(), clean_id(), select_batch_cases(), resolve_current_gpa_credits(), build_student_snapshot(), load_local_inputs() (+5 more)

### Community 13 - "previous_course_status_inference.py"
Cohesion: 0.06
Nodes (29): I. Recommendation impact, run_recommendations(), compare_course_sets(), distribution(), optimize_exact_credits(), plan_context_sensitivity(), prepare_course_rows(), score_courses_once() (+21 more)

### Community 14 - "previous_course_status_experiment.py"
Cohesion: 0.11
Nodes (20): augment_feature_frame(), build_experimental_datasets(), build_status_history(), _distribution(), _keys(), previous_status_for_targets(), main(), _protected_paths() (+12 more)

### Community 15 - "attempt_number_training.py"
Cohesion: 0.11
Nodes (18): main(), save_provenance(), source_signature(), capture_protected(), paired_cluster_interval(), protected_manifest(), row_fingerprint(), transform_matrix() (+10 more)

### Community 16 - "numpy"
Cohesion: 0.07
Nodes (16): check(), collect_term(), capture(), course_math(), main(), read_export(), records(), save() (+8 more)

### Community 17 - "test_main_runner.py"
Cohesion: 0.11
Nodes (17): _list_steps(), main(), _run_steps(), _select_steps(), _show_version_boundary(), Step, _record_processes(), test_all_dry_run_shows_v2_commands_without_execution() (+9 more)

### Community 18 - "verify_cleaning_policy_v2.py"
Cohesion: 0.20
Nodes (8): audit_policy(), compare_tables(), main(), compare(), describe(), main(), original_cleaner(), signature()

### Community 19 - "Storyboard — Recommendation V2 — Student 29485.111"
Cohesion: 0.07
Nodes (26): Delivery and continuity checks, Editable layer inventory, Evidence lock for the edit, Production preparation for Higgsfield / native compositor, Reusable animated motifs, Scene 10 — من قائمة إلى خطط, Scene 11 — سياق الخطة والمواد الأخرى, Scene 12 — 47 خاصية ومصفوفة مشتركة (+18 more)

### Community 20 - "test_clean_student_course.py"
Cohesion: 0.07
Nodes (46): A. Current semantics, B. Distribution, C. Outcome relationship, D. Experiment setup, Distribution shift, E. Overall model results, F. Repeat-only results, Fail calibration (+38 more)

### Community 21 - "analyze_repeat_withdrawal_balance.py"
Cohesion: 0.06
Nodes (42): finish_status_inventory(), grade_range_disagreements(), graph_navigation(), main(), nonstandard_history_sensitivity(), protected_manifest(), run(), sha256() (+34 more)

### Community 22 - "مسار مشروع Academic Advisor كاملًا"
Cohesion: 0.08
Nodes (26): 0. تعريف المسارات المركزي, 10. هندسة الخصائص الزمنية, 11. عقد الخصائص الرسمي, 12. التدريب الرسمي, 13. تقييم GPA للخطة الفعلية, 14. تحليل الأخطاء, 15. تجربة الاختصاص وExpected Points, 16. محرك ترشيح الخطط الحالي (+18 more)

### Community 23 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 24 - "evaluation/evaluate_xml_recommendations.py"
Cohesion: 0.11
Nodes (24): actual_metrics(), course_overlap(), course_text(), json_value(), main(), markdown_number(), observed_plan_estimate(), one_id() (+16 more)

### Community 25 - "parameters"
Cohesion: 0.30
Nodes (23): parameters, parameters, parameters, parameters, bagging_fraction, bagging_freq, bagging_seed, data_random_seed (+15 more)

### Community 26 - "inputs.py"
Cohesion: 0.13
Nodes (14): normalize_requirement_policies(), _requirement_id(), classify_candidate_status(), normalize_previous_status(), _explicitly_ineligible(), normalize_candidate_payloads(), normalize_request_payload(), normalize_student_payload() (+6 more)

### Community 27 - "previous_course_status_training.py"
Cohesion: 0.10
Nodes (20): prepare_course_matrix(), _check_saved_baseline(), evaluate_holdout(), _paired_metrics(), _predict(), _retake_sample(), status_slices(), _input_sha256() (+12 more)

### Community 28 - "test_two_stage_constraints.py"
Cohesion: 0.15
Nodes (25): _credit_value(), enumerate_feasible_plan_indices(), PlanConstraints, candidates(), policies(), request(), test_constraints_match_independent_exhaustive_oracle_and_preserve_candidates(), test_duplicate_normalized_requirement_ids_reject_even_when_values_match() (+17 more)

### Community 29 - "GradeScale"
Cohesion: 0.13
Nodes (12): Constraints and review focus, Official Recommendation V2 Implementation Plan, Tasks, descriptive_analysis(), distribution(), evaluate_predictions(), save_table(), subsets() (+4 more)

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
Cohesion: 0.15
Nodes (12): 1. التحليل حسب السنة الدراسية, 2. التحليل حسب الاختصاص, 3. الخصائص الأكثر تأثيرًا, 4. لماذا خطأ توقع العلامة مرتفع نسبيًا؟, أهم الخصائص المفردة, اختصاصات مستقرة نسبيًا, الاختصاصات الأضعف ذات العينة الكافية, التأثير حسب عائلة الخصائص (+4 more)

### Community 34 - "الخطة النهائية: 33 → 50 → 47 مع Balance كهدف فعلي"
Cohesion: 0.09
Nodes (21): 1. القرارات الثابتة والواجهات, 2. المدخلات والتاريخ والقيود, 3. تنفيذ التوقعات وBalance والترتيب, 4. التحقق وبوابتا اعتماد الاستراتيجيات, 5. ترتيب العمل وBenchmark والتسليم, 6. توثيق Baseline لهذه اللقطة, Balance components, Benchmark المعتمد (+13 more)

### Community 35 - "train_models.py"
Cohesion: 0.10
Nodes (26): fit_historical_grade_model(), model_metrics(), calibration_table(), classification_metrics(), feature_importance(), _json_default(), _lightgbm(), main() (+18 more)

### Community 36 - "تحليل تشخيصي لأعمدة طلب التوصية"
Cohesion: 0.11
Nodes (18): 10. أسئلة تتطلب تأكيد backend/support, 1. الطالب والفصل المستخدمان للتحقيق, 2. صفوف الطلب الخام للطالب والفصل, 3. الجداول والمصادر التي فُحصت, 4. ربط الأعمدة واحدًا واحدًا, 5. أدلة المطابقة والتكرار على مستوى الصفوف, 6. الأعمدة الغامضة, 7. أعمدة التسرب المحتملة (+10 more)

### Community 37 - "تقرير أخطاء أفضل مودل Expected Points"
Cohesion: 0.11
Nodes (18): 1. تعريف الأخطاء, 2. الخطأ العام على تسجيلات المواد, 3. النتائج حسب فصل 2025, 4. الخطأ حسب Course, 5. الخطأ حسب Degree, 6. خطأ الخطط, 7. الاستنتاج, 8. مصادر الأرقام (+10 more)

### Community 38 - "add_specialty_history_features"
Cohesion: 0.19
Nodes (9): add_specialty_history_features(), SpecialtyHistoryTests, rows(), test_20251_excludes_current_and_future_and_20252_includes_finalized_20251(), test_empty_test_keeps_output_schema(), test_generalized_parts_restore_unsorted_rows_with_duplicate_indices(), test_new_degree_enters_both_hierarchy_levels_only_in_later_parts(), test_test_parts_must_all_follow_training() (+1 more)

### Community 39 - "test_model_artifact_isolation.py"
Cohesion: 0.17
Nodes (9): isolation_violations(), test_artifact_namespaces(), test_dependency_checker_allows_official_and_local_imports(), test_dependency_checker_detects_forbidden_imports_and_paths(), test_official_packages_do_not_depend_on_experiments(), test_xml_recommendation_exception_does_not_allow_direct_experiment_imports(), _import_targets(), test_production_packages_do_not_import_project_runner() (+1 more)

### Community 40 - "clean_student_status"
Cohesion: 0.08
Nodes (36): C. 47 Feature Audit, Data / Features V2 migration report — 2026-09-21, count_regular_semesters_between(), is_regular_semester(), build_temporal_split(), main(), summarize_split(), clean_degree_course() (+28 more)

### Community 41 - "feature_contract.py"
Cohesion: 0.14
Nodes (14): capture_protected_files(), verify_protected_files(), main(), load_experiment(), prepare_course_folds(), train_experiment(), training_signature(), learn_category_levels() (+6 more)

### Community 42 - "test_experiments_v2_io.py"
Cohesion: 0.13
Nodes (7): assert_preserved(), feature_rows(), isolated_io(), synthetic_train(), SyntheticModel, test_coordinator_uses_v2_baseline_cache_outputs_and_metadata_candidate(), test_missing_v2_input_fails_without_using_v1()

### Community 43 - "pytest"
Cohesion: 0.26
Nodes (8): _legacy_47_matrix(), _matrix_inputs(), test_default_matrix_matches_legacy_47_exactly_without_mutating_inputs(), test_explicit_feature_order_coerces_only_the_requested_columns(), test_explicit_features_reject_duplicate_model_columns(), test_explicit_features_reject_names_outside_the_model_contract(), test_legacy_course_matrix_api_retains_33_feature_coercion_and_missing_validation(), test_stage1_matches_legacy_slice_without_requiring_plan_context()

### Community 44 - "fail"
Cohesion: 0.12
Nodes (17): brier, calibration_error_10_bins, log_loss, pr_auc, roc_auc, experimental_test_metrics, feature_importance, final_boost_rounds (+9 more)

### Community 45 - "metadata"
Cohesion: 0.12
Nodes (17): created_at_utc, dataset_version, experiment, feature_engineering_version, holdout_history_protocol, model_family, seed, targets (+9 more)

### Community 46 - "test_feature_pipeline.py"
Cohesion: 0.24
Nodes (6): attach_plan_context(), build_feature_tables(), main(), print_feature_summary(), FeaturePipelineTests, build()

### Community 47 - "project_status.py"
Cohesion: 0.27
Nodes (5): main(), print_model_metrics(), ProjectStage, relative(), test_stage_paths_order_and_version_boundary()

### Community 48 - "degree_points.py"
Cohesion: 0.11
Nodes (18): compare_holdout_by_degree(), load_feature_frames(), main(), run_validation(), selected_round_count(), build_metadata(), experiment_signature(), _json_default() (+10 more)

### Community 49 - "render_recommendation_explanation.py"
Cohesion: 0.33
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
Cohesion: 0.09
Nodes (20): 10. Course History Feature Injection, 11. Model Matrix and Feature Contract, 13. GradeScale Conversion, 14. Fail Prediction, 15. Plan Generation, 16. Plan Scoring, 17. Plan Ranking, 19. Important Intermediate Tables (+12 more)

### Community 54 - "test_clean_student_diploma.py"
Cohesion: 0.13
Nodes (13): main(), main(), merge_student_course_with_diploma(), enrichment_inputs(), test_main_builds_status_inner_join_and_auditable_plan_left_join(), test_main_rejects_many_to_many_enrichment_sources(), write_enrichment_inputs(), academic_info() (+5 more)

### Community 55 - "Readme.md"
Cohesion: 0.23
Nodes (3): Experiment boundary, Model Artifact Policy, Preserved history and migration status

### Community 56 - "modeling.py"
Cohesion: 0.22
Nodes (15): اليوم الثالث: آخر تعديلين والترشيح — حوالي 4.5 ساعات, Recommendation report only, Static dependency and writer audit, load_or_train_holdout(), aggregate_plans(), course_predictions(), evaluate_selected_holdout(), evaluate_variant() (+7 more)

### Community 57 - "provenance"
Cohesion: 0.19
Nodes (14): dataset_version_basis, metadata_path, metadata_sha256, source_artifact_sha256_at_promotion, source_evidence_sha256_at_promotion, target_basis, models/experiments/course_only_recommendation/category_levels.json, models/experiments/course_only_recommendation/fail_risk_classifier.txt (+6 more)

### Community 58 - "تدقيق مسار البيانات والمودلات والتوصية — 2026-09-14"
Cohesion: 0.14
Nodes (13): 1. ماذا حدث للطلاب الأربعة؟, 2. النتائج مرتبة بالأولوية, 3. حالة بقية مراحل المسار, 4. هل المودل الحالي مفيد؟, 5. ترتيب العمل المقترح, 6. الأدلة وإعادة الفحص, P1 — «الخطة الفعلية» في التقييم قد تكون جزءاً من التسجيل فقط, P1 — حذف تاريخ التدريب بسبب أحداث مستقبلية (+5 more)

### Community 59 - "test_build_registration_roster.py"
Cohesion: 0.36
Nodes (7): make_plan(), make_raw_course(), roster_inputs(), test_build_registration_roster_joins_exact_status_removes_outliers_and_keeps_plan_gaps(), test_build_registration_roster_keeps_only_registered_or_enrolled(), test_duplicate_merge_keys_raise_instead_of_multiplying_rows(), test_main_writes_full_train_and_test_rosters()

### Community 60 - "add_student_history_features"
Cohesion: 0.54
Nodes (3): add_student_history_features(), semester_rows(), StudentHistoryTests

### Community 61 - "test_previous_course_status_inference.py"
Cohesion: 0.21
Nodes (7): inference(), test_augmented_scoring_clips_predictions_before_grade_conversion(), test_augmented_scoring_rejects_nonfinite_predictions(), test_course_comparison_joins_by_course_identity_and_keeps_status(), test_course_comparison_rejects_mismatched_candidate_rows(), test_plan_comparison_uses_same_memberships_and_reports_rank_changes(), test_unresolved_prior_attempt_is_unknown_in_serving_rows()

### Community 62 - "Academic Advisor — Architecture Audit before PHP/Backend integration"
Cohesion: 0.05
Nodes (37): A. Executive Summary, Academic Advisor — Architecture Audit before PHP/Backend integration, attempt_number: القرار المدعوم بالأدلة, B. Current Data Flow, Catalog ownership, Current / Projected GPA, D. Raw Data Sources, E. Backend-Provided Fields (+29 more)

### Community 63 - "PREVIOUS_COURSE_STATUS EXPERIMENT"
Cohesion: 0.15
Nodes (12): 33 مقابل 34, 47 مقابل 48, Holdout: المقاييس الإجمالية, Holdout حسب آخر حالة سابقة, PREVIOUS_COURSE_STATUS EXPERIMENT, التحقق والعزل, الملفات والأوامر, النطاق والمصدر (+4 more)

### Community 64 - "compute_plan_context_features"
Cohesion: 0.32
Nodes (4): 12. Grade Prediction, 9. Feature Assembly, compute_plan_context_features(), PlanContextTests

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
Cohesion: 0.09
Nodes (20): 10. Proposed production structure (not created), 1. Baseline and deployment direction, 2. Recommendation request contract, 3. Candidate source contract, 4. Recommendation response contract, 5. Provenance contract, 7. Production Invariants, 9. Offline Build Pipeline vs Online Serving Pipeline (+12 more)

### Community 71 - "test_v2_paths.py"
Cohesion: 0.43
Nodes (4): versioned_path(), test_v2_artifacts_are_separate_from_originals(), test_versioned_path_preserves_parent_and_extension(), test_versioned_path_supports_artifact_extensions()

### Community 72 - "key_level"
Cohesion: 0.22
Nodes (11): key_level, key_level, both, course, course_keys, course_only, course_only_pct, status (+3 more)

### Community 73 - "تجربة الاختصاص وتوقع النقاط المباشر"
Cohesion: 0.18
Nodes (11): اعتماد المودل على تاريخ الاختصاص, السؤال, القرار المقترح, المخرجات, المقايضة على مستوى المادة, بروتوكول زمني, تجربة الاختصاص وتوقع النقاط المباشر, خصائص تاريخ الاختصاص (+3 more)

### Community 74 - "pandas"
Cohesion: 0.12
Nodes (20): cohort_counts(), main(), count(), main(), verify_policy_only(), build_registration_roster(), main(), clean_student_diploma() (+12 more)

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
Cohesion: 0.40
Nodes (4): الأولوية الحالية, اليوم الأول: كيف تُبنى الخصائص — حوالي 4.5 ساعات, اليوم الثاني: التدريب والتقييم — حوالي 4 ساعات, ملفات لا تعطيها وقتًا كبيرًا الآن

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

### Community 102 - "src/__init__.py"
Cohesion: 0.32
Nodes (3): compare(), digest(), main()

### Community 103 - "specialty_history.py"
Cohesion: 0.16
Nodes (11): 19. Risks and Limitations, FrozenSpecialtyHistory, _merge_frozen_test_history(), _merge_sequential_test_history(), _merge_training_history(), _prior_aggregates(), _total_aggregates(), _weighted_history_source() (+3 more)

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

### Community 114 - "تحقق النسخة النهائية"
Cohesion: 0.33
Nodes (5): إعادة التحقق, تحقق النسخة النهائية, تحقق الوظائف, تحقق مسار توصيات الخطط المحلي — 2026-09-12, قياس الأداء السابق

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

## Knowledge Gaps
- **583 isolated node(s):** `dataset_version`, `feature_engineering_version`, `grade_scale_sha256`, `grade_scale_version`, `path` (+578 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 975 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GradeScale` connect `GradeScale` to `analyze_model_errors.py`, `two_stage_artifacts.py`, `ابدأ من هنا — Academic Advisor`, `test_recommendation_v2.py`, `test_model_artifact_isolation.py`, `attempt_number_training.py`, `degree_points.py`, `Recommendation Trace — Student 29485.111`, `modeling.py`, `تشغيل توصيات الخطط محلياً`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `تشغيل توصيات الخطط محلياً` connect `تشغيل توصيات الخطط محلياً` to `enumerate_plan_indices`, `GradeScale`, `Readme.md`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `AcademicPlanRecommender` connect `pathlib` to `Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب`, `paths.py`, `compute_plan_context_features`, `enumerate_plan_indices`, `test_recommendation_v2.py`, `Production Contract — PHP ↔ Python Recommendation Service`, `feature_contract.py`, `pandas`, `test_local_recommendation.py`, `previous_course_status_inference.py`, `numpy`, `render_recommendation_explanation.py`, `modeling.py`, `evaluation/evaluate_xml_recommendations.py`, `inputs.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `prepare_model_matrix()` (e.g. with `Official Recommendation V2 Implementation Plan` and `8. Feature Contract`) actually correct?**
  _`prepare_model_matrix()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `dataset_version`, `feature_engineering_version`, `grade_scale_sha256` to the rest of the system?**
  _583 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `paths.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05174190888476603 - nodes in this community are weakly interconnected._
- **Should `analyze_model_errors.py` be split into smaller, more focused modules?**
  _Cohesion score 0.050580997949419004 - nodes in this community are weakly interconnected._