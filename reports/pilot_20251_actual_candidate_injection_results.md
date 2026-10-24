# Pilot 20251 — Actual-Course Candidate Injection Results

**DIAGNOSTIC ONLY — ACTUAL COURSES WERE INJECTED**

هذه مقارنة تشخيصية تعتمد على اختيارات الطالب بعد حدوثها. زيادة التقاطع لا تثبت تحسن التوصية أو الأهلية التاريخية، ولا تمثل `Historical Backtest` صالحًا. كل الأرقام أدناه مشتقة من ملفات التشغيل المحفوظة، دون تنبؤ جديد من مولد التقرير.

## 1. What Changed

أُضيف اتحاد مرشحات مؤقت في الذاكرة إلى موقع Pilot الموجود، مع اختيار `Original API` أو `Actual-Course Augmented` ومقارنة الوضعين للطالب نفسه. استُخدمت النماذج المحفوظة A/B/C وترتيبها المستقل وأفضل ثلاث خطط من المساحة المشتركة.

| الملف | الدور |
| --- | --- |
| [actual_candidates.py](<D:/AI/Real projects/Academic_Advisor_Simple/tools/recommendation_pilot_20251/actual_candidates.py>) | اتحاد المرشحات، تحقق البنية، التاريخ السابق، مصدر كل حقل |
| [actual_experiment.py](<D:/AI/Real projects/Academic_Advisor_Simple/tools/recommendation_pilot_20251/actual_experiment.py>) | تشغيل معزول، وضعا الساعات، قياس الزمن، بصمات الحماية، حفظ تشغيل جديد |
| [actual_metrics.py](<D:/AI/Real projects/Academic_Advisor_Simple/tools/recommendation_pilot_20251/actual_metrics.py>) | تقاطع التوصيات وأخطاء الخطة الفعلية بمقامين منفصلين |
| [actual_report.py](<D:/AI/Real projects/Academic_Advisor_Simple/tools/recommendation_pilot_20251/actual_report.py>) | توليد هذا التقرير من النتائج المحفوظة فقط |
| [engine.py](<D:/AI/Real projects/Academic_Advisor_Simple/tools/recommendation_pilot_20251/engine.py>) | نقطة إدخال مرشحات وتوقيت مع الاحتفاظ بسلوك الوضع الأصلي |
| [app.py](<D:/AI/Real projects/Academic_Advisor_Simple/tools/recommendation_pilot_20251/app.py>) | مسارات محلية خاصة بالتجربة |
| [app.js](<D:/AI/Real projects/Academic_Advisor_Simple/tools/recommendation_pilot_20251/static/app.js>) | أدوات المقارنة والتفاصيل والتحذير ضمن الواجهة القائمة |
| [index.html](<D:/AI/Real projects/Academic_Advisor_Simple/tools/recommendation_pilot_20251/static/index.html>) | اختيارات التجربة ضمن الموقع نفسه |
| [style.css](<D:/AI/Real projects/Academic_Advisor_Simple/tools/recommendation_pilot_20251/static/style.css>) | تنسيق إضافات الواجهة |

الاختبارات الجديدة تخص `actual_candidates` و`actual_experiment` و`actual_metrics` وواجهة الحقن. لا تدريب أو دمج نماذج أو تغيير أوزان أو فرض الخطة الفعلية ضمن `Top-3`.

| Run ID | الطلاب | الحالات | ميزانية الخطط | حالات البحث القصوى | مسار النتائج |
| --- | --- | --- | --- | --- | --- |
| `run_20261021T114914_4f2dcd430e` | 30 | 120 | 200 | 200000 | [ملفات التشغيل](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T114914_4f2dcd430e>) |
| `run_20261021T115456_6af0d2c1ad` | 1 | 4 | 2000 | 200000 | [ملفات التشغيل](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T115456_6af0d2c1ad>) |

التشغيل ذو عدد طلاب أقل من 30 يمثل النطاق المسجل فقط، ولا يُقدَّم على أنه إعادة تقييم جماعي كامل. تختلف ميزانية 200 عن 2000؛ الجداول تميز كل تشغيل.

## 2. Data Integrity

يعبر إلى بناء المرشحات من التسجيل الفعلي `course_id` و`course_credits` فقط. لا تعبر `final_mark` أو `actual_mark` أو النقاط أو حالة النجاح/الرسوب أو محاولة الفصل المستهدف. تُستخدم النتائج الحقيقية لاحقًا في حساب الأخطاء فقط.

يختار `observed.py` التسجيل بهوية `student_id + degree_id + part_id` ويربط النتيجة عبر `student_course_id` مع المادة والساعات. يطابق الحقن الكتالوج بمفتاح `degree_id + course_id`؛ وتُطبّع المعرفات الرقمية باستخدام `Decimal`. تساوي ساعات الكتالوج ساعات التسجيل شرط لازم، وتُرفض البنية الناقصة أو المتعارضة مع سبب صريح.

تُحسب `attempt_number` من أكبر محاولة في CLEANED history سابقة للطالب والمادة عبر الدرجات، بشرط `part_id < 20251`، ثم تُضاف محاولة واحدة. غياب سجل سابق في مصدر سليم يعطي 1 وفق عقد الاستيراد المحلي الموجود؛ لا يثبت اكتمال تاريخ المحاولات الرسمي أو أهلية التسجيل. مصدر غير صالح لا يُستبدل بمحاولة أولى مختلقة. لا تُحتسب حالة أو محاولة أو نتيجة للفصل المستهدف. بيانات C المرجعية وتاريخ النموذج ثابتان حتى `20243`؛ لا تدخل نتائج `20251` في مرجع الأقران، وتوقيت نفاذ الكتالوج غير مثبت.

الغائب يُحدد مقابل **API الخام**؛ المادة الموجودة فيه والمرفوضة بقواعد الأهلية الحالية تبقى مرفوضة. الاستثناء التشخيصي للمواد الغائبة المحقونة فقط، مع `historical_eligibility_unverified=true` و`official_requestability=UNVERIFIED`. تبقى حدود الساعات والقيود الأصلية نافذة. مصدر كل حقل محفوظ في `candidate_provenance` خارج مدخلات النموذج.

لم تُعد كتابة `courses_response.json` أو `Student API` أو Frozen History أو النماذج. قيم `TOTAL_*` قيم بداية الفصل وفق اتفاق الجامعة، وتُنسخ كما هي؛ لم يتغير معناها ولم تُحسب مجددًا لمطابقة V2. فروق Snapshot مع الميزات التاريخية وتحذيرات عدم التكافؤ باقية.

| Run | Branch | Base HEAD | فرع الأصل | Commits | Pushes |
| --- | --- | --- | --- | --- | --- |
| run_20261021T114914_4f2dcd430e | new_branch | 19c0870c3bfb2ff7695a45c29ce2bddc3d6690ce | expirennets | 0 | 0 |
| run_20261021T115456_6af0d2c1ad | new_branch | 19c0870c3bfb2ff7695a45c29ce2bddc3d6690ce | expirennets | 0 | 0 |

أقرّ المستخدم اسم `new_branch` للتجربة. سجل Git يثبت أن فرع checkout السابق هو `expirennets` عند الالتزام الأساسي نفسه؛ لا يُستنتج من الاسم دوره الإنتاجي. لم يغيّر التشغيل الفرع ولم ينفذ `merge` أو `push` أو Commit. وجود `PASS` أدناه يعني تطابق الملفات المحددة قبل التشغيل وبعده؛ تفاصيل المجموعة والبصمات محفوظة في ملف الحماية، ولا يساوي ذلك اعتمادًا للإنتاج. أكد التشغيلان `code_stable_during_run=true`.

| Run | الحماية | ملفات محمية | متغير | مضاف للمجموعة | الدليل |
| --- | --- | --- | --- | --- | --- |
| run_20261021T114914_4f2dcd430e | PASS | 1312 | 0 | 0 | [protected_files.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T114914_4f2dcd430e/protected_files.json>) |
| run_20261021T115456_6af0d2c1ad | PASS | 1312 | 0 | 0 | [protected_files.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T115456_6af0d2c1ad/protected_files.json>) |

| Run | المصدر/النموذج | المرجع | SHA256 |
| --- | --- | --- | --- |
| run_20261021T114914_4f2dcd430e | catalog_source | D:\AI\Real projects\Academic_Advisor_Simple\data\clean\degree_course_v2.parquet | `7f23a7e0e4678a5ae73f872c0db0dff866698f1567a0fe1520d1dc5327f197c0` |
| run_20261021T114914_4f2dcd430e | history_source | D:\AI\Real projects\Academic_Advisor_Simple\data\clean\student_course_v2.parquet | `55dfbddf62ca641e5186ddd713b13c91134cf0a20c53ef87c943ee911eaf1c00` |
| run_20261021T114914_4f2dcd430e | students.csv | قائمة العينة المحفوظة | `7b195ad673067173fddb31b8ce87dbc25d22b7c5d12a4019e99a08f0ccd0e7e6` |
| run_20261021T114914_4f2dcd430e | A/grade_regressor_v2.txt | نموذج/عقد محفوظ | `3794be06899046e15e854129bdd3a16437f791f3e4b72a7b0a99bf656bdebf8a` |
| run_20261021T114914_4f2dcd430e | A/fail_risk_classifier_v2.txt | نموذج/عقد محفوظ | `28bd34fb756c7670157a1748a0469e2b066b711d5decb9064fd433190a96d1e2` |
| run_20261021T114914_4f2dcd430e | A/category_levels_v2.json | نموذج/عقد محفوظ | `4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6` |
| run_20261021T114914_4f2dcd430e | A/model_metadata_v2.json | نموذج/عقد محفوظ | `8af46218a697eebc9873349a2a8ae9a2d8488278b56909cd5fc6b4a7ef82c83a` |
| run_20261021T114914_4f2dcd430e | A/v_acs_grade.parquet | نموذج/عقد محفوظ | `557e1cb7b03b09d690d639c8d61c50e5e537360d0dec0684e6a283047111aad2` |
| run_20261021T114914_4f2dcd430e | B/category_levels.json | نموذج/عقد محفوظ | `4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6` |
| run_20261021T114914_4f2dcd430e | B/fail_model.txt | نموذج/عقد محفوظ | `d21eda64adb08b298d394fa943aa2b9fe171569ba98926106a6cdd459956bfcc` |
| run_20261021T114914_4f2dcd430e | B/grade_model.txt | نموذج/عقد محفوظ | `301f5512f0ed354dc6eb6a8a95586891523defd94226e67fecc51b73b1af93b6` |
| run_20261021T114914_4f2dcd430e | C/category_levels.json | نموذج/عقد محفوظ | `4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6` |
| run_20261021T114914_4f2dcd430e | C/fail_model.txt | نموذج/عقد محفوظ | `55eccc885a3c82ae2eedf96aebdf7c0b4de915f9a367d0be0f528b5bbc69117f` |
| run_20261021T114914_4f2dcd430e | C/grade_model.txt | نموذج/عقد محفوظ | `11410a35bf95ecb1bbc17eecd20eec9a662c008d2d29b80c6211934e624f807e` |
| run_20261021T115456_6af0d2c1ad | catalog_source | D:\AI\Real projects\Academic_Advisor_Simple\data\clean\degree_course_v2.parquet | `7f23a7e0e4678a5ae73f872c0db0dff866698f1567a0fe1520d1dc5327f197c0` |
| run_20261021T115456_6af0d2c1ad | history_source | D:\AI\Real projects\Academic_Advisor_Simple\data\clean\student_course_v2.parquet | `55dfbddf62ca641e5186ddd713b13c91134cf0a20c53ef87c943ee911eaf1c00` |
| run_20261021T115456_6af0d2c1ad | students.csv | قائمة العينة المحفوظة | `7b195ad673067173fddb31b8ce87dbc25d22b7c5d12a4019e99a08f0ccd0e7e6` |
| run_20261021T115456_6af0d2c1ad | A/grade_regressor_v2.txt | نموذج/عقد محفوظ | `3794be06899046e15e854129bdd3a16437f791f3e4b72a7b0a99bf656bdebf8a` |
| run_20261021T115456_6af0d2c1ad | A/fail_risk_classifier_v2.txt | نموذج/عقد محفوظ | `28bd34fb756c7670157a1748a0469e2b066b711d5decb9064fd433190a96d1e2` |
| run_20261021T115456_6af0d2c1ad | A/category_levels_v2.json | نموذج/عقد محفوظ | `4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6` |
| run_20261021T115456_6af0d2c1ad | A/model_metadata_v2.json | نموذج/عقد محفوظ | `8af46218a697eebc9873349a2a8ae9a2d8488278b56909cd5fc6b4a7ef82c83a` |
| run_20261021T115456_6af0d2c1ad | A/v_acs_grade.parquet | نموذج/عقد محفوظ | `557e1cb7b03b09d690d639c8d61c50e5e537360d0dec0684e6a283047111aad2` |
| run_20261021T115456_6af0d2c1ad | B/category_levels.json | نموذج/عقد محفوظ | `4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6` |
| run_20261021T115456_6af0d2c1ad | B/fail_model.txt | نموذج/عقد محفوظ | `d21eda64adb08b298d394fa943aa2b9fe171569ba98926106a6cdd459956bfcc` |
| run_20261021T115456_6af0d2c1ad | B/grade_model.txt | نموذج/عقد محفوظ | `301f5512f0ed354dc6eb6a8a95586891523defd94226e67fecc51b73b1af93b6` |
| run_20261021T115456_6af0d2c1ad | C/category_levels.json | نموذج/عقد محفوظ | `4fb4f3dff5f1d1bf70972ad9d02384a01f73e4689fb514937f2d70eb966982f6` |
| run_20261021T115456_6af0d2c1ad | C/fail_model.txt | نموذج/عقد محفوظ | `55eccc885a3c82ae2eedf96aebdf7c0b4de915f9a367d0be0f528b5bbc69117f` |
| run_20261021T115456_6af0d2c1ad | C/grade_model.txt | نموذج/عقد محفوظ | `11410a35bf95ecb1bbc17eecd20eec9a662c008d2d29b80c6211934e624f807e` |

بصمات API لكل طالب، نسخ النماذج، GradeScale، مرجع C، Frozen History، roster والنتائج موجودة تفصيليًا في `run_manifest.json` و`protected_files.json` لكل تشغيل؛ لا يُكتفى ببصمات الجدول المختارة.

## 3. Before vs After

`Original` هو المصدر الأصلي بقواعده. `Augmented` اتحاد المصدر الخام مع الفعليات الغائبة القابلة لإعادة البناء البنيوي. تغطية الخام لا تساوي تغطية مجموعة النموذج: قد تبقى مادة مستبعدة بسياسة أصلية، وقد يكون طلب الطالب محجوبًا كليًا بسبب `FUTURE_COURSE_SOURCE`. قيمة `N/A` تعني نتيجة غير متاحة؛ لا تُحسب صفر تقاطع.

### Run `run_20261021T114914_4f2dcd430e` — 200 plans

الفعليات الفريدة: **166**؛ تغطية API الخام **86/166 → 166/166**؛ المضاف **80**. العد مرة واحدة لكل طالب، وليس مرة لكل وضع ساعات أو نموذج. التغطية اللاحقة للطلبات المحجوبة وصف لاتحاد بنيوي أُعد في الذاكرة، وليست مجموعة قابلة للتنبؤ.

| العينة | الفعلي | مرشحات API | الاتحاد الخام | المحقون | فعليات داخل الخام O→A | Model pool | مستبعد بسياسة أصلية |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P01 | 7 | 16 | 23 | 7 | 0 → 7 | 16 → 23 | 0 |
| P20251-01-P02 | 6 | 20 | 26 | 6 | 0 → 6 | 20 → 26 | 0 |
| P20251-01-P03 | 4 | 29 | 29 | 0 | 4 → 4 | 29 → 29 | 0 |
| P20251-01-P04 | 4 | 22 | 26 | 4 | 0 → 4 | 22 → 26 | 0 |
| P20251-01-P05 | 6 | 23 | 29 | 6 | 0 → 6 | 23 → 29 | 0 |
| P20251-02-P01 | 8 | 11 | 12 | 1 | 7 → 8 | 10 → 11 | 1 |
| P20251-02-P02 | 6 | 9 | 10 | 1 | 5 → 6 | 9 → 10 | 0 |
| P20251-02-P03 | 6 | 19 | 19 | 0 | 6 → 6 | 18 → 18 | 1 |
| P20251-02-P04 | 6 | 8 | 8 | 0 | 6 → 6 | 8 → 8 | 0 |
| P20251-02-P05 | 6 | 18 | 18 | 0 | 6 → 6 | 17 → 17 | 1 |
| P20251-03-P01 | 4 | 18 | 18 | 0 | 4 → 4 | 18 → 18 | 0 |
| P20251-03-P02 | 4 | 19 | 20 | 1 | 3 → 4 | 19 → 20 | 0 |
| P20251-03-P03 | 6 | 14 | 14 | 0 | 6 → 6 | 13 → 13 | 1 |
| P20251-03-P04 | 4 | 19 | 23 | 4 | 0 → 4 | BLOCKED_ORIGINAL_API_INPUT | N/A |
| P20251-03-P05 | 4 | 20 | 21 | 1 | 3 → 4 | 20 → 21 | 0 |
| P20251-04-P01 | 5 | 16 | 18 | 2 | 3 → 5 | 16 → 18 | 0 |
| P20251-04-P02 | 5 | 26 | 26 | 0 | 5 → 5 | 26 → 26 | 0 |
| P20251-04-P03 | 5 | 8 | 8 | 0 | 5 → 5 | 8 → 8 | 0 |
| P20251-04-P04 | 4 | 16 | 20 | 4 | 0 → 4 | 16 → 20 | 0 |
| P20251-04-P05 | 5 | 12 | 13 | 1 | 4 → 5 | 11 → 12 | 0 |
| P20251-05-P01 | 6 | 12 | 12 | 0 | 6 → 6 | 12 → 12 | 0 |
| P20251-05-P02 | 7 | 6 | 13 | 7 | 0 → 7 | 6 → 13 | 0 |
| P20251-05-P03 | 6 | 10 | 15 | 5 | 1 → 6 | BLOCKED_ORIGINAL_API_INPUT | N/A |
| P20251-05-P04 | 6 | 20 | 26 | 6 | 0 → 6 | BLOCKED_ORIGINAL_API_INPUT | N/A |
| P20251-05-P05 | 6 | 12 | 17 | 5 | 1 → 6 | BLOCKED_ORIGINAL_API_INPUT | N/A |
| P20251-06-P01 | 7 | 15 | 22 | 7 | 0 → 7 | 15 → 22 | 0 |
| P20251-06-P02 | 6 | 26 | 26 | 0 | 6 → 6 | 26 → 26 | 0 |
| P20251-06-P03 | 6 | 13 | 19 | 6 | 0 → 6 | 13 → 19 | 0 |
| P20251-06-P04 | 5 | 26 | 26 | 0 | 5 → 5 | 25 → 25 | 0 |
| P20251-06-P05 | 6 | 16 | 22 | 6 | 0 → 6 | 16 → 22 | 0 |

#### Experiment A — Fixed 18 Credits

الهدف ثابت 18؛ اختلاف الحمل الفعلي يمنع مقارنة التطابق الكامل.

كل خلية A/B/C هي `Top-1 overlap / Top-3 union overlap`؛ السهم من Original إلى Augmented.

| العينة | الحمل الفعلي | الهدف | A: O→A | B: O→A | C: O→A | سبب حجب/تعذر |
| --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P01 | 18.000 | 18.000 | 0/0 → 4/4 | 0/0 → 4/5 | 0/0 → 4/4 | — |
| P20251-01-P02 | 18.000 | 18.000 | 0/0 → 1/1 | 0/0 → 1/1 | 0/0 → 1/1 | — |
| P20251-01-P03 | 13.000 | 18.000 | 3/3 → 3/3 | 3/4 → 3/4 | 3/3 → 3/3 | — |
| P20251-01-P04 | 12.000 | 18.000 | 0/0 → 1/1 | 0/0 → 1/1 | 0/0 → 2/2 | — |
| P20251-01-P05 | 13.000 | 18.000 | 0/0 → 5/6 | 0/0 → 6/6 | 0/0 → 6/6 | — |
| P20251-02-P01 | 13.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-02-P02 | 16.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-02-P03 | 18.000 | 18.000 | 1/1 → 1/1 | 2/3 → 2/3 | 1/2 → 1/2 | — |
| P20251-02-P04 | 17.000 | 18.000 | 5/6 → 5/6 | 5/6 → 5/6 | 4/6 → 4/6 | — |
| P20251-02-P05 | 16.000 | 18.000 | 1/2 → 1/2 | 2/3 → 2/3 | 3/4 → 3/4 | — |
| P20251-03-P01 | 12.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-03-P02 | 12.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-03-P03 | 18.000 | 18.000 | 2/3 → 2/3 | 3/3 → 3/3 | 3/3 → 3/3 | — |
| P20251-03-P04 | 12.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | FUTURE_COURSE_SOURCE |
| P20251-03-P05 | 13.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-04-P01 | 24.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-04-P02 | 15.000 | 18.000 | 2/2 → 2/2 | 2/3 → 2/3 | 2/2 → 2/2 | — |
| P20251-04-P03 | 16.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-04-P04 | 12.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-04-P05 | 12.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-05-P01 | 18.000 | 18.000 | 3/4 → 3/4 | 2/4 → 2/4 | 3/3 → 3/3 | — |
| P20251-05-P02 | 16.000 | 18.000 | 0/0 → 0/4 | 0/0 → 1/2 | 0/0 → 1/2 | — |
| P20251-05-P03 | 18.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | FUTURE_COURSE_SOURCE |
| P20251-05-P04 | 16.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | FUTURE_COURSE_SOURCE |
| P20251-05-P05 | 17.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | FUTURE_COURSE_SOURCE |
| P20251-06-P01 | 20.000 | 18.000 | 0/0 → 2/2 | 0/0 → 3/3 | 0/0 → 2/3 | — |
| P20251-06-P02 | 17.000 | 18.000 | 2/3 → 2/3 | 2/2 → 2/2 | 2/3 → 2/3 | — |
| P20251-06-P03 | 17.000 | 18.000 | 0/0 → 2/3 | 0/0 → 3/3 | 0/0 → 2/3 | — |
| P20251-06-P04 | 15.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-06-P05 | 16.000 | 18.000 | 0/0 → 2/2 | 0/0 → 2/3 | 0/0 → 2/2 | — |

#### Experiment B — Actual Credit Load Diagnostic

الهدف مأخوذ من التسجيل الفعلي بعد حدوثه، وليس قرار حمل مستقلًا. لا تتجاوز التجربة حدود التسجيل عند تعارضه معها.

كل خلية A/B/C هي `Top-1 overlap / Top-3 union overlap`؛ السهم من Original إلى Augmented.

| العينة | الحمل الفعلي | الهدف | A: O→A | B: O→A | C: O→A | سبب حجب/تعذر |
| --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P01 | 18.000 | 18.000 | 0/0 → 4/4 | 0/0 → 4/5 | 0/0 → 4/4 | — |
| P20251-01-P02 | 18.000 | 18.000 | 0/0 → 1/1 | 0/0 → 1/1 | 0/0 → 1/1 | — |
| P20251-01-P03 | 13.000 | 13.000 | 2/2 → 2/2 | 2/2 → 2/2 | 2/2 → 2/2 | — |
| P20251-01-P04 | 12.000 | 12.000 | 0/0 → 1/1 | 0/0 → 1/1 | 0/0 → 1/2 | — |
| P20251-01-P05 | 13.000 | 13.000 | 0/0 → 5/6 | 0/0 → 5/6 | 0/0 → 5/6 | — |
| P20251-02-P01 | 13.000 | 13.000 | 6/6 → 6/6 | 6/6 → 6/6 | 6/6 → 6/6 | — |
| P20251-02-P02 | 16.000 | 16.000 | 3/4 → 4/6 | 3/4 → 4/5 | 4/5 → 4/5 | — |
| P20251-02-P03 | 18.000 | 18.000 | 1/1 → 1/1 | 2/3 → 2/3 | 1/2 → 1/2 | — |
| P20251-02-P04 | 17.000 | 17.000 | 5/6 → 5/6 | 6/6 → 6/6 | 5/6 → 5/6 | — |
| P20251-02-P05 | 16.000 | 16.000 | 1/2 → 1/2 | 2/2 → 2/2 | 2/3 → 2/3 | — |
| P20251-03-P01 | 12.000 | 12.000 | 2/2 → 2/2 | 4/4 → 4/4 | 3/3 → 3/3 | — |
| P20251-03-P02 | 12.000 | 12.000 | 2/2 → 2/2 | 3/3 → 3/3 | 2/3 → 2/3 | — |
| P20251-03-P03 | 18.000 | 18.000 | 2/3 → 2/3 | 3/3 → 3/3 | 3/3 → 3/3 | — |
| P20251-03-P04 | 12.000 | 12.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | FUTURE_COURSE_SOURCE |
| P20251-03-P05 | 13.000 | 13.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-04-P01 | 24.000 | 24.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | REQUESTED_CREDITS_OUTSIDE_EXPLICIT_LIMITS |
| P20251-04-P02 | 15.000 | 15.000 | 1/1 → 1/1 | 1/2 → 1/2 | 1/1 → 1/1 | — |
| P20251-04-P03 | 16.000 | 16.000 | 4/4 → 4/4 | 4/5 → 4/5 | 3/5 → 3/5 | — |
| P20251-04-P04 | 12.000 | 12.000 | 0/0 → 1/1 | 0/0 → 2/3 | 0/0 → 1/1 | — |
| P20251-04-P05 | 12.000 | 12.000 | 3/3 → 3/3 | 3/4 → 3/3 | 2/3 → 3/4 | — |
| P20251-05-P01 | 18.000 | 18.000 | 3/4 → 3/4 | 2/4 → 2/4 | 3/3 → 3/3 | — |
| P20251-05-P02 | 16.000 | 16.000 | N/A/N/A → 2/4 | N/A/N/A → 2/4 | N/A/N/A → 2/4 | NO_EXACT_CREDIT_SUBSET |
| P20251-05-P03 | 18.000 | 18.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | FUTURE_COURSE_SOURCE |
| P20251-05-P04 | 16.000 | 16.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | FUTURE_COURSE_SOURCE |
| P20251-05-P05 | 17.000 | 17.000 | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | N/A/N/A → N/A/N/A | FUTURE_COURSE_SOURCE |
| P20251-06-P01 | 20.000 | 20.000 | 0/0 → 2/2 | 0/0 → 2/4 | 0/0 → 2/3 | — |
| P20251-06-P02 | 17.000 | 17.000 | 3/3 → 3/3 | 2/3 → 2/3 | 2/2 → 2/2 | — |
| P20251-06-P03 | 17.000 | 17.000 | N/A/N/A → 3/4 | N/A/N/A → 4/4 | N/A/N/A → 3/3 | NO_EXACT_CREDIT_SUBSET |
| P20251-06-P04 | 15.000 | 15.000 | 0/0 → 0/0 | 0/1 → 0/1 | 0/1 → 0/1 | — |
| P20251-06-P05 | 16.000 | 16.000 | 0/0 → 1/3 | 0/0 → 2/2 | 0/0 → 1/3 | — |

#### Paired recommendation summary

متوسطات التقاطع أدناه تخص الطلاب الذين تتوفر لهم نتيجة في الوضعين معًا. يُعرض من أصبحت نتيجتهم متاحة بعد الإضافة على حدة؛ لا يُخلط تغير المقام بتغير التقاطع.

| اختبار الساعات | النموذج | أزواج متاحة | متاح حديثًا | متوسط Top-1 O→A | متوسط Top-3 O→A |
| --- | --- | --- | --- | --- | --- |
| actual_load | A | 22 | 2 | 1.727 → 2.455 | 1.955 → 2.864 |
| actual_load | B | 22 | 2 | 1.955 → 2.773 | 2.364 → 3.364 |
| actual_load | C | 22 | 2 | 1.773 → 2.500 | 2.182 → 3.136 |
| fixed_18 | A | 16 | 0 | 1.188 → 2.250 | 1.500 → 2.938 |
| fixed_18 | B | 16 | 0 | 1.312 → 2.625 | 1.750 → 3.250 |
| fixed_18 | C | 16 | 0 | 1.312 → 2.562 | 1.625 → 3.062 |

### Run `run_20261021T115456_6af0d2c1ad` — 2000 plans

الفعليات الفريدة: **6**؛ تغطية API الخام **0/6 → 6/6**؛ المضاف **6**. العد مرة واحدة لكل طالب، وليس مرة لكل وضع ساعات أو نموذج. التغطية اللاحقة للطلبات المحجوبة وصف لاتحاد بنيوي أُعد في الذاكرة، وليست مجموعة قابلة للتنبؤ.

| العينة | الفعلي | مرشحات API | الاتحاد الخام | المحقون | فعليات داخل الخام O→A | Model pool | مستبعد بسياسة أصلية |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P02 | 6 | 20 | 26 | 6 | 0 → 6 | 20 → 26 | 0 |

#### Experiment A — Fixed 18 Credits

الهدف ثابت 18؛ اختلاف الحمل الفعلي يمنع مقارنة التطابق الكامل.

كل خلية A/B/C هي `Top-1 overlap / Top-3 union overlap`؛ السهم من Original إلى Augmented.

| العينة | الحمل الفعلي | الهدف | A: O→A | B: O→A | C: O→A | سبب حجب/تعذر |
| --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P02 | 18.000 | 18.000 | 0/0 → 1/1 | 0/0 → 1/1 | 0/0 → 1/1 | — |

#### Experiment B — Actual Credit Load Diagnostic

الهدف مأخوذ من التسجيل الفعلي بعد حدوثه، وليس قرار حمل مستقلًا. لا تتجاوز التجربة حدود التسجيل عند تعارضه معها.

كل خلية A/B/C هي `Top-1 overlap / Top-3 union overlap`؛ السهم من Original إلى Augmented.

| العينة | الحمل الفعلي | الهدف | A: O→A | B: O→A | C: O→A | سبب حجب/تعذر |
| --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P02 | 18.000 | 18.000 | 0/0 → 1/1 | 0/0 → 1/1 | 0/0 → 1/1 | — |

#### Paired recommendation summary

متوسطات التقاطع أدناه تخص الطلاب الذين تتوفر لهم نتيجة في الوضعين معًا. يُعرض من أصبحت نتيجتهم متاحة بعد الإضافة على حدة؛ لا يُخلط تغير المقام بتغير التقاطع.

| اختبار الساعات | النموذج | أزواج متاحة | متاح حديثًا | متوسط Top-1 O→A | متوسط Top-3 O→A |
| --- | --- | --- | --- | --- | --- |
| actual_load | A | 1 | 0 | 0.000 → 1.000 | 0.000 → 1.000 |
| actual_load | B | 1 | 0 | 0.000 → 1.000 | 0.000 → 1.000 |
| actual_load | C | 1 | 0 | 0.000 → 1.000 | 0.000 → 1.000 |
| fixed_18 | A | 1 | 0 | 0.000 → 1.000 | 0.000 → 1.000 |
| fixed_18 | B | 1 | 0 | 0.000 → 1.000 | 0.000 → 1.000 |
| fixed_18 | C | 1 | 0 | 0.000 → 1.000 | 0.000 → 1.000 |

## 4. A/B/C Comparison

A يستخدم النموذج الأصلي و47 ميزة وتاريخه الفردي. B يستخدم النموذج المحفوظ ذا 44 ميزة وتاريخ الجامعة المجمع. C يستخدم النموذج المحفوظ ذا 47 ميزة، ومنها ميزات التشابه الثلاث. لا تتحد مخرجاتها في نموذج رابع. تتلقى الأنظمة داخل كل حالة هوية ومرشحات وحملًا وحدود بحث ومساحة خطط واحدة قبل ترتيب مستقل.

تقييم العلامات أدناه **للخطة الفعلية الكاملة بتوقع مستقل** عبر `observed_prediction.py`، حتى لو لم يولدها البحث. ليس خطأً لتوصيات بديلة لا نملك نتائجها المضادة للواقع. تُزال تكرارات أوضاع المرشحات/الساعات عند العد بمفتاح `sample_id + model`. `Bias = predicted − actual`، و`Micro` يزن كل مادة بالتساوي؛ `Macro` متوسط مقياس كل طالب.

مجموعة `low_archived_gpa` تعني GPA في Student Snapshot أقل من 2؛ `low_cohort_gpa` تستخدم قيمة العينة التاريخية أقل من 2. اختلاف المصدرين محفوظ، ولا يعني GPA الصفري أن الطالب جديد. المقاييس مشروطة بهذه اللقطة ولا تُعتمد كدقة تاريخية موثوقة.

### Prediction metrics — `run_20261021T114914_4f2dcd430e`

| المجموعة | النموذج | طلاب متاحون/مختارون | مواد | MAE Micro/Macro | RMSE Micro/Macro | Bias Micro/Macro | توقع مفقود/مرفوض |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all | A | 30/30 | 166 | 11.0870/11.0887 | 13.6418/12.7251 | -2.3217/-1.6648 | 0/0 |
| low_archived_gpa | A | 27/27 | 147 | 11.5058/11.4689 | 14.0388/13.1427 | -2.2699/-1.5848 | 0/0 |
| low_cohort_gpa | A | 20/20 | 105 | 10.7314/10.8230 | 13.1846/12.4942 | -0.1692/0.3984 | 0/0 |
| all | B | 30/30 | 166 | 12.3896/12.2382 | 15.6393/14.0517 | -5.6549/-4.9089 | 0/0 |
| low_archived_gpa | B | 27/27 | 147 | 12.9416/12.7182 | 16.1883/14.5909 | -6.0410/-5.2023 | 0/0 |
| low_cohort_gpa | B | 20/20 | 105 | 11.1797/11.2146 | 14.2260/13.2537 | -2.9110/-2.3163 | 0/0 |
| all | C | 30/30 | 166 | 11.1559/11.3002 | 14.3615/13.2403 | -1.1527/-0.2155 | 0/0 |
| low_archived_gpa | C | 27/27 | 147 | 11.5046/11.6343 | 14.7635/13.6409 | -0.9853/-0.0095 | 0/0 |
| low_cohort_gpa | C | 20/20 | 105 | 10.4263/10.7932 | 13.5571/12.7889 | 2.0930/2.9310 | 0/0 |

| المجموعة | النموذج | تسميات الرسوب | رسوب فعلي | Brier Micro/Macro | Log loss Micro/Macro | ROC AUC Micro/Macro |
| --- | --- | --- | --- | --- | --- | --- |
| all | A | 166 | 14 | 0.0715/0.0804 | 0.2595/0.2827 | 0.8313/0.4469 |
| low_archived_gpa | A | 147 | 14 | 0.0793/0.0882 | 0.2813/0.3045 | 0.8206/0.4469 |
| low_cohort_gpa | A | 105 | 10 | 0.0796/0.0917 | 0.2837/0.3151 | 0.8232/0.3000 |
| all | B | 166 | 14 | 0.0746/0.0821 | 0.2774/0.2968 | 0.8961/0.6073 |
| low_archived_gpa | B | 147 | 14 | 0.0825/0.0899 | 0.3008/0.3196 | 0.8851/0.6073 |
| low_cohort_gpa | B | 105 | 10 | 0.0784/0.0890 | 0.2906/0.3180 | 0.8968/0.5667 |
| all | C | 166 | 14 | 0.0721/0.0821 | 0.2570/0.2835 | 0.7871/0.4021 |
| low_archived_gpa | C | 147 | 14 | 0.0800/0.0901 | 0.2792/0.3060 | 0.7707/0.4021 |
| low_cohort_gpa | C | 105 | 10 | 0.0789/0.0928 | 0.2774/0.3140 | 0.7853/0.3333 |

الأقل في MAE الوصفي الكلي لهذا التشغيل هو **A** (11.0870). هذه مقارنة مشروطة بالمدخلات المحفوظة؛ لا تثبت تفوقًا إنتاجيًا أو تحسنًا سببيًا بسبب الحقن.

### Prediction metrics — `run_20261021T115456_6af0d2c1ad`

| المجموعة | النموذج | طلاب متاحون/مختارون | مواد | MAE Micro/Macro | RMSE Micro/Macro | Bias Micro/Macro | توقع مفقود/مرفوض |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all | A | 1/1 | 6 | 13.8725/13.8725 | 15.6040/15.6040 | -9.3476/-9.3476 | 0/0 |
| low_archived_gpa | A | 1/1 | 6 | 13.8725/13.8725 | 15.6040/15.6040 | -9.3476/-9.3476 | 0/0 |
| low_cohort_gpa | A | 1/1 | 6 | 13.8725/13.8725 | 15.6040/15.6040 | -9.3476/-9.3476 | 0/0 |
| all | B | 1/1 | 6 | 13.0523/13.0523 | 14.9381/14.9381 | -9.1979/-9.1979 | 0/0 |
| low_archived_gpa | B | 1/1 | 6 | 13.0523/13.0523 | 14.9381/14.9381 | -9.1979/-9.1979 | 0/0 |
| low_cohort_gpa | B | 1/1 | 6 | 13.0523/13.0523 | 14.9381/14.9381 | -9.1979/-9.1979 | 0/0 |
| all | C | 1/1 | 6 | 14.2385/14.2385 | 16.6001/16.6001 | -12.4228/-12.4228 | 0/0 |
| low_archived_gpa | C | 1/1 | 6 | 14.2385/14.2385 | 16.6001/16.6001 | -12.4228/-12.4228 | 0/0 |
| low_cohort_gpa | C | 1/1 | 6 | 14.2385/14.2385 | 16.6001/16.6001 | -12.4228/-12.4228 | 0/0 |

| المجموعة | النموذج | تسميات الرسوب | رسوب فعلي | Brier Micro/Macro | Log loss Micro/Macro | ROC AUC Micro/Macro |
| --- | --- | --- | --- | --- | --- | --- |
| all | A | 6 | 0 | 0.0658/0.0658 | 0.2960/0.2960 | N/A/N/A |
| low_archived_gpa | A | 6 | 0 | 0.0658/0.0658 | 0.2960/0.2960 | N/A/N/A |
| low_cohort_gpa | A | 6 | 0 | 0.0658/0.0658 | 0.2960/0.2960 | N/A/N/A |
| all | B | 6 | 0 | 0.0707/0.0707 | 0.3080/0.3080 | N/A/N/A |
| low_archived_gpa | B | 6 | 0 | 0.0707/0.0707 | 0.3080/0.3080 | N/A/N/A |
| low_cohort_gpa | B | 6 | 0 | 0.0707/0.0707 | 0.3080/0.3080 | N/A/N/A |
| all | C | 6 | 0 | 0.0654/0.0654 | 0.2952/0.2952 | N/A/N/A |
| low_archived_gpa | C | 6 | 0 | 0.0654/0.0654 | 0.2952/0.2952 | N/A/N/A |
| low_cohort_gpa | C | 6 | 0 | 0.0654/0.0654 | 0.2952/0.2952 | N/A/N/A |

الأقل في MAE الوصفي الكلي لهذا التشغيل هو **B** (13.0523). هذه مقارنة مشروطة بالمدخلات المحفوظة؛ لا تثبت تفوقًا إنتاجيًا أو تحسنًا سببيًا بسبب الحقن.

## 5. Search Limitations

حُفظ التعداد الأصلي: ترتيب `course_id` نصيًا ثم include-first وأول N خطط مطابقة لـ Decimal exact credits، مع ميزانية حالات معلنة. لم يُصلح انحياز البادئة ولم تُضف الخطة الفعلية قسرًا. `search_truncated=true` يعني أن أعلى ثلاث هي الأفضل داخل الجزء المفحوص، وليس ضمانًا للأفضلية العالمية.

### Search — `run_20261021T114914_4f2dcd430e`

| الحمل | الوضع | النموذج | طلاب بنتيجة | خطط مفحوصة | حالات زيارة | بحث مبتور | حمل فعلي متوافق | الفعلية فُحصت | الفعلية Top-3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| actual_load | augmented | A | 24 | 4204 | 85313 | 20 | 24 | 9 | 1 |
| actual_load | augmented | B | 24 | 4204 | 85313 | 20 | 24 | 9 | 2 |
| actual_load | augmented | C | 24 | 4204 | 85313 | 20 | 24 | 9 | 2 |
| fixed_18 | augmented | A | 16 | 3016 | 59956 | 15 | 5 | 1 | 0 |
| fixed_18 | augmented | B | 16 | 3016 | 59956 | 15 | 5 | 1 | 0 |
| fixed_18 | augmented | C | 16 | 3016 | 59956 | 15 | 5 | 1 | 0 |
| actual_load | original | A | 22 | 3694 | 70999 | 18 | 22 | 5 | 1 |
| actual_load | original | B | 22 | 3694 | 70999 | 18 | 22 | 5 | 2 |
| actual_load | original | C | 22 | 3694 | 70999 | 18 | 22 | 5 | 1 |
| fixed_18 | original | A | 16 | 2817 | 44973 | 14 | 5 | 1 | 0 |
| fixed_18 | original | B | 16 | 2817 | 44973 | 14 | 5 | 1 | 0 |
| fixed_18 | original | C | 16 | 2817 | 44973 | 14 | 5 | 1 | 0 |

#### Experiment A — Fixed 18 Credits — exposure and full-plan rank

ظهور المواد يعني عدد الفعليات التي ظهرت مرة على الأقل داخل الخطط المفحوصة، لا داخل المرشحات فقط. الإحصاء من A لأن مساحة الخطط واحدة؛ ترتيب الخطة الفعلية يعرض `A/B/C` لكل وضع، و`N/A` عند غيابها أو عدم توفر التنبؤ.

| العينة | خطط O→A | حالات O→A | مبتور O→A | مواد فعلية ظهرت O→A | الخطة الفعلية فُحصت O→A | رتبتها A/B/C: O→A |
| --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P01 | 200 → 200 | 2792 → 4936 | true → true | 0/7 → 7/7 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-01-P02 | 200 → 200 | 3621 → 6580 | true → true | 0/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-01-P03 | 200 → 200 | 3803 → 3803 | true → true | 4/4 → 4/4 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-01-P04 | 200 → 200 | 4508 → 5151 | true → true | 0/4 → 4/4 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-01-P05 | 200 → 200 | 5040 → 7382 | true → true | 0/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-02-P01 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-02-P02 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-02-P03 | 200 → 200 | 2795 → 2795 | true → true | 5/6 → 5/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-02-P04 | 16 → 16 | 147 → 147 | false → false | 6/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-02-P05 | 200 → 200 | 2649 → 2649 | true → true | 5/6 → 5/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-03-P01 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-03-P02 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-03-P03 | 200 → 200 | 4543 → 4543 | true → true | 5/6 → 5/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-03-P04 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-03-P05 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-04-P01 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-04-P02 | 200 → 200 | 2916 → 2916 | true → true | 5/5 → 5/5 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-04-P03 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-04-P04 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-04-P05 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-05-P01 | 200 → 200 | 1523 → 1523 | true → true | 6/6 → 6/6 | true → true | 113/190/126 → 113/190/126 |
| P20251-05-P02 | 1 → 200 | 13 → 2370 | false → true | 0/7 → 7/7 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-05-P03 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-05-P04 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-05-P05 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P01 | 200 → 200 | 2220 → 4228 | true → true | 0/7 → 6/7 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P02 | 200 → 200 | 5211 → 5211 | true → true | 6/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P03 | 200 → 200 | 1521 → 2459 | true → true | 0/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P04 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P05 | 200 → 200 | 1671 → 3263 | true → true | 0/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |

#### Experiment B — Actual Credit Load Diagnostic — exposure and full-plan rank

ظهور المواد يعني عدد الفعليات التي ظهرت مرة على الأقل داخل الخطط المفحوصة، لا داخل المرشحات فقط. الإحصاء من A لأن مساحة الخطط واحدة؛ ترتيب الخطة الفعلية يعرض `A/B/C` لكل وضع، و`N/A` عند غيابها أو عدم توفر التنبؤ.

| العينة | خطط O→A | حالات O→A | مبتور O→A | مواد فعلية ظهرت O→A | الخطة الفعلية فُحصت O→A | رتبتها A/B/C: O→A |
| --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P01 | 200 → 200 | 2792 → 4936 | true → true | 0/7 → 7/7 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-01-P02 | 200 → 200 | 3621 → 6580 | true → true | 0/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-01-P03 | 200 → 200 | 5950 → 5950 | true → true | 4/4 → 4/4 | true → true | 167/130/172 → 167/130/172 |
| P20251-01-P04 | 200 → 200 | 5264 → 5728 | true → true | 0/4 → 4/4 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-01-P05 | 200 → 200 | 5363 → 7474 | true → true | 0/6 → 6/6 | false → true | N/A/N/A/N/A → 10/5/2 |
| P20251-02-P01 | 42 → 112 | 483 → 1199 | false → false | 6/8 → 7/8 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-02-P02 | 31 → 71 | 355 → 769 | false → false | 5/6 → 6/6 | false → true | N/A/N/A/N/A → 64/58/22 |
| P20251-02-P03 | 200 → 200 | 2795 → 2795 | true → true | 5/6 → 5/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-02-P04 | 6 → 6 | 167 → 167 | false → false | 6/6 → 6/6 | true → true | 2/1/3 → 2/1/3 |
| P20251-02-P05 | 200 → 200 | 2920 → 2920 | true → true | 5/6 → 5/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-03-P01 | 200 → 200 | 2720 → 2720 | true → true | 4/4 → 4/4 | true → true | 156/1/24 → 156/1/24 |
| P20251-03-P02 | 200 → 200 | 3130 → 3600 | true → true | 3/4 → 4/4 | false → true | N/A/N/A/N/A → 167/17/7 |
| P20251-03-P03 | 200 → 200 | 4543 → 4543 | true → true | 5/6 → 5/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-03-P04 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-03-P05 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-04-P01 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-04-P02 | 200 → 200 | 2759 → 2759 | true → true | 5/5 → 5/5 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-04-P03 | 15 → 15 | 167 → 167 | false → false | 5/5 → 5/5 | true → true | 7/8/7 → 7/8/7 |
| P20251-04-P04 | 200 → 200 | 1998 → 2420 | true → true | 0/4 → 4/4 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-04-P05 | 200 → 200 | 1842 → 1880 | true → true | 4/5 → 5/5 | false → true | N/A/N/A/N/A → 100/80/19 |
| P20251-05-P01 | 200 → 200 | 1523 → 1523 | true → true | 6/6 → 6/6 | true → true | 113/190/126 → 113/190/126 |
| P20251-05-P02 | 0 → 200 | 13 → 2009 | false → true | N/A → 7/7 | N/A → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-05-P03 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-05-P04 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-05-P05 | 0 → 0 | 0 → 0 | false → false | N/A → N/A | N/A → N/A | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P01 | 200 → 200 | 1231 → 2597 | true → true | 0/7 → 6/7 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P02 | 200 → 200 | 2645 → 2645 | true → true | 6/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P03 | 0 → 200 | 6005 → 2991 | false → true | N/A → 6/6 | N/A → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P04 | 200 → 200 | 6343 → 6343 | true → true | 5/5 → 5/5 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |
| P20251-06-P05 | 200 → 200 | 6370 → 10598 | true → true | 0/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |

| العينة | الحمل | الوضع | النموذج | رتبة الفعلية | رتبة Top-3 | GPA الفعلية المتوقع | أفضل GPA مفحوص |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P03 | actual_load | original | A | 167 | N/A | 2.308 | 2.577 |
| P20251-01-P03 | actual_load | original | B | 130 | N/A | 2.250 | 2.481 |
| P20251-01-P03 | actual_load | original | C | 172 | N/A | 2.442 | 2.750 |
| P20251-01-P03 | actual_load | augmented | A | 167 | N/A | 2.308 | 2.577 |
| P20251-01-P03 | actual_load | augmented | B | 130 | N/A | 2.250 | 2.481 |
| P20251-01-P03 | actual_load | augmented | C | 172 | N/A | 2.442 | 2.750 |
| P20251-01-P05 | actual_load | augmented | A | 10 | N/A | 3.096 | 3.173 |
| P20251-01-P05 | actual_load | augmented | B | 5 | N/A | 2.808 | 2.885 |
| P20251-01-P05 | actual_load | augmented | C | 2 | 2 | 3.077 | 3.115 |
| P20251-02-P02 | actual_load | augmented | A | 64 | N/A | 2.328 | 2.500 |
| P20251-02-P02 | actual_load | augmented | B | 58 | N/A | 2.234 | 2.375 |
| P20251-02-P02 | actual_load | augmented | C | 22 | N/A | 2.359 | 2.391 |
| P20251-02-P04 | actual_load | original | A | 2 | 2 | 2.588 | 2.632 |
| P20251-02-P04 | actual_load | original | B | 1 | 1 | 2.074 | 2.074 |
| P20251-02-P04 | actual_load | original | C | 3 | 3 | 2.750 | 2.794 |
| P20251-02-P04 | actual_load | augmented | A | 2 | 2 | 2.588 | 2.632 |
| P20251-02-P04 | actual_load | augmented | B | 1 | 1 | 2.074 | 2.074 |
| P20251-02-P04 | actual_load | augmented | C | 3 | 3 | 2.750 | 2.794 |
| P20251-03-P01 | actual_load | original | A | 156 | N/A | 2.062 | 2.271 |
| P20251-03-P01 | actual_load | original | B | 1 | 1 | 1.938 | 1.938 |
| P20251-03-P01 | actual_load | original | C | 24 | N/A | 2.312 | 2.375 |
| P20251-03-P01 | actual_load | augmented | A | 156 | N/A | 2.062 | 2.271 |
| P20251-03-P01 | actual_load | augmented | B | 1 | 1 | 1.938 | 1.938 |
| P20251-03-P01 | actual_load | augmented | C | 24 | N/A | 2.312 | 2.375 |
| P20251-03-P02 | actual_load | augmented | A | 167 | N/A | 1.875 | 2.188 |
| P20251-03-P02 | actual_load | augmented | B | 17 | N/A | 1.875 | 2.000 |
| P20251-03-P02 | actual_load | augmented | C | 7 | N/A | 2.438 | 2.458 |
| P20251-04-P03 | actual_load | augmented | A | 7 | N/A | 2.297 | 2.391 |
| P20251-04-P03 | actual_load | augmented | B | 8 | N/A | 2.297 | 2.391 |
| P20251-04-P03 | actual_load | augmented | C | 7 | N/A | 2.250 | 2.297 |
| P20251-04-P03 | actual_load | original | A | 7 | N/A | 2.297 | 2.391 |
| P20251-04-P03 | actual_load | original | B | 8 | N/A | 2.297 | 2.391 |
| P20251-04-P03 | actual_load | original | C | 7 | N/A | 2.250 | 2.297 |
| P20251-04-P05 | actual_load | augmented | A | 100 | N/A | 2.208 | 2.375 |
| P20251-04-P05 | actual_load | augmented | B | 80 | N/A | 2.021 | 2.188 |
| P20251-04-P05 | actual_load | augmented | C | 19 | N/A | 2.188 | 2.292 |
| P20251-05-P01 | fixed_18 | original | A | 113 | N/A | 1.958 | 2.167 |
| P20251-05-P01 | fixed_18 | original | B | 190 | N/A | 1.750 | 1.958 |
| P20251-05-P01 | fixed_18 | original | C | 126 | N/A | 2.042 | 2.333 |
| P20251-05-P01 | fixed_18 | augmented | A | 113 | N/A | 1.958 | 2.167 |
| P20251-05-P01 | fixed_18 | augmented | B | 190 | N/A | 1.750 | 1.958 |
| P20251-05-P01 | fixed_18 | augmented | C | 126 | N/A | 2.042 | 2.333 |
| P20251-05-P01 | actual_load | original | A | 113 | N/A | 1.958 | 2.167 |
| P20251-05-P01 | actual_load | original | B | 190 | N/A | 1.750 | 1.958 |
| P20251-05-P01 | actual_load | original | C | 126 | N/A | 2.042 | 2.333 |
| P20251-05-P01 | actual_load | augmented | A | 113 | N/A | 1.958 | 2.167 |
| P20251-05-P01 | actual_load | augmented | B | 190 | N/A | 1.750 | 1.958 |
| P20251-05-P01 | actual_load | augmented | C | 126 | N/A | 2.042 | 2.333 |

### Search — `run_20261021T115456_6af0d2c1ad`

| الحمل | الوضع | النموذج | طلاب بنتيجة | خطط مفحوصة | حالات زيارة | بحث مبتور | حمل فعلي متوافق | الفعلية فُحصت | الفعلية Top-3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| actual_load | augmented | A | 1 | 2000 | 43558 | 1 | 1 | 0 | 0 |
| actual_load | augmented | B | 1 | 2000 | 43558 | 1 | 1 | 0 | 0 |
| actual_load | augmented | C | 1 | 2000 | 43558 | 1 | 1 | 0 | 0 |
| fixed_18 | augmented | A | 1 | 2000 | 43558 | 1 | 1 | 0 | 0 |
| fixed_18 | augmented | B | 1 | 2000 | 43558 | 1 | 1 | 0 | 0 |
| fixed_18 | augmented | C | 1 | 2000 | 43558 | 1 | 1 | 0 | 0 |
| actual_load | original | A | 1 | 2000 | 35448 | 1 | 1 | 0 | 0 |
| actual_load | original | B | 1 | 2000 | 35448 | 1 | 1 | 0 | 0 |
| actual_load | original | C | 1 | 2000 | 35448 | 1 | 1 | 0 | 0 |
| fixed_18 | original | A | 1 | 2000 | 35448 | 1 | 1 | 0 | 0 |
| fixed_18 | original | B | 1 | 2000 | 35448 | 1 | 1 | 0 | 0 |
| fixed_18 | original | C | 1 | 2000 | 35448 | 1 | 1 | 0 | 0 |

#### Experiment A — Fixed 18 Credits — exposure and full-plan rank

ظهور المواد يعني عدد الفعليات التي ظهرت مرة على الأقل داخل الخطط المفحوصة، لا داخل المرشحات فقط. الإحصاء من A لأن مساحة الخطط واحدة؛ ترتيب الخطة الفعلية يعرض `A/B/C` لكل وضع، و`N/A` عند غيابها أو عدم توفر التنبؤ.

| العينة | خطط O→A | حالات O→A | مبتور O→A | مواد فعلية ظهرت O→A | الخطة الفعلية فُحصت O→A | رتبتها A/B/C: O→A |
| --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P02 | 2000 → 2000 | 35448 → 43558 | true → true | 0/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |

#### Experiment B — Actual Credit Load Diagnostic — exposure and full-plan rank

ظهور المواد يعني عدد الفعليات التي ظهرت مرة على الأقل داخل الخطط المفحوصة، لا داخل المرشحات فقط. الإحصاء من A لأن مساحة الخطط واحدة؛ ترتيب الخطة الفعلية يعرض `A/B/C` لكل وضع، و`N/A` عند غيابها أو عدم توفر التنبؤ.

| العينة | خطط O→A | حالات O→A | مبتور O→A | مواد فعلية ظهرت O→A | الخطة الفعلية فُحصت O→A | رتبتها A/B/C: O→A |
| --- | --- | --- | --- | --- | --- | --- |
| P20251-01-P02 | 2000 → 2000 | 35448 → 43558 | true → true | 0/6 → 6/6 | false → false | N/A/N/A/N/A → N/A/N/A/N/A |

لم تظهر الخطة الفعلية كاملة في أي مساحة مفحوصة متاحة بهذا التشغيل؛ يُراجع جدول الحمل والتعرض قبل نسب السبب إلى ترتيب النموذج.

### Separate single-student / subset budget sensitivity

هذه حساسية ميزانية لعينة أصغر، مستقلة عن جدول الطلاب الثلاثين. لا تُضاف تسجيلاتها أو توقعاتها مرة أخرى إلى المقاييس الجماعية، ولا تمثل نتائج 2000 خطة لجميع الطلاب.

| Run | الميزانية | العينة | الحمل | الوضع | النموذج | Top-1 | Top-3 union | مبتور | الفعلية فُحصت |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | fixed_18 | original | A | 0 | 0 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | fixed_18 | original | B | 0 | 0 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | fixed_18 | original | C | 0 | 0 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | fixed_18 | augmented | A | 1 | 1 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | fixed_18 | augmented | B | 1 | 1 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | fixed_18 | augmented | C | 1 | 1 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | actual_load | original | A | 0 | 0 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | actual_load | original | B | 0 | 0 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | actual_load | original | C | 0 | 0 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | actual_load | augmented | A | 1 | 1 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | actual_load | augmented | B | 1 | 1 | true | false |
| run_20261021T115456_6af0d2c1ad | 2000 | P20251-01-P02 | actual_load | augmented | C | 1 | 1 | true | false |

### 200 / 2000 reproducibility

المقارنة التالية بين الحالات المشتركة المسجلة فقط. الحالات بلا خطط لا تُعد دليل تطابق تنبؤات. تطابق البادئة لا يثبت فحص بقية المساحة.

| الميزانية | حالات مشتركة | مسارات نموذج ذات خطط | بادئة المواد متطابقة | بادئة التوقعات متطابقة |
| --- | --- | --- | --- | --- |
| 200 → 2000 | 4 | 12 | 12/12 | 12/12 |

## 6. Real-Time Performance

في مقارنة الطلاب المقترنين ذوي النتائج، زاد متوسط زمن الحساب من 1.822 إلى 1.867 ثانية عند 18 ساعة، أي نحو 2.5%، ومن 1.809 إلى 1.962 ثانية عند الحمل الفعلي، أي نحو 8.5%. هذه ملاحظة وصفية من تشغيل واحد؛ لا تثبت فرقاً إحصائياً أو زمن خدمة إنتاجية. أعداد حالات المقارنة 16 و22 على الترتيب.

`total_request_seconds` يقيس حساب المرشحات والبحث والتنبؤ والترتيب بعد تدفئة الأصول، ويستبعد توقع الخطة الفعلية المستقل وبصمات الحماية وحفظ ملفات الدفعة وتسلسل HTTP ورسم المتصفح. زمن الدفعة في manifest ينتهي قبل كتابة ملفات النتائج؛ لذلك لا يُقدم على أنه زمن انتظار زر التشغيل كاملاً. يحتفظ الموقع بتصدير `dashboard_results.json` يضم Top-3 ومقاييس البحث الكامل، بينما يبقى تفصيل جميع الخطط المفحوصة محفوظاً محلياً. لم تُقس أزمنة النقل والعرض أو بدء الخدمة البارد كاختبار مستقل.

الأزمنة بالثواني، وكل خلية `mean / p95`. النماذج والمصادر دُفئت قبل الحالات، وتسلسل Original/Augmented متعاكس حسب فهرس الطالب، وبنفس عدد threads والميزانية. هذا قياس واحد لكل حالة، وليس اختبار حمل أو benchmark متكررًا.

جدول التشغيل المجمع يشمل الطلبات المحجوبة؛ الصفر في مرحلة متخطاة لا يعني كلفة نموذج صفرية. تجهيز المرشحات والتوليد وإجمالي الطلب مشتركة بين A/B/C، فلا تُجمع عبر النماذج. الميزات تشمل التاريخ والسياق والمصفوفة والتحقق؛ التنبؤ يشمل `Booster.predict` و`GradeScale.convert`؛ الترتيب يشمل التجميع والتسلسل. التوقع المستقل للخطة الفعلية وبصمات الحماية خارج زمن طلب التوصية.

### Latency — `run_20261021T114914_4f2dcd430e`

| الحمل | الوضع | النموذج | N | تجهيز المرشحات | توليد الخطط | استخراج الميزات | التنبؤ | الترتيب | إجمالي الطلب |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| actual_load | augmented | A | 30 | 0.026/0.041 | 0.089/0.168 | 0.053/0.083 | 0.013/0.022 | 0.083/0.167 | 1.578/3.266 |
| actual_load | augmented | B | 30 | 0.026/0.041 | 0.089/0.168 | 0.063/0.155 | 0.021/0.047 | 0.110/0.351 | 1.578/3.266 |
| actual_load | augmented | C | 30 | 0.026/0.041 | 0.089/0.168 | 0.974/1.940 | 0.023/0.035 | 0.098/0.183 | 1.578/3.266 |
| fixed_18 | augmented | A | 30 | 0.031/0.056 | 0.077/0.163 | 0.038/0.083 | 0.010/0.023 | 0.062/0.155 | 1.014/2.148 |
| fixed_18 | augmented | B | 30 | 0.031/0.056 | 0.077/0.163 | 0.036/0.085 | 0.015/0.032 | 0.064/0.138 | 1.014/2.148 |
| fixed_18 | augmented | C | 30 | 0.031/0.056 | 0.077/0.163 | 0.572/1.202 | 0.015/0.034 | 0.070/0.172 | 1.014/2.148 |
| actual_load | original | A | 30 | 0.007/0.014 | 0.084/0.166 | 0.054/0.119 | 0.012/0.023 | 0.071/0.142 | 1.333/2.644 |
| actual_load | original | B | 30 | 0.007/0.014 | 0.084/0.166 | 0.057/0.098 | 0.018/0.035 | 0.080/0.167 | 1.333/2.644 |
| actual_load | original | C | 30 | 0.007/0.014 | 0.084/0.166 | 0.823/1.431 | 0.017/0.032 | 0.085/0.179 | 1.333/2.644 |
| fixed_18 | original | A | 30 | 0.007/0.015 | 0.068/0.190 | 0.041/0.070 | 0.010/0.024 | 0.069/0.171 | 0.980/2.083 |
| fixed_18 | original | B | 30 | 0.007/0.015 | 0.068/0.190 | 0.036/0.093 | 0.015/0.034 | 0.059/0.140 | 0.980/2.083 |
| fixed_18 | original | C | 30 | 0.007/0.015 | 0.068/0.190 | 0.577/1.268 | 0.014/0.035 | 0.064/0.157 | 0.980/2.083 |

للمقارنة الزمنية المقترنة فقط، الجدول التالي يحصر الطلاب الذين توفرت لهم نتيجة النموذج في الوضعين، ويميز الحملين. نسبة أكبر من 1 تعني ارتفاع متوسط زمن الطلب في هذه العينة، دون إسناد سببي مستقل عن حجم الخطط والسياق.

| الحمل | النموذج | طلاب مقترنون | mean request O→A | p95 request O→A | نسبة A/O |
| --- | --- | --- | --- | --- | --- |
| fixed_18 | A | 16 | 1.822 → 1.867 | 2.350 → 2.292 | 1.025 |
| fixed_18 | B | 16 | 1.822 → 1.867 | 2.350 → 2.292 | 1.025 |
| fixed_18 | C | 16 | 1.822 → 1.867 | 2.350 → 2.292 | 1.025 |
| actual_load | A | 22 | 1.809 → 1.962 | 3.149 → 3.899 | 1.085 |
| actual_load | B | 22 | 1.809 → 1.962 | 3.149 → 3.899 | 1.085 |
| actual_load | C | 22 | 1.809 → 1.962 | 3.149 → 3.899 | 1.085 |

زمن التوقع المستقل للفعليات في التشغيل: 14.770 ثانية؛ زمن الدفعة المسجل شامل الإعداد/الحماية: 171.422 ثانية.

### Latency — `run_20261021T115456_6af0d2c1ad`

| الحمل | الوضع | النموذج | N | تجهيز المرشحات | توليد الخطط | استخراج الميزات | التنبؤ | الترتيب | إجمالي الطلب |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| actual_load | augmented | A | 1 | 0.059/0.059 | 1.817/1.817 | 0.102/0.102 | 0.110/0.110 | 3.018/3.018 | 14.935/14.935 |
| actual_load | augmented | B | 1 | 0.059/0.059 | 1.817/1.817 | 0.115/0.115 | 0.201/0.201 | 3.694/3.694 | 14.935/14.935 |
| actual_load | augmented | C | 1 | 0.059/0.059 | 1.817/1.817 | 1.329/1.329 | 0.220/0.220 | 4.205/4.205 | 14.935/14.935 |
| fixed_18 | augmented | A | 1 | 0.064/0.064 | 2.646/2.646 | 0.137/0.137 | 0.117/0.117 | 4.897/4.897 | 21.447/21.447 |
| fixed_18 | augmented | B | 1 | 0.064/0.064 | 2.646/2.646 | 0.163/0.163 | 0.184/0.184 | 5.162/5.162 | 21.447/21.447 |
| fixed_18 | augmented | C | 1 | 0.064/0.064 | 2.646/2.646 | 1.797/1.797 | 0.287/0.287 | 5.912/5.912 | 21.447/21.447 |
| actual_load | original | A | 1 | 0.016/0.016 | 3.394/3.394 | 0.156/0.156 | 0.132/0.132 | 5.540/5.540 | 22.965/22.965 |
| actual_load | original | B | 1 | 0.016/0.016 | 3.394/3.394 | 0.164/0.164 | 0.255/0.255 | 5.306/5.306 | 22.965/22.965 |
| actual_load | original | C | 1 | 0.016/0.016 | 3.394/3.394 | 1.863/1.863 | 0.305/0.305 | 5.729/5.729 | 22.965/22.965 |
| fixed_18 | original | A | 1 | 0.031/0.031 | 3.382/3.382 | 0.128/0.128 | 0.117/0.117 | 5.671/5.671 | 23.190/23.190 |
| fixed_18 | original | B | 1 | 0.031/0.031 | 3.382/3.382 | 0.202/0.202 | 0.294/0.294 | 5.941/5.941 | 23.190/23.190 |
| fixed_18 | original | C | 1 | 0.031/0.031 | 3.382/3.382 | 1.559/1.559 | 0.211/0.211 | 5.540/5.540 | 23.190/23.190 |

للمقارنة الزمنية المقترنة فقط، الجدول التالي يحصر الطلاب الذين توفرت لهم نتيجة النموذج في الوضعين، ويميز الحملين. نسبة أكبر من 1 تعني ارتفاع متوسط زمن الطلب في هذه العينة، دون إسناد سببي مستقل عن حجم الخطط والسياق.

| الحمل | النموذج | طلاب مقترنون | mean request O→A | p95 request O→A | نسبة A/O |
| --- | --- | --- | --- | --- | --- |
| fixed_18 | A | 1 | 23.190 → 21.447 | 23.190 → 21.447 | 0.925 |
| fixed_18 | B | 1 | 23.190 → 21.447 | 23.190 → 21.447 | 0.925 |
| fixed_18 | C | 1 | 23.190 → 21.447 | 23.190 → 21.447 | 0.925 |
| actual_load | A | 1 | 22.965 → 14.935 | 22.965 → 14.935 | 0.650 |
| actual_load | B | 1 | 22.965 → 14.935 | 22.965 → 14.935 | 0.650 |
| actual_load | C | 1 | 22.965 → 14.935 | 22.965 → 14.935 | 0.650 |

زمن التوقع المستقل للفعليات في التشغيل: 2.555 ثانية؛ زمن الدفعة المسجل شامل الإعداد/الحماية: 96.237 ثانية.

## 7. Historical Validity

يمكن استنتاج أثر إزالة نقص المواد من المرشحات على إمكانية وصول البحث إليها وعلى ترتيبها داخل الجزء المفحوص. ويمكن مقارنة أخطاء توقع الخطة الفعلية بصورة وصفية مشروطة بلقطة Student API الحالية.

لا تثبت التجربة أن المواد المحقونة كانت `IS_REQUESTABLE` تاريخيًا، أو أن الخطة كانت معتمدة أكاديميًا، أو أن أفضل ثلاث بدائل سترفع الأداء الحقيقي. لا تتوفر نتائج مضادة للواقع للمواد التي لم يسجلها الطالب. كتالوج البنية غير مثبت زمنيًا، ولقطات API الحالية لا تعادل تلقائيًا لقطة ما قبل قرار 20251. `official_registration_validated=false` باقٍ.

لم يُغيّر الحقن Student Snapshot لحل فروق V2. التفسير المتفق عليه لـ`TOTAL_*` كبداية الفصل باقٍ، لكن تكافؤ كامل اللقطة مع ميزات التدريب غير مثبت. لذلك لا تُستخدم زيادة Overlap وحدها لترقية نموذج أو تغيير قواعد الإنتاج.

### Validation evidence

دليل التحقق المحفوظ: [validation_20261021.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/validation_20261021.json>). لا يشغّل مولد التقرير أي اختبار.

| الفحص | الأمر المسجل | Exit | النتيجة المسجلة | السجل |
| --- | --- | --- | --- | --- |
| Pre-change related engine, observed prediction and model tests | .\.venv\Scripts\python.exe -m pytest tests/test_pilot_20251_engine.py tests/test_pilot_20251_observed_prediction.py tests/test_pilot_20251_modeling.py -q | 0 | 42 passed in 18.86s before changes | N/A |
| Final Pilot-related tests | $pilotTestPaths = @(Get-ChildItem tests\test_pilot_20251_*.py \| ForEach-Object { $_.FullName }); .\.venv\Scripts\python.exe -m pytest @pilotTestPaths -q | 0 | 197 passed, 1 existing Starlette deprecation warning in 24.87s | N/A |
| Full repository suite | .\.venv\Scripts\python.exe -m pytest -q | 1 | 1 failed, 1805 passed, 1 skipped, 1 warning, 6 subtests passed in 400.03s. Failure: tools/academic_advisor_streamlit/tests/test_ui_client.py::test_student_and_courses_get_use_proper_endpoints_auth_and_params | N/A |
| Confirm unrelated failure on unmodified HEAD-only copies | Extract ui_client.py and tests/test_ui_client.py from git show HEAD:tools/academic_advisor_streamlit/... into a temporary directory; run the single failing test there with project Python | 1 | Same test failed on HEAD-only copies: fake Courses response lacks data.registserRule required by ui_client.py:321. Repository Streamlit files unchanged. No fix outside scope. | N/A |
| Saved-result UI browser QA | GET-only local browser check on existing Pilot app at http://127.0.0.1:8876/ | 0 | Original/Augmented and fixed18/actual-load switches, injected names and IDs, diagnostic warning, one A/B/C card set, observed prediction metrics and zero console errors verified. No UI POST. | N/A |
| Graphify AST update | graphify update . | 0 | Code graph updated without LLM/API: 6791 nodes, 15527 edges, 365 communities. | N/A |

- All inference uses saved models; no training, university API calls, production src changes, commits, pushes, merges, or branch switches.
- The full suite was run during development; final focused Pilot tests cover the subsequent isolation, provenance and compact dashboard changes.
- Windows FastAPI TestClient needed local-loopback execution outside the restricted sandbox; automatic review permitted it.
- Cohort-30 budget is 200. Budget 2000 is a separate single-student sensitivity run, not a second 30-student cohort.
- Development/smoke runs are retained intact and excluded from the final report. Final runs freeze code during execution and use protection hashes before and after.
- TOTAL_* retain the university-declared beginning-of-semester meaning and original values. The inherited Pilot timing warning is preserved; V2 snapshot equivalence remains unverified.

### Saved warnings

التحقق النهائي الإضافي: اختبارات الواجهة الحالية **27 passed**، واختبارات RequestStore **48 passed, 1 skipped**. التخطي المقصود هو `tests/test_api_request_store.py::test_posix_database_and_private_root_permissions` لأن صلاحيات Windows تعتمد على ACLs لحساب خدمة النشر؛ ليس تخطياً بسبب غياب نموذج. بقي فشل Streamlit المذكور أعلاه مطابقاً لنسخة HEAD دون تعديل.

فحص سلامة أخير بعد تشغيل الواجهة وجد **1312/1312 NOT CHANGED**، وتطابقت بصمات كود Pilot الحالي مع بصمات التشغيلين دون اختلاف. الدليل: [final_integrity_20261021.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/final_integrity_20261021.json>). آخر تحديث Graphify هو AST فقط: 6824 عقدة و15561 علاقة، دون LLM/API.

أثبت فحص المتصفح الأخير على نتيجة الثلاثين تبديل الطلاب والوضعين والحملين، وظهور حالة «لم يبدأ» للبحث المحجوب، دون أخطاء Console أو إعادة تنبؤ عند GET. الاستجابة المصغرة المحفوظة كانت HTTP 200 بحجم 11,274,562 بايت. الواجهة متاحة محلياً على [Pilot 20251](http://127.0.0.1:8876/).

- `DIAGNOSTIC_ACTUAL_COURSE_INJECTION`
- `HISTORICAL_CANDIDATE_ELIGIBILITY_NOT_VERIFIABLE`
- `INCREASED_ACTUAL_OVERLAP_IS_NOT_PROVEN_RECOMMENDATION_IMPROVEMENT`
- `OBSERVED_PLAN_PREDICTION_IS_SEPARATE_FROM_RECOMMENDATION_QUALITY`
- `STUDENT_SNAPSHOT_TEMPORAL_EQUIVALENCE_UNVERIFIED_TOTAL_VALUES_UNCHANGED`

## 8. Next Steps

الخطوات المقترحة التالية غير منفذة:

1. تثبيت عقد Backend موحد `as_of/effective_time` قبل التسجيل يربط الطالب والدرجة ونسخة المنهج والأهلية والعروض والقواعد؛ حفظ المواد المسموحة والمرفوضة مع الأسباب.
2. توثيق مصدر وتوقيت `TOTAL_*` وعدادات الفصول والمحاولات وربط انتقالات الدرجات، مع الاحتفاظ بالقيم الأصلية وعدم استبدالها تلقائيًا ببديل محلي.
3. إعادة التقييم على نفس النماذج بعد وصول مرشحات أصلية ثابتة زمنياً؛ فصل توقع الخطة المسجلة عن جودة التوصيات والاعتماد الأكاديمي.
4. دراسة انحياز include-first واستقرار Top-3 تحت ميزانيات وترتيبات بحث معلنة في تجربة منفصلة؛ لا يُستنتج أن زيادة الميزانية وحدها تحل نقص المرشحات أو الأهلية.

## 9. Branch Exit Instructions

الفرع التجريبي المعتمد `new_branch`، وHEAD الأساسي في جدول Git أعلاه. سجل Git يثبت الانتقال من `expirennets` إلى `new_branch` عند الالتزام `19c0870c3bfb2ff7695a45c29ce2bddc3d6690ce`؛ هذا يثبت فرع الرجوع السابق، ولا يغير دور أي فرع آخر اسمه Production. لم يُنفذ هذا العمل Commit أو push أو merge أو تبديل فرع.

قائمة النقل المسموح بها إلى فرع الأصل لاحقًا هي التقرير وهذا التصدير المنقح فقط. يجب التحقق من وجود ملفات `portable_results` قبل نسخها؛ مولد التقرير لا يُنشئها تلقائيًا.

| مسار النقل المحدد | المحتوى |
| --- | --- |
| [التقرير النهائي](<D:/AI/Real projects/Academic_Advisor_Simple/reports/pilot_20251_actual_candidate_injection_results.md>) | نص النتائج والقيود دون كود تجريبي |
| [metrics_summary.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T114914_4f2dcd430e/portable_results/metrics_summary.json>) | مقاييس مجمعة فقط — موجود |
| [latency_summary.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T114914_4f2dcd430e/portable_results/latency_summary.json>) | أزمنة مجمعة فقط — موجود |
| [student_summary.csv](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T114914_4f2dcd430e/portable_results/student_summary.csv>) | معرفات عينات مستعارة وأرقام/حالات فقط؛ بلا مواد أو provenance — موجود |
| [provenance.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T114914_4f2dcd430e/portable_results/provenance.json>) | Branch/HEAD/configuration وSHA256 فقط؛ بلا payload أو سجل هويات — موجود |
| [metrics_summary.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T115456_6af0d2c1ad/portable_results/metrics_summary.json>) | مقاييس مجمعة فقط — موجود |
| [latency_summary.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T115456_6af0d2c1ad/portable_results/latency_summary.json>) | أزمنة مجمعة فقط — موجود |
| [student_summary.csv](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T115456_6af0d2c1ad/portable_results/student_summary.csv>) | معرفات عينات مستعارة وأرقام/حالات فقط؛ بلا مواد أو provenance — موجود |
| [provenance.json](<D:/AI/Real projects/Academic_Advisor_Simple/data/evaluation/recommendation_pilot_20251/experiments/actual_candidate_injection/run_20261021T115456_6af0d2c1ad/portable_results/provenance.json>) | Branch/HEAD/configuration وSHA256 فقط؛ بلا payload أو سجل هويات — موجود |

لا تنقل `student_results.json` أو `dashboard_results.json` أو `original_results.json` أو `augmented_results.json` أو `injected_courses.json` أو `protected_files.json` أو `student_metrics.csv` أو exports المواد/الخطط الكاملة؛ هذه ملفات تجربة محلية وقد تحتوي payload أو مرشحات/تفاصيل حقن أو هويات. ولا تنقل `actual_*.py` أو الاختبارات أو تعديلات engine/app/static أو Graphify. تبقى الملفات الكاملة محفوظة في فرع التجربة للتحقق المحلي.

قبل الرجوع، انسخ قائمة النتائج المنقحة والتقرير إلى مكان آمن خارج checkout. افحص `git status`، ثم يمكنك يدوياً حفظ تعديلات هذه التجربة بـ`git stash push --include-untracked -m pilot-20251-actual-candidates`، وبعد التحقق من المرجع السابق استخدم `git switch expirennets`. أعد نسخ التقرير والملخصات المحددة فقط من النسخة الخارجية؛ لا تطبق stash على فرع الرجوع. لاستكمال التجربة لاحقاً، ارجع إلى `new_branch` أولاً ثم استعد stash المناسب. ملفات data المتجاهلة من Git لا يحفظها stash وتبقى محلياً؛ احتفظ بنسخة مستقلة منها إن احتجت الأرشيف الكامل. تبديل الفرع وحده لا يعزل التعديلات غير المحفوظة. لم تُنفذ هذه الأوامر هنا.
