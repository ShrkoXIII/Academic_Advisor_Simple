# ءخريطة الملفات المهمة

لقطة `2026-10-06`. «موجود مسبقًا» لا تعني أنه أُنشئ ضمن `Two-Stage`، و«متوقع» تعني مسارًا ذكرته الخطة لكنه غير موجود.


| الملف                                                               | المرحلة                       | الدور                                                     |
| ------------------------------------------------------------------- | ----------------------------- | --------------------------------------------------------- |
| `docs/architecture/RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md` | جميع البنود                   | مصدر النطاق والترتيب وسجل إتمام الأولى والثانية.          |
| `scripts/promote_shortlist_artifacts.py`                            | `Phase 1`                     | تدقيق المصدر ونشر نسخ `33` دون تدريب.                     |
| `src/recommendation/two_stage_artifacts.py`                         | `Phase 1`                     | عقود `33/47` والتحميل والتحقق وأدلة المصدر.               |
| `src/paths.py`                                                      | `Phase 1`، ملف معدل           | مركزية مسارات النشر الجديد وأصول المشروع.                 |
| `.gitattributes`                                                    | `Phase 1`، ملف معدل           | حفظ البايتات للنسخ المنشورة الثلاث.                       |
| `models/shortlist_v2/grade_model.txt`                               | `Phase 1`                     | مودل العلامة `33` المنشور.                                |
| `models/shortlist_v2/fail_model.txt`                                | `Phase 1`                     | مودل احتمال الفشل `33` المنشور.                           |
| `models/shortlist_v2/category_levels.json`                          | `Phase 1`                     | فئات `Stage 1` المثبتة.                                   |
| `models/shortlist_v2/manifest.json`                                 | `Phase 1`؛ سيستخدمه `Phase 7` | عقود وأصول المرحلتين وأدلة المصدر وحالة الاعتماد الحالية. |
| `tests/test_two_stage_artifacts.py`                                 | `Phase 1`                     | التحقق من النشر والعقود والعزل والرفض.                    |
| `src/recommendation/inputs.py`                                      | `Phase 2`، ملف معدل           | محولات المدخلات الجاهزة و`PreparedRecommendationInputs`.  |
| `src/recommendation/course_status.py`                               | `Phase 2`                     | تصنيف الحالة السابقة الرسمية.                             |
| `src/recommendation/constraints.py`                                 | `Phase 2`                     | أرصدة الفئات وقيود إعادة الراسب والمنسحب والخطط الممكنة.  |
| `src/features/feature_contract.py`                                  | `Phase 2`، ملف معدل           | تجهيز مصفوفة بميزات مختارة دون تغيير الافتراضي `47`.      |
| `src/experiments/course_only_core.py`                               | `Phase 2`، ملف معدل           | تفويض تجهيز مصفوفة التجربة `33` إلى المساعد المشترك.      |
| `src/recommendation/__init__.py`                                    | `Phase 2`، ملف معدل           | تصدير الواجهات الجديدة.                                   |
| `tests/test_two_stage_matrix.py`                                    | `Phase 2`                     | توافق التحويل السابق وترتيب `33/47`.                      |
| `tests/test_two_stage_payloads.py`                                  | `Phase 2`                     | الهوية والقيم الجاهزة والتصنيف والعزل.                    |
| `tests/test_two_stage_constraints.py`                               | `Phase 2`                     | الخطط المقيدة مقابل مرجع مستقل والكسور والصفر.            |




## مكونات موجودة قبل الخطة ستستخدمها المراحل


| الملف                                                               | المرحلة المستفيدة       | الدور                                                            |
| ------------------------------------------------------------------- | ----------------------- | ---------------------------------------------------------------- |
| `models/experiments/course_only_recommendation/`                    | `Phase 1` فقط عند النشر | مصدر الأصول الأصلية؛ لا يقرأه التحميل الجديد وقت التشغيل.        |
| `models/grade_regressor_v2.txt`                                     | `Phase 1/5`             | مودل العلامة الرسمي `47` المثبت.                                 |
| `models/fail_risk_classifier_v2.txt`                                | `Phase 1/5`             | مودل احتمال الفشل الرسمي `47` المثبت.                            |
| `models/model_metadata_v2.json`                                     | `Phase 1/5`             | عقد التدريب والمصدر الرسمي للمرحلة الثانية.                      |
| `data/artifacts/category_levels_v2.json`                            | `Phase 1/5`             | فئات المودلات الرسمية.                                           |
| `src/grade_scale.py` و`data/raw/v_acs_grade.parquet`                | `Phase 1/5`             | تحويل العلامة إلى نقاط وتثبيت نسخة محتوى المقياس.                |
| `src/features/temporal_features.py`                                 | `Phase 3/5`             | `CourseHistoryState` ومفاتيح التاريخ وميزات `Plan/Peer`.         |
| `src/features/frozen_history.py`                                    | `Phase 3/5`             | حفظ وتحميل التاريخ المجمد والتحقق من القطع.                      |
| `data/artifacts/history_v2/as_of_20243/` و`as_of_20251/`            | `Phase 3/5`             | حزم التاريخ السابقة؛ ليست مخرجات `Delta` جديد.                   |
| `src/recommendation/engine.py`                                      | `Phase 5`               | المحرك المحلي السابق، مرجع توافق `47`.                           |
| `src/recommendation/plan_generation.py`                             | `Phase 2/5`             | البحث الدقيق وإنتاج صفوف الخطط، دون تغيير من هذه المهمة.         |
| `src/recommendation/plan_scoring.py`                                | `Phase 4/5/6`           | تلخيص أكاديمي وترتيب سابق للمقارنة.                              |
| `reports/repeat_withdrawal_analysis/policy_candidates.json`         | `Phase 4/5/6`           | اقتراحات وصفية لاختبارات السياسة، دون اعتماد إنتاجي.             |
| `src/recommendation/benchmark.py`                                   | `Phase 6`               | أداة محلية سابقة؛ ليست برنامج القياس المصطنع الجديد.             |
| `docs/architecture/RECOMMENDATION_TWO_STAGE_BASELINE_VALIDATION.md` | قبل التنفيذ             | نتيجة قديمة `612 passed, 1 failed`، وليست نتيجة المراحل الحالية. |




## مسارات متوقعة وغير منفذة


| المسار المتوقع المذكور في الخطة          | المرحلة                                 | الدور المخطط                           |
| ---------------------------------------- | --------------------------------------- | -------------------------------------- |
| `src/recommendation/history_update.py`   | `Phase 3`                               | `Delta` والحفظ المرحلي والتبديل الذري. |
| `src/recommendation/balance_policy.py`   | `Phase 4`                               | مكونات التوازن ونطاق السياسة.          |
| `src/recommendation/shortlist.py`        | `Phase 5`، مرتبط باستراتيجيات `Phase 4` | اختصار الخطط إلى `≤50`.                |
| `src/recommendation/two_stage_engine.py` | `Phase 5`                               | ربط المرحلتين والتاريخ والاستراتيجيات. |


الخطة لا تثبت أسماء ملفات نهائية مستقلة لواجهة الاستراتيجيات أو تقرير المقارنة أو `Benchmark` الجديد أو اختبارات المراحل اللاحقة؛ لم نختلق مسارات لها. ملفات `Graphify cache` والملفات الثانوية مستبعدة من هذه الخريطة.