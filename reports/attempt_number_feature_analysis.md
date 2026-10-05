# تحليل وتجربة `attempt_number` المعزولة

تاريخ التقرير: 2026-10-01. **القرار: Evidence is insufficient لإقرار استبدال الإنتاج.**
**Does the model need the exact attempt number? INCONCLUSIVE.**

جودة التنبؤ متقاربة جدًا في المتوسط بين A و B، لكن اختلاف النتيجة الزمنية لدى 3+، وتغيّر ترتيب التوصيات، وصغر عينة التوصيات تمنع إثبات أن الاستبدال لا يسبب خسارة مهمة للمنتج. الإجراء الحالي: **Keep attempt_number** إلى أن تتوافر أدلة أقوى؛ هذا إجراء احترازي مبني على نقص الدليل، وليس إثباتًا أن الرقم الكامل ضروري لكل تنبؤ. لا ترقية لأي تجربة.

كل الأرقام من ملفات V2 الحالية الفعلية. لا فرضية مسبقة بأن Boolean أفضل؛ لا Experiment D، ولا إعادة ضبط أو إعادة تدريب بعد رؤية نتائج Test لاختيار تمثيل جديد.

## A. Current semantics

المسار الفعلي في `src/data/clean_student_course.py`:

```text
Raw student-course records
→ normalize register_status
→ keep register_status in {R,E}
→ normalize finish_status, IDs, part_id
→ drop missing course_id/part_id; validate other required keys and duplicates
→ keep part_id > 20193
→ normalize values/flags
→ stable sort [student_id, course_id, part_id]
→ groupby [student_id, course_id], cumcount()+1
→ keep finish_status in {P,F,FE,FA}
→ drop any row with N in in_agpa/in_gpa/in_credits
→ later common-student joins, enrichment, diploma, outliers, temporal split, features
```

- المفتاح `(student_id, course_id)` يعبر تغيير `degree_id`. حد البيانات 20201 يعني أن محاولات ما قبل 2020 لا تدخل الرقم، فلا يمثل بالضرورة عدد المحاولات مدى الحياة.
- R و E يدخلان العدّ؛ أي تسجيل آخر مستبعد قبل العدّ. ترتيب الصفوف زمني تصاعدي، مع منع تكرار الطالب/المادة/الفصل حتى لو تغير degree، ومنع تكرار `student_course_id`.
- P نجاح، و F/FE/FA رسوب في تنظيف النتائج. Withdrawal وأي finish_status آخر أو مفقود يدخل العدّ إذا اجتاز فلاتر ما قبل العدّ، ثم يُحذف من النتائج. اختبار `test_withdrawn_counts_as_attempt_before_removal` يثبت ذلك.
- أعلام `in_agpa/in_gpa/in_credits` لا تغير العدّ. الصف ذو N يدخل العدّ ثم يُحذف؛ الغياب/قيمة أخرى لا تُعامل N تلقائيًا. الأسماء لا تكفي لاستنتاج معنى تاريخي إضافي.
- التسجيل الحالي دون نتيجة يدخل العدّ في الذاكرة، لكنه لا يظهر في Dataset Modeling بعد فلتر finish_status. إذا أصبح صفًا سابقًا لمحاولة لاحقة، قد يرفع رقمها؛ لا يحدث إعادة ترقيم بعد فلاتر Modeling.
- `feature_contract.py` يمرر `attempt_number` كـ float32 رقمي ضمن 47 Feature، دون bucketing أو categorical encoding. `temporal_features.py` لا يعيد حساب الرقم الشخصي، ويستخدمه لبناء متوسطات CourseHistory بشكل مستقل؛ هذه المتوسطات لم تتغير.
- `train_models.py` يستخدم `final_mark` للـ Grade و`is_fail` للفشل. `src/experiments/modeling.py` محرك تجارب degree/points اختياري، وليس Production target جديدًا لهذه التجربة؛ لا نغيره.

### الفرق الحالي مع Serving

`recommendation/inputs.py::normalize_candidates` ينظر فقط إلى السجل المنظف المشترك V2 للطالب/المادة قبل target part، دون degree، ثم يحسب `max(previous saved attempt_number)+1`؛ وإذا لا توجد نتائج سابقة محفوظة يعطي 1. لا يستخدم محاولات الفصل المستهدف أو المستقبل ولا رقمًا واردًا من طلب العميل.

يمكن للرقم المحفوظ أن يحتفظ بآثار Withdrawal/N أقدم منه، لكن Serving لا يرى محاولة مستبعدة أحدث من آخر نتيجة محفوظة، ولا يرى تاريخ مادة جميع صفوفه السابقة مستبعدة. لذا ليس مطابقًا تمامًا لعدّ جميع التسجيلات المؤهلة قبل فلاتر النتائج. لم يُصلَح هذا الفرق هنا.


فحص تاريخي عند صفوف Modeling: إعادة تطبيق صيغة Serving من النتائج السابقة المنظفة أعطت **14,961/424,352** اختلافًا (3.526%)؛ منها 1,157 في 20251 و 1,617 في 20252. الفحص قائم على prior cumulative maximum shifted، فلا يستخدم مستقبل الصف. يوجد 233 مفتاح طالب/مادة ظهر في أكثر من degree في السجل المنظف. تفاصيل الصفوف محلية في `serving_semantics_mismatches.parquet`.

الـ Model target للفشل هو `final_mark < 50`، وليس outcome code. يوجد 531 صفًا يختلف فيه تعريف الرسوب بالعلامة عن `course_outcome_status`؛ المقارنة تبقي target الحالي كما هو.

## B. Distribution

جدول كل الصفوف المستخدمة في Modeling، Train + Holdout، بعد كل فلاتر الإنتاج:

| attempt | rows | percent | students | courses |
| --- | --- | --- | --- | --- |
| 1 | 376035 | 88.614 | 12004 | 880 |
| 2 | 37798 | 8.907 | 7711 | 715 |
| 3 | 7928 | 1.868 | 3165 | 516 |
| 4 | 2094 | 0.493 | 1285 | 360 |
| 5+ | 497 | 0.117 | 407 | 188 |

First attempt = **88.614%**؛ repeat = **11.386%**.
الحد الأعلى 5؛ Mean = 1.145926؛ Median = 1؛ P95 = 2؛ P99 = 3.
المحاولة الثالثة فأكثر: **10,519 صفًا**؛ الطلاب ذوو أي repeat: **7,751**؛ المواد التي تظهر فيها repeats: **722**.

3+ ليست مجرد عشرات صفوف؛ لكن عدد الصفوف لا يساوي عدد وحدات مستقلة. حجم Holdout 3+ = 1,648 صفًا لدى 954 طالبًا، و 4+ = 474 صفًا لدى 330 طالبًا. ما فوق 5 غير قابل للحكم بهذه البيانات.

**قيد اختيار العينة:** `src/data/clean_outliers.py` يعتبر attempt خارج [1,5] outlier ويزيل الطالب كاملًا. السجل المنظف قبل Modeling يصل إلى 14 محاولة؛ لذلك لا ننسب ندرة 3+ إلى الواقع كاملًا، ولا نستنتج شيئًا عن 6+ أو الطلاب المستبعدين. فلتر outliers الحالي يستخدم بيانات السجل ومقاييس نتائج؛ توجد مشكلة اختيار محتملة تعتمد على معلومات لاحقة، لكنها سابقة لهذه التجربة وثابتة في A/B/C، ولم تُعدَّل.

### Distribution shift

| cohort | rows | repeat_percent | third_plus_rows |
| --- | --- | --- | --- |
| train | 356816 | 11.248 | 8871 |
| 20251 | 34408 | 8.617 | 761 |
| 20252 | 33128 | 15.754 | 887 |
| holdout | 67536 | 12.118 | 1648 |

تضاعفت تقريبًا نسبة repeats بين فصلي Holdout. توجد التفاصيل لجميع الفصول في `distribution_shift.csv` وتفاصيل توزيع كل cohort في `distribution.csv`.

## C. Outcome relationship

Train (وصفي، لا سببية):

| subset | rows | mean_final_mark | mean_points | fail_rate |
| --- | --- | --- | --- | --- |
| first | 316683 | 72.039121 | 2.441280 | 0.070361 |
| repeat | 40133 | 61.270825 | 1.804544 | 0.195301 |
| second | 31262 | 62.048589 | 1.848922 | 0.184121 |
| third | 6754 | 58.592686 | 1.644618 | 0.239118 |
| fourth_plus | 2117 | 58.329712 | 1.659424 | 0.220595 |

Holdout:

| subset | rows | mean_final_mark | mean_points | fail_rate |
| --- | --- | --- | --- | --- |
| first | 59352 | 72.170913 | 2.438823 | 0.082070 |
| repeat | 8184 | 59.489614 | 1.667766 | 0.251344 |
| second | 6536 | 60.674572 | 1.746175 | 0.226132 |
| third | 1174 | 55.717206 | 1.407368 | 0.337308 |
| fourth_plus | 474 | 52.493671 | 1.231540 | 0.386076 |

الفرق الكبير المرصود يحدث بين 1 و>1، لكن بقي فرق بين الثانية و 3+: الرسوب 22.61% مقابل 35.13%. وفي 4+ يظهر تغير زمني قوي: fail rate 29.44% في 20251 مقابل 46.15% في 20252. الخلفية الأكاديمية والمواد والفصول تختلف؛ هذه الأرقام لا تعني أن التكرار يسبب رسوبًا.

### التداخل مع Features الأخرى

حُسب هذا التحليل على Train فقط:

| feature | paired_rows | pearson | spearman | first_mean | repeat_mean |
| --- | --- | --- | --- | --- | --- |
| course_history_avg_attempt | 329807 | 0.2502 | 0.1615 | 1.0944 | 1.1477 |
| course_history_retake_rate | 329807 | 0.2478 | 0.1646 | 0.0784 | 0.1185 |
| prior_total_fail_courses | 356816 | 0.2389 | 0.3041 | 3.5962 | 9.1289 |
| prior_total_fail_credits | 356816 | 0.2376 | 0.3033 | 10.2403 | 25.9512 |
| prior_fail_credit_ratio | 322725 | 0.3702 | 0.3438 | 0.0862 | 0.2427 |

الرقم الشخصي يخص هذا الطالب وهذه المادة. `course_history_avg_attempt/retake_rate` يصفان نتائج الطلاب السابقة لهذه المادة/degree، مع fallback و smoothing ووزن زمني؛ أما `prior_total_fail_*` فيصف تاريخ الطالب عبر جميع المواد، ولا يحدد المادة المعادة. كذلك قد يكون repeat بعد انسحاب أو تحسين درجة، لا بعد رسوب فقط.

دليل بنيوي يتجاوز correlation: من 15,118 مجموعة course/degree/part في Train، يوجد 7,565 مجموعة تختلف فيها المحاولة الشخصية؛ **كلها** تحمل قيمة مطابقة للـ course retry aggregates بين طلابها، وتضم 261,712 صفًا. إذًا aggregates ليست نسخة من الرقم الشخصي.

عند مطابقة course/degree/part وشريحة prior fail courses (0، 1–4، 5–9، 10+) مع >=10 صفوف لكل first/repeat في الخلية: 205 خلية، 4,197 first و 2,900 repeat. المتوسط الموزون للفرق repeat−first: mark +0.9132، fail rate -0.0345. انقلاب الفرق عن الجدول الخام يبين قوة الاختلاط؛ هذا تشخيص وصفي لا ضبط سببي ولا إثبات redundancy. الاختبار العملي للفائدة هو C.

## D. Experiment setup

| Variant | Personal attempt feature | Feature count |
| --- | --- | --- |
| A | attempt_number، كما هو | 47 |
| B | is_repeat = (attempt_number > 1)، مكان العمود نفسه | 47 |
| C | حذف attempt_number فقط، دون بديل | 46 |

المصدر `temporal_train_features_v2.parquet` / `temporal_test_features_v2.parquet`؛ **356,816 / 67,536 صفًا**. المفاتيح وترتيبها مشتركة حرفيًا؛ SHA-256 للصفوف ولكل fold محفوظة في `setup.json` و`training_manifest.json`، مع التأكد من عدم تقاطع IDs وتطابق failure target. لا صفوف محذوفة أو مضافة لأي variant.

- Train: 20201–20243 حسب الفصول الـ 15 الحالية؛ Test: 20251 و 20252. لا تحديث للمودل بنتائج 20251؛ فقط features التاريخية المحفوظة الحالية تستخدم finalized 20251 قبل 20252، وفق apply-before-update.
- التحقق الزمني: through 20223 → 20231–20233 (205,369 fit /77,014 valid)؛ through 20233 → 20241–20243 (282,383 /74,433).
- نفس LightGBM، targets، categories fit-only، missing/unknown handling، weights (0.25 قبل 2022، 1 من 2022)، seed 42 وكل seeds الفرعية، deterministic، feature/bagging fractions و regularization. Fail بلا class weights.
- إعدادات Grade الرسمية num_leaves=63/min_leaf=100، learning_rate=.04، feature_fraction=.85، bagging=.90، L1=.20، L2=2.00؛ Fail 31/80، .04، .90، .90، .10، 1.00. باقي parameters كاملة في `setup.json`.
- **المقارنة النهائية تثبت 114 شجرة Grade و 112 Fail لجميع A/B/C**، وهي أعداد الإنتاج المختارة مسبقًا على pre-2025. لم نجعل B أو C يغيران الميزانية أو يعيدان اختيار hyperparameters. قدمنا CV بميزانية ثابتة كتشخيص مضبوط.
- وللحفاظ على استراتيجية Validation الأصلية أيضًا، نفذنا 12 fit إضافية بإعدادات candidate الرسمي المثبت، max=900 و patience=75، وفصول المشروع نفسها؛ الأعداد المثلى متاحة في `original_validation_protocol.json`. هذه تشخيصية؛ لم تغيّر أعداد fit النهائي أو تؤدي إلى تجربة جديدة.
- أعاد A المدرب محليًا توقعات الـ artifacts الرسمية بالضبط: maximum absolute difference **0.0** للـ Grade والـ Fail. عدم تطابق اسم `capaciy_63` في المصدر مع `capacity_63` في metadata لم يؤثر على القيم؛ نقرأ الإعدادات الفعلية من metadata، ولا نصلح الاسم هنا.

لا تستخدم B عدد المحاولات النهائي للمادة؛ تستخدم **فقط الرقم الموجود عند الصف** وتحوله مباشرة، فلا تضيف اعتمادًا على نتائج مستقبلية. بقي Frozen History و CourseHistoryState وكل course/plan/peer history columns ثابتة. لا نزعم أن Dataset خالٍ من جميع مشكلات اختيار العينة السابقة، أو أن Holdout لم يُعرض في تجارب المشروع الماضية؛ هذه تجربة ثابتة دون tuning على Holdout وليست blind prospective test جديدًا.

### Validation باستراتيجية الإنتاج الأصلية

| cohort | subset | variant | rows | mae | points_mae | log_loss | pr_auc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train_through_2022_validate_2023 | overall | A | 77014 | 9.267135 | 0.547176 | 0.246949 | 0.281773 |
| train_through_2022_validate_2023 | repeat | A | 10342 | 11.033627 | 0.727277 | 0.482529 | 0.339310 |
| train_through_2022_validate_2023 | third_plus | A | 2495 | 11.488467 | 0.767735 | 0.537330 | 0.387460 |
| train_through_2022_validate_2023 | overall | B | 77014 | 9.256761 | 0.546625 | 0.247362 | 0.279794 |
| train_through_2022_validate_2023 | repeat | B | 10342 | 11.014769 | 0.725222 | 0.482295 | 0.338139 |
| train_through_2022_validate_2023 | third_plus | B | 2495 | 11.512463 | 0.770741 | 0.542503 | 0.372518 |
| train_through_2022_validate_2023 | overall | C | 77014 | 9.268783 | 0.547115 | 0.247621 | 0.276476 |
| train_through_2022_validate_2023 | repeat | C | 10342 | 11.035941 | 0.728679 | 0.485740 | 0.330561 |
| train_through_2022_validate_2023 | third_plus | C | 2495 | 11.539394 | 0.773246 | 0.545224 | 0.359655 |
| train_through_2023_validate_2024 | overall | A | 74433 | 9.777679 | 0.551661 | 0.207684 | 0.205581 |
| train_through_2023_validate_2024 | repeat | A | 7882 | 11.839861 | 0.729320 | 0.431913 | 0.286661 |
| train_through_2023_validate_2024 | third_plus | A | 2180 | 12.651783 | 0.782339 | 0.502053 | 0.297812 |
| train_through_2023_validate_2024 | overall | B | 74433 | 9.782479 | 0.552208 | 0.208018 | 0.203913 |
| train_through_2023_validate_2024 | repeat | B | 7882 | 11.824558 | 0.727829 | 0.432313 | 0.285310 |
| train_through_2023_validate_2024 | third_plus | B | 2180 | 12.652484 | 0.779931 | 0.504114 | 0.299857 |
| train_through_2023_validate_2024 | overall | C | 74433 | 9.766291 | 0.551892 | 0.208162 | 0.204061 |
| train_through_2023_validate_2024 | repeat | C | 7882 | 11.798105 | 0.728590 | 0.435283 | 0.284201 |
| train_through_2023_validate_2024 | third_plus | C | 2180 | 12.613586 | 0.781537 | 0.507350 | 0.301546 |

تفاصيل fixed-budget CV والمقاييس الأخرى في `model_metrics.csv`. لا توجد مكاسب ثابتة لـ B في كل المقاييس/الفصول؛ التحليل لم يُضف trial لتصحيح فصل بعينه.

## E. Overall model results

Points هو تحويل توقع `final_mark` بواسطة GradeScale الرسمي؛ **لا يوجد مودل Production منفصل مدرب على points** في هذا المسار. لا نغير target إلى points لمجرد اسم Expected Points. GradeScale يستخدم أعلى `from_percent <= predicted_mark` لكل grade version، مع درجات النجاح، دون rounding.

| variant | rows | mae | rmse | within_5 | within_10 | points_mae | points_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 67536 | 9.707698 | 13.045276 | 0.349976 | 0.625888 | 0.576022 | 0.839027 |
| B | 67536 | 9.715150 | 13.049784 | 0.349458 | 0.624911 | 0.576215 | 0.839062 |
| C | 67536 | 9.717918 | 13.062878 | 0.350435 | 0.624319 | 0.577096 | 0.841161 |

كل مقاييس Fail الحالية:

| variant | log_loss | pr_auc | roc_auc | brier | calibration_error_10_bins |
| --- | --- | --- | --- | --- | --- |
| A | 0.274023 | 0.305110 | 0.809763 | 0.081177 | 0.021416 |
| B | 0.274334 | 0.303982 | 0.809448 | 0.081219 | 0.021542 |
| C | 0.274425 | 0.304361 | 0.809666 | 0.081240 | 0.022270 |

Lower أفضل لـ MAE/RMSE/log_loss/Brier/ECE؛ Higher أفضل لـ within/PR-AUC/ROC-AUC. دقة prediction similarity وحدها لا تعني صحة اختيار الخطط.

## F. Repeat-only results

**8,184 صفًا، 3,348 طالبًا**؛ أهم مقارنة:

| variant | rows | mae | rmse | points_mae | log_loss | pr_auc | roc_auc | brier | calibration_error_10_bins |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 8184 | 11.076449 | 14.673404 | 0.754979 | 0.518130 | 0.422897 | 0.705101 | 0.172621 | 0.051595 |
| B | 8184 | 11.089773 | 14.680746 | 0.755346 | 0.518008 | 0.420851 | 0.704958 | 0.172568 | 0.049792 |
| C | 8184 | 11.107394 | 14.735142 | 0.759653 | 0.519400 | 0.421149 | 0.705320 | 0.172805 | 0.052858 |

وللمحاولة الأولى والثانية:

| subset | variant | rows | mae | points_mae | log_loss | pr_auc |
| --- | --- | --- | --- | --- | --- | --- |
| first | A | 59352 | 9.518962 | 0.551346 | 0.240363 | 0.237287 |
| first | B | 59352 | 9.525604 | 0.551515 | 0.240734 | 0.235961 |
| first | C | 59352 | 9.526325 | 0.551923 | 0.240645 | 0.235832 |
| second | A | 6536 | 10.946127 | 0.732902 | 0.490769 | 0.381734 |
| second | B | 6536 | 10.960626 | 0.734279 | 0.491129 | 0.379934 |
| second | C | 6536 | 10.982135 | 0.738449 | 0.492553 | 0.380422 |

C أضعف من A على repeats في Grade MAE و Points MAE و Fail LogLoss، لكن حجم الزيادة صغير: +0.030945 mark، +0.004674 points، +0.001270 log loss. لا يكفي هذا وحده لإثبات ضرورة المعلومات الشخصية، ولا يعطي إذنًا بحذفها. جميع مقاييس C محفوظة مع فواصل الثقة.

### Paired uncertainty

فروق B−A؛ قيم موجبة تعني خسارة أعلى. 1,000 bootstrap draws على **الطلاب** مع كل صفوف الطالب في draw، seed=42، 95% percentile interval؛ مقارنة paired على الصف نفسه. هذه فواصل شرطية على المودلين المدربين؛ لا تغطي اختلاف training samples/seeds أو تغيّر الفصول مستقبلًا، ولا تُصحح تعدد المقارنات.

| subset | metric | rows | students | delta | low | high |
| --- | --- | --- | --- | --- | --- | --- |
| overall | grade_mae | 67536 | 7019 | 0.007452 | 0.004376 | 0.010365 |
| overall | points_mae | 67536 | 7019 | 0.000192 | -0.000292 | 0.000645 |
| overall | log_loss | 67536 | 7019 | 0.000311 | 0.000044 | 0.000565 |
| repeat | grade_mae | 8184 | 3348 | 0.013324 | 0.004069 | 0.022220 |
| repeat | points_mae | 8184 | 3348 | 0.000367 | -0.002027 | 0.002427 |
| repeat | log_loss | 8184 | 3348 | -0.000123 | -0.001274 | 0.000973 |
| third_plus | grade_mae | 1648 | 954 | 0.008661 | -0.013211 | 0.030334 |
| third_plus | points_mae | 1648 | 954 | -0.003641 | -0.010951 | 0.003012 |
| third_plus | log_loss | 1648 | 954 | -0.002036 | -0.005850 | 0.001457 |

Margins الوصفية المثبتة قبل fit: .10 mark MAE، .02 points MAE، .005 log loss. ليست حدود قبول منتج اعتمدها المستخدم، وليست شهادة equivalence لجميع metrics. الزيادات على Repeat/3+ المجمّعة أصغر منها، لكن ذلك لا يغطي PR-AUC أو ترتيب الخطط.

## G. Third+ attempt results

**1,648 صفًا، 954 طالبًا**؛ 761/537 في 20251 و 887/637 في 20252:

| variant | rows | students | mae | rmse | points_mae | log_loss | pr_auc | roc_auc | brier | calibration_error_10_bins |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 1648 | 954 | 11.593310 | 15.292103 | 0.842536 | 0.626647 | 0.516184 | 0.674131 | 0.217615 | 0.095037 |
| B | 1648 | 954 | 11.601972 | 15.308027 | 0.838896 | 0.624611 | 0.507086 | 0.668980 | 0.216936 | 0.085526 |
| C | 1648 | 954 | 11.604175 | 15.319746 | 0.843750 | 0.625877 | 0.505739 | 0.669517 | 0.217077 | 0.086650 |

3 و 4+ منفصلتان:

| subset | variant | rows | students | mae | points_mae | log_loss | pr_auc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| third | A | 1174 | 828 | 11.513006 | 0.836457 | 0.610257 | 0.497978 |
| third | B | 1174 | 828 | 11.525032 | 0.838799 | 0.610541 | 0.500405 |
| third | C | 1174 | 828 | 11.558315 | 0.842206 | 0.611856 | 0.498276 |
| fourth_plus | A | 474 | 330 | 11.792207 | 0.857595 | 0.667239 | 0.556018 |
| fourth_plus | B | 474 | 330 | 11.792535 | 0.839135 | 0.659457 | 0.528077 |
| fourth_plus | C | 474 | 330 | 11.717759 | 0.847574 | 0.660602 | 0.529777 |

مقارنة الفصول لدى Repeat و 3+:

| cohort | subset | variant | rows | mae | points_mae | log_loss | pr_auc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20251 | repeat | A | 2965 | 11.280568 | 0.766863 | 0.516848 | 0.432886 |
| 20251 | repeat | B | 2965 | 11.295452 | 0.769477 | 0.518699 | 0.414836 |
| 20251 | repeat | C | 2965 | 11.339582 | 0.774368 | 0.520109 | 0.419210 |
| 20251 | third_plus | A | 761 | 11.496816 | 0.823259 | 0.582915 | 0.478796 |
| 20251 | third_plus | B | 761 | 11.519473 | 0.825230 | 0.587366 | 0.450679 |
| 20251 | third_plus | C | 761 | 11.504679 | 0.826216 | 0.587750 | 0.452065 |
| 20252 | repeat | A | 5219 | 10.960486 | 0.748228 | 0.518859 | 0.424680 |
| 20252 | repeat | B | 5219 | 10.972923 | 0.747317 | 0.517615 | 0.429208 |
| 20252 | repeat | C | 5219 | 10.975484 | 0.751293 | 0.518997 | 0.426659 |
| 20252 | third_plus | A | 887 | 11.676097 | 0.859076 | 0.664166 | 0.545764 |
| 20252 | third_plus | B | 887 | 11.672751 | 0.850620 | 0.656564 | 0.545666 |
| 20252 | third_plus | C | 887 | 11.689536 | 0.858794 | 0.658587 | 0.541102 |

| cohort | metric | rows | students | delta | low | high |
| --- | --- | --- | --- | --- | --- | --- |
| 20251 | grade_mae | 761 | 537 | 0.022657 | -0.009824 | 0.054304 |
| 20251 | points_mae | 761 | 537 | 0.001971 | -0.006284 | 0.011181 |
| 20251 | log_loss | 761 | 537 | 0.004451 | 0.000247 | 0.008534 |
| 20252 | grade_mae | 887 | 637 | -0.003346 | -0.032290 | 0.026625 |
| 20252 | points_mae | 887 | 637 | -0.008455 | -0.019105 | 0.001451 |
| 20252 | log_loss | 887 | 637 | -0.007602 | -0.013410 | -0.002366 |

في 20251 ارتفع 3+ Fail LogLoss مع B بمقدار +.004451، CI [.000247,.008534]؛ لا نستطيع استبعاد خسارة أعلى من margin .005. في 20252 تحسن بمقدار −.007602، CI [−.013410,−.002366]. التجميع يخفي هذا الاتجاه المعاكس. PR-AUC المجمّع لـ 3+ انخفض .516184→.507086، ولـ 4+ .556018→.528077؛ حجم العينة/التذبذب يمنع الحكم القطعي على منفعة الرقم لكل tail أوفصل. Error هذه الشرائح أكبر من first؛ ندرتها لا تجعلها غير مهمة.

### Fail calibration

| subset | variant | rows | mean_predicted_fail | actual_fail_rate | prediction_minus_actual |
| --- | --- | --- | --- | --- | --- |
| first | A | 59352 | 0.064815 | 0.082070 | -0.017254 |
| first | B | 59352 | 0.064423 | 0.082070 | -0.017647 |
| first | C | 59352 | 0.064025 | 0.082070 | -0.018044 |
| second | A | 6536 | 0.185740 | 0.226132 | -0.040392 |
| second | B | 6536 | 0.185350 | 0.226132 | -0.040783 |
| second | C | 6536 | 0.181984 | 0.226132 | -0.044149 |
| third_plus | A | 1648 | 0.257029 | 0.351335 | -0.094306 |
| third_plus | B | 1648 | 0.265809 | 0.351335 | -0.085526 |
| third_plus | C | 1648 | 0.264685 | 0.351335 | -0.086650 |

B لا يعطي فعليًا نفس احتمال الرسوب لجميع الثانية والثالثة: المتوسط .185350 للثانية و.265809 لـ 3+، لأن Features التاريخ الأكاديمي/المادة الأخرى ما زالت مختلفة. لكنه يفقد التمييز الشخصي المباشر 2 مقابل 3+. كلا A و B يقللان الخطر عن المرصود؛ B حسّن mean calibration المجمّع لدى 3+، مع ضعف PR-AUC. جدول bin-by-bin الحالي، 10 bins، لكل subgroup و semester و variant متاح في `calibration_bins.csv`؛ لم نطبق recalibration.

## H. Prediction differences

Absolute B−A على الصفوف نفسها؛ delta fail probability بوحدة احتمال [0,1]، mark بوحدة [0,100]، points بوحدة [0,4]:

| subset | task | rows | mean | median | p95 | max |
| --- | --- | --- | --- | --- | --- | --- |
| overall | grade | 67536 | 0.281362 | 0.213529 | 0.764699 | 2.193225 |
| overall | points | 67536 | 0.014015 | 0.000000 | 0.250000 | 1.500000 |
| overall | fail | 67536 | 0.004909 | 0.001684 | 0.019896 | 0.165056 |
| repeat | grade | 8184 | 0.292335 | 0.227063 | 0.798025 | 1.847476 |
| repeat | points | 8184 | 0.016862 | 0.000000 | 0.250000 | 1.500000 |
| repeat | fail | 8184 | 0.011579 | 0.006886 | 0.037131 | 0.165056 |
| second | grade | 6536 | 0.287652 | 0.223368 | 0.778362 | 1.750309 |
| second | points | 6536 | 0.015147 | 0.000000 | 0.250000 | 1.500000 |
| second | fail | 6536 | 0.009871 | 0.006284 | 0.031551 | 0.111051 |
| third | grade | 1174 | 0.281782 | 0.221315 | 0.779135 | 1.847476 |
| third | points | 1174 | 0.018101 | 0.000000 | 0.250000 | 1.500000 |
| third | fail | 1174 | 0.011610 | 0.007618 | 0.037701 | 0.105779 |
| fourth_plus | grade | 474 | 0.383043 | 0.323512 | 0.908386 | 1.680053 |
| fourth_plus | points | 474 | 0.037447 | 0.000000 | 0.250000 | 1.500000 |
| fourth_plus | fail | 474 | 0.035061 | 0.019079 | 0.122141 | 0.165056 |

الحالات التالية اختيرت لتوضيح تغيرات كبيرة **وليست عينة تمثيلية**؛ لا ننشر IDs شخصية في التقرير، والتفاصيل محلية في Parquet:

| attempt_group | chosen_by | course_id | part_id | attempt_number | final_mark | grade_A | grade_B | points_A | points_B | fail_A | fail_B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | grade | 1421.111 | 20252 | 2 | 12 | 42.5345 | 44.2848 | 0.0000 | 0.0000 | 0.4652 | 0.4261 |
| 2 | fail | 664.111 | 20252 | 2 | 0 | 53.7757 | 52.8919 | 1.5000 | 1.5000 | 0.6091 | 0.4980 |
| 3 | grade | 959.111 | 20252 | 3 | 38 | 44.0179 | 45.8654 | 0.0000 | 0.0000 | 0.5641 | 0.5774 |
| 3 | fail | 689.111 | 20252 | 3 | 57 | 56.9576 | 57.2542 | 1.7500 | 1.7500 | 0.3704 | 0.4762 |
| 4+ | grade | 960.111 | 20252 | 4 | 12 | 45.3971 | 47.0772 | 0.0000 | 0.0000 | 0.5571 | 0.5703 |
| 4+ | fail | 677.111 | 20251 | 5 | 50 | 57.6815 | 57.8272 | 1.7500 | 1.7500 | 0.2889 | 0.4539 |

حتى first attempts يمكن أن تتغير توقعاتها بعد إعادة تدريب الشجر كله؛ مساواة تمثيلها الشخصي لا تعني مساواة كل splits/leaf values، خاصة مع feature_fraction. وفي C يقل عدد الأعمدة، فيتغير أيضًا فضاء اختيار feature_fraction؛ هذه خاصية ablation مع نفس إعدادات التدريب، وليست تعديلاً يدويًا لها. GradeScale المتقطع يضخم عبور حد 50 إلى فرق points يصل 1.5، رغم أن تغير mark صغير نسبيًا.

### Feature importance كدليل مساعد


| model | variant | feature | rank | gain_share | splits |
| --- | --- | --- | --- | --- | --- |
| grade | A | attempt_number | 22 | 0.002591 | 43 |
| grade | B | is_repeat | 23 | 0.002437 | 34 |
| fail | A | attempt_number | 18 | 0.006602 | 54 |
| fail | B | is_repeat | 19 | 0.004896 | 30 |

هذه أهمية gain مشروطة بالشجر وبتداخل Features؛ لا تثبت السببية ولا تحل محل A/B/C، ولا نقارن القيم الخام للـ gain بين مودلين مختلفي targets كدليل على المنفعة.

## I. Recommendation impact

أربعة طلبات فعلية صالحة من JSON exports الحالية، كلها تضم repeat candidates؛ واحدة فقط تضم 3+. اختيار inputs فقط، بترتيب حتمي، دون اختيار الحالات حسب تغير التوقعات. لم نصطنع requests أو توفر مواد في 20252. جُمعت 4,599 خطة exact18 ممكنة، بنفس المرشحين وترتيبهم و Frozen base history as_of_20243 و snapshot بداية 20251. القائمة والتفسيرات والاستبعادات في `recommendation_selection.json`.

أُعيد استخدام `prepare_candidates`، `enumerate_plan_indices`، `build_plan_rows`، `compute_plan_context_features`، GradeScale، `summarize_scored_plans`، `rank_plans` الإنتاجية دون أي تعديل. كل variant يتنبأ بكل course-in-plan لأن سياق الخطة مهم؛ لم نستخدم طريقة course-only. تحققنا أن A يطابق Production scoring لكل خطة: فرق 0.0. GPA projection هو additive الحالي، ويحمل تحذير repeat policy؛ لا نحسب استبدال درجات سابقة من عندنا.

| case | variant | candidates | repeat_candidates | third_plus_candidates | plans | top1_changed | top3_set_changed | top3_order_changed | rank_spearman | mean_absolute_rank_movement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case_01 | B | 13 | 2 | 2 | 233 | True | True | True | 0.8323 | 24.8670 |
| case_01 | C | 13 | 2 | 2 | 233 | True | True | True | 0.7952 | 30.3433 |
| case_02 | B | 9 | 1 | 0 | 10 | False | False | True | 0.9879 | 0.2000 |
| case_02 | C | 9 | 1 | 0 | 10 | False | False | False | 0.8182 | 1.2000 |
| case_03 | B | 15 | 1 | 0 | 2640 | True | True | True | 0.9459 | 216.5242 |
| case_03 | C | 15 | 1 | 0 | 2640 | True | True | True | 0.8237 | 346.8447 |
| case_04 | B | 13 | 1 | 0 | 1716 | False | False | False | 0.9783 | 79.7984 |
| case_04 | C | 13 | 1 | 0 | 1716 | False | True | True | 0.9560 | 114.8263 |

B: **Top‑1 تغير في 2/4**؛ Top‑3 set في 2/4؛ Top‑3 order في 3/4. C: Top‑1 في 2/4؛ Top‑3 set في 3/4. 2/4 ليس تقديرًا سكانيًا مستقرًا: Wilson95% تقريبًا 15%–85%، والعينة convenience أصلًا. الحالة الوحيدة 3+ تغير فيها Top‑1 و Top‑3؛ **INSUFFICIENT EVIDENCE** للحكم على معدل التغير أو quality لدى 3+ في Production.

GPA أفضل خطة لكل مودل:

| case | variant | best_expected_plan_gpa_A | best_expected_plan_gpa_other | best_projected_gpa_A | best_projected_gpa_other | baseline_top1_rank_other | other_top1_rank_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- |
| case_01 | B | 2.041667 | 2.041667 | 2.040081 | 2.040081 | 14 | 12 |
| case_01 | C | 2.041667 | 2.027778 | 2.040081 | 2.039407 | 28 | 12 |
| case_02 | B | 1.888889 | 1.888889 | 2.022964 | 2.022964 | 1 | 1 |
| case_02 | C | 1.888889 | 1.861111 | 2.022964 | 2.021579 | 1 | 1 |
| case_03 | B | 1.902778 | 1.902778 | 1.724830 | 1.724830 | 37 | 7 |
| case_03 | C | 1.902778 | 1.833333 | 1.724830 | 1.716327 | 62 | 266 |
| case_04 | B | 2.708333 | 2.666667 | 2.528529 | 2.521176 | 1 | 1 |
| case_04 | C | 2.708333 | 2.666667 | 2.528529 | 2.521176 | 1 | 1 |

قد تتغير Top‑1 مع نفس GPA بسبب فصل النقاط المتقطع و Fail tie breaker؛ هذا حدث في case_01 و case_03 مع B. لا تعني مساواة GPA أن المواد المختارة متطابقة.

تغير توقعات **الخطة نفسها** (absolute deltas، نمنع خلط أثر اختيار خطة مختلفة بأثر النموذج):

| case | same_plan_abs_expected_plan_gpa_mean | same_plan_abs_expected_plan_gpa_median | same_plan_abs_expected_plan_gpa_p95 | same_plan_abs_expected_plan_gpa_max | same_plan_abs_projected_cumulative_gpa_mean | same_plan_abs_projected_cumulative_gpa_max |
| --- | --- | --- | --- | --- | --- | --- |
| case_01 | 0.035765 | 0.041667 | 0.041667 | 0.041667 | 0.001735 | 0.002022 |
| case_02 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| case_03 | 0.014431 | 0.000000 | 0.027778 | 0.055556 | 0.001767 | 0.006803 |
| case_04 | 0.010951 | 0.000000 | 0.041667 | 0.041667 | 0.001933 | 0.007353 |

لكل حالة all-plans A/B/C محفوظة مع rank و expected_failed_credits وكل GPA في `recommendations/case_*/plans_*.parquet`. اختلاف الترتيب **حساسية سلوك**، وليس إثبات جودة أعلى أوأقل: لا تتوافر نتائج counterfactual للخطط البديلة. كذلك مصدر exports ووقت `is_requestable` لا يثبتان توفرها تاريخيًا في 20251؛ هذه مقارنة serving inputs موثوقة، وليست historical availability backtest أو policy evaluation كاملة.

### GPA للخطط المسجلة الفعلية

التقييم الحالي على observed plans، مختلف عن ترتيب البدائل: 12,713 خطة طالب/degree/فصل. كل مقاييس `summarize_plan_errors` الحالية محفوظة لجميع الفصول وال variants، وللخطط ذات أي repeat.


| variant | subset | plans | mae | credits_weighted_mae | rmse | bias | within_0_25 | within_0_50 | within_1_00 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | all_observed_plans | 12713 | 0.454199 | 0.416908 | 0.639670 | 0.213762 | 0.439943 | 0.684732 | 0.895383 |
| A | observed_plans_with_repeat | 4257 | 0.530971 | 0.491505 | 0.709002 | 0.306956 | 0.367865 | 0.604181 | 0.850834 |
| B | all_observed_plans | 12713 | 0.454920 | 0.417569 | 0.639630 | 0.213310 | 0.436876 | 0.684811 | 0.895619 |
| B | observed_plans_with_repeat | 4257 | 0.530995 | 0.491057 | 0.708705 | 0.307258 | 0.365281 | 0.604886 | 0.852243 |
| C | all_observed_plans | 12713 | 0.455849 | 0.418406 | 0.642127 | 0.218583 | 0.438213 | 0.681192 | 0.895383 |
| C | observed_plans_with_repeat | 4257 | 0.532488 | 0.492530 | 0.711490 | 0.312330 | 0.365046 | 0.601832 | 0.852713 |

## J. Production implication

| خيار | ماذا يحتاج Backend | حدود الدلالة |
| --- | --- | --- |
| A | رقم مطابق لقواعد العد الحالية للطالب/المادة، عبر degrees، مع cutoff | يعتمد على تاريخ عدّ كامل وفق الفلاتر المحددة |
| B | Boolean يدل على وجود محاولة سابقة **حسب قواعد العد نفسها** | لا يكفي تعريفه had_previous_fail أووجود صف ناجح/راسب محفوظ فقط |
| C | لا feature محاولة شخصية في المودل | تبقى احتياجات repeat policy والتاريخ وتجميع course retries مستقلة |

Boolean قد يقلل متطلبات نقل عدد المحاولات، لكن **لا يحل تلقائيًا اختلاف Cleaning/Serving** أوحد ماقبل 2020. تعريف has_previous_attempt يجب أن يتفق مع أنواع التسجيل counted؛ وإلا تختبر الخدمة feature مختلفة عن `(attempt_number>1)` هنا. وفي B/C ما زال التحذير `projected_gpa_requires_repeat_policy` يحتاج كشف repeat لأغراض Recommendation. لا يترتب على حذف feature شخصية حذف Frozen History أوقدرة النظام على معرفة retries تجميعيًا.

## K. Conclusion

**Evidence is insufficient** لإقرار أن Boolean مكافئ في Prediction quality **و**Recommendation behavior. على metrics المجمعة B قريب من A، لكن LogLoss لـ 3+ يتغير اتجاهه بين 20251/20252، و CI20251 لا يستبعد خسارة>.005، و PR‑AUC أقل، والترتيب تغير في 2/4 حالات. حجم العينة يكفي لرصد فروق التنبؤ الصغيرة المشروطة في 3+، لكنه لا يكفي لاستنتاج ثبات توصياتهم أوتعميمها على 6+.

**Keep attempt_number في Production حاليًا.** لا نزعم YES للضرورة الإحصائية، ولا NO لإمكان الاستبدال بلا خسارة؛ الإجابة **INCONCLUSIVE**. كذلك لا ندعم حذف attempt information لمجرد أن C قريب إجمالًا؛ هو أضعف على Repeat وبعض مقاييس Validation.

قبل قرار لاحق: عينة توصيات أكبر من فصول ذات requests موثقة الوقت، وبالأخص 3+؛ tolerances منتج متفق عليها لمقاييس Repeat/3+ و Top‑K؛ تحقق مستقبلي ثابت قبل أي engineering جديد. هذه خطوات تالية، لم تُستخدم لتعديل trial الحالي.

### العزل والتحقق وإعادة التنفيذ

- protected files: **799**؛ changed=[]؛ added=[]؛ production artifacts modified=False.
- الاختبارات المركزة: 11 passed (8 experiment tests + 3 dependency-direction tests). الاختبارات الكاملة: 592 passed, 1 pre-existing failure, 6 subtests passed.
- الفشل المتبقي السابق: `tests/test_train_models.py` يتوقع `capacity_63` بينما المصدر الحالي يعطي `capaciy_63`. لم يُصلح ضمن هذه المهمة. اختبار اتجاه الاعتماد نجح بعد وضع أداة Recommendation في scripts، دون تخفيف الاختبار.
- output/model SHA‑256 و ordered row fingerprints ومعلومات environment في manifests. ملفات predictions وال cases محلية وتتضمن سجلات؛ لم تُرسل ولم تُعمل commits لها.
- إضافة كود فقط: `src/experiments/attempt_number_*.py`؛ أداة orchestration/recommendation في `scripts/experiments/attempt_number_*.py`؛ اختبارات وتجربة plan وتقرير. لا تعديل source إنتاجي أو feature contract أو recommendation contract.

```powershell
.\.venv\Scripts\python.exe -m scripts.experiments.attempt_number_experiment
# Existing signed run: explicit reuse without silently refitting
.\.venv\Scripts\python.exe -m scripts.experiments.attempt_number_experiment --resume
# Rebuild report only from saved evidence
.\.venv\Scripts\python.exe -m scripts.experiments.attempt_number_experiment --report-only
```

أي محاولة initial جديدة في namespace موجودة تُرفض؛ --resume يتطلب نفس input/source signature ويتحقق من model hashes. الحذف الممكن لاحقًا محصور بـ namespace التجربة وموديولاتها الجديدة؛ لا يحتاج مراجعة أوتغيير artifacts الإنتاج.

### Summary

Points MAE و Fail LogLoss؛ قيمة أقل أفضل. عمودا Repeat/3+ يعرضان `points / logloss`:

| Experiment | Points model | Fail model | Repeat subset | Third+ subset | Recommendation impact | Complexity |
| --- | --- | --- | --- | --- | --- | --- |
| attempt_number | 0.576022 | 0.274023 | 0.754979 / 0.518130 | 0.842536 / 0.626647 | reference | عدد صحيح |
| is_repeat | 0.576215 | 0.274334 | 0.755346 / 0.518008 | 0.838896 / 0.624611 | Top‑1:2/4، Top‑3 set:2/4 | Boolean |
| no attempt | 0.577096 | 0.274425 | 0.759653 / 0.519400 | 0.843750 / 0.625877 | Top‑1:2/4، Top‑3 set:3/4 | feature أقل |

**Does the model need the exact attempt number? INCONCLUSIVE.**
الفروق الإجمالية صغيرة جدًا، و Boolean مرشح معقول للتبسيط، لكن 3+ يظهر تباينًا زمنيًا تخفيه المقارنة المجمعة.
التوصيات تغيرت في عينة صغيرة من cases حقيقية؛ لا دليل على تكافؤ quality للخطط المتغيرة.
الحفاظ على attempt_number حاليًا، مع بقاء B/C تجريبيين، هو القرار المدعوم بما لدينا.
