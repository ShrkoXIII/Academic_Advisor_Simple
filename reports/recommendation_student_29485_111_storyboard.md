# Storyboard — Recommendation V2 — Student 29485.111

مرجع لفيديو motion explainer بالعربية، مبني على التشغيل المؤكد للملف (7)، الفصل 20251، مجال الساعات 12–18 والهدف الدقيق 18. يصف عناصر تتحرك وتتفاعل مع البيانات والحسابات، لا تسلسل صور ثابتة. لم يُنتج فيديو أو يُرفع ملف الطالب إلى Higgsfield في هذه المهمة.

المدة المقترحة 6:12، وtiming مبدئي يراجع بعد تسجيل الصوت؛ ليست مدة مقاسة لتسجيل موجود. نسبة العرض 16:9، ومرجع التصميم 1920×1080. التقرير الفني: [Recommendation Trace](<D:/AI/Real projects/Academic_Advisor_Simple/reports/recommendation_student_29485_111_trace.md>).

الترتيب الذي يجب أن يظهر بصريًا:

```text
Request → Normalize → Student Snapshot + Frozen History
→ Candidate Preparation + Course History Features
→ Plan Generation → Plan Context → Model Matrix
→ Grade + Fail Prediction → GradeScale Points
→ Plan Scoring → Ranking → Top 3 + Provenance
```

**قاعدة الاستمرارية:** توقع المادة مرتبط بالخطة التي توجد داخلها. نستخدم المادة 1032.111 داخل plan_id=797 كمثال، ولا نعطيها توقعًا ثابتًا لجميع التركيبات. مشهد 20252 مثال مفاهيمي لا تشغيلًا ثانيًا.

## Visual language

- **الشكل:** خلفية #0B1220، وحدات واضحة بعمق خفيف، بطاقات مقررات، رقائق بيانات، وأسهم أو أنابيب تربط التحولات. تستخدم الحركة لإظهار مصدر القيمة وما يغيرها.
- **اللغة:** العربية داخل لوحات RTL؛ الأرقام والمعرّفات والمعادلات في رقائق LTR. خط عربي واضح مثل Noto Sans Arabic أو Tajawal عند توفره، وخط mono للرموز. لا تعكس المعادلة أو المعرّف عند تغيير اتجاه الواجهة.
- **الألوان:** الطلب cyan #38BDF 8؛ المراجع violet #A78BFA؛ التاريخ المجمد teal #2DD4BF؛ العلامة amber #FBBF 24؛ النقاط green #4ADE 80؛ خطر الرسوب coral #FB7185؛ سياق الخطة blue #60A5FA؛ النتائج المحجوبة red #F87171. كل لون تصاحبه تسمية أو أيقونة.
- **الأيقونات:** كبسولة للطلب، قمع للتطبيع، مجلد وقفل للتاريخ، تقويم للفصل، طبقات للـ snapshot، كتاب للكتالوج، شبكة للمصفوفة، ترس للمودل، درجات سلم للتحويل، مقياس احتمال للرسوب، باقة للخطة، قائمة مرتبة للـ ranking، وبصمة للمنشأ.
- **الحركات المتكررة:** رقائق تسير 0.5–0.9 ثانية، كشف طبقات، عداد أعداد، بوابة cutoff، حلقة peers تستثني المادة، وحدات ساعات تتراكم، وإضاءة عمود الترتيب. استخدم ease-in-out مع وقفات قراءة. سرعة العداد لا تمثل runtime الحقيقي.
- **الانتقالات:** match cut بين رقيقة وعمود، zoom على عتبة 85، pan من timeline إلى resolver، و split screen للمعدل الفصلي والتراكمي. اجعل الطالب والفصل وشارة exact 18 ثابتة عبر المشاهد.
- **الصوت:** تعليق عربي هادئ ومباشر؛ مؤثر قصير عند join أو رفض عبور cutoff. لا موسيقى تغطي شرح المعادلة. النص التالي draft، ولا يُدّعى أنه صوت مولّد بالفعل.

## What must be emphasized / not oversimplified

1. JSON قائمة مرشحين؛ الفصل ومجال الساعات أكدهما المستخدم خارج الملف.
2. 20251 يرى حتى 20243. و 20252 يرى حتى 20251 بعد نهائية النتائج، ولا يرى نتائج 20252.
3. المجال 12–18 يعني 18 بالضبط. لا رجوع تلقائي إلى 17 أو 15 أو 12.
4. توليد الخطة وسياقها يسبقان prediction النهائي. المصفوفة مشتركة بين Grade و Fail.
5. العلامة المتوقعة تتحول وفق GradeScale 3.111؛ expected_points ليس تكامل توقع على توزيع احتمالي.
6. لا تخلط history fail rate، وهو feature، مع fail_probability، وهو model output.
7. لا تخلط expected_plan_gpa مع projected_cumulative_gpa. Q/L يختلف عن (G×C+Q)/(C+L).
8. أفضل ثلاث خطط لا تعد بتحسين المعدل. هنا status=ok والتحسن المتوقع صفر.
9. البصمات تثبت هوية الملفات، ولا تثبت calibration أو تاريخ اعتماد الجامعة.
10. لا تقارن نتائج تسجيل مختلف بنتائج بدائل لم يسجلها الطالب. لا تخفِ اختلاف status 185 مقابل catalog 170، أو غياب تاريخ الأهلية.

## Scene 1 — الطلب يدخل النظام

- **Timing:** 00:00–00:16.
- **Objective:** تثبيت هوية الحالة والمسار الرسمي.
- **Visual metaphor:** كبسولة شفافة تمثل الطلب، تدخل آلة مكونة من وحدات مترابطة.
- **On-screen elements:** Student 29485.111، target 20251، ملف JSON (7)، official V2؛ عداد 15→2503→3 في الخلفية.
- **Motion / animation:** 0–4s تدخل الكبسولة؛ 4–9s ينكشف الطالب والفصل؛ 9–13s تتصل بطاقة الملف؛ 13–16s تقترب الكاميرا من وحدة Inputs. تبقى هوية الطالب مقروءة.
- **Voiceover draft:** «سنرى كيف تتحول قائمة خمسة عشر مقررًا إلى أفضل ثلاث خطط لهذا الطالب، باستخدام Recommendation V2 الرسمي.»
- **Technical truth being shown:** أرقام تشغيل حقيقي واحد للطالب والفصل المطلوبين. لا مودل تجريبي أو نتائج trace قديم.
- **Transition:** تتفتح الكبسولة إلى رقائق بيانات مع بقاء الطالب والفصل على الشريط العلوي.

## Scene 2 — من أين تأتي المدخلات؟

- **Timing:** 00:16–00:35.
- **Objective:** فصل بيانات التصدير عن معاملات الطلب ومراجع النظام.
- **Visual metaphor:** مركز فرز بثلاث طبقات: قائمة مواد، طلب مؤكد، ومراجع.
- **On-screen elements:** حقول JSON الخمسة؛ confirmed user request: target 20251، range 12–18؛ status reference: degree 42.111.
- **Motion / animation:** تنفصل رقائق course ID و credits و requestability إلى مسار المرشحين. الفصل والساعات تأتي من بطاقة تأكيد المستخدم. يظهر خط مختلف يربط الاختصاص بمرجع status. لا تظهر حقول غائبة داخل JSON.
- **Voiceover draft:** «الملف يرسل المقررات والساعات والهوية. الفصل ومجال الساعات حُددا صراحةً؛ معلومات الطالب والمراجع تستكمل من النظام.»
- **Technical truth being shown:** JSON ليس request envelope كاملًا. degree_id=42.111 ليس STUDENT_DEGREE_ID=30782.111 الموجود في XML.
- **Transition:** تتقدم رقيقة الساعات وحدها إلى Credit Resolver، وتنتظر بقية الرقائق على المسار.

## Scene 3 — المجال يتحول إلى هدف دقيق

- **Timing:** 00:35–00:52.
- **Objective:** ترسيخ upper_bound_exact.
- **Visual metaphor:** بوابة لا تفتح إلا لباقة عرضها 18 وحدة ساعات.
- **On-screen elements:** requested=[12,18]؛ target=18 exactly؛ باقات 12 و 15 و 17 و 18.
- **Motion / animation:** ينفصل الرقم 18 من قوس المجال ويثبت فوق البوابة. باقات 12 و 15 و 17 تنزلق إلى credit mismatch. باقة 18 تعبر. لا slider يعود إلى قيمة أقل.
- **Voiceover draft:** «المجال من اثنتي عشرة إلى ثماني عشرة ساعة يعني هنا ثماني عشرة بالضبط. لا يقبل النظام خطة أقل حتى لو كانت داخل المجال.»
- **Technical truth being shown:** هذه أمثلة ساعات subsets فعلية؛ لم يُجر model scoring للباقات غير المطابقة في هذا الطلب.
- **Transition:** تبقى شارة exact 18 في الشاشة بينما تتقدم الكبسولة إلى timeline.

## Scene 4 — Frozen History Resolver

- **Timing:** 00:52–01:15.
- **Objective:** إظهار اختيار cutoff وفق الفصل المطلوب.
- **Visual metaphor:** سكة زمنية يقف فوقها محلل الطلب وبجانبه مجلدات التاريخ.
- **On-screen elements:** 20242→20243→20251→20252؛ history_v2؛ as_of_20243 و as_of_20251؛ target 20251.
- **Motion / animation:** يضيء 20251، ويرجع سهم resolver إلى 20243. يرتفع as_of_20243 ويخرج state يحمل cutoff 20243. تبقى حزمة 20251 خافتة كخيار لفصل لاحق. zoom يعزل البيانات حتى 20243.
- **Voiceover draft:** «لتوصية الفصل 20251، نختار التاريخ حتى 20243. إنه الفصل السابق في التقويم: صيف السنة السابقة.»
- **Technical truth being shown:** اختيار bundle موجود والتحقق منه؛ لا إنشاء تلقائي أو اختيار أحدث حزمة مهما كان هدف الطلب. لا يظهر 20250 كفصل صالح.
- **Transition:** يتحول الحد الزمني إلى حاجز بقفل يحرس مسار التاريخ.

## Scene 5 — المستقبل لا يدخل التوقع

- **Timing:** 01:15–01:38.
- **Objective:** شرح منع التسرب والعدالة الزمنية.
- **Visual metaphor:** حاجز زجاجي يفصل المعرفة السابقة عن نتائج الهدف.
- **On-screen elements:** يسار الحاجز: finalized ≤20243؛ يمينه: نتائج 20251 و 20252. إطار مثال مفاهيمي: 20252←20251.
- **Motion / animation:** تحاول رقائق نتائج 20251 عبور حاجز طلب 20251 ثم ترجع بإشارة حجب واضحة. split screen صغير يبدل الهدف إلى 20252 كمثال؛ يتحرك الحاجز إلى 20251 بعد finalization، وتظل نتائج 20252 خارجه.
- **Voiceover draft:** «نستخدم ما كان متاحًا قبل الفصل فقط. ولطلب 20252، تدخل نتائج 20251 بعد نهائيتها، بينما تبقى نتائج 20252 خارج التوقع.»
- **Technical truth being shown:** لم يُشغّل طلب 20252 هنا. finalization مسجلة كشهادة في metadata، وليست timestamp مستقلًا لاعتماد الجامعة.
- **Transition:** يعود المثال إلى الطلب الأساسي، ويتحول الحاجز إلى إطار حزمة مجمدة.

## Scene 6 — محتوى الحزمة المجمدة

- **Timing:** 01:38–01:58.
- **Objective:** فصل aggregate state عن قائمة مرشحين أو تاريخ طالب خاص.
- **Visual metaphor:** خزان إحصاءات بخمس طبقات مفاتيح ومرجع global في المركز.
- **On-screen elements:** 356,816 صف مصدر؛ 5 جداول aggregate؛ 2,428 مفتاح degree×course؛ support عالمي 258,532.25؛ مساهمة الطالب 26 صفًا.
- **Motion / animation:** تندمج جزيئات المصدر في أحواض sums. يتحول عداد الصفوف إلى عرض مفاتيح الحالة مع تسمية الفرق. تدخل رقيقة 26 ضمن المصدر العام؛ لا تظهر سجلات طلاب آخرين. تظهر بصمة المصدر و cutoff على الحزمة.
- **Voiceover draft:** «الحزمة لا تضيف مواد مرشحة. إنها إحصاءات مجموعات من نتائج سابقة، مع مصدر وبصمة وحد زمني محفوظ.»
- **Technical truth being shown:** الحزمة الرسمية course history فقط. لا student_id كمفتاح، ولا specialty history، ولا قائمة طلب داخلها.
- **Transition:** يثبت التاريخ خلف Feature Assembly ويظهر مسار Student Snapshot بجانبه.

## Scene 7 — لقطة بداية الفصل

- **Timing:** 01:58–02:17.
- **Objective:** إبراز القيم المتاحة عند البداية.
- **Visual metaphor:** بطاقة طالب يضيء وجه البداية منها ويبقى وجه النتائج خلفها.
- **On-screen elements:** G=3.12؛ C=68؛ gpa_prev_1=2.67؛ gpa_prev_2=3.47؛ trend=−0.8؛ diploma_gpa=97.13.
- **Motion / animation:** تخرج حقول start من clean status. تتجه رقيقة END_AGPA من XML إلى صينية diagnostics. يظهر 68 كرصد ساعات سابق، و 18 كحمل الخطة الجديدة. يتشكل trend من الطرح.
- **Voiceover draft:** «نأخذ التراكمي ورصيد الساعات عند بداية الفصل، ونضيف تاريخ المعدل والدبلوم. نتائج نهاية الفصل لا تدخل هذه اللقطة.»
- **Technical truth being shown:** صف بداية الهدف وتاريخ سابق منقول بعمليات shift، مع مرجع الدبلوم. لا نسخ لقطة فصل قديم وتسميتها فصلًا جديدًا.
- **Transition:** تنسخ الرقائق المسموح بها من اللقطة على بطاقات المرشحين.

## Scene 8 — تجهيز المقررات المرشحة

- **Timing:** 02:17–02:35.
- **Objective:** إظهار normalization وربط الكتالوج.
- **Visual metaphor:** رصيف كتالوج يستقبل كل بطاقة بمفتاح degree×course.
- **On-screen elements:** 15 بطاقة؛ matched 15/15؛ credit conflicts 0؛ attempt_number=1؛ ملاحظة status 185 /catalog 170.
- **Motion / animation:** تدخل البطاقات رصيف المطابقة وتخرج مع year/semester/type. يصعد عداد matched إلى 15. تبرز المادة 1032.111 ذات الساعة الواحدة. يظهر اختلاف 185/170 في حاشية مقروءة.
- **Voiceover draft:** «نطابق كل مقرر مع كتالوج الاختصاص، ونثبت ساعاته ونوعه ورقم محاولته. تطابقت المقررات الخمسة عشر كلها.»
- **Technical truth being shown:** المصدر يقرر الأهلية؛ لا تعرض وحدة تعيد التحقق من الشُعب أو المقاعد أو prerequisites. اختلاف 185/170 لم يصححه المحرك تلقائيًا.
- **Transition:** تكبر بطاقة 1032 لتشرح إضافة التاريخ للمقرر.

## Scene 9 — الدعم التاريخي و smoothing

- **Timing:** 02:35–02:59.
- **Objective:** شرح دعم قليل مع قيمة تاريخية موجودة.
- **Visual metaphor:** ميزان يدمج مجموعًا محليًا مع مرجع عام.
- **On-screen elements:** course1032؛ key42.111||1032.111؛ support18؛ k20؛ global mark71.302408؛ local mark_sum من course_history_math.json؛ smoothed mark77.053899؛ missing=1.
- **Motion / animation:** تدخل الجزيئات المحلية عداد weighted sum، وتنضم وحدات prior. تتكون المعادلة (local_sum+20×global_mean)/(support+20) طبقة بعد طبقة. يضيء support 18<20 مع بقاء البطاقة.
- **Voiceover draft:** «لهذا المقرر تاريخ، لكن الدعم المحلي قليل. نمزج مجموعه مع المرجع العام، ونحفظ علمًا يوضح قلة الدعم.»
- **Technical truth being shown:** missing=1 لا يعني NaN أو إسقاط المقرر. effective_support ليس raw_count؛ كلاهما يعرض باسمه.
- **Transition:** تعود البطاقة بسبع خصائص تاريخية إلى مجموعة 15، ثم ترتفع الكاميرا إلى شبكة التركيبات.

## Scene 10 — من قائمة إلى خطط

- **Timing:** 02:59–03:23.
- **Objective:** إظهار التوليد قبل prediction النهائي.
- **Visual metaphor:** شبكة اختيار واستبعاد تخرج منها باقات مقررات.
- **On-screen elements:** 15 مرشحًا؛ 2^15 subsets؛ exact 18؛ 2,503 خطة؛ course_count بين 6 و 11.
- **Motion / animation:** تُشرح شعبتا include/exclude لمقررين، ثم zoom out لشبكة مختصرة. تنطفئ فروع تجاوز 18 أو استحالة بلوغه. يصل العداد 2503. تظهر باقات 6 و 9 و 11 مادة، وكل منها 18 ساعة.
- **Voiceover draft:** «نبحث عن التركيبات المطابقة للساعات دون فرض عدد ثابت من المواد. وجدنا ألفين وخمسمائة وثلاث خطط من ثماني عشرة ساعة.»
- **Technical truth being shown:** generation يسبق التوقع لأن plan context جزء من features. لا رسم course→prediction ثابت→combine.
- **Transition:** تُعزل الخطة 797 للتفسير مع 9 بطاقات؛ لا تمنح rank 1 بصريًا قبل التقييم.

## Scene 11 — سياق الخطة والمواد الأخرى

- **Timing:** 03:23–03:45.
- **Objective:** شرح leave-one-out peers.
- **Visual metaphor:** حلقة للخطة وحلقة ثانية تستثني المادة المركزية.
- **On-screen elements:** plan 797:9courses/18credits؛ course 1032:8peers/17credits؛ history plan fail rate 0.064357983؛ 14context features.
- **Motion / animation:** تتقدم 1032 إلى المركز. ترتبط بقية المواد بحلقة peers ويتحول عداد الساعات 18→17 عند استثنائها. تظهر بطاقات full-plan و peer features. تغيير باقة توضيحي يحرك context دون اختراع prediction جديد.
- **Voiceover draft:** «الطالب والمقرر وحدهما لا يكفيان. نضيف حمل الخطة وخصائص المواد الأخرى، ثم يصبح صف المادة جاهزًا للتوقع في هذا السياق.»
- **Technical truth being shown:** context يحسب من الساعات والتاريخ المجمد، لا من نتائج peers الحالية أو علامات متوقعة يعاد حقنها في features.
- **Transition:** تدخل الرقائق أعمدة مصفوفة مرتبة.

## Scene 12 — 47 خاصية ومصفوفة مشتركة

- **Timing:** 03:45–04:03.
- **Objective:** عرض العقد والمدخل المشترك للمودلين.
- **Visual metaphor:** نسيج صفوف وأعمدة يخرج منه مساران.
- **On-screen elements:** 42 numeric float 32 +5 categorical؛ 47 ordered columns؛ batches 17201×47 و 4034×47؛ إجمالي 21,235 صفًا؛ same X.
- **Motion / animation:** تملأ مجموعات student/course/history/context/policy الصف. تمر التصنيفات عبر category levels. تبقى IDs خارج 47 كملصقات joins. ينقسم تدفق X إلى Grade و Fail بشارة هوية واحدة.
- **Voiceover draft:** «كل مادة داخل كل خطة تمر في سبع وأربعين خاصية بالترتيب الرسمي. مودلا العلامة والرسوب يستخدمان المصفوفة نفسها.»
- **Technical truth being shown:** 21,235 course-in-plan rows، لا 15 فقط. لا outcomes ولا student/course/degree IDs ضمن X.
- **Transition:** يتقدم مسار Grade إلى مقياس العلامة، ويبقى مسار Fail ظاهرًا بالتوازي.

## Scene 13 — من علامة إلى درجة ونقاط

- **Timing:** 04:03–04:28.
- **Objective:** إبراز GradeScale والعتبة 85.
- **Visual metaphor:** مقياس علامة متصل بسلم نقاط متدرج.
- **On-screen elements:** 1032:84.966999908→B→3.0؛ 311.111:85.012567822→B+→3.25؛ grade_version 3.111؛ threshold 85.
- **Motion / animation:** تمر العلامات بوحدة clip[0,100] دون تغيير هنا. zoom شديد على 85:84.967 تبقى تحت العتبة و 85.013 تتجاوزها. لا تقريب إلى 85 قبل التحويل. تثبت grade/points على البطاقات.
- **Voiceover draft:** «المودل يتوقع علامة من مئة. سلم النسخة 3.111 يحولها إلى نقاط: أقل من خمسة وثمانين هنا B، وعند عبور العتبة تصبح B+.»
- **Technical truth being shown:** التحويل point estimate وليس توزيع احتمالات، ولا mark/25. الرقم المقرب للعرض لا يقرر grade.
- **Transition:** يلتحق مسار Fail ببطاقات المادة كمعلومة أخرى.

## Scene 14 — خطر الرسوب منفصل

- **Timing:** 04:28–04:44.
- **Objective:** فصل probability عن تحويل النقاط.
- **Visual metaphor:** مقياس احتمال صغير يلحق كل بطاقة.
- **On-screen elements:** Fail balanced_31؛ 1032 risk 0.00813193≈0.813193%؛ expected_points 3.0؛ probability clip[0,1].
- **Motion / animation:** تصل رقيقة risk من مودل Fail. تتجه إلى risk aggregation فقط؛ لا سهم منها يضرب points في(1−risk)، ولا بوابة تحذف المقرر.
- **Voiceover draft:** «مودل الرسوب يعيد احتمالًا من مسار آخر. نجمع منه ساعات الرسوب المتوقعة ونستخدمها لكسر التعادل بين الخطط.»
- **Technical truth being shown:** منفصل كمخرج وكود؛ لا ادعاء باستقلال احتمالي بين المواد أو calibration جديد. history fail rate ليس هذا prediction.
- **Transition:** تتجمع البطاقات في صينية حساب الخطة 797.

## Scene 15 — حساب معدل الخطة والتراكمي

- **Timing:** 04:44–05:06.
- **Objective:** ترجمة Q/L و G/C بصريًا.
- **Visual metaphor:** وعاء نقاط جديدة ورصيد سابق يندمجان في مقام جديد.
- **On-screen elements:** Q54.75؛ L18؛ G3.12؛ C68؛ Q/L3.041666667؛ (G×C+Q)/(C+L)=266.91/86=3.103604651؛ risk 0.173434142.
- **Motion / animation:** تدخل مساهمات credits×points إلى Q. تضاف 18 ساعة إلى 68 ليصير 86. split screen يميز معدل الفصل والتراكمي. يتجمع risk من credits×fail_probability في وعاء منفصل.
- **Voiceover draft:** «معدل الخطة هو النقاط الموزونة على ساعاتها. التراكمي المتوقع يضيفها إلى رصيد الطالب السابق، فينتج نحو 3.103605.»
- **Technical truth being shown:** projection additive دون repeat replacement؛ كل candidate attempt 1 هنا. expected_failed_credits ليس plan_difficulty_credit_load.
- **Transition:** تصغر المعادلة إلى summary row ثم تدخل جميع الخطط إلى leaderboard.

## Scene 16 — لماذا رتبت الخمس بهذا الشكل؟

- **Timing:** 05:06–05:30.
- **Objective:** توضيح كسر تعادل فعلي.
- **Visual metaphor:** جدول ترتيب تضيء مفاتيحه واحدًا بعد الآخر.
- **On-screen elements:** 797، 2173، 1080، 2223، 914؛ projected 3.103604651 للجميع؛ risks 0.173434142، 0.174463725، 0.174751484، 0.175146164، 0.175204696؛ 4sortkeys.
- **Motion / animation:** يضوء projected DESC ويكشف التعادل. يضيء risk ASC فتتحرك الصفوف إلى الترتيب الفعلي. يظهر 9/9/10 مواد للأفضل 3. يبقى semester GPA و plan_id كمفتاحين لاحقين، لا كمبرر لترتيب هذه الخمس.
- **Voiceover draft:** «الخمس الأولى متعادلة في التراكمي المتوقع. لذلك يقرر خطر الرسوب ترتيبها: الأقل أولًا، فتتقدم 797 على 2173 ثم 1080.»
- **Technical truth being shown:** full precision في sorting. عدد المواد لا يقرر ranking مباشرة، والفرق الصغير في probability ليس ضمانًا عمليًا.
- **Transition:** تنفصل الصفوف الثلاثة الأولى وتتحول إلى حزمة النتيجة.

## Scene 17 — Top 3 دون وعد بالتحسن

- **Timing:** 05:30–05:51.
- **Objective:** شرح status ok مع improvement 0.
- **Visual metaphor:** صندوق نتيجة تحيطه خطوط مقارنة واضحة.
- **On-screen elements:** returned 3؛ statusok؛ reasonnull؛ plans_with_expected_improvement 0؛ current 3.12؛ best 3.103605؛ delta−0.016395.
- **Motion / animation:** يظهر خط current 3.12 أعلى bestbar. تبرز delta بلون amber؛ تُغلق الحزمة وبداخلها 3 خطط. لا تأثير empty ولارفع مصطنع للنتيجة. إطار صغير منفصل يوضح no_matching_credit_plan عند 0combinations.
- **Voiceover draft:** «هذه أفضل الخطط المتاحة وفق الطلب، لكن لا توجد خطة يتوقع النظام أن ترفع المعدل الحالي. يعيد الثلاث ويصرح بعدم وجود تحسن متوقع.»
- **Technical truth being shown:** statusok يعني وجود نتائج مطابقة؛ لا يعني تحسنًا مضمونًا. empty سببها عدم matchingcredits في الفرع الآخر.
- **Transition:** تلتصق رقائق provenance بالحزمة.

## Scene 18 — الأدلة وحدود التفسير

- **Timing:** 05:51–06:12.
- **Objective:** إنهاء شرح قابل للتدقيق.
- **Visual metaphor:** حزمة لها ختم هوية مصادر وعدسات للحدود.
- **On-screen elements:** officialV 2؛ historycutoff 20243؛ 116protectedfilesunchanged؛ 71tests؛ eligibilitydateunknown؛ status 185/catalog 170؛ actualoverlap 0.
- **Motion / animation:** تثبت بصمات المودلز والتاريخ على حزمة النتيجة. تظهر ثلاثة callouts مقروءة للحدود، ثم zoomout إلى المسار الكامل. آخر 2s وقفه على Top 3 وال cutoff معرابط التقرير ومجلد debug.
- **Voiceover draft:** «التوصية تقدير مشروط بالقائمة والمراجع. حفظنا الحسابات والمصادر دون تغيير المودلز، ولا نعتبر نتائج تسجيل مختلف دليلًا على دقة البدائل.»
- **Technical truth being shown:** هذا controlledrun وليس backtestvalidated. لا بيانات طلاب آخرين ولا إشارة أنرفعًا خارجيًا أوفيديو export حدث بالفعل.
- **Transition:** توقف هادئ؛ لا اقتراح training أونشر بيانات الطالب.
## Production preparation for Higgsfield / native compositor

هذه مرحلة prep فقط. لم تُنشأ generation jobs ولم تُرفع ملفات الطالب أو تُنشر. يمكن لاحقًا استخدام Higgsfield لأصول مساعدة أو composition، لكن الأرقام العربية والمعرّفات والمعادلات والـ leaderboard تصمم كطبقات نصية أو متجهية حتمية في المونتاج. لا نفترض أن توليد فيديو عام يضمن كتابة 47 عمودًا أو عتبة 85 بصورة صحيحة.

### Editable layer inventory

| مجموعة الطبقات | عناصر قابلة للتحرير | مصدر القيم |
| --- | --- | --- |
| Request | كبسولة،chips هوية وفصل وساعات | request_summary.json |
| Inputs | حقول JSON،15 بطاقة،مراجع | source_inventory.json /candidate_courses.parquet |
| Timeline | target،cutoff،futureblocked،finalization | history_metadata.json |
| History | sums،support،prior،fallback | course_history_math.json /history_evidence.json |
| Snapshot | G،C،trend،diploma | student_snapshot.json |
| Context | plan797،peers،حمل وصعوبة | model_ready_sample_rows.parquet |
| Matrix | مجموعات 47 عمودًا،عداد 42+5 | model_feature_contract.json |
| Prediction | mark→grade→points،risk | scored_courses.parquet؛المفتاح(plan_id,course_id) |
| Scoring | Q/L،معادلة التراكمي،مؤشرالخطر | ranked_plans.parquet |
| Ranking | top5،مفاتيح الفرز،Top3 | ranked_plans.parquet /result.json |
| Evidence | بصمات،حدود،نتائج فحوص | provenance.json /verification.json |

اختيار course ID وحده من أول ظهور في scored_courses غير كافٍ، لأنه قد يخص خطة أخرى. صف 1032.111 داخل plan 797 هو mark 84.96699990831131، gradeB، points 3.0، risk 0.008131930704151. مثال 85.012567822 هو المادة 311.111 داخل plan 797، وليس plan_id311.

### Reusable animated motifs

- مسار رقائق البيانات يصل بين الوحدات ويحافظ على لون المصدر.
- حاجز cutoff واحد يتكرر في timeline وفي bundle، فتبقى العلاقة الزمنية واضحة.
- طبقة full-plan وحلقة peers تستثني البطاقة الحالية دون حذفها من الخطة.
- كتل credits تظهر أن 9 أو 10 مواد قد تعطي 18 ساعة نفسها.
- سلم threshold 85 واحد يوضح فرق B و B+، ولا يتحرك المقياس لتجميل النتيجة.
- إضاءة معيار الترتيب تنتقل من projected إلى risk حين يظهر التعادل.

### Delivery and continuity checks

- master 16:9؛ اقتراح 30fps عند التنفيذ لاحقًا. لا export جاهز ضمن هذا التسليم.
- styleboard لل palette والخطوط والبطاقات والأسهم، مع أصل vector لكل motif.
- هوية الطالب و target 20251 و exact 18 ثابتة خلال المشاهد؛ إطار 20252 موسوم«مثال مفاهيمي».
- voiceoverdraft يحتاج تسجيلًا ومراجعة نطق قبل timinglock. لا caption-burningjob حاليًا.
- تحقق بصريًا من RTL العربية و LTR المعادلات والمعرفات قبل finalrender.
- أكد near 85 ومن عضوية bestplans 9/9/10 مواد، ومن أن risk ليس feature التاريخ.
- آخر لوحة:statusok، returned 3، improvement 0، current 3.12، best 3.103605. لا يوحي successvisual ب guaranteedGPAincrease.
- حدود الأهلية والمنهج والتسجيل تبقى مقروءة؛ لا vo يعد بصلاحية تاريخية غير مثبتة.

## Evidence lock for the edit

| حقيقة لا تغيرها بالمونتاج | القيمة |
| --- | --- |
| student /degree /target |29485.111 /42.111 /20251 |
| source /candidate_count |json/exportdata(7).json /15 |
| credit request /exact target |12–18 /18 |
| history /source rows |history_v2/as_of_20243 /356816 |
| feature contract |47=42numeric+5categorical |
| matching plans /course rows |2503 /21235 |
| best plan |797؛9 مقررات؛18 ساعة |
| Top3 IDs |797،2173،1080 |
| Q /G /C /L |54.75 /3.12 /68 /18 |
| expected semester /projected cumulative GPA |3.041666667 /3.103604651 |
| best expected_failed_credits |0.173434142333 |
| status /returned /improved plans |ok /3 /0 |
| scope |طالب واحد؛طلب واحد؛لا تدريب أو  batch أو overwrite رسمي |

مرجع القيم المحلية: [debug directory](<D:/AI/Real projects/Academic_Advisor_Simple/data/debug/recommendation_trace_29485_111>). النتيجة النهائية لهذا التسليم هيStoryboardجاهز للإنتاج،وتقرير تفصيلي،وأدلةdebug؛لا فيديو مولد.
