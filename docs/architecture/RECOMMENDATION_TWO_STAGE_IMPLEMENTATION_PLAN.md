Status: APPROVED FOR IMPLEMENTATION
Production Ranking Strategy: UNAPPROVED
Balance Policy: B_observed_middle_v1
Date: 2026-10-05

# الخطة النهائية: 33 → 50 → 47 مع Balance كهدف فعلي

الموافقة هنا تخص تنفيذ المكونات والاختبارات والتقييم. لا تعني اعتماد استراتيجية Production Ranking قبل مراجعة نتائجها. لا يبدأ تنفيذ Production code ضمن خطوة حفظ هذه الوثيقة.

## 1. القرارات الثابتة والواجهات

**Balance هدف مستقل في ترتيب الخطط، ويمكنه تغيير الترتيب رغم اختلاف توقعات GPA والفشل.** تعرض مكوناته منفصلة، وتُقارن استراتيجيات دمجه قبل اعتماد استراتيجية Production. لا توجد أوزان أو استراتيجية نهائية معتمدة حاليًا.

تُقيّم استراتيجيتا المرحلتين بصورة مستقلة:

```text
stage1_shortlist_strategy
final_ranking_strategy
```

قد تتطابقان، لكن التطابق يجب أن يكون نتيجة للتقييم، لا افتراضًا مسبقًا. تُوثق وتُعتمد هوية وإصدار ونتائج كل استراتيجية بصورة منفصلة، وتُختبر توليفاتهما عبر المرحلتين قبل التفعيل.

يبقى المسار:

```text
Backend inputs + Frozen History
→ 33-feature Grade + Fail لكل Candidate
→ جميع الخطط الممكنة بالساعات الدقيقة والقيود الرسمية
→ stage1_shortlist_strategy تشمل Balance
→ أفضل 50 كحد أقصى
→ إضافة 14 Plan/Peer features
→ official 47-feature Grade + Fail
→ final_ranking_strategy تشمل Balance
→ Top K
```

### نتيجة Audit قبل التنفيذ

- توجد مودلات 33 مدربة فعلًا في `D:/AI/Real projects/Academic_Advisor_Simple/models/experiments/course_only_recommendation/`: `grade_regressor.txt` و`fail_risk_classifier.txt` و`category_levels.json` و`model_metadata.json`.
- فُحصت ملفات LightGBM نفسها: `feature_name()` وعدد الميزات وترتيبها و`pandas_categorical` تطابق العقود وCategories المحفوظة. بصمات المصدر والـArtifacts المذكورة في Metadata صحيحة وقت Audit.
- عقد Stage 1 هو `BASE_FEATURES − PLAN_CONTEXT_COLUMNS` مع الحفاظ على ترتيب العقد الرسمي: 28 Numeric + 5 Categorical = 33. Stage 2 تستخدم 42 Numeric + 5 Categorical = 47.
- Grade33 وGrade47 يتنبآن بـ`final_mark`، ثم GradeScale يحول العلامة إلى Points. Fail33 وFail47 يتنبآن باحتمال `is_fail == (final_mark < 50)`، لا بالحالة الرسمية السابقة للمادة.
- Cutoff تدريب المودلات الأربعة هو `20243`. Stage 2 توثقه في `course_history.initial_history_cutoff`؛ V2 مثبت بالمسارات ومصدر التدريب رغم غياب `dataset_version` الصريح من Metadata القديمة.
- يمكن تحميل Artifacts مباشرة بواسطة LightGBM دون استيراد `src.experiments`. تجهيز Matrix الرسمي الحالي إنتاجي بالفعل.
- لا يوجد Blocker متعلق بمودلات 33. يلزم استكمال عقد الحالة السابقة وحد إعادة الراسب في Backend قبل التكامل الحقيقي. اعتماد استراتيجيات Ranking وحدود التشغيل بوابات مستقلة موثقة أدناه.

بصمات مودلي 33 التي فُحصت:

```text
Grade33: 5b300050c974a68a5bc62dee923f2236878eb0f1a9e09e2c4321c4e124f1df97
Fail33:  dfb2325a6728151d26d02653a665be25c74e6ee3e51dd3f7be57af61212b5470
Levels:  4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6
Meta33:  6af88c246ed7649fba227eb953d1d33ac639109596c5b4a02fbdb17f387f9592
```

مصدر الرسم المستخدم في Audit:

```text
C:/Users/ASUS/.codex/visualizations/2026/10/03/01a10196-e9c3-7641-b6fe-45613c0ef920/architecture-analysis/graphify-out/graph.json
```

طوبقت علاقاته بالمصدر الحالي. إضافات Balance أحدث من هذا الرسم، وتحقق منها Audit من كود التشخيص والتقرير مباشرة. هذه المسارات دليل Audit؛ لا يصبح الرسم أو Reports مدخلًا لServing.

تُنشر نسخة مطابقة للبايتات من مودلي 33 وCategories تحت:

```text
D:/AI/Real projects/Academic_Advisor_Simple/models/shortlist_v2/
    grade_model.txt
    fail_model.txt
    category_levels.json
    manifest.json
```

Manifest يثبت أسماء الميزات وترتيبها وCategories والأهداف وCutoff ومعالجة المخرجات وبصمات المودلات و`grade_scale_version` و`grade_scale_sha256` وProvenance الأصلية. تُحفظ بصمات مصدر التدريب الحالية قبل أي تعديل للكود. لا تُعدّل Metadata التجارب لتعويض تغير بصمات مصدرها لاحقًا، ولا يُضعف فحص الصلاحية في Loader التجريبي.

تظل Artifacts المرحلة الثانية الرسمية:

```text
D:/AI/Real projects/Academic_Advisor_Simple/models/grade_regressor_v2.txt
D:/AI/Real projects/Academic_Advisor_Simple/models/fail_risk_classifier_v2.txt
D:/AI/Real projects/Academic_Advisor_Simple/models/model_metadata_v2.json
D:/AI/Real projects/Academic_Advisor_Simple/data/artifacts/category_levels_v2.json
```

الواجهات منفصلة:

```python
engine = TwoStagePlanRecommender.load()

engine.update_history_from_payload(
    history_payload=history_response,
)

result = engine.recommend_from_payloads(
    student_payload=student_response,
    request_payload=recommendation_request,
    top_k=3,
)
```

`load()` يحمّل المودلات الأربعة وCategories كل مرحلة وGradeScale وManifests وأحدث Frozen History محلية مكتملة وصحيحة مرة واحدة. `top_k` افتراضيًا 3 ومجاله `1..50`. يُرجع المتاح إذا كان أقل. تبقى واجهات Local وBacktesting القديمة على سلوكها الحالي.

لا يشمل هذا التغيير HTTP أو FastAPI أو PHP أو Deployment. مستقبلًا يمكن لـService/Backend clients إحاطة هذا Core دون نقل Logic المودلات إلى طبقة النقل.

## 2. المدخلات والتاريخ والقيود

### Frozen History

- Payload التاريخ هو **Delta لفصل نهائي واحد**، ويُحدّث عبر مسار مستقل عن Recommendation. Backend يرسل الفصول النهائية غير المطبقة بترتيبها.
- تُضاف المجاميع إلى نسخة من State الموجودة، دون إعادة بناء التاريخ القديم أو تطبيق أوزانه مرة أخرى. لا `backend_uniform_1` للتاريخ الكامل.
- للفصول الجديدة بعد 2022، وزن Delta فقط يساوي 1:

```text
count → raw_count وeffective_support
fail_count → fail_sum
retake_count → retake_sum
mark_sum وattempt_sum → كما وردا
```

- لا تُمرر صفوف Aggregates إلى `CourseHistoryState.update()` الخام؛ يُضاف Helper مستقل مثل `apply_history_delta()` لتطبيق المجاميع.
- تُستخدم `build_history_keys()` الحالية وLevels التالية، مع تقريب الساعات الحالي للـHistory keys فقط:

```text
1. degree_id + course_id
2. course_id
3. degree_id + plan_requirement_type_id + rounded_course_credits
4. faculty_id + plan_requirement_type_id + rounded_course_credits
5. plan_requirement_type_id + rounded_course_credits
6. global
```

- تبقى `smoothing_k=20` و`min_support=20` وتعريف `course_history_missing = (fallback_level >= 3) or (effective_support < 20)`.
- تُحسب بصمة Delta بعد تطبيع تمثيل القيم وترتيب الصفوف. نفس الفصل ونفس البصمة: `already_applied` دون تكرار الإضافة أو الرجوع بالنسخة النشطة إلى نسخة أقدم. نفس الفصل وبصمة مختلفة: `CONFLICT`. تحديث أقدم غير مسجل يُرفض كتحديث خارج الترتيب.
- المسار: Clone → Apply → Validate → Save staging → Reload/verify → Publish immutable bundle → Atomic swap. فشل التحديث يبقي النسخة السابقة، ولا يستبدل أي Bundle قديمة.
- كل Recommendation تلتقط مرجع State وMetadata واحدة عند بدايتها وتستخدمهما طوال المرحلتين؛ Requests الجديدة بعد Swap تستخدم النسخة الجديدة.
- Metadata تشمل `as_of_part`, `previous_as_of_part`, `previous_history_sha256`, `delta_part`, `delta_sha256`, `new_history_sha256`, `created_at`, `feature_engineering_version`، إضافة إلى Metadata اللازمة للتوافق مع Loader الحالي.

Serving يقبل فقط:

```python
history_as_of_part < target_part
```

التاريخ الأقدم من الفصل السابق مباشرة مسموح، مع Metadata توضح قِدمه؛ Current/Future history ممنوع. قواعد Backtesting تبقى مستقلة، ولا تتغير بصمت. مثال `history=20253, target=20262` صالح إذا كان 20253 أحدث تاريخ نهائي متاح محليًا. أحدث Bundle فعلية وقت Audit هي 20251، وليست أمثلة الفصول الجديدة.

### Snapshot وCandidates

- تُستخدم قيم Backend الجاهزة: `student_id`, `degree_id`, `faculty_id`, `part_id`, `grade_version_id`, `diploma_type_id`, `diploma_gpa`, `gpa_prev_1`, `gpa_prev_2`, `start_agpa_points`, `start_total_in_courses`, `start_total_in_credits`, `prior_total_reg_courses`, `prior_total_reg_credits`, `prior_total_fail_courses`, `prior_total_fail_credits`, `prior_fail_credit_ratio`, `prior_registered_semesters`, `observed_gap_semesters`, `degree_credits_count`, `current_gpa_credits`.
- اشتقاق Student features في Python يقتصر على `gpa_trend_delta`, `gpa_trend_missing`, `part_semester`. عند تعذر حساب Trend: القيمة Missing وFlag يساوي 1. `part_semester = part_id % 10`.
- لا إعادة حساب Ratio أو Gap، ولا `last_active_semester`.
- بيانات Candidate المباشرة: `course_id`, `course_name`, `course_credits`, `attempt_number`, `plan_course_type_id`, `plan_requirement_type_id`, `plan_year_order`, `plan_semester_order`, `plan_credits_count`.
- لا إعادة حساب Attempts أو Join مع Catalog محلي. يُوثق تعريف Attempt المتوافق مع التدريب دون استنتاج عدد مرات الرسوب منه.
- الحالة السابقة الرسمية تأتي عبر `previous_course_status` الدلالي أو `previous_finish_status` الرسمي. عند ورودهما معًا يجب أن يتطابق معناهما؛ الحقول المتعارضة تُرفض.

التصنيف:

| الحالة السابقة | Candidate group |
| --- | --- |
| `NEW` / `NEVER_TAKEN` | `NEW` |
| `F` / `FE` / `FA` أو `FAILED` | `FAILED_RETAKE` |
| `W` أو `WITHDRAWN` | `WITHDRAWN_RETAKE` |
| `P` أو `PASSED`، Other، Unknown، Unresolved | `OTHER_PREVIOUS` |

Missing/Unknown لا يصبح NEW أو Failed. لا يُستنتج سبب الإعادة من العلامة أو `attempt_number`. أكواد `D/Z/ST/T` الأخرى و`I/IP` غير المحسومة تبقى خارج Failed/Withdrawn، وفق Mapping المصدر الرسمي.

Backend مسؤول عن Eligibility. يُصفّى الرفض الصريح قبل Stage 1؛ لا تُحذف مواد راسبة لتطبيق حد ساعات الإعادة، لأنه قيد على الخطة.

### Hard constraints

```python
exact_target = (
    target_credits
    if target_credits is not None
    else max_credits
)

remaining = max(
    0,
    requirement_max_credits
    + allowed_overflow_credits
    - completed_credits
    - reserved_credits,
)
```

- Range ‏12–18 يعني **18 بالضبط**، دون تخفيض تلقائي. تبقى Validation الحالية لطلب هدف موجب وحدود سليمة.
- يُقبل اسم Requirement القديم `max_credits` ويُطبّع داخليًا إلى `requirement_max_credits`؛ اختلافهما عند ورودهما معًا خطأ مدخلات.
- تكلفة كل مادة مختارة هي كامل `course_credits` ضمن فئتها، بما فيها Repeat. أي Candidate دون Requirement Policy مقابلة يجعل الطلب ناقصًا ويُرفض.
- مجموع ساعات `FAILED_RETAKE` لا يتجاوز `allowed_failed_repeat_credits` القادم من Backend، وهو حد أقصى لا حد أدنى.
- `allowed_withdrawn_repeat_credits` مستقل ويُطبق فقط إذا أرسله Backend.
- `allowed_fail_credits` و`allowed_pass_position_type` يبقيان Metadata دون تفسير إضافي؛ لا يُستبدل الحد الصريح الجديد بالاسم القديم الغامض.
- حد إعادة الراسب يستخدم الحالة الرسمية؛ لا يستخدم احتمالات Fail model أو `expected_failed_credits`.
- مواد صفر ساعة اختيارية، تدخل في هوية الخطة وCounts وPlan/Peer context. لا تُدمج خطتان مختلفتان في اختيارها بوصفهما خطة واحدة.
- عند غياب خطة تحقق القيود والهدف: `status="no_feasible_plan"`.

## 3. تنفيذ التوقعات وBalance والترتيب

### Features والتوقعات

```python
stage1_features = [
    feature for feature in BASE_FEATURES
    if feature not in PLAN_CONTEXT_COLUMNS
]
assert len(stage1_features) == 33
```

لا يُنشأ Contract يدوي مستقل للـ33. تُستبعد الـ14 Plan/Peer columns الحالية فقط، مع الحفاظ على ترتيب `BASE_FEATURES`.

- Matrix helper مشترك يحافظ على Numeric coercion و`float32` وMissing/Unknown Categories وترتيب الميزات؛ يبقى الاستخدام القديم للـ47 مطابقًا.
- Stage 1: استدعاء واحد لكل مودل على **N صفوف**، دون Plan/Peer features، لجميع Candidates المؤهلة قبل قيود الخطط.
- Grade predictions تُقص إلى `[0,100]` ثم تُحوّل بواسطة GradeScale؛ احتمالات الفشل تُقص إلى `[0,1]`. المخرجات غير المحدودة أو ذات الشكل الخاطئ تُرفض. لا Model مستقل للـPoints.
- البحث الحالي باستخدام Decimal/وحدات صحيحة يستمر دون اختيار أفضل المواد مسبقًا أو تغيير خوارزمي. تُفحص القيود الرسمية قبل Shortlisting.
- لكل خطة: `expected_quality_points = sum(credits * expected_points)` و`expected_failed_credits = sum(credits * fail_probability)`.
- Stage 2 يقيّم Course-in-Plan rows للـShortlist فقط، باستخدام حساب الـ14 Plan/Peer الحالي و`group_columns=["plan_id"]`. ظهور المادة في خطط مختلفة يُقيّم منفصلًا.
- توقعات Stage 2 وحدها تدخل النتيجة النهائية، لا توقعات Stage 1.

لكل خطة تُعرض المقاييس:

```text
expected_quality_points
expected_failed_credits
expected_plan_gpa
projected_cumulative_gpa
expected_cumulative_gpa_gain
```

```python
projected_cumulative_gpa = (
    start_agpa_points * current_gpa_credits
    + expected_quality_points
) / (current_gpa_credits + plan_total_credits)
```

لا يُستبدل `current_gpa_credits` بـ`prior_total_reg_credits` في مسار Backend. يبقى الحساب Additive دون Grade Replacement، مع `projected_gpa_requires_repeat_policy` الواضح.

### Balance components

تعرض منفصلة:

```text
failed_retake_credits
withdrawn_retake_credits
new_credits
other_previous_credits

failed_ratio
withdrawn_ratio
total_previous_ratio

failed_balance_penalty
withdrawn_balance_penalty
total_previous_balance_penalty

scope_applicable
component_active_flags
disabled_reasons
```

`total_previous_ratio` يشمل Failed+Withdrawn فقط. لا تُجمع العقوبات في Scalar مبهم، ولا تُضاف أوزان أو Scaling ضمني. New يمثل الجزء المتبقي في المرجع المناسب، ولا يتحول إلى Quota مستقلة.

نطاقات `B_observed_middle_v1`:

| المكوّن | النطاق |
| --- | --- |
| Failed | `1/6 … 4/17` |
| Withdrawn | `0 … 3/17` |
| Failed+Withdrawn | `1/6 … 2/7` |

```python
distance = max(lower - ratio, 0, ratio - upper)
```

تظل السياسة ضمن المرجع المعتمد: فصول 1 و2، حمل 12–18، وخطط دون `OTHER_PREVIOUS`. يُعطّل المكوّن عند غياب Candidates مؤهلة ذات ساعات موجبة من فئته. النطاق الحساس القريب من 25% ليس حدًا صلبًا بديلًا.

**الخطة خارج النطاق المفضل تبقى Feasible.** لا Minimum Retake، ولا سقف تاريخي صلب، ولا تعديل للتوقعات بسبب Balance. لا تُقرأ Reports أو Diagnostics في Serving؛ تُحفظ السياسة المحلية بإصدار مستقل.

### واجهة ترتيب مشتركة مع استراتيجيتين مستقلتين

تُفصل حسابات المقاييس عن استراتيجية ترتيبها. تستقبل الواجهة المقاييس الأكاديمية ومكونات Balance، وتنتج ترتيبًا كليًا ثابتًا. مشاركة الواجهة لا تفرض مشاركة الاستراتيجية.

يُحسب `stage1_projected_cumulative_gpa` من توقعات Stage 1 باستخدام المقام نفسه المستخدم في Stage 2 لتسهيل المقارنة بوحدات متسقة؛ هذا مقياس خطة وليس Feature إضافية للمودل.

يُختبر مرشحان **غير معتمدين للإنتاج** لكل مرحلة بصورة مستقلة:

1. **Balance-first:** عقوبة Failed، ثم Failed+Withdrawn، ثم Withdrawn، ثم المقاييس الأكاديمية والهوية الثابتة.
2. **Pareto-based:** بناء Fronts باستخدام GPA والفشل وكل عقوبة Balance منفصلة؛ ثم ترتيب كامل داخل كل Front بأولوية Balance المذكورة، ثم المقاييس الأكاديمية والهوية.

الترتيب الأكاديمي القديم يستخدم **مرجع مقارنة تشخيصيًا فقط**: Stage 1 بجودة Points نزولًا، ثم ساعات الفشل صعودًا، ثم sorted course tuple؛ والنهائي بـProjected cumulative GPA نزولًا، ثم ساعات الفشل صعودًا، ثم Plan GPA نزولًا، ثم Plan ID. لا يصبح Fallback إنتاجيًا يعيد Balance إلى Tie-breaker.

في اختبارات نطاق التطبيق المختلط، يُختبر ترتيب الخطط المشمولة داخل مواقعها في المرجع الأكاديمي، مع إبقاء مواقع الخطط غير المشمولة. هذه قاعدة مرشحة تخضع للتقرير والاعتماد؛ تعطيل Balance لا يُعامل كعقوبة صفر مثالية أو كسبب رفض.

استراتيجية Pareto تُختبر أولًا على مجموعات Synthetic صغيرة كاملة. لا يُفترض أن Fronts وحدها تحدد Top 50 أو Top K، ولا تُنشر قبل تحديد اختيار كامل والتحقق من تكلفته.

هوية الخطة ثابتة من sorted course tuple وتمثيل JSON canonical وبصمة SHA-256. إعادة ترتيب Candidates لا تغير هوية الخطة أو Tie ordering.

التقييم والاعتماد مستقلان:

```text
Evaluate and approve stage1_shortlist_strategy independently.
Evaluate and approve final_ranking_strategy independently.
Evaluate their cross-stage combinations and shortlist effects.
They may be identical only as an outcome of evaluation.
```

يبقى Top K الأفضل حسب الاستراتيجية النهائية وتوقعات 47 **ضمن Shortlist المرحلة الأولى فقط**، دون Guaranteed Global Top-K.

Result Metadata تشمل بصمات التاريخ والمودلات وCategories و`grade_scale_version` و`grade_scale_sha256`، إصدارات العقود والسياسات، Input fingerprint، أعداد Candidates والخطط الممكنة والمختصرة والمقيّمة، والسياسات المطبقة. تُحفظ `stage1_shortlist_strategy` و`final_ranking_strategy` وإصدار واعتماد كل منهما بصورة منفصلة، مع إشارة Additive projection وحدود الـShortlist.

## 4. التحقق وبوابتا اعتماد الاستراتيجيات

### Synthetic tests

- إثبات أن Balance يغير ترتيب خطط ذات **GPA أو احتمالات فشل مختلفة** في كل مرحلة؛ تطبيق Tie-only يفشل هذا الاختبار.
- تغيير المقاييس الأكاديمية دون تغيير Balance، والعكس، مع عرض المفاضلة.
- صحة كل مكوّن ونطاقه وFlag تفعيله، دون جمع أو وزن مخفي.
- بقاء الخطط خارج النطاق ممكنة، وصحة NEW-only عند غياب الإعادات المؤهلة.
- معالجة نطاق التطبيق المختلط دون أفضلية اصطناعية للمكونات المعطلة.
- ترتيب كلي ثابت، دون Comparator غير متعدٍ أو اعتماد على ترتيب Candidates.
- مقارنة Shortlist كل مرشح للمرحلة الأولى بـOracle مستقل على جميع الخطط الصغيرة، وتقييم مرشحي الترتيب النهائي بصورة مستقلة على Shortlist ثابتة.
- اختبار توليفات Stage 1 × Final، بما فيها استراتيجيات مختلفة، دون Assertion يشترط التطابق.
- حالة تتجاوز 50 خطة، مع توقعات Stage 2 مصطنعة لجميع الخطط للمقارنة التشخيصية: قياس Shortlist overlap وفقد الخطط الأفضل أو الأكثر توازنًا. لا يشغّل المحرك الفعلي Stage 2 خارج Shortlist.
- استمرار تطابق ميزات وتوقعات Stage 2 مع المسار الحالي للخطط نفسها.
- اختبارات Artifact promotion على Synthetic fixture: الأصل والنسخة المنسوخة ينتجان التوقعات نفسها. تغير Feature name/order/count أو Categories أو Target/objective أو Model/GradeScale hash يمنع Load.
- History: Delta فوق تاريخ قديم موزون، old State/Bundle/weights unchanged، وعدم إعادة تطبيق الوزن القديم، Same-hash idempotency وDifferent-hash conflict وفشل الحفظ وتزامن Recommendation مع Update.
- Temporal integrity: قبول التاريخ النهائي الأقدم، منع Current/Future history، ومنع Cutoff تدريب حالي أو مستقبلي.
- Snapshot/Candidates: عدم إعادة حساب Ratio أو Gap أو Attempt؛ Trend وMissing وSemester صحيحة؛ فحص هوية الطالب والاختصاص والفصل؛ وتصنيف الحالة دون استخدام العلامة.
- Stage 1: Exactly N rows لكل مودل، دون Plan/Peer features أو حذف مواد بسبب قيد خطة.
- Search: Exact upper target دون Lower fallback، حدود الفئات وOverflow وحدود الراسب والمنسحب، Fractional/Zero credits، Ties، ترتيب المدخلات، أقل من 50، وNo feasible plan.
- Stage 2: دخول Shortlist فقط وتطابق الـ14 Context features والتوقعات والملخصات مع المسار الحالي عند تقييم الخطط نفسها.
- Isolation: عدم اعتماد Serving على Experiments أو Trainers، وفحص بصمات الـArtifacts والبيانات والتاريخ الموجودة قبل وبعد التنفيذ.

### Historical-policy tests

تُقرأ التقارير المحفوظة في `D:/AI/Real projects/Academic_Advisor_Simple/reports/repeat_withdrawal_analysis/`، ومنها `policy_candidates.json` وتركيبات الساعات المجمعة، دون تشغيل Recommendation على طلاب حقيقيين.

تتحقق الاختبارات من النطاق والمقامات والتصنيف وتفعيل المكونات وتوزيع العقوبات. تُنشأ Fixtures من التركيبات المرصودة بهويات وتوقعات Synthetic، مع توثيق هذا الفصل. النسب والاحتمالات التاريخية وصفية وليست أوزانًا معتمدة.

التقارير الحالية لا تحتوي بدائل Candidates المؤهلة أو توقعات الخطط البديلة أو جميع السياسات الجامعية التاريخية. لذلك **لا تثبت وحدها أفضل مفاضلة GPA–Balance أو تحسن نتائج الطلاب**.

### تقرير المقارنة والاعتماد المستقل

يعرض التقرير لكل مرشح ومرحلة:

- تغير GPA المتوقع وساعات الفشل المتوقعة وكل عقوبة Balance منفصلة.
- جودة واحتفاظ وتنوع الـShortlist لمرشحي `stage1_shortlist_strategy`.
- تغير Top K لمرشحي `final_ranking_strategy` على Shortlists ثابتة، ثم أثر توليفات المرحلتين.
- Shortlist وTop-K overlap مقابل المرجع الأكاديمي.
- أمثلة مفاضلة واضحة وحساسية الحدود والنطاق والمواد ذات صفر ساعة.
- صحة الترتيب وكلفته وحدود الأدلة التاريخية.

بعد مراجعة التقرير يُعتمد اختيار وإصدار ومعاملات، إن وجدت، **لكل مرحلة بصورة مستقلة**. لا اختيار تلقائي بسبب تشابه الخطط مع التسجيل التاريخي، ولا اشتراط أن تكون الاستراتيجيتان متطابقتين.

حتى الاعتماد:

```text
stage1_shortlist_strategy.approval_status = UNAPPROVED
final_ranking_strategy.approval_status = UNAPPROVED
production_ranking_strategy = UNAPPROVED
```

يمكن اختبار المكونات والمرشحين، لكن تحميل المسار الإنتاجي الجديد يرفض التفعيل دون اعتماد المرحلتين وتوليفتهما. لا Default بأوزان غير معتمدة أو Balance عند التعادل فقط.

## 5. ترتيب العمل وBenchmark والتسليم

1. تثبيت Audit وبصمات المصدر، ثم نشر نسخ مودلات 33 وManifests.
2. تنفيذ Payload adapters وMatrix helper والتصنيف والقيود.
3. تنفيذ History Delta والحفظ والتحويل الذري.
4. تنفيذ مقاييس Balance وواجهة الاستراتيجيات ومرشحي التقييم المستقل لكل مرحلة.
5. ربط المرحلتين واختبارات Parity وOracle وتوليفات الاستراتيجيات والتقرير التاريخي والسياساتي.
6. تنفيذ Benchmark وعرض نتائج المرحلتين والمفاضلات لاعتماد الاستراتيجيات بصورة مستقلة.
7. تثبيت السياسات المعتمدة في Manifest وإعادة التحقق وتحديث الوثائق والرسم.

المكونات الجديدة المتوقعة:

```text
D:/AI/Real projects/Academic_Advisor_Simple/src/recommendation/two_stage_engine.py
D:/AI/Real projects/Academic_Advisor_Simple/src/recommendation/shortlist.py
D:/AI/Real projects/Academic_Advisor_Simple/src/recommendation/balance_policy.py
D:/AI/Real projects/Academic_Advisor_Simple/src/recommendation/history_update.py
D:/AI/Real projects/Academic_Advisor_Simple/src/recommendation/course_status.py
```

التعديلات على الموجود تشمل `D:/AI/Real projects/Academic_Advisor_Simple/src/paths.py`، وArtifact loading وInputs وPlan generation/two-stage ranking داخل `D:/AI/Real projects/Academic_Advisor_Simple/src/recommendation/`، و`D:/AI/Real projects/Academic_Advisor_Simple/src/features/feature_contract.py` لتعميم Matrix helper مع الحفاظ على سلوكه القديم، وتصدير الواجهة الجديدة والاختبارات والوثائق. Local CLI وOutput وBenchmark تبقى أدوات Local/dev ولا تصبح عقود HTTP.

لا تدريب، ولا تعديل للمودلات أو Frozen bundles أو Datasets الموجودة، ولا Recommendation حقيقية. لا ترقية أي Artifact آخر تلقائيًا. تُشغّل الاختبارات المركزة ثم Full pytest وتوثق النتائج والفشل أو Skips صراحة. بعد تعديل الكود في مرحلة التنفيذ يُشغّل `graphify update .` وفق تعليمات المستودع.

يوجد فشل Baseline قديم بسبب `capaciy_63` في المصدر مقابل `capacity_63` في الاختبار. توثيقه منفصل عن الادعاء بأن Full suite ناجحة؛ هذه الخطوة تحفظ الخطة وتوثق الحالة ولا تصلح الكود. تصحيح الاسم المستقبلي، إن نُفذ ضمن الخطة، يقتصر على اسم Candidate دون تغيير Hyperparameters أو Artifact محفوظ، مع حفظ spelling المصدر الأصلي في Provenance النشر.

### Benchmark المعتمد

يستخدم حالات Synthetic سهلة وصعبة عند `15,20,25,30` Candidate، و`35` للضغط فقط. تشمل توزيعات ساعات وقيود مختلفة، الكسور والصفر وTies وغياب الحل، لا حالة واحدة لكل حجم.

يسجل:

```text
candidate_count
visited_search_states
feasible_plan_count
elapsed_time
peak_memory
shortlist_count
```

يُفصل قياس البحث عن كلفة ترتيب المرشحين وعن المسار الكامل. لا تغيير للبحث قبل النتائج، ولا `max_candidates` جديد أو رفض طلب بسبب عدد اختير محليًا.

تصنيفات الزمن التشخيصية فقط:

```text
< 1 sec: جيد جدًا
1–3 sec: قابل للاستخدام مبدئيًا
3–5 sec: يحتاج مراقبة
> 5 sec: مرشح قوي للتحسين
```

تُسجل الذاكرة الفعلية دون Hard Pass/Fail أو SLA إنتاجي مفترض. بعد النتائج يُعرض قرار `KEEP current exhaustive/pruned search` أو اقتراح تحسين منفصل إلى Branch-and-bound/Constrained Top-K DP؛ لا تعديل خوارزمي بناءً على التعقيد النظري وحده.

### OPEN PRODUCTION CONTRACT

```text
backend_max_candidate_count = UNRESOLVED
recommendation_latency_sla = UNRESOLVED
memory_budget_per_request = UNRESOLVED
```

معيار التسليم قبل اعتماد Ranking هو صحة المكونات، أثر Balance الحقيقي في اختبارات كل مرحلة، ثبات الترتيب، مطابقة Stage 2، حماية الملفات، وتقرير مفاضلات وتوليفات واضح. تثبيت Production Ranking يتطلب اعتماد الاستراتيجيتين بعد هذه الأدلة؛ تطابقهما احتمال ناتج عن التقييم فقط.

## 6. توثيق Baseline لهذه اللقطة

نتيجة Full pytest الفعلية والفشل القديم موثقان في:

`D:/AI/Real projects/Academic_Advisor_Simple/docs/architecture/RECOMMENDATION_TWO_STAGE_BASELINE_VALIDATION.md`

هذه الوثيقة خطة معتمدة للتنفيذ، وليست ادعاءً بأن Production implementation أو Ranking approval أو Benchmark قد اكتمل.

## Implementation Progress

### Phase 1 — Artifacts & Contracts

Status: COMPLETE
Date: 2026-10-05
Commit: Not created (user requested no automatic commit).

- نُشرت نسخ Grade33 وFail33 وCategories مطابقة للبايتات تحت `models/shortlist_v2/`، مع Manifest واحد يثبت عقد Stage 1 المشتق من `BASE_FEATURES − PLAN_CONTEXT_COLUMNS` وعقد Stage 2 ومراجعها الرسمية دون نسخها أو تغييرها.
- أضيف Loader مستقل يتحقق من أسماء/ترتيب/عدد Features وCategories داخل المودلات وTargets/Objectives وCutoff والبصمات وGradeScale وProvenance المكتملة؛ لا يقرأ مصادر التدريب أو التجارب وقت التحميل، ولا يفعّل محرك Recommendation أو Ranking.
- حُفظت Metadata الأصلية وبصمات المدخلات/المصدر الـ11 قبل التعديل، مع أدلة تعريف Target وGradeScale. بقي الاسم الأصلي `capaciy_63` في Provenance، واستُخدم `sha256:<digest>` كإصدار محتوى GradeScale، دون الادعاء بوجود Version سابق في المصدر.
- Tests: `tests/test_two_stage_artifacts.py`: **68 passed**؛ Regression المرتبط: **108 passed**؛ Full pytest النهائي: **680 passed, 1 failed, 6 subtests passed**. الفشل الوحيد **KNOWN BASELINE FAILURE**: `tests/test_train_models.py::test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`؛ لا New regression أو Skip في الملخص.
- المودلات الفعلية على 32 صفًا Synthetic: فرق توقعات الأصل/النسخة **0.0** لكل من Grade وFail. فحص SHA-256: **873** ملفًا موجودًا بقيت دون تغيير/حذف؛ الإضافات الوحيدة داخل `models/` و`data/` هي ملفات Promotion الأربعة، ليصبح العدد **877**.
- نُفّذ `graphify update .` باستخدام AST فقط. لم تُنفذ Matrix/Payload adapters أو History Delta أو البحث/الترتيب أو Engine أو Benchmark أو أي مرحلة لاحقة؛ حالات اعتماد الاستراتيجيتين وتوليفتهما بقيت `UNAPPROVED`.
- قيد نقل موروث: نهايات أسطر ملفات Stage 2 الرسمية تختلف بين Git index والنسخة المحلية المدققة. Manifest يثبت بايتات هذه اللقطة، لذا يجب نقل/نشر الملفات الرسمية المثبتة دون تطبيع نهايات الأسطر؛ Git checkout وحده قد ينتج بصمات مختلفة ويرفض Loader تحميلها. لم تُعد كتابة أي Artifact أصلية لمعالجة هذا القيد. قواعد `-text` الجديدة تحمي نسخ Stage 1 المنشورة فقط.

Next: البند 2 — Payload adapters وMatrix helper والتصنيف والقيود. Safe to continue: YES ضمن اللقطة المدققة؛ تفعيل Production Ranking يبقى مؤجلًا إلى بوابات الاعتماد اللاحقة.

### Phase 2 — Payload Adapters, Matrix Helper, Classification & Constraints

Status: COMPLETE
Date: 2026-10-06
Commit: Not created (user requested no automatic commit).

- أضيفت adapters خالصة دون I/O تستقبل عقد Core محليًا: `student_payload={snapshot, candidates}` وRequest منفصلة بهوية الطالب/الاختصاص/الفصل والساعات وسياسات Requirements. هذا ليس عقد HTTP/Backend transport معتمدًا. تُحفظ Ratio وGap وAttempt الجاهزة؛ يُشتق فقط Trend/Missing وSemester، ويُلزم `current_gpa_credits` دون fallback محلي.
- التصنيف يعتمد على المعنى الرسمي للحالة السابقة، ويرفض تعارض الحقلين حتى إن انتميا إلى المجموعة نفسها. Missing/Unknown لا يصبح NEW أو Failed، والرفض الصريح للأهلية فقط يحذف Candidate. Attempt موثق وفق عدّ المصدر الزمني عبر الاختصاصات قبل فلاتر الحالة وGPA؛ لا يُستنتج منه عدد مرات الرسوب.
- سياسات Requirements تُطبّع `max_credits` إلى `requirement_max_credits` مع رفض التعارض، وتحسب المتبقي بـDecimal. غياب Overflow/Completed/Reserved يعني صفر adjustments، وNull الصريح يُرفض. كل Candidate مؤهل يحتاج سياسة مقابلة؛ تكلفة Repeat كاملة، وحد الراسب الصريح مطلوب، وحد المنسحب مستقل واختياري. الاسمان القديمان `allowed_fail_credits` و`allowed_pass_position_type` Metadata فقط.
- `enumerate_feasible_plan_indices` يستخدم البحث الحالي دون تعديله ويفحص الخطط المكتملة قبل أي Shortlist مستقبلية. يبقى الحد الأعلى هدفًا دقيقًا دون تخفيض؛ الكسور والصفر محفوظة، وحدود الإعادة maxima لا minima.
- عُمم `prepare_model_matrix` بعقد مرتب اختياري، مع تطابق الاستخدام القديم للـ47 وNumeric float32 وMissing/Unknown Categories. أصبح `prepare_course_matrix` wrapper توافق يستدعي helper المشترك بدل نسخ Logic. لم تتغير Features/Targets/Version أو فحوص signature/Metadata التجربة؛ لذلك التوقيع التجريبي السابق يظل مرفوضًا بعد تغيير المصدر. Loader النسخ المنشورة من Phase 1 نجح فعليًا بعقود 33/33/47/47 دون تشغيل توقعات.
- Tests: المركزة **125 passed**؛ المجموعة الأوسع المرتبطة **258 passed**؛ Full pytest النهائي **805 passed, 1 failed, 6 subtests passed**. الفشل الوحيد **KNOWN BASELINE FAILURE**: `tests/test_train_models.py::test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]` بسبب `capaciy_63`؛ **NEW REGRESSION: 0**، ولا Unrelated failure أو Skip في الملخص. المراجعة المستقلة واختبارات تحويل Decimal إلى float أغلقت حالة overflow إلى infinity.
- SHA-256: الملفات الـ**877** الموجودة تحت `models/` و`data/` بقيت دون تغيير أو حذف أو إضافة. اكتمل `graphify update .` باستخدام AST فقط: 2296 nodes و5250 edges؛ لم يحدث تدريب أو Recommendation حقيقية أو اتصال Backend أو تفعيل Engine/Ranking أو تنفيذ Phase لاحقة.

Next: Phase 3 — History Delta والحفظ immutable والتحويل الذري. Safe to continue: YES ضمن نطاق الخطة؛ استراتيجيتا Ranking وتوليفتهما تبقى UNAPPROVED.
