# Academic Advisor — واجهة Streamlit الموحدة لتجربة 20251

بدأ التنفيذ: 2026-10-22. التحقق النهائي: 2026-10-24. الفرع: `new_branch`.

الحالة: **PASS — التنفيذ والتحقق المحلي مكتملان**. الواجهة والخدمة واختبارات التكامل منفذة. لم تُشغّل تجربة حقيقية لطالب أو للطلاب الثلاثين، ولم يُستدعَ أي endpoint جامعي، ولم يحدث تدريب للنماذج المشتركة أو Commit/Push/Merge.

## النتيجة وطريقة التشغيل

من جذر المشروع شغّل:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\tools\academic_advisor_streamlit\streamlit_app.py
```

داخل تبويب **تجربة توصية طالب** اختر `Pilot 20251 — Model Comparison`. بقي `Production FastAPI` الاختيار الافتراضي. Pilot يعمل مباشرة داخل Python ولا يحتاج تشغيل موقع Pilot أو خادمه على `8765`. مسار Production يحتفظ بخدمته الحالية على `8000`.

تحتفظ الواجهة بالتبويبات الثلاثة، وتضيف في Pilot:

- Snapshot واضح وافتراضي `after_backend_fix`؛ Before للتصفح فقط.
- العينة الأساسية 30 طالباً، وإظهار الاحتياط اختيارياً، وفحص Student/Courses/History قبل بدء التشغيل.
- اختيار مستقل للنماذج A/B/C، وافتراضي B/C. تسمية A هي `Historical Baseline / Diagnostic Only`، ولا تنتقل إعداداته إلى Production.
- ساعات مطابقة بدقة، افتراضي 18 ضمن عقد Runner القائم `(0,36]`، وميزانية 200 أو 1000 أو 2000 خطة. لا تخفيض تلقائي للساعات.
- أزرار مستقلة لتقييم الطالب، وكامل العينة الأساسية، والمجموعة الصالحة صراحةً عند نقص بعض الاستجابات.
- Run ID، تقدم الدفعة وحالة كل طالب/مودل، وتصفح التشغيلات المحفوظة مع Snapshot وعائلة التجربة. التحديث أو التنقل لا يبدأ التشغيل من جديد.
- بطاقات مقارنة، أفضل ثلاث خطط بالترتيب المحفوظ، تفاصيل المواد، التطابق ونسبته، ومقارنة منفصلة للخطة الفعلية.
- عرض سيناريو مستقل للنتائج التشخيصية القديمة: `candidate_mode / credit_experiment`. لا يبدأ مسار التشغيل العادي حقن مواد فعلية.

## الربط مع Pilot القائم

```text
streamlit_app.py -> pilot_ui.render_pilot()
    -> PilotService.start()
       -> ComparisonRunner.start() -> single-worker executor
          -> PilotEngine.evaluate_student(models=...)
          -> post-score enrichment: ObservedPlanStore + ObservedPlanPredictor
          -> existing recommendation/actual-plan metrics
          -> RunStore.save(): full results + compact presentation + completion receipt
    -> progress(), list_runs(), load_run(), presentation()
```

الخدمة لا تحتوي خوارزمية scoring أو features أو GradeScale أو توليد أو ترتيب خطط. تعيد استخدام `PilotEngine` و`ComparisonRunner` و`ObservedPlanPredictor` و`actual_metrics` مباشرة. بقيت الواجهة المستقلة لـPilot متاحة.

أضيف `models=None` بصورة متوافقة مع الاستدعاءات السابقة: الحذف يعني A/B/C كما سابقاً. عند تمرير الاختيار تُنفّذ inference للنماذج المختارة فقط. توليد الخطط يحدث مرة واحدة، وتستخدم جميع النماذج المختارة `plan_set_sha256` و`shared_inputs_sha256` نفسيهما. قد يحمّل مكوّن B/C المشترك artifacts الحزمة معاً، لكن لا يسجّل ذلك كتقييم للنموذج غير المختار.

الخدمة مورد واحد عبر `st.cache_resource(max_entries=1)`، مع تنفيذ متسلسل، وقفل للحالة، وإعادة استخدام المحرك، وحدود 64 حالة تشغيل و64 خطة فعلية مخبأة و8 تشغيلات محفوظة مختصرة. Session State الخاص بـPilot يحتوي المعرّفات والخيارات فقط. لا توجد `st.cache_data` لاستجابات الطلاب أو النتائج الكاملة، ولا تسجّل أخطاء العمال السجلات الخام أو تفاصيل الاستثناءات الحساسة.

## فصل التوقعات والمقاييس

تعرض الواجهة بوضوح ثلاثة سياقات:

1. معدل متوقع لخطة بديلة، وتوقعات مواد محسوبة في تركيب تلك الخطة.
2. معدل وتوقعات للخطة المسجلة الفعلية كاملةً، عبر `ObservedPlanPredictor` المستقل عن البحث والأهلية.
3. معدل وصفي محسوب للخطة الفعلية من `actual_points × course_credits / total credits` عند اكتمال النقاط والنتائج الصالحة لجميع المواد.

تُقرأ النتائج الفعلية بعد انتهاء scoring للخطط البديلة. الذي يدخل predictor الفعلي هو هوية المواد والساعات فقط؛ لا تدخل العلامات أو النقاط أو حالات النتيجة إلى توليد البدائل أو scoring لها. لا يعرض أي معدل مرصود لخطة بديلة لم يسجلها الطالب. العلامة الفعلية في جدول البديل مقصورة على مادة فعلية مطابقة ذات نتيجة صالحة.

المعدل الرسمي يبقى `N/A — OFFICIAL_SEMESTER_GPA_POLICY_NOT_VERIFIED`؛ المعدل الوصفي ليس إعلاناً عن معدل رسمي، ولا يوجد إسقاط تراكمي دون denominator وسياسة الإعادة. عند نقص النتائج يبقى المعدل الكامل `N/A`، ويعرض متوسط الجزء ذي النتائج بعنوان وسبب منفصلين.

تعرض الأخطاء بإشارة `prediction − actual`، والخطأ المطلق للمعدل، وMAE/RMSE/Bias على أزواج العلامات الصالحة، مع عدد المواد والتغطية. القيم الغائبة تبقى `N/A` مع السبب. سحب نسخة B/C يحجب التوقعات ومشتقات أخطائها أيضاً، وتُبطل ذاكرة قراءة النتائج عند تغير سجل النسخ المسحوبة.

## الأزمنة وحدود البحث

تعاد الاستفادة من timing delegates الموجودة في `actual_experiment.py`، دون استخدام `ActualCandidateEngine` أو مسار الحقن. تعرض الواجهة:

- تحضير المرشحين، توليد الخطط، وتحضير سياق الخطط المشترك من timers المحرك.
- feature preparation، inference وتحويل GradeScale، وترتيب/تجميع النتائج لكل مودل.
- زمن المودل للبدائل، وزمن التوقع الفعلي المحفوظ بصورة منفصلة.
- `comparison_wall_seconds` لكل طالب، شاملاً enrichment، و`run_completion.json.total_wall_seconds` للتشغيل شاملاً تهيئة المحرك والتقييم والحفظ، ومستثنياً انتظار الطابور.
- عدد الخطط التي أكمل المودل scoring لها، وحالات البحث وميزانيته وسبب القطع.

زمن features هو تحضير المرشحين وما يتبقى من وقت scorer بعد استبعاد نداءات inference/GradeScale المقاسة، ويشمل overhead معالجة الإطارات؛ ليس قياس profiler حصرياً لكل دالة feature. زمن ranking يشمل التجميع والتحويل إلى صيغة العرض. هذه الأزمنة متداخلة مع الإجماليات ولا تُجمع باعتبارها مستقلة. الأزمنة التي لم يقسها التشغيل القديم تبقى `N/A`.

تظهر حالات تحميل العرض المخبأ وتوقع الخطة الفعلية المخبأ. عند استخدام توقع مخبأ يبقى زمن التوقع الأصلي معلماً بوصفه قيمة محفوظة، ولا يُنسب إلى وقت إعادة الحساب الحالية. فشل التخزين يسجل `run_failure.json` في Run الجديد فقط، وتظهر حالته `failed` حتى بعد إعادة تحميل الخدمة؛ لا يُعرض كتقييم ناجح.

## سلامة Snapshot ومسارات الحفظ الفعلية

تستخدم الخدمة `snapshots.py` وعمليات التحقق الموجودة، ولا تُنشئ اصطلاح مسارات آخر. بالنسبة إلى:

```text
D:\AI\Real projects\Academic_Advisor_Simple\data\evaluation\recommendation_pilot_20251\
```

المسارات هي:

| الغرض | المسار تحت جذر Pilot |
|---|---|
| Student/Courses بعد الإصلاح | `snapshots/after_backend_fix/api_data/students/<sample_id>/` |
| History بعد الإصلاح | `snapshots/after_backend_fix/api_data/frozen_history/` |
| المقارنات الجديدة | `experiments/after_backend_fix/comparison/<Run ID>/` |
| الأرشيف المقروء | `experiments/before_backend_fix/comparison/` و`actual_candidate_injection/`، وجذور التوافق القائمة |
| حزمة B/C المشتركة الحالية | `before_backend_fix/experiments/model_versions/`، عبر resolver القائم |

الحزمة المشتركة هي `bc_20261019T163245_0226716d`، وSHA-256 للـmanifest في المؤشر `727c6cb6dfd763bfece38b269957691a1237724741b8328a3b7caf3d2d46dfb2`. لم يتغير المؤشر أو الحزمة أو GradeScale أو Frozen History artifacts. A يبقى scorer الرسمي التاريخي V2 ذي 47 feature؛ B/C الحزمة المعزولة ذات 44/47 feature، دون إعادة تدريب.

كل تشغيل جديد يستعمل Run ID فريداً وكتابة حصرية؛ لا يستبدل القديم. يضاف `presentation_results.json` مختصر لأفضل ثلاث خطط في التشغيلات الجديدة فقط. قراءة القديم تُسقطه في الذاكرة دون إعادة كتابته أو إثرائه باستجابات أحدث. Before ممنوع عند بدء التقييم وممنوع في حفظ RunStore. استجابة Courses الغائبة من After تؤدي إلى `MISSING_SNAPSHOT_RESPONSE` مع العينة والحقل، دون الرجوع إلى Before.

بقي تبويب الجمع ومسار الحفظ السابق: After افتراضياً، وتجاوز verified captures دون overwrite، وتقييم Pilot يقرأ الملفات الناتجة. لم نعد جلب Frozen History.

الفحص المحلي بتاريخ 2026-10-24: **Student 30/30، Courses 30/30، History files 15/15، والعينة الصالحة 30/30**. جودة صفوف History تحمل `PARTIAL` مع `usable_for_b_c=true` وفق سياسة Pilot الحالية لعزل الصفوف غير الصالحة؛ لم تُغيّر هذه السياسة. يوجد 29 تشغيل أرشيفي قابل للتصفح، ولا يوجد أي تشغيل After حقيقي جديد.

مقارنة SHA-256: **1468 ملفاً محمياً، 7,199,939,413 بايت، صفر اختلافات**. يشمل ذلك snapshots، التشغيلات السابقة والأصول القديمة، المودلات/artifacts، `src`، `ui_client.py`، cohort وتقرير الترحيل السابق. تقرير الترحيل السابق محفوظ كما كان؛ إحصاء Courses الغائبة فيه يمثل وقت إنشائه، والفحص الحالي أعلاه يخص الملفات التي جُمعت لاحقاً.

## الأدلة والاختبارات

أدلة التدقيق المحلية تحت:

```text
data/evaluation/recommendation_pilot_20251/unified_integration_audits/unified_20261022T115611/
```

| الدليل | النتيجة |
|---|---|
| `protected_before.json` / `protected_verification.json` | الملفات المحمية متطابقة |
| `protected_additions_check.json` | لا ملفات جديدة داخل snapshots/models/artifacts/src/experiments أو الأصل القديم؛ صفر تشغيلات After حقيقية |
| `production_ast_parity.json` | مسار توصية Production مطابق بنيوياً لـHEAD، 9 statements، عدا غلاف اختيار الوضع |
| `app_test_evidence.json` / `verify_layout.py` | AppTest فعلي على cohort المحفوظ: 3 تبويبات، 30 خياراً، After وB/C و18 ساعة افتراضياً، Before للقراءة فقط، لا HTTP ولا تهيئة مودلات ولا تشغيل عند rerender |
| `test_pilot_20251_selection.py` | جميع الاختيارات السبعة، plan hashes، course predictions وTop-3 متطابقة؛ لا scoring لغير المختار؛ reuse/progress/compact/failure persistence |
| `test_unified_pilot_service.py` | GPA/coverage/overlap/NA، عدم fallback، Before read-only، إثراء بعد scoring، السيناريوهات وسحب النسخ |
| `test_unified_pilot_integration.py` | 3 اختبارات: خدمة وRunner ومحرك وpredictor حقيقيون على fixture اصطناعي؛ B/C feature pipeline الأصلي مقابل timing delegates، بتطابق matrices/points/plan context، دون تدريب |
| Streamlit AppTest | 20 ناجحاً؛ Production form، عدم HTTP، الاختيارات، الدفعة/rerender، النتائج والسيناريوهات، الفشل، fractional credits، والعمل المحلي عند تعطل إعداد Production |

نتيجة الاختبارات ذات الصلة قبل الإضافات النهائية للعرض: **279 passed**. المراجعة المستقلة الأخيرة للخدمة/التنفيذ/التكامل: **33 passed**، دون ملاحظات جوهرية باقية.

الجولة الشاملة الأولى: **1875 passed, 1 skipped, 6 subtests passed** خلال **351.73 ثانية**. التحذير الوحيد deprecation موجود لـFastAPI/Starlette TestClient. التجاوز اختبار حماية POSIX للملفات على Windows، حيث يعتمد المشروع ACLs لحساب الخدمة.

أمر الجولة الشاملة النهائية:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache/uall_final
```

النتيجة النهائية على آخر نسخة من الكود: **1878 passed, 1 skipped, 1 warning, 6 subtests passed** خلال **221.70 ثانية**، كما في `full_suite_final.txt`. يتضمن ذلك اختبارات AppTest العشرين. تمت الاستعانة بتنفيذ الاختبارات المحلية خارج قيد Windows socketpair عند الحاجة؛ هذا لا يفعل اتصالات جامعة أو تشغيل تجربة فعلية. `git diff --check` ناجح؛ تحذيرات line endings فقط. تم `graphify update .` باستخراج AST محلي بلا API.

## الملفات التي عُدلت أو أُضيفت لهذا الدمج

هذه القائمة تخص الدمج الحالي؛ يحتوي Git أيضاً تغييرات قديمة من ترحيل snapshots والتشخيص لم تُحذف أو تُستبدل.

| الملف | التغيير |
|---|---|
| `tools/academic_advisor_streamlit/streamlit_app.py` | اختيار الوضع وغلاف Pilot؛ إتاحة Pilot المحلي إذا رفض إعداد Production |
| `tools/academic_advisor_streamlit/pilot_service.py` | خدمة orchestration وعرض النتائج المحفوظة |
| `tools/academic_advisor_streamlit/pilot_ui.py` | واجهة Pilot العربية ضمن Streamlit |
| `tools/recommendation_pilot_20251/selection.py` | تحقق مشترك من اختيار النماذج |
| `tools/recommendation_pilot_20251/adapter.py` | قراءة طلاب الاحتياط اختيارياً، مع default primary السابق |
| `tools/recommendation_pilot_20251/engine.py` | selective execution وtimers؛ التوليد والتوقع والترتيب كما هي |
| `tools/recommendation_pilot_20251/observed_prediction.py` | اختيار النماذج وcache bounded مع provenance، والمحافظة على مسار الخطة الكاملة |
| `tools/recommendation_pilot_20251/runner.py` | callback بعد scoring، reuse، تقدم محدود، compact saved view، إيصال الزمن وحالات الفشل |
| `tools/recommendation_pilot_20251/actual_metrics.py` | وسيط models اختياري؛ المعادلات دون تغيير |
| `tests/test_pilot_20251_selection.py` | اختبارات الاختيار والتطابق وحفظ التنفيذ |
| `tests/test_unified_pilot_service.py` | اختبارات الخدمة والعرض |
| `tests/test_unified_pilot_integration.py` | اختبارات التكامل وtiming delegates |
| `tools/academic_advisor_streamlit/tests/test_unified_pilot_ui.py` | AppTest للواجهة الموحدة |
| `docs/superpowers/plans/2026-10-22-unified-streamlit-pilot.md` | خطة التنفيذ والعقود |
| `reports/unified_streamlit_pilot_integration.md` | هذا التقرير |
| ملفات `graphify-out/` المولدة | تحديث AST المطلوب؛ بقيت النسخ الاحتياطية القائمة |

## الحدود المتبقية

- **الإعداد المحلي الحالي لـ`ADVISOR_UI_BACKEND_HEADERS` غير صالح وفق Config القائم.** لم نعدل `.env` أو credentials. يمكن فتح Pilot المحلي رغم ذلك؛ يبقى Production والجمع الحي بحاجة إلى تصحيح إعداد الاتصال. اختبار Production هنا offline باستخدام Config صالح وHTTP fixtures؛ لم ندع تشغيل endpoints الحية.
- لم تُشغّل تجربة الطالب أو دفعة الثلاثين الحقيقية؛ أنت تبدأها بعد مراجعة التغييرات. تأكيد التطابق مبني على fixtures ثابتة ومقارنة scoring/feature matrices/Top-3 وبصمات المودلات، وليس نتيجة قياس جديدة على الثلاثين.
- الخطط تحليلية `PROVISIONAL`، والبحث prefix حتمي محدود؛ لا يثبت optimum عالمياً أو صحة التسجيل. لم نغيّر سياسات الأهلية أو features أو ranking أو Frozen History activation.
- القيم غير الموجودة في تشغيل قديم تظل N/A؛ لا نعيد حسابه باستجابات جديدة. تصفح archive كبير قد يحتاج قراءة ملفه الكامل مرة قبل إسقاطه في الذاكرة؛ لا يعاد حفظه.
- الحالة الحية مستقرة بين rerenders في عملية Streamlit نفسها. لا توجد آلية جديدة لاستئناف مهمة انقطعت بسبب إنهاء العملية؛ تبقى التشغيلات التي اكتمل حفظها قابلة للتحميل.
- بوابة اكتمال snapshots/history المشتركة مطبقة حتى على A-only؛ بعد اكتمالها تُنفّذ A وحده دون B/C inference. الاحتياط الذي لا يملك captures صالحة يظهر محظوراً.
- تحديث تقدم العامل يدوي بزر التحديث؛ لا يُعاد بدء الدفعة أثناء التحديث.
