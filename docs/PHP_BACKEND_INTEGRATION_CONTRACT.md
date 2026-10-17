# عقد تكامل PHP مع Academic Advisor

يرسل PHP معلومات الطالب والمواد في طلبين مستقلين مرتبطين بـ`request_id`. آخر مكوّن يصل ويُكمل الزوج يشغّل `ApiService.recommend()` مرة واحدة؛ النتيجة هي رد التوصية الحالي. تحديث Frozen History مسار إداري مشترك عند تثبيت فصل، ويُنفّذ مستقلًا عن طلبات الطلاب.

جميع الأمثلة هنا اصطناعية. استخدم URL الخدمة والأسرار والمصادر الجامعية الفعلية من إعداد النشر. لا ترسل `owner` أو URL أو path داخل JSON، ولا تضع PII في `request_id` أو السجلات.

## المسارات والاعتماد

أرسل `X-API-Key` في كل مسار محمي. مفتاح الخدمة القديم `ADVISOR_API_KEY` يبقى صالحًا ويمثل caller باسم `legacy`. يمكن ضبط `ADVISOR_SERVICE_KEYS` كـJSON من `caller_id` إلى مفتاح مستقل لكل جهة؛ PHP يستخدم مفتاح جهته في header نفسه، وPython يستخرج الملكية منه. مشاركة مفتاح واحد تعني مشاركة ملكية الطلبات؛ لا تفصل جهتين تشتركان في السر نفسه.

| Method وURL | المفتاح | الطلب | الرد |
|---|---|---|---|
| `POST /api/v1/recommendation-inputs/student` | service | `StudentInputRequest` أدناه | `202` عند pending/processing؛ `200` لنتيجة التوصية المكتملة |
| `POST /api/v1/recommendation-inputs/courses` | service | `CoursesInputRequest` أدناه | السلوك نفسه، بأي ترتيب وصول |
| `GET /api/v1/recommendation-requests/{request_id}` | service وصاحب الطلب نفسه | دون body | `202` للحالة المنتظرة، `200` لغلاف النتيجة المكتملة؛ لا inference |
| `POST /recommend` و`POST /api/v1/recommendations` | service | `RecommendationRequest` القديم، بالمكوّنين معًا | عقد التوصية القديم محفوظ |
| `POST /api/v1/inputs/student/validate` و`POST /api/v1/inputs/courses/validate` | service | عقد التحقق القديم | تشخيص للقراءة فقط؛ لا تخزين ولا توصية |

المصدر: [schemas.py](../src/api/schemas.py)، وhandlers `student_input/courses_input/recommendation_request` في [app.py](../src/api/app.py)، والدالتان `submit_recommendation_input()` و`lookup_recommendation_request()` في [service.py](../src/api/service.py).

## تطابق المكوّنين

يجب أن يتطابق `request_id/student_id/degree_id/part_id` وcaller في الطالب والمواد. `request_id` من 1 إلى 128 محرفًا، يبدأ بحرف لاتيني أو رقم، والباقي حروف/أرقام أو `_ . -`. IDs الأكاديمية سلاسل؛ فصل `part_id` يقبل عددًا صحيحًا أو سلسلة.

الطالب يحمل `source_contexts.student`، والمواد تحمل `source_contexts.courses`. كل سياق يثبت هوية **عملية الجلب الخاصة به**. إذا أرسل أحد المكوّنين سياق المكوّن الآخر أو أي قيمة متداخلة في `integration_context`، يجب أن تتفق جميع القيم المتداخلة؛ التعارض يُرفض، ولا يحل السياق مكان شهادة المصدر الأصلي.

`recommendation` موجود في طلب الطالب فقط: `history_as_of_part` و`target_credits` **أو** `min_credits/max_credits`؛ الخيارات متنافية. `top_k` افتراضيًا 3 وفي المجال 1..50، و`mode` افتراضيًا `normal`. الساعات الدقيقة تُرسل كسلاسل عددية في أمثلة PHP لتجنب المرور عبر float.

مصادر `student_values/total_reg_credits_source` تخص الطالب، و`registration_policy/previous_course_statuses` تخص المواد. تبقى validators الحالية هي المرجع للتحقق الأكاديمي؛ لا يكتفي التخزين بصحة schema لتجاوز نقص المصدر.

## A. إرسال معلومات الطالب

`POST /api/v1/recommendation-inputs/student` — هذا JSON كامل صالح للعقد، مع dependencies اصطناعية مطابقة عند الاختبار. يفترض تفعيل التاريخ المعتمد حتى `20261` قبل توصية `20262`.

```json
{
  "request_id": "rec-example-20262-001",
  "student_id": "student-example",
  "degree_id": "degree-example",
  "part_id": 20262,
  "recommendation": {
    "history_as_of_part": 20261,
    "target_credits": "3",
    "top_k": 3,
    "mode": "normal"
  },
  "source_contexts": {
    "student": {"student_id": "student-example", "degree_id": "degree-example", "part_id": 20262}
  },
  "student_api_response": {
    "success": true,
    "data": {
      "studentDegreeInfo": {
        "STUDENT_STATUS_ID": "status-target",
        "STUDENT_ID": "student-example", "DEGREE_ID": "degree-example",
        "STATUS_SEMESTER_ID": "20262", "FACULTY_ID": "faculty-example",
        "GRADE_VERSION_ID": "3.111", "START_AGPA_POINTS": "2.8",
        "START_TOTAL_IN_COURSES": "24", "START_TOTAL_IN_CREDITS": "72",
        "TOTAL_REG_CREDITS": "75", "TOTAL_FAIL_COURSES": "1",
        "TOTAL_FAIL_CREDITS": "3", "SEMESTER_REG_COURSES": "6",
        "SEMESTER_REG_CREDITS": "18", "DEGREE_CREDITS_COUNT": "180",
        "diploma_gpa": "92", "diploma_type_id": "diploma-example"
      },
      "studentSummaryInfo": [
        {"STUDENT_STATUS_ID": "status-prior-1", "STUDENT_ID": "student-example", "DEGREE_ID": "degree-example",
         "PART_ID": "20253", "GPA_POINTS": "2.6", "SEMESTER_REG_COURSES": "5"},
        {"STUDENT_STATUS_ID": "status-prior-2", "STUDENT_ID": "student-example", "DEGREE_ID": "degree-example",
         "PART_ID": "20261", "GPA_POINTS": "3.1", "SEMESTER_REG_COURSES": "2"}
      ]
    }
  },
  "integration_context": {
    "total_reg_credits_source": {
      "source": "synthetic_official_gpa_ledger", "target_part": 20262,
      "as_of_part": 20261, "timing": "beginning_of_semester",
      "rules_reference": "synthetic_rules_v1"
    },
    "student_values": {
      "prior_total_reg_courses": {"value": 25, "source": "synthetic_ledger", "as_of_part": 20261},
      "prior_total_fail_courses": {"value": 1, "source": "synthetic_ledger", "as_of_part": 20261},
      "prior_total_fail_credits": {"value": "3", "source": "synthetic_ledger", "as_of_part": 20261},
      "prior_registered_semesters": {"value": 4, "source": "synthetic_ledger", "as_of_part": 20261}
    }
  }
}
```

عند غياب المواد يعود `202 Accepted`:

```json
{
  "request_id": "rec-example-20262-001",
  "status": "pending",
  "received": ["student"],
  "missing": ["courses"]
}
```

`75` ساعات GPA موثقة عند بداية الفصل؛ `72` ساعات إكمال، فلا تستبدل بها المقام. `source/rules_reference` الاصطناعيان في المثال خاصان بالاختبار؛ في الإنتاج يأتيان من مصدر جامعي معتمد.

## B. إرسال المواد

`POST /api/v1/recommendation-inputs/courses` — نفس الهوية و`request_id` ونفس مفتاح caller. تهجئة `registserRule` محفوظة.

```json
{
  "request_id": "rec-example-20262-001",
  "student_id": "student-example",
  "degree_id": "degree-example",
  "part_id": 20262,
  "source_contexts": {
    "courses": {"student_id": "student-example", "degree_id": "degree-example", "part_id": 20262}
  },
  "courses_api_response": {
    "success": true,
    "data": {
      "registserRule": {
        "LOAD_TYPE": "CREDIT",
        "MIN_CREDITS": "3", "MAX_CREDITS": "18",
        "MIN_STUDY_CREDITS": "3", "MAX_STUDY_CREDITS": "18",
        "GRAD_MIN_LIMIT": "3", "GRAD_MAX_LOAD": "18",
        "MAX_NEW_COURSES": "2"
      },
      "allowRegisterAllOptional": "N",
      "availableCourses": [
        {
          "COURSE_ID": "course-example", "COURSE_NAME_SL": "Synthetic course",
          "COURSE_CREDITS": "3", "REQUIREMENT_TYPE_ID": "R",
          "REQUIREMENT_ID": "group-example", "CREDITS_COUNT": "12",
          "REQUIREMENT_PASSED_CREDITS": "3", "IS_REQUESTABLE": "Y",
          "ALLOW_REGISTER": "Y", "STATUS_REASON_CODE": "REQUESTABLE",
          "YEAR_ORDER": "1", "SEMESTER_ORDER": "1",
          "ATTEMPTS_COUNT": "0", "FINISH_STATUS": null,
          "LAST_REGISTER_SEMESTER_ID": null
        }
      ]
    }
  },
  "integration_context": {
    "registration_policy": {
      "source": "synthetic_registration_policy", "part_id": 20262,
      "requirement_group_modes": {"group-example": "strict_remaining"},
      "allowed_failed_repeat_credits": "0", "allowed_withdrawn_repeat_credits": "0",
      "attempts_scope_confirmed": true, "load_profile": "study"
    }
  }
}
```

المثال يفترض كتالوجًا اصطناعيًا فيه المادة بنفس الخصائص ونوع `course_type_id="3"`. `ATTEMPTS_COUNT=0` و`FINISH_STATUS=null` يعطيان `NEW` ومحاولة `1`. المواد المكررة تحتاج الحالة السابقة المعروفة أو مصدرًا موثقًا مستقلًا؛ العداد وحده لا يعني رسوبًا.

إذا وصلت المواد أولًا، يعود pending مع `received=["courses"]` و`missing=["student"]`. عند وصول المكوّن المكمل، يستحوذ worker واحد على العملية وينفذ المسار القديم. إذا انتهى التنفيذ يعود `200` **برد المحرك الحالي مباشرة**، بلا غلاف جديد. مثال صيغة رد ناجح عندما لا توجد خطة:

```json
{
  "status": "no_feasible_plan",
  "metadata": {"top_k": 3, "returned_plan_count": 0, "history_as_of_part": 20261, "part_id": 20262},
  "recommendations": []
}
```

هذا مثال لصيغة الرد، وليس نتيجة مودل محسوبة للبيانات السابقة. عندما توجد خطط يبقى `status="ok"` وتحتوي `recommendations` مخرجات المحرك الحالية؛ لا يغير المسار الجديد المقاييس أو ترتيب Top K. ترجع استجابات الإدخال وlookup أيضًا header `X-Request-ID`.

## إعادة الإرسال واسترجاع النتيجة

إرسال المكوّن نفسه بنفس محتواه المطبّع تحت ID نفسه idempotent. تغيير المكوّن أو الهوية أو سياق متداخل يعطي conflict؛ لا تُرسل نسخة مصححة تحت ID سبق تخزين نسخة مختلفة له. الاستلام المتزامن أو retry أثناء التنفيذ يعطي `202 processing`، ولا يبدأ محاولة أخرى.

للانقطاع أو المهلة، استخدم `GET /api/v1/recommendation-requests/rec-example-20262-001` بمفتاح caller نفسه. لا تشغّل عملية توصية جديدة. عند الاكتمال يرجع غلاف مختلف عن POST:

```json
{
  "request_id": "rec-example-20262-001",
  "status": "completed",
  "received": ["student", "courses"],
  "missing": [],
  "result": {
    "status": "no_feasible_plan",
    "metadata": {"top_k": 3, "returned_plan_count": 0, "history_as_of_part": 20261, "part_id": 20262},
    "recommendations": []
  }
}
```

`pending/processing` يرجعان الغلاف المختصر `request_id/status/received/missing` مع `202`. فشل العملية يرجع غلافًا فيه هذه الحقول و`status:"failed"` و`error` بالشكل الحالي، مع HTTP المخزن. أخطاء schema/المصادقة ورفض الإدخال قبل تخزين الحالة ترجع `{"error":...}` كما في المسارات القديمة. عند فشل indeterminate بعد انتهاء مهلة processing لا يُعاد inference لهذا ID؛ راجع النتيجة وحالة الخدمة، وابدأ عملية جديدة بـID جديد عند اتخاذ قرار إعادة الطلب.

### مثال PHP مختصر

يفترض الكود `$studentInput` و`$coursesInput` بالمحتوى الكامل أعلاه، مبنيين من مصادر الجامعة وتأكيداتها الفعلية. خزّن `request_id` مرة واحدة للعملية في PHP، وحافظ عليه وعلى محتوى المكوّنين عند retry. لا تعِد توليد ID بعد انقطاع الاتصال.

```php
<?php
function advisorCall(string $base, string $method, string $path, string $key, ?array $body = null): array {
    $curl = curl_init(rtrim($base, '/') . $path);
    $headers = ['Accept: application/json', 'X-API-Key: ' . $key];
    $options = [
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT => 60
    ];
    if ($body !== null) {
        $headers[] = 'Content-Type: application/json';
        $options[CURLOPT_POSTFIELDS] = json_encode($body, JSON_THROW_ON_ERROR);
    }
    $options[CURLOPT_HTTPHEADER] = $headers;
    curl_setopt_array($curl, $options);
    $raw = curl_exec($curl);
    if ($raw === false) {
        curl_close($curl);
        throw new RuntimeException('Advisor transport failed; retrieve by the same request_id.');
    }
    $http = curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
    curl_close($curl);
    return [$http, json_decode($raw, true, 512, JSON_THROW_ON_ERROR)];
}

$base = getenv('ADVISOR_BASE_URL'); // URL الخدمة الحقيقي في إعداد PHP، عبر HTTPS في النشر.
$serviceKey = getenv('ADVISOR_API_KEY'); // أو المفتاح الخاص بهذه الجهة من إعداد النشر.
[$firstHttp, $first] = advisorCall($base, 'POST', '/api/v1/recommendation-inputs/student', $serviceKey, $studentInput);
if ($firstHttp >= 400) {
    throw new RuntimeException('Student submission was rejected; inspect the safe error code.');
}
[$secondHttp, $second] = advisorCall($base, 'POST', '/api/v1/recommendation-inputs/courses', $serviceKey, $coursesInput);
if ($secondHttp === 200) {
    $recommendationResult = $second; // صيغة التوصية القديمة مباشرة.
} elseif ($secondHttp === 202) {
    $requestId = rawurlencode($studentInput['request_id']);
    [$lookupHttp, $lookup] = advisorCall($base, 'GET', '/api/v1/recommendation-requests/' . $requestId, $serviceKey);
    if ($lookupHttp === 200) {
        $recommendationResult = $lookup['result'];
    } // عند202 انتظر ثم استعلم لاحقًا؛ لا تطلق inference جديدًا.
}
```

الترتيب المعاكس مدعوم. لا تسجل `$raw` أو المدخلات أو المفاتيح. قيم مهلة PHP في المثال خيارات عميل، وليست SLA للخدمة؛ lookup يعالج انقطاع انتظار الرد.

## C. تحديث Frozen History بعد تثبيت فصل

هذه عملية واحدة مشتركة للفصل المثبت، وليست عملية لكل طالب. `part_id` هنا يحدد **الفصل المنتهي**. مثال المجاميع:

```json
{
  "part_id": 20261,
  "rows": [
    {
      "degree_id": "D1", "course_id": "C1", "faculty_id": "F1",
      "plan_requirement_type_id": "R1", "course_credits": "3",
      "count": 20, "mark_sum": "1420", "fail_count": 3,
      "attempt_sum": 24, "retake_count": 4
    }
  ]
}
```

هذا JSON للمحتوى الأكاديمي فقط. لنشره، أرفق `finalization={"finalized_part_id":20261,"approval_reference":<actual university approval reference>}` من الحدث الرسمي؛ لا تصنع مرجعًا من وقت الإرسال أو من نجاح JSON.

| المفهوم | المثال |
|---|---|
| `delta_part`، وهو `part_id` في طلب Delta | `20261`: نتائج الفصل المثبت التي تضاف |
| `history_as_of_part` | `20261` بعد النشر والتفعيل: cutoff التاريخ التراكمي |
| `part_id` في طلب توصية الطالب | `20262`: الفصل الذي نوصي له |

قبل إضافة `20261` يجب أن يكون التاريخ النشط حتى `20253`. baseline التراكمي `20251` لا يكفي مباشرة؛ يجب أن تكون `20252` و`20253` أضيفتا بالترتيب. يحتسب calendar الفصل `3` أيضًا عند استمرارية التحديث، ولا يجوز القفز عليه بلا مسار migration صريح.

`normalize_history_delta()` يفحص صفوف المجاميع قبل تطبيقها. grain الذي يمنع التكرار هو `degree_id/course_id/faculty_id/plan_requirement_type_id` مع قيمة `course_credits` الكاملة المطبّعة. `build_history_keys()` يحافظ على مجموعات التاريخ الخمس، ويستخدم تقريب الساعات فقط في مفاتيح fallback المعتمدة للمستويات 3–5؛ لا تغير هذا التقريب في PHP.

`count` لكل صف يجب أن يكون صحيحًا وموجبًا وفق العقد القائم؛ للموسم الخالي يمكن إرسال `rows=[]` بدل صف بصفر. `fail_count/retake_count` صحيحان بين صفر وcount. الرسوب `final_mark < 50`، والإعادة `attempt_number > 1`. `mark_sum` داخل حدود العلامات ويتفق مع عدد الناجحين/الراسبين، و`attempt_sum` يتفق مع count والإعادات. إذا حمل الصف `part_id` اختياريًا يجب أن يساوي فصل Delta. قيم غير finite أو grain مكرر تُرفض.

للمفتاح التجميعي المطابق، يضيف النظام المجاميع: `100/7100/12/130/30` مع `20/1420/3/24/4` تصبح `120/8520/15/154/34` بترتيب `count/mark_sum/fail_count/attempt_sum/retake_count`. ينشئ مفاتيح جديدة عند الحاجة، ولا يستبدل التاريخ بصفوف الفصل الجديد. retry مطابق لا يضيف الفصل مرتين؛ fingerprint مختلف للفصل المضاف أو ترتيب غير صحيح يُرفض.

### المسار الإداري اليدوي

| الخطوة | URL | الاعتماد والحقول |
|---|---|---|
| الحالة | `GET /api/v1/admin/history/status` | admin |
| اختيار الوضع | `PUT /api/v1/admin/history/mode` | admin، `{"mode":"manual"}` بعد موافقة المشرف |
| أول baseline فقط | `POST /api/v1/admin/history/initialize` | admin، `expected_source_hash/approval_reference/confirmation:true/cumulative_history_confirmed:true` |
| تحقق دون كتابة | `POST /api/v1/history/deltas/validate` | admin، `part_id/rows/finalization?` |
| معاينة | `POST /api/v1/admin/history/preview` | admin، payload الفصل نفسه |
| نشر | `POST /api/v1/admin/history/commit` | admin، payload مع finalization و`preview_token` من المعاينة و`confirmation:true` |
| تفعيل | `POST /api/v1/admin/history/activate` | admin، `history_as_of_part/expected_history_sha256/confirmation:true`؛ `rollback:false` افتراضيًا |

baseline تراكمي معتمد من مصدر الجامعة، و`expected_source_hash` بصمة metadata التي راجعها المشرف بالفعل. لا تهيّئ مخزن التاريخ من Delta فصل واحد.

مثال PHP **منفصل** عن إرسال الطالب والمواد، باستخدام الدالة `advisorCall()` السابقة:

```php
<?php
$adminKey = getenv('ADVISOR_ADMIN_API_KEY');
$delta = [
    'part_id' => $finalizedSemesterFromUniversity,
    'rows' => $officialSemesterAggregates,
    'finalization' => [
        'finalized_part_id' => $finalizedSemesterFromUniversity,
        'approval_reference' => $actualUniversityApprovalReference
    ]
]; // هذه القيم تأتي من المصدر المثبت فعلًا؛ المجاميع تخص فصلًا واحدًا.
[$checkHttp, $check] = advisorCall($base, 'POST', '/api/v1/history/deltas/validate', $adminKey, $delta);
if ($checkHttp !== 200 || $check['validation_status'] !== 'valid') {
    throw new RuntimeException('History validation is not complete.');
}
[$previewHttp, $preview] = advisorCall($base, 'POST', '/api/v1/admin/history/preview', $adminKey, $delta);
if ($previewHttp !== 200 || !$preview['compatibility'] || $administratorConfirmedCommit !== true) {
    throw new RuntimeException('A compatible preview and explicit commit approval are required.');
}
$commitBody = $delta + ['preview_token' => $preview['preview_token'], 'confirmation' => true];
[$commitHttp, $commit] = advisorCall($base, 'POST', '/api/v1/admin/history/commit', $adminKey, $commitBody);
if ($commitHttp !== 200) {
    throw new RuntimeException('History commit was rejected.');
}
// خطوة موافقة مستقلة بعد مراجعة النسخة وبصمتها؛ commit لا يفعلها.
if ($administratorConfirmedActivation !== true || $approvedHistoryHash !== $commit['new_history_sha256']) {
    throw new RuntimeException('Explicit activation approval of this exact hash is required.');
}
$activation = [
    'history_as_of_part' => $commit['history_as_of_part'],
    'expected_history_sha256' => $approvedHistoryHash,
    'confirmation' => true,
    'rollback' => false
];
[$activateHttp, $activated] = advisorCall($base, 'POST', '/api/v1/admin/history/activate', $adminKey, $activation);
```

المثال يفترض `manual` وbaseline جاهزة ومعاينة `new_delta`. عند `already_applied` لا تعِد إضافة المجاميع؛ افحص الحالة والبصمة الحالية واتبع الرد القائم. `commit` ينشر حزمة immutable؛ التفعيل يبدل pointer فقط بعد توافق أصول الخدمة وفحص SHA-256. rollback تفعيل نسخة موجودة مع بصمتها المعتمدة و`rollback:true` وتأكيد مستقل.

### التثبيت التلقائي الموثوق

في وضع `auto_on_finalization` فقط، ترسل الجهة المؤتمنة payload نفسه **مع finalization الحقيقي** إلى `POST /api/v1/admin/history/finalization-events` بمفتاح `ADVISOR_FINALIZATION_API_KEY` المنفصل. يعيد المسار الموجود التحقق والمعاينة والنشر والتفعيل المصرح به. لا تستخدم service key أو admin key بدل هذا المفتاح، ولا تجعل وصول Delta العادي يطلق التفعيل التلقائي.

المسار الفعلي: `ApiService.validate_delta() → adapt_history_delta() → normalize_history_delta()` للتحقق؛ ثم `preview_history()/commit_history()/activate_history()` عبر `_history_operation()` إلى `CumulativeHistoryStore.preview/commit/activate`. النشر يعيد استخدام `FrozenHistoryManager.update_history_from_payload()` و`save_frozen_history_atomic()`؛ لا محرك تاريخ موازٍ.

## الأخطاء والاحتفاظ والتشغيل

شكل الخطأ محفوظ: `{"error":{"code":"...","message":"...","component":"..."}}`، وقد يحتوي حقولًا تشخيصية آمنة. schema غير صالح يرجع `422 INVALID_REQUEST_SCHEMA`. مفتاح مفقود `401`، وغير مخول `403`. تعارض correlation أو المحتوى `409`. الأخطاء الأكاديمية `422`، والتبعيات/انشغال الخدمة `503`. لا يعاد raw input أو أثر استثناء داخلي.

| إعداد Python | الافتراضي |
|---|---|
| `ADVISOR_REQUEST_STORE_PATH` | `PROJECT_ROOT/.api-state/requests.sqlite3` |
| `ADVISOR_REQUEST_PENDING_TTL_SECONDS` | `900` |
| `ADVISOR_REQUEST_PROCESSING_TTL_SECONDS` | `3600` |
| `ADVISOR_REQUEST_RESULT_TTL_SECONDS` | `86400` |
| `ADVISOR_REQUEST_MAX_COUNT` | `10000` سجل، بما فيها tombstones |
| `ADVISOR_REQUEST_MAX_PAYLOAD_BYTES` | `2097152` بايت |
| `ADVISOR_SERVICE_KEYS` | `{}`؛ legacy key مستقل يبقى مدعومًا |

SQLite مخزن معاملات على **قرص محلي لمضيف واحد**، يشترك فيه جميع workers باستخدام المسار نفسه. لا تستخدم network filesystem أو نسخة SQLite مستقلة لكل worker، ولا تعتبر ذلك حلًا متعدد المضيفين. معاملة الاستحواذ تمنع محاولتين للعملية نفسها؛ لا يمنح ذلك ضمان توفر كامل إذا انهار worker بعد الاستحواذ.

TTL يحذف بيانات الطالب والمواد والنتيجة وفق العمر المحدد، مع إبقاء tombstones محدودة العدد لهويات الطلبات وبصماتها لمنع إعادة inference بعد انتهاء الاحتفاظ. لا توجد إعادة تدوير تلقائية لمعرّفات الطلبات أو إخلاء يفتح ID قديمًا من جديد. عند بلوغ السعة يلزم إجراء إداري مخطط للأرشفة/التدوير، مع منع إعادة استعمال IDs القديمة؛ ضمان retry لهذا المخزن يخص قاعدة البيانات المحتفظ بها.

مهلة processing لا تعني إلغاء تنفيذ المودل. إذا انقضت أو انهار worker، تحفظ العملية كفشل غير محسوم، ولا يعاد تشغيلها تلقائيًا. استخدم ID جديدًا فقط بعد قرار caller الواعي. مخزن الطلبات منفصل عن `data/models/Frozen History`؛ لا ترسل history delta عبر مسارات إدخال الطالب.

ملفات SQLite وملفاتها المرافقة قد تحتوي معلومات أكاديمية. استخدم حساب خدمة خاصًا وACL خاصة على Windows، وصلاحيات مقيدة على POSIX؛ استثناء المسار الافتراضي من Git لا يغني عن حماية ملفات النشر أو النسخ الاحتياطية. TLS وصلاحيات المستخدم الجامعية وضبط reverse proxy وقيود body/التزامن وخطة الاحتفاظ مسؤوليات نشر. نجاح الاختبارات الاصطناعية لا يثبت جاهزية الإنتاج.

[دليل API التعليمي](../src/api/README.md) · [الإعدادات وعقد التاريخ التراكمي](API_CONFIGURATION_AND_CUMULATIVE_HISTORY.md)
