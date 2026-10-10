# شرح تنفيذ `Two-Stage Recommendation`

لقطة توثيق: **`2026-10-08`**، تشمل التنفيذ الحالي والتغييرات المحلية. الحالة: **`READY_FOR_STABILIZATION_REVIEW`**. اكتملت مراحل التنفيذ السبع، مع بقاء مشكلات تحقق وعقود تشغيل مفتوحة.

**عدد المراحل: 7.** تعني `COMPLETE` اكتمال نطاق التنفيذ المسجل لكل مرحلة؛ لا تعني اجتياز كل الحالات التشغيلية أو اعتماد `Stable Core v1`.

| المرحلة بحسب الخطة | الحالة | ما الذي نفذته؟ | افتح الشرح |
|---|---|---|---|
| `Phase 1 — Artifacts & Contracts` | `COMPLETE` | نشرت نسخ مودلات `33` وثبتت عقود `33/47` وأدلة المصدر وأضافت تحميلًا صارمًا. | [PHASE_01_ARTIFACTS_AND_CONTRACTS.md](PHASE_01_ARTIFACTS_AND_CONTRACTS.md) |
| `Phase 2 — Payload Adapters, Matrix Helper, Classification & Constraints` | `COMPLETE` | أضافت محولات المدخلات والتصنيف والقيود وتعميم المصفوفة، مع نتائج اختبارات وتحقق مسجلة. | [PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md](PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md) |
| `Phase 3 — History Delta & Atomic Swap` | `COMPLETE` | طبقت مجاميع فصل نهائي مع منع التكرار والتعارض، ونشرت حزمة جديدة قبل تبديل النسخة النشطة. | [PHASE_03_HISTORY_DELTA_SAVE_ATOMIC_SWAP.md](PHASE_03_HISTORY_DELTA_SAVE_ATOMIC_SWAP.md) |
| `Phase 4 — Balance & Independent Strategies` | `COMPLETE` | نفذت مكونات التوازن ومرشحي `balance_first / pareto` باستقلال اختيار المرحلتين. | [PHASE_04_BALANCE_METRICS_STRATEGIES.md](PHASE_04_BALANCE_METRICS_STRATEGIES.md) |
| `Phase 5 — Two-Stage Integration & Validation` | `COMPLETE` | ربطت `33 → ≤50 → 47` وأثبتت التوافق على عينات محددة وحدود الاختصار. | [PHASE_05_TWO_STAGE_INTEGRATION_VALIDATION.md](PHASE_05_TWO_STAGE_INTEGRATION_VALIDATION.md) |
| `Phase 6 — Corrected Benchmark & Strategy Evidence` | `COMPLETE` | قاست الكلفة والمفاضلات على حالات مصطنعة، وصححت أدلة إصدار العلامات غير المدعوم. | [PHASE_06_BENCHMARK_STRATEGY_APPROVAL.md](PHASE_06_BENCHMARK_STRATEGY_APPROVAL.md) |
| `Phase 7 — Approved Manifest & Revalidation` | `COMPLETE` | ثبتت اعتماد `pareto v1 → pareto v1` وفعلت التحميل من `Manifest` مع تثبيت الاختيارات طوال الطلب. | [PHASE_07_MANIFEST_POLICIES_REVALIDATION.md](PHASE_07_MANIFEST_POLICIES_REVALIDATION.md) |

**موضع التنفيذ الحالي:** انتهت بنود الخطة السبعة. أصبحت هذه الوثائق مرجعًا للمراجعة التدريجية؛ تحديثها لا يبدأ مراجعة `Contracts & Artifacts` أو تنفيذ إصلاحات.

- [TWO_STAGE_DATA_FLOW.md](TWO_STAGE_DATA_FLOW.md): المسار العام وحالة كل مكون.
- [FILE_MAP.md](FILE_MAP.md): الملفات المهمة وعلاقتها بالمراحل.
- [الخطة الأساسية](../docs/architecture/RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md): نطاق التنفيذ والبوابات.

## نقطة الدخول الفعلية

الواجهة المصدرة من [src/recommendation/__init__.py](../src/recommendation/__init__.py) هي `TwoStagePlanRecommender`، وتنفيذها في [two_stage_engine.py](../src/recommendation/two_stage_engine.py):

```python
from src.recommendation import TwoStagePlanRecommender

engine = TwoStagePlanRecommender.load()
result = engine.recommend_from_payloads(
    student_payload=ready_student_payload,
    request_payload=ready_request_payload,
    top_k=3,
)
```

المتغيران في المثال يمثلان مدخلات جاهزة وفق [Phase 2](PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md). يحمل `load()` الأصول والسياسات والتاريخ مرة واحدة. `top_k` بين `1` و`50`، والمخرج `status / metadata / recommendations`. التحديث المستقل متاح عبر `engine.update_history_from_payload(history_payload=...)`.

`load_for_evaluation()` وحقن مكونات المحرك يبقيان `evaluation_only / UNAPPROVED` حتى مع وجود `Manifest` معتمد. أما مسار `load()` المعتمد فيسجل `APPROVED / production_core`. هذه هوية سياسة داخل `Core` وليست شهادة جاهزية تشغيل خدمي. واجهة `src.recommend_local` ما زالت تستخدم `AcademicPlanRecommender` المحلي؛ لا تمثل نقطة دخول محرك المرحلتين، ولا توجد هنا طبقة `HTTP` جديدة.

## أساس الحكم وحدود الأدلة

| المصدر | ما استُخدم منه؟ |
|---|---|
| الكود والملفات الحالية | المرجع الأول لمسار التنفيذ وأسماء المكونات وحدود التحقق الفعلية. |
| [Manifest الحالي](../models/shortlist_v2/manifest.json) | اعتماد الاستراتيجيتين وتوليفتهما، `Balance`، العقود والبصمات والقيود التشغيلية. |
| `Implementation Progress` في [الخطة](../docs/architecture/RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md) | سجل تنفيذ كل مرحلة وتاريخها ونتائجها؛ أحدث سجل هو `Phase 7`. |
| [Phase 6 المصححة](../reports/two_stage_phase6/corrected/RESULT.md) و[Phase 7](../reports/two_stage_phase7/RESULT.md) | أدلة المفاضلات المصححة ثم الاعتماد والتحقق النهائي. |
| الوثائق والتقارير السابقة | سياق تاريخي؛ لا تتجاوز التنفيذ الحالي أو الأدلة المصححة. |

أرقام الاختبارات أدناه **نتائج تنفيذ سابقة مسجلة**، وليست تشغيلًا ضمن تحديث التوثيق. وجود الاختبار أو نجاح مجموعة معينة لا يثبت جميع الحالات التشغيلية.

| المرحلة | المركزة | المرتبطة | `Full pytest` وقت المرحلة |
|---|---:|---:|---|
| `1` | `68` | `108` | `680 passed, 1 failed, 6 subtests passed` |
| `2` | `125` | `258` | `805 passed, 1 failed, 6 subtests passed` |
| `3` | `61` | `352` | `866 passed, 1 failed, 6 subtests passed` |
| `4` | `97` | `445` | `963 passed, 1 failed, 6 subtests passed` |
| `5` | `91` | `529` | `1054 passed, 1 failed, 6 subtests passed` |
| `6` المصححة | `65` | `583` | `1119 passed, 1 failed, 6 subtests passed` |
| `7` | `160` | `646` | `1144 passed, 1 failed, 6 subtests passed` |

الفشل المشترك هو `capacity_63 / capaciy_63`. آخر تقرير يسجل `SKIPPED: 0`؛ الحزمة الكاملة ليست خضراء. أرقام المجموعات المرتبطة هي عدد الاختبارات الناجحة؛ تسجل بعض المراحل `6 subtests` إضافية أيضًا.

## الفروق والقيود المهمة

| المشكلة الحالية | الأثر وحدود الادعاء |
|---|---|
| `GradeScale` لا يرفض إصدار علامات غير مدعوم | يطبع `inputs.py` الهوية دون التحقق من وجودها في المقياس؛ تبدأ `GradeScale.convert()` بنقاط `0` وتصنيف `F` وتتركهما عند غياب الحزم المناسبة. قد يعود طلب ناجح بمقاييس خاطئة. تصحيح بيانات قياس `Phase 6` لا يصلح هذا المسار. |
| `capaciy_63` في المصدر مقابل `capacity_63` في الاختبار | فشل معروف في `tests/test_train_models.py` ما زال مفتوحًا. |
| استعادة أصول `Stage 2` من `Git` ونهايات الأسطر | البايتات المحلية المثبتة تختلف عن النسخة المستعادة من `Git`؛ تحويل الأسطر يغير `SHA-256` وقد يرفض التحميل. حماية `-text` المضافة تخص أصول `Stage 1` المنشورة. |
| حدود التشغيل غير معتمدة | `backend_max_candidate_count` و`recommendation_latency_sla` و`memory_budget_per_request` كلها `UNRESOLVED`. الحد `≤50` يخص الخطط التي تصل إلى `Stage 2`، لا عدد المواد أو كلفة البحث السابق. |
| الجودة الواقعية غير مثبتة | الأدلة المصطنعة والتوافق لا تثبت تحسن توصيات طلاب حقيقيين. `global_top_k_guaranteed=false`، و`Projected GPA` جمع إضافي لا يطبق استبدال علامات الإعادة. |

اعتمد الإنسان في `2026-10-08` كلًا من `stage1_shortlist_strategy=pareto v1` و`final_ranking_strategy=pareto v1` وتوليفتهما بصورة مستقلة. عبارات `UNAPPROVED` في مقدمة الخطة وسجلات المراحل السابقة تصف وقتها؛ أما بقاء الوصف نفسه في `load_for_evaluation()` فهو سلوك حالي مقصود.

الـ`Baseline` الذي يسجل `612 passed`، ونتائج `Phase 6` الأصلية ذات إصدار العلامات غير المدعوم، ليست أدلة الحالة الحالية. لا تُمحى تلك النتائج؛ يوضح [شرح Phase 6](PHASE_06_BENCHMARK_STRATEGY_APPROVAL.md) ما أُبطل وما بقي صالحًا.

## اكتمال التنفيذ وحدود الاعتماد

| الوصف | المعنى | الحالة الحالية |
|---|---|---|
| `Implementation Complete` | تنفيذ بنود الخطة السبعة وتسجيل أدلتها. | نعم، مع القيود المذكورة. |
| `Stable Core Approved` | قبول النواة بعد مراجعة الاستقرار ومعالجة أو قبول المشكلات صراحة. | غير حاصل؛ الحالة `READY_FOR_STABILIZATION_REVIEW`. |
| `Production Ready` | قبول عقود التشغيل والتكامل والبيئة والأداء وجودة الاستخدام المطلوبة. | غير مثبت وغير معتمد بهذه المراحل. |

## نطاق هذه المهمة

تحديث `2026-10-08` يقتصر على ملفات `Markdown` العشرة المرتبطة هنا داخل `plan_explanation/`. استُخدمت خريطة `graphify` للتنقل والتحقق من العلاقات، مع الرجوع إلى الكود ودون `graphify update`. لا تدريب أو `Benchmark` أو تشغيل توصية أو اختبارات مشروع جديدة، ولا تعديل كود أو بيانات أو مودلات أو `Manifest` أو تقارير تاريخية، ولا `Commit/Push`. التحقق الخاص بهذه المهمة يراجع التوثيق وروابطه ورموزه ونطاق التغييرات.

شجرة العمل مشتركة وبها تغييرات سابقة. رصدت المقارنة أثناء هذا التحديث إضافات متزامنة لتجربة `attempt_number_removal_20261008` وملفات رسم وذاكرة مؤقتة خارج نطاقه؛ لم تُعدّلها مهمة التوثيق أو تتراجع عنها. لذلك يخص قيد الملفات العشرة **تغييرات هذه المهمة**، وليس جميع التغييرات الظاهرة في `git status` للمشروع.
