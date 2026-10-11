# إصلاح تسمية مرشح `capacity_63`

تاريخ التنفيذ: 2026-10-10. طلب المستخدم إصلاح كل ما يتعلق بعدم اتساق `capacity_63` و`capaciy_63` بعد تسليم Backend API. هذا تصحيح تسمية وتوثيق؛ لا تدريب أو نشر أو توصية لطالب حقيقي أو Git commit.

## السبب والتغيير

كان [train_models.py](../src/modeling/train_models.py) يسمي مرشح `num_leaves=63` باسم `capaciy_63`، بينما metadata الرسمية و[المحمّل V2](../src/recommendation/artifacts.py) و[محمّل Two-Stage](../src/recommendation/two_stage_artifacts.py) واختبار اختيار المرشح تستخدم `capacity_63`. أثبت تشغيل الاختبار قبل التعديل عدم الاتساق: **11 passed, 1 failed**؛ الفشل هو `test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`.

صُحح الاسم في تعريف المرشح إلى `capacity_63`. لم تتغير ترتيب المرشحين أو قيم `num_leaves=63`, `min_data_in_leaf=100`, `feature_fraction=0.85`, `bagging_fraction=0.90`, `lambda_l1=0.20`, `lambda_l2=2.00`، ولا seed أو الفصول أو أعداد boosting أو early stopping أو بقية كود المدرب. الاختبار الموجود يمر عبر المرشحين الثلاثة والفصلين باستخدام مودل مصطنع؛ لم يُخفف الاختبار أو loader، ولم يُضف alias يسمح بالاسم الخاطئ في عقد V2 الرسمي.

عُدّل التوثيق الحي الذي كان يصف المشكلة بأنها مفتوحة، وصيغ مولدات تقارير `course_only` و`attempt_number` لتمييز التسمية الحالية من نتائج تشغيلات التجارب السابقة. أرقام نتائج API ومراحل Two-Stage والتجارب السابقة محفوظة كما سُجلت؛ يرتبط وضعها الحالي بهذا التقرير.

## الأدلة التاريخية وبصمات المصدر

يبقى `capaciy_63` مقصودًا في metadata التجارب المحفوظة، وفي provenance داخل manifest القديم، وفي fixtures التي تختبر حفظ المصدر الأصلي، وفي تقارير وlogs تشغيلات سابقة وأداة تصدير التقرير التاريخي `scripts/experiments/student_progress_20261010/report.py`. هذه المواضع تسجل ما نُفذ وقتها؛ استبدالها سيغير الأدلة دون تدريب جديد. اختبار `test_two_stage_artifacts.py` يثبت الاحتفاظ بالتسمية الأصلية وبصماتها في provenance.

بصمة ملف المدرب قبل الإصلاح:

```text
d9c88283a0237050cd32f696cc58d511ca8a59b394617a3de13e1340e9f149aa
```

بصمة ملف المدرب بعد الإصلاح:

```text
b89aa1d8299a635d38e0321f60113c385f9a478100646c9b3702a1d23b0c6a14
```

تغير بصمة المصدر متوقع ومصرح به، ويغير signatures التي تتضمنه. `experiment_signature()` وواجهات cache/reuse تبقى صارمة؛ لا تغيير لبصمات محفوظة ولا bypass لقبول cache قديم. لم تُعد تشغيل تجربة أو توليد تقرير تجريبي من المدخلات الحقيقية.

## التحقق

| المكوّن | النتيجة |
|---|---|
| المدرب وtraining config | **PASS**: 19 passed |
| المحمّلات والتجارب وcache/provenance | **PASS**: 127 passed |
| Full pytest | **PASS**: 1262 passed، 6 subtests passed، 0 failed؛ 193.12 ثانية؛ تحذير Starlette/httpx واحد غير متعلق بالتسمية |
| تطابق جميع إعدادات التدريب عدا الاسم | **PASS**: AST قبل/بعد متطابق بعد استبدال string واحدة؛ جميع الإعدادات العددية والفصول ثابتة، ومولدات التقارير سليمة نحويًا |
| SHA-256 لملفات `data/` و`models/` | **PASS**: 1230 ملفًا قبل/بعد؛ changed=0، added=0، removed=0؛ `NOT CHANGED` |
| graphify AST update | **PASS**: بلا LLM؛ 3495 nodes، 8739 edges، 224 communities؛ أسماء بعض communities اشتقت من hub عند تغير التجميع، ولم تُشغّل labeling عبر API |
| Git diff وHEAD | **PASS**: `diff --check` بلا أخطاء، HEAD ثابت، لا commit؛ التغييرات في اسم المرشح ونصوص التقارير والتوثيق وخريطة graphify فقط |

الفشل الوحيد الذي أُعيد إنتاجه قبل الإصلاح اجتاز الاختبار بعده، ولا regression جديدة في التشغيل الكامل. `PARTIAL` و`BLOCKED` الخاصة بإصلاح التسمية: **لا يوجد**؛ القيود الجامعية المنفصلة تبقى موثقة في تقرير API. روابط التوثيق إلى هذا التقرير فُحصت ووجدت سليمة.

الأوامر من جذر المشروع:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_train_models.py tests/test_training_config.py -q --tb=short --basetemp='.pytest_cache/capacity63-focused'
.\.venv\Scripts\python.exe -m pytest tests/test_experiment_io.py tests/test_course_only_recommendation.py tests/test_attempt_number_experiment.py tests/test_recommendation_v2.py tests/test_two_stage_artifacts.py -q --tb=short --basetemp='.pytest_cache/capacity63-related'
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp='.pytest_cache/capacity63-full'
graphify update .
git -c safe.directory='D:/AI/Real projects/Academic_Advisor_Simple' diff --check
```

ملفات التدقيق المحلية في `.pytest_cache/capacity63-audit/`: baseline، inventories قبل/بعد، المقارنة، وlogs المجموعتين المرتبطة والكاملة. baseline بدأ من working tree نظيفة وHEAD=`359146880d3717169d998916a39309dd89481c7b`؛ لا commit من هذه المهمة.

هذا الإصلاح لا يعتمد أداء الإنتاج أو اكتمال بيانات الجامعة أو جودة التوصيات الحقيقية؛ حالات `PARTIAL` و`BLOCKED` الجامعية في [تقرير API](backend_api_integration.md) مستقلة عن عطل التسمية.
