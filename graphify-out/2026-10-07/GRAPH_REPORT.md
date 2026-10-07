# Graph Report - Academic_Advisor_Simple  (2026-10-06)

## Corpus Check
- 284 files · ~2,315,898 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 51 file(s) not represented in the graph (top: .csv 18, .log 14, .parquet 8)

## Summary
- 2634 nodes · 6116 edges · 158 communities (141 shown, 17 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 441 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- paths.py
- analyze_model_errors.py
- GradeScale
- isolated_io
- test_recommendation_v2.py
- test_two_stage_artifacts.py
- Pre-Modeling Data V2 and Features V2 Audit
- Experiment Winner Decision Audit V2
- SyntheticModel
- save_recommendations
- add_student_history_features
- test_clean_outliers.py
- course_only_evaluation.py
- previous_course_status_experiment.py
- numpy
- explain_recommendation.py
- sys
- verify_cleaning_policy_v2.py
- Storyboard — Recommendation V2 — Student 29485.111
- clean_student_course
- analyze_repeat_withdrawal_balance.py
- مسار مشروع Academic Advisor كاملًا
- What You Must Do When Invoked
- evaluation/evaluate_xml_recommendations.py
- parameters
- add_specialty_history_features
- previous_course_status_training.py
- inputs.py
- pytest
- manifest.json
- fail
- Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب
- تحليل أخطاء مودل العلامة والخطة حسب السنة والاختصاص
- الخطة النهائية: 33 → 50 → 47 مع Balance كهدف فعلي
- test_train_models.py
- test_ranking_strategies.py
- تقرير أخطاء أفضل مودل Expected Points
- test_history_update.py
- experiment_io.py
- clean_student_status
- feature_contract.py
- AcademicPlanRecommender
- prepare_model_matrix
- fail
- metadata
- previous_status_for_targets
- project_status.py
- degree_points.py
- render_recommendation_explanation.py
- grade
- متابعة بناء Academic Advisor
- merge
- Recommendation Trace — Student 29485.111
- clean_student_diploma
- START_HERE.md
- pipeline_audit.py
- provenance
- تدقيق مسار البيانات والمودلات والتوصية — 2026-09-14
- test_build_registration_roster.py
- specialty_history.py
- test_previous_course_status_inference.py
- Academic Advisor — Architecture Audit before PHP/Backend integration
- PREVIOUS_COURSE_STATUS EXPERIMENT
- Project State — Productization Baseline
- summarize_scored_plans
- fail_risk_classifier
- input_sha256_at_promotion
- input_sha256
- COURSE-ONLY 33-FEATURE EXPERIMENT
- Production Contract — PHP ↔ Python Recommendation Service
- test_v2_paths.py
- key_level
- تجربة الاختصاص وتوقع النقاط المباشر
- J. Candidate & Requirement Policy Contract
- training_weights
- levels
- student_status_course_comparison_metrics.json
- student_level
- load_or_train_holdout
- trace_student_29485_20251.py
- تشغيل توصيات الخطط محلياً
- Repository Guidelines
- graphify reference: extra exports and benchmark
- course_history
- grade_regressor
- normalize_history_delta
- F. Precomputed Serving State
- توثيق Baseline قبل تنفيذ Recommendation Two-stage
- Model Artifact Isolation Audit Implementation Plan
- previous_course_status_inference.py
- selected_candidate
- feature_contract
- pandas
- inner_merge
- Model Artifact Isolation Audit
- main
- summary.md
- ابدأ من هنا — Academic Advisor
- Official Recommendation V2 migration — 2026-09-27
- graphify reference: query, path, explain
- Isolated attempt-number experiment plan
- I. Semester Update Lifecycle
- H. Frozen History Analysis
- student_level
- مراجعة خصائص المودل — 2026-09-10
- جدول تتبع تحسينات المودل
- ImportTests
- artifacts
- training_weight
- enumerate_plan_indices
- test_analyze_model_errors.py
- test_recommendation_inputs_v2.py
- test_repeat_withdrawal_balance.py
- Academic Advisor — Architecture Map
- D. Raw Data Sources
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- HistorySnapshot
- B. Current Data Flow
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- FrozenHistoryManager
- extraction-spec.md
- 2026-09-27-course-only-recommendation.md
- student_status_course_comparison.md
- importlib
- `Phase 6 — تنفيذ Benchmark وعرض نتائج المرحلتين والمفاضلات لاعتماد الاستراتيجيات بصورة مستقلة.`
- CourseHistoryState
- `Phase 3 — History Delta والحفظ immutable والتحويل الذري`
- verification.md
- academic-advisor-simple
- `Phase 4 — تنفيذ مقاييس Balance وواجهة الاستراتيجيات ومرشحي التقييم المستقل لكل مرحلة.`
- `Phase 5 — ربط المرحلتين واختبارات Parity وOracle وتوليفات الاستراتيجيات والتقرير التاريخي والسياساتي.`
- `Phase 7 — تثبيت السياسات المعتمدة في Manifest وإعادة التحقق وتحديث الوثائق والرسم.`
- plan_explanation/README.md
- `Phase 1 — Artifacts & Contracts`
- test_modeling_v2_io.py
- 06 — API Sequence
- C. 47 Feature Audit
- compute_plan_context_features
- clean_id_columns
- 3. الملفات المنتجة أو المعدلة
- evaluate_holdout
- status_slices
- prediction_contract
- validate_history_state
- شرح تنفيذ `Two-Stage Recommendation`
- التحقق من التوصية بالتراكمي المتوقع والتاريخ المجمد
- Data / Features V2 migration report — 2026-09-21
- read.md
- test_build_shap_importance_uses_absolute_contributions_and_family_sums
- analyze_course_plan_changes.py

## God Nodes (most connected - your core abstractions)
1. `prepare_model_matrix()` - 52 edges
2. `file_sha256()` - 45 edges
3. `load_frozen_history()` - 41 edges
4. `AcademicPlanRecommender` - 35 edges
5. `GradeScale` - 34 edges
6. `enumerate_plan_indices()` - 34 edges
7. `require_current_features()` - 32 edges
8. `clean_student_course()` - 31 edges
9. `clean_id_columns()` - 31 edges
10. `normalize_candidates()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `attempt_number: القرار المدعوم بالأدلة` --references--> `clean_student_course()`  [INFERRED]
  reports/..md → src/data/clean_student_course.py
- `GPA للخطط المسجلة الفعلية` --references--> `summarize_plan_errors()`  [INFERRED]
  reports/attempt_number_feature_analysis.md → src/evaluation/evaluate_plan_gpa.py
- ``src/experiments/course_only_core.py` و`src/recommendation/__init__.py`` --references--> `prepare_course_matrix()`  [INFERRED]
  plan_explanation/PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md → src/experiments/course_only_core.py
- `2. قبل → بعد` --references--> `prepare_model_matrix()`  [INFERRED]
  plan_explanation/PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md → src/features/feature_contract.py
- ``src/features/feature_contract.py`` --references--> `prepare_model_matrix()`  [INFERRED]
  plan_explanation/PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md → src/features/feature_contract.py

## Import Cycles
- None detected.

## Communities (158 total, 17 thin omitted)

### Community 0 - "paths.py"
Cohesion: 0.08
Nodes (39): Final output shape: Frozen History, 18. Production Complexity, لماذا frozen، وكيف يمنع التسرب؟, main(), build_frozen_history(), file_sha256(), load_frozen_history(), previous_academic_part() (+31 more)

### Community 1 - "analyze_model_errors.py"
Cohesion: 0.19
Nodes (20): attach_analysis_columns(), build_course_segments(), build_degree_analysis(), build_plan_frame(), build_plan_segments(), build_shap_importance(), build_year_analysis(), build_year_degree_analysis() (+12 more)

### Community 2 - "GradeScale"
Cohesion: 0.09
Nodes (26): A. التسلسل المنفذ محليًا — 6 أطراف, 2. قبل → بعد, `scripts/promote_shortlist_artifacts.py`, `src/recommendation/two_stage_artifacts.py`, 4. أهم الملفات بالتفصيل المختصر, build_promotion_manifest(), promote_shortlist_artifacts(), verify_training_sources() (+18 more)

### Community 3 - "isolated_io"
Cohesion: 0.15
Nodes (6): feature_rows(), isolated_io(), load_model(), synthetic_fit(), SyntheticGradeModel, analysis()

### Community 4 - "test_recommendation_v2.py"
Cohesion: 0.05
Nodes (52): ملفات الاختبار الثلاثة, RecordingModel, synthetic_candidates(), synthetic_components(), synthetic_course_history(), synthetic_engine(), synthetic_grade_scale(), synthetic_snapshot() (+44 more)

### Community 5 - "test_two_stage_artifacts.py"
Cohesion: 0.07
Nodes (55): `tests/test_two_stage_artifacts.py`, 10. أسئلة تتطلب تأكيد backend/support, 1. الطالب والفصل المستخدمان للتحقيق, 2. صفوف الطلب الخام للطالب والفصل, 3. الجداول والمصادر التي فُحصت, 4. ربط الأعمدة واحدًا واحدًا, 5. أدلة المطابقة والتكرار على مستوى الصفوف, 6. الأعمدة الغامضة (+47 more)

### Community 6 - "Pre-Modeling Data V2 and Features V2 Audit"
Cohesion: 0.07
Nodes (24): 10. Blockers, 11. Non-blocking Review Items, 12. Final Decision, 1. Executive Result, 2. Pipeline Map, 3. Artifact Inventory, 4. V1/V2 Isolation, 5. Temporal Integrity (+16 more)

### Community 7 - "Experiment Winner Decision Audit V2"
Cohesion: 0.10
Nodes (19): 10. Specialty-History Support Analysis, 11. Course-Level Accuracy, 12. Bias Analysis, 13. Tail / Extreme Error Analysis, 14. Direct-Points Experiments, 15. Credit-Weighting Experiments, 16. Degree ID vs Degree History, 17. Robustness / Bootstrap (+11 more)

### Community 8 - "SyntheticModel"
Cohesion: 0.22
Nodes (3): SyntheticModel, test_main_reads_v2_and_writes_only_v2_with_correct_metadata(), synthetic_fit()

### Community 9 - "save_recommendations"
Cohesion: 0.12
Nodes (5): 20. Leakage and Contract Checks, طريقة الرصد وحدودها, save_recommendations(), SyntheticIntegrationTests, PlanPreservationTests

### Community 10 - "add_student_history_features"
Cohesion: 0.14
Nodes (14): إعادة التحقق, تحقق النسخة النهائية, تحقق الوظائف, تحقق مسار توصيات الخطط المحلي — 2026-09-12, قياس الأداء السابق, attach_plan_context(), build_feature_tables(), main() (+6 more)

### Community 11 - "test_clean_outliers.py"
Cohesion: 0.06
Nodes (46): 03 — Data + Features Pipeline, A. التنظيف والإثراء — 10 عقد, B. فرع Roster — تسجيلات السياق وليست Targets, حدود جودة البيانات والزمن, لقطة الوسائط المحلية, مصادر البيانات الفعلية, Appendix: 62-column outlier-filtered output inventory, `build_registration_roster.py` (+38 more)

### Community 13 - "course_only_evaluation.py"
Cohesion: 0.08
Nodes (19): compare_course_sets(), distribution(), optimize_exact_credits(), plan_context_sensitivity(), prepare_course_rows(), capture_protected_files(), compare_case(), experimental_run() (+11 more)

### Community 14 - "previous_course_status_experiment.py"
Cohesion: 0.20
Nodes (8): augment_feature_frame(), build_experimental_datasets(), build_status_history(), _distribution(), main(), _protected_paths(), verify_protected_files(), test_roster_is_chronology_and_w_is_not_a_zero_mark_fail()

### Community 15 - "numpy"
Cohesion: 0.09
Nodes (25): main(), save_provenance(), source_signature(), run_recommendations(), descriptive_analysis(), distribution(), evaluate_predictions(), save_table() (+17 more)

### Community 16 - "explain_recommendation.py"
Cohesion: 0.32
Nodes (11): check(), collect_term(), capture(), course_math(), main(), read_export(), records(), save() (+3 more)

### Community 17 - "sys"
Cohesion: 0.06
Nodes (24): clean_xml(), get_value(), load_xml(), convert_xml_to_json(), main(), xml_rows(), _list_steps(), main() (+16 more)

### Community 18 - "verify_cleaning_policy_v2.py"
Cohesion: 0.13
Nodes (9): audit_policy(), compare_tables(), main(), verify_policy_only(), compare(), describe(), main(), original_cleaner() (+1 more)

### Community 19 - "Storyboard — Recommendation V2 — Student 29485.111"
Cohesion: 0.07
Nodes (26): Delivery and continuity checks, Editable layer inventory, Evidence lock for the edit, Production preparation for Higgsfield / native compositor, Reusable animated motifs, Scene 10 — من قائمة إلى خطط, Scene 11 — سياق الخطة والمواد الأخرى, Scene 12 — 47 خاصية ومصفوفة مشتركة (+18 more)

### Community 20 - "clean_student_course"
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
Cohesion: 0.13
Nodes (25): 01 — System Context, الأنظمة الخارجية الحقيقية وحدودها, دليل العلاقات, المسار الحالي — 12 عقدة, 7. Student Snapshot Construction, select_cases(), clean_id(), actual_metrics() (+17 more)

### Community 25 - "parameters"
Cohesion: 0.30
Nodes (23): parameters, parameters, parameters, parameters, bagging_fraction, bagging_freq, bagging_seed, data_random_seed (+15 more)

### Community 26 - "add_specialty_history_features"
Cohesion: 0.19
Nodes (9): add_specialty_history_features(), SpecialtyHistoryTests, rows(), test_20251_excludes_current_and_future_and_20252_includes_finalized_20251(), test_empty_test_keeps_output_schema(), test_generalized_parts_restore_unsorted_rows_with_duplicate_indices(), test_new_degree_enters_both_hierarchy_levels_only_in_later_parts(), test_test_parts_must_all_follow_training() (+1 more)

### Community 27 - "previous_course_status_training.py"
Cohesion: 0.16
Nodes (12): _input_sha256(), learn_augmented_levels(), _load_tables(), load_variant(), prepare_augmented_folds(), prepare_augmented_matrix(), train_all_variants(), train_augmented_one() (+4 more)

### Community 28 - "inputs.py"
Cohesion: 0.05
Nodes (61): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 2. قبل → بعد, 3. الملفات المنتجة أو المعدلة, 4. أهم الملفات بالتفصيل المختصر, 5. مخطط سير البيانات, 6. `Input → Processing → Output` (+53 more)

### Community 29 - "pytest"
Cohesion: 0.20
Nodes (6): predict_course_points(), FixedMarks, test_aggregate_plan_gpa_uses_student_degree_part_and_credit_weighting(), test_build_metrics_report_preserves_contract_and_parts(), test_predict_course_points_preserves_audit_and_quality_points(), test_summarize_plan_errors_includes_threshold_boundaries()

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
Cohesion: 0.10
Nodes (19): 1. التحليل حسب السنة الدراسية, 2. التحليل حسب الاختصاص, 3. الخصائص الأكثر تأثيرًا, 4. لماذا خطأ توقع العلامة مرتفع نسبيًا؟, 5. إجراءات التحسين المقترحة بالترتيب, أهم الخصائص المفردة, أولوية 1 — تقييم مرشح Expected Points على خطط بديلة, أولوية 2 — مودلات Quantile وعدم اليقين (+11 more)

### Community 34 - "الخطة النهائية: 33 → 50 → 47 مع Balance كهدف فعلي"
Cohesion: 0.13
Nodes (15): 1. القرارات الثابتة والواجهات, 3. تنفيذ التوقعات وBalance والترتيب, 4. التحقق وبوابتا اعتماد الاستراتيجيات, 5. ترتيب العمل وBenchmark والتسليم, 6. توثيق Baseline لهذه اللقطة, Balance components, Benchmark المعتمد, Features والتوقعات (+7 more)

### Community 35 - "test_train_models.py"
Cohesion: 0.13
Nodes (10): feature_importance(), FakeImportanceModel, temporal_frame(), test_calibration_table_returns_only_populated_bins_with_correct_aggregates(), test_classification_metrics_clips_endpoint_probabilities(), test_classification_metrics_known_ranking_and_probabilities(), test_feature_importance_returns_top_25_without_renormalizing(), test_feature_importance_sorts_descending_and_normalizes_gain() (+2 more)

### Community 36 - "test_ranking_strategies.py"
Cohesion: 0.07
Nodes (48): BalancePolicy, compute_balance_components(), _course_records(), _academic_key(), canonical_plan_identity(), _pareto_levels(), PlanIdentity, rank_academic_reference() (+40 more)

### Community 37 - "تقرير أخطاء أفضل مودل Expected Points"
Cohesion: 0.11
Nodes (18): 1. تعريف الأخطاء, 2. الخطأ العام على تسجيلات المواد, 3. النتائج حسب فصل 2025, 4. الخطأ حسب Course, 5. الخطأ حسب Degree, 6. خطأ الخطط, 7. الاستنتاج, 8. مصادر الأرقام (+10 more)

### Community 38 - "test_history_update.py"
Cohesion: 0.13
Nodes (30): api(), delta(), hashes(), save_initial(), targets(), test_aggregate_addition_preserves_weighted_prefix_and_matches_raw_oracle(), test_bad_lineage_is_not_selected_on_restart(), test_cleanup_failure_after_publication_does_not_report_failed_update() (+22 more)

### Community 39 - "experiment_io.py"
Cohesion: 0.10
Nodes (9): compare(), digest(), main(), isolation_violations(), test_artifact_namespaces(), test_dependency_checker_allows_official_and_local_imports(), test_dependency_checker_detects_forbidden_imports_and_paths(), test_official_packages_do_not_depend_on_experiments() (+1 more)

### Community 40 - "clean_student_status"
Cohesion: 0.13
Nodes (25): count_regular_semesters_between(), is_regular_semester(), add_enrollment_features(), clean_student_status(), main(), test_count_regular_semesters_between_rejects_invalid_part_id(), test_is_regular_semester(), test_is_regular_semester_rejects_invalid_part_id() (+17 more)

### Community 41 - "feature_contract.py"
Cohesion: 0.12
Nodes (17): build_metrics_report(), main(), print_report(), summarize_plan_errors(), load_experiment(), train_experiment(), training_signature(), learn_category_levels() (+9 more)

### Community 42 - "AcademicPlanRecommender"
Cohesion: 0.14
Nodes (15): 05 — Recommendation Runtime, أين توضع المكونات الجديدة؟ — موجودة ولم تدمج, اعتماد التحميل مقابل اعتماد الطلب — 8 عقد, الحساب والترتيب, الطلب الحالي — 12 عقدة, الكلفة ومخرجات الطلب, المدخلات وحدود المرشحين, 4. أهم الملفات بالتفصيل المختصر (+7 more)

### Community 43 - "prepare_model_matrix"
Cohesion: 0.20
Nodes (12): Phase 2 — Payload Adapters, Matrix Helper, Classification & Constraints, prepare_course_matrix(), prepare_model_matrix(), FeatureContractTests, _legacy_47_matrix(), _matrix_inputs(), test_default_matrix_matches_legacy_47_exactly_without_mutating_inputs(), test_explicit_feature_order_coerces_only_the_requested_columns() (+4 more)

### Community 44 - "fail"
Cohesion: 0.12
Nodes (17): brier, calibration_error_10_bins, log_loss, pr_auc, roc_auc, experimental_test_metrics, feature_importance, final_boost_rounds (+9 more)

### Community 45 - "metadata"
Cohesion: 0.10
Nodes (21): category_levels.json, fail_risk_classifier.txt, grade_regressor.txt, artifact_sha256, created_at_utc, dataset_version, experiment, feature_engineering_version (+13 more)

### Community 46 - "previous_status_for_targets"
Cohesion: 0.25
Nodes (12): _keys(), previous_status_for_targets(), row(), test_first_attempt_ignores_current_and_future_outcomes(), test_latest_prior_attempt_wins_even_when_history_is_unsorted(), test_latest_unresolved_attempt_is_unknown_not_first_or_older_fail(), test_mark_boundaries_use_previous_attempt_only(), test_missing_prior_mark_without_explicit_withdrawal_is_rejected() (+4 more)

### Community 47 - "project_status.py"
Cohesion: 0.36
Nodes (4): main(), print_model_metrics(), relative(), test_stage_paths_order_and_version_boundary()

### Community 48 - "degree_points.py"
Cohesion: 0.14
Nodes (18): compare_holdout_by_degree(), load_feature_frames(), main(), run_validation(), selected_round_count(), build_metadata(), experiment_signature(), load_cached_validation() (+10 more)

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
Cohesion: 0.07
Nodes (28): 10. Course History Feature Injection, 11. Model Matrix and Feature Contract, 12. Grade Prediction, 13. GradeScale Conversion, 14. Fail Prediction, 16. Plan Scoring, 17. Plan Ranking, 18. Top 3 Output (+20 more)

### Community 54 - "clean_student_diploma"
Cohesion: 0.21
Nodes (9): clean_student_diploma(), main(), merge_student_course_with_diploma(), academic_info(), test_clean_student_diploma_groups_rare_types_and_fills_gpa(), test_clean_student_diploma_rejects_broken_input_contract(), test_main_writes_clean_and_merged_diploma_artifacts(), test_merge_student_course_with_diploma_preserves_unmatched_courses() (+1 more)

### Community 55 - "START_HERE.md"
Cohesion: 0.38
Nodes (3): Experiment boundary, Model Artifact Policy, Preserved history and migration status

### Community 56 - "pipeline_audit.py"
Cohesion: 0.20
Nodes (12): اليوم الثالث: آخر تعديلين والترشيح — حوالي 4.5 ساعات, aggregate_plans(), course_predictions(), evaluate_selected_holdout(), evaluate_variant(), feature_columns(), fit_experiment_model(), fit_weights() (+4 more)

### Community 57 - "provenance"
Cohesion: 0.19
Nodes (14): dataset_version_basis, metadata_path, metadata_sha256, source_artifact_sha256_at_promotion, source_evidence_sha256_at_promotion, target_basis, models/experiments/course_only_recommendation/category_levels.json, models/experiments/course_only_recommendation/fail_risk_classifier.txt (+6 more)

### Community 58 - "تدقيق مسار البيانات والمودلات والتوصية — 2026-09-14"
Cohesion: 0.14
Nodes (13): 1. ماذا حدث للطلاب الأربعة؟, 2. النتائج مرتبة بالأولوية, 3. حالة بقية مراحل المسار, 4. هل المودل الحالي مفيد؟, 5. ترتيب العمل المقترح, 6. الأدلة وإعادة الفحص, P1 — «الخطة الفعلية» في التقييم قد تكون جزءاً من التسجيل فقط, P1 — حذف تاريخ التدريب بسبب أحداث مستقبلية (+5 more)

### Community 59 - "test_build_registration_roster.py"
Cohesion: 0.36
Nodes (7): make_plan(), make_raw_course(), roster_inputs(), test_build_registration_roster_joins_exact_status_removes_outliers_and_keeps_plan_gaps(), test_build_registration_roster_keeps_only_registered_or_enrolled(), test_duplicate_merge_keys_raise_instead_of_multiplying_rows(), test_main_writes_full_train_and_test_rosters()

### Community 60 - "specialty_history.py"
Cohesion: 0.24
Nodes (10): 19. Risks and Limitations, _finish_specialty_history(), FrozenSpecialtyHistory, _merge_frozen_test_history(), _merge_sequential_test_history(), _merge_training_history(), _prior_aggregates(), _safe_average() (+2 more)

### Community 61 - "test_previous_course_status_inference.py"
Cohesion: 0.21
Nodes (7): inference(), test_augmented_scoring_clips_predictions_before_grade_conversion(), test_augmented_scoring_rejects_nonfinite_predictions(), test_course_comparison_joins_by_course_identity_and_keeps_status(), test_course_comparison_rejects_mismatched_candidate_rows(), test_plan_comparison_uses_same_memberships_and_reports_rank_changes(), test_unresolved_prior_attempt_is_unknown_in_serving_rows()

### Community 62 - "Academic Advisor — Architecture Audit before PHP/Backend integration"
Cohesion: 0.20
Nodes (9): A. Executive Summary, Academic Advisor — Architecture Audit before PHP/Backend integration, E. Backend-Provided Fields, G. Runtime Features, K. Train/Serve Skew Risks, L. Questions for Backend Team, Leakage classification لجميع مصادر الـ 47, M. Proposed Minimal Request (+1 more)

### Community 63 - "PREVIOUS_COURSE_STATUS EXPERIMENT"
Cohesion: 0.15
Nodes (12): 33 مقابل 34, 47 مقابل 48, Holdout: المقاييس الإجمالية, Holdout حسب آخر حالة سابقة, PREVIOUS_COURSE_STATUS EXPERIMENT, التحقق والعزل, الملفات والأوامر, النطاق والمصدر (+4 more)

### Community 64 - "Project State — Productization Baseline"
Cohesion: 0.20
Nodes (9): A. Current Production Baseline, B. Current Recommendation Rules, C. Current Ranking, D. Validated Academic Rules, E. University Term Policy, F. EXPERIMENTAL — NOT PRODUCTION, G. Production Boundary, H. Current Workstreams (+1 more)

### Community 65 - "summarize_scored_plans"
Cohesion: 0.16
Nodes (12): 04 — Model Training Lifecycle, Artifacts: من ينتجها ومن يستهلكها؟, Evaluation ليست مسارًا واحدًا, Version / release debt, الأهداف والاستهلاك — 7 عقد, 4. أهم الملفات بالتفصيل المختصر, GPA للخطط المسجلة الفعلية, I. Recommendation impact (+4 more)

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
Cohesion: 0.19
Nodes (9): Completion evidence, Data and features V2 structural migration, Evidence and rulings, Review focus, Tasks, versioned_path(), test_v2_artifacts_are_separate_from_originals(), test_versioned_path_preserves_parent_and_extension() (+1 more)

### Community 72 - "key_level"
Cohesion: 0.22
Nodes (11): key_level, key_level, both, course, course_keys, course_only, course_only_pct, status (+3 more)

### Community 73 - "تجربة الاختصاص وتوقع النقاط المباشر"
Cohesion: 0.18
Nodes (11): اعتماد المودل على تاريخ الاختصاص, السؤال, القرار المقترح, المخرجات, المقايضة على مستوى المادة, بروتوكول زمني, تجربة الاختصاص وتوقع النقاط المباشر, خصائص تاريخ الاختصاص (+3 more)

### Community 74 - "J. Candidate & Requirement Policy Contract"
Cohesion: 0.25
Nodes (8): Catalog ownership, Current / Projected GPA, J. Candidate & Requirement Policy Contract, Requested credit hours والمواد ذات الساعات الصفرية, الحد الأدنى للمرشحين, الخطة الكاملة والمواد المسجلة مسبقًا, المتطلبات والساعات الاختيارية, جرد السياسات

### Community 75 - "training_weights"
Cohesion: 0.15
Nodes (9): prepare_course_folds(), prepare_folds(), training_weights(), test_prepare_folds_learns_categories_only_from_each_fit_subset(), test_prepare_folds_preserves_temporal_boundaries_targets_and_weights(), test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric(), fake_train_one(), test_training_weights_preserves_index_and_numeric_coercion() (+1 more)

### Community 76 - "levels"
Cohesion: 0.24
Nodes (10): levels, path, sha256, diploma_type_id, grade_version_id, part_semester, plan_course_type_id, plan_requirement_type_id (+2 more)

### Community 77 - "student_status_course_comparison_metrics.json"
Cohesion: 0.20
Nodes (9): classification, course, status, dependencies, legacy_script_has_v2_imports, legacy_script_uses_v1_paths, student_course_depends_on_status_keys, student_status_depends_on_course_keys (+1 more)

### Community 78 - "student_level"
Cohesion: 0.20
Nodes (10): after_common_student_policy, rows, student_level, course, status, both, course, course_only (+2 more)

### Community 79 - "load_or_train_holdout"
Cohesion: 0.17
Nodes (9): Task 2: Regression tests, Recommendation report only, Static dependency and writer audit, load_or_train_holdout(), _json_default(), save_results(), test_save_results_preserves_parquet_and_json_outputs(), ExperimentCacheTests (+1 more)

### Community 80 - "trace_student_29485_20251.py"
Cohesion: 0.14
Nodes (4): save_json(), show(), table(), display()

### Community 81 - "تشغيل توصيات الخطط محلياً"
Cohesion: 0.25
Nodes (8): 1. قائمة المواد, 2. التشغيل من مجلد المشروع, 3. المودل والنتائج, 4. الاختبارات وقياس الأداء, 5. معادلة الترتيب وحدود الإعادات, 7. إعادة تشغيل المثال المحلي السابق, 8. الربط اللاحق بالـAPI, تشغيل توصيات الخطط محلياً

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

### Community 86 - "normalize_history_delta"
Cohesion: 0.20
Nodes (5): apply_history_delta(), _apply_normalized_delta(), _canonical_number(), HistoryDelta, normalize_history_delta()

### Community 87 - "F. Precomputed Serving State"
Cohesion: 0.40
Nodes (5): attempt_number: القرار المدعوم بالأدلة, F. Precomputed Serving State, GPA history: المتشابهات ليست مترادفات, observed_gap_semesters, Student totals و Leakage

### Community 88 - "توثيق Baseline قبل تنفيذ Recommendation Two-stage"
Cohesion: 0.25
Nodes (7): Full pytest, الفشل القديم capacity_63, توثيق Baseline قبل تنفيذ Recommendation Two-stage, سلامة البيانات والـArtifacts, مراجعة Git index قبل Commit, نطاق Commit والاستثناءات المحلية, نطاق هذه اللقطة

### Community 89 - "Model Artifact Isolation Audit Implementation Plan"
Cohesion: 0.29
Nodes (6): Execution notes, Global Constraints, Model Artifact Isolation Audit Implementation Plan, Review Focus, Task 1: Inventory and protections, Task 3: Policy and audit report

### Community 90 - "previous_course_status_inference.py"
Cohesion: 0.15
Nodes (11): score_courses_once(), write_json(), _attach_status(), _load_experimental_models(), pair_course_scores(), pair_plan_course_scores(), pair_plan_summaries(), _pair_scored_rows() (+3 more)

### Community 91 - "selected_candidate"
Cohesion: 0.57
Nodes (8): selected_candidate, selected_candidate, selected_candidate, selected_candidate, candidate, folds, mean_best_iteration, mean_primary_metric

### Community 92 - "feature_contract"
Cohesion: 0.50
Nodes (8): categorical_features, feature_count, model_features, numeric_features, removed_features, feature_contract, feature_contract, feature_contract

### Community 93 - "pandas"
Cohesion: 0.08
Nodes (8): cohort_counts(), main(), count(), main(), load_course_history_state(), main(), write_json(), empty_summaries()

### Community 94 - "inner_merge"
Cohesion: 0.25
Nodes (8): inner_merge, course_rows_after, course_rows_before, dropped_percentage, dropped_rows, students_after, students_before, students_completely_lost

### Community 95 - "Model Artifact Isolation Audit"
Cohesion: 0.25
Nodes (8): Auxiliary state, excluded from trained-model classification, Concise diff, Experiment results and cache, Final status, Inventory, Model Artifact Isolation Audit, Official baseline and provenance limitations, Verification

### Community 96 - "main"
Cohesion: 0.23
Nodes (12): دورة التدريب الأساسية — 9 عقد, _paired_metrics(), calibration_table(), classification_metrics(), _json_default(), _lightgbm(), main(), regression_metrics() (+4 more)

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

### Community 102 - "I. Semester Update Lifecycle"
Cohesion: 0.40
Nodes (5): Gaps يجب حلها قبل تغليف التدريب الحالي, I. Semester Update Lifecycle, التوصية أثناء 20261 غير المكتمل, بعد إغلاق الفصل أو وصول تصحيح, صلاحيات الأدمن والـ Jobs المقترحة

### Community 103 - "H. Frozen History Analysis"
Cohesion: 0.40
Nodes (4): H. Frozen History Analysis, التحقق، اكتمال المصدر والتصحيحات, المدخلات والمجاميع المخزنة, الملفات الموجودة فعليًا وحدودها

### Community 104 - "student_level"
Cohesion: 0.33
Nodes (6): student_level, both_students, course_only_students, course_students, status_only_students, status_students

### Community 105 - "مراجعة خصائص المودل — 2026-09-10"
Cohesion: 0.33
Nodes (5): التحقق, بقية الحسابات التي روجعت, حالة إعادة الإنتاج, ما تغيّر, مراجعة خصائص المودل — 2026-09-10

### Community 106 - "جدول تتبع تحسينات المودل"
Cohesion: 0.25
Nodes (6): 1. جميع النسخ المجربة, 2. الأثر المعزول لكل إضافة, 3. تحقق 2025 للنسخة الفائزة فقط, 4. القرار الحالي, جدول تتبع تحسينات المودل, حسب فصل 2025

### Community 108 - "artifacts"
Cohesion: 0.40
Nodes (5): category_levels, fail_model, grade_model, model_metadata, artifacts

### Community 109 - "training_weight"
Cohesion: 0.40
Nodes (5): training_weight, applied_only_during_fit, before_2022, fit_only, from_2022

### Community 110 - "enumerate_plan_indices"
Cohesion: 0.16
Nodes (5): 15. Plan Generation, enumerate_plan_indices(), visit(), EnumerationTests, PlanEnumerationTests

### Community 111 - "test_analyze_model_errors.py"
Cohesion: 0.23
Nodes (10): course_rows(), plan_rows(), test_build_plan_frame_attaches_context_and_year(), test_course_metrics(), test_course_segments_return_metrics_by_mark_and_missing_flags(), test_feature_family(), test_one_way_effect_size_uses_current_anova_formula(), test_plan_metrics_previous_gpa_coverage_and_boundaries() (+2 more)

### Community 112 - "test_recommendation_inputs_v2.py"
Cohesion: 0.13
Nodes (14): main(), parse_args(), SyntheticXmlEngine, test_local_loader_reads_only_cleaned_v2_and_preserves_history(), test_local_missing_v2_fails_without_legacy_fallback(), test_local_supplied_snapshot_reads_only_v2_catalog_and_attempts(), test_xml_missing_v2_fails_without_legacy_fallback(), test_xml_older_history_opt_in_applies_to_recommendation_and_observed_plan() (+6 more)

### Community 113 - "test_repeat_withdrawal_balance.py"
Cohesion: 0.16
Nodes (18): rows(), test_analysis_runner_preserves_inputs_and_rejects_existing_output(), test_available_credits_use_last_prior_not_current_credit_value(), test_conflicting_same_semester_attempts_are_rejected(), test_current_and_future_outcomes_cannot_change_previous_status(), test_decimal_and_zero_credit_courses_are_not_rounded(), test_exact_duplicates_are_reported_and_do_not_double_credits(), test_failed_repeated_and_not_repeated() (+10 more)

### Community 114 - "Academic Advisor — Architecture Map"
Cohesion: 0.22
Nodes (8): Academic Advisor — Architecture Map, Architecture Map, Current Architecture Status, Flows غير مثبتة, Important Boundaries, أكبر Technical Debt, نطاق الفحص وحدود التحقق, ProjectStage

### Community 115 - "D. Raw Data Sources"
Cohesion: 0.50
Nodes (4): D. Raw Data Sources, Schemas الفعلية كاملة, أمثلة Provenance من Raw إلى Model, ما أثبتته القيم الفعلية

### Community 116 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 117 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 118 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 119 - "HistorySnapshot"
Cohesion: 0.25
Nodes (4): Implementation Progress, Phase 1 — Artifacts & Contracts, Phase 3 — History Delta, Immutable Publication & Atomic State Swap, HistorySnapshot

### Community 120 - "B. Current Data Flow"
Cohesion: 0.67
Nodes (3): B. Current Data Flow, الوقت وتقليل Queries: القرار المقترح, متى نضيف Column إلى View؟

### Community 123 - "FrozenHistoryManager"
Cohesion: 0.25
Nodes (6): 02 — End-to-End Pipeline, Orchestration وحدود التشغيل, V1 وV2 مساران منفصلان, الفجوات المثبتة / حدود الإثبات, المسار الجزئي للـTwo-Stage, FrozenHistoryManager

### Community 127 - "importlib"
Cohesion: 0.32
Nodes (3): _import_targets(), test_production_packages_do_not_import_project_runner(), test_upstream_packages_do_not_import_recommendation()

### Community 128 - "`Phase 6 — تنفيذ Benchmark وعرض نتائج المرحلتين والمفاضلات لاعتماد الاستراتيجيات بصورة مستقلة.`"
Cohesion: 0.14
Nodes (14): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 2. قبل → بعد, 3. الملفات المنتجة أو المعدلة, 5. مخطط سير البيانات, 6. `Input → Processing → Output`, 7. كيف تم اختبار المرحلة؟ (+6 more)

### Community 129 - "CourseHistoryState"
Cohesion: 0.19
Nodes (10): C. Feature Engineering — 9 عقد, Constraints and review focus, Official Recommendation V2 Implementation Plan, Tasks, 4. أهم الملفات بالتفصيل المختصر, اليوم الأول: كيف تُبنى الخصائص — حوالي 4.5 ساعات, build_temporal_course_history(), CourseHistoryState (+2 more)

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
Cohesion: 0.13
Nodes (15): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 2. قبل → بعد, 3. الملفات المنتجة أو المعدلة, 5. مخطط سير البيانات, 6. `Input → Processing → Output`, 7. كيف تم اختبار المرحلة؟ (+7 more)

### Community 139 - "plan_explanation/README.md"
Cohesion: 0.18
Nodes (3): ءخريطة الملفات المهمة, مسارات متوقعة وغير منفذة, مكونات موجودة قبل الخطة ستستخدمها المراحل

### Community 140 - "`Phase 1 — Artifacts & Contracts`"
Cohesion: 0.18
Nodes (11): 10. المشاكل أو القيود المعروفة, 11. ماذا تستلم المرحلة التالية؟, 1. الفكرة العامة, 4. أهم الملفات بالتفصيل المختصر, 5. مخطط سير البيانات, 6. `Input → Processing → Output`, 7. كيف تم اختبار المرحلة؟, 8. أهم ما أثبتته المرحلة (+3 more)

### Community 143 - "06 — API Sequence"
Cohesion: 0.40
Nodes (5): 06 — API Sequence, B. Planned Integration — 7 أطراف, Flows لا يمكن إثباتها من الكود, دليل الموجود مقابل المخطط, فصل التحديث عن الطلب

### Community 144 - "C. 47 Feature Audit"
Cohesion: 0.29
Nodes (6): C. 47 Feature Audit, main(), enrichment_inputs(), test_main_builds_status_inner_join_and_auditable_plan_left_join(), test_main_rejects_many_to_many_enrichment_sources(), write_enrichment_inputs()

### Community 145 - "compute_plan_context_features"
Cohesion: 0.24
Nodes (6): المسار العام لـ`Two-Stage`, حدود القراءة الصحيحة للمخطط, مسار تحديث التاريخ المنفصل, 9. Feature Assembly, compute_plan_context_features(), PlanContextTests

### Community 146 - "clean_id_columns"
Cohesion: 0.16
Nodes (20): build_registration_roster(), main(), clean_degree_course(), main(), clean_column_names(), clean_id_columns(), extract_university_id(), to_float() (+12 more)

### Community 147 - "3. الملفات المنتجة أو المعدلة"
Cohesion: 0.40
Nodes (5): 3. الملفات المنتجة أو المعدلة, `Artifacts` ناتجة, `Generated / Auxiliary files`, ملفات جديدة, ملفات معدلة

### Community 148 - "evaluate_holdout"
Cohesion: 0.40
Nodes (4): _check_saved_baseline(), evaluate_holdout(), _predict(), _retake_sample()

### Community 150 - "prediction_contract"
Cohesion: 0.25
Nodes (8): clip, clip, expected_points_method, prediction_contract, fail, grade, reject_non_finite, reject_wrong_shape

### Community 152 - "شرح تنفيذ `Two-Stage Recommendation`"
Cohesion: 0.50
Nodes (4): أساس الحكم وحدود الأدلة, الفروق والقيود المهمة, شرح تنفيذ `Two-Stage Recommendation`, نطاق هذه المهمة

### Community 153 - "التحقق من التوصية بالتراكمي المتوقع والتاريخ المجمد"
Cohesion: 0.13
Nodes (13): 2. المدخلات والتاريخ والقيود, Frozen History, Hard constraints, Snapshot وCandidates, 5. Provenance contract, 6. نسخ Frozen Historical State, إعادة التشغيل على القوائم المحفوظة, التحقق الفعلي من النسختين (+5 more)

### Community 154 - "Data / Features V2 migration report — 2026-09-21"
Cohesion: 0.60
Nodes (4): Data / Features V2 migration report — 2026-09-21, build_temporal_split(), main(), summarize_split()

### Community 155 - "read.md"
Cohesion: 0.50
Nodes (3): الأولوية الحالية, اليوم الثاني: التدريب والتقييم — حوالي 4 ساعات, ملفات لا تعطيها وقتًا كبيرًا الآن

### Community 157 - "analyze_course_plan_changes.py"
Cohesion: 0.83
Nodes (3): main(), normalize_name(), print_table()

## Knowledge Gaps
- **677 isolated node(s):** `dataset_version`, `feature_engineering_version`, `grade_scale_sha256`, `grade_scale_version`, `path` (+672 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1106 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AcademicPlanRecommender` connect `AcademicPlanRecommender` to `Academic Advisor — ترشيح الخطة الفصلية عبر توقع العلامة ومخاطر الرسوب`, `paths.py`, `test_recommendation_v2.py`, `Production Contract — PHP ↔ Python Recommendation Service`, `feature_contract.py`, `course_only_evaluation.py`, `06 — API Sequence`, `explain_recommendation.py`, `render_recommendation_explanation.py`, `trace_student_29485_20251.py`, `numpy`, `pipeline_audit.py`, `evaluation/evaluate_xml_recommendations.py`, `previous_course_status_inference.py`, `inputs.py`, `pandas`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `GradeScale` connect `GradeScale` to `CourseHistoryState`, `analyze_model_errors.py`, `ابدأ من هنا — Academic Advisor`, `test_recommendation_v2.py`, `experiment_io.py`, `feature_contract.py`, ``Phase 1 — Artifacts & Contracts``, `numpy`, `degree_points.py`, `تشغيل توصيات الخطط محلياً`, `compute_plan_context_features`, `load_or_train_holdout`, `Recommendation Trace — Student 29485.111`, `pytest`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `prepare_model_matrix()` connect `prepare_model_matrix` to `CourseHistoryState`, `analyze_model_errors.py`, `Pre-Modeling Data V2 and Features V2 Audit`, `course_only_evaluation.py`, `numpy`, `explain_recommendation.py`, `compute_plan_context_features`, `evaluate_holdout`, `previous_course_status_training.py`, `inputs.py`, `pytest`, `feature_contract.py`, `AcademicPlanRecommender`, `Recommendation Trace — Student 29485.111`, `pipeline_audit.py`, `summarize_scored_plans`, `training_weights`, `trace_student_29485_20251.py`, `pandas`, `main`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `prepare_model_matrix()` (e.g. with `C. Feature Engineering — 9 عقد` and `Artifacts: من ينتجها ومن يستهلكها؟`) actually correct?**
  _`prepare_model_matrix()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `dataset_version`, `feature_engineering_version`, `grade_scale_sha256` to the rest of the system?**
  _677 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `paths.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08070175438596491 - nodes in this community are weakly interconnected._
- **Should `GradeScale` be split into smaller, more focused modules?**
  _Cohesion score 0.08853410740203194 - nodes in this community are weakly interconnected._