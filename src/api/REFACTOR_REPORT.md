# API refactor — تقرير التنفيذ والتحقق

النطاق: تنظيم `src/api/` والاختبارات والتوثيق المتصل بها؛ بلا تدريب أو commit أو تغيير لعقود PHP وحسابات core.

- [x] تتبع `recommend_from_payloads()` إلى snapshot والمرشحين والطلب وحد التاريخ، وفحص مصادر `BACKEND_SNAPSHOT_COLUMNS`.
- [x] حفظ نسخة API الأصلية للمقارنة المباشرة، وتسجيل الاختبارات قبل نقل الكود.
- [x] نقل أدوات التحقق المشتركة إلى `validators/common.py` مع الحفاظ على هوية `ApiError` و`ValidationResult` ومسارات الاستيراد السابقة.
- [x] فصل تحقق الطالب والمواد والتاريخ إلى دوال مسماة؛ الإبقاء على ترتيب الفحص والتشخيص الجزئي والحسابات المشتركة.
- [x] اختصار `ApiService.recommend()` إلى خطوات مسماة مع المحافظة على ترتيب التاريخ والجاهزية والتزامن وسياسات الساعات.
- [x] اختبار `/recommend` مقابل المسار القديم، ثم إضافة alias إلى handler نفسه دون تغيير الإدارة أو startup.
- [x] توثيق الحقول ومسار التنفيذ ومثال اصطناعي وتشغيل push/pull في README.
- [x] مقارنة المخرجات والأخطاء واستدعاء المحرك بالنسخة الأصلية، ثم تشغيل اختبارات API والمجموعة الكاملة وفحص hashes وdiff.

مراجعة الحواف: هوية الصفوف غير المؤهلة قبل التصفية؛ نقص schema التاريخ؛ توقيت مقام المعدل؛ التعارض بعد تخصيص قيمة جزئية؛ دقة Decimal؛ رفض التزامن؛ استقلال صلاحيات الخدمة والإدارة وعمليات التاريخ.

## خط الأساس

اختبارات API الأربعة المطلوبة: `70 passed`، بلا فشل؛ تحذير واحد من Starlette بشأن httpx.

المجموعة الكاملة قبل تعديل الكود: `1369 passed, 6 subtests passed`، بلا فشل؛ التحذير نفسه.

بيئة Windows المقيدة توقفت عند `asyncio.socketpair()` في TestClient؛ اكتملت الاختبارات عند تشغيل الأمر نفسه خارج قيد sandbox. لم يُعدّل التطبيق لمعالجة هذا العائق البيئي.

## Before / After

قبل النقل كانت ملفات adapters تجمع فحص الهوية والمصدر والحساب والتحويل داخل مسارات طويلة، وكانت `recommend()` تعرض التفاصيل الزمنية والسياسات والقفل والاستجابة في جسم واحد.

بعد النقل تُقرأ خطوات بناء snapshot من `build_student_snapshot()`، وتُراجع قواعد الطالب في `validators/student.py`. تحفظ adapters ترتيب التنفيذ وتجميع التشخيص الجزئي، بينما تملك validators فحوص البيانات. أصبحت `recommend()` خمس خطوات مسماة، بلا classes جديدة.

## New Structure

```text
src/api/
├── app.py
├── schemas.py
├── service.py
├── settings.py
├── backend_client.py
├── adapters/
│   ├── __init__.py
│   ├── student.py
│   ├── courses.py
│   └── history.py
├── validators/
│   ├── __init__.py
│   ├── common.py
│   ├── student.py
│   ├── courses.py
│   └── history.py
├── student_adapter.py       # compatibility imports
├── courses_adapter.py       # compatibility imports
├── history_adapter.py       # compatibility imports
├── validation.py            # compatibility imports
├── __init__.py
├── README.md
└── REFACTOR_REPORT.md
```

ملفات `__init__.py` علامات packages لازمة للاستيراد؛ الملفات القديمة واجهات توافق ذات مالك تنفيذ واحد.

## Execution Flow

`app.recommend()` داخل `create_app()` يستقبل `RecommendationRequest` بعد المصادقة وقراءة Decimal، ثم يشغّل `ApiService.recommend()` في threadpool:

1. `_validate_recommendation_inputs()` → `validate_student()` و`validate_courses()` → adapters والتحقق المناسب.
2. `_prepare_recommendation_context()` → تحديث manager والتحقق من cutoff والوضع والجاهزية وتاريخ تدريب كل stage ووجود نسخة التاريخ الدقيقة.
3. `_build_engine_request()` → تقاطع حدود الساعات والسياسات ومجموعات المتطلبات.
4. `_run_recommendation()` → قفل الخدمة → `engine.recommend_from_payloads()` → تحرير القفل حتى عند الخطأ.
5. `_recommendation_response()` → metadata المسموح بها والتوصيات → `json_safe()` و`JSONResponse` في app.

`snapshot` يأتي من `adapt_student()` → `extract_student_info()` → `build_student_snapshot()`، و`candidates` من `adapt_courses()`. `history_as_of_part` من الطلب بعد التحقق الزمني واختيار النسخة الدقيقة، و`engine_request` من السياسات والمواد والحدود المؤكدة.

## Moved Logic / Remaining Complexity

- `validators/common.py`: نفس `ApiError` و`ValidationResult` وفحوص الأرقام والهوية والفصل وربط PHP والمصادر و`json_safe()`.
- `validators/student.py`: شكل الرد وهوية الطالب، الحقول المطلوبة والدبلوم، provenance وتوقيت GPA-credit snapshots وتعارض المصادر، schema التاريخ ومفاتيحه وقيمه، نسخة GradeScale وتعارض العداد.
- `validators/courses.py`: هوية جميع الصفوف والتكرار قبل التصفية، أهلية المواد واتساق المجموعة، السبب والنتيجة السابقة، مطابقة الكتالوج، caps وقواعد الساعات والاختياريات ونطاق المحاولات. يبقى `ATTEMPTS_COUNT + 1` وتجميع caps الدقيق والتحويل والفرز في adapter.
- `validators/history.py`: شكل Delta ومعرّفاته، استدعاء `normalize_history_delta()` الأصلي، إثبات finalization ومعاينة lineage دون نشر؛ adapter يجمع payload والنتيجة وchecks وsummary بترتيبها السابق.
- adapters تبني السجلات وتحوّل الأسماء وتستدعي `compute_student_gpa_history()` و`add_student_history_features()` ودوال التقويم الأصلية؛ لا تعيد كتابة ميزات core.
- فحوص الحقول تستدعى عند الموضع الأصلي في التحويل. بعض التعارضات تحصل بعد تخصيص قيمة جزئية، ويجب حفظ هذه القيمة وترتيب الأخطاء كما كانا.
- `_official_gpa_credits()` يجمع التحقق والمصالحة الدقيقة للمجموع الرسمي؛ الطرح جزء من إثبات الحساب الإضافي، وفصله سيكرر قراءة المصدر والتحقق منه.
- فحص finalization التشخيصي وعملية الإدارة يملكان شروطاً ورسائل مختلفة؛ لم تُوحَّد عمليات الإدارة أو تُغيَّر صلاحياتها.

## Compatibility

المسار الجديد الوحيد هو `POST /recommend`، وهو decorator إضافي للـhandler نفسه في `/api/v1/recommendations`. بقيت `GET /health` والتشخيص والإدارة والتحديث التاريخي و`create_app()` وstartup كما كانت. لا يعتمد المسار الرئيسي على `BackendClient`، الذي بقي خيار جلب مستقلًا دون مسار HTTP إضافي.

حُفظت مفاتيح البيانات الخارجية، الأخطاء والحالات وchecks والحقول غير المتاحة، دقة Decimal، والعقود الأكاديمية والزمنية. لم تتغير إعدادات الخدمة أو schemas أو منطق core.

## Verification

اختبارات alias الستة فشلت أولاً بـ404 قبل إضافة المسار. المقارنة التركيبية بعد فصل service أثبتت تطابق عبارات `recommend()` بالترتيب، وتطابق 19 دالة خدمة أخرى، وتطابق أدوات التحقق المشتركة بالكامل.

| التحقق | قبل | بعد |
|---|---|---|
| اختبارات API الأربعة المطلوبة | 70 passed | 76 passed |
| اختبارات API الأخرى والتوافق الجديد | ضمن baseline الكاملة | 112 passed |
| المجموعة الكاملة | 1369 passed، 6 subtests passed | 1409 passed، 6 subtests passed |
| الفشل | 0 | 0 |

كل تشغيل pytest النهائي له تحذير Starlette واحد عن httpx؛ ظهر في baseline نفسها. لا يوجد فشل سابق أو جديد في هذه النسخة الحالية. اختبارات جديدة: 6 حالات alias، و17 لاختبار فصل المواد والتاريخ، و17 لحدود الاستيراد والتوافق؛ الزيادة الكلية 40.

الأوامر المستخدمة:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_api_adapters.py tests/test_api_http.py tests/test_api_integration.py tests/test_api_core_extensions.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_api_academic_semantics.py tests/test_api_backend_client.py tests/test_api_cumulative_integration.py tests/test_api_history_admin.py tests/test_api_refactor_boundaries.py tests/test_api_course_history_refactor.py -q
.\.venv\Scripts\python.exe -m pytest -q
git -c safe.directory='D:/AI/Real projects/Academic_Advisor_Simple' diff --check
```

المقارنة المباشرة بالنسخة المحفوظة قبل النقل: **409 حالات، 0 اختلاف**:

- 141 حالة snapshot وتشخيص طالب، تشمل التاريخ الجزئي والكامل والمصادر والدبلوم والنسخة والتوقيت.
- 170 حالة مرشحين وقواعد تسجيل وسياسات Decimal وأهلية ومحاولات وتعارضات.
- 22 حالة توصية، تقارن الاستجابة والأخطاء وkwargs المحرك واختيار التاريخ والقفل.
- 48 حالة إدارة تاريخ تقارن الاستدعاءات وشروط العمليات والأخطاء الآمنة.
- 26 حالة تحقق تاريخ مع manager وبدونه، تشمل replay وlineage والتعارض.
- حالتان للمحرك الأصلي بمودلات وتاريخ اصطناعيين، إحداهما بميزات nullable: الاستجابات الثلاث ومصفوفات Grade/Fail في 33/47 متطابقة، ونجحت الحالتان بـ`status=ok`.

فحوص AST إضافية: جسم `_official_gpa_credits()` و`_check_source_duplicates()` و`_rules()` مطابق للأصل؛ `ApiError` و`ValidationResult` نفس كائنَي الاستيراد، لا نسخ جديدة. اختبارات استيراد interpreter جديد تؤكد استقلال adapters وvalidators وservice عن FastAPI/Pydantic وHTTP startup.

المراجعة المستقلة النهائية: لا ملاحظات تستدعي تعديل الكود. جدول README يغطّي حقول `BACKEND_SNAPSHOT_COLUMNS` الـ21 والأعمدة الأربعة المطلوبة؛ المثال الاصطناعي يجتاز `RecommendationRequest` ويعطي snapshot مطابقاً موثقاً بـ24 حقلاً وطلب محرك بقيود Decimal متطابقة. روابط التوثيق النسبية التسعة صالحة. الحقول الثلاثة الإضافية هي semester وGPA trend وmissing، وتُحسب كما كانت.

SHA-256 بعد انتهاء المجموعة الكاملة: **1320 ملفاً قبل وبعد، 0 تغيير** في `data/` و`models/` وملفات `src/` خارج `api/`، مع استبعاد bytecode. **NOT CHANGED:** البيانات الخام والأصول المحفوظة والمودلات وحزم التاريخ وكود الحسابات والتوليد والترتيب. بقيت `settings.py` و`schemas.py` أيضاً كما كانتا. `git diff --check` ناجح؛ إشعارات CRLF من Git ليست أخطاء whitespace.

خارج API والاختبارات والتوثيق المرتبط، التغيير الوحيد هو خريطة الكود المشتقة `graphify-out/` لأن `AGENTS.md` يطلب `graphify update .` بعد تعديل الكود. نجح تحديث AST المحلي بلا LLM أو API cost، وأنشأ خريطة 5512 عقدة مع عرض HTML مجمّع. لا تعني الأسماء المجمعة تحديثاً دلالياً لتوثيق المشروع.

لم يحصل تدريب أو تشغيل pipeline أو توصية حقيقية أو commit. لم تُعدّل ملفات `docs/code_walkthrough/` السابقة أو تعليقات المستخدم الموجودة مسبقاً في `app.py`.
