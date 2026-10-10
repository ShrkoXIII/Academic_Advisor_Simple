# دمج Academic Advisor Backend API

طبقة `src/api/` تستقبل ردود الجامعة وتتحقق منها وتحولها إلى `{snapshot, candidates}` وقيود المحرك الحالي. لا تعيد تدريب المودلات ولا تضيف أعمدة إلى عقد الميزات. `pareto v1 → pareto v1` هو اختيار API، وتبقى بوابة اعتماد الـmanifest الأصلية إلزامية. `top_k=3` افتراضيًا؛ الحد المتوافق مع shortlist هو 50.

## التشغيل المحلي

من جذر المشروع، باستخدام البيئة الافتراضية:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[api,api-test]'
# اضبط ADVISOR_API_KEY وADVISOR_ADMIN_API_KEY في بيئة الخدمة، بقيمتين منفصلتين.
.\.venv\Scripts\python.exe -m uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

`src.api` و`src.api.service` يعملان دون FastAPI/Pydantic. استيراد `src.api.app` يحتاج extra `api`، لكنه لا يحمل الأصول. `create_app()` يُنشئ خدمة، و`lifespan` يحمل catalog وGradeScale وFrozen History والمودلات بصورة مستقلة. جميع المسارات تأتي من `src.paths`، دون paths خاصة في HTTP.

التشغيل متعدد workers والميزانية وSLA وحد مواد الإنتاج لم تُعتمد. يوجد طلب inference واحد داخل كل process؛ طلب متزامن يُرفض بـ`503 INFERENCE_BUSY`. هذا لا يحدد مهلة إنتاج ولا يعالج الكلفة الأسية للبحث.

## مسؤولية PHP وربط البيانات

PHP يوثق المستخدم ويثبت صلاحياته على الطالب والاختصاص، ثم يجلب Student API وCourses API باستخدام الهوية والفصل المطلوبين. يُرفق سياق **كل عملية جلب** بصورة مستقلة. الخدمة Python تقارن السياقين بالطلب وبأي هوية في الردود؛ مفتاح الخدمة يوثق PHP، ولا يحل محل صلاحيات المستخدم الجامعية.

كل POST غير إداري يحتاج `X-API-Key: <ADVISOR_API_KEY>`. Delta يحتاج مفتاح `ADVISOR_ADMIN_API_KEY` المنفصل؛ مفتاح الخدمة لا يسمح به. `GET /health` متاح دون مفتاح ولا يعرض أسرارًا أو paths. الطلب عبر شبكة الخدمة يحتاج إعداد TLS وضبط السجلات لدى مشغّل PHP/proxy؛ هذه الطبقة لا تنشر خدمة خارجية.

المفاتيح المشتركة للطلبات:

```json
{
  "student_id": "student-synthetic",
  "degree_id": "13.111",
  "part_id": 20251,
  "source_contexts": {
    "student": {"student_id": "student-synthetic", "degree_id": "13.111", "part_id": 20251},
    "courses": {"student_id": "student-synthetic", "degree_id": "13.111", "part_id": 20251}
  }
}
```

كل ID سلسلة، بما فيها لاحقة مثل `.111`؛ semester يقبل سلسلة أو عددًا صحيحًا. يتطلب تحقق الطالب سياق `student` ورد `student_api_response`، وتحقق المواد سياق `courses` ورد `courses_api_response`؛ التوصية تتطلب الاثنين. لا يُقبل سياق واحد كدليل على جلب الرد الآخر.

شكل Student: `{success: true, data: {studentDegreeInfo: {...}, studentSummaryInfo: [...]}}`. تطابق هوية `studentDegreeInfo` إلزامي، وتُراجع أيضًا أي هوية في غلاف الرد أو root data. كل سجل تاريخي يطابق الطالب والاختصاص، وفصله أقدم من الهدف؛ aliases الفصل داخل السجل يجب أن تتفق. فحص الهوية يشمل كل السجلات حتى عند نقص schema في سجل سابق.

شكل Courses: `{success: true, data: {registserRule: {...}, availableCourses: [...], allowRegisterAllOptional: "Y"|"N"}}`. يحافظ العقد على تهجئة `registserRule` الفعلية. تفحص أي هوية في root data أو أي مادة قبل التصفية. المثال الأصلي لا يحمل هذه الهوية: مستوى التحقق `php_attested`، وليس إثباتًا من محتوى Courses وحده. لا يمكن Python أن يثبت صحة السياق الذي يشهد به PHP دون مصدر جامعي إضافي.

## المدخلات الناقصة ومصادرها

`studentDegreeInfo` يوفر IDs، `START_AGPA_POINTS`، `START_TOTAL_IN_COURSES`، `START_TOTAL_IN_CREDITS`، `DEGREE_CREDITS_COUNT`. الدبلوم مطلوب عبر `diploma_gpa`/`DIPLOMA_GPA` و`diploma_type_id`/`DIPLOMA_TYPE_ID`؛ aliases قابلة للضبط.

القيم الإضافية في `integration_context.student_values`:

| المفتاح | الدلالة |
|---|---|
| `current_gpa_credits` | المقام الرسمي للساعات الداخلة في معدل البداية؛ مطلوب، ويمكن أن يكون صفرًا رسميًا |
| `prior_total_reg_courses`، `prior_total_reg_credits` | إجمالي التسجيل قبل فصل الهدف، وفق دلالة cleaning الحالية |
| `prior_total_fail_courses`، `prior_total_fail_credits` | مجاميع الرسوب عند بداية الفصل |
| `prior_registered_semesters` | عداد الفصل السابق الرسمي، وليس عدد صفوف summary |

كل قيمة `{value: ..., source: "official_source_name", as_of_part: 20243}`. المصدر غير فارغ والفصل قبل الهدف. لا يقبل Adapter حقول ميزات مشتقة اعتباطية. القيم الأصلية المكافئة، مثل `CURRENT_GPA_CREDITS` و`TOTAL_FAIL_*` و`PRIOR_TOTAL_*`، يجب أن تطابق القيم الإضافية. قيم `TOTAL_REG_*` غير المؤكدة زمنيًا لا تُستبدل تلقائيًا بالمجاميع السابقة؛ تُظهر تشخيص `registration_totals_require_timing_contract`.

لا يستخدم `129` أو `108` أو مجموع `111` مقامًا تلقائيًا. Fixtures النجاح تعطي `108` من مصدر **اصطناعي صريح** لاختبار الربط؛ ليست اعتمادًا للمثال الحقيقي. معلومات الدبلوم والمقام والعدادات وسياسات التسجيل في fixture هي بيانات اختبار.

`studentSummaryInfo` يحتاج `STUDENT_STATUS_ID, STUDENT_ID, DEGREE_ID, PART_ID, GPA_POINTS, SEMESTER_REG_COURSES`. نتائج الطالب في **فصل الهدف** لا تدخل الحساب. الفصول غير المسجلة تحفظ في الجدول، وGPA السابق يأتي من registered shifts الأصلي. `observed_gap_semesters` يعيد استخدام calendar الأصلي، ويحتاج معرفة التسجيل الحالي وآخر تسجيل سابق. ساعاته الموجبة تثبت وجود تسجيل؛ الصفر لا يثبت عدد المواد بسبب مواد zero-credit.

عند وجود جميع أعمدة الدالة الأصلية `last_enrolled_gpa, total_reg_courses, total_reg_credits, total_fail_courses, total_fail_credits, reg_total_semesters`، تستخدم `add_student_history_features()`، ويُراجع العداد المشتق مقابل المصدر الإضافي. عند عدم وجودها تستخدم فقط `compute_student_gpa_history()` المشترك النقي. لا يجري تمرير schema جزئية إلى الدالة الكاملة.

المجهول لا يصير صفرًا. يقبل المحرك الحالي null في تاريخ GPA والعدادات حيث يسمح عقد snapshot بذلك. نقص الدبلوم/المقام يُرفض، ونقص schema أو gaps اللازمة يحجب التوصية. واجهات التحقق تعرض `unavailable_fields` و`partial`، ولا تعيد snapshot أو المدخلات الخام.

## المواد والسياسات

الأرقام finite وغير سالبة؛ `ATTEMPTS_COUNT` عدد صحيح والمحاولة الحالية +1. على PHP تأكيد أنه عداد جميع التسجيلات السابقة للمادة عبر الاختصاصات، قبل تصفية finish status وGPA inclusion، وليس عداد الرسوب. يتطلب الكتالوج هوية degree+course، ويثبت credits وrequirement type/year/semester/credits_count. `plan_course_type_id` يأتي من `course_type_id` بالكتالوج؛ لا يُستنتج من requirement type.

الحقول `IS_REQUESTABLE` و`ALLOW_REGISTER` تحتاج Y/N صريحًا. الصفوف غير المؤهلة لا تدخل المرشحين، لكن هويتها وتعارض نسخ المادة يُفحصان أولًا. التكرار المطابق يزيل نسخة واحدة فقط؛ المتعارض يُرفض حتى إذا كانت نسخة غير مؤهلة. `STATUS_REASON_CODE=EXCEPTION` يحتاج course ID في التفويض الصريح. لا يستنتج `FAILED` أو `WITHDRAWN` من عدد المحاولات.

الحالة السابقة تأتي من `FINISH_STATUS` مع `LAST_REGISTER_SEMESTER_ID` قبل الهدف، أو `integration_context.previous_course_statuses[course_id]` بقيمة ومصدر و`as_of_part`. تُراجع المصادر معًا إن حضرا. New مع محاولة سابقة أو حالة معادة دون محاولة سابقة تعارض.

`integration_context.registration_policy` مطلوب للاستدلال؛ يمثل تأكيد PHP للسياسات الجامعية:

```json
{
  "source": "official_registration_policy",
  "part_id": 20251,
  "requirement_group_modes": {"4.111": "strict_remaining", "5.111": "strict_remaining", "6.111": "strict_remaining"},
  "group_overflow_credits": {},
  "allow_register_all_optional_confirmed": true,
  "approved_exception_course_ids": [],
  "allowed_failed_repeat_credits": 6,
  "allowed_withdrawn_repeat_credits": 3,
  "attempts_scope_confirmed": true,
  "load_profile": "study"
}
```

هذه قيم توضيحية وليست سياسات افتراضية. كل مجموعة مرشحة تحتاج mode مؤكدًا:

| mode | القيد |
|---|---|
| `strict_remaining` | `CREDITS_COUNT - REQUIREMENT_PASSED_CREDITS`؛ passed أكبر من maximum تعارض |
| `approved_overflow` | `max(0, maximum + approved overflow - passed)`؛ مقدار overflow صريح |
| `unbounded` | تأكيد عدم وجود cap لهذه المجموعة؛ يمثله المحرك بمجموع ساعات مرشحيها دون تكرار |

الهوية الداخلية للمجموعة canonical JSON `[degree_id, REQUIREMENT_ID]`. لا تدخل هوية المجموعة أو caps في مصفوفة المودل. تصنيفات `plan_requirement_type_id` تبقى نفسها، وcap التصنيف الداخلي يساوي كل ساعات مرشحيه؛ caps الأعمال الفعلية مستقلة حسب المجموعة. لذلك ثلاث مواد من ساعتين لا تمر عند بقاء أربع ساعات.

`allowRegisterAllOptional` محفوظ؛ Y يحتاج تأكيد تفسيره، ولا يعطل caps. `MAX_NEW_COURSES` قيد اختياري عند وجوده، وغيابه يعني عدم إدخال cap جديد. `allowed_withdrawn_repeat_credits` يمكن إغفاله وفق العقد القديم؛ failed cap صريح إلزامي. `load_profile` يختار study أو graduation حسب تأكيد الجامعة، وتُراجع جميع أزواج min/max.

## التوصية والتاريخ

التوصية تضيف `history_as_of_part` المطلوب، و`target_credits` أو `min_credits` مع `max_credits`، و`top_k` الاختياري، و`mode` الاختياري. Exact وRange متنافيان. يُحسب تقاطع المطلوب مع مجال التسجيل المؤكد، ويستخدم الحد الأعلى الفعلي هدفًا دقيقًا؛ `12..18` يعني 18 دون نزول إلى 17 عند غياب خطة.

`mode=normal` افتراضي: cutoff يساوي `previous_academic_part(part_id)`. `mode=backtesting` يحتاج أيضًا `ADVISOR_ENABLE_BACKTESTING=true`. الأقدم فقط مسموح؛ الهدف والمستقبل ممنوعان. target يجب أن يلي cutoff التدريب في كل stage. الحزمة المحددة يجب أن تكون موجودة ومتوافقة، دون fallback إلى أحدث حزمة. caching يحفظ snapshot الحزمة المطلوبة، وتبقى مثبتة أثناء الطلب.

الإضافات اختيارية في Core؛ الاستدعاء القديم دون `history_as_of_part` و`allow_older_history` يحتفظ بسلوكه السابق. HTTP يمررهما صراحة دائمًا. الرد يسجل mode وcutoff، وحالة `input_validation` و`unavailable_student_fields` عندما يدعم العقد null، وmetadata عامة فقط؛ لا IDs شخصية ولا paths ولا raw data. plan IDs وcourse IDs وأسماء المواد ومقاييس التوصية بيانات مخرجات أكاديمية مطلوبة.

## التحقق وhealth والأخطاء

كل تحقق يعطي `validation_status: valid|partial|invalid`، و`validation_completed`، و`checks`، و`unavailable_fields`، وأخطاء محددة وملخصًا عدديًا. التحقق من الطالب والمواد مستقل عن مودلات inference وFrozen History؛ غياب catalog أو GradeScale يجعل فحصهما `unavailable` ويمنع وصف النتيجة بأنها كاملة.

`/health` يعرض بصورة منفصلة `api_health`, `model_readiness`, `history_readiness`, `catalog_readiness`, `grade_scale_readiness`, `recommendation_readiness`. صحة HTTP لا تثبت وجود الحزمة المطلوبة لفصل معين أو صلاحية مدخلات طالب معين.

| HTTP | أمثلة |
|---|---|
| 200 | توصية أو no_feasible_plan، أو تشخيص valid/partial مع `validation_completed=false` للجزئي |
| 401 / 403 | مفتاح مفقود / غير مخول، أو استخدام مفتاح الخدمة في Delta |
| 422 | `MISSING_SOURCE_CONTEXT`, `IDENTITY_MISMATCH`, `MISSING_FIELD`, `FUTURE_SOURCE`, `INVALID_HISTORY_CUTOFF`, `PERFORMANCE_TEST_LIMIT` |
| 409 | تكرار متعارض أو `DELTA_CONFLICT` |
| 503 | `DEPENDENCY_UNAVAILABLE`, `HISTORY_UNAVAILABLE`, `AUTH_UNCONFIGURED`, `INFERENCE_BUSY` |
| 500 | `INTERNAL_ERROR` برسالة عامة؛ الاستثناء الأصلي لا يصعد إلى سجل ASGI |

Pydantic errors لا تعيد input أو arbitrary dictionary keys. JSON decimals تحفظ عند parsing قبل Pydantic؛ لا تتحول الساعات عبر float. NaN/Infinity ممنوعة.

## History Delta

```json
{
  "part_id": 20251,
  "rows": [{"degree_id": "D", "course_id": "C00", "faculty_id": "F", "plan_requirement_type_id": "R", "course_credits": 3,
            "count": 20, "fail_count": 0, "retake_count": 0, "mark_sum": 1800, "attempt_sum": 20}],
  "finalization": {"finalized_part_id": 20251, "approval_reference": "official_finalization_reference"}
}
```

`finalization` اختياري للمعاينة. بدونه الفحص `unavailable`، ومعه `admin_attested`؛ إثبات التثبيت الفعلي مسؤولية الإدارة الجامعية، وليس نتيجة نجاح المجاميع. بدون تاريخ محمل يظل فحص schema والمجاميع والبصمة متاحًا، بينما lineage/replay/order غير متاحة والنتيجة partial. مع تاريخ محمل يُعرض base hash وcutoff وnew_delta/already_applied؛ المختلف لنفس الفصل أو out-of-order يُرفض 409. الفحص بالنسبة إلى snapshot المدير المحمّل؛ تغييرات خارج العملية تحتاج إعادة تحميل الخدمة.

هذا المسار لا يكتب ملفًا ولا ينشر ولا يفعل تاريخًا. Core القديم الذي يحتاج `finalized=True` للتحديث بقي كما هو. المجاميع الحالية تحتوي marks/counts/attempts فقط؛ لا تقدير `points_sum`. loader الرسمي يرفض أي bundle يتطلب عقد نقاط/ميزات إضافية لا يوفرها المسار الحالي.

## خريطة الميزات الحالية

| الميزات | المصدر والحساب |
|---|---|
| `gpa_prev_1`, `gpa_prev_2`, `gpa_trend_delta`, `gpa_trend_missing` | helper registered GPA shifts الأصلي، مع null حقيقي عند تاريخ ناقص |
| `start_agpa_points`, `start_total_in_courses`, `start_total_in_credits` | حقول START الفعلية |
| `prior_total_reg_courses`, `prior_total_reg_credits`, `prior_total_fail_courses`, `prior_total_fail_credits` | مصادر beginning-of-semester موثقة؛ لا تصحيح افتراضي لفرق مجاميع API |
| `prior_fail_credit_ratio` | fail credits / reg credits؛ مقام صفر أو مجهول يعطي null |
| `prior_registered_semesters` | المصدر الرسمي أو counter السابق من schema كاملة، دون عد صفوف مفترض |
| `observed_gap_semesters` | calendar الأصلي وآخر فصل مسجل والتسجيل الحالي |
| `diploma_gpa`, `diploma_type_id` | الدبلوم الحقيقي عبر aliases موثقة |
| `degree_credits_count` | degree information |
| `course_credits`, `attempt_number` | API finite credits وprevious attempts +1 |
| `plan_course_type_id`, `plan_requirement_type_id`, `plan_year_order`, `plan_semester_order`, `plan_credits_count` | properties مراجعَة مع كتالوج الاختصاص؛ course type من catalog وحده |
| `grade_version_id`, `part_semester` | الطالب مع تحقق GradeScale؛ semester من الهدف |
| `course_history_avg_mark`, `course_history_fail_rate`, `course_history_avg_attempt`, `course_history_retake_rate`, `course_history_effective_support`, `course_history_fallback_level`, `course_history_missing` | Frozen History واحدة، apply الأصلي (7 ميزات) |
| `plan_course_count`, `plan_total_credits`, `plan_credit_weighted_fail_rate`, `plan_credit_weighted_avg_mark`, `plan_credit_weighted_avg_attempt`, `plan_difficulty_credit_load` | حسابات السياق الأصلية للخطط المدرجة في shortlist |
| `peer_course_count`, `peer_total_credits`, `peer_credit_weighted_fail_rate`, `peer_credit_weighted_avg_mark`, `peer_credit_weighted_avg_attempt`, `peer_difficulty_credit_load`, `peer_max_fail_rate`, `peer_difficulty_missing` | السياق الأصلي دون المادة الحالية (8 ميزات peer) |

المجموع 47. Stage 1 يستخدم 33 بدون 14 plan/peer، وStage 2 يستخدم47 بعد shortlist فقط. `current_gpa_credits` وgroup identity وcaps ليست ميزات مودل.

## إعداد اختبار الأداء

```text
ADVISOR_PERFORMANCE_TEST_MODE=true
ADVISOR_PERFORMANCE_TEST_MAX_CANDIDATES=17
```

17 مثال قابل للتغيير، وليس default. تفعيل الوضع دون cap موجب صريح خطأ إعداد. خارج الوضع لا يطبق cap حتى إن كانت قيمة البيئة موجودة. التجاوز يرفض التوصية **كاملة**؛ واجهات التحقق تحلل كل المواد. حدود الأداء الحقيقية `UNRESOLVED`.

الإعدادات الأخرى: `ADVISOR_ENABLE_BACKTESTING` افتراضي false، `ADVISOR_DIPLOMA_GPA_ALIASES` و`ADVISOR_DIPLOMA_TYPE_ALIASES` قوائم CSV. لا تحفظ الأسرار أو ملفات طلبات الطلاب في Git أو logs.

## التحقق

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_api_adapters.py tests/test_api_http.py tests/test_api_integration.py tests/test_api_core_extensions.py -q
.\.venv\Scripts\python.exe -m pytest -q
graphify update .
```

في بيئة sandbox الحالية يلزم تشغيل اختبارات HTTP خارج sandbox لأن asyncio socketpair المحلي يتوقف داخله. Fixtures داخل `tests/fixtures/` منقحة؛ النجاح يعتمد على مصادر وسياسات اصطناعية معلنة. نجاحها لا يثبت بيانات المثال الحقيقي أو أداء الإنتاج. راجع [تقرير PASS/PARTIAL/BLOCKED](../../reports/backend_api_integration.md) للنتائج الفعلية وفشل baseline وبصمات الأصول.
