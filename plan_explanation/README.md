# شرح تنفيذ `Two-Stage Recommendation`

لقطة توثيق: `2026-10-06`، عند `HEAD: 9cc3203` مع التغييرات المحلية الحالية. التوثيق يصف التنفيذ الموجود؛ لا يعتمد حالة الخطة وحدها.

**عدد المراحل: 7 بنود تنفيذ.** اسما الأولى والثانية من عناوين `Implementation Progress`، واسم الثالثة من `Next` الحالي. أسماء البنود `4–7` من نص قسم «ترتيب العمل وBenchmark والتسليم» حرفيًا؛ لا توجد لها عناوين تقدم تنفيذ بعد.

| المرحلة بحسب الخطة | الحالة | ماذا فعلت أو ستفعل بجملة واحدة؟ | افتح الشرح |
|---|---|---|---|
| `Phase 1 — Artifacts & Contracts` | `COMPLETE` | نشرت نسخ مودلات `33` وثبتت عقود `33/47` وأدلة المصدر وأضافت تحميلًا صارمًا. | [PHASE_01_ARTIFACTS_AND_CONTRACTS.md](PHASE_01_ARTIFACTS_AND_CONTRACTS.md) |
| `Phase 2 — Payload Adapters, Matrix Helper, Classification & Constraints` | `COMPLETE` | أضافت محولات المدخلات والتصنيف والقيود وتعميم المصفوفة، مع نتائج اختبارات وتحقق مسجلة. | [PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md](PHASE_02_PAYLOAD_ADAPTERS_MATRIX_CLASSIFICATION_CONSTRAINTS.md) |
| `Phase 3 — History Delta والحفظ immutable والتحويل الذري` | `NOT IMPLEMENTED YET` | ستضيف مجاميع فصل نهائي إلى نسخة تاريخ ثم تنشرها وتبدل المرجع النشط بأمان. | [PHASE_03_HISTORY_DELTA_SAVE_ATOMIC_SWAP.md](PHASE_03_HISTORY_DELTA_SAVE_ATOMIC_SWAP.md) |
| `Phase 4 — تنفيذ مقاييس Balance وواجهة الاستراتيجيات ومرشحي التقييم المستقل لكل مرحلة.` | `NOT IMPLEMENTED YET` | ستنفذ مكونات التوازن ومرشحي ترتيب مستقلين للمرحلتين. | [PHASE_04_BALANCE_METRICS_STRATEGIES.md](PHASE_04_BALANCE_METRICS_STRATEGIES.md) |
| `Phase 5 — ربط المرحلتين واختبارات Parity وOracle وتوليفات الاستراتيجيات والتقرير التاريخي والسياساتي.` | `NOT IMPLEMENTED YET` | ستربط مسار `33 → ≤50 → 47` وتثبت توافقه وحدود الاختصار. | [PHASE_05_TWO_STAGE_INTEGRATION_VALIDATION.md](PHASE_05_TWO_STAGE_INTEGRATION_VALIDATION.md) |
| `Phase 6 — تنفيذ Benchmark وعرض نتائج المرحلتين والمفاضلات لاعتماد الاستراتيجيات بصورة مستقلة.` | `NOT IMPLEMENTED YET` | ستقيس الكلفة والمفاضلات وتعرض أدلة اعتماد كل استراتيجية وتوليفتهما. | [PHASE_06_BENCHMARK_STRATEGY_APPROVAL.md](PHASE_06_BENCHMARK_STRATEGY_APPROVAL.md) |
| `Phase 7 — تثبيت السياسات المعتمدة في Manifest وإعادة التحقق وتحديث الوثائق والرسم.` | `NOT IMPLEMENTED YET` | ستثبت القرارات المعتمدة وتعيد التحقق من مسار التفعيل. | [PHASE_07_MANIFEST_POLICIES_REVALIDATION.md](PHASE_07_MANIFEST_POLICIES_REVALIDATION.md) |

**موضع التنفيذ الحالي:** اكتملت `Phase 2`، والتالية `Phase 3` ولم تبدأ. بقيت المراحل `3–7` غير منفذة؛ اكتمال المدخلات لا يعني اكتمال المحرك.

- [TWO_STAGE_DATA_FLOW.md](TWO_STAGE_DATA_FLOW.md): المسار العام وحالة كل مكون.
- [FILE_MAP.md](FILE_MAP.md): الملفات المهمة وعلاقتها بالمراحل.
- [الخطة الأساسية](../docs/architecture/RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md): نطاق التنفيذ والبوابات.

## أساس الحكم وحدود الأدلة

| المصدر | ما استُخدم منه؟ |
|---|---|
| الخطة، خصوصًا قسمي تقدم `Phase 1/2` | الأهداف وترتيب العمل والنتائج المسجلة. |
| `git diff` والملفات غير المتتبعة | فصل تغييرات `Phase 1` عن المكونات المحلية الجديدة للبند الثاني. |
| الكود وملفات الاختبار الحالية | أسماء التوابع والسلوك الذي تستهدف الاختبارات التحقق منه. |
| `models/shortlist_v2/manifest.json` والملفات المثبتة فيه | العقود والبصمات وحالة الاعتماد؛ فحص قراءة فقط للملفات الثمانية أعطى اختلافات `[]`. |
| سجلات `recommendation_phase1_miy7l3z5` المحلية | نتيجة `Full pytest` النهائية، تطابق توقعات `32` صفًا مصطنعًا، وسلامة الملفات وقت تنفيذ الأولى. |

لم تشغل مهمة التوثيق اختبارات المشروع أو تدريبًا أو توصية أو `Benchmark`. أرقام `Phase 1/2` نتائج تنفيذ مسجلة؛ المراحل اللاحقة تستخدم `Test result not recorded.` لا نجعل وجود اختبار دليلًا على نجاح تشغيله.

## الفروق والقيود المهمة

لم يثبت اختلاف وظيفي بين نطاق البندين المكتملين والتنفيذ المراجع. `Next` أسفل سجل الأولى يصف تسليمها وقتها؛ `Next` الأحدث أسفل الثانية هو مرجع المرحلة الحالية. اكتمال المكونات لا يعتمد استراتيجيات الترتيب أو عقد النقل الحقيقي.

- `Production Ranking Strategy: UNAPPROVED`؛ اعتماد `stage1_shortlist_strategy` و`final_ranking_strategy` و`combination` ما زال مؤجلًا.
- لا يوجد `TwoStagePlanRecommender` أو محرك متكامل للمرحلتين في النسخة الحالية.
- الفشل القديم `capaciy_63` مقابل `capacity_63` قائم؛ أحدث نتيجة مسجلة بعد الثانية `805 passed, 1 failed, 6 subtests passed`.
- بصمات `Stage 2` تثبت بايتات الملفات المحلية؛ تحويل نهايات الأسطر أثناء النقل قد يجعل التحميل يرفضها.
- وثيقة [Baseline](../docs/architecture/RECOMMENDATION_TWO_STAGE_BASELINE_VALIDATION.md) تصف لقطة أقدم قبل التنفيذ (`612 passed`)، وليست حالة التنفيذ الحالية.

## نطاق هذه المهمة

الملفات التي كتبتها هذه المهمة كلها توثيق داخل `plan_explanation/`. بقيت بصمات الملفات الـ`877` تحت `models/` و`data/` ثابتة، وكذلك `scripts/` و`reports/` و`.gitattributes`. ظهر أثناء القراءة تحديث متزامن في `src/` و`tests/` والخطة سجل إتمام الثانية؛ أعيدت مراجعة التوثيق على هذه الحالة، ولم تكتب مهمة التوثيق تلك التغييرات. تحديثات `graphify` مساعدة؛ لم تنفذ هذه المهمة مرحلة جديدة أو تصلح خللًا.
