Date: 2026-10-05
Validation Status: KNOWN BASELINE FAILURE
Implementation Status: PLAN SAVED; PRODUCTION IMPLEMENTATION NOT STARTED

# توثيق Baseline قبل تنفيذ Recommendation Two-stage

## نطاق هذه اللقطة

حُفظت الخطة المعتمدة في `D:/AI/Real projects/Academic_Advisor_Simple/docs/architecture/RECOMMENDATION_TWO_STAGE_IMPLEMENTATION_PLAN.md`، مع تقييم واعتماد `stage1_shortlist_strategy` و`final_ranking_strategy` بصورة مستقلة. Production Ranking ما زالت UNAPPROVED.

شملت هذه الخطوة حفظ الوثائق وفحص Git وتشغيل Full pytest وتجهيز Commit للوضع الحالي المراجع. لا تنفيذ للخطة أو تدريب أو Benchmark أو Recommendation حقيقية. الكود والتقارير وArtifacts التجارب المضافة إلى اللقطة كانت موجودة قبل هذه الخطوة، ولا يُعد Commit نشرًا لها في Production.

الفحص أجري على فرع `Production`، وكان HEAD قبل Commit:

```text
d24642c0b7c0ec9ef21001a4276e0514c66c60ae
```

## Full pytest

الأمر من جذر المشروع:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

النتيجة الفعلية:

```text
1 failed, 612 passed, 6 subtests passed in 49.00s
Exit code: 1
```

لم يظهر Skipped في ملخص هذه الجولة. لا توصف Full suite بأنها ناجحة؛ الفشل الوحيد أدناه بقي كما هو.

## الفشل القديم capacity_63

الاختبار:

```text
tests/test_train_models.py::test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]
```

المصدر `D:/AI/Real projects/Academic_Advisor_Simple/src/modeling/train_models.py:94` يعرّف اسم Candidate بالشكل `capaciy_63`، بينما الاختبار يتوقع `capacity_63`. فشل Assertion في `D:/AI/Real projects/Academic_Advisor_Simple/tests/test_train_models.py:186`:

```text
AssertionError: assert 'capaciy_63' == 'capacity_63'
```

هذا اختلاف إملائي موثق قبل حفظ الخطة، وموجود في المصدر والاختبار عند HEAD السابق المذكور. الاختبار يستخدم Synthetic frame وFakeModel عبر monkeypatch، وليس تدريبًا حقيقيًا. بقية الحالة الاختبارية المقابلة لـFail نجحت.

لم يُصحح الاسم في هذه الخطوة، ولم تُعدّل Parameters أو Model metadata أو Artifacts لإخفاء الفشل. إصلاح الاسم المستقبلي يُراجع كتغيير مصدر محدود، وتبقى Provenance الأصلية للـArtifacts المحفوظة كما هي.

## سلامة البيانات والـArtifacts

فُحص SHA-256 لجميع الملفات الموجودة تحت `D:/AI/Real projects/Academic_Advisor_Simple/models/` و`D:/AI/Real projects/Academic_Advisor_Simple/data/` قبل وبعد Full pytest، مع استبعاد Python caches:

```text
Protected files before: 873
Protected files after: 873
Changed: []
Removed: []
Added: []
```

بصمة Manifest الفحص القبلي:

```text
c9a64b9cf3f37148fb16a8aa43d50d17e696774b9e667e669a5e98a9037fc6a6
```

الـ39 ملفًا الموجودة مسبقًا تحت `D:/AI/Real projects/Academic_Advisor_Simple/models/experiments/attempt_number/` تُحفظ في Commit بوصفها Artifacts تجريبية حالية، دون Promotion أو تغيير للبايتات. أضيفت قاعدة `-text` محدودة لهذه الملفات في `D:/AI/Real projects/Academic_Advisor_Simple/.gitattributes` لمنع تحويل نهايات الأسطر عند Git checkout، لأن المستودع يستخدم `core.autocrlf=true` ولأن Metadata تثبت بصمات هذه الملفات.

## نطاق Commit والاستثناءات المحلية

تُضم الخطة وتقرير التحقق والحالة الحالية المراجعة من الكود والاختبارات والتقارير المجمعة وArtifacts التجارب وتعليمات Graphify. تُضم ملفات الرسم الأساسية، وتبقى Cache المحلية المولدة خارج Commit. لم يتغير Production source ضمن هذه الخطوة، ولذلك لم يُشغّل Graphify update لإعادة بناء الرسم.

الملفات التالية تبقى محلية وغير مضافة، وفق تعليمات `D:/AI/Real projects/Academic_Advisor_Simple/AGENTS.md` التي تمنع إدراج سجلات الطلاب في Commits:

```text
D:/AI/Real projects/Academic_Advisor_Simple/notebooks/s.ipynb
D:/AI/Real projects/Academic_Advisor_Simple/docs/PRODUCTION_CONTRACT.md
D:/AI/Real projects/Academic_Advisor_Simple/reports/..md
D:/AI/Real projects/Academic_Advisor_Simple/reports/api_request_column_mapping.md
D:/AI/Real projects/Academic_Advisor_Simple/reports/attempt_number_feature_analysis.md
```

تحتوي هذه الملفات سجلات أو أمثلة أكاديمية فردية، ولم تُحذف أو تُعدّل أو تُنظف في هذه الخطوة. مخرجات التشخيص الفردية الموجودة في `reports/repeat_withdrawal_analysis/` تبقى مستبعدة بواسطة `.gitignore` الخاصة بذلك المجلد؛ التقارير المضافة منه مجمعة أو توثق المصادر والبصمات.

ملفات التشغيل المحلية للفحص محفوظة خارج المستودع في:

```text
C:/Users/ASUS/AppData/Local/Temp/recommendation_plan_baseline_59br9yoc/full_pytest.log
C:/Users/ASUS/AppData/Local/Temp/recommendation_plan_baseline_59br9yoc/pytest_result.json
C:/Users/ASUS/AppData/Local/Temp/recommendation_plan_baseline_59br9yoc/protected_before.json
C:/Users/ASUS/AppData/Local/Temp/recommendation_plan_baseline_59br9yoc/protected_after.json
C:/Users/ASUS/AppData/Local/Temp/recommendation_plan_baseline_59br9yoc/integrity_result.json
```

هذه الملفات المؤقتة دليل محلي للجولة الحالية وقد لا تبقى متاحة لاحقًا. النتيجة وسبب الفشل وسلامة الملفات موثقة في هذه الوثيقة داخل Commit.

## مراجعة Git index قبل Commit

أضيفت 103 ملفات مراجعة إلى Git index. تضم 39 ملف Model/Metadata/Category من تجربة Attempt number الموجودة مسبقًا. طوبقت بايتات كل ملف من هذه الـ39 بين Working tree وGit index، والاختلافات `[]`. لم يُضف أي من الملفات الخمسة المستثناة أو `graphify-out/cache/`.

فحص Git الافتراضي يعتبر CR في نهايات الأسطر الأصلية للـJSON التجريبية Trailing whitespace، لأن بايتاتها حُفظت كما هي. نجح الفحص عند تعريف CRLF نهاية سطر سليمة، دون إعادة كتابة أي Artifact:

```powershell
git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --cached --check
```

```text
Exit code: 0
Output: empty
```
