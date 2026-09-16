# تشغيل توصيات الخطط محلياً

المحرك يقيّم جميع التركيبات المطابقة للساعات المطلوبة باستخدام Expected Points.
إذا أعطيته قيمة واحدة مثل `18` يطابقها بالضبط، وإذا أعطيته `12–18` يولّد كل
الخطط التي تحقق `12 ≤ مجموع الساعات ≤ 18`، وعدد المواد متغير. يقيّم ويحفظ
جميع الخطط المطابقة، ويرجع أفضل ثلاث خطط افتراضيًا حتى إذا لم تحسن أي منها
المعدل. الترتيب حسب **التراكمي المتوقع بعد الخطة**، ثم ساعات الرسوب المتوقعة،
ثم المعدل الفصلي المتوقع، ثم معرّف الخطة. مخاطر الرسوب ليست شرط استبعاد.

## 1. قائمة المواد

جهّز ملف JSON يحتوي قائمة سجلات، أو Parquet بالأعمدة نفسها:

```json
[
  {"course_id": "COURSE_ID_1", "course_credits": 2},
  {"course_id": "COURSE_ID_2", "course_credits": 3}
]
```

المعرّفات في المثال placeholders؛ استبدلها بمعرّفات حقيقية من اختصاص الطالب.
يمكن إضافة `course_name_sl`. يستكمل المحرك خصائص المواد من
`data/clean/degree_course.parquet` باستخدام `(degree_id, course_id)`.

يقبل أيضاً تصدير الشركة بأسماء أعمدة uppercase. إذا وجد `IS_REQUESTABLE`
يشترط وجود `STUDENT_ID` ويختار الطالب و`Y` فقط. ينظف فراغات المعرفات، ويحافظ
على الجزء العشري مثل `33330.111`. القائمة تعتبر معتمدة من حيث أهلية المواد؛
لا يعيد المحرك حساب المتطلبات السابقة أو تعارض الشعب أو المقاعد.

إذا تضمن الملف `part_id` مختلفاً يرفضه. الصفوف ذات الفصل الفارغ ترتبط بالفصل
الذي تحدده صراحة في التشغيل؛ لذلك يجب أن يكون الملف قائمة مؤمّنة لذلك الفصل.
لا تمرّر الملف الخام القديم المختلط على أنه قائمة فصل جاهزة.

التكرار المتطابق يدمج مع تسجيل عدد الصفوف ومعرّفاتها في تقرير الاستيراد؛
التكرار المتعارض أو اختلاف ساعات المادة عن الكتالوج أو عدم تطابقها يوقف
التقييم ويظهر السبب. الساعات الكسرية محفوظة، والمواد ذات الصفر ساعة خيارات
إضافية تدخل عدد المواد وخصائص الحمل، ولا تدخل مجموع النقاط الموزون.

## 2. التشغيل من مجلد المشروع

```powershell
.\.venv\Scripts\python.exe -m src.recommend_local --candidates data/local_candidates.json --student-id "33330.111" --degree-id "YOUR_DEGREE_ID" --part-id 20251 --history-as-of-part 20243 --credits 18
```

لإعطاء مجال، استبدل `--credits 18` بـ `--min-credits 12 --max-credits 18`.
هذا المجال يشمل كل التركيبات بين 12 و18 ساعة، بما فيها الطرفان. لا تعطي
الصيغتين معاً. لا يوجد خروج تلقائي عن الحدود ولا شرط ثابت لعدد المواد.

افتراضياً يستخرج snapshot بداية الفصل المحدد من سجل الحالة المحلي الكامل
قبل تصفية صفوف النتائج، ويضيف التاريخ السابق والشهادة والكلية. لا يستخدم
`end_agpa_points` أو نتائج الفصل المستهدف، ولا ينسخ snapshot فصل أقدم ويسميه
فصلاً جديداً. حساب `attempt_number` يتبع تعريف التدريب: آخر رقم محاولة
محفوظ في التسجيلات المنظفة السابقة + 1، و1 للمادة دون تاريخ سابق.

إذا لم توجد حالة واحدة للطالب والاختصاص والفصل، أو لم تتوفر الكلية والشهادة،
زوّد `--snapshot data/student_snapshot.json`. يجب أن يصف هذا الملف **بداية
الفصل المستهدف**، ويحوي المفاتيح التالية كلها؛ قيم التاريخ المجهول يمكن أن
تكون `null`، ولا نحولها إلى أصفار:

```text
student_id, degree_id, part_id, faculty_id, grade_version_id,
gpa_prev_1, gpa_prev_2, gpa_trend_delta, gpa_trend_missing,
start_agpa_points, start_total_in_courses, start_total_in_credits,
prior_total_reg_courses, prior_total_reg_credits,
prior_total_fail_courses, prior_total_fail_credits, prior_fail_credit_ratio,
prior_registered_semesters, observed_gap_semesters,
diploma_gpa, diploma_type_id, degree_credits_count
```

المفاتيح يجب أن تطابق وسيطات التشغيل. إذا لم تحدد `--current-gpa` يستخدم
`start_agpa_points` من snapshot، ويجب أن تكون قيمة فعلية بين 0 و4.
يستخدم `total_reg_credits` لساعات المعدل السابق، وفق تعديل صاحب المشروع
بتاريخ 2026-09-15. هذه القيمة محفوظة في snapshot باسم `prior_total_reg_credits`
وتنسخ من المصدر مباشرةً. لا يقرأ ساعات الفصل الفعلية لترتيب البدائل؛ يستخدم
مجموع ساعات كل خطة مقترحة. القيمة الناقصة أو السالبة لا تتحول إلى صفر.
يمكن تمرير `--current-gpa-credits` صراحةً، أو إضافة `current_gpa_credits` إلى
snapshot. ترتيب الاختيار: وسيط CLI، ثم الحقل الاختياري، ثم
`prior_total_reg_credits`. هذا الحقل الاختياري لا يدخل خصائص النموذج.
يبقى `start_total_in_credits` ضمن خصائص النموذج، لكنه لم يعد مصدر ساعات
المعادلة التراكمية.

خيارات إضافية: `--top-n 3` لتغيير عدد الخطط المعروضة، `--batch-size 2000`،
`--threads 4`، و`--output-dir` لمجلد جديد.
لا يعاد استخدام مجلد تشغيل سابق حتى لا تختلط النتائج.

## 3. المودل والنتائج

يُحمّل `models/experiments/degree_points/selected_model.txt` مع عقد خصائصه
وفئاته من metadata. النسخة المختارة عند تنفيذ هذا المسار بتاريخ 2026-09-12
هي `degree_history_points_temporal`، والتوقعات مقيدة إلى `[0,4]` كما في
التقييم التجريبي. لا نضرب Expected Points باحتمال النجاح مرة ثانية.

يُحمّل FailRiskClassifier وفئاته بصورة مستقلة. تاريخ المقررات وتاريخ
الاختصاص يأتيان من نسخة صريحة تحددها `--history-as-of-part`؛ لا يعيد التحميل
بناء Specialty History من جدول التدريب. النسخة يجب أن تكون أقدم من الفصل
المطلوب؛ استخدام نسخة أقدم من الفصل السابق يحتاج `--allow-older-history`.
خصائص `plan_*` و`peer_*` يعاد حسابها داخل كل خطة؛ نقاط المادة ليست ثابتة
عند تغيير المواد المرافقة. لا يُعاد تدريب أي مودل أثناء التوصية.

تحت `data/evaluation/recommendations/<run>/`:

| الملف | المحتوى |
|---|---|
| `import_report.json` | الفلاتر والتكرارات والتعارضات ومصدر الإدخال |
| `candidates.parquet` | القائمة المثرية المستخدمة |
| `snapshot.json` | بيانات بداية الفصل التي دخلت التقييم لإعادة التجربة |
| `plans.parquet` | كل الخطط المطابقة مرتبة، صف لكل خطة، بما فيها غير المحسنة |
| `courses.parquet` | تفاصيل كل مادة في كل خطة مطابقة، تحفظ بالدفعات |
| `result.json` | أفضل ثلاث خطط والعدادات والتراكمي المتوقع وبصمات التاريخ والمودلات |

اربط الملفين بواسطة `plan_id`. تفاصيل المواد ليست مرتبة عالمياً حسب رتبة
الخطة؛ الترتيب النهائي في `plans.parquet`. يحتفظ المحرك بملخصات الخطط فقط في
الذاكرة، وبتفاصيل أفضل ثلاث خطط، وبدفعة العمل الحالية. مساحة الملخصات تنمو
بعدد الخطط المطابقة، بينما تفاصيل المواد تحفظ تدريجيًا على القرص. قد يزيد
حجم الملفات عن التشغيلات القديمة التي كانت تحذف الخطط غير المحسنة.

معرّف الخطة ثابت عند تبديل ترتيب قائمة المواد أو حجم الدفعة ضمن المدخلات
نفسها؛ ليس معرّفاً عالمياً بين طلبات مختلفة. `gpa_gain` هو الفرق بين معدل
الخطة المتوقع والمعدل الحالي، **وليس مقدار ارتفاع التراكمي الجديد**.
الفحص يستخدم القيم قبل تقريب العرض. كل القيم توقعات؛ النتائج الفعلية للخطط
غير المسجلة غير معروفة.

حالات `result.json`: `ok` أو `no_matching_credit_plan`. عدم تحسن المعدل يعطي
`ok` مع `has_expected_improvement: false` وأفضل الخطط المتاحة. عدم وجود خطط
مطابقة ينتج ملفات Parquet فارغة ذات أعمدة معروفة. لا يظهر
`result.json` قبل اكتمال حساب وحفظ الخطط، لذا غيابه يعني أن التشغيل لم يكتمل.
أخطاء المدخلات تعطي `error.json` أو تقرير استيراد بالأسباب ورمز خروج 2.

يعرض الملخص `min_credits` و`max_credits` و`matching_plan_count` لعدد الخطط
ضمن الحدود، و`scored_plan_count` لعدد الخطط المقيمة، و`returned_plan_count`
لعدد الخطط المعروضة، و`plans_with_expected_improvement` لعدد الخطط المحسنة
ضمن جميع الخطط المقيمة. بقي `accepted_plan_count` للتوافق فقط؛ أصبح مساويًا
لعدد الخطط المقيمة وليس لعدد الخطط المحسنة. `target_credits` يساوي القيمة المحددة عند تساوي
الحدين ويكون `null` للمجال. التشغيلات الأقدم سبقت تصحيح دعم المجال، وكانت
تستخدم اسم العداد `exact_plan_count`؛ لم تُعدّل ملفاتها التاريخية.

## 4. الاختبارات وقياس الأداء

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m src.benchmark_recommendation --history-as-of-part 20243
```

اختبارات التكامل تستخدم artifacts المحلية وتُتجاوز إذا لم تتوفر؛ الاختبارات
الأخرى تعمل بأمثلة صغيرة. تشمل التطابق مع توقعات التجربة المحفوظة، منع تسرب
النتائج، الساعات الكسرية، ترتيب المواد والدفعات، الفلاتر، والحالات الفارغة.

الـbenchmark ينشئ قوائم 15 و20 و25 مادة من الكتالوج، بساعات 2 و3 وهدف 18
ساعة، ويشغّل كل حجم في عملية مستقلة. يحفظ الزمن وذروة ذاكرة العملية والنتائج
تحت `data/evaluation/recommendation_benchmarks/`. هذه **قوائم اختبار أداء**
ولا تثبت أهلية طالب لتسجيل المواد؛ الاختبار الفعلي يبدأ بقائمتك المعتمدة.
حجم البحث يعتمد على توزيع الساعات، وليس عدد المواد وحده.
يعتمد اختبار الأداء معدلًا افتراضيًا `2.5` وساعات معدل افتراضية `60`.

## 5. معادلة الترتيب وحدود الإعادات

```text
G = current_gpa                     # start_agpa_points افتراضيًا
C = current_gpa_credits             # prior_total_reg_credits = total_reg_credits افتراضيًا
L = sum(course_credits)             # ساعات الخطة المقترحة
Q = sum(course_credits * expected_points)

expected_plan_gpa = Q / L
projected_cumulative_gpa = (G * C + Q) / (C + L)
expected_cumulative_gpa_gain = projected_cumulative_gpa - G
is_expected_cumulative_improvement = projected_cumulative_gpa > G
expected_failed_credits = sum(course_credits * fail_probability)

sort by projected_cumulative_gpa DESC,
        expected_failed_credits ASC,
        expected_plan_gpa DESC,
        plan_id ASC
```

وبأسماء حقول المصدر للحساب بعد ظهور نتائج الفصل:

```text
new_cumulative_gpa =
    (semester_reg_credits * gpa_points + total_reg_credits * prevagpapoint)
    / (semester_reg_credits + total_reg_credits)
```

`prevagpapoint` هنا هو المعدل التراكمي السابق، ويقابله `start_agpa_points`
في snapshot. أثناء التوصية يحل معدل الخطة المتوقع وساعاتها محل
`gpa_points` و`semester_reg_credits`؛ لا تستخدم نتائج الفصل المستهدف الفعلية.

مثلًا `G=2, C=60, L=12, Q=42` يعطي تراكميًا `2.25`. خطة `18` ساعة
بمعدل فصلي `3.25` تعطي `178.5 / 78 = 2.28846`، فتسبق خطة `12` ساعة
بمعدل فصلي أعلى `3.5`. شرط التحسن علم توضيحي فقط ويستخدم القيم دون تقريب.

الحساب معزول في `project_cumulative_gpa`. لا توجد قاعدة لاستبدال نقاط محاولة
قديمة. إذا تضمنت الخطة `attempt_number > 1` يظهر
`projected_gpa_requires_repeat_policy: true`؛ التراكمي المعروض حينها سيناريو
إضافي، ولا يمثل حساب الجامعة الدقيق للإعادة. العلم تحذير محافظ ولا يثبت أن
نقاط المحاولة القديمة تدخل معدل هذا الاختصاص. عدم ظهور العلم لا يثبت عدم
وجود إعادة: تاريخ المحاولات منظف ويبدأ بعد 20193 وقد يستبعد محاولات أقدم.
مخاطر الرسوب ونقاط المقررات تظل كما يتنبأ بها النموذجان الحاليان.

## 6. نسخ Frozen Historical State

```text
data/artifacts/history/
  as_of_20243/
    course_history_state.pkl
    specialty_history_state.pkl
    metadata.json
  as_of_20251/
    course_history_state.pkl
    specialty_history_state.pkl
    metadata.json
```

البناء مستقل عن التدريب. تحدد ملفات المصدر صراحةً؛ يستخدم البناء أعمدة
النتائج والتجميع القائمة فقط، ولا يعيد تدريب مودل أو توليد خصائص تنبؤية.
يجب توفير كامل التاريخ المنظف النهائي حتى الحد المطلوب. يمكن أن تضم ملفات
المصدر فصولًا أحدث، لكن البناء يقتطع `part_id <= as_of_part` قبل التجميع.
يرفض تكرار `student_course_id` داخل التاريخ المختار، والنتائج الناقصة، وعدم
وجود نتائج في الحد المطلوب. `--finalized-through-part` إقرار بأن النتائج
نهائية؛ لا تستطيع قيمة `part_id` وحدها إثبات وقت اعتمادها لدى الجامعة.

للترحيل الأول فقط، بعد التحقق من مطابقة النسخة القديمة للمصدر:

```powershell
.\.venv\Scripts\python.exe -m src.build_frozen_history --as-of-part 20243 --finalized-through-part 20243 --sources data/features/temporal_train_features.parquet --verify-legacy-course-state data/artifacts/course_history_state.pkl
```

لبناء التاريخ حتى نهاية `20251` من الجداول المحلية الحالية:

```powershell
.\.venv\Scripts\python.exe -m src.build_frozen_history --as-of-part 20251 --finalized-through-part 20251 --sources data/features/temporal_train_features.parquet data/features/temporal_test_features.parquet
```

**النسختان أُنشئتا في هذا التعديل؛ إعادة الأمر لن تكتب فوقهما، بل سترفض وجود
النسخة.** بعد فصل لاحق، اختر `as_of_part` جديدًا ومرر مصادر تشمل كامل تاريخه
النهائي. لا تعتمد التوصية على استمرار وجود ملفات المصدر عند التحميل.
الأصل `data/artifacts/course_history_state.pkl` بقي محفوظًا، ولا يقرأه محمل
التوصية الجديد. باني الخصائص القديم قد يحدّث ذلك الأصل عند تشغيله، لكنه لا
يكتب داخل مجلدات التاريخ المرقمة.

يحجز الحفظ مجلدًا جديدًا حصريًا، ويكتب metadata آخرًا. النسخة الجزئية غير
قابلة للتحميل ولا يعاد استخدامها تلقائيًا. لفحص بناء فاشل، استخدم مجلد اختبار
جديدًا مع `--history-root` دون حذف النسخ الموجودة. لا يوجد مؤشر `latest`.
احفظ نسخة احتياطية من `data/artifacts/history`؛ مجلد `data/` مستبعد من Git.

metadata تضم الفصل والتوقيت ونسخة هندسة الخصائص ونوع التاريخ، وحد اعتماد
النتائج وعددها وتوزيعها على الفصول، وبصمات ملفات المصدر وملفي الحالة. التحميل
يتحقق من البصمات ومن تطابق الفصل في المقررات والاختصاص وmetadata والمسار.
بصمة metadata نفسها تحفظ في provenance التوصية.

```python
from src.recommendation import AcademicPlanRecommender

engine = AcademicPlanRecommender.load(history_as_of_part=20243)
# استخدم نفس المودلات مع التاريخ الأحدث:
engine = AcademicPlanRecommender.load(history_as_of_part=20251)
```

يحفظ `result.json` كلاً من `target_part` و`history_as_of_part` و`model_training`،
ولا يساوي بين تاريخ التدريب وتاريخ الخدمة. المودلان الحاليان مرتبطان بتدريب
حتى `20243`؛ cutoff نموذج Expected Points مستنتج من وصف بروتوكول metadata
القديم وموسوم بذلك في `basis`. أي metadata مستقبلية تحتوي
`training_as_of_part` صريحًا تتقدم على هذا الاستنتاج. عدم توفر cutoff مسجل
يعطي `null`، ولا يستنتج من تاريخ الخدمة أو جدول التدريب المتغير.

مسموح: `20251 / 20243` و`20252 / 20251`. للاسترجاع الأقدم مثل
`target=20252 / history=20243` أضف `--allow-older-history`. هذا الخيار لا
يسمح بتسرب نتائج الفصل المستهدف أو المستقبل، ولا بتدريب مودل حتى الفصل
المستهدف. التقويم يفترض ثلاثة أجزاء أكاديمية في السنة (`YYYY1..YYYY3`).
التاريخ المجمد هنا هو تجميع المقررات والاختصاص؛ snapshot الطالب ومحاولاته
يصفان بداية الفصل المطلوب، وليسا snapshot طالب من فصل النسخة الأقدم.

## 7. إعادة تشغيل المثال المحلي السابق

الأمران التاليان يستخدمان ملفات المرشحين المحفوظة للطالب `29485.111`،
والاختصاص `42.111`، ومجال `12–18` شاملًا الطرفين. هذه إعادة تشغيل لقوائم
التحقق السابقة؛ حفظها محليًا لا يثبت أهليتها التاريخية لدى الجامعة.

```powershell
.\.venv\Scripts\python.exe -m src.recommend_local --candidates data/evaluation/recommendation_trace_pilot/explained_29485_20260913T114511285272Z/20251/candidates.json --student-id 29485.111 --degree-id 42.111 --part-id 20251 --history-as-of-part 20243 --min-credits 12 --max-credits 18

.\.venv\Scripts\python.exe -m src.recommend_local --candidates data/evaluation/recommendation_trace_pilot/explained_29485_20260913T114511285272Z/20252/candidates.json --student-id 29485.111 --degree-id 42.111 --part-id 20252 --history-as-of-part 20251 --min-credits 12 --max-credits 18
```

تولد الأوامر مجلد تشغيل جديدًا تلقائيًا. لإعادة تجربة ثابتة لبيانات الطالب،
مرر أيضًا `--snapshot` بمسار `snapshot.json` الذي حفظه التشغيل المرجعي.
تجميد التاريخ يضمن إعادة استخدام التجميع ذاته؛ ثبات snapshot والقائمة
والمودل والكتالوج مطلوب لإعادة إنتاج التوصية كاملةً.

## 8. الربط اللاحق بالـAPI

المسار الداخلي هو `normalize_candidates` ثم `AcademicPlanRecommender.recommend`.
الأول يستقبل DataFrame ويمكن تغذيته من ملف أو استجابة API، والثاني لا ينفذ
استعلامات. يجلب النظام البيانات مرة واحدة ويحمّل المودلات مرة واحدة لكل عملية.

استعلام جهة الشركة يستخدم قيمة مرتبطة، مثلاً:

```sql
SELECT *
FROM V_CRG_STD_COR_TEMP_REQUEST
WHERE STUDENT_ID = :student_id
  AND IS_REQUESTABLE = 'Y'
ORDER BY COURSE_NAME_SL ASC
```

على adapter الشركة توفير قائمة تخص فصل الطلب صراحة ومعالجة معنى الصفوف ذات
`PART_ID` الفارغ وفق عقدها؛ لا نستنتج هذا المعنى من التصدير القديم. ترتيب
الاسم للعرض فقط. لم يُنفّذ اتصال الشركة أو HTTP أو تسجيل المواد؛ تنتقل هذه
المرحلة بعد قبول النتائج المحلية وقياس الأداء على قوائم فعلية.
