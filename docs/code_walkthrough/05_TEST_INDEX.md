# فهرس الاختبارات إلى الشفرة

الغرض العثور على الاختبار الذي يثبت سلوكًا عند قراءة ملف المصدر. لا يعيد هذا الفهرس شرح كل شفرة اختبار، ولا يدعي تنفيذًا جديدًا.

## ما الذي أحصي؟

تحت مجلد الاختبارات ستة وسبعون ملفًا وستمئة وواحد وسبعون تعريف دالة اختبار اسميًا. العدد الفعلي عند التشغيل مختلف بسبب المعاملات والاختبارات الفرعية وطريقة الجمع. توجد ثلاثة ملفات اختبار إضافية داخل تجربة تقدم الطالب، تحوي ثلاثة عشر تعريفًا، ومذكورة في فهرس الأدوات.

## آخر دليل تشغيل متاح

السجل المحلي السابق يذكر:


```text
1369 passed, 1 warning, 6 subtests passed in 269.59s
```

لم تُشغّل هذه المهمة الاختبارات. التحذير المسجل من عميل اختبار النقل؛ لا يتحول نجاح سجل سابق إلى إعلان جاهزية إنتاج أو اتصال جامعة.

[تقرير التنفيذ السابق](../../reports/api_cumulative_history.md)

الملف المحلي التفصيلي موجود لكنه غير أصل تشغيل للتطبيق:


```text
.pytest_cache/cumulative-api-audit/full-final.txt
```

## اختبارات يجب قراءتها أولًا

١. اتساق الطالب والمقام والحالة السابقة للمادة.

[الدلالات الأكاديمية](../../tests/test_api_academic_semantics.py)

[المحولات](../../tests/test_api_adapters.py)

٢. مرور الطلب في النواة بمصفوفتي الميزات والقيود.

[تكامل النواة](../../tests/test_api_integration.py)

[حد النقل والمصادقة](../../tests/test_api_http.py)

٣. ثبات التاريخ والتحديث والرجوع وفصل الإدارة.

[المجاميع](../../tests/test_history_update.py)

[المخزن الدائم](../../tests/test_cumulative_history.py)

[إدارة الواجهات](../../tests/test_api_history_admin.py)

٤. استقلال ترتيب المرحلتين والأصول والبحث الدقيق.

[اعتماد المرحلتين](../../tests/test_two_stage_activation.py)

[ترتيب الخطط](../../tests/test_ranking_strategies.py)

[محرك المرحلتين](../../tests/test_two_stage_engine.py)

## كيف تقرأ علاقة الاختبار؟

الرابط الآتي يستند إلى استيراد رمز أو وحدة أو نداء استيراد ديناميكي ثابت، ومعه بعض العلاقات غير المباشرة التي يبينها مسار الخدمة. عدم ذكر ملف لا يثبت غياب تغطية غير مباشرة. القضايا المعروضة مقتطفات من شروط فعلية، وليست تقارير نتيجة اجراها هذا الدليل.

<a id="test-1"></a>

## ملف الاختبار 1

```text
tests/__init__.py
```

[افتح الملف](../../tests/__init__.py)

لا علاقة داخلية مباشرة محسومة في الفهرس؛ قد يكون اختبار أداة أو حماية ملفات أو تجهيزًا مساعدًا.

لا دوال اختبار مسماة في هذا الملف؛ دوره تعريف حزمة أو عينات ومودلات اصطناعية.

<a id="test-2"></a>

## ملف الاختبار 2

```text
tests/api_fixtures.py
```

[افتح الملف](../../tests/api_fixtures.py)

صفحات المصدر المرتبطة:

- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)

لا دوال اختبار مسماة في هذا الملف؛ دوره تعريف حزمة أو عينات ومودلات اصطناعية.

<a id="test-3"></a>

## ملف الاختبار 3

```text
tests/recommendation_fixtures.py
```

[افتح الملف](../../tests/recommendation_fixtures.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)
- [المحرك المحلي ذو الزوج الواحد](recommendation/engine.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)

لا دوال اختبار مسماة في هذا الملف؛ دوره تعريف حزمة أو عينات ومودلات اصطناعية.

<a id="test-4"></a>

## ملف الاختبار 4

```text
tests/test_academic_calendar.py
```

[افتح الملف](../../tests/test_academic_calendar.py)

صفحات المصدر المرتبطة:

- [رزنامة الفصول والفجوات](data/academic_calendar.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_regular_semesters_between
test_is_regular_semester
test_is_regular_semester_rejects_invalid_part_id
test_count_regular_semesters_between_rejects_invalid_part_id
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_regular_semesters_between
```


```python
assert count_regular_semesters_between(previous, current) == expected
```

<a id="test-5"></a>

## ملف الاختبار 5

```text
tests/test_analyze_model_errors.py
```

[افتح الملف](../../tests/test_analyze_model_errors.py)

صفحات المصدر المرتبطة:

- [تحليل أخطاء النموذج زمنيًا وبحسب المجموعات](evaluation/analyze_model_errors.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_modeling_does_not_import_evaluation
test_course_metrics
test_plan_metrics_previous_gpa_coverage_and_boundaries
test_selected_fold_iterations
test_build_plan_frame_attaches_context_and_year
test_year_degree_and_year_degree_analyses_keep_grouping_and_support
test_plan_segments_use_existing_gpa_and_count_bands
test_course_segments_return_metrics_by_mark_and_missing_flags
test_feature_family
test_one_way_effect_size_uses_current_anova_formula
test_build_shap_importance_uses_absolute_contributions_and_family_sums
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_modeling_does_not_import_evaluation
```


```python
assert all((not alias.name.startswith('src.evaluation') for alias in node.names))
```

<a id="test-6"></a>

## ملف الاختبار 6

```text
tests/test_api_academic_semantics.py
```

[افتح الملف](../../tests/test_api_academic_semantics.py)

صفحات المصدر المرتبطة:

- [تطبيع المواد والأهلية والقيود](api/courses_adapter.md)
- [عقود أجسام الطلبات](api/schemas.md)
- [الإعدادات ومصادرها البيئية](api/settings.md)
- [تحويل الطالب إلى لقطة بداية الفصل](api/student_adapter.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [توحيد الحالة السابقة ومجموعة المادة](recommendation/course_status.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_official_beginning_total_supplies_gpa_denominator_and_existing_feature
test_official_beginning_total_preserves_training_feature_definition
test_official_total_rejects_conflicting_sourced_supplement
test_post_semester_total_129_does_not_silently_subtract_registered_18
test_post_semester_denominator_requires_complete_additive_authoritative_count
test_post_semester_derivation_honors_confirmed_exclusions
test_post_semester_derivation_rejects_missing_finalization_or_rules
test_official_total_rejects_wrong_snapshot_or_unverified_semantics
test_derived_gpa_count_cannot_exceed_registered_or_cumulative_count
test_unattested_totals_and_completed_credits_never_supply_denominator
test_missing_official_total_requires_sourced_override
test_legacy_sourced_override_keeps_separate_model_feature_provenance
test_legacy_credit_snapshot_cannot_be_stale_for_target
test_zero_previous_attempts_and_null_finish_status_are_new_without_supplement
test_repeated_course_uses_official_previous_status_without_supplement
test_repeat_missing_status_is_invalid_and_never_inferred_from_attempts
test_repeat_missing_status_accepts_authoritative_prior_ledger
test_zero_attempts_conflicting_previous_outcome_is_rejected
test_repeated_course_conflicting_official_and_supplemental_status_rejected
test_unresolved_official_status_cannot_enable_repeat
test_repeat_target_or_future_registration_status_is_rejected
test_matching_official_and_supplemental_status_preserves_canonical_mapping
test_typed_http_contract_accepts_official_total_evidence_and_rejects_string_bool
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_official_beginning_total_supplies_gpa_denominator_and_existing_feature
```


```python
assert result.errors == []
```

<a id="test-7"></a>

## ملف الاختبار 7

```text
tests/test_api_adapters.py
```

[افتح الملف](../../tests/test_api_adapters.py)

صفحات المصدر المرتبطة:

- [المعاينة التشخيصية لدفعة التاريخ](api/history_adapter.md)
- [تنسيق التحقق والتوصية والإدارة](api/service.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.api.service
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_complete_student_uses_previous_gpa_and_explicit_denominator
test_actual_sanitized_student_reports_missing_diploma_and_denominator
test_independent_source_bindings_reject_wrong_identity
test_target_outcomes_never_enter_snapshot
test_all_17_courses_and_attempt_conversion_preserve_group_identity
test_invalid_attempt_count_rejected
test_identical_duplicates_removed_conflicts_rejected
test_invalid_identity_is_checked_before_ineligible_filtering
test_validation_independent_of_models_history_and_missing_catalog
test_status_and_exception_information_are_not_inferred
test_duplicate_conflicting_eligibility_cannot_disappear_during_filtering
test_matching_decimal_denominator_sources_do_not_conflict_after_float_conversion
test_conflicting_historical_semester_aliases_rejected
test_student_root_identity_is_checked_as_well_as_degree_info
test_complete_schema_rejects_invalid_previous_gpa_and_fractional_counter
test_response_wrapper_identity_cannot_conflict_with_data
test_count_outside_model_float_range_is_input_error
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_complete_student_uses_previous_gpa_and_explicit_denominator
```


```python
assert result.errors == []
```

<a id="test-8"></a>

## ملف الاختبار 8

```text
tests/test_api_backend_client.py
```

[افتح الملف](../../tests/test_api_backend_client.py)

صفحات المصدر المرتبطة:

- [الجلب المباشر الاختياري للاختبار](api/backend_client.md)
- [الإعدادات ومصادرها البيئية](api/settings.md)
- [أدوات الهوية والأرقام والتشخيص الآمن](api/validation.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_php_push_remains_default_and_pull_requires_explicit_configuration
test_environment_urls_timeout_and_courses_parameters
test_unsafe_endpoint_configuration_is_rejected
test_client_uses_actual_student_parameters_and_configured_courses_parameters
test_rebinding_to_private_address_is_blocked_before_transport
test_redirects_and_upstream_errors_never_leak_body
test_local_http_requires_explicit_loopback_testing_mode
test_tls_connection_pins_validated_ip_and_preserves_original_server_name
test_mixed_public_and_private_dns_answers_are_rejected
test_multicast_dns_address_is_rejected_before_transport
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_php_push_remains_default_and_pull_requires_explicit_configuration
```


```python
assert ApiSettings().direct_fetch_enabled is False
```

<a id="test-9"></a>

## ملف الاختبار 9

```text
tests/test_api_core_extensions.py
```

[افتح الملف](../../tests/test_api_core_extensions.py)

صفحات المصدر المرتبطة:

- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [القيود الأكاديمية على الخطط](recommendation/constraints.md)
- [مجاميع الدفعات ومدير اللقطة](recommendation/history_update.md)
- [المحرك المعتمد ذو المرحلتين](recommendation/two_stage_engine.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_requirement_groups_do_not_merge_by_model_category
test_max_new_courses_is_an_optional_plan_constraint
test_exact_history_selection_and_explicit_backtesting
test_delta_preview_never_publishes_or_claims_finalization
test_partial_summary_reuses_original_gpa_shift_and_nonregistered_semesters
test_loaded_artifact_factory_enforces_approval_without_reloading
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_requirement_groups_do_not_merge_by_model_category
```


```python
assert list(enumerate_feasible_plan_indices(candidates, constraints)) == [(0, 1, 3), (0, 2, 3), (1, 2, 3)]
```

<a id="test-10"></a>

## ملف الاختبار 10

```text
tests/test_api_cumulative_integration.py
```

[افتح الملف](../../tests/test_api_cumulative_integration.py)

صفحات المصدر المرتبطة:

- [إنشاء تطبيق الواجهات والمصادقة](api/app.md)
- [تنسيق التحقق والتوصية والإدارة](api/service.md)
- [الإعدادات ومصادرها البيئية](api/settings.md)
- [أدوات الهوية والأرقام والتشخيص الآمن](api/validation.md)
- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [المحرك المعتمد ذو المرحلتين](recommendation/two_stage_engine.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_http_migration_manual_auto_rollback_and_existing_pareto_contract
test_missing_artifacts_block_migration_but_http_validation_remains_available
test_specialty_feature_requirement_rejects_update_before_publication
test_worker_started_before_migration_adopts_shared_active_pointer
test_corrupt_active_pointer_preserves_independent_diagnostics
test_read_only_delta_validation_rejects_skipped_semester_without_writing
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_http_migration_manual_auto_rollback_and_existing_pareto_contract
```


```python
assert status['active_as_of_part'] == 20251
```

<a id="test-11"></a>

## ملف الاختبار 11

```text
tests/test_api_history_admin.py
```

[افتح الملف](../../tests/test_api_history_admin.py)

صفحات المصدر المرتبطة:

- [إنشاء تطبيق الواجهات والمصادقة](api/app.md)
- [تنسيق التحقق والتوصية والإدارة](api/service.md)
- [الإعدادات ومصادرها البيئية](api/settings.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_admin_status_and_durable_mode_workflow
test_service_credentials_cannot_access_administration
test_manual_preview_commit_and_activation_are_separate
test_finalization_event_has_its_own_authorized_credential
test_confirmation_and_finalization_proof_are_required_before_writing
test_request_cannot_supply_a_history_source_path_or_backend_url
test_baseline_requires_explicit_cumulative_history_attestation
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_admin_status_and_durable_mode_workflow
```


```python
assert response.status_code == 200
```

<a id="test-12"></a>

## ملف الاختبار 12

```text
tests/test_api_http.py
```

[افتح الملف](../../tests/test_api_http.py)

صفحات المصدر المرتبطة:

- [إنشاء تطبيق الواجهات والمصادقة](api/app.md)
- [المعاينة التشخيصية لدفعة التاريخ](api/history_adapter.md)
- [تنسيق التحقق والتوصية والإدارة](api/service.md)
- [الإعدادات ومصادرها البيئية](api/settings.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.api.app
src.api.service
src.api.settings
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_http_health_and_validators_survive_unready_models_and_history
test_http_context_conflicts_make_zero_engine_calls
test_missing_courses_context_and_payload_identity_conflict_stop_inference
test_performance_limit_is_configurable_and_never_truncates_validation
test_config_limit_applies_only_in_test_mode
test_stale_cutoff_requires_both_explicit_and_enabled_backtesting
test_target_history_and_training_cutoff_forbidden
test_admin_delta_validation_is_partial_without_history_and_never_publishes
test_auth_keys_errors_and_sensitive_inputs_never_echoed
test_credit_bounds_use_actual_upper_intersection
test_http_numeric_literals_keep_decimal_precision
test_invalid_structured_eligibility_is_422_not_server_error
test_runtime_exception_does_not_escape_to_server_logs
test_invalid_target_status_key_is_422
test_missing_exact_bundle_is_503_with_no_fallback
test_empty_candidates_return_no_feasible_plan_with_actual_core
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_http_health_and_validators_survive_unready_models_and_history
```


```python
assert health['api_health'] == 'healthy'
```

<a id="test-13"></a>

## ملف الاختبار 13

```text
tests/test_api_integration.py
```

[افتح الملف](../../tests/test_api_integration.py)

صفحات المصدر المرتبطة:

- [المعاينة التشخيصية لدفعة التاريخ](api/history_adapter.md)
- [تنسيق التحقق والتوصية والإدارة](api/service.md)
- [الإعدادات ومصادرها البيئية](api/settings.md)
- [أدوات الهوية والأرقام والتشخيص الآمن](api/validation.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [مجاميع الدفعات ومدير اللقطة](recommendation/history_update.md)
- [المحرك المعتمد ذو المرحلتين](recommendation/two_stage_engine.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_api_calls_actual_core_with_33_and_47_features_and_group_caps
test_original_gpa_calculation_and_helper_are_identical_on_full_schema
test_all_history_identity_rows_checked_even_when_first_schema_incomplete
test_supplement_conflict_with_original_beginning_fail_total_is_rejected
test_nonregistered_semesters_preserve_gpa_and_current_gap
test_future_supplement_and_history_rejected_before_models
test_missing_optional_max_new_does_not_invent_a_limit
test_independent_startup_load_failures_and_import_without_http_dependencies
test_delta_replay_conflict_and_validation_never_changes_bundle
test_delta_aggregates_equal_individual_outcomes_without_estimated_points
test_contract_nullable_history_remains_unknown_and_response_is_explicit
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_api_calls_actual_core_with_33_and_47_features_and_group_caps
```


```python
assert result['status'] == 'ok'
```

<a id="test-14"></a>

## ملف الاختبار 14

```text
tests/test_attempt_number_experiment.py
```

[افتح الملف](../../tests/test_attempt_number_experiment.py)

صفحات المصدر المرتبطة:

- [أدوات تجربة رقم المحاولة](experiments/attempt_number_core.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_transform_keeps_other_columns_order_categories_and_input
test_unknown_or_invalid_attempt_cannot_become_first_attempt
test_row_fingerprint_detects_order_and_membership_changes
test_cluster_bootstrap_resamples_students_and_retains_all_their_rows
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_transform_keeps_other_columns_order_categories_and_input
```


```python
assert binary.columns.tolist() == ['x', 'is_repeat', 'cat']
```

<a id="test-15"></a>

## ملف الاختبار 15

```text
tests/test_balance_policy.py
```

[افتح الملف](../../tests/test_balance_policy.py)

صفحات المصدر المرتبطة:

- [مكونات التوازن الناعم](recommendation/balance_policy.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_exact_policy_is_versioned_and_has_no_new_quota
test_separate_credit_denominators_and_penalties
test_exact_band_boundaries_have_zero_distance
test_distance_on_both_sides_is_soft
test_reference_scope_accepts_fractional_inclusive_loads
test_outside_scope_has_no_artificial_zero_penalty
test_only_positive_eligible_candidates_activate_components
test_zero_credit_members_affect_identity_and_scope_but_not_credit_ratios
test_candidate_permutation_preserves_metrics_and_input_frames
test_invalid_credits_are_rejected
test_sum_of_finite_credits_that_overflows_output_is_rejected
test_incomplete_or_inconsistent_plan_input_is_rejected
test_local_policy_matches_saved_descriptive_bands_without_runtime_report_io
test_observed_aggregate_mixes_with_synthetic_ids_have_correct_ratios_and_penalties
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_exact_policy_is_versioned_and_has_no_new_quota
```


```python
assert policy.version == 'B_observed_middle_v1'
```

<a id="test-16"></a>

## ملف الاختبار 16

```text
tests/test_build_registration_roster.py
```

[افتح الملف](../../tests/test_build_registration_roster.py)

صفحات المصدر المرتبطة:

- [إنشاء سجل التسجيل الكامل](data/build_registration_roster.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_build_registration_roster_keeps_only_registered_or_enrolled
test_build_registration_roster_joins_exact_status_removes_outliers_and_keeps_plan_gaps
test_main_writes_full_train_and_test_rosters
test_duplicate_merge_keys_raise_instead_of_multiplying_rows
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_build_registration_roster_keeps_only_registered_or_enrolled
```


```python
assert len(result) == expected_rows
```

<a id="test-17"></a>

## ملف الاختبار 17

```text
tests/test_build_student_course_enriched.py
```

[افتح الملف](../../tests/test_build_student_course_enriched.py)

صفحات المصدر المرتبطة:

- [ربط النتائج بحالة الطالب والخطة](data/build_student_course_enriched.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_main_builds_status_inner_join_and_auditable_plan_left_join
test_main_rejects_many_to_many_enrichment_sources
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_main_builds_status_inner_join_and_auditable_plan_left_join
```


```python
assert result['student_course_id'].tolist() == ['SC1', 'SC2']
```

<a id="test-18"></a>

## ملف الاختبار 18

```text
tests/test_clean_degree_course.py
```

[افتح الملف](../../tests/test_clean_degree_course.py)

صفحات المصدر المرتبطة:

- [تنظيف كتالوج الاختصاص](data/clean_degree_course.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_clean_degree_course_normalizes_contract_and_stable_order
test_clean_degree_course_rejects_missing_required_columns
test_main_writes_the_clean_degree_course_artifact
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_clean_degree_course_normalizes_contract_and_stable_order
```


```python
assert result.columns.tolist() == degree_course_module.FINAL_COLUMNS
```

<a id="test-19"></a>

## ملف الاختبار 19

```text
tests/test_clean_outliers.py
```

[افتح الملف](../../tests/test_clean_outliers.py)

صفحات المصدر المرتبطة:

- [تدقيق القيم المتطرفة واستبعاد الطلاب](data/clean_outliers.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_validate_columns_names_every_missing_requirement
test_summarize_rule_aggregates_repeated_triggers_per_student
test_build_outlier_audit_applies_each_status_upper_limit
test_build_outlier_audit_rejects_negative_status_totals
test_build_outlier_audit_checks_both_gpa_boundaries
test_build_outlier_audit_checks_course_level_ranges
test_build_outlier_audit_checks_logical_consistency
test_build_outlier_audit_checks_status_once_but_courses_per_record
test_build_outlier_audit_accepts_valid_24_credit_course
test_remove_outlier_students_removes_every_row_for_flagged_students
test_main_writes_clean_rows_and_outlier_audit
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_summarize_rule_aggregates_repeated_triggers_per_student
```


```python
assert result['student_id'].tolist() == ['S1']
```

<a id="test-20"></a>

## ملف الاختبار 20

```text
tests/test_clean_student_course.py
```

[افتح الملف](../../tests/test_clean_student_course.py)

صفحات المصدر المرتبطة:

- [تنظيف نتائج المواد وتكوين المحاولات](data/clean_student_course.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_clean_student_course_basic_contract_and_input_immutability
test_registration_status_is_normalized_before_filtering
test_finish_status_map_normalizes_and_maps_current_codes
test_unsupported_finish_statuses_are_currently_removed
test_attempts_are_numbered_per_student_and_course_after_chronological_sort
test_duplicate_student_course_semester_raises_value_error
test_withdrawn_counts_as_attempt_before_removal
test_semester_cutoff_is_strictly_greater_than_20193
test_all_course_id_columns_use_safe_id_normalization
test_missing_required_key_raises_value_error
test_missing_critical_key_excludes_only_that_row
test_both_critical_keys_missing_on_same_row_yields_empty_clean_frame
test_duplicate_student_course_id_raises_value_error
test_numeric_fields_are_converted_to_current_nullable_dtypes
test_invalid_numeric_input_keeps_current_conversion_failure
test_text_fields_are_trimmed
test_any_exclusion_flag_n_removes_the_course
test_deterministic_ordering_is_independent_of_source_order
test_raw_and_internal_columns_are_removed_but_outcome_remains
test_empty_result_is_a_dataframe_with_current_output_schema
test_main_persists_the_same_cleaning_result_to_a_created_directory
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_clean_student_course_basic_contract_and_input_immutability
```


```python
assert result.index.tolist() == [0]
```

<a id="test-21"></a>

## ملف الاختبار 21

```text
tests/test_clean_student_diploma.py
```

[افتح الملف](../../tests/test_clean_student_diploma.py)

صفحات المصدر المرتبطة:

- [تنظيف الدبلوم وربطه بالطالب](data/clean_student_diploma.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_clean_student_diploma_groups_rare_types_and_fills_gpa
test_clean_student_diploma_rejects_broken_input_contract
test_merge_student_course_with_diploma_preserves_unmatched_courses
test_merge_student_course_with_diploma_rejects_ambiguous_features
test_main_writes_clean_and_merged_diploma_artifacts
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_clean_student_diploma_groups_rare_types_and_fills_gpa
```


```python
assert result.columns.tolist() == diploma_module.FINAL_COLUMNS
```

<a id="test-22"></a>

## ملف الاختبار 22

```text
tests/test_clean_student_status.py
```

[افتح الملف](../../tests/test_clean_student_status.py)

صفحات المصدر المرتبطة:

- [تنظيف الحالة وتاريخ التسجيل](data/clean_student_status.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_add_enrollment_features_tracks_only_observed_history
test_observed_gap_counts_regular_semesters_between_enrollments
test_optional_non_enrollment_does_not_increase_gap
test_semester_four_is_excluded_before_enrollment_history
test_only_semester_four_rows_produce_empty_clean_status
test_other_invalid_semesters_remain_strict
test_enrolled_optional_semester_updates_last_enrolled_gpa
test_business_filters_remove_only_the_matching_row
test_every_excluded_permanent_status_id_is_filtered
test_filtered_row_still_supplies_prior_enrollment_history
test_clean_student_status_preserves_columns_and_normalizes_ids_and_text
test_part_id_cutoff_still_excludes_20193
test_main_reads_only_status_and_writes_complete_clean_status
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_add_enrollment_features_tracks_only_observed_history
```


```python
assert pd.isna(actual_gpa) if expected_gpa is None else actual_gpa == expected_gpa
```

<a id="test-23"></a>

## ملف الاختبار 23

```text
tests/test_clean_utils.py
```

[افتح الملف](../../tests/test_clean_utils.py)

صفحات المصدر المرتبطة:

- [أدوات تنظيف الأعمدة والمعرفات](data/cleaning_utils.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_clean_column_names_normalizes_whitespace_without_mutating_input
test_clean_id_preserves_meaningful_dots_and_normalizes_nulls
test_clean_id_columns_cleans_multiple_selected_columns_and_copies_input
test_extract_university_id_extracts_after_final_dot_without_inventing_validation
test_to_integer_converts_numeric_inputs_to_nullable_int64
test_to_float_converts_numeric_and_decimal_inputs_to_nullable_float64
test_numeric_converters_keep_current_invalid_value_failure
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_clean_column_names_normalizes_whitespace_without_mutating_input
```


```python
assert result.columns.tolist() == ['final_mark', 'student_id', 'course_name_sl']
```

<a id="test-24"></a>

## ملف الاختبار 24

```text
tests/test_corrected_phase6_evaluation.py
```

[افتح الملف](../../tests/test_corrected_phase6_evaluation.py)

صفحات المصدر المرتبطة:

- [مكونات التوازن الناعم](recommendation/balance_policy.md)
- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_recall_has_independent_top_k_denominator_and_explicit_lost_ids
test_no_solution_recall_is_not_reported_as_perfect_retention
test_recall_at50_cannot_be_inflated_by_larger_shortlist
test_recall_rejects_duplicate_plan_ids
test_fixed_final_pool_and_all_four_pairs_use_identical_scored_metrics
test_fixed_pool_rejects_nonfinite_metrics
test_evaluator_never_silently_accepts_unsupported_grade_version
test_explicit_grade_version_must_be_finite_supported_and_nonboolean
test_explicit_supported_grade_version_is_recorded_with_category_coverage
test_offline_oracle_bound_refuses_large_fixture_without_stage2_inference
test_no_solution_fixture_skips_stage2_and_does_not_invent_comparisons
test_summary_keeps_recommendation_separate_from_approval
test_exact_objective_ties_are_additional_sensitivity_not_identity_recall
test_disabled_balance_distances_remain_missing_in_distributions
test_summary_determinism_requires_every_actual_check
test_skipped_candidate_permutation_is_explicitly_unverified
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_recall_has_independent_top_k_denominator_and_explicit_lost_ids
```


```python
assert evidence == {'k': 3, 'denominator': 3, 'retained_count': 2, 'recall_at_50': 2 / 3, 'oracle_plan_ids': ['P0', 'P1', 'P2'], 'lost_plan_ids': ['P1']}
```

<a id="test-25"></a>

## ملف الاختبار 25

```text
tests/test_corrected_phase6_rerun.py
```

[افتح الملف](../../tests/test_corrected_phase6_rerun.py)

لا علاقة داخلية مباشرة محسومة في الفهرس؛ قد يكون اختبار أداة أو حماية ملفات أو تجهيزًا مساعدًا.

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_every_nonsearch_row_is_invalidated_including_timeout_and_duplicate_batch
test_jobs_preserve_old_independent_choices_and_each_observations_deadline
test_completed_replacements_must_match_job_and_prove_supported_grade_version
test_old_metric_values_are_never_in_the_corrected_aggregate
test_incomplete_or_duplicate_replacement_set_is_rejected
test_old_files_remain_byte_identical_and_archive_is_separate
test_resume_rejects_changed_context_and_preserves_original_baseline
test_completion_rejects_changed_worker_source
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_every_nonsearch_row_is_invalidated_including_timeout_and_duplicate_batch
```


```python
assert inventory['retained_search_indices'] == [0]
```

<a id="test-26"></a>

## ملف الاختبار 26

```text
tests/test_course_only_recommendation.py
```

[افتح الملف](../../tests/test_course_only_recommendation.py)

صفحات المصدر المرتبطة:

- [حساب البحث على ميزات المادة فقط](experiments/course_only_core.md)
- [مقارنة تجربة المادة بالمحرك المحلي](experiments/course_only_evaluation.md)
- [تدريب تجربة المواد المستقلة](experiments/course_only_training.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.experiments.course_only_core
src.experiments.course_only_evaluation
src.experiments.course_only_training
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_course_matrix_does_not_need_plan_context_and_retains_unknown_categories
test_exact_search_uses_every_candidate_and_risk_then_course_order_for_ties
test_fractional_credit_search_and_zero_credit_optional_courses
test_top_k_matches_independent_bruteforce_and_is_input_order_invariant
test_optimizer_rejects_invalid_scores
test_sensitivity_uses_population_std_and_course_sets_ignore_plan_ids
test_scoring_predicts_each_candidate_once_and_clips_before_grade_conversion
test_training_folds_keep_official_temporal_cutoffs_weights_and_33_columns
test_official_rescore_lookup_uses_hashable_course_sets_for_arrow_strings
test_course_rows_reject_target_or_future_training_history_and_stale_history
test_complete_comparison_preserves_same_request_scores_and_official_rescoring
test_protection_preflight_preserves_original_hashes_and_detects_later_changes
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_course_matrix_does_not_need_plan_context_and_retains_unknown_categories
```


```python
assert matrix.shape == (2, 33)
```

<a id="test-27"></a>

## ملف الاختبار 27

```text
tests/test_cumulative_history.py
```

[افتح الملف](../../tests/test_cumulative_history.py)

صفحات المصدر المرتبطة:

- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [الإدارة الدائمة للتاريخ التراكمي](recommendation/cumulative_history.md)
- [مجاميع الدفعات ومدير اللقطة](recommendation/history_update.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.recommendation.cumulative_history
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_lazy_defaults_and_persistent_modes
test_approved_initialization_preserves_full_weighted_history_and_source
test_initialization_requires_exact_approved_cumulative_prefix
test_preview_commit_activation_separate_and_sequential_raw_equivalence
test_confirmation_binds_hash_and_base_and_prevents_conflicting_replay
test_manual_automatic_and_disabled_workflows
test_failed_publication_and_compatibility_preserve_active_history
test_rollback_exact_selection_and_reload_do_not_delete_later_versions
test_concurrent_preview_confirmations_do_not_duplicate_version
test_serving_proxy_pins_requests_and_readonly_validation_preserves_pending
test_exact_older_legacy_backtesting_version_remains_accessible
test_missing_serving_compatibility_allows_partial_preview_but_blocks_publication
test_activation_hash_and_rollback_confirmation_are_checked
test_disabled_blocks_initialization_and_overlapping_roots_are_rejected
test_cross_process_lock_is_exclusive_and_released_on_process_exit
test_single_semester_baseline_cannot_be_misrepresented_as_cumulative
test_specialty_requirement_and_missing_points_are_not_fabricated
test_corrupted_control_or_active_hash_never_selects_a_different_version
test_failed_atomic_pointer_replace_preserves_previous_active_version
test_unactivated_committed_history_cannot_be_selected_explicitly
test_normal_capture_after_rollback_cannot_bypass_active_pointer
test_preexisting_bundle_without_activation_record_cannot_be_served
test_readonly_proxy_rejects_skipped_semester_without_changing_control
test_baseline_retry_adopts_exact_verified_bundle_after_pointer_failure
test_baseline_retry_rejects_conflicting_approval_or_source_without_overwrite
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_lazy_defaults_and_persistent_modes
```


```python
assert not root.exists()
```

<a id="test-28"></a>

## ملف الاختبار 28

```text
tests/test_degree_points_config.py
```

[افتح الملف](../../tests/test_degree_points_config.py)

صفحات المصدر المرتبطة:

- [تنسيق تجربة أهداف النقاط والاختصاص](experiments/degree_points.md)
- [إعداد تجربة الاختصاص والنقاط](experiments/degree_points_config.md)
- [ملفات تجربة الاختصاص ومصدرها](experiments/experiment_io.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_experiment_configuration_preserves_folds_and_variants
test_experiment_modules_import_without_running_experiment
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_experiment_configuration_preserves_folds_and_variants
```


```python
assert BASELINE_VARIANT == 'baseline_mark_temporal'
```

<a id="test-29"></a>

## ملف الاختبار 29

```text
tests/test_degree_points_experiment.py
```

[افتح الملف](../../tests/test_degree_points_experiment.py)

صفحات المصدر المرتبطة:

- [خوارزميات ملاءمة التجارب وتقييمها](experiments/modeling.md)
- [تاريخ الاختصاص التجريبي](experiments/specialty_history.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_changing_current_or_future_labels_changes_no_earlier_features
test_frozen_history_rejects_overlap_with_test_semester
test_current_part_does_not_enter_its_own_specialty_history
test_later_test_part_includes_only_prior_test_outcomes
test_credit_weight_multiplies_temporal_weight
```

<a id="test-30"></a>

## ملف الاختبار 30

```text
tests/test_evaluate_plan_gpa.py
```

[افتح الملف](../../tests/test_evaluate_plan_gpa.py)

صفحات المصدر المرتبطة:

- [تقييم معدل الخطط المرصودة](evaluation/evaluate_plan_gpa.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_predict_course_points_preserves_audit_and_quality_points
test_aggregate_plan_gpa_uses_student_degree_part_and_credit_weighting
test_summarize_plan_errors_includes_threshold_boundaries
test_build_metrics_report_preserves_contract_and_parts
test_import_does_not_run_evaluation
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_predict_course_points_preserves_audit_and_quality_points
```


```python
assert not {'final_mark', 'points', 'gpa_points'} & set(result)
```

<a id="test-31"></a>

## ملف الاختبار 31

```text
tests/test_evaluation_v2_io.py
```

[افتح الملف](../../tests/test_evaluation_v2_io.py)

صفحات المصدر المرتبطة:

- [تحليل أخطاء النموذج زمنيًا وبحسب المجموعات](evaluation/analyze_model_errors.md)
- [تقييم معدل الخطط المرصودة](evaluation/evaluate_plan_gpa.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [مرجع المسارات والإصدارات](paths.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_plan_evaluation_reads_and_writes_v2_with_shared_grade_scale
test_error_analysis_uses_v2_in_historical_holdout_and_shap_paths
test_missing_v2_input_fails_without_v1_fallback_or_output
test_direct_import_resolves_v2_and_intentionally_shared_scale
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_plan_evaluation_reads_and_writes_v2_with_shared_grade_scale
```


```python
assert reads == [versioned['MODEL_METADATA_PATH'], versioned['TEMPORAL_TEST_FEATURES_PATH'], versioned['GRADE_MODEL_PATH'], versioned['CATEGORY_LEVELS_PATH'], scale]
```

<a id="test-32"></a>

## ملف الاختبار 32

```text
tests/test_experiment_io.py
```

[افتح الملف](../../tests/test_experiment_io.py)

صفحات المصدر المرتبطة:

- [إعداد تجربة الاختصاص والنقاط](experiments/degree_points_config.md)
- [ملفات تجربة الاختصاص ومصدرها](experiments/experiment_io.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [مرجع المسارات والإصدارات](paths.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_signature_hashes_current_dependencies_deterministically
test_validation_cache_reuses_only_matching_signature
test_metadata_retains_protocol_and_artifact_contract
test_save_results_preserves_parquet_and_json_outputs
test_base_modeling_package_has_no_experiment_imports
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_signature_hashes_current_dependencies_deterministically
```


```python
assert experiment_io.experiment_signature() == expected
```

<a id="test-33"></a>

## ملف الاختبار 33

```text
tests/test_experiments_v2_io.py
```

[افتح الملف](../../tests/test_experiments_v2_io.py)

صفحات المصدر المرتبطة:

- [تنسيق تجربة أهداف النقاط والاختصاص](experiments/degree_points.md)
- [إعداد تجربة الاختصاص والنقاط](experiments/degree_points_config.md)
- [ملفات تجربة الاختصاص ومصدرها](experiments/experiment_io.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [مرجع المسارات والإصدارات](paths.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_coordinator_uses_v2_baseline_cache_outputs_and_metadata_candidate
test_missing_v2_input_fails_without_using_v1
test_path_constants_are_v2_and_grade_scale_is_shared
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_coordinator_uses_v2_baseline_cache_outputs_and_metadata_candidate
```


```python
assert all((versioned[name].is_file() for name in OUTPUTS))
```

<a id="test-34"></a>

## ملف الاختبار 34

```text
tests/test_feature_contract_responsibilities.py
```

[افتح الملف](../../tests/test_feature_contract_responsibilities.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [الأهداف وأوزان التدريب](modeling/training_config.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_saved_training_levels_keep_unseen_serving_values_unknown
test_base_matrix_preserves_schema_and_category_handling
test_modeling_targets_and_training_weights_preserve_values
```

<a id="test-35"></a>

## ملف الاختبار 35

```text
tests/test_feature_pipeline.py
```

[افتح الملف](../../tests/test_feature_pipeline.py)

صفحات المصدر المرتبطة:

- [تنسيق تجربة أهداف النقاط والاختصاص](experiments/degree_points.md)
- [ملفات تجربة الاختصاص ومصدرها](experiments/experiment_io.md)
- [تاريخ الاختصاص التجريبي](experiments/specialty_history.md)
- [تجميع ملفات ميزات التدريب](features/build_temporal_features.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_poisoning_current_and_future_outcomes_leaves_all_features_unchanged
test_feature_version_survives_parquet_projection_and_rejects_old_models
test_validation_cache_rejects_old_or_different_feature_data
test_changed_features_force_holdout_retraining
```

<a id="test-36"></a>

## ملف الاختبار 36

```text
tests/test_filter_common_students.py
```

[افتح الملف](../../tests/test_filter_common_students.py)

صفحات المصدر المرتبطة:

- [مزامنة مجموعة الطلاب](data/filter_common_students.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_keeps_only_students_present_in_both_tables
test_keeps_all_rows_for_common_student_despite_different_parts_and_degrees
test_does_not_modify_inputs_in_place
test_stage_reads_pre_common_and_writes_filtered_v2
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_keeps_only_students_present_in_both_tables
```


```python
assert filtered_status.student_id.tolist() == ['B', 'C']
```

<a id="test-37"></a>

## ملف الاختبار 37

```text
tests/test_frozen_history.py
```

[افتح الملف](../../tests/test_frozen_history.py)

صفحات المصدر المرتبطة:

- [تاريخ الاختصاص التجريبي](experiments/specialty_history.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [مرجع المسارات والإصدارات](paths.md)
- [المحرك المحلي ذو الزوج الواحد](recommendation/engine.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_new_version_preserves_original_hashes_and_values
test_target_and_future_outcomes_cannot_enter_prefix
test_prefix_fingerprint_survives_row_order_and_future_dtype_change
test_rejects_unfinalized_missing_cutoff_duplicate_and_invalid_source
test_base_history_ignores_experimental_labels_but_specialty_requires_them
test_invalid_prefix_values_are_rejected
test_history_selection_requires_explicit_stale_opt_in
test_legacy_optional_course_specialty_mismatch_refused_by_save_and_load
test_optional_specialty_load_requires_matching_bundle
test_hash_tampering_and_incomplete_bundle_are_rejected
test_legacy_migration_verifies_values_without_changing_original
test_same_models_load_two_versions_without_reading_any_training_table
test_selection_is_required_and_missing_version_is_not_rebuilt
```

<a id="test-38"></a>

## ملف الاختبار 38

```text
tests/test_frozen_history_v2.py
```

[افتح الملف](../../tests/test_frozen_history_v2.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [مرجع المسارات والإصدارات](paths.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_v2_load_default_uses_isolated_root_and_missing_v2_never_falls_back
test_v2_rejects_unversioned_or_wrong_version_bundle
test_v2_rejects_specialty_artifacts_without_opening_them
test_v2_hash_corruption_is_rejected
test_v2_new_cutoff_has_only_finalized_prefix_and_cannot_overwrite
test_v2_target_outcomes_and_end_gpa_do_not_change_history
test_v2_required_cutoff_contract
test_v2_build_rejects_old_sources_and_specialty_opt_in
test_cli_defaults_to_v2_sources_and_saves_source_hashes
test_cli_rejects_unvalidated_custom_source
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_v2_load_default_uses_isolated_root_and_missing_v2_never_falls_back
```


```python
assert loaded.global_sums['raw_count'] == 2
```

<a id="test-39"></a>

## ملف الاختبار 39

```text
tests/test_grade_scale.py
```

[افتح الملف](../../tests/test_grade_scale.py)

صفحات المصدر المرتبطة:

- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_supported_versions_convert_passing_marks
test_supported_versions_keep_failing_marks_at_zero_and_f
test_convert_rejects_invalid_version_even_in_a_mixed_batch
test_convert_rejects_missing_version_argument
test_convert_requires_one_version_per_mark
test_convert_keeps_empty_batches_valid
test_supported_version_boundaries_remain_unchanged
test_version_with_only_failing_bands_is_unsupported
test_empty_pass_bands_cannot_accept_a_version
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_convert_rejects_invalid_version_even_in_a_mixed_batch
```


```python
assert 'grade_version_id' in str(exc.value)
```

<a id="test-40"></a>

## ملف الاختبار 40

```text
tests/test_history_update.py
```

[افتح الملف](../../tests/test_history_update.py)

صفحات المصدر المرتبطة:

- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [مجاميع الدفعات ومدير اللقطة](recommendation/history_update.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.recommendation.history_update
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_aggregate_addition_preserves_weighted_prefix_and_matches_raw_oracle
test_delta_identity_is_canonical_and_state_bytes_are_deterministic
test_invalid_aggregate_is_rejected_without_mutating_prefix
test_delta_contract_validation
test_numeric_ids_normalize_to_existing_history_keys
test_empty_finalized_semester_advances_without_changing_sums
test_update_publishes_verified_immutable_bundle_and_lineage
test_same_delta_after_newer_update_and_restart_never_rolls_back
test_older_unrecorded_delta_is_rejected
test_serving_accepts_older_history_without_changing_backtesting_rule
test_serving_forbids_current_or_future_history
test_snapshot_metadata_is_not_shared_mutable_state
test_failed_update_keeps_active_snapshot_and_old_bundle
test_existing_destination_is_never_overwritten_even_if_incomplete
test_latest_valid_load_skips_incomplete_corrupt_and_wrong_version
test_missing_history_never_rebuilds_or_falls_back
test_concurrent_reader_keeps_one_snapshot_while_update_publishes
test_concurrent_same_delta_adds_only_once
test_structurally_invalid_state_is_rejected
test_unreadable_pickle_with_matching_hash_is_skipped
test_cleanup_failure_after_publication_does_not_report_failed_update
test_update_uses_normalized_delta_even_if_callers_payload_changes
test_two_managers_cannot_replace_a_published_version
test_bad_lineage_is_not_selected_on_restart
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_aggregate_addition_preserves_weighted_prefix_and_matches_raw_oracle
```


```python
assert updated.global_sums == {'effective_support': 4.25, 'raw_count': 5.0, 'mark_sum': 270.0, 'fail_sum': 1.25, 'attempt_sum': 5.5, 'retake_sum': 1.25}
```

<a id="test-41"></a>

## ملف الاختبار 41

```text
tests/test_local_recommendation.py
```

[افتح الملف](../../tests/test_local_recommendation.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [المحرك المحلي ذو الزوج الواحد](recommendation/engine.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)
- [أداة التوصية المحلية](recommendation/local_cli.md)
- [حفظ مخرجات التوصية المحلية](recommendation/output.md)
- [البحث عن مجموعات بالساعات الدقيقة](recommendation/plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](recommendation/plan_scoring.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_exhaustive_oracle_fractional_zero_and_variable_count
test_single_value_is_exact_and_range_keeps_both_bounds
test_range_uses_upper_exact_with_decimal_zero_and_variable_count
test_range_rejects_interior_when_upper_is_unreachable
test_mixed_credit_totals_rank_by_gpa_not_quality_point_sum
test_gpa_improvement_flag_and_risk_only_tiebreak
test_company_filter_ids_duplicates_and_prior_attempt
test_conflicts_missing_catalog_wrong_part_fail_explicitly
test_json_and_parquet_same_and_empty_list
test_local_cli_without_snapshot_uses_synthetic_inputs_and_mock_models
test_official_matrix_and_course_context_parity
test_batch_order_empty_and_export
test_range_export_and_batch_order_use_upper_exact
test_supplied_outcomes_cannot_override_context
test_missing_gpa_and_mismatched_snapshot_are_rejected
test_snapshot_ignores_current_future_outcomes
```

<a id="test-42"></a>

## ملف الاختبار 42

```text
tests/test_main_runner.py
```

[افتح الملف](../../tests/test_main_runner.py)

صفحات المصدر المرتبطة:

- [منظم نقاط التنفيذ وتسلسل البناء](main.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_registry_has_dependency_order_and_named_optional_steps
test_list_displays_standard_and_optional_work_without_execution
test_all_standard_stages_are_v2_and_request_workflows_keep_their_labels
test_all_dry_run_shows_v2_commands_without_execution
test_section_and_step_selection_use_only_requested_modules
test_failure_stops_later_steps_and_returns_nonzero
test_all_excludes_optional_work_and_delegates_request_arguments
test_range_selects_inclusive_standard_sections
test_process_launch_exception_is_reported_and_stops
test_arguments_are_not_broadcast_across_multiple_steps
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_registry_has_dependency_order_and_named_optional_steps
```


```python
assert runner.STANDARD_SECTIONS == ('data', 'features', 'modeling', 'evaluation', 'experiments')
```

<a id="test-43"></a>

## ملف الاختبار 43

```text
tests/test_model_artifact_isolation.py
```

[افتح الملف](../../tests/test_model_artifact_isolation.py)

صفحات المصدر المرتبطة:

- [تنسيق تجربة أهداف النقاط والاختصاص](experiments/degree_points.md)
- [إعداد تجربة الاختصاص والنقاط](experiments/degree_points_config.md)
- [ملفات تجربة الاختصاص ومصدرها](experiments/experiment_io.md)
- [خوارزميات ملاءمة التجارب وتقييمها](experiments/modeling.md)
- [تحويل العلامة إلى نقاط وفق النسخة](grade_scale.md)
- [مرجع المسارات والإصدارات](paths.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_artifact_namespaces
test_dependency_checker_detects_forbidden_imports_and_paths
test_dependency_checker_allows_official_and_local_imports
test_xml_recommendation_exception_does_not_allow_direct_experiment_imports
test_official_packages_do_not_depend_on_experiments
test_experiment_saves_preserve_official_v2_and_legacy_hashes
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_artifact_namespaces
```


```python
assert actual == paths.PROJECT_ROOT / expected
```

<a id="test-44"></a>

## ملف الاختبار 44

```text
tests/test_modeling_v2_io.py
```

[افتح الملف](../../tests/test_modeling_v2_io.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [تدريب الزوج الرسمي واختيار إعداداته](modeling/train_models.md)
- [مرجع المسارات والإصدارات](paths.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_modeling_io_constants_resolve_to_isolated_v2_files
test_main_reads_v2_and_writes_only_v2_with_correct_metadata
test_missing_v2_input_fails_without_reading_v1_or_writing_models
test_direct_script_import_resolves_v2_paths_without_running_training
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_modeling_io_constants_resolve_to_isolated_v2_files
```


```python
assert hasattr(paths, versioned_name)
```

<a id="test-45"></a>

## ملف الاختبار 45

```text
tests/test_plan_gpa_evaluation.py
```

[افتح الملف](../../tests/test_plan_gpa_evaluation.py)

صفحات المصدر المرتبطة:

- [تقييم معدل الخطط المرصودة](evaluation/evaluate_plan_gpa.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_plan_gpa_uses_credit_weighted_points
```

<a id="test-46"></a>

## ملف الاختبار 46

```text
tests/test_previous_course_status_data.py
```

[افتح الملف](../../tests/test_previous_course_status_data.py)

صفحات المصدر المرتبطة:

- [بيانات تجربة الحالة السابقة](experiments/previous_course_status_data.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_roster_is_chronology_and_w_is_not_a_zero_mark_fail
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_roster_is_chronology_and_w_is_not_a_zero_mark_fail
```


```python
assert augmented.previous_course_status.tolist() == ['WITHDRAWN', '__UNKNOWN__', 'CONDITIONAL_PASS', 'NEVER_TAKEN']
```

<a id="test-47"></a>

## ملف الاختبار 47

```text
tests/test_previous_course_status_evaluation.py
```

[افتح الملف](../../tests/test_previous_course_status_evaluation.py)

صفحات المصدر المرتبطة:

- [تقييم المودلات الموسعة بالحالة السابقة](experiments/previous_course_status_evaluation.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_status_slices_measure_retake_errors_without_small_group_pr_auc
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_status_slices_measure_retake_errors_without_small_group_pr_auc
```


```python
assert failed['rows'] == 2
```

<a id="test-48"></a>

## ملف الاختبار 48

```text
tests/test_previous_course_status_inference.py
```

[افتح الملف](../../tests/test_previous_course_status_inference.py)

صفحات المصدر المرتبطة:

- [مقارنة توقعات وخطط الحالة السابقة](recommendation_experiments/previous_course_status_inference.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.recommendation_experiments.previous_course_status_inference
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_course_comparison_joins_by_course_identity_and_keeps_status
test_course_comparison_rejects_mismatched_candidate_rows
test_unresolved_prior_attempt_is_unknown_in_serving_rows
test_plan_comparison_uses_same_memberships_and_reports_rank_changes
test_augmented_scoring_clips_predictions_before_grade_conversion
test_augmented_scoring_rejects_nonfinite_predictions
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_course_comparison_joins_by_course_identity_and_keeps_status
```


```python
assert paired.course_id.tolist() == ['B', 'A']
```

<a id="test-49"></a>

## ملف الاختبار 49

```text
tests/test_previous_course_status_training.py
```

[افتح الملف](../../tests/test_previous_course_status_training.py)

صفحات المصدر المرتبطة:

- [حساب البحث على ميزات المادة فقط](experiments/course_only_core.md)
- [تدريب الحالة السابقة كميزة إضافية](experiments/previous_course_status_training.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_two_contracts_append_one_categorical_without_changing_base
test_augmented_matrix_keeps_order_and_maps_unseen_status
test_augmented_folds_keep_official_cutoffs_and_fit_weights
test_lightgbm_receives_six_categorical_features
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_two_contracts_append_one_categorical_without_changing_base
```


```python
assert PLAN_AWARE_WITH_PREVIOUS_STATUS == [*BASE_FEATURES, 'previous_course_status']
```

<a id="test-50"></a>

## ملف الاختبار 50

```text
tests/test_project_status.py
```

[افتح الملف](../../tests/test_project_status.py)

صفحات المصدر المرتبطة:

- [مرجع المسارات والإصدارات](paths.md)
- [عرض الحالة المحلية للمشروع](project_status.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_stage_paths_order_and_version_boundary
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_stage_paths_order_and_version_boundary
```


```python
assert [stage.number for stage in stages] == list(range(1, 10))
```

<a id="test-51"></a>

## ملف الاختبار 51

```text
tests/test_projected_recommendation.py
```

[افتح الملف](../../tests/test_projected_recommendation.py)

صفحات المصدر المرتبطة:

- [تحميل أصول المحرك المحلي الرسمي](recommendation/artifacts.md)
- [المحرك المحلي ذو الزوج الواحد](recommendation/engine.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)
- [حفظ مخرجات التوصية المحلية](recommendation/output.md)
- [توقع المواد وتلخيص جودة الخطط](recommendation/plan_scoring.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_additive_example_and_zero_prior_credits
test_invalid_or_unknown_denominators_are_rejected
test_larger_load_can_win_despite_lower_semester_gpa
test_all_four_ranking_keys
test_explicit_model_cutoff_takes_priority_over_legacy_history_metadata
test_twenty_below_current_gpa_plans_are_scored_saved_and_top_three_returned
test_batch_and_candidate_order_are_stable_and_top_n_override_is_deliberate
test_projection_uses_prior_registered_credits_and_proposed_semester
test_one_two_and_no_matching_plans
test_snapshot_preserves_serving_only_denominator_and_history_validation
```

<a id="test-52"></a>

## ملف الاختبار 52

```text
tests/test_ranking_strategies.py
```

[افتح الملف](../../tests/test_ranking_strategies.py)

صفحات المصدر المرتبطة:

- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_identity_is_canonical_sha256_and_includes_optional_zero_course
test_invalid_plan_identity_is_rejected
test_balance_changes_rank_despite_different_gpa_and_failures
test_academic_changes_with_equal_balance_and_balance_changes_with_equal_academics
test_mixed_scope_preserves_ineligible_positions_in_academic_reference
test_new_only_with_no_positive_repeat_candidates_keeps_reference
test_balance_key_priority_is_failed_then_total_then_withdrawn
test_pareto_fronts_and_complete_selection_match_independent_oracle
test_withdrawn_is_an_independent_pareto_dominance_dimension
test_full_ties_have_total_order_independent_of_input_and_index
test_independent_stage_strategies_can_differ_without_approval_or_defaults
test_invalid_metrics_cannot_enter_total_order
test_identity_and_disabled_component_contracts_are_validated
test_empty_complete_set_and_input_immutability
test_imports_and_evaluation_do_not_read_reports_or_load_experiments
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_identity_is_canonical_sha256_and_includes_optional_zero_course
```


```python
assert identity.canonical_json == expected_json
```

<a id="test-53"></a>

## ملف الاختبار 53

```text
tests/test_recommendation.py
```

[افتح الملف](../../tests/test_recommendation.py)

صفحات المصدر المرتبطة:

- [البحث عن مجموعات بالساعات الدقيقة](recommendation/plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](recommendation/plan_scoring.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_predicted_mark_uses_official_pass_band_thresholds
test_exact_credits_allow_different_course_counts
test_ranking_uses_gpa_then_failure_without_risk_exclusion
```

<a id="test-54"></a>

## ملف الاختبار 54

```text
tests/test_recommendation_dependency_direction.py
```

[افتح الملف](../../tests/test_recommendation_dependency_direction.py)

صفحات المصدر المرتبطة:

- [تحليل تغير كتالوج الخطة القديم](diagnostics/analyze_course_plan_changes.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.diagnostics.analyze_course_plan_changes
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_upstream_packages_do_not_import_recommendation
test_production_packages_do_not_import_project_runner
test_course_plan_change_diagnostic_uses_package_location
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_upstream_packages_do_not_import_recommendation
```


```python
assert target != 'src.recommendation' and (not target.startswith('src.recommendation.'))
```

<a id="test-55"></a>

## ملف الاختبار 55

```text
tests/test_recommendation_inputs_v2.py
```

[افتح الملف](../../tests/test_recommendation_inputs_v2.py)

صفحات المصدر المرتبطة:

- [تقييم توصيات ملفات التصدير](evaluation/evaluate_xml_recommendations.md)
- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_local_loader_reads_only_cleaned_v2_and_preserves_history
test_local_missing_v2_fails_without_legacy_fallback
test_local_supplied_snapshot_reads_only_v2_catalog_and_attempts
test_snapshot_and_attempts_ignore_target_and_future_outcomes
test_xml_reads_only_v2_preserves_actual_math_and_explicit_target
test_xml_missing_v2_fails_without_legacy_fallback
test_xml_older_history_requires_explicit_opt_in
test_xml_older_history_opt_in_applies_to_recommendation_and_observed_plan
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_local_loader_reads_only_cleaned_v2_and_preserves_history
```


```python
assert set(reads) == set(paths.values())
```

<a id="test-56"></a>

## ملف الاختبار 56

```text
tests/test_recommendation_package.py
```

[افتح الملف](../../tests/test_recommendation_package.py)

لا علاقة داخلية مباشرة محسومة في الفهرس؛ قد يكون اختبار أداة أو حماية ملفات أو تجهيزًا مساعدًا.

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_public_and_component_imports_do_not_load_models
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_public_and_component_imports_do_not_load_models
```


```python
assert result.returncode == 0
```

<a id="test-57"></a>

## ملف الاختبار 57

```text
tests/test_recommendation_v2.py
```

[افتح الملف](../../tests/test_recommendation_v2.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [مرجع المسارات والإصدارات](paths.md)
- [تحميل أصول المحرك المحلي الرسمي](recommendation/artifacts.md)
- [قياس المحرك المحلي](recommendation/benchmark.md)
- [حفظ مخرجات التوصية المحلية](recommendation/output.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.recommendation
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_loader_reads_only_official_v2_artifacts
test_missing_official_artifact_never_falls_back
test_loader_rejects_incompatible_official_contract
test_mark_to_points_uses_versioned_grade_scale_and_shared_matrix
test_prediction_clipping
test_nonfinite_predictions_fail_before_clipping
test_missing_feature_fails_and_unknown_categories_use_saved_levels
test_exact_upper_bound_no_fallback_result_metadata
test_twenty_poor_plans_are_all_saved_and_top_three_returned
test_recommendation_source_has_no_experiment_or_legacy_path_dependency
test_importing_public_api_does_not_load_models
test_default_top_three_returns_every_available_plan_when_fewer_exist
test_benchmark_adapter_uses_v2_inputs_with_a_tiny_synthetic_request
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_loader_reads_only_official_v2_artifacts
```


```python
assert models == [files['GRADE_MODEL_PATH_V2'], files['FAIL_MODEL_PATH_V2']]
```

<a id="test-58"></a>

## ملف الاختبار 58

```text
tests/test_repeat_withdrawal_balance.py
```

[افتح الملف](../../tests/test_repeat_withdrawal_balance.py)

صفحات المصدر المرتبطة:

- [تشغيل تدقيق سياسة التوازن الوصفية](diagnostics/analyze_repeat_withdrawal_balance.md)
- [تقرير التحليل الوصفي للإعادات](diagnostics/repeat_withdrawal_report.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_failed_repeated_and_not_repeated
test_withdrawn_repeated_and_not_repeated
test_latest_previous_attempt_wins
test_current_and_future_outcomes_cannot_change_previous_status
test_decimal_and_zero_credit_courses_are_not_rounded
test_exact_duplicates_are_reported_and_do_not_double_credits
test_conflicting_same_semester_attempts_are_rejected
test_unverified_and_missing_statuses_do_not_become_failed_or_new
test_status_precedes_mark_and_other_codes_are_separate
test_no_history_in_observed_window_is_corrected_by_raw_prior
test_available_credits_use_last_prior_not_current_credit_value
test_student_totals_count_attempts_not_unique_courses
test_credit_bins_keep_decimal_other_values_visible
test_zero_load_ratios_remain_undefined
test_nonstandard_old_parts_are_explicit_sensitivity_only
test_policy_components_use_separate_backlog_denominators
test_small_policy_reference_reports_insufficient_evidence
test_analysis_runner_preserves_inputs_and_rejects_existing_output
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_failed_repeated_and_not_repeated
```


```python
assert r.available_failed_courses == 2
```

<a id="test-59"></a>

## ملف الاختبار 59

```text
tests/test_specialty_history_sequential.py
```

[افتح الملف](../../tests/test_specialty_history_sequential.py)

صفحات المصدر المرتبطة:

- [تاريخ الاختصاص التجريبي](experiments/specialty_history.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_20251_excludes_current_and_future_and_20252_includes_finalized_20251
test_generalized_parts_restore_unsorted_rows_with_duplicate_indices
test_new_degree_enters_both_hierarchy_levels_only_in_later_parts
test_training_rows_never_see_own_or_future_part_outcomes
test_empty_test_keeps_output_schema
test_test_parts_must_all_follow_training
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_20251_excludes_current_and_future_and_20252_includes_finalized_20251
```


```python
assert changed_features.loc[2, 'degree_history_avg_mark'] == pytest.approx(20 / 3)
```

<a id="test-60"></a>

## ملف الاختبار 60

```text
tests/test_student_course_status.py
```

[افتح الملف](../../tests/test_student_course_status.py)

صفحات المصدر المرتبطة:

- [تصنيف أحدث محاولة سابقة](features/student_course_status.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_mark_boundaries_use_previous_attempt_only
test_first_attempt_ignores_current_and_future_outcomes
test_latest_prior_attempt_wins_even_when_history_is_unsorted
test_retake_status_tracks_latest_attempt
test_students_and_courses_are_isolated
test_same_part_attempts_without_sequence_are_rejected
test_missing_prior_mark_without_explicit_withdrawal_is_rejected
test_latest_unresolved_attempt_is_unknown_not_first_or_older_fail
test_nullable_integer_mark_does_not_override_explicit_withdrawal
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_mark_boundaries_use_previous_attempt_only
```


```python
assert result.tolist() == [expected]
```

<a id="test-61"></a>

## ملف الاختبار 61

```text
tests/test_temporal_features.py
```

[افتح الملف](../../tests/test_temporal_features.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_fallback_uses_the_most_specific_available_history
test_roster_only_courses_never_become_finalized_history
test_consecutive_test_parts_roll_forward_only_after_each_outcome
test_saved_state_cannot_score_its_own_or_earlier_semester
test_current_semester_result_does_not_change_its_history_features
test_pre_2022_history_uses_quarter_weight
test_test_outcomes_cannot_update_frozen_train_state
test_groups_are_isolated_by_student_degree_and_part
test_peer_max_handles_tied_maximum_and_missing_course_history
test_credit_weighting_and_leave_one_out_match_manual_values
test_current_and_future_results_cannot_change_current_history
test_source_totals_are_already_before_current_semester
test_full_status_history_keeps_excluded_and_non_enrolled_semesters
test_gpa_trend_distinguishes_decline_and_improvement
test_20252_uses_20251_but_not_future_student_history
test_model_contract_excludes_raw_ids_and_leakage
test_changing_current_mark_changes_no_model_feature
```

<a id="test-62"></a>

## ملف الاختبار 62

```text
tests/test_train_models.py
```

[افتح الملف](../../tests/test_train_models.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [تدريب الزوج الرسمي واختيار إعداداته](modeling/train_models.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_regression_metrics_known_errors_and_inclusive_boundaries
test_classification_metrics_known_ranking_and_probabilities
test_classification_metrics_clips_endpoint_probabilities
test_calibration_table_returns_only_populated_bins_with_correct_aggregates
test_shared_parameters_copies_candidate_and_keeps_deterministic_defaults
test_prepare_folds_preserves_temporal_boundaries_targets_and_weights
test_prepare_folds_learns_categories_only_from_each_fit_subset
test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric
test_feature_importance_sorts_descending_and_normalizes_gain
test_feature_importance_returns_top_25_without_renormalizing
test_trainer_imports_as_a_script_without_running_training
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_regression_metrics_known_errors_and_inclusive_boundaries
```


```python
assert result == pytest.approx({'mae': 7.5, 'rmse': math.sqrt(87.5), 'within_5': 0.5, 'within_10': 0.75})
```

<a id="test-63"></a>

## ملف الاختبار 63

```text
tests/test_training_config.py
```

[افتح الملف](../../tests/test_training_config.py)

صفحات المصدر المرتبطة:

- [الأهداف وأوزان التدريب](modeling/training_config.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_target_definitions
test_training_weights_year_boundary
test_training_weights_preserves_index_and_numeric_coercion
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_target_definitions
```


```python
assert TARGET_GRADE == 'final_mark'
```

<a id="test-64"></a>

## ملف الاختبار 64

```text
tests/test_two_stage_activation.py
```

[افتح الملف](../../tests/test_two_stage_activation.py)

صفحات المصدر المرتبطة:

- [مرجع المسارات والإصدارات](paths.md)
- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)
- [التحقق من اعتماد سياسة الترتيب](recommendation/ranking_policy.md)
- [المحرك المعتمد ذو المرحلتين](recommendation/two_stage_engine.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_verified_artifact_loader_accepts_complete_human_approval
test_incomplete_or_inconsistent_approval_still_refuses_assets
test_approval_does_not_bypass_existing_feature_or_model_hash_checks
test_approved_production_preserves_pareto_results_and_labels_actual_usage
test_production_loads_once_then_is_deterministic_and_defends_approval_snapshot
test_production_does_not_allow_replacing_an_approved_strategy
test_wrong_stage_or_missing_strategy_fails_before_any_inference
test_one_request_pins_both_approved_choices_despite_mid_request_replacement
test_unapproved_load_fails_before_history_loading
test_manifest_choices_are_independent_without_changing_the_actual_human_approval
test_pinned_approved_models_match_evaluation_on_known_grade_version_synthetic_payload
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_verified_artifact_loader_accepts_complete_human_approval
```


```python
assert bundle.stage1.grade_model.num_feature() == 33
```

<a id="test-65"></a>

## ملف الاختبار 65

```text
tests/test_two_stage_artifacts.py
```

[افتح الملف](../../tests/test_two_stage_artifacts.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](recommendation/two_stage_artifacts.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.recommendation.two_stage_artifacts
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_stage_contracts_derive_33_and_47_from_the_official_order
test_promotion_copies_exact_bytes_and_archives_original_provenance
test_promoted_pair_produces_the_same_synthetic_predictions
test_repeat_promotion_refuses_overwrite_and_preserves_published_bytes
test_manifest_is_deterministic_for_the_same_verified_artifacts
test_artifact_loading_does_not_accept_ranking_approval_in_phase1
test_failed_promotion_leaves_no_partial_bundle_or_source_changes
test_promotion_rejects_stale_input_or_source_signature
test_promotion_rejects_changed_source_model_bytes
test_promotion_rejects_incompatible_source_model_even_if_its_hash_is_resigned
test_loader_checks_model_header_semantics_even_with_matching_hashes
test_loader_checks_fail_model_objective_even_with_matching_hash
test_loader_checks_the_order_of_categorical_columns_in_model_metadata
test_loader_rejects_reinterpreted_fail_targets_or_objectives
test_loader_rejects_reinterpreted_grade_target
test_loader_rejects_corrupt_manifest_feature_contract
test_loader_rejects_current_or_future_training_cutoff
test_loader_rejects_changed_model_or_grade_scale_hash
test_loader_rejects_changed_official_metadata_after_promotion
test_loader_rejects_changed_category_bytes_or_order
test_missing_promoted_model_never_falls_back_to_experimental_or_official_model
test_loader_rejects_an_unpinned_model_path_even_with_identical_bytes
test_runtime_load_needs_no_experiment_or_training_file_reads_or_imports
test_loader_rejects_incompatible_manifest_version
test_runtime_module_has_no_direct_experiment_or_trainer_import
test_loader_requires_archived_original_provenance
test_loader_rejects_malformed_archived_metadata_hash
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_stage_contracts_derive_33_and_47_from_the_official_order
```


```python
assert first['model_features'] == [name for name in BASE_FEATURES if name not in PLAN_CONTEXT_COLUMNS]
```

<a id="test-66"></a>

## ملف الاختبار 66

```text
tests/test_two_stage_benchmark.py
```

[افتح الملف](../../tests/test_two_stage_benchmark.py)

صفحات المصدر المرتبطة:

- [القيود الأكاديمية على الخطط](recommendation/constraints.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](recommendation/plan_generation.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_search_counter_counts_actual_recursion_and_preserves_order
test_feasible_counter_keeps_zero_options_and_filters_complete_plans
test_scenarios_cover_sizes_fractions_zero_ties_constraints_and_no_solution
test_measurements_use_real_core_and_explicit_strategies_without_bundle_io
test_small_search_matches_independent_subsets
test_jobs_compare_stages_independently_and_every_combination
test_timeout_is_censored_evidence_never_a_fabricated_measurement
test_report_keeps_approvals_open_and_records_censored_jobs
test_no_solution_is_measured_without_inventing_ranker_work
test_final_comparison_uses_identical_fixed_shortlist_for_both_strategies
test_worker_subprocess_serializes_completed_search
test_worker_timeout_returns_censored_record
test_atomic_checkpoint_has_complete_json_and_no_leftover
test_fast_search_is_not_blamed_for_full_or_ranking_timeouts
test_slow_non_dense_search_is_included_in_the_search_decision
test_missing_search_measurement_cannot_produce_a_keep_verdict
test_dense_upper_target_search_has_the_complete_choose_six_count
test_inference_fixture_uses_a_grade_version_present_in_loaded_bands
test_inference_fixture_rejects_a_scale_without_supported_versions
test_corrected_report_does_not_embed_fabricated_phase5_quality_snapshot
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_search_counter_counts_actual_recursion_and_preserves_order
```


```python
assert observed == list(enumerate_plan_indices(candidates, 3)) == [(0,), (1,)]
```

<a id="test-67"></a>

## ملف الاختبار 67

```text
tests/test_two_stage_constraints.py
```

[افتح الملف](../../tests/test_two_stage_constraints.py)

صفحات المصدر المرتبطة:

- [القيود الأكاديمية على الخطط](recommendation/constraints.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_requirement_alias_and_adjustments_preserve_fractional_remaining
test_requirement_without_adjustments_defaults_to_zero_adjustments
test_overcompleted_requirement_has_zero_remaining
test_invalid_requirement_policy_rejects
test_duplicate_normalized_requirement_ids_reject_even_when_values_match
test_invalid_requirement_record_list_rejects
test_invalid_direct_constraints_reject
test_failed_repeat_cap_is_required
test_zero_credit_choices_remain_distinct_with_repeat_caps_zero
test_failed_cap_and_withdrawn_cap_are_independent_maxima
test_other_previous_and_attempts_or_probabilities_do_not_consume_repeat_caps
test_selected_repeat_costs_full_credits_to_requirement
test_fractional_subsets_match_hand_derived_oracle
test_constraints_match_independent_exhaustive_oracle_and_preserve_candidates
test_unreachable_upper_target_has_no_lower_fallback
test_missing_requirement_policy_rejects_even_for_zero_credit_candidate
test_invalid_candidate_constraint_fields_reject
test_missing_candidate_constraint_column_rejects
test_empty_candidate_set_has_no_feasible_plan
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_requirement_alias_and_adjustments_preserve_fractional_remaining
```


```python
assert actual == {'12': Decimal('3.250')}
```

<a id="test-68"></a>

## ملف الاختبار 68

```text
tests/test_two_stage_engine.py
```

[افتح الملف](../../tests/test_two_stage_engine.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [مرجع المسارات والإصدارات](paths.md)
- [المحرك المحلي ذو الزوج الواحد](recommendation/engine.md)
- [مجاميع الدفعات ومدير اللقطة](recommendation/history_update.md)
- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](recommendation/plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](recommendation/plan_scoring.md)
- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](recommendation/two_stage_artifacts.md)
- [المحرك المعتمد ذو المرحلتين](recommendation/two_stage_engine.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.recommendation.two_stage_engine
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_two_stage_orchestration_has_an_explicit_evaluation_entrypoint
test_production_activation_refuses_unapproved_independent_strategies
test_evaluation_factory_loads_assets_and_history_once_for_reused_requests
test_evaluation_needs_two_explicit_stage_choices
test_stage_one_predicts_n_rows_once_before_plan_constraints
test_invalid_grade_version_is_rejected_before_any_inference
test_missing_grade_version_field_is_rejected_before_any_inference
test_only_explicitly_rejected_candidates_are_removed_before_stage_one
test_more_than_fifty_plans_only_scores_fifty_in_stage_two
test_final_outputs_use_stage_two_predictions_and_backend_projection_denominator
test_model_boundary_rejects_malformed_or_nonfinite_outputs
test_prediction_clipping_applies_before_grade_scale_and_plan_aggregation
test_stage_two_context_matrix_predictions_and_summaries_match_legacy_path
test_stage_two_fourteen_context_features_match_hand_calculated_zero_credit_plan
test_pinned_official_stage_two_models_match_legacy_on_identical_synthetic_plans
test_decimal_tenths_at_maximum_grade_points_are_feasible_and_scoreable
test_identity_shortlist_and_input_hash_are_stable_under_candidate_order
test_missing_history_values_have_a_json_safe_deterministic_fingerprint
test_result_provenance_has_model_category_scale_history_and_input_hashes
test_returned_nested_metadata_cannot_change_later_requests_or_history
test_unsupported_opaque_metadata_is_rejected_without_nondeterministic_repr
test_cross_stage_strategy_choices_remain_independent_in_result_metadata
test_top_k_must_be_an_integer_within_one_to_fifty
test_less_than_fifty_returns_available_plans_without_padding
test_fractional_credits_keep_exact_feasibility_and_output_totals
test_optional_zero_course_preserves_two_identities_and_changes_plan_context
test_credit_range_uses_upper_exact_target_without_lower_fallback
test_no_feasible_plan_never_calls_stage_two
test_current_or_future_training_cutoff_is_rejected_on_each_request
test_current_or_future_history_is_rejected
test_older_finalized_history_is_accepted_and_age_is_explicit
test_request_retains_one_history_snapshot_during_atomic_update
test_engine_import_has_no_experiment_or_trainer_runtime_dependency
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_two_stage_orchestration_has_an_explicit_evaluation_entrypoint
```


```python
assert callable(engine.load_for_evaluation)
```

<a id="test-69"></a>

## ملف الاختبار 69

```text
tests/test_two_stage_evaluation.py
```

[افتح الملف](../../tests/test_two_stage_evaluation.py)

صفحات المصدر المرتبطة:

- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](recommendation/shortlist.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_complete_synthetic_evaluation_has_all_feasible_plans
test_real_shortlist_matches_independent_complete_subset_and_ranking_oracle
test_all_four_cross_stage_results_match_independent_final_oracle
test_fixed_shortlist_is_identical_for_both_final_comparisons
test_over_50_diagnostic_reports_lost_global_quality_and_component_retention
test_aggregate_report_preserves_denominators_and_does_not_claim_historical_eligibility
test_report_sensitivity_keeps_soft_distance_and_correct_scope_and_availability
test_mixed_scope_report_preserves_outside_academic_slots_for_all_candidates
test_reports_are_deterministic_and_cli_only_writes_requested_output
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_complete_synthetic_evaluation_has_all_feasible_plans
```


```python
assert synthetic_result['feasible_plan_count'] == 176
```

<a id="test-70"></a>

## ملف الاختبار 70

```text
tests/test_two_stage_matrix.py
```

[افتح الملف](../../tests/test_two_stage_matrix.py)

صفحات المصدر المرتبطة:

- [حساب البحث على ميزات المادة فقط](experiments/course_only_core.md)
- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](recommendation/two_stage_artifacts.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_default_matrix_matches_legacy_47_exactly_without_mutating_inputs
test_stage1_matches_legacy_slice_without_requiring_plan_context
test_explicit_feature_order_coerces_only_the_requested_columns
test_explicit_features_reject_names_outside_the_model_contract
test_explicit_features_reject_duplicate_model_columns
test_legacy_course_matrix_api_retains_33_feature_coercion_and_missing_validation
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_default_matrix_matches_legacy_47_exactly_without_mutating_inputs
```


```python
assert levels == original_levels
```

<a id="test-71"></a>

## ملف الاختبار 71

```text
tests/test_two_stage_payloads.py
```

[افتح الملف](../../tests/test_two_stage_payloads.py)

صفحات المصدر المرتبطة:

- [عقود النواة والمدخلات المحلية](recommendation/inputs.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_ready_values_are_preserved_without_io_or_candidate_cap_filtering
test_missing_trend_stays_missing
test_only_explicit_eligibility_rejection_removes_candidates
test_cross_identity_or_invalid_part_is_rejected
test_missing_ready_snapshot_field_is_rejected
test_invalid_snapshot_numbers_are_rejected
test_decimal_to_float_overflow_is_rejected
test_invalid_candidate_numbers_are_rejected
test_duplicate_course_identity_after_normalization_is_rejected
test_candidate_order_and_untrusted_features_do_not_change_prepared_rows
test_empty_candidates_keep_model_and_status_columns
test_target_overrides_valid_range_and_legacy_fail_name_is_not_a_cap
test_invalid_request_constraints_are_rejected
test_imports_are_production_safe
test_official_classification_does_not_use_marks_or_attempts
test_conflicting_full_status_meanings_are_rejected
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_ready_values_are_preserved_without_io_or_candidate_cap_filtering
```


```python
assert result.snapshot['prior_fail_credit_ratio'] == 0.73
```

<a id="test-72"></a>

## ملف الاختبار 72

```text
tests/test_two_stage_shortlist.py
```

[افتح الملف](../../tests/test_two_stage_shortlist.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [القيود الأكاديمية على الخطط](recommendation/constraints.md)
- [توقع المواد وتلخيص جودة الخطط](recommendation/plan_scoring.md)
- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](recommendation/shortlist.md)
- [المحرك المعتمد ذو المرحلتين](recommendation/two_stage_engine.md)

أهداف الاستيراد الديناميكي الموجودة:

```text
src.recommendation.plan_scoring
src.recommendation.shortlist
src.recommendation.two_stage_engine
```

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_complete_feasibility_before_shortlist_fractional_and_optional_zero
test_no_lower_credit_fallback_and_no_prefiltering_of_failed_availability
test_shared_scoring_rejects_nonfinite_or_wrong_shape_before_clip
test_input_hash_preserves_credit_precision_beyond_decimal_context
test_exact_target_above_twelve_does_not_accept_twelve
test_exact_long_decimal_cost_cannot_round_below_a_hard_cap
test_remaining_policy_arithmetic_preserves_every_supplied_decimal_digit
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_complete_feasibility_before_shortlist_fractional_and_optional_zero
```


```python
assert set(result.all_plans.course_tuple) == expected == {('C',), ('C', 'D'), ('E', 'F'), ('D', 'E', 'F')}
```

<a id="test-73"></a>

## ملف الاختبار 73

```text
tests/test_v2_paths.py
```

[افتح الملف](../../tests/test_v2_paths.py)

صفحات المصدر المرتبطة:

- [مرجع المسارات والإصدارات](paths.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_versioned_path_preserves_parent_and_extension
test_versioned_path_supports_artifact_extensions
test_v2_artifacts_are_separate_from_originals
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_versioned_path_preserves_parent_and_extension
```


```python
assert hasattr(paths, 'versioned_path')
```

<a id="test-74"></a>

## ملف الاختبار 74

```text
tests/test_v2_pipeline.py
```

[افتح الملف](../../tests/test_v2_pipeline.py)

صفحات المصدر المرتبطة:

- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [مرجع المسارات والإصدارات](paths.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_full_v2_chain_uses_only_new_intermediates_and_preserves_v1
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_full_v2_chain_uses_only_new_intermediates_and_preserves_v1
```


```python
assert local(paths.PRE_COMMON_STUDENT_COURSE_PATH_V2).is_file()
```

<a id="test-75"></a>

## ملف الاختبار 75

```text
tests/test_xml_package.py
```

[افتح الملف](../../tests/test_xml_package.py)

صفحات المصدر المرتبطة:

- [تحويل التصدير المحلي إلى سجلات](data/xml_to_json.md)
- [تقييم توصيات ملفات التصدير](evaluation/evaluate_xml_recommendations.md)
- [واجهة اسم قديم لتحويل التصدير](xml_2_json.md)

أسماء جميع الاختبارات المعرفة في هذا الملف:

```text
test_xml_module_imports_do_not_create_directories
test_xml_converter_and_evaluator_keep_parsing_behavior
test_xml_evaluation_root_module_still_exposes_cli_help
test_xml_conversion_root_entrypoint_delegates_to_package
test_xml_conversion_direct_script_resolves_project_package
```

مثال قضية محددة يختبرها التعريف التالي:

```text
test_xml_module_imports_do_not_create_directories
```


```python
assert result.returncode == 0
```

<a id="test-76"></a>

## ملف الاختبار 76

```text
tests/two_stage_fixtures.py
```

[افتح الملف](../../tests/two_stage_fixtures.py)

صفحات المصدر المرتبطة:

- [العقد المرتب لميزات المودل](features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](features/temporal_features.md)
- [مجاميع الدفعات ومدير اللقطة](recommendation/history_update.md)
- [الهوية والترتيب وجبهات المفاضلة](recommendation/ranking.md)
- [التحقق من اعتماد سياسة الترتيب](recommendation/ranking_policy.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](recommendation/two_stage_artifacts.md)

لا دوال اختبار مسماة في هذا الملف؛ دوره تعريف حزمة أو عينات ومودلات اصطناعية.

## تمرين تدقيق دون تنفيذ

اختر اسم اختبار متعلق بالقطع أو الهوية، وافتح مصدره والصفحة المرتبطة. حدد الإعداد الاصطناعي والشرط الذي يتوقع رفضه، ثم قارنه بشرط الدالة الفعلية. لا تشغل أداة تدريب أو أثر توصية على طالب حقيقي.

