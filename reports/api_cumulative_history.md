# API Configuration and Cumulative Frozen History — تقرير التنفيذ

تاريخ التنفيذ: `2026-10-11`. نُفّذت الإضافات في المستودع الحالي دون إعادة تصميم API، أو تدريب، أو تشغيل توصية لطالب حقيقي، أو ترحيل/تفعيل تاريخ فعلي، أو Git commit. بقي PHP-push افتراضيًا و`pareto v1 → pareto v1` وTop 3 والعقود ذات 33/47 ميزة محفوظة.

## النتيجة وحدود الاعتماد

| الحالة | المكوّن | دليل التنفيذ وحدوده |
|---|---|---|
| PASS | إعداد الاتصال والعميل الاختياري | URLs/مهلة/token من البيئة، معاملات Student الفعلية، معاملات Courses صريحة، DNS/IP pinning وTLS ورفض SSRF/redirects؛ اختبارات نقل اصطناعي دون اتصال بالجامعة |
| PASS | المقام والمحاولات | مصدر بداية رسمي يغني عن مكمل مكرر، اشتقاق نهاية الفصل بشهادة اكتمال وقواعد جمع وزيادة GPA رسمية، رفض الغموض والتناقض؛ الحالات الجديدة والإعادات تستخدم التطبيع الحالي |
| PASS | المخزن التراكمي | baseline تراكمية 20251 معتمدة بالبصمات، ثم 20252/20253/20261، تكافؤ المجاميع/الأوزان مع مرجع اصطناعي، نسخ immutable، منع التكرار والترتيب الخاطئ |
| PASS | الإدارة والتفعيل | modes دائمة، صلاحيات مستقلة، preview/commit/activation، أحداث تثبيت موثقة، قفل OS بين العمليات، pointer ذرية، rollback، واستعادة bootstrap بعد فشل كتابة pointer |
| PASS | سلامة الخدمة السابقة | تحديث العمال الذين بدأوا قبل migration، منع استخدام النسخة قبل تفعيلها، snapshots صريحة، read-only diagnostics مستقلة، وتطابق توصية اصطناعية قبل/بعد migration مع Pareto/Pareto وTop 3 |
| PASS | المراجعة | أربع ملاحظات مهمة أُعيد إنتاجها وإصلاحها ثم راجعها وكيل مستقل؛ لا ملاحظات Critical/Important مفتوحة |
| PARTIAL | الدلالات الفعلية لتدريب `prior_total_reg_credits` | الكود ينقل `total_reg_credits` مباشرةً، لكن توقيت export التدريب نفسه يحتاج شهادة الجامعة؛ لم تتغير الحسابات أو البيانات لإخفاء هذا الاعتماد |
| PARTIAL | اتصال الجامعة والتشغيل | URLs ومعاملات Courses والمصادقة وقواعد الاستثناءات وصلاحيات PHP وTLS وSLA تحتاج إعداد الجامعة؛ الاختبارات المحلية لا تثبت جاهزية الإنتاج |
| BLOCKED | ترحيل/تفعيل baseline الحقيقية الآن | لم يقدم اعتماد محدد لاكتمال المصدر وبصمة metadata ومرجع الموافقة وتأكيد المشرف عبر المسار الإداري؛ لم تُنشأ أي نسخة تشغيلية جديدة. الإجراء الآمن منفذ ومختبر فقط |

## Before / After

| قبل الإضافة | بعد الإضافة |
|---|---|
| PHP يدفع الردين إلى API | نفس العقد الافتراضي، مع `BackendClient` اختياري للاختبار من إعدادات موثوقة |
| مقام GPA يحتاج مكملًا موثقًا مستقلًا | `TOTAL_REG_CREDITS` الرسمي يكفي عندما يثبت timing؛ المكمل يبقى اختياريًا عند غياب مصدر بداية موثوق |
| الحالة السابقة للمواد تتطلب إثباتًا منفصلًا في بعض الردود | حالة `FINISH_STATUS` الرسمية السابقة مقبولة للإعادة؛ صفر محاولات/null يصبح NEW؛ التناقض مرفوض |
| إدارة Phase 3 تنشر immutable history وتبدل مرجع المدير داخل العملية | wrapper مستقل يعيد استخدام النشر الحالي، ويفصل commit عن تفعيل pointer دائمة بين العمال |
| endpoint Delta للتحقق فقط | محفوظ بلا كتابة، مع endpoints إدارية منفصلة للتشغيل المعتمد ورفض تجاوز فصل في المخزن التراكمي |

## الملفات الدقيقة لهذه المهمة

| المجموعة | الملفات |
|---|---|
| تعديل API الحالية | `src/api/settings.py`, `app.py`, `service.py`, `schemas.py`, `student_adapter.py`, `courses_adapter.py`, `README.md` |
| وحدات جديدة | `src/api/backend_client.py`, `src/recommendation/cumulative_history.py` |
| المسارات | `src/paths.py`: إضافة `FROZEN_HISTORY_INCREMENTAL_DIR` فقط |
| اختبارات جديدة | `tests/test_api_backend_client.py`, `tests/test_api_academic_semantics.py`, `tests/test_api_history_admin.py`, `tests/test_api_cumulative_integration.py`, `tests/test_cumulative_history.py` |
| توثيق جديد | `docs/API_CONFIGURATION_AND_CUMULATIVE_HISTORY.md`, `docs/ACADEMIC_DATA_SEMANTICS_AUDIT.md`, `reports/api_cumulative_history_plan.md`, هذا التقرير |
| توثيق معماري محدث | `plan_explanation/PHASE_03_HISTORY_DELTA_SAVE_ATOMIC_SWAP.md`, `plan_explanation/PHASE_07_MANIFEST_POLICIES_REVALIDATION.md` |
| Graphify | AST update في `graphify-out/` مع backup تلقائي في `graphify-out/2026-10-11/`؛ 3722 nodes، 9478 edges، 226 communities؛ دون LLM |

لم تتغير `history_update.py`, `frozen_history.py`, `temporal_features.py`, `two_stage_engine.py`, `recommend_local.py` أو عقود المودلات في هذه المهمة. تغييرات تصحيح اسم `capacity_63` السابقة كانت موجودة قبل البداية، وحُفظت دون rollback أو commit؛ تظهر في Git diff الكلي ولا تنتمي إلى هذه الإضافة.

## عقود التشغيل

[العمارة والإعدادات وعقد PHP الإداري](../docs/API_CONFIGURATION_AND_CUMULATIVE_HISTORY.md) يحدد كل متغيرات البيئة، المسارات، الأدوار، تسلسل manual/automatic، layout، سياسة rollback والتوافق. [تدقيق الدلالات الأكاديمية](../docs/ACADEMIC_DATA_SEMANTICS_AUDIT.md) يحدد حقول GPA وشهادة source/timing وحالات المحاولات والمصادر غير المكتملة.

- `manual` الافتراضي يُكتب في `control.json` عند أول عملية إدارية؛ الإعداد المحفوظ يتقدم على افتراضي البيئة بعد restart.
- initialize يحتاج source root من البيئة فقط، وSHA-256 لـ`as_of_20251/metadata.json`، ومرجع اعتماد، و`confirmation:true` و`cumulative_history_confirmed:true`. وجود سوابق ومجاميع متسقة لا يثبت اكتمال الجامعة منفردًا؛ يسجل `admin_attested`.
- commit ينشئ نسخة مكتملة دون السماح بخدمتها. activate يتحقق من hash والتوافق والـlineage ثم يكتب pointer و`activated_versions` معًا ذريًا.
- في normal لا يمكن تخطي pointer بعد rollback؛ backtesting الصريح والمفعل يستطيع قراءة نسخة سبق تفعيلها، ولا يستطيع استخدام نسخة لم تُفعّل قط. النسخ السابقة لـ20251 تبقى محددة بالـcutoff نفسه من المصدر القديم للقراءة فقط.
- `disabled` يمنع initialization والتحديث والتفعيل؛ تغيير mode وstatus والتحقق القديم يظلون متاحين للدور المخول. auto يحتاج مفتاح finalization مستقلًا ومرجع تثبيت موثوقًا؛ وصول البيانات وحده لا يثبت التثبيت.
- فشل البناء أو التوافق يحفظ pointer السابق. فشل كتابة pointer أثناء bootstrap يسمح بإعادة اعتماد النسخة المطابقة فقط، دون إعادة كتابتها. إذا تعذر التخزين نفسه قد يتعذر حفظ سجل الفشل؛ يبقى المؤشر السابق محفوظًا.
- القفل مثبت على نظام ملفات محلي بين threads/processes، وليس ضمانًا لتخزين موزع متعدد hosts.

## اختبارات القبول

| البنود المطلوبة | الاختبارات |
|---|---|
| URL/timeout/token، PHP-push ثابت، SSRF/redirects/TLS/DNS | `test_api_backend_client.py` |
| مقام رسمي، مثال 129/18، ساعات مكتملة ليست مقامًا، غموض/تعارض/توقيت، تكافؤ الميزة | `test_api_academic_semantics.py` مع اختبارات الحساب الأصلي الحالية |
| NEW/FAILED/WITHDRAWN، نقص الحالة والتناقض | `test_api_academic_semantics.py` واختبارات الإعادة الحالية |
| baseline تراكمية 20251، sequence إلى 20261، hashes/aggregate parity، idempotence/order، rollback/recovery/failures | `test_cumulative_history.py` |
| modes/auth/finalization، فصل commit/activation، workers، readiness، specialty، pointer تالفة، read-only بلا كتابة | `test_api_history_admin.py`, `test_api_cumulative_integration.py` |
| CLI وTwo-Stage/Pareto/Top 3/33 و47 وعدم regression | اختبارات API الحالية وTwo-Stage/History، وCLI `--help`، والمجموعة الكاملة |

كل المدخلات الجديدة اصطناعية. لم تُستخدم ملفات الطالب الشخصية كـfixtures، ولم يحدث اتصال مباشر بالجامعة. جولات RED→GREEN موثقة أثناء التنفيذ للعميل والإدارة والدلالات والتاريخ وإصلاحات المراجعة.

## نتائج التحقق النهائية

| الفحص | النتيجة النهائية |
|---|---|
| المركّزة، خمسة ملفات جديدة | **107 passed** في 10.32s |
| المرتبطة، API/History/Temporal/Two-Stage/Training config | **503 passed، 6 subtests passed** في 119.08s |
| الكاملة `python -m pytest -q --tb=short` | **1369 passed، 6 subtests passed** في 269.59s |
| CLI `python -m src.recommend_local --help` | PASS، exit 0؛ لا توصية أو تدريب |
| SHA-256 لكل ملفات `data/` و`models/` | **1230 قبل / 1230 بعد؛ 0 تغيّر، 0 حذف، 0 إضافة** |
| مخزن التشغيل الجديد | `data/artifacts/history_incremental/` غير منشأ؛ لا migration أو activation حقيقية |
| Git | HEAD بقي `359146880d3717169d998916a39309dd89481c7b`، لا commit؛ التغييرات السابقة محفوظة |
| Graphify AST | PASS، 3722 nodes و9478 edges و226 communities؛ query بعد التحديث وجد `BackendClient` و`CumulativeHistoryStore` واختبارات التفعيل |

كل جولات الاختبار النهائية انتهت دون failures أو skips. بقي تحذير واحد معروف من Starlette/httpx؛ لم نغيّر تبعيات الاختبار خارج نطاق المهمة. فحص Git لم يجد تغييرات في core history أو temporal features أو Two-Stage engine أو CLI.

أدلة التشغيل المحلية في `.pytest_cache/cumulative-api-audit/`: `focused-final.txt`, `related-final.txt`, `full-final.txt`, `cli-help.txt`, `graphify.txt`, `protected_comparison.json`, `protected_before.json`, `protected_after.json`, `baseline.json`, `git_after.json`. مجلد الأدلة محلي وغير متعقب في Git.

فشل خط الأساس القديم `capaciy_63` مقابل `capacity_63` كان قد أُصلح في المهمة السابقة؛ لا يُعاد تصنيفه كفشل جديد. لا اعتماد لإنتاج أو أداء إنتاج بمجرد PASS للاختبارات الاصطناعية.
