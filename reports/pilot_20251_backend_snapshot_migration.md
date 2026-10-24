# Pilot 20251 — فصل Before / After Backend Fix

التاريخ: 2026-10-22. الفرع: `new_branch`. حالة الترحيل والتحقق: **PASS**. جمع Courses المصححة والتقييم الحقيقي التالي متروكان للمشغّل.

تم فصل جمع الاستجابات وقراءة المدخلات وحفظ النتائج. الافتراضي هو `after_backend_fix`، والأرشيف `before_backend_fix` للقراءة فقط. لم تُجرَ اتصالات جامعة أو دفعة توصية حقيقية جديدة أو إعادة تدريب أو Commit/Push.

## البنية النهائية

```text
D:\AI\Real projects\Academic_Advisor_Simple\data\evaluation\recommendation_pilot_20251\
├── students.csv                         # نسخة مطابقة؛ 30 أساسياً و12 احتياطاً
├── snapshots/
│   ├── before_backend_fix/
│   │   ├── students.csv                 # توثيق العينة الأصلية
│   │   └── api_data/
│   │       ├── students/                # 30 Student + 30 Courses مع metadata
│   │       └── frozen_history/          # 15 استجابة مع metadata
│   └── after_backend_fix/
│       └── api_data/
│           ├── students/                # 30 Student مع metadata؛ Courses غائبة عمداً
│           └── frozen_history/          # نفس bytes الفصول الـ15 وmetadata
├── experiments/
│   ├── before_backend_fix/
│   │   ├── comparison/                  # 21 Run محفوظاً
│   │   └── actual_candidate_injection/  # 8 Runs محفوظة
│   └── after_backend_fix/
│       ├── comparison/                  # وجهة المقارنة الجديدة؛ فارغة الآن
│       └── actual_candidate_injection/  # وجهة التشخيص الصريح؛ فارغة الآن
├── before_backend_fix/                  # الأصل الموجود قبل التنفيذ؛ احتُفظ به كاملاً
│   ├── students.csv
│   ├── API_CHECKLIST.md
│   ├── api_data/
│   └── experiments/
│       ├── model_versions/              # الحزم المشتركة في مكانها الفعلي، دون نقل/نسخ
│       ├── preparation_20261019T105323/  # لم يتغير
│       ├── _audit/                      # لم يتغير
│       └── ...                          # الأصول السابقة للتجارب محفوظة أيضاً
└── migration_audits/migration_20261022T110600_c622ec5b/
```

**تكييف ضروري للبنية المقترحة:** عند بدء المهمة كان المجلد الكامل، بما فيه النماذج والتحضيرات، موجوداً مسبقاً تحت `before_backend_fix/`، ولم تكن المسارات السابقة في الجذر موجودة. لم ننقل حزم النماذج مجدداً ولم نكررها. يفصل `model_versions_root()` اختيار الحزم المشتركة عن اختيار snapshot، ويفهم الموقع القياسي أيضاً إذا كان موجوداً في نسخة أخرى من المشروع.

## إجراءات الترحيل وسلامة الملفات

أُنشئ جرد وبصمات قبل النسخ. صنّف الجرد 29 Run مكتملة، ولا توجد Runs غير مكتملة ضمن المجلدات المكتشفة. صُنّفت `model_versions` و`preparation_*` و`_audit` كمخرجات مشتركة/مساندة تُترك في مكانها. رُصدت 4521 إشارة مسار في manifests والنتائج دون تعديلها.

نُسخ الأرشيف إلى Before بإنشاء حصري؛ ثم نُسخت Student وFrozen History وmetadata الأصلية إلى After. لم تُنسخ Courses القديمة إلى After. أُعيد توفير `students.csv` في الجذر بنسخة مطابقة، ونُظمت Runs بنسخ كاملة تحافظ على Run IDs وmanifests والتوقعات والمقاييس وCSV والصادرات المحمولة.

| الفحص | النتيجة |
|---|---|
| الملفات الأصلية المحمية، بما فيها النماذج وartifacts والتقارير السابقة | 823 ملفاً؛ الفحص الأولي والختامي PASS، عدد المتغيرات صفر |
| الملفات المنسوخة | 471 نسخة؛ تطابق SHA-256 مع المصدر أولياً وختامياً، عدد الاختلافات صفر |
| حذف أو نقل أصول | صفر؛ بقيت الأصول في مكانها |
| حجم النسخ الإضافية | 3,523,150,830 بايت؛ نحو 3.28 GiB |
| العينة | SHA-256: `7b195ad673067173fddb31b8ce87dbc25d22b7c5d12a4019e99a08f0ccd0e7e6` |
| Before | Student 30/30، Courses 30/30، History 15/15 |
| After | Student 30/30، Courses 0/30، History 15/15 |
| النماذج B/C | READY؛ النسخة `bc_20261019T163245_0226716d`؛ العقود 44/47 ميزة |
| manifest النموذج المشترك | `727c6cb6dfd763bfece38b269957691a1237724741b8328a3b7caf3d2d46dfb2` |

التفاصيل الخاصة محفوظة في مجلد التدقيق: `inventory_before.json`، و`copy_verification.json`، و`runtime_validation.json`. يسجل `legacy_path_mappings.json` عدد 33 تحويل مسار، وكل وجهاته موجودة؛ بذلك تبقى الإشارات القديمة قابلة للتتبّع دون إعادة كتابة التقارير أو نتائجها. لا تُنقل ملفات التدقيق المحتوية مسارات/هويات خاصة إلى Git. مجلد `data/` مستبعد أصلاً.

حماية Before هي رفض الكتابة من المجمّع ومشغّلات التجربة، مع التحقق بالبصمات؛ لم تُغيّر صلاحيات Windows. تُترك النسخ الأصلية المكررة عمداً، ولم تُنفذ أي إزالة لها.

## سلوك التشغيل والقراءة

- المجمّع يعرض snapshot النشطة واكتمال Student وCourses كلّاً على حدة. زر جمع الـ30 يحفظ Courses المصححة في After ويتجاوز المحفوظ السليم. فشل ملف جديد لا يمس الاستجابات الناجحة. جلب التاريخ معطل في تبويب الجمع.
- يوجد أمر جمع صريح يستخدم المجمّع والعميل نفسيهما، ويجلب Courses فقط؛ يشترط Student الأصلية الموثقة، ولا يستدعي نموذجاً أو توصية أو History API.
- الطالب الواحد والدفعة والتاريخ وتوقع الخطة الفعلية وتشخيص تغطية المرشحات تستخدم snapshot نفسها. غياب Courses الجديدة ينتج `MISSING_SNAPSHOT_RESPONSE`؛ تحققنا من هذا الحظر لجميع الطلاب الثلاثين دون تشغيل التنبؤ.
- المقارنة العادية تستخدم مرشحات API الأصلية المصححة. الحقن يتطلب تفعيل مربع التشخيص صراحة؛ عرض نتيجة Augmented محفوظة لا يفعّل الحقن لتشغيل جديد.
- كل Run جديدة تحت After، بإنشاء حصري ومعرّف فريد. manifest تسجل snapshot ومسارها وبصمات Student/Courses والتاريخ والعينة والنماذج وإعدادات التشغيل ونوع التجربة وGit commit وبصمات الكود. الاستجابة الغائبة تسجل `null` في بصمتها مع حالة الحظر.
- الاكتشاف يعرض 21 مقارنة و8 تجارب تشخيصية قديمة بمعرّفاتها، دون تكرار الأصول والنسخ في القائمة. `actual_report.py` حمّل Run تشخيصية قديمة بنجاح. التوليد الجديد للتقرير يستخدم ملفاً جديداً ولا يكتب فوق تقرير قائم.
- تحميل Before لا يعيد حساب توقع الخطة الفعلية: يُعرض التوقع المحفوظ إن وجد، وإلا يظهر `HISTORICAL_RECOMPUTATION_DISABLED`. كذلك تُحظر إعادة الحساب عبر snapshot مختلفة. تظل فحوص النماذج المسحوبة فعالة دون إعادة كتابة الملفات.
- لم يتغير `ui_client.py` أو عقد FastAPI الإنتاجي أو LightGBM أو GradeScale أو ميزات المقررات أو توليد الخطط أو ترتيبها أو تجميع التاريخ أو حالة التاريخ الرسمية.

## الملفات المعدلة والمضافة

ضمن `tools/academic_advisor_streamlit/`: `pilot_collection_store.py`، `streamlit_app.py`، `collect_pilot.py` (جديد)، `COLLECTOR_README.md`، و`tests/test_ui_client.py` (تصحيح fixture فقط).

ضمن `tools/recommendation_pilot_20251/`: `snapshots.py` و`snapshot_migration.py` (جديدان)، `adapter.py`، `history.py`، `engine.py`، `runner.py`، `app.py`، `actual_experiment.py`، `actual_report.py`، `modeling.py` (حل مسار التحميل فقط)، `observed_prediction.py`، `__main__.py`، `static/app.js`، `static/index.html`، و`README.md`.

الاختبارات: أضيف `tests/test_pilot_20251_snapshot_migration.py` و`tests/test_pilot_20251_snapshot_paths.py`. عُدّلت مسارات fixtures في `test_pilot_20251_engine.py` و`test_pilot_20251_history.py` و`test_pilot_20251_actual_experiment.py` و`test_pilot_20251_observed.py`.

التوثيق: هذا التقرير و`docs/superpowers/plans/2026-10-22-pilot-backend-snapshots.md`. ملفات Graphify المولدة تُحدّث وفق تعليمات المستودع؛ كانت تعديلات أخرى في Graphify وملفات تجربة الحقن موجودة قبل المهمة ولم تُلغَ.

## التحقق والاختبارات

| المتطلب | الدليل |
|---|---|
| A: حفظ التاريخ | جرد المصدر + مقارنة بصمات الأصول والنسخ |
| B/C: جمع جديد بلا استبدال | حفظ Courses اصطناعية في After مرة واحدة ثم تجاوز النسخة السليمة |
| D/E: منع fallback والربط | وجود Courses قديمة لا يمنع حظر غياب Courses الجديدة؛ المحرك الافتراضي يقرأ After |
| F: توافق النماذج | تحميل B/C الحقيقيين وعقديهما وGradeScale ومرجع C دون تدريب |
| G/H: التخزين والتصفح | Run اصطناعية في After؛ تحميل Before وبياناتها الأصلية دون إعادة scoring |
| I: اتساق snapshot | بصمات Student/Courses وملف التاريخ ومساره داخل manifest |
| J: Smoke | عميل اصطناعي → المجمّع → After → محرك التوصية → Run منفصلة |

اجتازت المجموعة المرتبطة أولاً 213 اختباراً، ثم 216 بعد اكتمال الاختبارات الإضافية. اجتازت مراجعة مستقلة 7 اختبارات وفحص الكود؛ أُصلح اختلاف snapshot عند تصفح Run من وضع Before. واجتاز فحص السبب المحدد 51 اختباراً.

الفحص الشامل الأول: 1798 passed، 26 failed، 1 skipped. كانت 25 حالة بسبب وضع `--basetemp` تحت `data/`، مما فعّل حارس فصل قاعدة طلبات FastAPI عن البيانات؛ نُقل مجلد الاختبار خارج `data/` دون تعديل الحارس. الحالة الأخرى fixture قديمة لا تحتوي `registserRule` رغم أن العميل يشترطها؛ أُصلحت الاستجابة الاصطناعية فقط. لا تُنسب هذه الإخفاقات إلى منطق snapshots.

اختبارات `TestClient` داخل عزل Windows علقت في `asyncio/socketpair` قبل دخول التطبيق؛ أُعيد التشغيل خارج العزل ونجحت المجموعة المرتبطة. المسار القصير للاختبارات يتجنب أيضاً حد طول المسار في Windows. توجد ملاحظة deprecation من Starlette/httpx؛ لم تُغير الاعتماديات.

الفحص الشامل النهائي: **1825 passed، 1 skipped، 6 subtests passed** في 310.80 ثانية، دون إخفاقات. الاختبار المتخطى هو `tests/test_api_request_store.py::test_posix_database_and_private_root_permissions`؛ سببه أن حماية Windows تعتمد صلاحيات حساب الخدمة ولا تطبق اختبارات POSIX. السجل: `full_suite_final.txt` في مجلد التدقيق. المجموعة المرتبطة: **216 passed**؛ سجلها `related_suite.txt`.

الفحص الختامي لكل الملفات: **PASS؛ 823 مصدراً دون تغيير و471 نسخة دون اختلاف**، كما في `final_integrity.txt`. اجتاز `git diff --check` الملفات المعنية، ولم يتغير أي ملف في `src/`. اكتمل `graphify update .` بنجاح باستخراج AST فقط دون LLM أو تكلفة API.

نجح أيضاً فحص Streamlit بـ`AppTest` مع منع `requests` بالكامل: After هي الافتراضية، أزرار جمع Before معطلة، وجلب التاريخ معطل، ولا استثناءات في العرض. توجد رسائل deprecation من Streamlit حول `use_container_width` الموروثة؛ لم تُغيّر الواجهة أو الاعتماديات لمعالجتها. تحققت أوامر `--help` للمجمّع وPilot دون تنفيذ جمع أو توصية.

## أوامر المشغّل — لم تُنفذ عمليات الجمع أو الدفعة التالية

كل الأوامر من جذر المشروع:

```powershell
Set-Location -LiteralPath 'D:\AI\Real projects\Academic_Advisor_Simple'
```

تشغيل Streamlit:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\tools\academic_advisor_streamlit\streamlit_app.py
```

في التبويب الثالث اختر `after_backend_fix` ثم اضغط **جمع الأساسيين الـ30 وحفظهم**. المتوقع قبل الجمع: Student 30/30 وCourses 0/30 وHistory 15/15.

أو جمع Courses المصححة للـ30 بأمر صريح، باستخدام إعدادات API والمصادقة الحالية:

```powershell
.\.venv\Scripts\python.exe -m tools.academic_advisor_streamlit.collect_pilot --all-primary --snapshot after_backend_fix
```

تشغيل Recommendation Pilot؛ افتح [الواجهة المحلية](http://127.0.0.1:8765):

```powershell
.\.venv\Scripts\python.exe -m tools.recommendation_pilot_20251 --port 8765 --snapshot after_backend_fix
```

بعد اكتمال Courses فقط، تشغيل تقييم B/C عبر مشغّل المقارنة الحالي الذي يعرض A/B/C معاً، بمرشحات API فقط ودون حقن:

```powershell
.\.venv\Scripts\python.exe -m tools.recommendation_pilot_20251 --run-all --snapshot after_backend_fix --credits 18 --max-plans 200
```

الوصول إلى Runs القديمة من قائمة التشغيلات الموسومة `before_backend_fix`، أو بأوامر قراءة فقط بعد تشغيل Pilot:

```powershell
(Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/runs').runs | Where-Object snapshot_id -EQ 'before_backend_fix'
Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/runs/run_20261019T164310_28d0fb7cb2'
Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/actual-candidate-runs/run_20261021T114914_4f2dcd430e'
```

خادم عرض Before مستقل اختياري؛ يرفض بدء Runs جديدة:

```powershell
.\.venv\Scripts\python.exe -m tools.recommendation_pilot_20251 --port 8766 --snapshot before_backend_fix
```

إنشاء تقرير مستقل من تشخيص سابق دون إعادة تنبؤ؛ يختار اسماً جديداً مؤرخاً:

```powershell
.\.venv\Scripts\python.exe -m tools.recommendation_pilot_20251.actual_report --run-id run_20261021T113124_3a9a6349ec
```

إعادة الفحوص المحلية:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache/t
.\.venv\Scripts\python.exe -m tools.recommendation_pilot_20251.snapshot_migration --verify .\data\evaluation\recommendation_pilot_20251\migration_audits\migration_20261022T110600_c622ec5b\inventory_before.json
```

## الحدود

لم يُختبر Backend المصحح حياً، ولم تُجمع Courses الجديدة. لذلك لا توجد نتائج After حقيقية بعد، وكل طالب يبقى محظوراً حتى استكمال استجابته الجديدة. هذا مقصود ولا يُعالج باستخدام بيانات Before. بقيت الأصول المكررة والنماذج والتحضيرات في مواقعها الموصوفة أعلاه. لا يشهد هذا الترحيل بصحة السياسات أو جودة التنبؤ أو جاهزية الإنتاج.
