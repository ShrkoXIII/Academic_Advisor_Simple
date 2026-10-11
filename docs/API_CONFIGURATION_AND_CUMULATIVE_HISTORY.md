# API configuration and cumulative Frozen History

التغيير المعتمد بتاريخ 2026-10-11 يضيف إعداد اتصال اختياري وإدارة تاريخ تراكمية إلى API الحالية. يبقى PHP-push افتراضيًا، وعقد `POST /api/v1/recommendations` واستراتيجية `pareto v1 → pareto v1` و`top_k=3` كما هي. لا تدريب ولا تعديل لميزات 33/47 أو ملفات المودلات.

## اتصال الجامعة

في PHP-push، PHP يوثق المستخدم ويتحقق من صلاحيات الطالب والاختصاص، ويجلب الردين ويرسل سياقي الجلب المستقلين إلى FastAPI. Python يتحقق من الاتساق؛ لا يستنتج صلاحيات المستخدم الجامعية من مفتاح الخدمة.

Python-pull اختياري للاختبار المحلي من `BackendClient(ApiSettings.from_env()).fetch_inputs(student_id=..., degree_id=..., part_id=...)`. يعيد envelope داخليًا لتمريره إلى واجهات التحقق الحالية؛ لا يضيف URL إلى طلب HTTP ولا ينشئ مسار توصية جديدًا. على أداة الاختبار المحافظة على سرية الرد وعدم طباعته أو تسجيله. Student GET يستخدم `studentId` و`semesterId`، وCourses GET يستخدم URL وخريطة query parameters يحددها مشغّل الخدمة صراحةً؛ لا endpoint أو أسماء معاملات مفترضة للمواد.

| متغير البيئة | الدلالة والافتراضي |
|---|---|
| `ADVISOR_API_KEY` | مفتاح PHP-push العادي؛ secret خارج Git |
| `ADVISOR_ADMIN_API_KEY` | مفتاح إداري مستقل؛ secret خارج Git |
| `ADVISOR_FINALIZATION_API_KEY` | مفتاح مستقل للجهة التي ترسل حدث تثبيت فصل؛ لا مفتاح خدمة أو إدارة عادي |
| `ADVISOR_ENABLE_DIRECT_FETCH` | `false`؛ عدم ضبط URLs لا يؤثر على PHP-push |
| `ADVISOR_STUDENT_API_URL` | URL الطالب من deployment environment؛ بلا قيمة افتراضية |
| `ADVISOR_COURSES_API_URL` | URL المواد الحقيقي من الجامعة؛ بلا قيمة افتراضية |
| `ADVISOR_COURSES_QUERY_PARAMETERS` | JSON يربط مفاتيح `student_id/degree_id/part_id` بأسماء المعاملات الحقيقية؛ مطلوب صراحةً حتى لو `{}` |
| `ADVISOR_API_TIMEOUT_SECONDS` | `10`؛ مهلة socket موجبة ومحدودة رياضيًا، تشمل الاتصال/القراءة وليست SLA إنتاج |
| `ADVISOR_BACKEND_TOKEN` | Bearer token اختياري في `Authorization` للردين؛ لا يوضع في URL |
| `ADVISOR_ALLOW_LOCAL_BACKEND_HTTP` | `false`؛ عند تفعيله يسمح بـHTTP/HTTPS على loopback للاختبار فقط |
| `ADVISOR_HISTORY_INCREMENTAL_ROOT` | افتراضيًا `src.paths.FROZEN_HISTORY_INCREMENTAL_DIR`: `data/artifacts/history_incremental/` |
| `ADVISOR_HISTORY_BASELINE_SOURCE_ROOT` | افتراضيًا `src.paths.FROZEN_HISTORY_DIR_V2`؛ مصدر migration معتمد، وليس path في الطلب |
| `ADVISOR_HISTORY_UPDATE_MODE` | `manual`؛ bootstrap فقط، والإعداد المحفوظ دائمًا له الأولوية بعد إنشائه |

URLs الإعداد لا تسمح بـuserinfo أو query أو fragment. العميل يتحقق من جميع عناوين DNS، ويرفض العناوين الخاصة والمحجوزة وmetadata endpoints؛ الاستثناء الاختياري خاص بـloopback. الاتصال يثبت عنوان IP الذي فُحص مع TLS/SNI وHost الأصليين، فلا يعيد DNS بين الفحص والاتصال. لا proxy من البيئة ولا متابعة redirects، والأخطاء لا تعيد URL أو الرد الخام أو token. حد الرد 8 MiB. المنظومة لا تقبل URL من الطالب أو PHP داخل payload.

## مقام GPA وتوقيته

| الحقل الجامعي | المعنى المعتمد |
|---|---|
| `START_TOTAL_IN_CREDITS` | ساعات النجاح/الإكمال السابقة؛ ليست مقام GPA |
| `TOTAL_REG_CREDITS` | الساعات المسجلة التي يحتسبها GPA رسميًا، حسب الاستثناءات الجامعية وتوقيت اللقطة |
| `START_AGPA_POINTS` | GPA التراكمي عند بداية فصل الهدف |
| `SEMESTER_REG_CREDITS` | ساعات تسجيل فصل الهدف؛ لا تثبت منفردةً الساعات الداخلة في GPA |

`integration_context.total_reg_credits_source` يوثق المصدر، `target_part`، `as_of_part`، و`timing` مع `rules_reference`. `beginning_of_semester` يتطلب الهدف نفسه وcutoff الفصل السابق؛ عند ثبوت ذلك يزوّد `TOTAL_REG_CREDITS` مباشرةً `prior_total_reg_credits` و`current_gpa_credits`، فلا يلزم supplement مكرر. Supplement مخالف يُرفض.

`end_of_semester` يتطلب `as_of_part` يساوي الهدف، و`semester_complete=true`، و`additive_credit_accounting=true` تحت قواعد جامعية موثقة، و`semester_gpa_counted_credits` الموثق للفصل. حينها فقط: `prior GPA-counted credits = TOTAL_REG_CREDITS - semester_gpa_counted_credits`. هذه شهادة PHP على القواعد والمصدر، وليست إثباتًا تستخلصه Python من الأرقام وحدها. إذا أثرت الإعادات/الاستثناءات في مجموع الماضي بحيث لا يكون الجمع إضافيًا، يُرفض الاشتقاق.

مثال 20251: `129` بعد الفصل و`18` ساعات تسجيل لا يكفيان لإثبات `111`. تصبح عملية الطرح مقبولة فقط إذا ثبت اكتمال الفصل وقواعد الجمع وأن **18 كلها** GPA-counted. لا يُستخدم `START_TOTAL_IN_CREDITS` أو `108` أو `111` مقامًا تلقائيًا. يبقى sourced override `integration_context.student_values.current_gpa_credits` للحالات التي لا يوفر فيها الرد الأصلي بداية موثوقة، بشرط المصدر وcutoff الصحيحين وعدم التعارض مع قيمة رسمية مثبتة.

تدقيق التدريب: `add_student_history_features()` ينقل `total_reg_credits` من جدول status الأصلي مباشرةً إلى `prior_total_reg_credits`، ثم يستخدمه في الميزات الأصلية مثل fail-credit ratio؛ الاسم وحده لا يثبت توقيت لقطة المصدر التدريبي. عقد inference المقصود يحتاج بداية الفصل، وتصحيح Adapter يثبت هذا التوقيت دون إعادة تعريف العمود أو إعادة بناء بيانات التدريب. يلزم تأكيد جامعي لتوقيت هذا الحقل في export التدريب قبل إعلان التكافؤ الدلالي الكامل؛ لا يعالج ذلك بتغيير المودلات ضمن هذه المهمة. بيانات تاريخ الطالب تنتهي قبل الهدف؛ نتائج الهدف والمستقبل لا تدخل lags/gaps. قواعد استبدال علامات الإعادة موضوع منفصل عن تصحيح مقام التسجيل.

## المحاولات والحالة السابقة

| السابقة | `FINISH_STATUS` | التصنيف |
|---|---|---|
| `ATTEMPTS_COUNT=0` | null | `NEW` |
| `ATTEMPTS_COUNT=0` | نتيجة سابقة غير null | تعارض يُرفض |
| `ATTEMPTS_COUNT>0` | حالة جامعية معروفة | `normalize_previous_status()` الأصلي |
| `ATTEMPTS_COUNT>0` | null/مفقود | رفض، إلا إذا توفر مصدر سابق authoritative منفصل |

يبقى `attempt_number = ATTEMPTS_COUNT + 1`. العداد وحده لا يعني رسوبًا أو انسحابًا. إذا وجد `LAST_REGISTER_SEMESTER_ID` يُراجع أنه قبل الهدف؛ وإذا وجد supplement وحالة أصلية يجب أن يتطابقا. سياق Courses الموثق يثبت أن الحالة المعطاة هي السابقة ذات الصلة؛ الكتالوج والقيود والتفويضات الأصلية لا تتغير.

## مخزن التاريخ التراكمي

```text
data/artifacts/history_v2/              # محفوظ بلا تعديل، ومصدر سابق/تاريخ backtesting
data/artifacts/history_incremental/
  control.json                          # mode، pointer النشط، pending، successes/failures؛ كتابة ذرية
  .workflow.lock                        # قفل OS يحرر تلقائيًا عند انتهاء العملية
  as_of_20251/                          # cumulative approved baseline
    course_history_state.pkl
    metadata.json
  as_of_20252/                          # baseline + finalized delta 20252
  as_of_20253/                          # previous + finalized delta 20253
  as_of_20261/                          # previous + finalized delta 20261
```

اسم metadata الفعلي يتبع `src.paths.history_metadata_path()`؛ لا يغيّر هذا المخزن تنسيق الحزم الموجود. يجري ترحيل نسخة **تراكمية** معتمدة عبر نهاية 20251 من المصدر المحدد في إعداد الخدمة، بعد فحص بصمة metadata والحالة والمجاميع ووجود تاريخ سابق و20251 معًا وتوافق عقود V2. لا تكفي حزمة مكونة من نتائج 20251 وحده. لا إعادة بناء من الصفوف الفردية أو صناعة مجاميع ناقصة؛ completeness الجامعة تتطلب موافقة المصدر المرجعية.

بعد الترحيل، التحديث هو aggregates فقط. `count/mark_sum/fail_count/attempt_sum/retake_count` وحقول المفاتيح والـcredits الحالية تبقى كما هي؛ الماضي يحتفظ بأوزانه والتحديث الجديد بوزنه الأصلي. لا `points_sum` تقديري ولا specialty history مفترض. أي حزمة تتطلب ميزات specialty غير المتاحة تُرفض قبل التفعيل.

النشر يعيد استخدام `FrozenHistoryManager` و`save_frozen_history_atomic()`: validate → clone → add → stage → reload/hash/aggregate verification → publish immutable directory. النشر لا يبدل pointer الخدمة ولا يسمح بتوصية من النسخة المحفوظة قبل تفعيلها. التفعيل عملية منفصلة تراجع النسخة المكتملة وبصمتها وتوافق artifacts ثم تبدل pointer ذرية وتسجل بصمتها في `activated_versions`. العمليات تسلسلية بين threads/processes بواسطة قفل نظام ملفات محلي؛ القراءة تثبت snapshot واحدة في الطلب. النسخ المكتملة لا تستبدل، وفشل التحديث يحفظ pointer السابق.

إذا نُشرت baseline ثم فشلت كتابة pointer، إعادة initialize تستطيع اعتماد النسخة الموجودة فقط بعد تطابق المصدر والبصمات والاعتماد والـmetadata والمجاميع والتوافق بالكامل. لا تستبدل النسخة أو تقبل اعتمادًا مختلفًا؛ يعود `baseline_recovered:true` عند الاستعادة. العمال الذين بدأوا قبل التهيئة يتبنون المؤشر الدائم قبل الخدمة، ولا يحتاجون إلى تلقي عملية الإدارة نفسها. تلف pointer أو بصمته يعطل جاهزية التاريخ والتوصية، وتبقى صحة HTTP والتحقق من البنية مستقلين.

cutoff التدريب يقيد فصل الهدف، وليس أحدث تاريخ خدمة صالحًا: الهدف يجب أن يأتي بعد تدريب المودلات وبعد تاريخ الخدمة. `as_of_20261` يخدم أهدافًا بعد 20261؛ لا توصية 20261 نفسها. `normal` يحتاج الفصل السابق بالضبط ولا يسمح بنسخة أحدث من pointer النشط بعد rollback. `backtesting` صريح ومفعّل يسمح بتاريخ أقدم من الهدف، ويستطيع اختيار نسخة سبق تفعيلها قبل rollback؛ لا يتيح نسخة لم تُفعّل قط. التاريخ السابق لـ20251 يأتي بالـcutoff نفسه من المصدر القديم للقراءة فقط. CLI السابق ومسارات التاريخ الافتراضية القديمة لا تتغير.

## عقد الإدارة مع PHP

PHP يوثق المشرف ويفحص صلاحياته الجامعية قبل إرسال المفتاح الإداري؛ لا يضع المفاتيح في متصفح الطالب أو logs. المرجع النهائي شهادة الجهة الجامعية وليس استنتاجًا من وصول JSON. جميع الطلبات التالية strict؛ paths وURLs غير مقبولة في الطلب.

| المسار | المصادقة | المدخل |
|---|---|---|
| `GET /api/v1/admin/history/status` | admin | بلا body |
| `PUT /api/v1/admin/history/mode` | admin | `{mode: disabled|manual|auto_on_finalization}` |
| `POST /api/v1/admin/history/initialize` | admin | `expected_source_hash, approval_reference, confirmation:true, cumulative_history_confirmed:true` |
| `POST /api/v1/admin/history/preview` | admin | عقد Delta الحالي: `part_id, rows, finalization?` |
| `POST /api/v1/admin/history/commit` | admin | عقد Delta مع finalization، و`preview_token, confirmation:true` |
| `POST /api/v1/admin/history/activate` | admin | `history_as_of_part, expected_history_sha256, confirmation:true, rollback:false` |
| `POST /api/v1/admin/history/finalization-events` | finalization | عقد Delta مع finalization وapproval reference |
| `POST /api/v1/history/deltas/validate` | admin | endpoint السابق؛ read-only بلا pending/commit/activation |

status يعرض mode المحفوظ، cutoff وبصمة pointer، النسخ المتاحة والنسخ التي سبق تفعيلها، آخر نجاح، pending fingerprints/cutoffs، failures الآمنة والتوافق أو عدم توفر artifacts. لا rows خاصة أو paths أو نص استثناءات خام. الفشل المتوقع في mode/lineage/confirmation/compatibility يُرفض؛ تبقى HTTP والواجهات التشخيصية مستقلة عن جاهزية المودلات. التحقق read-only في المخزن التراكمي يفحص الفصل التالي نفسه دون كتابة pending أو control.

Manual sequence:

1. اضبط mode=`manual` من واجهة PHP الإدارية.
2. عند أول migration فقط، راجع المصدر التراكمي 20251 وبصمة `metadata.json` واعتماد الجامعة، ثم initialize مع `confirmation:true` و`cumulative_history_confirmed:true`. التصريح الأخير يقر باكتمال جميع السوابق المعتمدة، ويُسجّل الاكتمال `admin_attested`؛ فحص المجاميع وحده لا يثبت اكتمال الجامعة. لا path من الطلب ولا إعادة كتابة المصدر.
3. استلم aggregates الفصل النهائي وapproval reference الموافق لنفس `part_id`.
4. شغّل endpoint التحقق read-only، ثم preview واحفظ `preview_token` وبصمة Delta وcutoff الأساس والمقترح.
5. اعرض هذه البيانات للمشرف ثم اطلب تأكيده الصريح؛ commit يحمل payload نفسه وtoken المعاينة. تغيّر الأساس أو البصمة يرفض الطلب.
6. راجع النسخة المكتملة وhash الناتج. commit لا يفعلها.
7. activate بالـcutoff والـhash المعتمد والتأكيد. النسخة تصبح متاحة لعمليات الخدمة التالية دون تعديل snapshots الجارية.

Automatic sequence:

1. المشرف يختار `auto_on_finalization` في المخزن الدائم.
2. الجهة المؤتمنة ترسل حدث تثبيت حقيقي بمفتاح finalization، ومرجع اعتماد، وDelta كامل.
3. تحقق البنية والمجاميع والفصل التالي والتوافق والبصمة؛ طبق مرة واحدة ثم فعّل النسخة المكتملة ذرّيًا.
4. التكرار بنفس البصمة idempotent، والمختلف أو خارج الترتيب يرفض. مجرد وصول البيانات لا يطلق هذا المسار؛ endpoint manual commit لا يستبدل حدث finalization.

في `disabled` تُمنع initialize/commit/activation والحدث التلقائي؛ يبقى status وتغيير mode والتحقق read-only متاحًا للمخول. rollback يحتاج activate لنسخة موجودة متوافقة بالـhash و`rollback:true` وتأكيد؛ لا يحذف النسخ الأحدث.

## حدود الإثبات

الاختبارات المحلية تثبت العقود والتسلسل والحماية باستخدام بيانات اصطناعية؛ لا اعتماد إنتاج تلقائي. تبقى URL/معاملات Courses وآلية مصادقة الجامعة، قواعد GPA-counting/exclusions/additivity، مرجع اكتمال baseline وتثبيت الفصل، صلاحيات PHP وTLS ونشر متعدد العمليات/SLA مسؤوليات أو بيانات تشغيل جامعية. [تقرير التنفيذ والاختبارات](../reports/api_cumulative_history.md).
