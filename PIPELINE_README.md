# مسار مشروع Academic Advisor كاملًا

> تحديث النقل إلى V2: مراحل `src.data` و`src.features` تكتب ملفات `_v2` وتقرأ الوسائط من الإصدار نفسه. المسارات غير الملحقة والأرقام القديمة أدناه تصف مخرجات V1 المحفوظة. التدريب والتقييم والتوصية ما زالت تستخدم مخرجاتها الحالية ولم تُحوّل إلى V2. التشغيل الفعلي الكامل لـV2 متوقف حاليًا على مفاتيح ناقصة في raw courses وفصول خام غير صالحة وفق الحراس الحالية؛ راجع [تقرير النقل](reports/data_features_v2_20260921/report.md).

هذا الملف يشرح خط انتقال البيانات كاملًا: ما الذي يدخل كل مرحلة، ما السكربت
المسؤول عنها، ما الملفات التي تنتج، ومن يستهلك هذه الملفات بعد ذلك.

للحالة الحالية والخطوة التالية استخدم `START_HERE.md`. أما هذا الملف فهو مرجع
الـpipeline من البداية إلى النهاية.

## الخريطة الكاملة

```text
data/raw/
│
├─ v_crg_student_course_raw.parquet
├─ v_add_student_degree_status.parquet
├─ v_acd_degree_course.parquet
├─ v_add_academic_info.parquet
└─ v_acs_grade.parquet
        │
        ▼
تنظيف الجداول الأساسية
│
├─ src/data/clean_student_course.py
├─ src/data/clean_student_status.py
├─ src/data/clean_degree_course.py
└─ src/data/clean_student_diploma.py
        │
        ▼
data/clean/
│
├─ student_course.parquet
├─ student_status.parquet
├─ degree_course.parquet
└─ student_diploma.parquet
        │
        ▼
الإثراء والدمج
│
├─ src/data/build_student_course_enriched.py
└─ src/data/clean_student_diploma.py
        │
        ├─ data/clean/student_course_enriched.parquet
        └─ data/merged/student_course_enriched_with_diploma.parquet
        │
        ▼
حذف الطلاب ذوي القيم الشاذة
│
└─ src/data/clean_outliers.py
        │
        ▼
data/merged/
│
├─ student_course_enriched_without_outliers.parquet
└─ outlier_students.parquet
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
تقسيم صفوف أهداف المودل                  بناء roster الحمل الكامل
src/data/build_temporal_split.py              src/data/build_registration_roster.py
        │                                      │
        ▼                                      ▼
data/temporal/                          data/temporal/
├─ temporal_train.parquet               ├─ temporal_train_roster.parquet
└─ temporal_test.parquet                └─ temporal_test_roster.parquet
        │                                      │
        └──────────────────┬───────────────────┘
                           ▼
هندسة الخصائص الزمنية
src/features/build_temporal_features.py
src/features/temporal_features.py
                           │
                           ▼
data/features/
├─ temporal_train_features.parquet
└─ temporal_test_features.parquet

data/artifacts/
├─ course_history_state.pkl
└─ category_levels.json   ← ينشأ فعليًا عند التدريب
                           │
                           ▼
عقد الخصائص
src/features/feature_contract.py
                           │
             ┌─────────────┼─────────────────┐
             ▼             ▼                 ▼
      التدريب الرسمي    تقييم baseline     التجارب
      train_models.py   evaluate_plan_gpa  experiment_degree_points.py
             │             │                 │
             ▼             ▼                 ▼
          models/      data/evaluation/   data/evaluation/experiments/
             │             │                 │
             └──────┬──────┴────────┬────────┘
                    ▼               ▼
             تحليل الأخطاء       تقارير بشرية
             analyze_model_errors reports/
                    │
                    ▼
             محرك ترشيح الخطط
             src/recommendation.py
                    │
                    ▼
        [الخطوة الحالية] backtesting للخطط البديلة
```

## 0. تعريف المسارات المركزي

كل مسارات الملفات معرفة في:

```text
src/paths.py
```

أي سكربت جديد يجب أن يستخدم ثوابت `paths.py` بدل كتابة مسار يدوي داخله.

## 1. البيانات الخام

المجلد:

```text
data/raw/
```

### الملفات المستخدمة حاليًا

| الملف | المحتوى | أول سكربت يقرأه |
|---|---|---|
| `v_crg_student_course_raw.parquet` | تسجيلات المقررات، النتيجة، العلامة والنقاط | `clean_student_course.py` و`build_registration_roster.py` |
| `v_add_student_degree_status.parquet` | حالة الطالب وملخص الفصل والتراكمات | `clean_student_status.py` |
| `v_acd_degree_course.parquet` | مقررات الخطط وأنواع المتطلبات والساعات | `clean_degree_course.py` |
| `v_add_academic_info.parquet` | معدل ونوع الشهادة قبل الجامعة | `clean_student_diploma.py` |
| `v_acs_grade.parquet` | جدول تحويل العلامة إلى grade وpoints | `evaluate_plan_gpa.py` و`recommendation.py` |

### ملفات معرفة للمراحل القادمة ولم تدخل المسار بعد

| الملف | الاستخدام المخطط |
|---|---|
| `v_crg_std_cor_temp_request.parquet` | طلبات أو تسجيلات المقررات المؤقتة |
| `v_sch_course_offers.parquet` | المقررات والشعب المطروحة في الفصل |
| `v_cor_course_prerequisite.parquet` | المتطلبات السابقة للمقررات |

هذه الملفات الثلاثة يفترض أن تدخل لاحقًا في بناء **قائمة المواد القانونية
الجاهزة** قبل إرسالها إلى محرك الترشيح.

## 2. تنظيف تسجيلات المقررات

```text
المدخل الأساسي:
data/raw/v_crg_student_course_raw.parquet

السكربت:
src/data/clean_student_course.py

المخرج الأولي المستقل:
data/clean/student_course_pre_common_v2.parquet

المخرج النهائي بعد تقاطع الطلاب:
data/clean/student_course_v2.parquet
```

أهم العمليات: الاحتفاظ بتسجيلات `R/E` والنتائج `P/F/FE/FA` بعد 2019، تنظيف
المعرفات والأنواع، إزالة السجلات غير الداخلة في GPA، وحساب `attempt_number`.

## 3. تنظيف حالة الطالب

```text
المدخل الأساسي:
data/raw/v_add_student_degree_status.parquet

السكربت:
src/data/clean_student_status.py

المخرج الأولي المستقل:
data/clean/student_status_pre_common_v2.parquet

المخرج النهائي بعد تقاطع الطلاب:
data/clean/student_status_v2.parquet
```

أهم العمليات: فلترة الحالة ونمط الدراسة، تنظيف تراكمات الطالب، حساب
`last_enrolled_gpa` و`observed_gap_semesters`، والاحتفاظ بصف واحد لكل حالة
طالب وفصل.

### ملاحظة إعادة البناء من الصفر

ينظف `clean_student_course.py` و`clean_student_status.py` المصدرين باستقلال،
ويكتبان `student_course_pre_common_v2.parquet` و`student_status_pre_common_v2.parquet`.
بعدهما تشغّل `src/data/filter_common_students.py` تقاطع `student_id` فقط وتكتب
`student_course_v2.parquet` و`student_status_v2.parquet` للاستهلاك اللاحق.
تُحفظ جميع صفوف الطالب المشترك حتى لو اختلف `degree_id` أو `part_id`.

## 4. تنظيف مقررات الخطة

```text
المدخل:
data/raw/v_acd_degree_course.parquet

السكربت:
src/data/clean_degree_course.py

المخرج:
data/clean/degree_course.parquet
```

يحفظ خصائص المقرر ضمن الاختصاص: نوع المقرر، نوع المتطلب، ترتيب السنة والفصل،
ساعات المقرر وإجمالي ساعات الخطة.

## 5. إثراء تسجيل المقرر

```text
المدخلات:
data/clean/student_course.parquet
data/clean/student_status.parquet
data/clean/degree_course.parquet

السكربت:
src/data/build_student_course_enriched.py

المخرج:
data/clean/student_course_enriched.parquet
```

المفاتيح:

- حالة الطالب: `[student_id, degree_id, part_id]`.
- خصائص المقرر في الخطة: `[degree_id, course_id]`.

## 6. تنظيف الشهادة ودمجها

```text
المدخلات:
data/raw/v_add_academic_info.parquet
data/clean/student_course_enriched.parquet

السكربت:
src/data/clean_student_diploma.py

المخرجات:
data/clean/student_diploma.parquet
data/merged/student_course_enriched_with_diploma.parquet
```

يبقي `student_id`, `diploma_gpa`, `diploma_type_id`، ويحذف نوع الشهادة
المفقود، ويجمع الأنواع النادرة في `55.111`، ثم يدمجها مع تسجيلات الطالب.

## 7. تنظيف القيم الشاذة

```text
المدخل:
data/merged/student_course_enriched_with_diploma.parquet

السكربت:
src/data/clean_outliers.py

المخرجات:
data/merged/student_course_enriched_without_outliers.parquet
data/merged/outlier_students.parquet
```

إذا ظهر للطالب سجل مخالف لقواعد الفصل أو المقرر، يحذف الطالب كاملًا من بيانات
النمذجة ويحفظ سبب الحذف داخل ملف audit.

الملف الذي تعتمد عليه كل المراحل اللاحقة هو:

```text
data/merged/student_course_enriched_without_outliers.parquet
```

## 8. التقسيم الزمني لصفوف الأهداف

```text
المدخل:
data/merged/student_course_enriched_without_outliers.parquet

السكربت:
src/data/build_temporal_split.py

المخرجات:
data/temporal/temporal_train.parquet   # 20201–20243
data/temporal/temporal_test.parquet    # 20251–20252
```

الفصل `20253` غير المكتمل مستبعد. لا يوجد shuffle، و2025 يبقى اختبارًا زمنيًا.

## 9. بناء roster الحمل الفصلي

هذه مرحلة موازية للتقسيم السابق، لأنها تحتاج كل تسجيلات `R/E` وليس النتائج
النهائية فقط.

```text
المدخلات:
data/raw/v_crg_student_course_raw.parquet
data/clean/student_status.parquet
data/clean/degree_course.parquet
data/merged/outlier_students.parquet

السكربت:
src/data/build_registration_roster.py

المخرجات:
data/clean/registration_roster.parquet
data/temporal/temporal_train_roster.parquet
data/temporal/temporal_test_roster.parquet
```

الـroster يتضمن المنسحب وغير المكتمل لأنهما كانا جزءًا من حمل الفصل. أما
`temporal_train/test.parquet` فيمثلان الصفوف التي تملك هدفًا قابلًا للتدريب.

## 10. هندسة الخصائص الزمنية

```text
المدخلات:
data/temporal/temporal_train.parquet
data/temporal/temporal_test.parquet
data/temporal/temporal_train_roster.parquet
data/temporal/temporal_test_roster.parquet

مشغّل المرحلة:
src/features/build_temporal_features.py

منطق الخصائص:
src/features/temporal_features.py

المخرجات:
data/features/temporal_train_features.parquet
data/features/temporal_test_features.parquet
data/artifacts/course_history_state.pkl
```

مجموعات الخصائص الناتجة:

- تاريخ الطالب السابق وتراكماته.
- `gpa_prev_1`, `gpa_prev_2`, `gpa_trend_delta`.
- تاريخ وصعوبة المقرر من الفصول السابقة فقط.
- خصائص حمل الخطة `plan_*`.
- خصائص المواد المرافقة leave-one-out باسم `peer_*`.
- `part_semester` وهدف `is_fail`.

## 11. عقد الخصائص الرسمي

```text
src/features/feature_contract.py
```

هذا الملف لا ينتج parquet. وظيفته تحديد ما يدخل المودل:

- `NUMERIC_FEATURES`.
- `CATEGORICAL_FEATURES`.
- `MODEL_FEATURES`، وعددها الحالي 47.
- `TARGET_GRADE = final_mark`.
- `TARGET_FAIL = is_fail`.
- أعمدة التسرب والمعرفات الخام المستبعدة.
- أوزان التدريب الزمنية.

أي تعديل على خصائص baseline يبدأ من هذا الملف، وليس من `train_models.py`.

## 12. التدريب الرسمي

```text
المدخلات:
data/features/temporal_train_features.parquet
data/features/temporal_test_features.parquet

عقد الخصائص:
src/features/feature_contract.py

السكربت:
src/modeling/train_models.py

المخرجات:
models/grade_regressor.txt
models/fail_risk_classifier.txt
models/model_metadata.json
data/artifacts/category_levels.json
```

المودلات:

- GradeRegressor: يتوقع `final_mark`.
- FailRiskClassifier: يتوقع `is_fail = final_mark < 50`.

الضبط الزمني:

```text
تدريب حتى 2022 → validation 2023
تدريب حتى 2023 → validation 2024
تدريب نهائي 2020–2024 → test 2025
```

`model_metadata.json` هو أول ملف تفتحه لمعرفة إعدادات التدريب، أفضل iterations،
قائمة الخصائص، والنتائج.

## 13. تقييم GPA للخطة الفعلية

```text
المدخلات:
data/features/temporal_test_features.parquet
models/grade_regressor.txt
data/artifacts/category_levels.json
data/raw/v_acs_grade.parquet

السكربت:
src/evaluate_plan_gpa.py

المخرجات:
data/evaluation/plan_gpa_course_predictions_2025.parquet
data/evaluation/plan_gpa_evaluation_2025.parquet
data/evaluation/plan_gpa_metrics_2025.json
```

الحساب:

```text
Plan GPA = Σ(course_credits × points) / Σ(course_credits)
```

هذا تقييم للخطة التي سجلها الطالب فعلًا، وليس تقييمًا لقدرة النظام على اختيار
خطة بديلة أفضل.

## 14. تحليل الأخطاء

```text
المدخلات:
temporal train/test features
grade_regressor.txt
model_metadata.json
category_levels.json
v_acs_grade.parquet

السكربت:
src/analyze_model_errors.py

المخرجات:
data/evaluation/error_analysis/model_error_by_year.parquet
data/evaluation/error_analysis/model_error_by_degree.parquet
data/evaluation/error_analysis/model_error_by_year_and_degree.parquet
data/evaluation/error_analysis/plan_error_segments.parquet
data/evaluation/error_analysis/course_error_segments.parquet
data/evaluation/error_analysis/grade_model_shap_importance.parquet
data/evaluation/error_analysis/grade_model_shap_families.parquet
data/evaluation/error_analysis/analysis_summary.json

التقرير:
reports/model_error_analysis.md
```

## 15. تجربة الاختصاص وExpected Points

ملف التشغيل:

```text
src/experiment_degree_points.py
```

تفصيل الكود:

| الملف | المسؤولية |
|---|---|
| `src/experiments/degree_points.py` | تعريف `FOLDS` و`VARIANTS` واختيار الفائز وحفظ النتائج |
| `src/experiments/specialty_history.py` | خصائص تاريخ الاختصاص والاختصاص × نوع المتطلب |
| `src/experiments/modeling.py` | تجهيز X، اختيار target، الوزن، التدريب ومقاييس الخطة |

المدخلات الأساسية:

```text
data/features/temporal_train_features.parquet
data/features/temporal_test_features.parquet
models/model_metadata.json
data/raw/v_acs_grade.parquet
```

خصائص النسخة الفائزة:

```text
MODEL_FEATURES الرسمية: 47
+ SPECIALTY_HISTORY_FEATURES: 10
= 57 خاصية

target = points
sample_weight = temporal_weight  # النسخة المختارة حالياً: degree_history_points_temporal
```

المخرجات التفصيلية:

```text
data/evaluation/experiments/degree_points/
├─ validation_results.parquet
├─ validation_summary.parquet
├─ selected_holdout_course_predictions.parquet
├─ selected_holdout_plan_predictions.parquet
├─ selected_holdout_by_degree.parquet
└─ experiment_metadata.json
```

مخرجات المودل:

```text
models/experiments/degree_points/
├─ selected_model.txt
└─ selected_category_levels.json
```

التقارير:

```text
reports/degree_points_experiment.md
reports/model_improvement_table.md
```

`experiment_metadata.json` يحتوي كل `VARIANTS`، والنسخة الفائزة، وقائمة
خصائصها الرقمية والتصنيفية كاملة.

## 16. محرك ترشيح الخطط الحالي

```text
الكود:
src/recommendation.py

الأدوات المساندة:
src/grade_scale.py
src/features/temporal_features.py
src/features/feature_contract.py
```

المدخلات وقت الاستخدام:

- student snapshot قبل الفصل.
- قائمة مواد قانونية جاهزة.
- `part_id`.
- ساعات محددة نطابقها بالضبط، أو مجال نقبل جميع الخطط ضمنه شاملاً طرفيه، مع عدد مواد متغير.
- معدل الطالب الحالي: يقبل كل خطة معدلها المتوقع أعلى منه، دون حد استبعاد للرسوب.

الملفات التي يحملها:

```text
models/experiments/degree_points/selected_model.txt
models/experiments/degree_points/selected_category_levels.json
models/fail_risk_classifier.txt
data/artifacts/category_levels.json
data/artifacts/course_history_state.pkl
data/features/temporal_train_features.parquet
data/evaluation/experiments/degree_points/experiment_metadata.json
```

المحرك يستخدم Expected Points مباشرة، ويحسب خصائص حمل كل خطة على دفعات.
التشغيل: `python -m src.recommend_local`. تفاصيل الإدخال والحفظ والاختبارات
في [LOCAL_RECOMMENDATION.md](LOCAL_RECOMMENDATION.md).

## 17. المسار القادم: بناء المواد القانونية وBacktesting

```text
v_sch_course_offers.parquet
v_cor_course_prerequisite.parquet
v_crg_std_cor_temp_request.parquet
student snapshot + degree plan
                    │
                    ▼
بناء قائمة المواد القانونية والجاهزة
                    │
                    ▼
src/recommendation.py
                    │
                    ▼
خطط بديلة مرتبة
                    │
                    ▼
مقارنة الخطة المقترحة بالخطة الفعلية تاريخيًا
```

التوليد والتقييم المحليان جاهزان من قائمة مواد معتمدة بصيغة JSON أو Parquet.
ربط جهة الشركة وتحديد معنى صفوف الفصل الفارغ وتقييم سياسة الترشيح على بيانات
فعلية ما زالت خطوات لاحقة؛ لن نبني قواعد أهلية بديلة عن القائمة المعتمدة.

## 18. ملفات المتابعة والاختبارات

| الملف | الوظيفة |
|---|---|
| `START_HERE.md` | نقطة الدخول والتنقل السريع |
| `PROJECT_TRACKER.md` | ما أُنجز وما بقي |
| `PIPELINE_README.md` | خط الملفات والتنفيذ الكامل |
| `Readme.md` | شرح القرارات والمنهجية |
| `src/project_status.py` | فحص وجود artifacts وعرض المقاييس الحالية |
| `tests/test_temporal_features.py` | اختبارات منع التسرب والخصائص الزمنية |
| `tests/test_recommendation.py` | اختبارات تعداد وترتيب الخطط |
| `tests/test_plan_gpa_evaluation.py` | اختبار معادلة GPA |
| `tests/test_degree_points_experiment.py` | اختبارات خصائص الاختصاص ووزن الساعات |

تشغيل الحالة والاختبارات:

```powershell
python src\project_status.py
python -m unittest discover -s tests -v
```

## 19. ترتيب التشغيل الحالي

من جذر المشروع، وبعد معالجة عوائق المصدر بقرار منفصل، ترتيب بناء قسمَي البيانات والخصائص V2 هو:

```powershell
python -m src.data.clean_student_course
python -m src.data.clean_student_status
python -m src.data.filter_common_students
python -m src.data.clean_degree_course
python -m src.data.build_student_course_enriched
python -m src.data.clean_student_diploma
python -m src.data.clean_outliers
python -m src.data.build_temporal_split
python -m src.data.build_registration_roster
python -m src.features.build_temporal_features
```

تنتهي سلسلة V2 هنا. الأوامر التالية مستقلة وتقرأ ملفات V1 الحالية؛ لا تدرّب على مخرجات V2 الجديدة:

```powershell
python src\modeling\train_models.py
python src\evaluate_plan_gpa.py
python src\analyze_model_errors.py
python src\experiment_degree_points.py
python -m unittest discover -s tests -v
```

## 20. أين تحفظ الأشياء؟

| النوع | المسار | يدخل Git؟ |
|---|---|---:|
| البيانات الخام والمنظفة | `data/raw`, `data/clean`, `data/merged` | لا |
| التقسيم والخصائص | `data/temporal`, `data/features`, `data/artifacts` | لا |
| نتائج التقييم التفصيلية | `data/evaluation` | لا |
| المودلات الرسمية | `models/` | نعم حاليًا |
| مودلات التجارب | `models/experiments/` | نعم حاليًا |
| التقارير المقروءة | `reports/` | نعم |
| كود التنفيذ | `src/` | نعم |
| الاختبارات | `tests/` | نعم |

مجلد `data/` كامل موجود في `.gitignore`. لذلك عند مشاركة المشروع عبر GitHub،
تظهر الأكواد والمودلات والتقارير، لكن ملفات parquet والنتائج التفصيلية تبقى
محلية.
