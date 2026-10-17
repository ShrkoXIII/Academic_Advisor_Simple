# تجربة إزالة اعتماد `attempt_sum`

## A. الهدف

قياس أثر إزالة الاعتماد التاريخي على `attempt_sum` لأن واجهة الجامعة لا توفره، دون تخمينه أو إضافة ميزات بديلة. النتائج التالية محسوبة من ملفات التنفيذ المحفوظة، وليست اقتراحًا لاعتماد النماذج في الإنتاج.

## B. تدقيق الاعتماد

المسار الرسمي: outcomes النهائية → `attempt_number × temporal_weight` → `attempt_sum` في الحالة التاريخية → `course_history_avg_attempt` → المتوسطان الموزونان لسياق الخطة والمواد الأخرى. يتطلب مسار تحديث Frozen History الرسمي الحقل نفسه؛ حذف أعمدة التدريب وحده لا يزيل هذا الاعتماد.

| المصدر الفعلي | الاعتماد |
| --- | --- |
| [src/features/temporal_features.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/features/temporal_features.py:128>) | تجميع attempt_sum؛ يبقى retake_sum مستقلاً |
| [src/features/temporal_features.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/features/temporal_features.py:184>) | المتوسط التاريخي من attempt_sum |
| [src/features/temporal_features.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/features/temporal_features.py:374>) | اشتقاق plan/peer average attempt |
| [src/features/feature_contract.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/features/feature_contract.py:56>) | عقد الميزات الرسمي |
| [src/experiments/course_only_core.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/experiments/course_only_core.py:21>) | استبعاد سياق الخطة من shortlist مع إبقاء historical average attempt |
| [src/recommendation/history_update.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/recommendation/history_update.py:36>) | عقد delta الرسمي ما زال يتطلب attempt_sum |
| [src/features/frozen_history.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/features/frozen_history.py:49>) | إدارة الحزم والحدود الزمنية الرسمية لم تتغير |
| [src/features/build_temporal_features.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/features/build_temporal_features.py:36>) | بناء الجداول الزمنية الرسمية؛ لم يُعَد بناؤها |
| [src/modeling/train_models.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/modeling/train_models.py:231>) | إعادة استخدام تدريب LightGBM الرسمي |
| [src/experiments/course_only_training.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/experiments/course_only_training.py:25>) | مسار تدريب shortlist الرسمي؛ تُقرأ إعداداته المؤرشفة |
| [src/evaluation/evaluate_plan_gpa.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/evaluation/evaluate_plan_gpa.py:78>) | تجميع GPA للخطة المرصودة بوحدة الساعات نفسها |
| [src/recommendation/two_stage_engine.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/recommendation/two_stage_engine.py:173>) | الاستدلال الرسمي للمرحلة الثانية لم يتغير |
| [scripts/experiments/attempt_sum_removal/history.py](<D:/AI/Real projects/Academic_Advisor_Simple/scripts/experiments/attempt_sum_removal/history.py:38>) | حالة منفصلة بخمسة مجاميع |

المحذوف فقط: `course_history_avg_attempt`، `plan_credit_weighted_avg_attempt`، `peer_credit_weighted_avg_attempt`. يبقى `attempt_number` الخاص بالمرشح، و`course_history_retake_rate`، و`retake_sum`. `retake_count` يحسب محاولات الإعادة كأحداث `attempt_number > 1` في البيانات المحلية؛ ليس بديلًا لمجموع المحاولات.

## C. العزل

تم التحقق من 7198 ملفًا محميًا؛ `unchanged=True`. يشمل ذلك العقود الرسمية والبيانات والنماذج وManifest وFrozen History وGraphify. الاستثناءات هي مساحات التجربة المحددة وملفات التشغيل المؤقتة فقط.

الأدلة: [attempt_sum_removal](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/experiments/attempt_sum_removal>)؛ النماذج: [attempt_sum_removal](<D:/AI/Real projects/Academic_Advisor_Simple/models/experiments/attempt_sum_removal>). تعيد `protected_before.json` و`protection.json` توثيق مقارنة SHA-256.

## D. إعداد التدريب وإعادة الإنتاج

Dataset: `V2`. ينتهي التدريب في `20243`، والتقييم على `20251` و`20252`. هذه بيانات 2025 سبق فحصها؛ الاختبار retrospective وليس اختبارًا أعمى جديدًا. فواصل التحقق: التدريب حتى 2022 ثم 2023، والتدريب حتى 2023 ثم 2024. الهدف `final_mark` و`is_fail = final_mark < 50`؛ وزن الصف قبل 2022 هو `0.25` وبعد ذلك `1.0`.

تعريف الوزن: [src/modeling/training_config.py](<D:/AI/Real projects/Academic_Advisor_Simple/src/modeling/training_config.py:10>). نفس الصفوف وترتيبها، وتحويل الفئات، وGradeScale، والأهداف والأوزان بين الطرفين. لا retuning ولا early stopping: عدد جولات كل fold مأخوذ من baseline المختار نفسه، والجولات النهائية ثابتة من metadata.

```json
{
  "created_utc": "2026-10-17T09:45:16.824335+00:00",
  "rows": {
    "train": 356816,
    "test": 67536,
    "train_fingerprint": "eb85d01ecf9a1d3a5b69b8849d8950ff031a222992c3585a8b587afa41b8faee",
    "test_fingerprint": "b901d7bf09d2950e61d8e99df6ddb2cf11f72fa5b6fa6c946d00d9012dc80799"
  },
  "input_sha256": {
    "data\\features\\temporal_train_features_v2.parquet": "026faac5933709c0903dac1b0ea2ca88be71d55c1bb6f805eb265d0f4cbe204f",
    "data\\features\\temporal_test_features_v2.parquet": "6d2c8dd0f8aa44d68812d66a21480cc328ca51beb482c0431c3d304c1a14bf05"
  },
  "python": "3.11.5",
  "lightgbm": "4.7.0",
  "pandas": "3.0.5",
  "numpy": "2.4.6",
  "threads": 4,
  "retuned": false
}
```

| العائلة | grade rounds | fail rounds | ميزات baseline | ميزات reduced |
| --- | --- | --- | --- | --- |
| stage2 | 114 | 112 | 47 | 44 |
| stage1 | 125 | 85 | 33 | 32 |

القيم أعلاه مستخرجة من التنفيذ. معاملات LightGBM الفعلية وإثبات إعادة baseline:

### stage2

```json
{
  "effective_parameters": {
    "grade": {
      "bagging_fraction": 0.9,
      "bagging_freq": 1,
      "bagging_seed": 42,
      "data_random_seed": 42,
      "deterministic": true,
      "feature_fraction": 0.85,
      "feature_fraction_seed": 42,
      "force_col_wise": true,
      "lambda_l1": 0.2,
      "lambda_l2": 2.0,
      "learning_rate": 0.04,
      "max_bin": 255,
      "metric": "l1",
      "min_data_in_leaf": 100,
      "num_leaves": 63,
      "num_threads": 4,
      "objective": "regression",
      "seed": 42,
      "verbosity": -1
    },
    "fail": {
      "bagging_fraction": 0.9,
      "bagging_freq": 1,
      "bagging_seed": 42,
      "data_random_seed": 42,
      "deterministic": true,
      "feature_fraction": 0.9,
      "feature_fraction_seed": 42,
      "force_col_wise": true,
      "lambda_l1": 0.1,
      "lambda_l2": 1.0,
      "learning_rate": 0.04,
      "max_bin": 255,
      "metric": "binary_logloss",
      "min_data_in_leaf": 80,
      "num_leaves": 31,
      "num_threads": 4,
      "objective": "binary",
      "seed": 42,
      "verbosity": -1
    }
  },
  "saved_baseline_verification": {
    "grade": {
      "verified": true,
      "max_metric_difference": 0.0
    },
    "fail": {
      "verified": true,
      "max_metric_difference": 0.0
    }
  },
  "baseline_replica_max_prediction_difference": {
    "grade": 0.0,
    "fail": 0.0
  }
}
```

### stage1

```json
{
  "effective_parameters": {
    "grade": {
      "bagging_fraction": 0.85,
      "bagging_freq": 1,
      "bagging_seed": 42,
      "data_random_seed": 42,
      "deterministic": true,
      "feature_fraction": 0.8,
      "feature_fraction_seed": 42,
      "force_col_wise": true,
      "lambda_l1": 0.5,
      "lambda_l2": 4.0,
      "learning_rate": 0.04,
      "max_bin": 255,
      "metric": "l1",
      "min_data_in_leaf": 160,
      "num_leaves": 47,
      "num_threads": 4,
      "objective": "regression",
      "seed": 42,
      "verbosity": -1
    },
    "fail": {
      "bagging_fraction": 0.9,
      "bagging_freq": 1,
      "bagging_seed": 42,
      "data_random_seed": 42,
      "deterministic": true,
      "feature_fraction": 0.85,
      "feature_fraction_seed": 42,
      "force_col_wise": true,
      "lambda_l1": 0.2,
      "lambda_l2": 2.0,
      "learning_rate": 0.04,
      "max_bin": 255,
      "metric": "binary_logloss",
      "min_data_in_leaf": 100,
      "num_leaves": 63,
      "num_threads": 4,
      "objective": "binary",
      "seed": 42,
      "verbosity": -1
    }
  },
  "saved_baseline_verification": {
    "grade": {
      "verified": true,
      "max_metric_difference": 0.0
    },
    "fail": {
      "verified": true,
      "max_metric_difference": 0.0
    }
  },
  "baseline_replica_max_prediction_difference": {
    "grade": 0.0,
    "fail": 0.0
  }
}
```

تحقق زمني محفوظ؛ لا تُستخدم نتائجه لاختيار إعداد جديد:

| العائلة | fold | الطرف | train rows | valid rows | rounds | Grade MAE | Fail log loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stage2 | train_through_2022_validate_2023 | baseline | 205369 | 77014 | {"grade": 122, "fail": 128} | 9.2671349 | 0.24694937 |
| stage2 | train_through_2022_validate_2023 | reduced | 205369 | 77014 | {"grade": 122, "fail": 128} | 9.2738043 | 0.24695766 |
| stage2 | train_through_2023_validate_2024 | baseline | 282383 | 74433 | {"grade": 105, "fail": 97} | 9.7776792 | 0.20768366 |
| stage2 | train_through_2023_validate_2024 | reduced | 282383 | 74433 | {"grade": 105, "fail": 97} | 9.7703962 | 0.20806049 |
| stage1 | train_through_2022_validate_2023 | baseline | 205369 | 77014 | {"grade": 143, "fail": 95} | 9.2569545 | 0.24693142 |
| stage1 | train_through_2022_validate_2023 | reduced | 205369 | 77014 | {"grade": 143, "fail": 95} | 9.2742615 | 0.2469211 |
| stage1 | train_through_2023_validate_2024 | baseline | 282383 | 74433 | {"grade": 107, "fail": 75} | 9.7547735 | 0.20768279 |
| stage1 | train_through_2023_validate_2024 | reduced | 282383 | 74433 | {"grade": 107, "fail": 75} | 9.7746833 | 0.20800506 |

## E. توافق Frozen History

الحالة التجريبية تحفظ `effective_support, raw_count, mark_sum, fail_sum, retake_sum` فقط. أُعيد تشغيل جميع فصول train/test باستخدام roster الأصلي. تقارن 6 ميزات تاريخية و12 ميزة سياق متبقية، مع تطابق missingness؛ التسامح العددي `rtol=1e-12, atol=1e-10`. مصفوفات float32 والفئات وأسماء الأعمدة وترتيبها وأنواعها تطابق النسخة المحفوظة تطابقًا تامًا.

| split | rows | roster rows | features replayed | max diff | full exact | full cols | shortlist exact | shortlist cols | cutoff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | 356816 | 388978 | 18 | 0 | True | 44 | True | 32 | 20243 |
| test | 67536 | 74814 | 18 | 0 | True | 44 | True | 32 | 20252 |

```json
{
  "snapshots": {
    "20243": {
      "path": "D:\\AI\\Real projects\\Academic_Advisor_Simple\\data\\evaluation\\experiments\\attempt_sum_removal\\reduced_history\\state_as_of_20243.pkl",
      "as_of_part": 20243,
      "global_sums": {
        "effective_support": 258532.25,
        "raw_count": 356816.0,
        "mark_sum": 18433972.0,
        "fail_sum": 21132.75,
        "retake_sum": 30403.25
      },
      "table_rows": {
        "1": 2428,
        "2": 823,
        "3": 383,
        "4": 95,
        "5": 23
      },
      "sum_columns": [
        "effective_support",
        "raw_count",
        "mark_sum",
        "fail_sum",
        "retake_sum"
      ]
    },
    "20251": {
      "path": "D:\\AI\\Real projects\\Academic_Advisor_Simple\\data\\evaluation\\experiments\\attempt_sum_removal\\reduced_history\\state_as_of_20251.pkl",
      "as_of_part": 20251,
      "global_sums": {
        "effective_support": 292940.25,
        "raw_count": 391224.0,
        "mark_sum": 20853784.0,
        "fail_sum": 24716.75,
        "retake_sum": 33368.25
      },
      "table_rows": {
        "1": 2592,
        "2": 856,
        "3": 412,
        "4": 104,
        "5": 24
      },
      "sum_columns": [
        "effective_support",
        "raw_count",
        "mark_sum",
        "fail_sum",
        "retake_sum"
      ]
    }
  },
  "delta_check": {
    "part": 20251,
    "rows": 34408,
    "passed": true,
    "aggregate_rows": 1771,
    "sums": [
      "effective_support",
      "raw_count",
      "mark_sum",
      "fail_sum",
      "retake_sum"
    ]
  }
}
```

يُحسب سياق الفصل قبل تحديث الحالة بنتائجه؛ الدلتا النهائية لـ20251 تقارن بمسار تحديث outcomes المحلية ثم تسمح بسياق 20252. التاريخ الرسمي ما زال يتطلب `attempt_sum` ولم يُستبدل بهذه الحالة. توافق local replay لا يثبت تعريفات API: دلالة `count` مقابل `students_count`، و`retake_count`، وfinalized/cutoff في واجهة الجامعة تبقى `UNVERIFIED` حتى مطابقتها مع الجهة الموردة.

## F. المقارنة العددية

الفرق دائمًا `reduced − baseline`. انخفاض مقاييس الخطأ/الخسارة أفضل؛ ارتفاع AUC ونسب within أفضل. `bias` موقّع ويُقرأ قربه من الصفر، وليس اتجاهه وحده. النسب within أعداد بين 0 و1. Course points تنتج من تحويل العلامة المتوقعة عبر GradeScale نفسه؛ ليست توقعًا احتماليًا مباشرًا لتوزيع النقاط.

### Full 47 → 44

| Metric | Official baseline | Reduced | Delta | الاتجاه |
| --- | --- | --- | --- | --- |
| grade_mae | 9.7076976 | 9.7293619 | 0.021664313 | تراجع وصفي |
| grade_rmse | 13.045276 | 13.076511 | 0.03123476 | تراجع وصفي |
| grade_within_5 | 0.34997631 | 0.34828832 | -0.0016879886 | تراجع وصفي |
| grade_within_10 | 0.62588842 | 0.62390429 | -0.001984127 | تراجع وصفي |
| grade_bias | 2.2651705 | 2.3224538 | 0.057283252 | أبعد عن الصفر |
| fail_pr_auc | 0.30510996 | 0.30575683 | 0.00064686504 | تحسن وصفي |
| fail_roc_auc | 0.80976257 | 0.80946493 | -0.00029764543 | تراجع وصفي |
| fail_brier | 0.081176685 | 0.081159413 | -1.7271797e-05 | تحسن وصفي |
| fail_log_loss | 0.27402279 | 0.27455617 | 0.00053337955 | تراجع وصفي |
| fail_calibration_error_10_bins | 0.021415814 | 0.022375846 | 0.00096003155 | تراجع وصفي |
| points_mae | 0.57602242 | 0.57715515 | 0.0011327292 | تراجع وصفي |
| points_rmse | 0.83902695 | 0.84089332 | 0.0018663772 | تراجع وصفي |
| points_bias | 0.17328166 | 0.17596911 | 0.0026874556 | أبعد عن الصفر |
| student_macro_grade_mae | 10.523208 | 10.540222 | 0.017014617 | تراجع وصفي |
| student_macro_points_mae | 0.61958306 | 0.62027451 | 0.00069144436 | تراجع وصفي |
| student_macro_plan_mae | 0.4658995 | 0.46757282 | 0.0016733169 | تراجع وصفي |
| plan_gpa_plans | 12713 | 12713 | 0 | تعادل |
| plan_gpa_mae | 0.4541994 | 0.45582521 | 0.0016258039 | تراجع وصفي |
| plan_gpa_credits_weighted_mae | 0.41690761 | 0.41885182 | 0.0019442041 | تراجع وصفي |
| plan_gpa_rmse | 0.63966967 | 0.64333691 | 0.003667247 | تراجع وصفي |
| plan_gpa_bias | 0.21376226 | 0.21722749 | 0.0034652315 | أبعد عن الصفر |
| plan_gpa_median_absolute_error | 0.30952381 | 0.3125 | 0.0029761905 | تراجع وصفي |
| plan_gpa_within_0_25 | 0.43955007 | 0.43663966 | -0.0029104067 | تراجع وصفي |
| plan_gpa_within_0_50 | 0.68378825 | 0.68166444 | -0.0021238103 | تراجع وصفي |
| plan_gpa_within_1_00 | 0.8951467 | 0.8943601 | -0.0007865964 | تراجع وصفي |

### Shortlist 33 → 32

| Metric | Official baseline | Reduced | Delta | الاتجاه |
| --- | --- | --- | --- | --- |
| grade_mae | 9.7180166 | 9.7331942 | 0.015177654 | تراجع وصفي |
| grade_rmse | 13.079372 | 13.082345 | 0.0029729539 | تراجع وصفي |
| grade_within_5 | 0.35067223 | 0.34978382 | -0.00088841507 | تراجع وصفي |
| grade_within_10 | 0.62448176 | 0.62474828 | 0.00026652452 | تحسن وصفي |
| grade_bias | 2.3676131 | 2.3090797 | -0.058533429 | أقرب للصفر |
| fail_pr_auc | 0.29913243 | 0.30666173 | 0.0075293014 | تحسن وصفي |
| fail_roc_auc | 0.80797108 | 0.80837526 | 0.00040417991 | تحسن وصفي |
| fail_brier | 0.081472778 | 0.081309807 | -0.00016297147 | تحسن وصفي |
| fail_log_loss | 0.27549502 | 0.27533203 | -0.00016298075 | تحسن وصفي |
| fail_calibration_error_10_bins | 0.022241706 | 0.023572979 | 0.0013312733 | تراجع وصفي |
| points_mae | 0.57679608 | 0.57708852 | 0.00029243663 | تراجع وصفي |
| points_rmse | 0.84121847 | 0.84022393 | -0.00099453676 | تحسن وصفي |
| points_bias | 0.17940062 | 0.17406642 | -0.0053341921 | أقرب للصفر |
| student_macro_grade_mae | 10.53128 | 10.552157 | 0.02087642 | تراجع وصفي |
| student_macro_points_mae | 0.62007721 | 0.62040079 | 0.00032358677 | تراجع وصفي |
| student_macro_plan_mae | 0.46696493 | 0.46740591 | 0.00044098013 | تراجع وصفي |
| plan_gpa_plans | 12713 | 12713 | 0 | تعادل |
| plan_gpa_mae | 0.45529488 | 0.45584771 | 0.00055283229 | تراجع وصفي |
| plan_gpa_credits_weighted_mae | 0.41806921 | 0.41886476 | 0.0007955523 | تراجع وصفي |
| plan_gpa_rmse | 0.64172842 | 0.64150245 | -0.00022596224 | تحسن وصفي |
| plan_gpa_bias | 0.22195126 | 0.21678109 | -0.0051701686 | أقرب للصفر |
| plan_gpa_median_absolute_error | 0.3125 | 0.3125 | 0 | تعادل |
| plan_gpa_within_0_25 | 0.4357744 | 0.4357744 | 0 | تعادل |
| plan_gpa_within_0_50 | 0.68284433 | 0.68158578 | -0.0012585542 | تراجع وصفي |
| plan_gpa_within_1_00 | 0.89522536 | 0.89569732 | 0.00047195784 | تحسن وصفي |

| العائلة | model | baseline train s | reduced train s | baseline predict s | reduced predict s | baseline bytes | reduced bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stage2 | grade | 5.8232637 | 6.7898209 | 0.3320074 | 0.3560021 | 697965 | 697906 |
| stage2 | fail | 4.543187 | 4.6456693 | 0.2387952 | 0.2916765 | 402573 | 403060 |
| stage1 | grade | 5.6461421 | 6.604574 | 0.4180743 | 0.5113053 | 578056 | 578464 |
| stage1 | fail | 6.0013927 | 4.4726657 | 0.2517559 | 0.3356481 | 598610 | 599017 |

وقت التدريب للـbaseline هو إعادة تدريب replica بالإعداد نفسه. زمن التنبؤ median لثلاث مرات بعد warm-up، على الصفوف والجهاز وعدد threads نفسه؛ جرت اختبارات المستودع بالتوازي مع بعض التدريب، لذلك الأزمنة وصفية وتتأثر بحمل الجهاز، ولا تثبت تفوقًا في الأداء أو زمن خدمة API أو ترتيب خطط مرشحة.

## G. الطلبة ذوو المعدل السابق المنخفض

الفئات الموجبة هي `(0,1]`، `(1,2]`، `(2,3]`، `(3,4]` و`(0,2]`. نفصل الصفر مع outcomes سابقة مرصودة عن الصفر دون outcomes سابقة مرصودة وعن التاريخ المجهول. التاريخ المتاح left-censored: عدم رصد فصل سابق لا يثبت أن الطالب جديد، والصفر وحده لا يثبت تعثرًا أكاديميًا. تحتسب مجموعات المعدل باستخدام `start_agpa_points`، أما عدّ الفصول السابقة فوصفي للتقييم فقط.

### stage2

| cohort | students | plans | course rows | base Plan MAE | reduced Plan MAE | delta | base student macro | reduced student macro |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| positive_prior_gpa_0_1 | 165 | 174 | 638 | 0.72058528 | 0.72509349 | 0.0045082065 | 0.72232008 | 0.72514401 |
| positive_prior_gpa_1_2 | 1083 | 1347 | 5962 | 0.62293509 | 0.62217456 | -0.00076052959 | 0.59378965 | 0.59319054 |
| positive_prior_gpa_2_3 | 4410 | 6962 | 37260 | 0.424575 | 0.42634259 | 0.0017675949 | 0.44200439 | 0.44371404 |
| positive_prior_gpa_3_4 | 1185 | 1819 | 10807 | 0.25278887 | 0.25259925 | -0.00018961474 | 0.27604332 | 0.27575919 |
| positive_prior_gpa_le_2 | 1236 | 1521 | 6600 | 0.63410612 | 0.63394833 | -0.0001577945 | 0.61118039 | 0.61112047 |
| zero_with_observed_prior_outcomes | 430 | 648 | 3432 | 0.31204176 | 0.30676808 | -0.0052736826 | 0.33351522 | 0.32692903 |
| zero_no_observed_prior_outcomes | 1763 | 1763 | 9437 | 0.67603204 | 0.68304571 | 0.0070136756 | 0.67603204 | 0.68304571 |
| zero_history_unknown | 0 | 0 | 0 | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| missing_prior_gpa | 0 | 0 | 0 | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| prior_gpa_out_of_range | 0 | 0 | 0 | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |

### stage1

| cohort | students | plans | course rows | base Plan MAE | reduced Plan MAE | delta | base student macro | reduced student macro |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| positive_prior_gpa_0_1 | 165 | 174 | 638 | 0.71770512 | 0.72186678 | 0.0041616629 | 0.71908588 | 0.72590797 |
| positive_prior_gpa_1_2 | 1083 | 1347 | 5962 | 0.62637297 | 0.62548079 | -0.00089217655 | 0.59572609 | 0.5952097 |
| positive_prior_gpa_2_3 | 4410 | 6962 | 37260 | 0.42652384 | 0.4265739 | 5.005219e-05 | 0.44394247 | 0.4439256 |
| positive_prior_gpa_3_4 | 1185 | 1819 | 10807 | 0.25227989 | 0.25497897 | 0.0026990893 | 0.2758084 | 0.27870235 |
| positive_prior_gpa_le_2 | 1236 | 1521 | 6600 | 0.63682122 | 0.63650719 | -0.0003140253 | 0.61286522 | 0.61301042 |
| zero_with_observed_prior_outcomes | 430 | 648 | 3432 | 0.31270937 | 0.31105395 | -0.0016554118 | 0.33477176 | 0.33169736 |
| zero_no_observed_prior_outcomes | 1763 | 1763 | 9437 | 0.67417299 | 0.67605637 | 0.0018833746 | 0.67417299 | 0.67605637 |
| zero_history_unknown | 0 | 0 | 0 | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| missing_prior_gpa | 0 | 0 | 0 | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| prior_gpa_out_of_range | 0 | 0 | 0 | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |

`n_students` عدد هويات student_id الفريدة داخل الفئة، وقد يظهر الطالب في أكثر من فصل أو فئة؛ خطأ الطالب macro يعطي كل طالب وزنًا متساويًا، بينما Plan MAE يعطي كل خطة مرصودة وزنًا متساويًا.

## H. توافق المرحلتين

عقد full يحذف الميزات الثلاث ليصبح 44؛ shortlist يستبعد أصلًا ميزات سياق الخطة ويحذف historical average attempt فقط ليصبح 32. تظل هوية ميزات التدريب والاستدلال وترتيبها موثقة في `feature_contract.json` و`compatibility.json`. التوافق المثبت يخص المصفوفات والتوقعات للخطط المرصودة ومسار التاريخ التجريبي؛ لم يُقَس shortlist recall أو جودة البحث عن خطط بديلة أو جودة التوصيات counterfactual، ولم يتغير Manifest.

## I. الحكم وعدم اليقين

paired student-cluster bootstrap: `2000` draws، seed `42`، فواصل percentile 95%؛ تُسحب هوية الطالب كاملة مع الحفاظ على مقام كل مقياس. المقارنة مشتركة الصفوف/الخطط باستخدام المفاتيح الفعلية. الفئات الثانوية وصفية، دون تصحيح تعدد المقارنات.

الهوامش حُددت مسبقًا في PLAN.md قبل النتائج: overall Plan MAE `+0.01`، positive prior GPA ≤2 Plan MAE `+0.02`، overall Log Loss `+0.002` وBrier `+0.001`. هي افتراضات بحثية وليست موافقة أكاديمية. `COMPARABLE` يتطلب الحد الأعلى لكل CI ضمن هامشه؛ `WORSE` إذا تجاوز الحد الأدنى أي هامش؛ `BETTER` يتطلب أيضًا الحد الأعلى لتحسن overall Plan MAE أقل من `−0.01`. خلاف ذلك `INCONCLUSIVE`. عدم الدلالة وحده لا يثبت التكافؤ، ولا نعيد ضبط الهوامش بعد مشاهدة النتائج.

### stage2: `COMPARABLE`

| cohort | metric | margin | delta | 95% low | 95% high |
| --- | --- | --- | --- | --- | --- |
| overall | plan_gpa_mae | 0.01 | 0.0016258039 | 0.00066802716 | 0.0026376879 |
| positive_prior_gpa_le_2 | plan_gpa_mae | 0.02 | -0.0001577945 | -0.0039528359 | 0.0033021326 |
| overall | fail_log_loss | 0.002 | 0.00053337955 | 0.00022252489 | 0.00084207695 |
| overall | fail_brier | 0.001 | -1.7271797e-05 | -0.00010046247 | 6.2107273e-05 |

فواصل المؤشرات الأساسية والثانوية:

| cohort | metric | delta | 95% low | 95% high | students |
| --- | --- | --- | --- | --- | --- |
| overall | grade_mae | 0.021664313 | 0.015176999 | 0.028241336 | 7019 |
| overall | points_mae | 0.0011327292 | 0.00039865617 | 0.0019213885 | 7019 |
| overall | fail_log_loss | 0.00053337955 | 0.00022252489 | 0.00084207695 | 7019 |
| overall | fail_brier | -1.7271797e-05 | -0.00010046247 | 6.2107273e-05 | 7019 |
| overall | plan_gpa_mae | 0.0016258039 | 0.00066802716 | 0.0026376879 | 7019 |
| overall | plan_gpa_bias | 0.0034652315 | 0.002406684 | 0.0044780615 | 7019 |
| overall | student_macro_plan_mae | 0.0016733169 | 0.00048560096 | 0.002988704 | 7019 |
| positive_prior_gpa_0_1 | grade_mae | 0.06446625 | -0.016597253 | 0.14277359 | 165 |
| positive_prior_gpa_0_1 | points_mae | 0.00039184953 | -0.009908839 | 0.010518115 | 165 |
| positive_prior_gpa_0_1 | fail_log_loss | -0.001157728 | -0.0057715922 | 0.0035564246 | 165 |
| positive_prior_gpa_0_1 | fail_brier | -0.00067277861 | -0.0025648295 | 0.0012707107 | 165 |
| positive_prior_gpa_0_1 | plan_gpa_mae | 0.0045082065 | -0.005721842 | 0.015034891 | 165 |
| positive_prior_gpa_0_1 | plan_gpa_bias | 0.017072283 | 0.0073193299 | 0.027330701 | 165 |
| positive_prior_gpa_0_1 | student_macro_plan_mae | 0.0028239303 | -0.0065328586 | 0.011690482 | 165 |
| positive_prior_gpa_1_2 | grade_mae | 0.0071196502 | -0.013365189 | 0.028102834 | 1083 |
| positive_prior_gpa_1_2 | points_mae | -0.0018030862 | -0.0047793369 | 0.0011525068 | 1083 |
| positive_prior_gpa_1_2 | fail_log_loss | -3.860191e-05 | -0.0013859105 | 0.001393679 | 1083 |
| positive_prior_gpa_1_2 | fail_brier | -5.6228995e-05 | -0.00055383997 | 0.00044761451 | 1083 |
| positive_prior_gpa_1_2 | plan_gpa_mae | -0.00076052959 | -0.0045636492 | 0.0028677233 | 1083 |
| positive_prior_gpa_1_2 | plan_gpa_bias | -0.0015274753 | -0.0057108115 | 0.0023666437 | 1083 |
| positive_prior_gpa_1_2 | student_macro_plan_mae | -0.00059911191 | -0.0049321482 | 0.0033903771 | 1083 |
| positive_prior_gpa_le_2 | grade_mae | 0.012663155 | -0.0080428525 | 0.032786358 | 1236 |
| positive_prior_gpa_le_2 | points_mae | -0.0015909091 | -0.0045010856 | 0.0013384758 | 1236 |
| positive_prior_gpa_le_2 | fail_log_loss | -0.0001467841 | -0.0014972807 | 0.0011367746 | 1236 |
| positive_prior_gpa_le_2 | fail_brier | -0.00011582879 | -0.00060155891 | 0.00034268226 | 1236 |
| positive_prior_gpa_le_2 | plan_gpa_mae | -0.0001577945 | -0.0039528359 | 0.0033021326 | 1236 |
| positive_prior_gpa_le_2 | plan_gpa_bias | 0.00060030771 | -0.0032740164 | 0.0043436694 | 1236 |
| positive_prior_gpa_le_2 | student_macro_plan_mae | -5.9912999e-05 | -0.0041069999 | 0.0035054974 | 1236 |

`stage2/grade_mae`: delta `0.021664313`، CI `[0.015176999, 0.028241336]`: تراجع إحصائي قابل للرصد لأن CI موجب بالكامل. الحكم العملي أعلاه يُقارن بالهوامش المحددة مسبقًا؛ قد يجتمع COMPARABLE عمليًا مع تراجع صغير ذي دلالة إحصائية.

`stage2/plan_gpa_mae`: delta `0.0016258039`، CI `[0.00066802716, 0.0026376879]`: تراجع إحصائي قابل للرصد لأن CI موجب بالكامل. الحكم العملي أعلاه يُقارن بالهوامش المحددة مسبقًا؛ قد يجتمع COMPARABLE عمليًا مع تراجع صغير ذي دلالة إحصائية.

### stage1: `COMPARABLE`

| cohort | metric | margin | delta | 95% low | 95% high |
| --- | --- | --- | --- | --- | --- |
| overall | plan_gpa_mae | 0.01 | 0.00055283229 | -0.00042577299 | 0.0014206564 |
| positive_prior_gpa_le_2 | plan_gpa_mae | 0.02 | -0.0003140253 | -0.0044201139 | 0.0036008793 |
| overall | fail_log_loss | 0.002 | -0.00016298075 | -0.0004916859 | 0.00015771152 |
| overall | fail_brier | 0.001 | -0.00016297147 | -0.00026320545 | -7.2641646e-05 |

فواصل المؤشرات الأساسية والثانوية:

| cohort | metric | delta | 95% low | 95% high | students |
| --- | --- | --- | --- | --- | --- |
| overall | grade_mae | 0.015177654 | 0.0088183674 | 0.021411693 | 7019 |
| overall | points_mae | 0.00029243663 | -0.00047765157 | 0.0010181382 | 7019 |
| overall | fail_log_loss | -0.00016298075 | -0.0004916859 | 0.00015771152 | 7019 |
| overall | fail_brier | -0.00016297147 | -0.00026320545 | -7.2641646e-05 | 7019 |
| overall | plan_gpa_mae | 0.00055283229 | -0.00042577299 | 0.0014206564 | 7019 |
| overall | plan_gpa_bias | -0.0051701686 | -0.0061178538 | -0.0042028835 | 7019 |
| overall | student_macro_plan_mae | 0.00044098013 | -0.00062501252 | 0.0014039238 | 7019 |
| positive_prior_gpa_0_1 | grade_mae | 0.11028235 | 0.027553304 | 0.19875114 | 165 |
| positive_prior_gpa_0_1 | points_mae | 0.0027429467 | -0.011245648 | 0.015698635 | 165 |
| positive_prior_gpa_0_1 | fail_log_loss | 0.0039784768 | -0.002880882 | 0.011616961 | 165 |
| positive_prior_gpa_0_1 | fail_brier | 0.001544684 | -0.0011675583 | 0.0044993221 | 165 |
| positive_prior_gpa_0_1 | plan_gpa_mae | 0.0041616629 | -0.010056141 | 0.017883421 | 165 |
| positive_prior_gpa_0_1 | plan_gpa_bias | 0.0040892975 | -0.0099335361 | 0.018323341 | 165 |
| positive_prior_gpa_0_1 | student_macro_plan_mae | 0.0068220878 | -0.0066565314 | 0.020027748 | 165 |
| positive_prior_gpa_1_2 | grade_mae | 0.011078902 | -0.0084238631 | 0.030575022 | 1083 |
| positive_prior_gpa_1_2 | points_mae | -0.00071284804 | -0.0035575125 | 0.002217456 | 1083 |
| positive_prior_gpa_1_2 | fail_log_loss | -0.00071468027 | -0.0022881379 | 0.00085517467 | 1083 |
| positive_prior_gpa_1_2 | fail_brier | -0.00038844989 | -0.00096938575 | 0.0001753125 | 1083 |
| positive_prior_gpa_1_2 | plan_gpa_mae | -0.00089217655 | -0.004923101 | 0.0033272384 | 1083 |
| positive_prior_gpa_1_2 | plan_gpa_bias | 0.0022320741 | -0.0017928892 | 0.006161839 | 1083 |
| positive_prior_gpa_1_2 | student_macro_plan_mae | -0.0005163932 | -0.0049712133 | 0.0033761314 | 1083 |
| positive_prior_gpa_le_2 | grade_mae | 0.020668569 | 0.0012916292 | 0.040450129 | 1236 |
| positive_prior_gpa_le_2 | points_mae | -0.00037878788 | -0.0032953567 | 0.002613504 | 1236 |
| positive_prior_gpa_le_2 | fail_log_loss | -0.00026100842 | -0.0017938446 | 0.0013681744 | 1236 |
| positive_prior_gpa_le_2 | fail_brier | -0.00020158028 | -0.00075414595 | 0.00040347589 | 1236 |
| positive_prior_gpa_le_2 | plan_gpa_mae | -0.0003140253 | -0.0044201139 | 0.0036008793 | 1236 |
| positive_prior_gpa_le_2 | plan_gpa_bias | 0.0024445375 | -0.0015351153 | 0.0063287731 | 1236 |
| positive_prior_gpa_le_2 | student_macro_plan_mae | 0.00014519717 | -0.0042274438 | 0.003887134 | 1236 |

`stage1/grade_mae`: delta `0.015177654`، CI `[0.0088183674, 0.021411693]`: تراجع إحصائي قابل للرصد لأن CI موجب بالكامل. الحكم العملي أعلاه يُقارن بالهوامش المحددة مسبقًا؛ قد يجتمع COMPARABLE عمليًا مع تراجع صغير ذي دلالة إحصائية.

`stage1/plan_gpa_mae`: delta `0.00055283229`، CI `[-0.00042577299, 0.0014206564]`: الفاصل يشمل الصفر؛ اتجاه الفرق غير محسوم إحصائيًا. الحكم العملي أعلاه يُقارن بالهوامش المحددة مسبقًا؛ قد يجتمع COMPARABLE عمليًا مع تراجع صغير ذي دلالة إحصائية.

## J. التوصية والأسئلة الستة

1. **هل يمكن حذف `attempt_sum` بأمان من العقد المستقبلي؟** المسار التجريبي يدعم تمثيل التاريخ وتحديثه دون هذا الحقل مع parity موثق؛ الحكم التنبؤي المستقل: `stage2=COMPARABLE, stage1=COMPARABLE`. الأمان الكامل لعقد API غير مثبت قبل التحقق من تعريفات بقية المجاميع وcutoff، ولا يمكن تحميل الحالة المختزلة مكان الحالة الرسمية مباشرة.

2. **ما الميزات التي تختفي من عقد الإنتاج؟** إذا تقرر الانتقال لاحقًا: `course_history_avg_attempt` و`plan_credit_weighted_avg_attempt` و`peer_credit_weighted_avg_attempt` للـfull؛ الأولى فقط للـshortlist. يبقى `attempt_number` و`course_history_retake_rate` و`retake_sum`.

3. **هل تغيرت الدقة بصورة مهمة؟** الحكم المحدد سلفًا هو `stage2=COMPARABLE, stage1=COMPARABLE`؛ جداول F وI تعرض الفروق وفواصلها. لا نساوي فرقًا صغيرًا في MAE بتحسن موثوق ولا نخلط بين الدلالة الإحصائية والهامش العملي.

4. **هل الأثر مختلف لدى أصحاب GPA المنخفض؟** تعرض G الفئات الموجبة منفصلة والصفر منفصلًا، وتعرض I فواصل `(0,2]` والفئتين الأدنى. يُقرأ اختلاف الأثر من هذه التقديرات وحدودها؛ الفئات قليلة الطلاب وفواصلها الواسعة لا تدعم تعميمًا مستقلًا.

5. **هل البديل متوافق مع المرحلتين؟** نعم ضمن replay المحلي للميزات المتبقية ومصفوفتي 44 و32، مع تدريب وتقييم مستقلين لكل عائلة. دمج engine/Manifest وتشغيل توصيات بديلة في الإنتاج لم يُنفذ ولم يُثبت بهذه التجربة.

6. **اعتماد مباشر أم بحث ميزات بديلة أولًا؟** لا اعتماد إنتاجي مباشر. إذا كانت العائلتان COMPARABLE/BETTER فالأدلة تدعم الانتقال إلى تحقق عقد الجامعة وتقييم الدمج المنفصل، دون اشتراط اختراع ميزات بديلة. إذا كانت أي عائلة WORSE/INCONCLUSIVE يلزم تحقيق إضافي محدد، وقد تُبحث البدائل في تجربة لاحقة مستقلة. لم تُضف هذه التجربة أي بديل ولم تُرقَّ أي قطعة أثرية.

### إعادة التشغيل والملفات

الأمر القابل لإعادة الإنتاج من جذر المستودع:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.experiments.attempt_sum_removal.runner --threads 4 --draws 2000
```

المشغل يرفض التشغيل إذا وُجد أي مجلد نتائج/نماذج للتجربة أو التقرير النهائي؛ لا overwrite ولا resume. لتكرار مستقل يجب حفظ هذه الأدلة أولًا واختيار مساحة جديدة مصرح بها أو إعادة تشغيله في checkout نظيف. `metadata.json` يحفظ الإعدادات والأزمنة وإعادة baseline، و`comparison.csv/json` المقارنات، `validation.json` الفواصل الزمنية، و`stage*_intervals.csv` عدم اليقين، و`stage*_*_cohorts.csv` أحجام الفئات ومقاييسها. البيانات الفردية تظل محلية داخل مساحة التجربة.


### تحقق الاختبارات

```json
{
  "focused": {
    "status": "PASS",
    "passed": 53,
    "skipped": 2,
    "skip_reason": "Windows symbolic link creation not permitted"
  },
  "related": {
    "status": "PASS",
    "passed": 57,
    "subtests_passed": 6
  },
  "full_suite": {
    "status": "INCOMPLETE",
    "reason": "Interrupted at existing tests/test_api_cumulative_integration.py:52; standalone faulthandler trace shows Windows asyncio proactor socketpair socket.accept waiting during TestClient.__enter__; no full-suite PASS claimed",
    "log": "scripts/experiments/attempt_sum_removal/full_tests.log",
    "diagnostic_log": "scripts/experiments/attempt_sum_removal/hang_check.log"
  }
}
```

`focused_tests`: [scripts/experiments/attempt_sum_removal/focused_tests.log](<D:/AI/Real projects/Academic_Advisor_Simple/scripts/experiments/attempt_sum_removal/focused_tests.log>)

```text
.....................................................ss                  [100%]
53 passed, 2 skipped in 5.21s
```

`related_tests`: [scripts/experiments/attempt_sum_removal/related_tests.log](<D:/AI/Real projects/Academic_Advisor_Simple/scripts/experiments/attempt_sum_removal/related_tests.log>)

```text
.........................................................          [100%]
57 passed, 6 subtests passed in 3.83s
```

`full_tests`: [scripts/experiments/attempt_sum_removal/full_tests.log](<D:/AI/Real projects/Academic_Advisor_Simple/scripts/experiments/attempt_sum_removal/full_tests.log>)

```text
........................................................................ [  4%]
........................................................................ [  9%]
```

