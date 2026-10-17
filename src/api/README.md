# طبقة API في Academic Advisor

هذه الطبقة تحوّل ردود الجامعة إلى المدخلات التي يفهمها محرك التوصية. نقطة الوصول إلى المحرك هي هذا الاستدعاء داخل `ApiService`:

```python
service.engine.recommend_from_payloads(
    student_payload={"snapshot": student.normalized, "candidates": candidates},
    request_payload=engine_request,
    top_k=request.get("top_k", 3),
    history_as_of_part=cutoff,
    allow_older_history=mode == "backtesting",
)
```

`snapshot` هو وضع الطالب عند بداية فصل الهدف، و`candidates` هي المواد المؤهلة بعد التحقق، و`engine_request` يحمل الهوية والساعات وقيود التسجيل. تبني طبقة API هذه المدخلات ثم تعيد نتيجة المحرك ببيانات وصفية عامة محددة في `PUBLIC_METADATA`.

المسار الأساسي هو `PHP-push`: يجلب PHP رد الطالب ورد المواد ويرسلهما معًا بالعقد السابق، أو في طلبين منفصلين مرتبطين بـ`request_id`. `BackendClient` أداة `Python-pull` اختيارية ومستقلة؛ تشغيل API لا يستدعيها تلقائيًا. طبقة الإدخال الجديدة تعيد استخدام حسابات المحرك وميزات `33/47` واختيار `pareto v1 → pareto v1` وبوابة اعتماد `manifest`.

[عقد تسليم PHP الكامل](../../docs/PHP_BACKEND_INTEGRATION_CONTRACT.md) يبين JSON الطالب والمواد المنفصلين، الاسترجاع وretry، وتحديث Frozen History الإداري.

## Project Structure

```text
src/api/
├── app.py                   # HTTP، المصادقة، startup، ومعالجة الأخطاء
├── service.py               # ترتيب التحقق والتجهيز واستدعاء المحرك
├── schemas.py               # شكل طلبات HTTP وأنواع حقولها
├── settings.py              # الإعدادات من البيئة والتحقق منها
├── backend_client.py        # جلب اختياري لردي الجامعة من Python
├── request_store.py         # تجميع مكونات الطلب في SQLite محلية بمعاملات وTTL
├── adapters/
│   ├── __init__.py
│   ├── student.py           # تحويل بيانات الطالب إلى snapshot
│   ├── courses.py           # تحويل المواد والسياسات إلى candidates وقيود
│   └── history.py           # تجهيز نتيجة التحقق من History Delta
├── validators/
│   ├── __init__.py
│   ├── common.py            # الهوية والأرقام والمصدر والتشخيص الآمن
│   ├── student.py           # فحوص رد الطالب وتاريخه ومصدر ساعات GPA
│   ├── courses.py           # فحوص المواد والكتالوج والسياسات
│   └── history.py           # فحوص Delta وتثبيت الفصل والتاريخ
├── student_adapter.py       # توافق مع مسار الاستيراد السابق
├── courses_adapter.py       # توافق مع مسار الاستيراد السابق
├── history_adapter.py       # توافق مع مسار الاستيراد السابق
├── validation.py            # توافق مع مسار الاستيراد السابق
├── README.md
└── REFACTOR_REPORT.md        # أدلة المقارنة والاختبارات لهذه المهمة
```

`adapters` تبني البيانات الداخلية، و`validators` تفحص المدخلات والأدلة التي تعتمد عليها. الملفات السابقة تعيد تصدير الأسماء اللازمة، لذلك تبقى الاستيرادات القديمة صالحة. يمكن استيراد `src.api` و`ApiService` دون FastAPI أو Pydantic؛ يحتاج `app.py` حزمة `api` الاختيارية.

حسابات الطالب المشتركة تبقى في [temporal_features.py](../features/temporal_features.py)، وحساب الفجوات في [academic_calendar.py](../data/academic_calendar.py). عقد `snapshot` والتحقق النهائي منه في [inputs.py](../recommendation/inputs.py)، والمحرك في [two_stage_engine.py](../recommendation/two_stage_engine.py). مسارات الأصول مركزية في [src/paths.py](../paths.py).

## Student API Data Flow

لفهم مدخل المحرك، نتتبع كيف يصل `student.normalized` إليه:

1. `ApiService.recommend(request)` يستدعي `_validate_recommendation_inputs()`. هذه الخطوة تنفذ `validate_student()` و`validate_courses()`، وتجمع الأخطاء قبل بدء inference.
2. `validate_student()` يستدعي `adapters.student.adapt_student()`. تعيد الدالة `ValidationResult`؛ يحتوي `normalized` على اللقطة الداخلية، و`errors/checks/unavailable_fields/summary` على التشخيص.
3. `extract_student_info(request, result)` يستخرج `studentDegreeInfo` و`studentSummaryInfo` ويتحقق من غلاف الرد والهوية وسياق جلب الطالب. يستخدم `binding()` و`response_data()` و`check_record_identity()`.
4. `build_student_snapshot()` يبدأ حقول `BACKEND_SNAPSHOT_COLUMNS` بقيمة `None`، ويضيف الهوية المتحقق منها. ثم يرتب الخطوات التالية: `map_student_fields()` → `add_sourced_student_values()` → `add_history_features()` → `validate_grade_version()` → `add_snapshot_features()`.
5. `map_student_fields()` يحول الحقول المباشرة وحقول الدبلوم. `add_sourced_student_values()` يضيف المجاميع الموثقة ويفحص التعارض مع المصادر الأصلية.
6. `add_history_features()` يستخدم `normalize_student_history()` لفحص صفوف التاريخ، و`validate_history_target()` لفحص سجل الهدف. ثم يعيد استخدام الحسابات الأصلية للـGPA والعداد والفجوات.
7. `_prepare_recommendation_context()` يفحص cutoff وmode وجاهزية التبعيات واكتمال التاريخ اللازم وحد التدريب، ويثبت التاريخ المطلوب. `_build_engine_request()` يبني هدف الساعات وقيود التصنيفات والمجموعات.
8. `_run_recommendation()` يأخذ قفل inference ثم ينفذ `service.engine.recommend_from_payloads()`. `_recommendation_response()` يعيد `status/recommendations` والبيانات الوصفية المسموحة.

كل قيمة تمر أولًا عبر تحقق نوعها وهوية مصدرها. فصل الهدف ونتائجه لا يدخلان تاريخ الطالب. لا تستخدم الطبقة `GPA_POINTS` أو `END_AGPA_POINTS` أو `SEMESTER_FAIL_CREDITS` من سجل الهدف لبناء ميزات الماضي.

### كيف يُحسب تاريخ الطالب؟

تحتاج صفوف `studentSummaryInfo` إلى `STUDENT_STATUS_ID, STUDENT_ID, DEGREE_ID, PART_ID, GPA_POINTS, SEMESTER_REG_COURSES`. تفحص هوية **كل** الصفوف قبل التعامل مع نقص schema، وترفض الفصل الحالي أو المستقبل وتكرار مفاتيح الفصل أو status.

عند التاريخ الجزئي، يستخدم `add_history_features()` الدالة `compute_student_gpa_history()`: ترتيب زمني، واستخدام GPA للفصول المسجلة، و`ffill` ثم `shift(1)` للحصول على المعدل السابق. `LAST_ENROLLED_GPA` التاريخي إن توفر يؤثر عبر المعدل السابق للسجل التاريخي في `gpa_prev_2` للهدف؛ `gpa_prev_1` للهدف يأتي من GPA التسجيل السابق لأن قيمة الهدف نفسها مجهولة. الفصول غير المسجلة تبقى في الجدول، والمعدل المجهول يبقى `None`.

إذا كانت جميع الصفوف التاريخية تحتوي أيضًا `LAST_ENROLLED_GPA, TOTAL_REG_COURSES, TOTAL_REG_CREDITS, TOTAL_FAIL_COURSES, TOTAL_FAIL_CREDITS, REG_TOTAL_SEMESTERS`، تستخدم الدالة `add_student_history_features()`. تعيد هذه الدالة استخدام حساب GPA نفسه، وتأخذ `prior_registered_semesters` من العداد الرسمي للسجل السابق؛ لا تستبدله بعدد صفوف الرد. إذا توفر supplement مختلف لهذا العداد، يُرفض التعارض.

`observed_gap_semesters` يعتمد على آخر فصل فيه مواد مسجلة، ثم `count_regular_semesters_between()`؛ يضاف فصل الهدف إذا كان منتظمًا والطالب غير مسجل فيه. يحتاج الحساب معرفة التسجيل الحالي: `SEMESTER_REG_COURSES` أو ساعات موجبة تثبت وجود تسجيل. ساعات صفر وحدها لا تثبت غياب التسجيل، لأن المواد قد تكون صفرية الساعات.

### مصدر ساعات GPA

تبقى `_official_gpa_credits()` في `validators/student.py`، ويُعاد تصديرها من مسار التوافق السابق. تحقق الشهادة واستخراج القيمة الدقيقة جزء واحد: لا يمكن حساب قيمة موثوقة قبل إثبات توقيت المصدر وقواعده.

- `beginning_of_semester`: يجب أن يطابق `target_part` فصل الهدف، وأن يساوي `as_of_part` الفصل السابق مباشرة. عندها يوفر `TOTAL_REG_CREDITS` الرسمي كلا الحقلين `current_gpa_credits` و`prior_total_reg_credits`.
- `end_of_semester`: يجب أن يكون `as_of_part` هو فصل الهدف، مع `semester_complete=true` و`additive_credit_accounting=true` و`semester_gpa_counted_credits` موثق. عندها فقط تُطرح الساعات المحتسبة للفصل من الإجمالي باستخدام `sum_credit_values()`.
- عند غياب الشهادة الرسمية، يمكن استخدام `integration_context.student_values` بمصدر وcutoff موثقين. `current_gpa_credits` و`prior_total_reg_credits` يحتاجان الفصل السابق مباشرة. أي supplement يتعارض مع القيمة الرسمية يُرفض.

`START_TOTAL_IN_CREDITS` ساعات إكمال سابقة، و`SEMESTER_REG_CREDITS` ساعات التسجيل الحالي؛ لا يصبح أي منهما مقام GPA تلقائيًا. شهادة PHP تثبت قواعد الجامعة وتوقيت المصدر؛ اتساق الأرقام وحده لا يثبت هذه القواعد. [تفاصيل عقد المقام والتاريخ](../../docs/API_CONFIGURATION_AND_CUMULATIVE_HISTORY.md).

## Student Feature Mapping

هذه جميع الحقول الـ21 في `BACKEND_SNAPSHOT_COLUMNS` الفعلي. الجدول يبين مصدرها في مسار API، وليس مجرد تفسير لأسمائها.

| Feature | API Source | Transformation | Function |
|---|---|---|---|
| `student_id` | الطلب و`source_contexts.student` و`studentDegreeInfo.STUDENT_ID` | مطابقة الهوية وحفظها كسلسلة | `extract_student_info()` |
| `degree_id` | الطلب والسياق و`studentDegreeInfo.DEGREE_ID` | مطابقة هوية الاختصاص | `extract_student_info()` |
| `faculty_id` | `studentDegreeInfo.FACULTY_ID` | سلسلة ID غير فارغة | `map_student_fields()` |
| `grade_version_id` | `studentDegreeInfo.GRADE_VERSION_ID` | سلسلة ID مع تحقق الدعم من GradeScale | `map_student_fields()`، `validate_grade_version()` |
| `gpa_prev_1` | `studentSummaryInfo.GPA_POINTS/SEMESTER_REG_COURSES` | GPA آخر تسجيل سابق؛ سجل الهدف له GPA مجهول | `add_history_features()` → `compute_student_gpa_history()` مباشرة أو عبر `add_student_history_features()` |
| `gpa_prev_2` | تاريخ GPA؛ و`LAST_ENROLLED_GPA` التاريخي إن توفر | registered shift إضافي عبر `gpa_prev_1` التاريخي؛ القيمة الرسمية التاريخية تُستخدم إذا كانت موجودة | `add_history_features()` → `compute_student_gpa_history()` مباشرة أو عبر `add_student_history_features()` |
| `start_agpa_points` | `studentDegreeInfo.START_AGPA_POINTS` | GPA البداية بين 0 و4 | `map_student_fields()` |
| `start_total_in_courses` | `studentDegreeInfo.START_TOTAL_IN_COURSES` | عدد صحيح غير سالب إلى قيمة رقمية | `map_student_fields()` |
| `start_total_in_credits` | `studentDegreeInfo.START_TOTAL_IN_CREDITS` | ساعات الإكمال السابقة إلى قيمة رقمية | `map_student_fields()` |
| `prior_total_reg_courses` | `integration_context.student_values.prior_total_reg_courses` | مجموع بداية الفصل بمصدر وcutoff موثقين | `add_sourced_student_values()` |
| `prior_total_reg_credits` | `TOTAL_REG_CREDITS` مع `total_reg_credits_source`، أو `student_values.prior_total_reg_credits` | قيمة البداية مباشرة أو اشتقاق موثق أو supplement؛ رفض التعارض | `_official_gpa_credits()`، `add_sourced_student_values()` |
| `prior_total_fail_courses` | `student_values.prior_total_fail_courses` | عدد صحيح؛ يراجع `TOTAL_FAIL_COURSES` الأصلي عند وجوده | `add_sourced_student_values()` |
| `prior_total_fail_credits` | `student_values.prior_total_fail_credits` | ساعات؛ يراجع `TOTAL_FAIL_CREDITS` الأصلي عند وجوده | `add_sourced_student_values()` |
| `prior_fail_credit_ratio` | `prior_total_fail_credits` و`prior_total_reg_credits` في snapshot | fail credits / reg credits؛ `None` عند مقام صفر/مجهول أو رسوب مجهول | `build_student_snapshot()` |
| `prior_registered_semesters` | `student_values.prior_registered_semesters`، أو `REG_TOTAL_SEMESTERS` السابق عند schema كاملة | supplement موثق أو shift للعداد السابق؛ رفض التعارض | `add_sourced_student_values()`، `add_history_features()` → `add_student_history_features()` |
| `observed_gap_semesters` | آخر تسجيل تاريخي والتسجيل الحالي من `studentDegreeInfo` | عدد الفصول المنتظمة الفاصلة، مع إضافة الهدف المنتظم إذا كان غير مسجل | `add_history_features()` → `count_regular_semesters_between()`، `is_regular_semester()` |
| `diploma_gpa` | `studentDegreeInfo.diploma_gpa/DIPLOMA_GPA` افتراضيًا | aliases من `settings.diploma_gpa_aliases`؛ قيمة رقمية finite | `map_student_fields()` |
| `diploma_type_id` | `studentDegreeInfo.diploma_type_id/DIPLOMA_TYPE_ID` افتراضيًا | aliases من `settings.diploma_type_aliases`؛ سلسلة، ورفض التعارض | `map_student_fields()` |
| `degree_credits_count` | `studentDegreeInfo.DEGREE_CREDITS_COUNT` | ساعات الاختصاص إلى قيمة رقمية | `map_student_fields()` |
| `part_id` | الطلب والسياق وهوية فصل `studentDegreeInfo` | مطابقة الفصل وتطبيعه وفق `part()` | `extract_student_info()` |
| `current_gpa_credits` | `TOTAL_REG_CREDITS` الموثق، أو `student_values.current_gpa_credits` | مقام GPA الرسمي عند البداية؛ ليس ميزة مودل | `_official_gpa_credits()`، `add_sourced_student_values()` |

يضيف `add_snapshot_features()` ثلاثة حقول مشتقة: `part_semester = part_id % 10`، و`gpa_trend_delta = gpa_prev_1 - gpa_prev_2`، و`gpa_trend_missing = 1` إذا كان الاتجاه مجهولًا. يعيد `normalize_student_payload()` في Core حساب هذه الحقول أيضًا عند تجهيز المدخلات؛ لا يثق بقيمة اتجاه مُرسلة من الخارج.

كل supplement شكله `{value, source, as_of_part}`، ومصدره غير فارغ وفصله قبل الهدف. يسمح Adapter فقط بالحقول الستة الموثقة في `SOURCED_FIELDS`. المجهول يبقى `None`؛ نقص الدبلوم أو مقام GPA خطأ، ونقص schema التاريخ أو gap اللازم يمنع التوصية. بعض histories والمجاميع nullable وفق عقد Core، وتظهر ضمن `unavailable_student_fields`.

بعد اللقطة: تضيف المواد خصائصها من الرد والكتالوج، وتضيف Frozen History الميزات السبع `course_history_*`. يستخدم Stage 1 الميزات الـ33، ويختار حتى 50 خطة. يحسب `compute_plan_context_features()` ميزات `plan_*` الست و`peer_*` الثماني للـshortlist، ثم يستخدم Stage 2 الميزات الـ47. هوية المجموعة وcaps و`current_gpa_credits` لا تدخل مصفوفة المودل.

## One Request Example

هذا طلب **اصطناعي كامل** لتوضيح التحويل. جميع IDs والقيم والسياسات أدناه أمثلة تعليمية؛ لا تمثل بيانات طالب أو إعدادات الجامعة. يفترض اختبار المواد كتالوجًا اصطناعيًا مطابقًا للمادة ونوعها `3`؛ لا يضيف الطلب هذه المادة إلى كتالوج الخدمة الفعلي.

```json
{
  "student_id": "student-example",
  "degree_id": "degree-example",
  "part_id": 20251,
  "history_as_of_part": 20243,
  "target_credits": 3,
  "top_k": 3,
  "mode": "normal",
  "source_contexts": {
    "student": {"student_id": "student-example", "degree_id": "degree-example", "part_id": 20251},
    "courses": {"student_id": "student-example", "degree_id": "degree-example", "part_id": 20251}
  },
  "student_api_response": {
    "success": true,
    "data": {
      "studentDegreeInfo": {
        "STUDENT_STATUS_ID": "status-target",
        "STUDENT_ID": "student-example", "DEGREE_ID": "degree-example",
        "STATUS_SEMESTER_ID": "20251", "FACULTY_ID": "faculty-example",
        "GRADE_VERSION_ID": "3.111", "START_AGPA_POINTS": "2.8",
        "START_TOTAL_IN_COURSES": "24", "START_TOTAL_IN_CREDITS": "72",
        "TOTAL_REG_CREDITS": "75", "TOTAL_FAIL_COURSES": "1",
        "TOTAL_FAIL_CREDITS": "3", "SEMESTER_REG_COURSES": "6",
        "SEMESTER_REG_CREDITS": "18", "DEGREE_CREDITS_COUNT": "180",
        "diploma_gpa": "92", "diploma_type_id": "diploma-example"
      },
      "studentSummaryInfo": [
        {"STUDENT_STATUS_ID": "status-prior-1", "STUDENT_ID": "student-example", "DEGREE_ID": "degree-example",
         "PART_ID": "20242", "GPA_POINTS": "2.6", "SEMESTER_REG_COURSES": "5"},
        {"STUDENT_STATUS_ID": "status-prior-2", "STUDENT_ID": "student-example", "DEGREE_ID": "degree-example",
         "PART_ID": "20243", "GPA_POINTS": "3.1", "SEMESTER_REG_COURSES": "2"}
      ]
    }
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
    "total_reg_credits_source": {
      "source": "synthetic_official_gpa_ledger", "target_part": 20251,
      "as_of_part": 20243, "timing": "beginning_of_semester",
      "rules_reference": "synthetic_rules_v1"
    },
    "student_values": {
      "prior_total_reg_courses": {"value": 25, "source": "synthetic_ledger", "as_of_part": 20243},
      "prior_total_fail_courses": {"value": 1, "source": "synthetic_ledger", "as_of_part": 20243},
      "prior_total_fail_credits": {"value": 3, "source": "synthetic_ledger", "as_of_part": 20243},
      "prior_registered_semesters": {"value": 4, "source": "synthetic_ledger", "as_of_part": 20243}
    },
    "registration_policy": {
      "source": "synthetic_registration_policy", "part_id": 20251,
      "requirement_group_modes": {"group-example": "strict_remaining"},
      "allowed_failed_repeat_credits": 0, "allowed_withdrawn_repeat_credits": 0,
      "attempts_scope_confirmed": true, "load_profile": "study"
    }
  }
}
```

الطالب هنا مسجل حاليًا وله سجلان سابقان. نتيجة `adapt_student()` الداخلية بعد التحويل هي:

```json
{
  "student_id": "student-example", "degree_id": "degree-example",
  "faculty_id": "faculty-example", "grade_version_id": "3.111",
  "gpa_prev_1": 3.1, "gpa_prev_2": 2.6,
  "start_agpa_points": 2.8, "start_total_in_courses": 24.0,
  "start_total_in_credits": 72.0, "prior_total_reg_courses": 25.0,
  "prior_total_reg_credits": 75.0, "prior_total_fail_courses": 1.0,
  "prior_total_fail_credits": 3.0, "prior_fail_credit_ratio": 0.04,
  "prior_registered_semesters": 4.0, "observed_gap_semesters": 0,
  "diploma_gpa": 92.0, "diploma_type_id": "diploma-example",
  "degree_credits_count": 180.0, "part_id": 20251,
  "current_gpa_credits": 75.0, "part_semester": 1,
  "gpa_trend_delta": 0.5, "gpa_trend_missing": 0
}
```

`75` جاءت من الإجمالي الرسمي الموثق؛ `72` بقيت ساعات إكمال. `3 / 75 = 0.04`، و`3.1 - 2.6 = 0.5`. العداد `4` جاء من المصدر الإضافي، رغم وجود صفين فقط في المثال.

تحول `adapt_courses()` المادة إلى مرشح `NEW` بمحاولة `1`؛ `course_credits` تصبح `Decimal("3")`، ونوع المادة يأتي من الكتالوج. هوية المجموعة الداخلية هي JSON `["degree-example","group-example"]`، والساعات المتبقية `12 - 3 = 9`.

يصبح طلب المحرك:

```python
engine_request = {
    "student_id": "student-example",
    "degree_id": "degree-example",
    "part_id": 20251,
    "target_credits": Decimal("3"),
    "allowed_failed_repeat_credits": Decimal("0"),
    "allowed_withdrawn_repeat_credits": Decimal("0"),
    "requirement_policies": [
        {"plan_requirement_type_id": "R", "max_credits": Decimal("3")}
    ],
    "requirement_group_policies": {
        '["degree-example","group-example"]': Decimal("9")
    },
    "max_new_courses": 2,
}
```

تصل اللقطة والمرشح وهذا الطلب إلى الاستدعاء الموضح في بداية الملف، مع `history_as_of_part=20243` و`allow_older_history=False`. عُرضت هنا نتيجة adapters؛ نجاح توصية HTTP يتطلب أيضًا الكتالوج الفعلي وGradeScale والأصول المعتمدة وحزمة التاريخ المحددة. الرد الخارجي للتوصية يحتوي `status` و`metadata` و`recommendations`؛ واجهات التحقق لا تعيد اللقطة أو الرد الخام.

## How to Run

نفذ من جذر المشروع باستخدام البيئة الافتراضية:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[api,api-test]'
$env:ADVISOR_API_KEY = '<service-key>'
$env:ADVISOR_ADMIN_API_KEY = '<different-admin-key>'
$env:ADVISOR_FINALIZATION_API_KEY = '<different-finalization-key>'
.\.venv\Scripts\python.exe -m uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

قيم المفاتيح أعلاه placeholders؛ اضبط أسرار الخدمة خارج Git وبقيم مختلفة. `create_app()` ينشئ التطبيق، و`lifespan` يحمل الكتالوج وGradeScale والتاريخ والمودلات بصورة مستقلة عبر `ApiService.initialize()`. فشل تحميل تبعية يبقي `/health` والتشخيص متاحين، ويمنع inference غير الجاهز.

### PHP-push: المسار الأساسي

PHP يوثق المستخدم ويتحقق من صلاحياته على الطالب والاختصاص، ويجلب الردين للفصل المطلوب، ثم يرسل JSON بنفس شكل المثال مع `source_contexts.student` و`source_contexts.courses` مستقلين. مفتاح الخدمة يوثق الجهة المرسلة؛ صلاحيات المستخدم الجامعية مسؤولية PHP.

احفظ JSON المثال في ملف محلي خارج Git، ثم أرسل الطلب:

```powershell
$requestJsonPath = '<absolute-path-to-request.json>'
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/recommend' `
  -Headers @{ 'X-API-Key' = $env:ADVISOR_API_KEY } `
  -ContentType 'application/json' -Body (Get-Content -LiteralPath $requestJsonPath -Raw)
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/health'
```

`POST /recommend` alias للمسار السابق `POST /api/v1/recommendations`؛ لهما handler والمصادقة وschema والنتيجة نفسها. IDs الاصطناعية في المثال تحتاج dependencies اصطناعية مطابقة كما في الاختبارات؛ تشغيل الأمر على خدمة بكتالوج فعلي لا يثبت صلاحية تلك IDs.

### إرسال الطالب والمواد في طلبين

أرسل `POST /api/v1/recommendation-inputs/student` بعقد `StudentInputRequest`: عقد تحقق الطالب السابق مع `request_id` و`recommendation` الإلزامي، وفيه cutoff وخيارات الساعات و`top_k/mode`. أرسل `POST /api/v1/recommendation-inputs/courses` بعقد `CoursesInputRequest`: عقد تحقق المواد السابق مع `request_id` نفسه. لكل مكوّن سياق جلبه ومصادره الموثقة؛ الهوية والفصل والجهة المرسلة يجب أن تتطابق، وأي تعارض في السياقات المشتركة يُرفض.

أي المكوّنين يمكن أن يصل أولًا. المكوّن الأول يرجع `202` مع `request_id/status:"pending"/received/missing`. عند اكتمال الزوج، يستحوذ worker واحد على العملية ويعيد استعمال المسار الحالي:

```text
app.student_input() أو app.courses_input()
  → ApiService.submit_recommendation_input()
  → RequestStore.replay()/submit() والاستحواذ بمعاملة
  → ApiService._assemble_recommendation_request()
  → ApiService.recommend()
  → adapters/validators → engine.recommend_from_payloads()
  → RequestStore.complete()/fail() → app.input_response()
```

POST المكتمل يعيد رد التوصية القديم مباشرةً مع `200`، وretry مطابق يعيد النتيجة المحفوظة دون inference جديد. أثناء التنفيذ يعود `202 processing`. للاسترجاع بعد انقطاع الاتصال، استخدم `GET /api/v1/recommendation-requests/{request_id}` بالمفتاح نفسه: المكتمل يرجع غلافًا فيه `status:"completed"` و`result`، والمنتظر `202`، والفاشل غلاف `status:"failed"` و`error` مع HTTP المخزن. يضاف `X-Request-ID` لاستجابات الحالة. lookup لا يشغّل inference، وواجهات التحقق السابقة لا تخزن أي طلب.

مفتاح `ADVISOR_API_KEY` السابق يمثل caller باسم `legacy`. للجهات المستقلة يمكن ضبط `ADVISOR_SERVICE_KEYS` كـJSON يربط caller IDs بمفاتيح مختلفة؛ header يبقى `X-API-Key`. مصدر الملكية هو المصادقة، وليس حقلًا يرسله PHP. [الأمثلة الكاملة وقواعد الأخطاء والاحتفاظ](../../docs/PHP_BACKEND_INTEGRATION_CONTRACT.md).

### Python-pull: جلب اختياري مستقل

لأداة جلب محلية فقط، اضبط URLs من إعداد الجامعة الفعلي:

```powershell
$env:ADVISOR_ENABLE_DIRECT_FETCH = 'true'
$env:ADVISOR_STUDENT_API_URL = '<actual-https-student-api-url>'
$env:ADVISOR_COURSES_API_URL = '<actual-https-courses-api-url>'
$env:ADVISOR_COURSES_QUERY_PARAMETERS = '<actual-json-query-parameter-mapping>'
$env:ADVISOR_API_TIMEOUT_SECONDS = '10'
$env:ADVISOR_BACKEND_TOKEN = '<optional-backend-bearer-token>'
```

خريطة المعاملات JSON تربط المفاتيح `student_id/degree_id/part_id` بأسماء معاملات Courses الحقيقية. لا توجد قيمة افتراضية للـURLs أو أسماء Courses. يمكن أن تكون الخريطة `{}` إذا كان ذلك عقد endpoint الفعلي. Student GET يستخدم `studentId` و`semesterId` كما في `BackendClient.fetch_inputs()`.

```python
from src.api.backend_client import BackendClient
from src.api.settings import ApiSettings

inputs = BackendClient(ApiSettings.from_env()).fetch_inputs(
    student_id="student-example", degree_id="degree-example", part_id=20251
)
```

هذا مثال استدعاء للأداة؛ لا تشغله على الجامعة بمعرفات المثال. يعيد العميل الردين وسياقي الجلب فقط، ولا يستكمل الدبلوم أو مصادر ساعات GPA أو سياسة التسجيل أو cutoff التوصية. تضيف الأداة المستدعية هذه البيانات الموثقة قبل إرسال الطلب المعتاد. لا يتغير مسار `/recommend` عند تفعيل الجلب، ولا يقبل الطلب URL.

URLs تتطلب HTTPS وعنوانًا عامًا. خيار `ADVISOR_ALLOW_LOCAL_BACKEND_HTTP=true` يسمح بـloopback للاختبار. العميل يفحص DNS ويثبت العنوان للاتصال مع TLS، ويرفض redirects وproxy من البيئة؛ حد الرد `8 MiB`. لا تطبع الردود أو tokens.

### الإعدادات الأخرى

| الإعداد | القيمة الافتراضية أو وظيفته |
|---|---|
| `ADVISOR_ENABLE_DIRECT_FETCH` | `false`؛ PHP-push لا يحتاج URLs |
| `ADVISOR_API_TIMEOUT_SECONDS` | `10` ثوانٍ للـsocket؛ لا يمثل SLA إنتاج |
| `ADVISOR_ALLOW_LOCAL_BACKEND_HTTP` | `false` |
| `ADVISOR_ENABLE_BACKTESTING` | `false`؛ backtesting يحتاج تفعيل البيئة وmode الطلب معًا |
| `ADVISOR_DIPLOMA_GPA_ALIASES` | `diploma_gpa,DIPLOMA_GPA` |
| `ADVISOR_DIPLOMA_TYPE_ALIASES` | `diploma_type_id,DIPLOMA_TYPE_ID` |
| `ADVISOR_PERFORMANCE_TEST_MODE` | `false` |
| `ADVISOR_PERFORMANCE_TEST_MAX_CANDIDATES` | بلا حد افتراضي؛ مطلوب عدد موجب عند تفعيل وضع اختبار الأداء |
| `ADVISOR_HISTORY_INCREMENTAL_ROOT` | `src.paths.FROZEN_HISTORY_INCREMENTAL_DIR` |
| `ADVISOR_HISTORY_BASELINE_SOURCE_ROOT` | `src.paths.FROZEN_HISTORY_DIR_V2` |
| `ADVISOR_HISTORY_UPDATE_MODE` | `manual` عند bootstrap؛ الإعداد الدائم له الأولوية لاحقًا |
| `ADVISOR_SERVICE_KEYS` | `{}` افتراضيًا؛ caller IDs ومفاتيح مستقلة، مع بقاء legacy key |
| `ADVISOR_REQUEST_STORE_PATH` | `PROJECT_ROOT/.api-state/requests.sqlite3`؛ منفصل عن البيانات والمودلات والتاريخ |
| `ADVISOR_REQUEST_PENDING_TTL_SECONDS` | `900` |
| `ADVISOR_REQUEST_PROCESSING_TTL_SECONDS` | `3600` |
| `ADVISOR_REQUEST_RESULT_TTL_SECONDS` | `86400` |
| `ADVISOR_REQUEST_MAX_COUNT` | `10000`؛ يشمل tombstones لمنع إعادة ID بعد expiry |
| `ADVISOR_REQUEST_MAX_PAYLOAD_BYTES` | `2097152` بايت |

في وضع اختبار الأداء، تجاوز عدد المرشحين المحدد يرفض التوصية كاملة؛ لا يقص المواد ولا يختصر التحقق. خارج هذا الوضع لا يُطبق هذا cap. حدود الأداء الفعلية وSLA والتشغيل متعدد workers تبقى `UNRESOLVED`. يوجد قفل inference واحد لكل process؛ الطلب المتزامن يُرفض بـ`503 INFERENCE_BUSY`.

تجميع الطلبات يدعم workers على المضيف نفسه باستخدام **قاعدة SQLite نفسها على قرص محلي**. لا يشمل تعدد المضيفين أو قواعد مستقلة لكل worker أو network filesystem. انتهاء TTL يزيل payload/النتائج ويبقي tombstones محدودة ضمن السعة؛ لا يُفتح ID قديم تلقائيًا لمحاولة جديدة. فشل worker أو انتهاء مهلة processing يعطي نتيجة غير محسومة محفوظة دون إعادة inference. تفعيل ID جديد قرار caller صريح. استخدم حساب خدمة خاصًا وACL مقيدة على Windows، ولا تسجل بيانات الطلب. استثناء `.api-state/` من Git يحمي المسار الافتراضي، وتبقى حماية أي path مخصص والنسخ الاحتياطية مسؤولية النشر.

## المواد والتوصية

`adapt_courses()` يفحص هوية جميع الصفوف والتكرار قبل تصفية غير المؤهلين. `IS_REQUESTABLE` و`ALLOW_REGISTER` يحتاجان `Y/N` صريحًا. التكرار المطابق يُزال، والمتعارض يُرفض حتى لو كانت إحدى النسخ غير مؤهلة. خصائص المادة تُراجع مع كتالوج degree+course، و`plan_course_type_id` يأتي من `course_type_id` وحده.

`attempt_number = ATTEMPTS_COUNT + 1`؛ نطاق العداد يجب أن يطابق عقد التدريب ويؤكده PHP عبر `attempts_scope_confirmed`. صفر محاولات مع نتيجة سابقة فارغة يعطي `NEW`. العداد الموجب يحتاج `FINISH_STATUS` السابق أو مصدرًا مستقلًا في `previous_course_statuses`؛ لا يستنتج الرسوب أو الانسحاب من العداد. عند وجود `LAST_REGISTER_SEMESTER_ID` يجب أن يسبق الهدف. حالات المصادر المتعارضة تُرفض.

`STATUS_REASON_CODE=EXCEPTION` يحتاج course ID في `approved_exception_course_ids`. `allowRegisterAllOptional=Y` يحتاج تأكيد تفسيره، ولا يلغي caps. `registration_policy` له مصدر وفصل مؤكدان و`load_profile=study|graduation` وfailed-repeat cap صريح. withdrawn cap اختياري وفق العقد الحالي، وغياب `MAX_NEW_COURSES` لا يصنع حدًا جديدًا.

| `requirement_group_modes` | قيد المجموعة |
|---|---|
| `strict_remaining` | `CREDITS_COUNT - REQUIREMENT_PASSED_CREDITS`؛ تجاوز passed للحد خطأ |
| `approved_overflow` | `max(0, maximum + approved overflow - passed)`؛ overflow صريح |
| `unbounded` | عدم وجود cap مؤكد؛ تمثيله الداخلي مجموع ساعات المرشحين بعد إزالة التكرار |

هوية المجموعة canonical JSON من `degree_id` و`REQUIREMENT_ID`. caps مجموعات المتطلبات مستقلة عن تصنيف المادة؛ cap التصنيف الداخلي يساوي مجموع ساعات مرشحيه.

`target_credits` أو `min_credits/max_credits` خياران متنافيان. يُحسب تقاطع المجال المطلوب مع قواعد التسجيل، ثم يصبح الحد الأعلى هدفًا دقيقًا: `12..18` يعني 18، دون النزول إلى 17 عند غياب خطة. `top_k` افتراضيًا 3 وفي المجال 1..50؛ النتيجة Top K داخل shortlist وليست ضمانًا على كل الخطط عالميًا.

`mode=normal` يحتاج `history_as_of_part` للفصل السابق مباشرة. `backtesting` الصريح والمفعّل يسمح بتاريخ أقدم، ويمنع الهدف والمستقبل. يجب أن يأتي الهدف بعد تدريب **كل** stage، وأن توجد حزمة cutoff المطلوبة وتكون متوافقة. لا fallback إلى أحدث حزمة أو أصول V1، وتثبت snapshot التاريخ أثناء الطلب.

## المسارات والتشخيص

واجهتا التحقق اختياريتان للتشخيص؛ التوصية تنفذ التحقق داخليًا ولا تتطلب استدعاءهما أولًا.

| المسار | المفتاح | الوظيفة |
|---|---|---|
| `GET /health` | دون مفتاح | صحة HTTP وجاهزية المودلات والتاريخ والكتالوج وGradeScale والتوصية |
| `POST /recommend` | `ADVISOR_API_KEY` | التوصية نفسها عبر alias |
| `POST /api/v1/recommendations` | `ADVISOR_API_KEY` | مسار التوصية السابق |
| `POST /api/v1/recommendation-inputs/student` | service key وصاحب العملية | تخزين الطالب وربطه بـrequest_id؛ يوصي إذا أكمل الزوج |
| `POST /api/v1/recommendation-inputs/courses` | service key وصاحب العملية | تخزين المواد؛ الترتيب مستقل |
| `GET /api/v1/recommendation-requests/{request_id}` | service key وصاحب العملية | استرجاع الحالة/النتيجة دون inference |
| `POST /api/v1/inputs/student/validate` | `ADVISOR_API_KEY` | تشخيص الطالب دون inference |
| `POST /api/v1/inputs/courses/validate` | `ADVISOR_API_KEY` | تشخيص المواد دون inference |
| `POST /api/v1/history/deltas/validate` | `ADVISOR_ADMIN_API_KEY` | تحقق Delta للقراءة فقط |
| `GET /api/v1/admin/history/status` | `ADVISOR_ADMIN_API_KEY` | حالة المخزن والتاريخ النشط |
| `PUT /api/v1/admin/history/mode` | `ADVISOR_ADMIN_API_KEY` | اختيار وضع التحديث |
| `POST /api/v1/admin/history/initialize` | `ADVISOR_ADMIN_API_KEY` | تهيئة baseline تراكمية معتمدة |
| `POST /api/v1/admin/history/preview` | `ADVISOR_ADMIN_API_KEY` | معاينة Delta وإصدار preview token |
| `POST /api/v1/admin/history/commit` | `ADVISOR_ADMIN_API_KEY` | نشر النسخة المكتملة بعد التأكيد |
| `POST /api/v1/admin/history/activate` | `ADVISOR_ADMIN_API_KEY` | تفعيل نسخة أو rollback مؤكد |
| `POST /api/v1/admin/history/finalization-events` | `ADVISOR_FINALIZATION_API_KEY` | حدث تثبيت الفصل من الجهة المؤتمنة |

كل POST وPUT محمي يستخدم `X-API-Key`. صلاحيات المفاتيح الثلاثة مستقلة، ومسارات الإدارة وstartup تحتفظ بعقودها السابقة.

تعرض واجهات التحقق `validation_status=valid|partial|invalid` و`validation_completed` و`checks` و`errors` و`unavailable_fields` و`summary`. `partial` قد يعود HTTP 200 مع `validation_completed=false`. لا يعيد التشخيص المدخلات الخام أو snapshot. `/health` لا يعني أن inference جاهز؛ افحص `recommendation_readiness.ready`.

| HTTP | أمثلة على النتيجة |
|---|---|
| `200` | توصية، `no_feasible_plan`، أو تشخيص valid/partial |
| `401 / 403` | مفتاح مفقود أو غير مخول |
| `422` | schema أو هوية أو مصدر أو cutoff أو مدخل أكاديمي غير صالح |
| `409` | تكرار أو Delta أو workflow متعارض |
| `503` | مصادقة غير مضبوطة، تبعية أو تاريخ غير متاح، أو worker مشغول |
| `500` | `INTERNAL_ERROR` برسالة عامة |

`DecimalRequest` يحفظ decimals عند قراءة JSON، و`DecimalRoute` يطبق ذلك على المسارات. الساعات تبقى `Decimal` أثناء القيود والبحث، ثم تُحوّل في موضع inference الأصلي. `json_safe()` يحول Decimal إلى سلسلة عند الرد. NaN/Infinity ممنوعة، وأخطاء schema والاستثناءات لا تكشف مدخلات أو paths أو أسرارًا.

## History Delta والإدارة

تحقق Delta يستخدم `part_id/rows/finalization?`. `finalization` شهادة الجهة الجامعية؛ وجود مجاميع سليمة لا يثبت تثبيت الفصل. دون تاريخ محمل يمكن فحص schema والمجاميع والبصمة، وتبقى lineage/replay/order غير متاحة. endpoint التحقق لا يكتب ولا ينشر ولا يفعل التاريخ.

المخزن التراكمي مستقل: تهيئة baseline معتمدة → preview → commit بتأكيد وtoken → activate بتأكيد وبصمة. `manual` هو الوضع الافتراضي، و`auto_on_finalization` يحتاج حدثًا موثوقًا بمفتاحه المنفصل. `commit` وحده لا يفعل النسخة. تبقى الحزم السابقة immutable، ولا تُصنع `points_sum` أو مجاميع تخصص غير متاحة.

راجع [عقد الإعدادات والتاريخ التراكمي](../../docs/API_CONFIGURATION_AND_CUMULATIVE_HISTORY.md) للتسلسل والحقول والـrollback، و[تقرير التنفيذ السابق](../../reports/api_cumulative_history.md) للأدلة وحدودها.

في تكامل PHP الجديد، Delta `part_id=20261` يضيف **نتائج20261 فقط** إلى تاريخ نشط حتى20253؛ يحتاج وجود20252 و20253 بعد baseline20251، ولا يقفز مباشرة من20251. التفعيل المعتمد يجعل `history_as_of_part=20261` متاحًا لتوصية `part_id=20262`. هذه عملية مشتركة للفصل لا تتكرر لكل طالب. [payload الجامعة وتسلسل PHP اليدوي والتلقائي](../../docs/PHP_BACKEND_INTEGRATION_CONTRACT.md).

## التحقق من إعادة التنظيم

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_api_adapters.py tests/test_api_http.py tests/test_api_integration.py tests/test_api_core_extensions.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

الاختبارات تستخدم سجلات اصطناعية وdependencies محقونة وتتحقق من الدقة والهوية والرفض قبل inference والـ33/47 والتاريخ والمصادقة. [REFACTOR_REPORT.md](REFACTOR_REPORT.md) يسجل المقارنة مع النسخة السابقة ونتائج التشغيل الفعلية؛ لا يُستنتج نجاح الإنتاج من أمثلة الاختبارات.
