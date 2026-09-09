# ابدأ من هنا — Academic Advisor

هذا هو **مدخل المشروع الوحيد** عند العودة إليه أو فتح محادثة جديدة. لا تبدأ
بقراءة السكربتات عشوائيًا؛ استخدم الخريطة التالية للوصول إلى المرحلة التي
تهمك.

## أين وصل المشروع الآن؟

المشروع موجود بعد تدريب المودلات وتقييم توقع GPA للخطة الفعلية، وقبل اعتماد
سياسة ترشيح الخطط البديلة:

```text
تنظيف ودمج
  → تقسيم زمني
  → roster كامل
  → خصائص زمنية آمنة
  → تدريب Grade + Fail
  → تقييم الخطة الفعلية
  → تحليل الأخطاء
  → تجربة Expected Points والاختصاص
  → [نحن هنا] backtesting لترتيب الخطط البديلة
```

الوضع الحالي للمودلات:

- **رسمي حاليًا:** `GradeRegressor` و`FailRiskClassifier`.
- **مرشح مثبت تجريبيًا:** `ExpectedPointsRegressor` مع تاريخ الاختصاص ووزن
  الساعات؛ حسن Plan GPA MAE من `0.3764` إلى `0.3450` على 2025.
- **غير منفذ بعد:** دمج Expected Points داخل ترتيب الخطط ثم backtesting على
  الخطط البديلة.

## كيف أتنقل في المشروع؟

| أريد أن أعرف | الملف الذي أفتحه |
|---|---|
| ما مسار كل ملف من raw حتى النتائج؟ | `PIPELINE_README.md` |
| أين وصلنا وما الخطوة التالية؟ | `PROJECT_TRACKER.md` |
| شرح المشروع من البيانات حتى الترشيح | `Readme.md` |
| ما الخصائص الرسمية التي تدخل المودل؟ | `src/feature_contract.py` |
| كيف حُسبت الخصائص الزمنية؟ | `src/temporal_features.py` |
| كيف تم تدريب المودلين الرسميين؟ | `src/train_models.py` |
| كيف تُبنى وتُرتب الخطط؟ | `src/recommendation.py` |
| ما التجارب التي جُربت ونتيجة كل إضافة؟ | `reports/model_improvement_table.md` |
| لماذا الخطأ مرتفع وأين؟ | `reports/model_error_analysis.md` |
| تفاصيل تجربة الاختصاص والنقاط | `reports/degree_points_experiment.md` |

لعرض الحالة آليًا:

```powershell
python src\project_status.py
```

## المسار الرسمي للتدريب

```text
data/temporal/temporal_train.parquet
data/temporal/temporal_test.parquet
                │
                ▼
src/build_temporal_features.py
                │
                ├─ data/features/temporal_train_features.parquet
                ├─ data/features/temporal_test_features.parquet
                └─ data/artifacts/course_history_state.pkl
                │
                ▼
src/train_models.py
                │
                ├─ models/grade_regressor.txt
                ├─ models/fail_risk_classifier.txt
                └─ models/model_metadata.json
```

عقد خصائص التدريب الرسمي موجود كاملًا في `src/feature_contract.py`:

- `NUMERIC_FEATURES`: الخصائص الرقمية.
- `CATEGORICAL_FEATURES`: الخصائص التصنيفية.
- `MODEL_FEATURES`: القائمة النهائية التي تدخل `X`.
- `TARGET_GRADE = final_mark`.
- `TARGET_FAIL = is_fail`.
- `training_weights`: وزن `0.25` لما قبل 2022 و`1.0` للباقي.

لتشغيل التدريب الرسمي فقط:

```powershell
python src\train_models.py
```

## مسار تجربة Expected Points والاختصاص

ملف التشغيل الذي تستدعيه قصير ومقصود أن يبقى كذلك:

```powershell
python src\experiment_degree_points.py
```

ثم ينتقل التنفيذ إلى وحدات منفصلة:

```text
src/experiment_degree_points.py
    └─ مدخل CLI فقط

src/experiments/degree_points.py
    ├─ FOLDS: التقسيمات الزمنية
    ├─ VARIANTS: تعريف كل نسخة مجربة
    ├─ اختيار النسخة الفائزة
    └─ حفظ المخرجات

src/experiments/specialty_history.py
    ├─ خصائص تاريخ الاختصاص
    ├─ خصائص الاختصاص × نوع المتطلب
    ├─ smoothing
    └─ منع تسرب الفصل الحالي وتجميد 2025

src/experiments/modeling.py
    ├─ تجهيز X والتصنيفات
    ├─ اختيار target: mark أو points
    ├─ sample weights
    ├─ تدريب LightGBM
    └─ مقاييس المادة والخطة
```

النسخة الفائزة معرفة ضمن `VARIANTS` بهذه الأبعاد:

```text
feature_profile = degree_history
target          = points
credit_weighted = true
```

خصائصها هي خصائص `MODEL_FEATURES` الرسمية مضافًا إليها القائمة
`SPECIALTY_HISTORY_FEATURES` الموجودة في
`src/experiments/specialty_history.py`.

## سجل التجارب ونتائجها

| التجربة | ملف التشغيل | تعريف الخصائص/النسخ | النتائج المحلية التفصيلية | التقرير المقروء | المودل |
|---|---|---|---|---|---|
| Baseline Grade + Fail | `src/train_models.py` | `src/feature_contract.py` | `models/model_metadata.json` | قسم التدريب في `Readme.md` | `models/grade_regressor.txt`, `models/fail_risk_classifier.txt` |
| Plan GPA baseline | `src/evaluate_plan_gpa.py` | خصائص baseline | `data/evaluation/plan_gpa_*` | `reports/model_error_analysis.md` | يستخدم GradeRegressor |
| تحليل السنة والاختصاص وSHAP | `src/analyze_model_errors.py` | خصائص baseline | `data/evaluation/error_analysis/` | `reports/model_error_analysis.md` | يستخدم GradeRegressor |
| Degree + Direct Points | `src/experiment_degree_points.py` | `src/experiments/degree_points.py` و`specialty_history.py` | `data/evaluation/experiments/degree_points/` | `reports/degree_points_experiment.md` و`model_improvement_table.md` | `models/experiments/degree_points/selected_model.txt` |

مهم: مجلد `data/` موجود في `.gitignore`، لذلك النتائج التفصيلية داخله محلية
على الجهاز ولا تظهر بعد clone من GitHub. التقارير الملخصة والمودلات موجودة
داخل Git.

## أين أجد نتيجة كل نسخة من التجربة؟

داخل:

```text
data/evaluation/experiments/degree_points/
```

| الملف | محتواه |
|---|---|
| `validation_results.parquet` | صف لكل نسخة ولكل سنة validation: 2023 و2024 |
| `validation_summary.parquet` | متوسط كل نسخة وترتيبها والتحسن عن baseline |
| `selected_holdout_course_predictions.parquet` | توقع النقاط لكل مادة في 2025 |
| `selected_holdout_plan_predictions.parquet` | GPA الفعلي والمتوقع لكل خطة في 2025 |
| `selected_holdout_by_degree.parquet` | النتيجة حسب الاختصاص |
| `experiment_metadata.json` | كل الـvariants، النسخة الفائزة، قائمة خصائصها كاملة، المقاييس والمسارات |

للقراءة السريعة دون فتح parquet استخدم:

- `reports/model_improvement_table.md`: كل إضافة وما مقدار تحسينها.
- `reports/degree_points_experiment.md`: تفسير التجربة والقرار.

## قاعدة إضافة تجربة جديدة

أي تجربة قادمة تتبع نفس التنظيم:

1. تعريف النسخ والـfolds في `src/experiments/<experiment_name>.py`.
2. إعادة استخدام `src/experiments/modeling.py` بدل نسخ كود التدريب والمقاييس.
3. وضع الخصائص الجديدة فقط في وحدة مستقلة داخل `src/experiments/`.
4. حفظ النتائج التفصيلية في `data/evaluation/experiments/<experiment_name>/`.
5. حفظ المودل في `models/experiments/<experiment_name>/`.
6. كتابة خلاصة بشرية في `reports/<experiment_name>.md`.
7. إضافة صف إلى جدول «سجل التجارب» في هذا الملف.

بهذا يبقى لكل تجربة مكان واحد لتعريفها، ومكان واحد لنتائجها، ولا يعود سكربت
التشغيل ملفًا طويلًا يكرر التدريب والتحليل.
