# خريطة ملفات `Two-Stage Recommendation`

لقطة **`2026-10-08`**. المكونات أدناه موجودة فعليًا؛ اكتملت مراحل التنفيذ السبع. الخريطة تشرح ملفات المسار وعلاقاته، ولا تنسب كل ملف مشترك إلى مرحلة إنشائه. الحالة العامة [READY_FOR_STABILIZATION_REVIEW](README.md)، ومسار العمليات في [TWO_STAGE_DATA_FLOW](TWO_STAGE_DATA_FLOW.md).

## 1. ملفات التشغيل الأساسية

| الملف | المرحلة / الاستخدام | أهم الدوال أو الكلاسات ودورها |
|---|---|---|
| [src/recommendation/__init__.py](../src/recommendation/__init__.py) | واجهة عامة | يصدر `TwoStagePlanRecommender` ومحولات المدخلات والقيود ومدير التاريخ؛ يبقي `AcademicPlanRecommender` متاحًا. |
| [two_stage_engine.py](../src/recommendation/two_stage_engine.py) | `5/7`، نقطة الدخول | `TwoStagePlanRecommender.load()` للتفعيل المعتمد؛ `load_for_evaluation()` للتقييم؛ `recommend_from_payloads()` للطلب؛ `update_history_from_payload()` للتحديث المستقل. `_ranking_metadata()` يثبت وصف السياسة، و`_prepare_candidates()/_score_stage2()` يربطان الميزات. |
| [two_stage_artifacts.py](../src/recommendation/two_stage_artifacts.py) | `1/7` | `ModelPair/TwoStageArtifacts`، `stage_feature_contract()`، `artifact_relative_paths()`، `validate_stage_metadata()`، `validate_archived_provenance()`، `validate_artifact_manifest()`، `load_model_pair()`، `load_manifest_assets()` و`load_two_stage_artifacts()`: عقود وبصمات وتحميل دون تدريب أو مسار بديل. |
| [ranking_policy.py](../src/recommendation/ranking_policy.py) | `7` | `balance_policy_contract()` و`validate_ranking_policy()`: الاعتمادات الثلاثة والهويات والنسخ والتوليفة والنطاق ومصدر القرار والعقود غير المحسومة. |
| [inputs.py](../src/recommendation/inputs.py) | `2` ومحول محلي سابق | `PreparedRecommendationInputs` و`normalize_student_payload()/normalize_candidate_payloads()/normalize_request_payload()/prepare_recommendation_payloads()`: مدخلات جاهزة دون وصل كتالوج أو إعادة حساب تاريخ الطالب. |
| [course_status.py](../src/recommendation/course_status.py) | `2` | `normalize_previous_status()` و`classify_candidate_status()`: تصنيف رسمي للراسب والمنسحب والجديد والحالات الأخرى، ورفض التعارض. |
| [constraints.py](../src/recommendation/constraints.py) | `2/5` | `normalize_requirement_policies()` و`PlanConstraints` و`enumerate_feasible_plan_indices()`: أرصدة الفئات وحدا إعادة الراسب والمنسحب على الخطط الدقيقة. |
| [plan_generation.py](../src/recommendation/plan_generation.py) | مشترك، تدقيق الدقة في `5` | `resolve_credit_bounds()` و`enumerate_plan_indices()` للهدف الدقيق؛ `decimal_credit_units()/sum_credit_values()` لحفظ الدقة؛ `build_plan_rows()` لصفوف مواد الخطط. |
| [history_update.py](../src/recommendation/history_update.py) | `3` | `HistoryDelta/normalize_history_delta()/apply_history_delta()/validate_history_state()`، و`HistorySnapshot`، و`FrozenHistoryManager.load()/capture()/update_history_from_payload()`: مجاميع وتكرار وتعارض ونسخة نشطة. |
| [balance_policy.py](../src/recommendation/balance_policy.py) | `4` | `BalancePolicy/B_OBSERVED_MIDDLE_V1/compute_balance_components()`: نسب وعقوبات ونطاق وأعلام تفعيل منفصلة دون تغيير الأهلية. |
| [ranking.py](../src/recommendation/ranking.py) | `4` | `PlanIdentity/canonical_plan_identity()/RankingStrategy`، `rank_academic_reference()`، `_pareto_levels()` و`rank_evaluation_plans()`: هوية ثابتة وترتيب كامل مستقل لكل مرحلة. |
| [shortlist.py](../src/recommendation/shortlist.py) | `5` | `SHORTLIST_LIMIT=50`، `ShortlistResult` و`build_stage1_shortlist()`: كل الخطط الممكنة بمقاييس `33` ثم المختصر وخريطة فهارس المواد. |
| [plan_scoring.py](../src/recommendation/plan_scoring.py) | مشترك، توسع في `5` | `score_course_rows()` للتوقع والتحويل، `summarize_scored_plans()` للتجميع، `project_cumulative_gpa()` للإسقاط؛ `rank_plans()` للترتيب المحلي السابق. |
| [feature_contract.py](../src/features/feature_contract.py) | مشترك، تعميم في `2` | `prepare_model_matrix()` يقبل ترتيب `33/47` ويحافظ على افتراضي `BASE_FEATURES` والتحويل الرقمي والفئات المثبتة. |
| [temporal_features.py](../src/features/temporal_features.py) | مشترك | `CourseHistoryState/build_history_keys()` و`COURSE_HISTORY_COLUMNS` السبع؛ `compute_plan_context_features()` و`PLAN_CONTEXT_COLUMNS` الأربع عشرة. |
| [frozen_history.py](../src/features/frozen_history.py) | مشترك، نشر ذري في `3` | `load_frozen_history()/save_frozen_history()/validate_history_selection()`، وإضافة `save_frozen_history_atomic()` للحفظ المرحلي والتحقق والنشر الحصري. |
| [grade_scale.py](../src/grade_scale.py) | مشترك | `GradeScale.from_parquet()/convert()`: العلامة المتوقعة إلى نقاط وتصنيف؛ لا يرفض حاليًا إصدارًا غير مدعوم. |
| [src/paths.py](../src/paths.py) | مركزي | مسارات أصول `V2` و`SHORTLIST_*` و`TWO_STAGE_MANIFEST_PATH` و`FROZEN_HISTORY_DIR_V2` و`GRADE_SCALE_PATH`. |

اسم `rank_evaluation_plans()` ووصف `RankingStrategy` لا يعنيان أن الترتيب محصور بالتقييم الآن؛ يستدعيهما المحرك المفعّل أيضًا، ويضيف هوية الاعتماد بعد تحقق `Manifest`. لا يقرأ المسار التشغيلي تقارير `Phase 6` أو أصول التجارب أو مصادر التدريب.

## 2. الأصول المثبتة والتاريخ

| المسار | الدور والحالة |
|---|---|
| [models/shortlist_v2/grade_model.txt](../models/shortlist_v2/grade_model.txt) و[fail_model.txt](../models/shortlist_v2/fail_model.txt) | نسختا `Stage 1` المنشورتان بميزات `33`، من أصول سابقة دون تدريب جديد. |
| [models/shortlist_v2/category_levels.json](../models/shortlist_v2/category_levels.json) | فئات `Stage 1` المثبتة. |
| [models/shortlist_v2/manifest.json](../models/shortlist_v2/manifest.json) | عقود المرحلتين والمصدر الأصلي والبصمات و`GradeScale` واعتماد `pareto v1 → pareto v1` وحدود التشغيل `UNRESOLVED`. |
| [models/grade_regressor_v2.txt](../models/grade_regressor_v2.txt) و[fail_risk_classifier_v2.txt](../models/fail_risk_classifier_v2.txt) | مودلا `Stage 2` الرسميان بميزات `47`؛ مراجع مثبتة دون نسخ جديد. |
| [models/model_metadata_v2.json](../models/model_metadata_v2.json) | عقد ومصدر التدريب الرسمي لـ`Stage 2`. |
| [data/artifacts/category_levels_v2.json](../data/artifacts/category_levels_v2.json) | فئات `Stage 2`. |
| [data/raw/v_acs_grade.parquet](../data/raw/v_acs_grade.parquet) | مصدر `GradeScale`؛ نسخة المحتوى `sha256:<digest>` مستقلة عن `grade_version_id` داخل الطلب. |
| [data/artifacts/history_v2/](../data/artifacts/history_v2/) | حزم تاريخ ثابتة؛ المدير يختار أحدث حزمة مكتملة وصحيحة. آخر تحقق تحميل مسجل في `Phase 7` وصل إلى `20251`. |
| [.gitattributes](../.gitattributes) | حماية بايتات ملفات `Stage 1` المنشورة؛ مشكلة اختلاف نهايات أسطر `Stage 2` بين `Git` والنسخة المحلية ما زالت مفتوحة. |

`TwoStageArtifacts` يجمع المودلات والفئات والمقياس و`Manifest`، ولا يتضمن التاريخ؛ يحمله المدير بصورة منفصلة.

## 3. الاختبارات

| الملفات | المسؤولية |
|---|---|
| [test_two_stage_artifacts.py](../tests/test_two_stage_artifacts.py) | النشر والعقود وترتيب الميزات والفئات والأهداف والبصمات والمصدر والعزل. |
| [test_two_stage_matrix.py](../tests/test_two_stage_matrix.py) | توافق مصفوفة `33/47` والتحويل والترتيب. |
| [test_two_stage_payloads.py](../tests/test_two_stage_payloads.py) و[test_two_stage_constraints.py](../tests/test_two_stage_constraints.py) | القيم الجاهزة والهوية والتصنيف والقيود والدقة ومرجع الخطط الكامل الصغير. |
| [test_history_update.py](../tests/test_history_update.py) | `Delta` والتكرار والتعارض وفشل النشر وثبات النسخة والتزامن المحلي. |
| [test_balance_policy.py](../tests/test_balance_policy.py) و[test_ranking_strategies.py](../tests/test_ranking_strategies.py) | النطاق والمكونات والكسور والهوية والاستقلال والتعادل والهيمنة. |
| [test_two_stage_engine.py](../tests/test_two_stage_engine.py) و[test_two_stage_shortlist.py](../tests/test_two_stage_shortlist.py) | الربط وعدد التوقعات وحد المختصر والتوافق وعزل توقعات المرحلة النهائية. |
| [test_two_stage_evaluation.py](../tests/test_two_stage_evaluation.py) و[two_stage_fixtures.py](../tests/two_stage_fixtures.py) | تقارير `Phase 5` وتجهيزات مصطنعة مشتركة؛ ليست بيانات طلاب أو اعتماد جودة واقعية. |
| [test_two_stage_benchmark.py](../tests/test_two_stage_benchmark.py) | حالات وعقود القياس والمهلات. |
| [test_corrected_phase6_rerun.py](../tests/test_corrected_phase6_rerun.py) و[test_corrected_phase6_evaluation.py](../tests/test_corrected_phase6_evaluation.py) | إبطال واستبدال الأدلة، المصدر والاستئناف، مرجع الجودة والثبات. |
| [test_two_stage_activation.py](../tests/test_two_stage_activation.py) | اعتماد `Manifest` والتفعيل والتوافق وثبات الاختيارات ورفض التغيير غير المعتمد. |
| [test_recommendation_v2.py](../tests/test_recommendation_v2.py)، [test_projected_recommendation.py](../tests/test_projected_recommendation.py)، [test_frozen_history_v2.py](../tests/test_frozen_history_v2.py) | فحوص مرتبطة للمحرك المحلي والإسقاط وتاريخ `V2`. |
| [test_train_models.py](../tests/test_train_models.py) | الفشل المعروف: توقع `capacity_63` مقابل `capaciy_63` في [train_models.py](../src/modeling/train_models.py). |

وجود ملف اختبار لا يعني أن كل حالات التشغيل مغطاة. نتائج كل مرحلة التاريخية وحدودها موضحة في صفحاتها و[README](README.md).

## 4. أدوات النشر والتقييم خارج Serving

| الملف | الاستخدام |
|---|---|
| [promote_shortlist_artifacts.py](../scripts/promote_shortlist_artifacts.py) | `verify_training_sources()/build_promotion_manifest()/promote_shortlist_artifacts()`: نشر `Stage 1` بعد تدقيق المصدر؛ لا يستدعى في طلب التوصية. |
| [evaluate_two_stage_ranking.py](../scripts/evaluate_two_stage_ranking.py) | `evaluate_synthetic()/evaluate_historical_policy()/build_evaluation_report()`: تقرير `Phase 5` بتوقعات مصطنعة وتراكيب وصفية. |
| [benchmark_two_stage.py](../scripts/benchmark_two_stage.py) | `synthetic_case()/measure_case()/run_worker()/censored_result()`: قياسات مصطنعة منفصلة ومهلات. |
| [rerun_corrected_phase6.py](../scripts/rerun_corrected_phase6.py) | `classify_old_evidence()/run_corrected_benchmarks()/assemble_corrected_results()`: إعادة القياس المصحح وحماية المصدر. |
| [evaluate_corrected_phase6.py](../scripts/evaluate_corrected_phase6.py) | `evaluate_fixture()/recall_evidence()/compare_fixed_final()/summarize_evidence()`: مرجع `Stage 2` محدود ومقارنة مستقلة للنهائي. |

## 5. التجارب السابقة والمكونات المحلية الباقية للتوافق

| الملف أو المسار | علاقته بالنواة الحالية |
|---|---|
| [models/experiments/course_only_recommendation/](../models/experiments/course_only_recommendation/) | مصدر نشر `Stage 1` التاريخي؛ لا يرجع إليه المحرك عند فقد أصل رسمي. |
| [src/experiments/course_only_core.py](../src/experiments/course_only_core.py) | `prepare_course_matrix()` يفوض مصفوفة التجربة إلى المساعد المشترك؛ تبقى فحوص توقيع التجربة مستقلة. |
| [course_only_training.py](../src/experiments/course_only_training.py)، [course_only_evaluation.py](../src/experiments/course_only_evaluation.py)، [course_only_report.py](../src/experiments/course_only_report.py)، [course_only_recommendation.py](../src/experiments/course_only_recommendation.py) | مسار البحث السابق؛ ليس تبعية تشغيل `TwoStagePlanRecommender`. |
| [src/recommendation/engine.py](../src/recommendation/engine.py) | `AcademicPlanRecommender` المحلي: توافق ومقارنة لخطط `47`؛ ليس المحرك الجديد ولا fallback له. |
| [artifacts.py](../src/recommendation/artifacts.py) | تحميل ومصدر أصول المحرك المحلي السابق؛ متميز عن `two_stage_artifacts.py`. |
| [inputs.py](../src/recommendation/inputs.py) | يحتفظ بـ`load_local_inputs()` والمحولات المحلية إلى جانب قسم `Payload` الخالص؛ لا يستدعي المحرك الجديد مسار الوصل المحلي. |
| [local_cli.py](../src/recommendation/local_cli.py) و[src/recommend_local.py](../src/recommend_local.py) | واجهة الأوامر الحالية للمحرك المحلي السابق. |
| [output.py](../src/recommendation/output.py) | حفظ نتائج المسار المحلي وملفاته؛ النواة الجديدة تعيد بنية نتيجة إلى المستدعي. |
| [benchmark.py](../src/recommendation/benchmark.py) | قياس محلي قديم، منفصل عن `scripts/benchmark_two_stage.py`. |

## 6. التقارير والتوثيق

| المرجع | كيفية استخدامه |
|---|---|
| [الخطة وسجل التنفيذ](../docs/architecture/RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md) | أهداف ونطاق وتاريخ `Phases 1–7`. فقرات `Next/UNAPPROVED` القديمة تصف تاريخها؛ أحدث سجل واعتماد `Manifest` هما الحالة الحالية. |
| [Baseline Validation](../docs/architecture/RECOMMENDATION_TWO_STAGE_BASELINE_VALIDATION.md) | لقطة ما قبل التنفيذ؛ `612 passed` ليست نتيجة التنفيذ الحالي. |
| [reports/repeat_withdrawal_analysis/](../reports/repeat_withdrawal_analysis/) | تحليل وصفي ومقترحات سياسة، لا قواعد أهلية `Backend`. |
| [Phase 5 comparison](../reports/two_stage_phase5/comparison.md) | سجل تاريخي بتوقعات مصطنعة؛ لا يخلط مع تقييم الجودة بالمودلات الفعلية. |
| [Phase 6 corrected RESULT](../reports/two_stage_phase6/corrected/RESULT.md) | المرجع الحالي للكلفة والمفاضلات المصححة. ملفا الجودة `2.111/3.111` منفصلان عن قياس `1.111`. |
| [Phase 6 old_invalidated](../reports/two_stage_phase6/corrected/old_invalidated/README.md) | حفظ الأدلة الأصلية المبطلة مع توضيح البحث غير المتأثر؛ لا تُمحى النتائج أو يعاد تقديمها كحالية. |
| [Phase 7 RESULT](../reports/two_stage_phase7/RESULT.md) و[verification.json](../reports/two_stage_phase7/verification.json) | قرار التفعيل والتحقق والاختبارات وحماية الأصول. |
| [README](README.md) و[TWO_STAGE_DATA_FLOW](TWO_STAGE_DATA_FLOW.md) وصفحات `PHASE_01…PHASE_07` المرتبطة في `README` | شرح الحالة الحالية والتنقل بين المكونات والمراحل والقيود. |
| [graphify-out/graph.json](../graphify-out/graph.json) و[GRAPH_REPORT.md](../graphify-out/GRAPH_REPORT.md) | خريطة علاقات مساعدة للتنقل؛ يؤكد الكود السلوك، ولا تعد الخريطة أصل تشغيل أو دليل اعتماد. |

لم يغير تحديث التوثيق هذه الملفات خارج `plan_explanation/`. ما زالت بعض تعليقات المصدر تصف سياق مرحلة أقدم، مثل عبارة التقييم في `ranking.py` أو المحرك المستقبلي في `history_update.py`؛ تصف هذه الخريطة الاستدعاءات الفعلية الحالية دون تعديل تلك التعليقات.
