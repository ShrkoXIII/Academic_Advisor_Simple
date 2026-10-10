# تجربة مستقلة لحذف `attempt_number` — 2026-10-08

## النتيجة

**مستوى الضرر صغير، ويختلف بين النموذجين.** الحذف يضر نموذج `47` ميزة قليلًا، ويحسن متوسط نموذج `33` في اختبار 2025 قليلًا، لكنه يزيد خطأ العلامة لدى الطلاب الذين يعيدون المادة في النموذجين. لذلك القرار الحالي: **`KEEP_ATTEMPT_NUMBER_FOR_NOW`**؛ نتائج التجربة لا تعتمد حذفها من الإنتاج.

- `47 → 46`: `Grade MAE` يرتفع من `9.707698` إلى `9.717918`، أي `+0.010221` علامة من 100 أو نحو `+0.105%` من الخطأ الأصلي. `Fail LogLoss` يرتفع من `0.274023` إلى `0.274425`، أي نحو `+0.147%`.
- `33 → 32`: `Grade MAE` ينخفض من `9.718017` إلى `9.708218`، أي نحو `-0.101%`؛ `Fail LogLoss` ينخفض من `0.275495` إلى `0.274932`، أي نحو `-0.204%`. هذا التحسن الإجمالي لا يتكرر في فصلي التحقق الأقدم.
- المعيدون: خطأ العلامة يرتفع `+0.030945` في نموذج 47 (`+0.279%`) و`+0.035672` في نموذج 33 (`+0.322%`). الزيادة في خطأ نقاط `GradeScale` نحو `+0.619%` و`+0.429%` على الترتيب.
- المحاولة الثالثة فأكثر: مؤشرات مختلطة وفواصل ثقة تشمل الصفر؛ لا يوجد دليل ثابت على ضرر كبير.

النسب السابقة تغير نسبي في **الخطأ**، وليست نسب فقدان في دقة النموذج أو نسب رسوب إضافية.

## ما الذي تمثله الميزة؟

`attempt_number` هو ترتيب تسجيل الطالب في المادة نفسها: `1` لأول محاولة، `2` للثانية وهكذا. في الكود الحالي، يرتب `clean_student_course.py` السجلات حسب `(student_id, course_id, part_id)` ثم يستخدم `cumcount()+1` لكل `(student_id, course_id)`، دون فصل حسب `degree_id`. الحساب يسبق إزالة بعض حالات الانتهاء، لذلك لا يعني الرقم عدد مرات الرسوب فقط. لا يحتوي وحده على نتيجة المحاولة السابقة.

يعطي النموذج معلومة شخصية عن إعادة **هذه المادة**؛ `course_history_avg_attempt` و`course_history_retake_rate` يصفان تاريخ المادة لدى المجموعة، و`prior_total_fail_courses` يصف تاريخ الطالب العام، لذلك أبقينا كل تلك الميزات ثابتة في هذه التجربة.

## نطاق المقارنة وضبطها

| العائلة | مع الميزة A | بعد حذفها C | Grade trees | Fail trees |
| --- | --- | --- | --- | --- |
| `47_plan_aware` | 47 ميزة | 46 ميزة | 114 | 112 |
| `33_course_only` | 33 ميزة | 32 ميزة | 125 | 85 |

- أربعة نماذج في كل تقسيم × ثلاثة تقسيمات × عائلتين = **24 تدريبًا جديدًا**. لم تُستخدم النماذج التجريبية القديمة بدل إعادة التدريب.
- تدريب على `356,816` سجلًا حتى `20243`؛ اختبار على `67,536` سجلًا في `20251` و`20252`، لـ`7,019` طالبًا. `8,184` سجل إعادة لـ`3,348` طالبًا؛ `1,648` سجل محاولة ثالثة فأكثر لـ`954` طالبًا.
- فصلا التحقق: التدريب حتى `20223` والتقييم في `20231–20233`؛ ثم التدريب حتى `20233` والتقييم في `20241–20243`.
- نفس الصفوف وترتيبها، targets، الأوزان، معالجة القيم والفئات، إعدادات LightGBM وseed `42` وعدد الأشجار لكل زوج. الحذف يزيل `attempt_number` وحده من مصفوفة النموذج؛ لم يُستبدل بميزة أخرى ولم تُعدّل البيانات الأصلية.
- قرأنا إعدادات كل عائلة من metadata الموجودة وثبتناها قبل المقارنة. لا tuning جديد ولا early stopping مختلف ولا اختيار إعدادات من Test. الفصول هنا تستخدم ميزانية الأشجار النهائية الثابتة للتشخيص، وليست إعادة تشغيل شبكة التوليف الأصلية.
- نستخدم ميزات V2 الزمنية المحفوظة كما هي. تاريخ `20252` يمكن أن يحتوي نتائج `20251` النهائية وفق بروتوكول التاريخ الموجود، لكن النموذج لا يُعاد تدريبه على اختبار 2025.
- نماذج 33 الأصلية مطابقة بالبايت لنماذج `stage1` في `models/shortlist_v2/`. نماذج 47 الأصلية هي المراجع المسجلة لـ`stage2` في manifest الحالي.
- **تطابق خط الأساس:** النماذج الأربعة A أعادت توقعات المراجع المحفوظة بالضبط: أكبر فرق مطلق `0.0` لكل Grade وFail في العائلتين. الدليل: `baseline_reproduction.json`.
- Test 2025 سبق الاطلاع عليه في تجارب المشروع؛ هذه مقارنة بإعدادات مثبتة، وليست holdout جديدًا أعمى.

## المقاييس على Holdout

`A` مع الميزة؛ `C` دونها. الأقل أفضل لـ`MAE`, `Points MAE`, `LogLoss`؛ الأعلى أفضل لـ`PR-AUC`.

| family | subset | variant | rows | mae | points_mae | log_loss | pr_auc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 47_plan_aware | overall | A | 67536 | 9.707698 | 0.576022 | 0.274023 | 0.305110 |
| 47_plan_aware | overall | C | 67536 | 9.717918 | 0.577096 | 0.274425 | 0.304361 |
| 47_plan_aware | repeat | A | 8184 | 11.076449 | 0.754979 | 0.518130 | 0.422897 |
| 47_plan_aware | repeat | C | 8184 | 11.107394 | 0.759653 | 0.519400 | 0.421149 |
| 47_plan_aware | third_plus | A | 1648 | 11.593310 | 0.842536 | 0.626647 | 0.516184 |
| 47_plan_aware | third_plus | C | 1648 | 11.604175 | 0.843750 | 0.625877 | 0.505739 |
| 33_course_only | overall | A | 67536 | 9.718017 | 0.576796 | 0.275495 | 0.299132 |
| 33_course_only | overall | C | 67536 | 9.708218 | 0.576367 | 0.274932 | 0.308770 |
| 33_course_only | repeat | A | 8184 | 11.072020 | 0.755010 | 0.520475 | 0.419044 |
| 33_course_only | repeat | C | 8184 | 11.107693 | 0.758248 | 0.520678 | 0.428954 |
| 33_course_only | third_plus | A | 1648 | 11.584565 | 0.841778 | 0.632151 | 0.508225 |
| 33_course_only | third_plus | C | 1648 | 11.624101 | 0.846025 | 0.629551 | 0.514360 |

## مقدار التغير

`delta = C - A`؛ الموجب في مقاييس الخطأ يعني ضررًا، والسالب في `PR-AUC` يعني ضررًا. `relative_percent` هو نسبة التغير قياسًا إلى نفس المقياس قبل الحذف.

| family | subset | metric | delta | relative_percent |
| --- | --- | --- | --- | --- |
| 47_plan_aware | overall | mae | 0.010221 | 0.105284 |
| 47_plan_aware | overall | points_mae | 0.001074 | 0.186365 |
| 47_plan_aware | overall | log_loss | 0.000402 | 0.146604 |
| 47_plan_aware | overall | pr_auc | -0.000749 | -0.245323 |
| 47_plan_aware | repeat | mae | 0.030945 | 0.279374 |
| 47_plan_aware | repeat | points_mae | 0.004674 | 0.619057 |
| 47_plan_aware | repeat | log_loss | 0.001269 | 0.244990 |
| 47_plan_aware | repeat | pr_auc | -0.001748 | -0.413298 |
| 47_plan_aware | third_plus | mae | 0.010864 | 0.093713 |
| 47_plan_aware | third_plus | points_mae | 0.001214 | 0.144040 |
| 47_plan_aware | third_plus | log_loss | -0.000770 | -0.122886 |
| 47_plan_aware | third_plus | pr_auc | -0.010445 | -2.023510 |
| 33_course_only | overall | mae | -0.009798 | -0.100827 |
| 33_course_only | overall | points_mae | -0.000429 | -0.074446 |
| 33_course_only | overall | log_loss | -0.000563 | -0.204193 |
| 33_course_only | overall | pr_auc | 0.009638 | 3.221920 |
| 33_course_only | repeat | mae | 0.035672 | 0.322183 |
| 33_course_only | repeat | points_mae | 0.003238 | 0.428872 |
| 33_course_only | repeat | log_loss | 0.000204 | 0.039149 |
| 33_course_only | repeat | pr_auc | 0.009911 | 2.365029 |
| 33_course_only | third_plus | mae | 0.039536 | 0.341280 |
| 33_course_only | third_plus | points_mae | 0.004248 | 0.504595 |
| 33_course_only | third_plus | log_loss | -0.002600 | -0.411356 |
| 33_course_only | third_plus | pr_auc | 0.006135 | 1.207108 |

## عدم اليقين

Paired student-cluster bootstrap بـ`1000` إعادة سحب وseed `42`، مع الاحتفاظ بجميع صفوف الطالب في العينة. الفاصل `95%` يقيس عدم اليقين من عينة الطلاب، ولا يغطي اختلاف seeds أو اختيارات hyperparameters أو تغير الفصول مستقبلًا.

| family | subset | metric | delta | low | high |
| --- | --- | --- | --- | --- | --- |
| 47_plan_aware | overall | mae | 0.010221 | 0.003611 | 0.016677 |
| 47_plan_aware | overall | points_mae | 0.001074 | 0.000379 | 0.001835 |
| 47_plan_aware | overall | log_loss | 0.000402 | 0.000077 | 0.000728 |
| 47_plan_aware | repeat | mae | 0.030945 | 0.006788 | 0.056092 |
| 47_plan_aware | repeat | points_mae | 0.004674 | 0.001803 | 0.007748 |
| 47_plan_aware | repeat | log_loss | 0.001269 | -0.000237 | 0.002794 |
| 47_plan_aware | third_plus | mae | 0.010864 | -0.038030 | 0.057931 |
| 47_plan_aware | third_plus | points_mae | 0.001214 | -0.006621 | 0.008974 |
| 47_plan_aware | third_plus | log_loss | -0.000770 | -0.005163 | 0.003376 |
| 33_course_only | overall | mae | -0.009798 | -0.016309 | -0.003218 |
| 33_course_only | overall | points_mae | -0.000429 | -0.001143 | 0.000304 |
| 33_course_only | overall | log_loss | -0.000563 | -0.000915 | -0.000216 |
| 33_course_only | repeat | mae | 0.035672 | 0.012890 | 0.056503 |
| 33_course_only | repeat | points_mae | 0.003238 | 0.000579 | 0.005961 |
| 33_course_only | repeat | log_loss | 0.000204 | -0.001368 | 0.001760 |
| 33_course_only | third_plus | mae | 0.039536 | -0.007735 | 0.084546 |
| 33_course_only | third_plus | points_mae | 0.004248 | -0.002767 | 0.011857 |
| 33_course_only | third_plus | log_loss | -0.002600 | -0.006811 | 0.001882 |

التراجع الإجمالي في خطأ العلامة والنقاط وLogLoss لنموذج 47 فواصله أعلى من الصفر. وفي نموذج 33، التحسن الإجمالي في خطأ العلامة وLogLoss فواصله أدنى من الصفر، بينما تراجع خطأ العلامة والنقاط لدى المعيدين فواصله أعلى من الصفر. لذلك صغر الأثر لا يعني أنه صفر، وتفاوت الشرائح مهم.

## فصول التحقق السابقة

| family | cohort | subset | metric | delta |
| --- | --- | --- | --- | --- |
| 47_plan_aware | train_through_2022_validate_2023 | overall | mae | 0.006080 |
| 47_plan_aware | train_through_2022_validate_2023 | overall | points_mae | 0.000192 |
| 47_plan_aware | train_through_2022_validate_2023 | overall | log_loss | 0.000644 |
| 47_plan_aware | train_through_2022_validate_2023 | overall | pr_auc | -0.005135 |
| 47_plan_aware | train_through_2022_validate_2023 | repeat | mae | 0.001161 |
| 47_plan_aware | train_through_2022_validate_2023 | repeat | points_mae | 0.001112 |
| 47_plan_aware | train_through_2022_validate_2023 | repeat | log_loss | 0.003086 |
| 47_plan_aware | train_through_2022_validate_2023 | repeat | pr_auc | -0.008345 |
| 47_plan_aware | train_through_2022_validate_2023 | third_plus | mae | 0.029259 |
| 47_plan_aware | train_through_2022_validate_2023 | third_plus | points_mae | 0.003106 |
| 47_plan_aware | train_through_2022_validate_2023 | third_plus | log_loss | 0.007073 |
| 47_plan_aware | train_through_2022_validate_2023 | third_plus | pr_auc | -0.025396 |
| 47_plan_aware | train_through_2023_validate_2024 | overall | mae | -0.001531 |
| 47_plan_aware | train_through_2023_validate_2024 | overall | points_mae | 0.000890 |
| 47_plan_aware | train_through_2023_validate_2024 | overall | log_loss | 0.000309 |
| 47_plan_aware | train_through_2023_validate_2024 | overall | pr_auc | -0.001820 |
| 47_plan_aware | train_through_2023_validate_2024 | repeat | mae | -0.004192 |
| 47_plan_aware | train_through_2023_validate_2024 | repeat | points_mae | 0.002823 |
| 47_plan_aware | train_through_2023_validate_2024 | repeat | log_loss | 0.003348 |
| 47_plan_aware | train_through_2023_validate_2024 | repeat | pr_auc | -0.004664 |
| 47_plan_aware | train_through_2023_validate_2024 | third_plus | mae | 0.003856 |
| 47_plan_aware | train_through_2023_validate_2024 | third_plus | points_mae | 0.007339 |
| 47_plan_aware | train_through_2023_validate_2024 | third_plus | log_loss | 0.005237 |
| 47_plan_aware | train_through_2023_validate_2024 | third_plus | pr_auc | -0.000624 |
| 33_course_only | train_through_2022_validate_2023 | overall | mae | 0.007403 |
| 33_course_only | train_through_2022_validate_2023 | overall | points_mae | -0.000036 |
| 33_course_only | train_through_2022_validate_2023 | overall | log_loss | 0.000932 |
| 33_course_only | train_through_2022_validate_2023 | overall | pr_auc | -0.005529 |
| 33_course_only | train_through_2022_validate_2023 | repeat | mae | 0.016336 |
| 33_course_only | train_through_2022_validate_2023 | repeat | points_mae | 0.000435 |
| 33_course_only | train_through_2022_validate_2023 | repeat | log_loss | 0.003061 |
| 33_course_only | train_through_2022_validate_2023 | repeat | pr_auc | -0.006669 |
| 33_course_only | train_through_2022_validate_2023 | third_plus | mae | 0.051992 |
| 33_course_only | train_through_2022_validate_2023 | third_plus | points_mae | 0.002405 |
| 33_course_only | train_through_2022_validate_2023 | third_plus | log_loss | 0.003494 |
| 33_course_only | train_through_2022_validate_2023 | third_plus | pr_auc | -0.016899 |
| 33_course_only | train_through_2023_validate_2024 | overall | mae | 0.016759 |
| 33_course_only | train_through_2023_validate_2024 | overall | points_mae | 0.000712 |
| 33_course_only | train_through_2023_validate_2024 | overall | log_loss | 0.000628 |
| 33_course_only | train_through_2023_validate_2024 | overall | pr_auc | -0.002742 |
| 33_course_only | train_through_2023_validate_2024 | repeat | mae | -0.002847 |
| 33_course_only | train_through_2023_validate_2024 | repeat | points_mae | -0.001649 |
| 33_course_only | train_through_2023_validate_2024 | repeat | log_loss | 0.004018 |
| 33_course_only | train_through_2023_validate_2024 | repeat | pr_auc | -0.008657 |
| 33_course_only | train_through_2023_validate_2024 | third_plus | mae | 0.015711 |
| 33_course_only | train_through_2023_validate_2024 | third_plus | points_mae | -0.000115 |
| 33_course_only | train_through_2023_validate_2024 | third_plus | log_loss | 0.007440 |
| 33_course_only | train_through_2023_validate_2024 | third_plus | pr_auc | -0.014126 |

في نموذج 33، الحذف يرفع `Grade MAE` و`Fail LogLoss` الإجماليين في **فصلي التحقق الأقدم**، خلاف تحسنهما الإجمالي في 2025. وفي نموذج 47، يزيد `Fail LogLoss` و`Points MAE` الإجماليين في كلا الفصلين. هذا يمنع اعتماد قرار حذف عام من متوسط Holdout وحده.

## كل فصل من اختبار 2025

| family | cohort | subset | metric | delta |
| --- | --- | --- | --- | --- |
| 47_plan_aware | 20251 | overall | mae | 0.024125 |
| 47_plan_aware | 20251 | overall | log_loss | 0.000185 |
| 47_plan_aware | 20251 | repeat | mae | 0.059015 |
| 47_plan_aware | 20251 | repeat | log_loss | 0.003260 |
| 47_plan_aware | 20251 | third_plus | mae | 0.007863 |
| 47_plan_aware | 20251 | third_plus | log_loss | 0.004835 |
| 47_plan_aware | 20252 | overall | mae | -0.004221 |
| 47_plan_aware | 20252 | overall | log_loss | 0.000627 |
| 47_plan_aware | 20252 | repeat | mae | 0.014998 |
| 47_plan_aware | 20252 | repeat | log_loss | 0.000138 |
| 47_plan_aware | 20252 | third_plus | mae | 0.013439 |
| 47_plan_aware | 20252 | third_plus | log_loss | -0.005579 |
| 33_course_only | 20251 | overall | mae | -0.027381 |
| 33_course_only | 20251 | overall | log_loss | -0.000481 |
| 33_course_only | 20251 | repeat | mae | 0.005760 |
| 33_course_only | 20251 | repeat | log_loss | 0.002402 |
| 33_course_only | 20251 | third_plus | mae | 0.032721 |
| 33_course_only | 20251 | third_plus | log_loss | 0.000484 |
| 33_course_only | 20252 | overall | mae | 0.008464 |
| 33_course_only | 20252 | overall | log_loss | -0.000647 |
| 33_course_only | 20252 | repeat | mae | 0.052666 |
| 33_course_only | 20252 | repeat | log_loss | -0.001045 |
| 33_course_only | 20252 | third_plus | mae | 0.045383 |
| 33_course_only | 20252 | third_plus | log_loss | -0.005246 |

## أهمية الميزة داخل الأشجار

| family | task | attempt_gain_share_percent | attempt_gain_rank |
| --- | --- | --- | --- |
| 47_plan_aware | grade | 0.259070 | 22 |
| 47_plan_aware | fail | 0.660228 | 18 |
| 33_course_only | grade | 0.247509 | 22 |
| 33_course_only | fail | 0.816082 | 19 |

حصة gain للميزة نحو `0.25%` في Grade و`0.66–0.82%` في Fail؛ ترتيبها متوسط. هذه الحصص ليست مقدار فقدان الأداء عند حذفها ولا قياسًا سببيًا. المقارنة بعد إعادة التدريب أعلاه هي الدليل العملي.

## الأثر على التوصيات

لم نشغّل توصيات فعلية ولم نقس جودة ترتيب الخطط في هذه التجربة. يمكن لتغير صغير في العلامة أن يتجاوز عتبة في `GradeScale`، لذلك لا تعادل سلامة المتوسط العام إثبات بقاء `Top K` أو تحسنها. لا تستنتج من هذه الأرقام نسبة ضرر لترتيب التوصيات.

## العزل والملفات

تمت مقارنة SHA-256 لـ**957 ملفًا محميًا** قبل التجربة وبعدها: `changed=[]`, `added=[]`, `official_artifacts_modified=false`. يشمل ذلك البيانات السابقة، النماذج السابقة، Frozen History، وملفات Python خارج التجارب تحت `src/`. **Production models / feature contract / history: NOT CHANGED.**

- [السكربت](../scripts/experiments/attempt_number_removal_recheck.py).
- [دليل المقاييس](../data/evaluation/experiments/attempt_number_removal_20261008/model_metrics.csv).
- [التغيرات](../data/evaluation/experiments/attempt_number_removal_20261008/removal_deltas.csv).
- [فواصل الثقة](../data/evaluation/experiments/attempt_number_removal_20261008/paired_student_bootstrap.csv).
- [إثبات العزل](../data/evaluation/experiments/attempt_number_removal_20261008/isolation_verification.json).
- النماذج الجديدة: `models/experiments/attempt_number_removal_20261008/` فقط.

إعادة التشغيل في مجلد **جديد**:

```powershell
.\.venv\Scripts\python.exe -m scripts.experiments.attempt_number_removal_recheck --output-name attempt_number_removal_new_run
```

السكربت يرفض الكتابة فوق تجربة موجودة. الزمن الفعلي للتدريب والتقييم في هذه الجلسة نحو `312.5` ثانية، دون احتساب الفحص الأول للملفات أو اختبارات المشروع.

## التحقق من السكربت والمشروع

- فحص التجربة واتجاه الاعتماد: **11 passed**؛ `tests/test_attempt_number_experiment.py` و`tests/test_recommendation_dependency_direction.py`.
- تم تشغيل المقارنة الفعلية كاملة: **24 نموذجًا جديدًا**، ومقاييس كل تقسيم وشريحة محفوظة؛ baseline parity تساوي صفرًا لجميع المراجع الأربعة، وعزل الملفات المحمية تحقق مجددًا بعد الفحص.
- الفحص العام الأول: `1053 passed, 92 failed, 6 subtests passed`. `91` إخفاقًا زالت عند نقل `TEMP` و`TMP` و`--basetemp` إلى مساحة العمل؛ شملت رفض Windows عمليات `rename/replace` في مجلد sandbox المؤقت الافتراضي. ثلاثة اختبارات ممثلة لهذه المشكلة نجحت مباشرة بعد تغيير البيئة.
- **الفحص العام النهائي: `1144 passed, 1 failed, 6 subtests passed`.** الإخفاق الباقي baseline سابق: المصدر يسمّي المرشح `capaciy_63` والاختبار يتوقع `capacity_63` في `tests/test_train_models.py:186`. لم نعدّل المصدر أو الاختبار لإخفائه. لا نصف المجموعة الكاملة بأنها green.
- **Regressions observed: 0** بعد تجاوز مشكلة بيئة الملفات المؤقتة. هذه عبارة عن نتائج المجموعة الحالية، ولا تعني ضمانًا مطلقًا لخلو كل كود من الأخطاء.
- `graphify update .` اكتمل بتحديث AST فقط، دون تكلفة API.
- `git diff --check` لم يسجل أخطاء whitespace. تعديلات الإنتاج الموجودة في مساحة العمل قبل البداية، بما فيها manifest ومكونات المرحلتين، بقيت كما كانت وفق بصمات البداية؛ الإضافات الخاصة بالطلب هي سكربت التجربة والتقرير وأدلتها، مع تحديث graphify.
- [سجل الفحص الكامل](attempt_number_removal_20261008_validation/pytest_full.log) و[نتيجة JUnit](attempt_number_removal_20261008_validation/pytest_full.xml). أرقام الاختبارات والتصنيف محفوظة أيضًا في `validation_results.json` داخل مجلد أدلة التجربة.

أمر الفحص العام النهائي استخدم `--basetemp reports/attempt_number_removal_20261008_validation/pytest_full` مع توجيه `TEMP/TMP` إلى مجلد مؤقت داخل مساحة العمل. لم يتطلب تعديل كود الإنتاج.
