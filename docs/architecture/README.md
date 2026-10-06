# Academic Advisor — Architecture Map

لقطة فحص **2026-10-06** للـworking tree الحالي عند `eb0d8f74043a6fb8e5ecac5e3197452b975a261b`، بما فيه التغييرات المحلية الموجودة قبل هذه المهمة. الكود وmetadata والملفات المحلية هي مرجع الحالة؛ التقارير السابقة سياق تاريخي.

## Architecture Map

1. [System Context](01_system_context.md): الأطراف الخارجية وحدود النظام.
2. [End-to-End Pipeline](02_end_to_end_pipeline.md): المسار الفعلي وحدود V1/V2 والفجوات.
3. [Data + Features](03_data_features_pipeline.md): المدخلات والتحويلات والمخرجات والمستهلكون.
4. [Model Training](04_model_training.md): التحقق الزمني واختيار المودلات والأصول.
5. [Recommendation Runtime](05_recommendation_runtime.md): طلب طالب واحد في المحرك الحالي.
6. [API Sequence](06_api_sequence.md): التنفيذ المحلي مقابل Planned Integration.

في الرسومات: السهم المتصل يثبت استدعاءً أو قراءة/كتابةً أو اعتماد بيانات موجودًا. السهم المتقطع موسوم بالتخطيط أو بالفجوة ولا يثبت اتصالًا منفذًا. جداول الأدلة تربط العلاقات بملفات المصدر والتوابع الرئيسية. ليست الرسومات ترتيبًا إجباريًا لتشغيل جميع المراحل.

## Current Architecture Status

| التصنيف | الحالة المثبتة الآن | الدليل |
| --- | --- | --- |
| Official baseline | محرك توصية محلي بـ47 ميزة، Grade/Fail V2 وGradeScale وتاريخ مقررات مجمد؛ يمكن استدعاؤه من Python أو CLI. هذه جاهزية baseline محلي، وليست إثبات تشغيل خدمة Production منشورة. | [engine.py](../../../src/recommendation/engine.py)، [artifacts.py](../../../src/recommendation/artifacts.py)، [LOCAL_RECOMMENDATION.md](../../../LOCAL_RECOMMENDATION.md) |
| V2 offline | Cleaning → split → features → modeling → observed-plan evaluation ومسار degree/points تستخدم `_v2` فعليًا. | [main.py](../../../src/main.py)، [paths.py](../../../src/paths.py)، [train_models.py](../../../src/modeling/train_models.py) |
| V1 / Legacy | جداول ومودلات وفئات وتاريخ دون `_v2` محفوظة، ويقرأها `project_status.py` جزئيًا وتشخيص تغيّر الخطط. ليست fallback للتوصية الرسمية. | [project_status.py](../../../src/project_status.py)، [analyze_course_plan_changes.py](../../../src/diagnostics/analyze_course_plan_changes.py) |
| Experimental | degree/direct-points وspecialty history، course-only 33 الأصلي، previous-status 34/48، attempt-number A/B/C؛ لا تدخل scoring الرسمي. | [experiments/](../../../src/experiments/)، [recommendation_experiments/](../../../src/recommendation_experiments/)، [MODEL_ARTIFACT_POLICY.md](../../MODEL_ARTIFACT_POLICY.md) |
| Two-Stage assets | نسخ Grade33/Fail33 منشورة تحت `models/shortlist_v2/` مع manifest يثبتها ويثبت مودلي47. هذا نشر أصول، لا تفعيل محرك `33 → ≤50 → 47`. | [two_stage_artifacts.py](../../../src/recommendation/two_stage_artifacts.py)، [manifest.json](../../../models/shortlist_v2/manifest.json) |
| Two-Stage building blocks | payload adapters وتصنيف الحالة وقيود الخطط موجودة. History Delta و`FrozenHistoryManager` موجودان محليًا، و`history_update.py` واختباره غير متتبعين في Git وقت الفحص. | [inputs.py](../../../src/recommendation/inputs.py)، [constraints.py](../../../src/recommendation/constraints.py)، [history_update.py](../../../src/recommendation/history_update.py) |
| غير موصول | لا `TwoStagePlanRecommender` أو `two_stage_engine.py` أو `shortlist.py` أو `balance_policy.py`؛ لا FastAPI/PHP implementation داخل هذا repository. | حصر ملفات وAST لـ`src/`، [two_stage_artifacts.py](../../../src/recommendation/two_stage_artifacts.py)، [PRODUCTION_CONTRACT.md](../../PRODUCTION_CONTRACT.md) |
| الاستراتيجيات | `stage1_shortlist_strategy` و`final_ranking_strategy` و`combination` كلها `UNAPPROVED` في manifest. ترتيب baseline الحالي موجود؛ لا يعني اعتماد استراتيجية Two-Stage. | [manifest.json](../../../models/shortlist_v2/manifest.json)، [plan_scoring.py](../../../src/recommendation/plan_scoring.py) |

### أكبر Technical Debt

1. **إعادة إنتاج التدريب لا تتطابق تمامًا مع عقد التحميل.** المصدر يسمي المرشح `capaciy_63`، بينما metadata الحالية والمحمّل الصارم يشترطان `capacity_63`. إذا اختير المرشح نفسه عند إعادة التدريب، تُحفظ تسمية يرفضها serving. التدريب يكتب مباشرة في المسارات الرسمية؛ ليست هناك عملية release ذرية لحزمة المودلات الأربع. [تفصيل التدريب](04_model_training.md).
2. **حالة المشروع مشتتة بين الكود والوثائق.** `PIPELINE_README.md` و`Readme.md` ومراحل `project_status.py` ما زالت تحمل حدود V1 أقدم، رغم ترحيل المراحل الفعلية إلى V2. `plan_explanation/` تصف History Delta بأنه غير منفذ، بينما يوجد في working tree الحالي. هذه لقطة محلية، لا إعلان اكتمال مرحلة. [تفصيل الحدود](02_end_to_end_pipeline.md).
3. **Provenance غير مكتمل بين جميع الجداول.** فحص headers وجد `student_course_v2` بـ456,595 صفًا و`student_course_enriched_v2` بـ456,453؛ اختلاف العدد قد ينتج عن الـinner join أو عن أوقات بناء مختلفة ولا يثبت وحده خطأً. لا يجوز اعتبار وجود الملفات أو عداد `project_status.complete` شهادة توافق كامل. بالمقابل، بصمات مصادر حزم Frozen History V2 الحالية طابقت ملفات features الحالية. [تفصيل البيانات](03_data_features_pipeline.md).
4. **كلفة البحث وحالة التكامل.** baseline يحصي كل التركيبات المطابقة، ويحسب ميزات وتوقعات المادة لكل خطة. batching يقلل ذاكرة صفوف المقررات مؤقتًا؛ جميع summaries تبقى في الذاكرة. `top_n` لا يقلل البحث. الاختصار Two-Stage والـAPI لم يربطا بعد. [Runtime](05_recommendation_runtime.md).
5. **العقد الجامعي لا يُستنتج من ML.** سياسة استبدال درجات الإعادات في GPA غير منفذة، وتوفر المواد والمتطلبات السابقة وتوقيت إغلاق النتائج ليست مثبتة باتصال حي. Backend payload helpers وحدها لا تنفذ أهلية الجامعة. [API](06_api_sequence.md).

## Important Boundaries

| الحد | المسؤولية الحالية / المتوقعة |
| --- | --- |
| Training vs Inference | `modeling/train_models.py` يقرأ targets ويختار ويعيد fit ويحفظ؛ `recommendation/engine.py` يقرأ أصولًا موجودة ويحسب predictions فقط. التدريب لا يحدث داخل الطلب. |
| Historical vs target semester | `CourseHistoryState.apply` يرفض target عند/قبل cutoff؛ البناء يعمل apply-before-update. snapshot يصف بداية الفصل المطلوب؛ نتائج ذلك الفصل مسموحة كتقييم بعد scoring فقط. |
| Offline build vs request time | raw cleaning وtemporal split وfeature tables وFrozen History build خارج الطلب. تطبيق سبع ميزات history وحساب14 ميزة plan/peer وGPA والترتيب داخل الطلب. |
| Student state vs course history | Frozen History إحصاءات مقررات؛ snapshot الطالب وGPA والمحاولات والقيود ليست محتواه. |
| Backend vs ML service | الاتجاه المخطط: PHP يوفر هوية الطالب والمرشحين والسياسات وsnapshot موثوقًا. Python يتحقق من القيم ويطبق history ويكوّن ويقيّم الخطط. HTTP والتوثيق والصلاحيات والأهلية الحية لم تنفذ هنا. |
| Official vs Experimental | الرسمي يقرأ V2 المحدد ولا يستورد التجارب. نشر نسخ33 لا يحوّل التجربة الأصلية إلى runtime رسمي مكتمل. |
| Model version vs dataset vs history | `feature_engineering_version=2` يظهر في V1 وV2؛ ليس بديلًا عن مسار dataset. cutoff التدريب الحالي20243 مستقل عن cutoff history المستخدم20243 أو20251. |

## نطاق الفحص وحدود التحقق

- حصر recursive للأقسام المطلوبة، وتحليل AST لجميع79 ملف Python تحت `src/` و55 ملف اختبار و8 سكربتات و6 أدوات debugging؛ فحص imports ومواضع I/O واستدعاءات المسارات الرئيسية.
- فحص65 ملفًا تحت `models/` و812 تحت `data/`، وقراءة schemas/row counts من Parquet headers وmetadata والعقود، دون تضمين سجلات طلاب في هذا التوثيق. راجع [جرد مصادر البيانات](03_data_features_pipeline.md).
- مراجعة documentation الحالية وتقارير المعمارية/العزل/الخصائص/التجارب، وnotebooks وXML/JSON adapters وCLI/configuration. graphify استُخدم للتوجيه الأولي، ثم طوبقت العلاقات على المصدر الحالي؛ لم يُبنَ graph جديد.
- شُغّل `python -B -m src.main --list` و`--all --dry-run` فقط للتحقق من orchestration. لم يُشغّل pipeline أو training أو recommendation أو evaluation أو benchmark، ولم يُشغّل pytest. أسماء الاختبارات أدلة على العقود المستهدفة، وليست ادعاء نجاحها الآن.
- مخرجات هذه المهمة سبعة ملفات Markdown جديدة فقط. الخطة وBaseline الموجودان مسبقًا داخل هذا المجلد محفوظان دون تعديل. لم تُصلح أي مشكلة مكتشفة.

## Flows غير مثبتة

لا يثبت الكود الحالي: استخراج Parquet آليًا من قاعدة الجامعة، طلب PHP حي إلى FastAPI، تسليم Response عبر واجهة طالب، تطبيق prerequisites/offer capacity، تدفق `33 → ≤50 → 47` متكامل، تحديث History Manager داخل baseline، release/rollback للمودلات، أو تحسن فعلي للخطط البديلة غير المسجلة. التفاصيل في [End-to-End](02_end_to_end_pipeline.md) و[API Sequence](06_api_sequence.md).
