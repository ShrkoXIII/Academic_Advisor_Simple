# خريطة الملفات الكاملة

الجرد يشمل خمسة وتسعين ملف مصدر، وستة وسبعين ملفًا تحت مجلد الاختبارات، وإحدى وثلاثين أداة أو ملفًا مساعدًا خارج شجرة المصدر؛ المجموع مئتان واثنان في هذه الشجرات. لا توجد ملفات بايثون مباشرة في جذر المشروع بحسب الفحص.

كل ملف مصدر له صفحة شرح، بما فيها تعريفات الحزم والأسماء القديمة. التصنيف مبني على الاستيرادات والنداءات ومداخل التنفيذ، ولا يعني أن كل ملف نشط يُستدعى في كل طلب.

- ثلاثة وستون نشطًا في الخدمة أو البناء أو التقييم أو الأدوات المشتركة.
- ستة وعشرون تجريبيًا أو وصفيًا خارج خدمة التوصية.
- ستة أسماء توافق قديمة أو تحليل مصادر سابقة، مع بيان الاستخدام المدعوم بدل تسميتها غير مستعملة.

[خطة التعلم](00_START_HERE.md)

[مداخل التنفيذ والأدوات](06_ENTRY_POINTS_AND_TOOLS.md)

[فهرس الاختبارات](05_TEST_INDEX.md)

## واجهات الخدمة

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/api/__init__.py</code>
</td>
<td>
يحدد حزمة بايثون ويضع وصفًا قصيرًا إن وجد؛ ليس خطوة تنفيذ أكاديمية.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="api/__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/api/app.py</code>
</td>
<td>
هذا هو حد النقل الشبكي: ينشئ التطبيق ومساراته ويضبط المصادقة والأخطاء، ثم يسلّم العمل إلى الخدمة. لا يقرر السياسة الأكاديمية ولا يجري توقعًا بنفسه.
</td>
<td>
<pre>DecimalRequest
DecimalRoute
create_app</pre>
</td>
<td>
واجهة وتشغيل
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="api/schemas.md">شرح التبعية</a>
<br>
<code>src/api/schemas.py</code>
<br>
<a href="api/service.md">شرح التبعية</a>
<br>
<code>src/api/service.py</code>
<br>
<a href="api/settings.md">شرح التبعية</a>
<br>
<code>src/api/settings.py</code>
<br>
<a href="api/validation.md">شرح التبعية</a>
<br>
<code>src/api/validation.py</code>
</td>
<td>
<a href="api/app.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/api/backend_client.py</code>
</td>
<td>
يوفر اتصالًا صغيرًا معزولًا للاختبار المحلي عندما لا تستخدم الخلفية الوسيطة الدفع. لا يغير عقد التوصية ولا يشغّل المحرك.
</td>
<td>
<pre>_PinnedHTTPSConnection
BackendClient</pre>
</td>
<td>
واجهة وتشغيل
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="api/validation.md">شرح التبعية</a>
<br>
<code>src/api/validation.py</code>
</td>
<td>
<a href="api/backend_client.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/api/courses_adapter.py</code>
</td>
<td>
يحوّل مواد الجامعة المصرح بها إلى المرشحين والسياسات التي يفهمها المحرك، مع فصل نوع مادة الخطة عن مجموعة المتطلب وحالة المحاولة السابقة.
</td>
<td>
<pre>group_identity
adapt_courses
_check_source_duplicates
_course
_rules</pre>
</td>
<td>
واجهة وتشغيل
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="api/validation.md">شرح التبعية</a>
<br>
<code>src/api/validation.py</code>
<br>
<a href="recommendation/course_status.md">شرح التبعية</a>
<br>
<code>src/recommendation/course_status.py</code>
<br>
<a href="recommendation/plan_generation.md">شرح التبعية</a>
<br>
<code>src/recommendation/plan_generation.py</code>
</td>
<td>
<a href="api/courses_adapter.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/api/history_adapter.py</code>
</td>
<td>
يوصل شكل الطلب الإداري إلى عقد المجاميع الداخلي من دون حفظ أو تفعيل نسخة. يحافظ على استقلال التحقق عند غياب التاريخ.
</td>
<td>
<pre>adapt_history_delta</pre>
</td>
<td>
واجهة وتشغيل
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="api/validation.md">شرح التبعية</a>
<br>
<code>src/api/validation.py</code>
<br>
<a href="recommendation/history_update.md">شرح التبعية</a>
<br>
<code>src/recommendation/history_update.py</code>
</td>
<td>
<a href="api/history_adapter.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/api/schemas.py</code>
</td>
<td>
يفصل أشكال الطلبات العامة عن الحسابات. يمنع تمرير حقول غير معروفة ويسجل الهوية وسياقي الجلب ومصادر القيم والسياسات الإدارية صراحةً.
</td>
<td>
<pre>Envelope
Identity
SourceContexts
SourcedValue
RegistrationPolicy
TotalRegCreditsSource
IntegrationContext
StudentValidationRequest
CoursesValidationRequest
RecommendationRequest
Finalization
HistoryDeltaRequest
HistoryModeRequest
HistoryInitializeRequest
HistoryCommitRequest
HistoryActivationRequest</pre>
</td>
<td>
واجهة وتشغيل
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="api/schemas.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/api/service.py</code>
</td>
<td>
يجمع النقل والمحولات والأصول والمحرك من دون نقل التدريب إلى الواجهة. هو المكان الذي يقرر هل الطلب صالح ومكتمل وجاهز قبل أول توقع.
</td>
<td>
<pre>ApiService</pre>
</td>
<td>
واجهة وتشغيل
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="api/courses_adapter.md">شرح التبعية</a>
<br>
<code>src/api/courses_adapter.py</code>
<br>
<a href="api/history_adapter.md">شرح التبعية</a>
<br>
<code>src/api/history_adapter.py</code>
<br>
<a href="api/settings.md">شرح التبعية</a>
<br>
<code>src/api/settings.py</code>
<br>
<a href="api/student_adapter.md">شرح التبعية</a>
<br>
<code>src/api/student_adapter.py</code>
<br>
<a href="api/validation.md">شرح التبعية</a>
<br>
<code>src/api/validation.py</code>
</td>
<td>
<a href="api/service.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/api/settings.py</code>
</td>
<td>
يجمع إعداد النقل والأمن والاختبار والتاريخ دون أسرار مكتوبة في المصدر، ويكشف الإعداد المتعارض مبكرًا.
</td>
<td>
<pre>validate_backend_url
ApiSettings</pre>
</td>
<td>
واجهة وتشغيل
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="api/settings.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/api/student_adapter.py</code>
</td>
<td>
يحوّل الرد الجامعي إلى لقطة الطالب المطلوبة للتوقع دون تسريب نتيجة فصل الهدف، ويشرح الميزات المتاحة والمفقودة بدل اختراع قيم لها.
</td>
<td>
<pre>adapt_student
_official_gpa_credits
_history</pre>
</td>
<td>
واجهة وتشغيل
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="api/validation.md">شرح التبعية</a>
<br>
<code>src/api/validation.py</code>
<br>
<a href="data/academic_calendar.md">شرح التبعية</a>
<br>
<code>src/data/academic_calendar.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="features/temporal_features.md">شرح التبعية</a>
<br>
<code>src/features/temporal_features.py</code>
<br>
<a href="recommendation/inputs.md">شرح التبعية</a>
<br>
<code>src/recommendation/inputs.py</code>
</td>
<td>
<a href="api/student_adapter.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/api/validation.py</code>
</td>
<td>
يوحّد التحقق الصغير المشترك حتى لا تختلف حدود الطالب والمواد والتاريخ في تفسير الهوية أو الأعداد أو مصادر القيم.
</td>
<td>
<pre>ApiError
identifier
number
part
response_data
identity
check_record_identity
binding
sourced
ValidationResult
json_safe</pre>
</td>
<td>
واجهة وتشغيل
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="api/validation.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## نواة التوصية

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/recommendation/__init__.py</code>
</td>
<td>
يجمع أسماء الواجهات العامة للنواة للتوافق وسهولة الاستيراد، من دون حساب مستقل.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="recommendation/artifacts.md">شرح التبعية</a>
<br>
<code>src/recommendation/artifacts.py</code>
<br>
<a href="recommendation/constraints.md">شرح التبعية</a>
<br>
<code>src/recommendation/constraints.py</code>
<br>
<a href="recommendation/course_status.md">شرح التبعية</a>
<br>
<code>src/recommendation/course_status.py</code>
<br>
<a href="recommendation/engine.md">شرح التبعية</a>
<br>
<code>src/recommendation/engine.py</code>
<br>
<a href="recommendation/history_update.md">شرح التبعية</a>
<br>
<code>src/recommendation/history_update.py</code>
</td>
<td>
<a href="recommendation/__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/artifacts.py</code>
</td>
<td>
يحافظ على مسار التوصية المحلي المدعوم بزوج رسمي واحد وتاريخ صريح، مع فحص العقود.
</td>
<td>
<pre>model_training_provenance
load_recommendation_artifacts</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="grade_scale.md">شرح التبعية</a>
<br>
<code>src/grade_scale.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="recommendation/artifacts.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/balance_policy.py</code>
</td>
<td>
يصف مزيج الإعادات والمواد الجديدة دون فرض حصة صلاحية أو توقع جديد.
</td>
<td>
<pre>BalancePolicy
_course_records
compute_balance_components</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="recommendation/constraints.md">شرح التبعية</a>
<br>
<code>src/recommendation/constraints.py</code>
</td>
<td>
<a href="recommendation/balance_policy.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/benchmark.py</code>
</td>
<td>
يوفر قياسًا محليًا متكررًا لوقت المحرك السابق والذاكرة مع مدخلات طلب صريحة.
</td>
<td>
<pre>peak_memory_mib
benchmark
main</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
<br>
<a href="recommendation/engine.md">شرح التبعية</a>
<br>
<code>src/recommendation/engine.py</code>
<br>
<a href="recommendation/inputs.md">شرح التبعية</a>
<br>
<code>src/recommendation/inputs.py</code>
<br>
<a href="recommendation/output.md">شرح التبعية</a>
<br>
<code>src/recommendation/output.py</code>
</td>
<td>
<a href="recommendation/benchmark.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/constraints.py</code>
</td>
<td>
يفصل صلاحية الخطة عن جودة توقعها وترتيبها. لا يحق لدرجة مرتفعة تجاوز سقف متطلب أو ساعات إعادة.
</td>
<td>
<pre>_credit_value
_requirement_id
normalize_requirement_policies
PlanConstraints
enumerate_feasible_plan_indices</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="recommendation/plan_generation.md">شرح التبعية</a>
<br>
<code>src/recommendation/plan_generation.py</code>
</td>
<td>
<a href="recommendation/constraints.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/course_status.py</code>
</td>
<td>
يحافظ على فصل الجديد والراسب والمنسحب والسابق الآخر في القيود والتوازن.
</td>
<td>
<pre>normalize_previous_status
classify_candidate_status</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="recommendation/course_status.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/cumulative_history.py</code>
</td>
<td>
يضع حول مدير التاريخ آلية دائمة للوضع والموافقة والمؤشر النشط، مع تخزين مستقل لا يكتب داخل جذور التاريخ السابقة.
</td>
<td>
<pre>HistoryUpdateError
_now
_digest
_approval
_confirmation
_overlap
CumulativeHistoryStore
_ServingHistoryManager</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
<br>
<a href="recommendation/history_update.md">شرح التبعية</a>
<br>
<code>src/recommendation/history_update.py</code>
</td>
<td>
<a href="recommendation/cumulative_history.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/engine.py</code>
</td>
<td>
يحتفظ بمسار التوصية المحلي الرسمي السابق؛ ليس المحرك الذي تختاره واجهة المرحلتين الحالية.
</td>
<td>
<pre>resolve_current_gpa_credits
AcademicPlanRecommender</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="features/temporal_features.md">شرح التبعية</a>
<br>
<code>src/features/temporal_features.py</code>
<br>
<a href="recommendation/artifacts.md">شرح التبعية</a>
<br>
<code>src/recommendation/artifacts.py</code>
<br>
<a href="recommendation/inputs.md">شرح التبعية</a>
<br>
<code>src/recommendation/inputs.py</code>
</td>
<td>
<a href="recommendation/engine.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/history_update.py</code>
</td>
<td>
يضيف نتائج فصل نهائي مجمّعة إلى نسخة من التاريخ بدل إعادة بناء الصفوف الفردية، ويمنع التكرار والتعارض ويحفظ اتساق اللقطة طوال الطلب.
</td>
<td>
<pre>_number
_part
_canonical_number
HistoryDelta
normalize_history_delta
validate_history_state
apply_history_delta
_apply_normalized_delta
HistorySnapshot
_validate_update_metadata
FrozenHistoryManager</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="features/temporal_features.md">شرح التبعية</a>
<br>
<code>src/features/temporal_features.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="recommendation/history_update.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/inputs.py</code>
</td>
<td>
يفصل قراءة الملفات المحلية وتطبيع أغلفة النواة عن نقل الواجهات، ويوحّد فحص اللقطة والمرشحين والسياسات.
</td>
<td>
<pre>CandidateImportError
read_candidate_file
normalize_candidates
build_student_snapshot
validate_snapshot
load_local_inputs
PreparedRecommendationInputs
_payload_id
_payload_number
_payload_part
_validate_payload_identity
normalize_student_payload
_explicitly_ineligible
normalize_candidate_payloads
normalize_request_payload
prepare_recommendation_payloads</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/academic_calendar.md">شرح التبعية</a>
<br>
<code>src/data/academic_calendar.py</code>
<br>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="features/temporal_features.md">شرح التبعية</a>
<br>
<code>src/features/temporal_features.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
<br>
<a href="recommendation/constraints.md">شرح التبعية</a>
<br>
<code>src/recommendation/constraints.py</code>
</td>
<td>
<a href="recommendation/inputs.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/local_cli.py</code>
</td>
<td>
توصل ملفات المرشحين واللقطة إلى المحرك الرسمي السابق وتحفظ أثر التنفيذ.
</td>
<td>
<pre>main</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
<br>
<a href="recommendation/engine.md">شرح التبعية</a>
<br>
<code>src/recommendation/engine.py</code>
<br>
<a href="recommendation/inputs.md">شرح التبعية</a>
<br>
<code>src/recommendation/inputs.py</code>
<br>
<a href="recommendation/output.md">شرح التبعية</a>
<br>
<code>src/recommendation/output.py</code>
<br>
<a href="recommendation/plan_generation.md">شرح التبعية</a>
<br>
<code>src/recommendation/plan_generation.py</code>
</td>
<td>
<a href="recommendation/local_cli.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/output.py</code>
</td>
<td>
يعزل التسلسل وحفظ الملفات عن الحساب والترتيب.
</td>
<td>
<pre>write_json
save_recommendations</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="recommendation/output.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/plan_generation.py</code>
</td>
<td>
ينشئ عضويات الخطط دون توقعات أو ترتيب، ويحافظ على الكسور وهوية المواد ذات الساعات الصفرية.
</td>
<td>
<pre>decimal_credit_units
sum_credit_values
resolve_credit_bounds
enumerate_plan_indices
build_plan_rows</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="recommendation/plan_generation.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/plan_scoring.py</code>
</td>
<td>
يجمع الحسابات المشتركة للتوقع ومعدل الخطة والمعدل التراكمي المتوقع، كي تستخدمها المرحلتان والمحرك المحلي بتعريف واحد.
</td>
<td>
<pre>score_course_rows
rank_plans
project_cumulative_gpa
summarize_scored_plans
empty_summaries</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
</td>
<td>
<a href="recommendation/plan_scoring.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/ranking.py</code>
</td>
<td>
يفصل معايير اختيار الأولى عن ترتيب النهائي ويحفظ هوية خطة مستقلة عن ترتيب صفوف المواد.
</td>
<td>
<pre>PlanIdentity
canonical_plan_identity
RankingStrategy
_validated_rows
_academic_key
rank_academic_reference
_pareto_levels
rank_evaluation_plans</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="recommendation/balance_policy.md">شرح التبعية</a>
<br>
<code>src/recommendation/balance_policy.py</code>
</td>
<td>
<a href="recommendation/ranking.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/ranking_policy.py</code>
</td>
<td>
يتحقق من القرار البشري المسجل في البيان ولا يصدر قرار اعتماد بنفسه.
</td>
<td>
<pre>balance_policy_contract
validate_ranking_policy</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="recommendation/balance_policy.md">شرح التبعية</a>
<br>
<code>src/recommendation/balance_policy.py</code>
<br>
<a href="recommendation/ranking.md">شرح التبعية</a>
<br>
<code>src/recommendation/ranking.py</code>
</td>
<td>
<a href="recommendation/ranking_policy.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/shortlist.py</code>
</td>
<td>
يستخدم توقع المادة مرة واحدة ليختار الخطط التي تستحق إعادة توقعها مع سياقها في المرحلة الثانية.
</td>
<td>
<pre>ShortlistResult
build_stage1_shortlist</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="recommendation/balance_policy.md">شرح التبعية</a>
<br>
<code>src/recommendation/balance_policy.py</code>
<br>
<a href="recommendation/constraints.md">شرح التبعية</a>
<br>
<code>src/recommendation/constraints.py</code>
<br>
<a href="recommendation/plan_scoring.md">شرح التبعية</a>
<br>
<code>src/recommendation/plan_scoring.py</code>
<br>
<a href="recommendation/ranking.md">شرح التبعية</a>
<br>
<code>src/recommendation/ranking.py</code>
</td>
<td>
<a href="recommendation/shortlist.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/two_stage_artifacts.py</code>
</td>
<td>
يحمي التشغيل من تحميل مودل تجريبي أو ترتيب ميزات أو أهداف أو نسخ فئات لا تطابق الاعتماد.
</td>
<td>
<pre>ModelPair
TwoStageArtifacts
stage_feature_contract
artifact_relative_paths
project_file
read_artifact_json
_is_sha256
verify_artifact_hash
validate_stage_metadata
load_model_pair
validate_archived_provenance
validate_artifact_manifest
load_manifest_assets
load_two_stage_artifacts</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="features/temporal_features.md">شرح التبعية</a>
<br>
<code>src/features/temporal_features.py</code>
<br>
<a href="grade_scale.md">شرح التبعية</a>
<br>
<code>src/grade_scale.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="recommendation/two_stage_artifacts.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation/two_stage_engine.py</code>
</td>
<td>
ينسق المحرك المرشحين والقيود والتاريخ ومودلات المرحلتين واختياري الترتيب المستقلين، ويحفظ مصدر القرار في البيانات الوصفية.
</td>
<td>
<pre>_json_value
_input_fingerprint
TwoStagePlanRecommender</pre>
</td>
<td>
نواة التوصية
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/temporal_features.md">شرح التبعية</a>
<br>
<code>src/features/temporal_features.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
<br>
<a href="recommendation/balance_policy.md">شرح التبعية</a>
<br>
<code>src/recommendation/balance_policy.py</code>
<br>
<a href="recommendation/history_update.md">شرح التبعية</a>
<br>
<code>src/recommendation/history_update.py</code>
</td>
<td>
<a href="recommendation/two_stage_engine.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## هندسة الميزات والتاريخ

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/features/__init__.py</code>
</td>
<td>
يحدد حزمة بايثون ويضع وصفًا قصيرًا إن وجد؛ ليس خطوة تنفيذ أكاديمية.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="features/__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/features/build_frozen_history.py</code>
</td>
<td>
توفر مدخل تنفيذ صريح لإنشاء نسخة خدمة من نتائج موثقة بدل بناء تاريخ تلقائي عند الطلب.
</td>
<td>
<pre>main</pre>
</td>
<td>
ميزات مشتركة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="features/build_frozen_history.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/features/build_temporal_features.py</code>
</td>
<td>
يربط حسابات التاريخ وسياق التسجيل وحالة الطالب في جدول الميزات النهائي.
</td>
<td>
<pre>attach_plan_context
build_feature_tables
print_feature_summary
main</pre>
</td>
<td>
ميزات مشتركة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/temporal_features.md">شرح التبعية</a>
<br>
<code>src/features/temporal_features.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="features/build_temporal_features.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/features/feature_contract.py</code>
</td>
<td>
يثبت قائمة الميزات وترتيبها وأنواعها ومستويات الفئات؛ أسماء الأعمدة وحدها لا تكفي لتوافق مصفوفة مع مودل محفوظ.
</td>
<td>
<pre>require_current_features
learn_category_levels
prepare_model_matrix
save_category_levels
load_category_levels</pre>
</td>
<td>
ميزات مشتركة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="features/feature_contract.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/features/frozen_history.py</code>
</td>
<td>
يفصل نسخة تاريخ الخدمة النهائية عن أصول التدريب، ويضمن أن اسم القطع والبيانات والبصمات تصف النسخة نفسها.
</td>
<td>
<pre>file_sha256
previous_academic_part
validate_history_selection
validate_history_pair
build_frozen_history
verify_legacy_course_history
save_frozen_history
load_frozen_history
save_frozen_history_atomic</pre>
</td>
<td>
ميزات مشتركة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/temporal_features.md">شرح التبعية</a>
<br>
<code>src/features/temporal_features.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="features/frozen_history.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/features/student_course_status.py</code>
</td>
<td>
يوفر حالة سابقة دقيقة للتجارب والتحليل، دون تحويلها إلى ميزة رسمية للمودل الحالي.
</td>
<td>
<pre>_keys
previous_status_for_targets</pre>
</td>
<td>
ميزات مشتركة
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="features/student_course_status.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/features/temporal_features.py</code>
</td>
<td>
يحفظ التعريف الواحد لتاريخ المواد والمعدل السابق وسياق الخطة، كي لا تحسب مرحلة التدريب والتوصية ميزات مختلفة بالاسم نفسه.
</td>
<td>
<pre>temporal_weight
_joined_key
build_history_keys
CourseHistoryState
build_temporal_course_history
compute_student_gpa_history
add_student_history_features
compute_plan_context_features
save_course_history_state
load_course_history_state</pre>
</td>
<td>
ميزات مشتركة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="features/temporal_features.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## التدريب

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/modeling/__init__.py</code>
</td>
<td>
يحدد حزمة بايثون ويضع وصفًا قصيرًا إن وجد؛ ليس خطوة تنفيذ أكاديمية.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="modeling/__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/modeling/train_models.py</code>
</td>
<td>
يدرّب مودل علامة ومودل احتمال رسوب، ويختار الإعداد بطيّات زمنية قبل تقييم الاختبار اللاحق.
</td>
<td>
<pre>_lightgbm
regression_metrics
classification_metrics
calibration_table
shared_parameters
prepare_folds
train_one
tune_model
feature_importance
_json_default
main</pre>
</td>
<td>
تدريب
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="modeling/training_config.md">شرح التبعية</a>
<br>
<code>src/modeling/training_config.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="modeling/train_models.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/modeling/training_config.py</code>
</td>
<td>
يعزل تعريف الهدف والوزن الزمني المشترك الذي تستعمله الملاءمة.
</td>
<td>
<pre>training_weights</pre>
</td>
<td>
تدريب
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="modeling/training_config.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## البيانات والتنظيف

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/data/__init__.py</code>
</td>
<td>
يحدد حزمة بايثون ويضع وصفًا قصيرًا إن وجد؛ ليس خطوة تنفيذ أكاديمية.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="data/__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/academic_calendar.py</code>
</td>
<td>
يحسب فجوات الدراسة وفق الفصول المنتظمة بدل فرق الأرقام الخام.
</td>
<td>
<pre>is_regular_semester
count_regular_semesters_between</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="data/academic_calendar.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/build_registration_roster.py</code>
</td>
<td>
يحفظ مواد التسجيل بما فيها الحالات التي ليست نتائج تدريب صالحة، حتى يصف سياق خطة الطالب حمله الفعلي.
</td>
<td>
<pre>build_registration_roster
main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/build_temporal_split.md">شرح التبعية</a>
<br>
<code>src/data/build_temporal_split.py</code>
<br>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="data/build_registration_roster.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/build_student_course_enriched.py</code>
</td>
<td>
يجهز الجدول الموحد الذي ستنضم إليه معلومات الدبلوم قبل فصل التدريب.
</td>
<td>
<pre>main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="data/build_student_course_enriched.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/build_temporal_split.py</code>
</td>
<td>
يمنع اختيار الصفوف عشوائيًا عبر الزمن ويعزل فصلًا غير مكتمل عن التقييم.
</td>
<td>
<pre>build_temporal_split
summarize_split
main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="data/build_temporal_split.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/clean_degree_course.py</code>
</td>
<td>
ينتج المصدر المرجعي لنوع مادة الخطة وساعاتها وترتيبها.
</td>
<td>
<pre>clean_degree_course
main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="data/clean_degree_course.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/clean_outliers.py</code>
</td>
<td>
يبني سببًا قابلًا للتدقيق لكل طالب يستبعده تنظيف التدريب بدل حذف صف متطرف بلا أثر.
</td>
<td>
<pre>_validate_columns
_summarize_rule
build_outlier_audit
remove_outlier_students
main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="data/clean_outliers.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/clean_student_course.py</code>
</td>
<td>
يجعل النتائج المستخدمة للتدريب قابلة للربط، ويحفظ رقم المحاولة قبل تصفية النتائج غير المدعومة.
</td>
<td>
<pre>clean_student_course
main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="data/clean_student_course.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/clean_student_diploma.py</code>
</td>
<td>
يوفر مدخلي الدبلوم للمودل دون تضاعف الصفوف عند الربط.
</td>
<td>
<pre>clean_student_diploma
merge_student_course_with_diploma
main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="data/clean_student_diploma.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/clean_student_status.py</code>
</td>
<td>
ينتج الصفوف الزمنية المرجعية ويحسب آخر معدل مسجل والفجوات قبل تصفية حالة الدراسة.
</td>
<td>
<pre>add_enrollment_features
clean_student_status
main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/academic_calendar.md">شرح التبعية</a>
<br>
<code>src/data/academic_calendar.py</code>
<br>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="data/clean_student_status.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/cleaning_utils.py</code>
</td>
<td>
يوحد تفسير المعرفات والقيم الخالية وأسماء الأعمدة لجميع خطوات البيانات.
</td>
<td>
<pre>clean_column_names
clean_id
clean_id_columns
extract_university_id
to_integer
to_float</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="data/cleaning_utils.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/filter_common_students.py</code>
</td>
<td>
يجعل جدولي الحالة والنتائج يتشاركان الطلاب دون حذف فصول طالب مشترك بسبب عدم تطابق صف بعينه.
</td>
<td>
<pre>filter_common_students
main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="data/filter_common_students.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/xml_spreadsheet.py</code>
</td>
<td>
يعزل قراءة صيغة جدول الجامعة عن تطبيع البيانات الأكاديمية.
</td>
<td>
<pre>clean_xml
load_xml
get_value</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="data/xml_spreadsheet.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/data/xml_to_json.py</code>
</td>
<td>
يحوّل أوراق التصدير إلى سجلات قابلة للقراءة محليًا؛ ليس نقطة جلب جامعية.
</td>
<td>
<pre>convert_xml_to_json
main</pre>
</td>
<td>
إعداد بيانات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/xml_spreadsheet.md">شرح التبعية</a>
<br>
<code>src/data/xml_spreadsheet.py</code>
</td>
<td>
<a href="data/xml_to_json.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## التقييم

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/evaluation/__init__.py</code>
</td>
<td>
يحدد حزمة بايثون ويضع وصفًا قصيرًا إن وجد؛ ليس خطوة تنفيذ أكاديمية.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="evaluation/__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/evaluation/analyze_model_errors.py</code>
</td>
<td>
يفسر مواضع الخطأ ويقارنها عبر سنوات واختصاصات وشرائح.
</td>
<td>
<pre>one_way_effect_size
course_metrics
plan_metrics
selected_fold_iterations
fit_historical_grade_model
attach_analysis_columns
make_out_of_time_predictions
build_plan_frame
build_year_analysis
build_degree_analysis
build_year_degree_analysis
segment_metrics
build_plan_segments
build_course_segments
feature_family
build_shap_importance
main</pre>
</td>
<td>
تقييم
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="evaluation/evaluate_plan_gpa.md">شرح التبعية</a>
<br>
<code>src/evaluation/evaluate_plan_gpa.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="grade_scale.md">شرح التبعية</a>
<br>
<code>src/grade_scale.py</code>
<br>
<a href="modeling/train_models.md">شرح التبعية</a>
<br>
<code>src/modeling/train_models.py</code>
<br>
<a href="modeling/training_config.md">شرح التبعية</a>
<br>
<code>src/modeling/training_config.py</code>
</td>
<td>
<a href="evaluation/analyze_model_errors.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/evaluation/evaluate_plan_gpa.py</code>
</td>
<td>
يقيس دقة مودل العلامة على خطط الطلاب المرصودة، لا جودة اختيار خطة لم تُسجل.
</td>
<td>
<pre>predict_course_points
aggregate_plan_gpa
summarize_plan_errors
build_metrics_report
print_report
main</pre>
</td>
<td>
تقييم
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="grade_scale.md">شرح التبعية</a>
<br>
<code>src/grade_scale.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="evaluation/evaluate_plan_gpa.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/evaluation/evaluate_xml_recommendations.py</code>
</td>
<td>
يقارن توصيات محلية بمواد مسجلة في أمثلة تصدير ويكتب تقارير أثر.
</td>
<td>
<pre>parse_args
json_value
write_json
xml_rows
source_candidates
one_id
actual_metrics
observed_plan_estimate
course_overlap
markdown_number
course_text
report_markdown
run_case
main</pre>
</td>
<td>
تقييم
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="data/xml_spreadsheet.md">شرح التبعية</a>
<br>
<code>src/data/xml_spreadsheet.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
<br>
<a href="recommendation/__init__.md">شرح التبعية</a>
<br>
<code>src/recommendation/__init__.py</code>
<br>
<a href="recommendation/inputs.md">شرح التبعية</a>
<br>
<code>src/recommendation/inputs.py</code>
</td>
<td>
<a href="evaluation/evaluate_xml_recommendations.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## التشخيص والتحليل

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/diagnostics/__init__.py</code>
</td>
<td>
يحدد حزمة بايثون ويضع وصفًا قصيرًا إن وجد؛ ليس خطوة تنفيذ أكاديمية.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="diagnostics/__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/diagnostics/analyze_course_plan_changes.py</code>
</td>
<td>
يصف اختلافات أسماء المواد وساعاتها وأنواعها في مصادر النسخة الأولى.
</td>
<td>
<pre>normalize_name
print_table
main</pre>
</td>
<td>
تشخيص
<br>
واجهة قديمة مدعومة أو تحليل مصدر سابق
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="diagnostics/analyze_course_plan_changes.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/diagnostics/analyze_repeat_withdrawal_balance.py</code>
</td>
<td>
يجمع مصادر السجل والتحليل وتقرير نطاق التوازن مع حماية الملفات.
</td>
<td>
<pre>sha256
protected_manifest
graph_navigation
finish_status_inventory
status_evidence
grade_range_disagreements
nonstandard_history_sensitivity
run
main</pre>
</td>
<td>
تشخيص
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="diagnostics/repeat_withdrawal_balance.md">شرح التبعية</a>
<br>
<code>src/diagnostics/repeat_withdrawal_balance.py</code>
<br>
<a href="diagnostics/repeat_withdrawal_report.md">شرح التبعية</a>
<br>
<code>src/diagnostics/repeat_withdrawal_report.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="diagnostics/analyze_repeat_withdrawal_balance.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/diagnostics/compare_student_status_course.py</code>
</td>
<td>
يفحص التشارك بين جدولي الحالة والمواد المنظفين.
</td>
<td>
<pre>main</pre>
</td>
<td>
تشخيص
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="diagnostics/compare_student_status_course.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/diagnostics/repeat_withdrawal_balance.py</code>
</td>
<td>
يبني وصفًا رجعيًا للتسجيل ومخزون آخر محاولات، لا قواعد أهلية مباشرة.
</td>
<td>
<pre>semantic_status
prepare_attempts
student_totals
analyze_semesters
describe_metrics
credit_bins</pre>
</td>
<td>
تشخيص
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
</td>
<td>
<a href="diagnostics/repeat_withdrawal_balance.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/diagnostics/repeat_withdrawal_report.py</code>
</td>
<td>
يعرض المجموعات والقيم المتطرفة والبدائل المقترحة دون منحها صلاحية تسجيل.
</td>
<td>
<pre>write_json
markdown_table
cohorts
policy_candidates
aggregate_outputs
outlier_outputs
render_summary</pre>
</td>
<td>
تشخيص
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="diagnostics/repeat_withdrawal_balance.md">شرح التبعية</a>
<br>
<code>src/diagnostics/repeat_withdrawal_balance.py</code>
</td>
<td>
<a href="diagnostics/repeat_withdrawal_report.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## تجارب الميزات والمودلات

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/experiments/__init__.py</code>
</td>
<td>
يحدد حزمة بايثون ويضع وصفًا قصيرًا إن وجد؛ ليس خطوة تنفيذ أكاديمية.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="experiments/__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/attempt_number_analysis.py</code>
</td>
<td>
يقارن التوزيع والخطأ بين المحاولة الأولى والإعادة والثالثة وما بعدها.
</td>
<td>
<pre>subsets
distribution
save_table
descriptive_analysis
evaluate_predictions</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="evaluation/evaluate_plan_gpa.md">شرح التبعية</a>
<br>
<code>src/evaluation/evaluate_plan_gpa.py</code>
<br>
<a href="experiments/attempt_number_core.md">شرح التبعية</a>
<br>
<code>src/experiments/attempt_number_core.py</code>
<br>
<a href="grade_scale.md">شرح التبعية</a>
<br>
<code>src/grade_scale.py</code>
<br>
<a href="modeling/train_models.md">شرح التبعية</a>
<br>
<code>src/modeling/train_models.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="experiments/attempt_number_analysis.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/attempt_number_core.py</code>
</td>
<td>
يدعم ثلاث صيغ بحثية لرقم المحاولة: كما هو، أو علم إعادة، أو حذفه. يحفظ هوية الصفوف وحماية الأصول.
</td>
<td>
<pre>write_json
transform_matrix
row_fingerprint
paired_cluster_interval
protected_manifest
capture_protected
verify_protected</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="experiments/attempt_number_core.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/attempt_number_report.py</code>
</td>
<td>
يجمع النتائج المسجلة في وثيقة قرار بحثي واضحة.
</td>
<td>
<pre>table
build_report</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/attempt_number_core.md">شرح التبعية</a>
<br>
<code>src/experiments/attempt_number_core.py</code>
</td>
<td>
<a href="experiments/attempt_number_report.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/attempt_number_training.py</code>
</td>
<td>
يدرب صيغًا معزولة مع إبقاء إعدادات المقارنة موثقة.
</td>
<td>
<pre>load_frames
model_metrics
run_training</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/attempt_number_core.md">شرح التبعية</a>
<br>
<code>src/experiments/attempt_number_core.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="modeling/train_models.md">شرح التبعية</a>
<br>
<code>src/modeling/train_models.py</code>
<br>
<a href="modeling/training_config.md">شرح التبعية</a>
<br>
<code>src/modeling/training_config.py</code>
</td>
<td>
<a href="experiments/attempt_number_training.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/attempt_number_validation.py</code>
</td>
<td>
يعيد التحقق من أرقام المقارنة الزمنية الأصلية قبل تفسير التجربة.
</td>
<td>
<pre>original_validation</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/attempt_number_analysis.md">شرح التبعية</a>
<br>
<code>src/experiments/attempt_number_analysis.py</code>
<br>
<a href="experiments/attempt_number_core.md">شرح التبعية</a>
<br>
<code>src/experiments/attempt_number_core.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="grade_scale.md">شرح التبعية</a>
<br>
<code>src/grade_scale.py</code>
<br>
<a href="modeling/train_models.md">شرح التبعية</a>
<br>
<code>src/modeling/train_models.py</code>
</td>
<td>
<a href="experiments/attempt_number_validation.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/course_only_core.py</code>
</td>
<td>
يختبر فصل توقع المادة عن سياق الخطة باستخدام عقد ثلاثة وثلاثين مدخلًا.
</td>
<td>
<pre>prepare_course_matrix
prepare_course_rows
score_courses_once
optimize_exact_credits
distribution
plan_context_sensitivity
compare_course_sets</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="features/temporal_features.md">شرح التبعية</a>
<br>
<code>src/features/temporal_features.py</code>
<br>
<a href="recommendation/inputs.md">شرح التبعية</a>
<br>
<code>src/recommendation/inputs.py</code>
<br>
<a href="recommendation/plan_generation.md">شرح التبعية</a>
<br>
<code>src/recommendation/plan_generation.py</code>
</td>
<td>
<a href="experiments/course_only_core.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/course_only_evaluation.py</code>
</td>
<td>
يقارن مجموعات الخطط والوقت وعدد صفوف التوقع في مسارين منفصلين.
</td>
<td>
<pre>PredictionCounter
official_plan_lookup
compare_case
save_case
select_batch_cases
run_comparisons
capture_protected_files
verify_protected_files</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="data/cleaning_utils.md">شرح التبعية</a>
<br>
<code>src/data/cleaning_utils.py</code>
<br>
<a href="experiments/course_only_core.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_core.py</code>
<br>
<a href="experiments/course_only_training.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_training.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="experiments/course_only_evaluation.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/course_only_recommendation.py</code>
</td>
<td>
يجمع تدريب التجربة والمقارنة والتقرير كتشغيل بحثي صريح.
</td>
<td>
<pre>main</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/course_only_evaluation.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_evaluation.py</code>
<br>
<a href="experiments/course_only_report.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_report.py</code>
<br>
<a href="experiments/course_only_training.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_training.py</code>
<br>
<a href="recommendation/engine.md">شرح التبعية</a>
<br>
<code>src/recommendation/engine.py</code>
</td>
<td>
<a href="experiments/course_only_recommendation.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/course_only_report.py</code>
</td>
<td>
يفصل كتابة التقرير عن التدريب والقياس.
</td>
<td>
<pre>read_json
table
plan_table
build_report</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/course_only_core.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_core.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="experiments/course_only_report.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/course_only_training.py</code>
</td>
<td>
ينشئ أصول تجربة الثلاثة والثلاثين التي كانت مصدرًا لترقية المرحلة الأولى.
</td>
<td>
<pre>write_json
training_signature
prepare_course_folds
train_experiment
load_experiment</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/course_only_core.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_core.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="modeling/train_models.md">شرح التبعية</a>
<br>
<code>src/modeling/train_models.py</code>
<br>
<a href="modeling/training_config.md">شرح التبعية</a>
<br>
<code>src/modeling/training_config.py</code>
</td>
<td>
<a href="experiments/course_only_training.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/degree_points.py</code>
</td>
<td>
يقارن بدائل بحثية مع مرجع العلامة الرسمي ويختار وفق سنوات التحقق.
</td>
<td>
<pre>load_feature_frames
run_validation
selected_round_count
load_or_train_holdout
compare_holdout_by_degree
main</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/degree_points_config.md">شرح التبعية</a>
<br>
<code>src/experiments/degree_points_config.py</code>
<br>
<a href="experiments/experiment_io.md">شرح التبعية</a>
<br>
<code>src/experiments/experiment_io.py</code>
<br>
<a href="experiments/modeling.md">شرح التبعية</a>
<br>
<code>src/experiments/modeling.py</code>
<br>
<a href="experiments/specialty_history.md">شرح التبعية</a>
<br>
<code>src/experiments/specialty_history.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
</td>
<td>
<a href="experiments/degree_points.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/degree_points_config.py</code>
</td>
<td>
يسمي بدائل أهداف وميزات وأوزان تجربة الاختصاص دون تغيير العقد الرسمي.
</td>
<td>
<pre>—</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
</td>
<td>
<a href="experiments/degree_points_config.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/experiment_io.py</code>
</td>
<td>
يحفظ نتائج التجربة ويفصل إعادة الاستخدام عن فقدان المصدر.
</td>
<td>
<pre>experiment_signature
load_cached_validation
build_metadata
_json_default
save_results
print_summary</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/degree_points_config.md">شرح التبعية</a>
<br>
<code>src/experiments/degree_points_config.py</code>
<br>
<a href="experiments/modeling.md">شرح التبعية</a>
<br>
<code>src/experiments/modeling.py</code>
<br>
<a href="experiments/specialty_history.md">شرح التبعية</a>
<br>
<code>src/experiments/specialty_history.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="experiments/experiment_io.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/modeling.py</code>
</td>
<td>
يوفر أدوات تجربة الاختصاص دون اعتمادها في تقديم التوصيات.
</td>
<td>
<pre>feature_columns
learn_levels
prepare_matrix
fit_weights
fit_experiment_model
course_predictions
aggregate_plans
prediction_metrics
evaluate_variant
validation_summary
select_variant
degree_metrics
evaluate_selected_holdout</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/specialty_history.md">شرح التبعية</a>
<br>
<code>src/experiments/specialty_history.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="modeling/train_models.md">شرح التبعية</a>
<br>
<code>src/modeling/train_models.py</code>
<br>
<a href="modeling/training_config.md">شرح التبعية</a>
<br>
<code>src/modeling/training_config.py</code>
</td>
<td>
<a href="experiments/modeling.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/previous_course_status_data.py</code>
</td>
<td>
يلحق حالة آخر محاولة بالميزات في ملفات بحثية منفصلة.
</td>
<td>
<pre>build_status_history
augment_feature_frame
_distribution
build_experimental_datasets</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="features/student_course_status.md">شرح التبعية</a>
<br>
<code>src/features/student_course_status.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="experiments/previous_course_status_data.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/previous_course_status_evaluation.py</code>
</td>
<td>
يقارن النموذج الأساسي والموسع على الصفوف نفسها وشرائح الحالات.
</td>
<td>
<pre>status_slices
_predict
_paired_metrics
_check_saved_baseline
_retake_sample
evaluate_holdout</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/course_only_core.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_core.py</code>
<br>
<a href="experiments/course_only_training.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_training.py</code>
<br>
<a href="experiments/previous_course_status_data.md">شرح التبعية</a>
<br>
<code>src/experiments/previous_course_status_data.py</code>
<br>
<a href="experiments/previous_course_status_training.md">شرح التبعية</a>
<br>
<code>src/experiments/previous_course_status_training.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
</td>
<td>
<a href="experiments/previous_course_status_evaluation.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/previous_course_status_training.py</code>
</td>
<td>
يختبر زيادة عقد المادة إلى أربعة وثلاثين والخطة إلى ثمانية وأربعين دون ترقيتهما للتشغيل.
</td>
<td>
<pre>learn_augmented_levels
prepare_augmented_matrix
prepare_augmented_folds
train_augmented_one
tune_augmented_model
_input_sha256
_load_tables
load_variant
train_all_variants</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/course_only_core.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_core.py</code>
<br>
<a href="experiments/course_only_training.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_training.py</code>
<br>
<a href="experiments/previous_course_status_data.md">شرح التبعية</a>
<br>
<code>src/experiments/previous_course_status_data.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
</td>
<td>
<a href="experiments/previous_course_status_training.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiments/specialty_history.py</code>
</td>
<td>
ينشئ ميزات مجاميع الاختصاص ومتطلبه لأبحاث اختيار الهدف والميزات.
</td>
<td>
<pre>_weighted_history_source
_prior_aggregates
_total_aggregates
_merge_training_history
_merge_frozen_test_history
_safe_average
_finish_specialty_history
add_specialty_history_features
_merge_sequential_test_history
FrozenSpecialtyHistory</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="modeling/training_config.md">شرح التبعية</a>
<br>
<code>src/modeling/training_config.py</code>
</td>
<td>
<a href="experiments/specialty_history.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## تجارب أثر التوصية

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/recommendation_experiments/__init__.py</code>
</td>
<td>
يحدد حزمة بايثون ويضع وصفًا قصيرًا إن وجد؛ ليس خطوة تنفيذ أكاديمية.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="recommendation_experiments/__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation_experiments/previous_course_status_experiment.py</code>
</td>
<td>
يجمع تجهيز البيانات والتدريب والتقييم ومقارنة أثر التوصية في تجربة منفصلة.
</td>
<td>
<pre>_protected_paths
verify_protected_files
main</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/previous_course_status_data.md">شرح التبعية</a>
<br>
<code>src/experiments/previous_course_status_data.py</code>
<br>
<a href="experiments/previous_course_status_evaluation.md">شرح التبعية</a>
<br>
<code>src/experiments/previous_course_status_evaluation.py</code>
<br>
<a href="experiments/previous_course_status_training.md">شرح التبعية</a>
<br>
<code>src/experiments/previous_course_status_training.py</code>
<br>
<a href="features/frozen_history.md">شرح التبعية</a>
<br>
<code>src/features/frozen_history.py</code>
<br>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="recommendation_experiments/previous_course_status_experiment.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommendation_experiments/previous_course_status_inference.py</code>
</td>
<td>
يقارن العقود الأساسية والموسعة مع عضويات متطابقة حتى لا يختلط أثر الميزة بأثر مجموعة المواد.
</td>
<td>
<pre>prepare_augmented_matrix
score_augmented_rows
_pair_scored_rows
pair_course_scores
pair_plan_course_scores
pair_plan_summaries
_attach_status
_load_experimental_models
run_student_comparison</pre>
</td>
<td>
تجريبي
<br>
تجريبي أو وصفي خارج الخدمة
</td>
<td>
<a href="experiments/course_only_core.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_core.py</code>
<br>
<a href="experiments/course_only_training.md">شرح التبعية</a>
<br>
<code>src/experiments/course_only_training.py</code>
<br>
<a href="experiments/previous_course_status_training.md">شرح التبعية</a>
<br>
<code>src/experiments/previous_course_status_training.py</code>
<br>
<a href="features/feature_contract.md">شرح التبعية</a>
<br>
<code>src/features/feature_contract.py</code>
<br>
<a href="features/student_course_status.md">شرح التبعية</a>
<br>
<code>src/features/student_course_status.py</code>
</td>
<td>
<a href="recommendation_experiments/previous_course_status_inference.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## جذر المصدر والأسماء المتوافقة

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية الأساسية
</th>
<th>
الدوال والأصناف العليا
</th>
<th>
الدور والتصنيف
</th>
<th>
تبعيات داخلية مهمة
</th>
<th>
صفحة الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>src/__init__.py</code>
</td>
<td>
يحدد حزمة بايثون ويضع وصفًا قصيرًا إن وجد؛ ليس خطوة تنفيذ أكاديمية.
</td>
<td>
<pre>—</pre>
</td>
<td>
تعريف حزمة
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="__init__.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/benchmark_recommendation.py</code>
</td>
<td>
يحافظ على أمر تشغيل سابق عبر إعادة تصدير وظائف التنفيذ من وحدتها الحالية. وجوده لا يعني وجود خوارزمية مستقلة.
</td>
<td>
<pre>—</pre>
</td>
<td>
مشترك وأدوات
<br>
واجهة قديمة مدعومة أو تحليل مصدر سابق
</td>
<td>
<a href="recommendation/benchmark.md">شرح التبعية</a>
<br>
<code>src/recommendation/benchmark.py</code>
</td>
<td>
<a href="benchmark_recommendation.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/evaluate_xml_recommendations.py</code>
</td>
<td>
يحافظ على أمر تشغيل سابق عبر إعادة تصدير وظائف التنفيذ من وحدتها الحالية. وجوده لا يعني وجود خوارزمية مستقلة.
</td>
<td>
<pre>—</pre>
</td>
<td>
مشترك وأدوات
<br>
واجهة قديمة مدعومة أو تحليل مصدر سابق
</td>
<td>
<a href="evaluation/evaluate_xml_recommendations.md">شرح التبعية</a>
<br>
<code>src/evaluation/evaluate_xml_recommendations.py</code>
</td>
<td>
<a href="evaluate_xml_recommendations.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/experiment_degree_points.py</code>
</td>
<td>
يحافظ على أمر تشغيل سابق عبر إعادة تصدير وظائف التنفيذ من وحدتها الحالية. وجوده لا يعني وجود خوارزمية مستقلة.
</td>
<td>
<pre>—</pre>
</td>
<td>
مشترك وأدوات
<br>
واجهة قديمة مدعومة أو تحليل مصدر سابق
</td>
<td>
<a href="experiments/degree_points.md">شرح التبعية</a>
<br>
<code>src/experiments/degree_points.py</code>
</td>
<td>
<a href="experiment_degree_points.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/grade_scale.py</code>
</td>
<td>
يحافظ على تحويل العلامة المتوقع كما استعمله التدريب والتقييم، مع رفض النسخ غير المدعومة.
</td>
<td>
<pre>GradeScale</pre>
</td>
<td>
مشترك وأدوات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="grade_scale.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/main.py</code>
</td>
<td>
يجمع خطوات المشروع بترتيب تبعيات ظاهر ويتيح العرض دون التنفيذ.
</td>
<td>
<pre>Step
_select_steps
_show_version_boundary
_list_steps
_run_steps
main</pre>
</td>
<td>
مشترك وأدوات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="main.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/paths.py</code>
</td>
<td>
يجمع أسماء أصول البيانات والمودلات والتاريخ ويمنع توزيع مسارات متعارضة بين الطبقات.
</td>
<td>
<pre>versioned_path
academic_part
frozen_history_dir
course_history_state_path
specialty_history_state_path
history_metadata_path</pre>
</td>
<td>
مشترك وأدوات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
لا استيراد داخلي.
</td>
<td>
<a href="paths.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/project_status.py</code>
</td>
<td>
يجمع نظرة تشغيلية إلى الملفات والمرحل وإحصاءات المودلات دون تشغيل البناء.
</td>
<td>
<pre>ProjectStage
relative
print_model_metrics
main</pre>
</td>
<td>
مشترك وأدوات
<br>
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة
</td>
<td>
<a href="paths.md">شرح التبعية</a>
<br>
<code>src/paths.py</code>
</td>
<td>
<a href="project_status.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/recommend_local.py</code>
</td>
<td>
يحافظ على أمر تشغيل سابق عبر إعادة تصدير وظائف التنفيذ من وحدتها الحالية. وجوده لا يعني وجود خوارزمية مستقلة.
</td>
<td>
<pre>—</pre>
</td>
<td>
مشترك وأدوات
<br>
واجهة قديمة مدعومة أو تحليل مصدر سابق
</td>
<td>
<a href="recommendation/local_cli.md">شرح التبعية</a>
<br>
<code>src/recommendation/local_cli.py</code>
</td>
<td>
<a href="recommend_local.md">فتح شرح الملف</a>
</td>
</tr>
<tr>
<td>
<code>src/xml_2_json.py</code>
</td>
<td>
يحافظ على أمر تشغيل سابق عبر إعادة تصدير وظائف التنفيذ من وحدتها الحالية. وجوده لا يعني وجود خوارزمية مستقلة.
</td>
<td>
<pre>—</pre>
</td>
<td>
مشترك وأدوات
<br>
واجهة قديمة مدعومة أو تحليل مصدر سابق
</td>
<td>
<a href="data/xml_spreadsheet.md">شرح التبعية</a>
<br>
<code>src/data/xml_spreadsheet.py</code>
<br>
<a href="data/xml_to_json.md">شرح التبعية</a>
<br>
<code>src/data/xml_to_json.py</code>
</td>
<td>
<a href="xml_2_json.md">فتح شرح الملف</a>
</td>
</tr>
</tbody>
</table>

## ملفات الاختبارات والمساعدة

كل ملف أدناه له قسم في الفهرس يحصر أسماء الاختبارات الفعلية وروابط الوحدات المستوردة. ارتباط الاستيراد لا يدعي أن كل اختبار في الملف يفحص كل وحدة.

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
المسؤولية والعدد الثابت
</th>
<th>
أمثلة الأسماء العليا المهمة
</th>
<th>
مصادر مرتبطة
</th>
<th>
الفهرس
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>tests/__init__.py</code>
</td>
<td>
تعريف حزمة أو تجهيز عينات وأصول اصطناعية.
</td>
<td>
<pre>—</pre>
</td>
<td>
علاقة ديناميكية أو مساعدة؛ راجع الفهرس.
</td>
<td>
<a href="05_TEST_INDEX.md#test-1">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/api_fixtures.py</code>
</td>
<td>
تعريف حزمة أو تجهيز عينات وأصول اصطناعية.
</td>
<td>
<pre>—</pre>
</td>
<td>
<code>src.grade_scale</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-2">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/recommendation_fixtures.py</code>
</td>
<td>
تعريف حزمة أو تجهيز عينات وأصول اصطناعية.
</td>
<td>
<pre>—</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.features.temporal_features</code>
<br>
<code>src.grade_scale</code>
<br>
<code>src.recommendation</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-3">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_academic_calendar.py</code>
</td>
<td>
اختبارات؛ 4 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_regular_semesters_between
test_is_regular_semester
test_is_regular_semester_rejects_invalid_part_id</pre>
</td>
<td>
<code>src.data.academic_calendar</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-4">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_analyze_model_errors.py</code>
</td>
<td>
اختبارات؛ 11 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_modeling_does_not_import_evaluation
test_course_metrics
test_plan_metrics_previous_gpa_coverage_and_boundaries</pre>
</td>
<td>
<code>src.evaluation</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-5">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_api_academic_semantics.py</code>
</td>
<td>
اختبارات؛ 23 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_official_beginning_total_supplies_gpa_denominator_and_existing_feature
test_official_beginning_total_preserves_training_feature_definition
test_official_total_rejects_conflicting_sourced_supplement</pre>
</td>
<td>
<code>src.api.courses_adapter</code>
<br>
<code>src.api.settings</code>
<br>
<code>src.api.student_adapter</code>
<br>
<code>src.features.temporal_features</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-6">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_api_adapters.py</code>
</td>
<td>
اختبارات؛ 17 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_complete_student_uses_previous_gpa_and_explicit_denominator
test_actual_sanitized_student_reports_missing_diploma_and_denominator
test_independent_source_bindings_reject_wrong_identity</pre>
</td>
<td>
علاقة ديناميكية أو مساعدة؛ راجع الفهرس.
</td>
<td>
<a href="05_TEST_INDEX.md#test-7">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_api_backend_client.py</code>
</td>
<td>
اختبارات؛ 10 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_php_push_remains_default_and_pull_requires_explicit_configuration
test_environment_urls_timeout_and_courses_parameters
test_unsafe_endpoint_configuration_is_rejected</pre>
</td>
<td>
<code>src.api.settings</code>
<br>
<code>src.api.validation</code>
<br>
<code>src.api.backend_client</code>
<br>
<code>src.api</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-8">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_api_core_extensions.py</code>
</td>
<td>
اختبارات؛ 6 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_requirement_groups_do_not_merge_by_model_category
test_max_new_courses_is_an_optional_plan_constraint
test_exact_history_selection_and_explicit_backtesting</pre>
</td>
<td>
<code>src.features</code>
<br>
<code>src.recommendation.constraints</code>
<br>
<code>src.recommendation.history_update</code>
<br>
<code>src.recommendation.two_stage_engine</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-9">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_api_cumulative_integration.py</code>
</td>
<td>
اختبارات؛ 6 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_http_migration_manual_auto_rollback_and_existing_pareto_contract
test_missing_artifacts_block_migration_but_http_validation_remains_available
test_specialty_feature_requirement_rejects_update_before_publication</pre>
</td>
<td>
<code>src.api.app</code>
<br>
<code>src.api.service</code>
<br>
<code>src.api.settings</code>
<br>
<code>src.api.validation</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-10">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_api_history_admin.py</code>
</td>
<td>
اختبارات؛ 7 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_admin_status_and_durable_mode_workflow
test_service_credentials_cannot_access_administration
test_manual_preview_commit_and_activation_are_separate</pre>
</td>
<td>
<code>src.api.service</code>
<br>
<code>src.api.settings</code>
<br>
<code>src.api.app</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-11">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_api_http.py</code>
</td>
<td>
اختبارات؛ 16 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_http_health_and_validators_survive_unready_models_and_history
test_http_context_conflicts_make_zero_engine_calls
test_missing_courses_context_and_payload_identity_conflict_stop_inference</pre>
</td>
<td>
علاقة ديناميكية أو مساعدة؛ راجع الفهرس.
</td>
<td>
<a href="05_TEST_INDEX.md#test-12">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_api_integration.py</code>
</td>
<td>
اختبارات؛ 11 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_api_calls_actual_core_with_33_and_47_features_and_group_caps
test_original_gpa_calculation_and_helper_are_identical_on_full_schema
test_all_history_identity_rows_checked_even_when_first_schema_incomplete</pre>
</td>
<td>
<code>src.api.service</code>
<br>
<code>src.api.settings</code>
<br>
<code>src.api.validation</code>
<br>
<code>src.features.temporal_features</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-13">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_attempt_number_experiment.py</code>
</td>
<td>
اختبارات؛ 4 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_transform_keeps_other_columns_order_categories_and_input
test_unknown_or_invalid_attempt_cannot_become_first_attempt
test_row_fingerprint_detects_order_and_membership_changes</pre>
</td>
<td>
<code>src.experiments.attempt_number_core</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-14">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_balance_policy.py</code>
</td>
<td>
اختبارات؛ 14 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_exact_policy_is_versioned_and_has_no_new_quota
test_separate_credit_denominators_and_penalties
test_exact_band_boundaries_have_zero_distance</pre>
</td>
<td>
<code>src.recommendation.balance_policy</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-15">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_build_registration_roster.py</code>
</td>
<td>
اختبارات؛ 4 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_build_registration_roster_keeps_only_registered_or_enrolled
test_build_registration_roster_joins_exact_status_removes_outliers_and_keeps_plan_gaps
test_main_writes_full_train_and_test_rosters</pre>
</td>
<td>
<code>src.data.build_registration_roster</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-16">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_build_student_course_enriched.py</code>
</td>
<td>
اختبارات؛ 2 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_main_builds_status_inner_join_and_auditable_plan_left_join
test_main_rejects_many_to_many_enrichment_sources</pre>
</td>
<td>
<code>src.data.build_student_course_enriched</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-17">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_clean_degree_course.py</code>
</td>
<td>
اختبارات؛ 3 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_clean_degree_course_normalizes_contract_and_stable_order
test_clean_degree_course_rejects_missing_required_columns
test_main_writes_the_clean_degree_course_artifact</pre>
</td>
<td>
<code>src.data.clean_degree_course</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-18">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_clean_outliers.py</code>
</td>
<td>
اختبارات؛ 11 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_validate_columns_names_every_missing_requirement
test_summarize_rule_aggregates_repeated_triggers_per_student
test_build_outlier_audit_applies_each_status_upper_limit</pre>
</td>
<td>
<code>src.data.clean_outliers</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-19">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_clean_student_course.py</code>
</td>
<td>
اختبارات؛ 21 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_clean_student_course_basic_contract_and_input_immutability
test_registration_status_is_normalized_before_filtering
test_finish_status_map_normalizes_and_maps_current_codes</pre>
</td>
<td>
<code>src.data.clean_student_course</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-20">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_clean_student_diploma.py</code>
</td>
<td>
اختبارات؛ 5 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_clean_student_diploma_groups_rare_types_and_fills_gpa
test_clean_student_diploma_rejects_broken_input_contract
test_merge_student_course_with_diploma_preserves_unmatched_courses</pre>
</td>
<td>
<code>src.data.clean_student_diploma</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-21">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_clean_student_status.py</code>
</td>
<td>
اختبارات؛ 13 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_add_enrollment_features_tracks_only_observed_history
test_observed_gap_counts_regular_semesters_between_enrollments
test_optional_non_enrollment_does_not_increase_gap</pre>
</td>
<td>
<code>src.data.clean_student_status</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-22">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_clean_utils.py</code>
</td>
<td>
اختبارات؛ 7 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_clean_column_names_normalizes_whitespace_without_mutating_input
test_clean_id_preserves_meaningful_dots_and_normalizes_nulls
test_clean_id_columns_cleans_multiple_selected_columns_and_copies_input</pre>
</td>
<td>
<code>src.data.cleaning_utils</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-23">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_corrected_phase6_evaluation.py</code>
</td>
<td>
اختبارات؛ 16 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_recall_has_independent_top_k_denominator_and_explicit_lost_ids
test_no_solution_recall_is_not_reported_as_perfect_retention
test_recall_at50_cannot_be_inflated_by_larger_shortlist</pre>
</td>
<td>
<code>src.recommendation.balance_policy</code>
<br>
<code>src.recommendation.ranking</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-24">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_corrected_phase6_rerun.py</code>
</td>
<td>
اختبارات؛ 8 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_every_nonsearch_row_is_invalidated_including_timeout_and_duplicate_batch
test_jobs_preserve_old_independent_choices_and_each_observations_deadline
test_completed_replacements_must_match_job_and_prove_supported_grade_version</pre>
</td>
<td>
علاقة ديناميكية أو مساعدة؛ راجع الفهرس.
</td>
<td>
<a href="05_TEST_INDEX.md#test-25">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_course_only_recommendation.py</code>
</td>
<td>
اختبارات؛ 12 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_course_matrix_does_not_need_plan_context_and_retains_unknown_categories
test_exact_search_uses_every_candidate_and_risk_then_course_order_for_ties
test_fractional_credit_search_and_zero_credit_optional_courses</pre>
</td>
<td>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-26">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_cumulative_history.py</code>
</td>
<td>
اختبارات؛ 25 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_lazy_defaults_and_persistent_modes
test_approved_initialization_preserves_full_weighted_history_and_source
test_initialization_requires_exact_approved_cumulative_prefix</pre>
</td>
<td>
<code>src.features.frozen_history</code>
<br>
<code>src.features.temporal_features</code>
<br>
<code>src.recommendation.history_update</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-27">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_degree_points_config.py</code>
</td>
<td>
اختبارات؛ 2 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_experiment_configuration_preserves_folds_and_variants
test_experiment_modules_import_without_running_experiment</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.experiments.degree_points_config</code>
<br>
<code>src.experiments</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-28">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_degree_points_experiment.py</code>
</td>
<td>
اختبارات؛ 5 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_changing_current_or_future_labels_changes_no_earlier_features
test_frozen_history_rejects_overlap_with_test_semester
test_current_part_does_not_enter_its_own_specialty_history</pre>
</td>
<td>
<code>src.experiments.modeling</code>
<br>
<code>src.experiments.specialty_history</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-29">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_evaluate_plan_gpa.py</code>
</td>
<td>
اختبارات؛ 5 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_predict_course_points_preserves_audit_and_quality_points
test_aggregate_plan_gpa_uses_student_degree_part_and_credit_weighting
test_summarize_plan_errors_includes_threshold_boundaries</pre>
</td>
<td>
<code>src.evaluation</code>
<br>
<code>src.grade_scale</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-30">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_evaluation_v2_io.py</code>
</td>
<td>
اختبارات؛ 4 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_plan_evaluation_reads_and_writes_v2_with_shared_grade_scale
test_error_analysis_uses_v2_in_historical_holdout_and_shap_paths
test_missing_v2_input_fails_without_v1_fallback_or_output</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.evaluation</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-31">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_experiment_io.py</code>
</td>
<td>
اختبارات؛ 5 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_signature_hashes_current_dependencies_deterministically
test_validation_cache_reuses_only_matching_signature
test_metadata_retains_protocol_and_artifact_contract</pre>
</td>
<td>
<code>src.experiments</code>
<br>
<code>src.experiments.degree_points_config</code>
<br>
<code>src.experiments.experiment_io</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-32">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_experiments_v2_io.py</code>
</td>
<td>
اختبارات؛ 3 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_coordinator_uses_v2_baseline_cache_outputs_and_metadata_candidate
test_missing_v2_input_fails_without_using_v1
test_path_constants_are_v2_and_grade_scale_is_shared</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.experiments</code>
<br>
<code>src.experiments.degree_points_config</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-33">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_feature_contract_responsibilities.py</code>
</td>
<td>
اختبارات؛ 3 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_saved_training_levels_keep_unseen_serving_values_unknown
test_base_matrix_preserves_schema_and_category_handling
test_modeling_targets_and_training_weights_preserve_values</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.features</code>
<br>
<code>src.modeling</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-34">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_feature_pipeline.py</code>
</td>
<td>
اختبارات؛ 4 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_poisoning_current_and_future_outcomes_leaves_all_features_unchanged
test_feature_version_survives_parquet_projection_and_rejects_old_models
test_validation_cache_rejects_old_or_different_feature_data</pre>
</td>
<td>
<code>src.features.build_temporal_features</code>
<br>
<code>src.features.feature_contract</code>
<br>
<code>src.experiments.degree_points</code>
<br>
<code>src.experiments.experiment_io</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-35">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_filter_common_students.py</code>
</td>
<td>
اختبارات؛ 4 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_keeps_only_students_present_in_both_tables
test_keeps_all_rows_for_common_student_despite_different_parts_and_degrees
test_does_not_modify_inputs_in_place</pre>
</td>
<td>
<code>src.data.filter_common_students</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-36">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_frozen_history.py</code>
</td>
<td>
اختبارات؛ 13 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_new_version_preserves_original_hashes_and_values
test_target_and_future_outcomes_cannot_enter_prefix
test_prefix_fingerprint_survives_row_order_and_future_dtype_change</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.experiments.specialty_history</code>
<br>
<code>src.features.frozen_history</code>
<br>
<code>src.paths</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-37">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_frozen_history_v2.py</code>
</td>
<td>
اختبارات؛ 10 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_v2_load_default_uses_isolated_root_and_missing_v2_never_falls_back
test_v2_rejects_unversioned_or_wrong_version_bundle
test_v2_rejects_specialty_artifacts_without_opening_them</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.features</code>
<br>
<code>src.features.feature_contract</code>
<br>
<code>src.features.frozen_history</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-38">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_grade_scale.py</code>
</td>
<td>
اختبارات؛ 9 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_supported_versions_convert_passing_marks
test_supported_versions_keep_failing_marks_at_zero_and_f
test_convert_rejects_invalid_version_even_in_a_mixed_batch</pre>
</td>
<td>
<code>src.grade_scale</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-39">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_history_update.py</code>
</td>
<td>
اختبارات؛ 24 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_aggregate_addition_preserves_weighted_prefix_and_matches_raw_oracle
test_delta_identity_is_canonical_and_state_bytes_are_deterministic
test_invalid_aggregate_is_rejected_without_mutating_prefix</pre>
</td>
<td>
<code>src.features</code>
<br>
<code>src.features.temporal_features</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-40">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_local_recommendation.py</code>
</td>
<td>
اختبارات؛ 16 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_exhaustive_oracle_fractional_zero_and_variable_count
test_single_value_is_exact_and_range_keeps_both_bounds
test_range_uses_upper_exact_with_decimal_zero_and_variable_count</pre>
</td>
<td>
<code>src.recommendation</code>
<br>
<code>src.recommendation.inputs</code>
<br>
<code>src.recommendation.output</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-41">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_main_runner.py</code>
</td>
<td>
اختبارات؛ 10 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_registry_has_dependency_order_and_named_optional_steps
test_list_displays_standard_and_optional_work_without_execution
test_all_standard_stages_are_v2_and_request_workflows_keep_their_labels</pre>
</td>
<td>
<code>src</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-42">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_model_artifact_isolation.py</code>
</td>
<td>
اختبارات؛ 6 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_artifact_namespaces
test_dependency_checker_detects_forbidden_imports_and_paths
test_dependency_checker_allows_official_and_local_imports</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.experiments</code>
<br>
<code>src.experiments.degree_points_config</code>
<br>
<code>src.grade_scale</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-43">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_modeling_v2_io.py</code>
</td>
<td>
اختبارات؛ 4 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_modeling_io_constants_resolve_to_isolated_v2_files
test_main_reads_v2_and_writes_only_v2_with_correct_metadata
test_missing_v2_input_fails_without_reading_v1_or_writing_models</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.features.feature_contract</code>
<br>
<code>src.modeling</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-44">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_plan_gpa_evaluation.py</code>
</td>
<td>
اختبارات؛ 1 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_plan_gpa_uses_credit_weighted_points</pre>
</td>
<td>
<code>src.evaluation.evaluate_plan_gpa</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-45">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_previous_course_status_data.py</code>
</td>
<td>
اختبارات؛ 1 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_roster_is_chronology_and_w_is_not_a_zero_mark_fail</pre>
</td>
<td>
<code>src.experiments.previous_course_status_data</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-46">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_previous_course_status_evaluation.py</code>
</td>
<td>
اختبارات؛ 1 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_status_slices_measure_retake_errors_without_small_group_pr_auc</pre>
</td>
<td>
<code>src.experiments.previous_course_status_evaluation</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-47">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_previous_course_status_inference.py</code>
</td>
<td>
اختبارات؛ 6 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_course_comparison_joins_by_course_identity_and_keeps_status
test_course_comparison_rejects_mismatched_candidate_rows
test_unresolved_prior_attempt_is_unknown_in_serving_rows</pre>
</td>
<td>
علاقة ديناميكية أو مساعدة؛ راجع الفهرس.
</td>
<td>
<a href="05_TEST_INDEX.md#test-48">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_previous_course_status_training.py</code>
</td>
<td>
اختبارات؛ 4 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_two_contracts_append_one_categorical_without_changing_base
test_augmented_matrix_keeps_order_and_maps_unseen_status
test_augmented_folds_keep_official_cutoffs_and_fit_weights</pre>
</td>
<td>
<code>src.experiments.course_only_core</code>
<br>
<code>src.experiments.previous_course_status_training</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-49">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_project_status.py</code>
</td>
<td>
اختبارات؛ 1 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_stage_paths_order_and_version_boundary</pre>
</td>
<td>
<code>src</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-50">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_projected_recommendation.py</code>
</td>
<td>
اختبارات؛ 10 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_additive_example_and_zero_prior_credits
test_invalid_or_unknown_denominators_are_rejected
test_larger_load_can_win_despite_lower_semester_gpa</pre>
</td>
<td>
<code>src.recommendation</code>
<br>
<code>src.recommendation.inputs</code>
<br>
<code>src.recommendation.output</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-51">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_ranking_strategies.py</code>
</td>
<td>
اختبارات؛ 15 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_identity_is_canonical_sha256_and_includes_optional_zero_course
test_invalid_plan_identity_is_rejected
test_balance_changes_rank_despite_different_gpa_and_failures</pre>
</td>
<td>
<code>src.recommendation.ranking</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-52">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_recommendation.py</code>
</td>
<td>
اختبارات؛ 3 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_predicted_mark_uses_official_pass_band_thresholds
test_exact_credits_allow_different_course_counts
test_ranking_uses_gpa_then_failure_without_risk_exclusion</pre>
</td>
<td>
<code>src.recommendation</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-53">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_recommendation_dependency_direction.py</code>
</td>
<td>
اختبارات؛ 3 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_upstream_packages_do_not_import_recommendation
test_production_packages_do_not_import_project_runner
test_course_plan_change_diagnostic_uses_package_location</pre>
</td>
<td>
علاقة ديناميكية أو مساعدة؛ راجع الفهرس.
</td>
<td>
<a href="05_TEST_INDEX.md#test-54">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_recommendation_inputs_v2.py</code>
</td>
<td>
اختبارات؛ 8 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_local_loader_reads_only_cleaned_v2_and_preserves_history
test_local_missing_v2_fails_without_legacy_fallback
test_local_supplied_snapshot_reads_only_v2_catalog_and_attempts</pre>
</td>
<td>
<code>src.recommendation</code>
<br>
<code>src.evaluation</code>
<br>
<code>src.features.frozen_history</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-55">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_recommendation_package.py</code>
</td>
<td>
اختبارات؛ 1 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_public_and_component_imports_do_not_load_models</pre>
</td>
<td>
علاقة ديناميكية أو مساعدة؛ راجع الفهرس.
</td>
<td>
<a href="05_TEST_INDEX.md#test-56">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_recommendation_v2.py</code>
</td>
<td>
اختبارات؛ 13 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_loader_reads_only_official_v2_artifacts
test_missing_official_artifact_never_falls_back
test_loader_rejects_incompatible_official_contract</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.features.feature_contract</code>
<br>
<code>src.recommendation</code>
<br>
<code>src.recommendation.output</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-57">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_repeat_withdrawal_balance.py</code>
</td>
<td>
اختبارات؛ 18 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_failed_repeated_and_not_repeated
test_withdrawn_repeated_and_not_repeated
test_latest_previous_attempt_wins</pre>
</td>
<td>
<code>src.diagnostics.repeat_withdrawal_report</code>
<br>
<code>src.diagnostics.analyze_repeat_withdrawal_balance</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-58">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_specialty_history_sequential.py</code>
</td>
<td>
اختبارات؛ 6 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_20251_excludes_current_and_future_and_20252_includes_finalized_20251
test_generalized_parts_restore_unsorted_rows_with_duplicate_indices
test_new_degree_enters_both_hierarchy_levels_only_in_later_parts</pre>
</td>
<td>
<code>src.experiments.specialty_history</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-59">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_student_course_status.py</code>
</td>
<td>
اختبارات؛ 9 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_mark_boundaries_use_previous_attempt_only
test_first_attempt_ignores_current_and_future_outcomes
test_latest_prior_attempt_wins_even_when_history_is_unsorted</pre>
</td>
<td>
<code>src.features.student_course_status</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-60">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_temporal_features.py</code>
</td>
<td>
اختبارات؛ 17 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_fallback_uses_the_most_specific_available_history
test_roster_only_courses_never_become_finalized_history
test_consecutive_test_parts_roll_forward_only_after_each_outcome</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.features.temporal_features</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-61">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_train_models.py</code>
</td>
<td>
اختبارات؛ 11 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_regression_metrics_known_errors_and_inclusive_boundaries
test_classification_metrics_known_ranking_and_probabilities
test_classification_metrics_clips_endpoint_probabilities</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.modeling</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-62">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_training_config.py</code>
</td>
<td>
اختبارات؛ 3 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_target_definitions
test_training_weights_year_boundary
test_training_weights_preserves_index_and_numeric_coercion</pre>
</td>
<td>
<code>src.modeling.training_config</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-63">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_two_stage_activation.py</code>
</td>
<td>
اختبارات؛ 11 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_verified_artifact_loader_accepts_complete_human_approval
test_incomplete_or_inconsistent_approval_still_refuses_assets
test_approval_does_not_bypass_existing_feature_or_model_hash_checks</pre>
</td>
<td>
<code>src.recommendation</code>
<br>
<code>src</code>
<br>
<code>src.recommendation.ranking</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-64">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_two_stage_artifacts.py</code>
</td>
<td>
اختبارات؛ 27 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_stage_contracts_derive_33_and_47_from_the_official_order
test_promotion_copies_exact_bytes_and_archives_original_provenance
test_promoted_pair_produces_the_same_synthetic_predictions</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.features.temporal_features</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-65">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_two_stage_benchmark.py</code>
</td>
<td>
اختبارات؛ 20 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_search_counter_counts_actual_recursion_and_preserves_order
test_feasible_counter_keeps_zero_options_and_filters_complete_plans
test_scenarios_cover_sizes_fractions_zero_ties_constraints_and_no_solution</pre>
</td>
<td>
<code>src.recommendation.constraints</code>
<br>
<code>src.recommendation.plan_generation</code>
<br>
<code>src.recommendation.inputs</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-66">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_two_stage_constraints.py</code>
</td>
<td>
اختبارات؛ 19 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_requirement_alias_and_adjustments_preserve_fractional_remaining
test_requirement_without_adjustments_defaults_to_zero_adjustments
test_overcompleted_requirement_has_zero_remaining</pre>
</td>
<td>
<code>src.recommendation</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-67">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_two_stage_engine.py</code>
</td>
<td>
اختبارات؛ 33 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_two_stage_orchestration_has_an_explicit_evaluation_entrypoint
test_production_activation_refuses_unapproved_independent_strategies
test_evaluation_factory_loads_assets_and_history_once_for_reused_requests</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.features.temporal_features</code>
<br>
<code>src.recommendation.history_update</code>
<br>
<code>src.recommendation.inputs</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-68">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_two_stage_evaluation.py</code>
</td>
<td>
اختبارات؛ 9 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_complete_synthetic_evaluation_has_all_feasible_plans
test_real_shortlist_matches_independent_complete_subset_and_ranking_oracle
test_all_four_cross_stage_results_match_independent_final_oracle</pre>
</td>
<td>
<code>src.recommendation.ranking</code>
<br>
<code>src.recommendation.shortlist</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-69">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_two_stage_matrix.py</code>
</td>
<td>
اختبارات؛ 6 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_default_matrix_matches_legacy_47_exactly_without_mutating_inputs
test_stage1_matches_legacy_slice_without_requiring_plan_context
test_explicit_feature_order_coerces_only_the_requested_columns</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.recommendation.two_stage_artifacts</code>
<br>
<code>src.experiments.course_only_core</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-70">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_two_stage_payloads.py</code>
</td>
<td>
اختبارات؛ 16 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_ready_values_are_preserved_without_io_or_candidate_cap_filtering
test_missing_trend_stays_missing
test_only_explicit_eligibility_rejection_removes_candidates</pre>
</td>
<td>
<code>src.recommendation</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-71">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_two_stage_shortlist.py</code>
</td>
<td>
اختبارات؛ 7 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_complete_feasibility_before_shortlist_fractional_and_optional_zero
test_no_lower_credit_fallback_and_no_prefiltering_of_failed_availability
test_shared_scoring_rejects_nonfinite_or_wrong_shape_before_clip</pre>
</td>
<td>
<code>src.recommendation.constraints</code>
<br>
<code>src.recommendation.ranking</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-72">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_v2_paths.py</code>
</td>
<td>
اختبارات؛ 3 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_versioned_path_preserves_parent_and_extension
test_versioned_path_supports_artifact_extensions
test_v2_artifacts_are_separate_from_originals</pre>
</td>
<td>
<code>src</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-73">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_v2_pipeline.py</code>
</td>
<td>
اختبارات؛ 1 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_full_v2_chain_uses_only_new_intermediates_and_preserves_v1</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.features.temporal_features</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-74">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/test_xml_package.py</code>
</td>
<td>
اختبارات؛ 5 تعريفًا اسميًا قبل التوليد بالمعاملات.
</td>
<td>
<pre>test_xml_module_imports_do_not_create_directories
test_xml_converter_and_evaluator_keep_parsing_behavior
test_xml_evaluation_root_module_still_exposes_cli_help</pre>
</td>
<td>
<code>src.data</code>
<br>
<code>src.evaluation.evaluate_xml_recommendations</code>
<br>
<code>src</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-75">قسم ملف الاختبار</a>
</td>
</tr>
<tr>
<td>
<code>tests/two_stage_fixtures.py</code>
</td>
<td>
تعريف حزمة أو تجهيز عينات وأصول اصطناعية.
</td>
<td>
<pre>—</pre>
</td>
<td>
<code>src.features.feature_contract</code>
<br>
<code>src.features.frozen_history</code>
<br>
<code>src.features.temporal_features</code>
<br>
<code>src.recommendation.history_update</code>
</td>
<td>
<a href="05_TEST_INDEX.md#test-76">قسم ملف الاختبار</a>
</td>
</tr>
</tbody>
</table>

## أدوات التنفيذ والبحث خارج المصدر

لأدوات الترقية والبناء والقياس والتتبع آثار كتابة أو توقع أو تدريب؛ لم تُشغّل. ملفات المساعدة التي لا تملك حارس تشغيل قد تنفذ عملًا عند الاستيراد.

<table>
<thead>
<tr>
<th>
المسار
</th>
<th>
الدور
</th>
<th>
الدوال العليا
</th>
<th>
مصادر مهمة
</th>
<th>
قسم الشرح
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>scripts/benchmark_two_stage.py</code>
</td>
<td>
تقييم أو قياس أو فحص جامعي محلي.
</td>
<td>
<pre>synthetic_case
synthetic_history_manager
supported_synthetic_grade_version
_means
_comparison
_final_metrics
measure_case
timing_class
benchmark_jobs
censored_result
run_worker
_write_worker_json
build_report
save_report
main</pre>
</td>
<td>
<code>src.features.temporal_features</code>
<br>
<code>src.recommendation.benchmark</code>
<br>
<code>src.recommendation.constraints</code>
<br>
<code>src.recommendation.history_update</code>
<br>
<code>src.recommendation.inputs</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-1">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/evaluate_corrected_phase6.py</code>
</td>
<td>
تقييم أو قياس أو فحص جامعي محلي.
</td>
<td>
<pre>_hash
corrected_fixture
recall_evidence
_tie_signature
_tie_recall
distributions
_top_comparison
compare_fixed_final
tradeoff_examples
_collect
evaluate_fixture
summarize_evidence
build_report
main</pre>
</td>
<td>
<code>src.data.cleaning_utils</code>
<br>
<code>src.features.temporal_features</code>
<br>
<code>src.recommendation.history_update</code>
<br>
<code>src.recommendation.inputs</code>
<br>
<code>src.recommendation.plan_scoring</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-2">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/evaluate_two_stage_ranking.py</code>
</td>
<td>
تقييم أو قياس أو فحص جامعي محلي.
</td>
<td>
<pre>synthetic_fixture
_metrics
_change
_diagnostic_stage2
_top_comparison
evaluate_synthetic
_mix_courses
_synthetic_eligible
evaluate_historical_policy
evaluate_sensitivities
evaluate_mixed_scope
build_evaluation_report
save_report
main</pre>
</td>
<td>
<code>src.recommendation.balance_policy</code>
<br>
<code>src.recommendation.constraints</code>
<br>
<code>src.recommendation.ranking</code>
<br>
<code>src.recommendation.shortlist</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-3">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/attempt_number_experiment.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>source_signature
save_provenance
main</pre>
</td>
<td>
<code>src.experiments.attempt_number_analysis</code>
<br>
<code>src.experiments.attempt_number_core</code>
<br>
<code>src.experiments.attempt_number_report</code>
<br>
<code>src.experiments.attempt_number_training</code>
<br>
<code>src.experiments.attempt_number_validation</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-4">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/attempt_number_recommendation.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>select_cases
run_recommendations</pre>
</td>
<td>
<code>src.data.cleaning_utils</code>
<br>
<code>src.experiments.attempt_number_analysis</code>
<br>
<code>src.experiments.attempt_number_core</code>
<br>
<code>src.features.feature_contract</code>
<br>
<code>src.features.temporal_features</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-5">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/attempt_number_removal_recheck.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>families
evaluate
run</pre>
</td>
<td>
<code>src.experiments</code>
<br>
<code>src.experiments.attempt_number_training</code>
<br>
<code>src.features.feature_contract</code>
<br>
<code>src.features.frozen_history</code>
<br>
<code>src.grade_scale</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-6">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/complete_registration.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>run</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.grade_scale</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-7">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/coverage.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>run</pre>
</td>
<td>
<code>src</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-8">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/data_analysis.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>save
numeric
window
stats
corr
pair_stats
mapping
identity
table
main</pre>
</td>
<td>
أدوات مكتبة أو وحدات مساعدة محلية.
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-9">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/downstream.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>validated_model
candidate_rows
run</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.features.frozen_history</code>
<br>
<code>src.features.temporal_features</code>
<br>
<code>src.grade_scale</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-10">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/evidence/executed_workflow.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>write_json
feature_subset
temporal_partition
configuration_signature
validate_signature
protected_manifest
verify_protected
load_train
specs
matrix
aggregate_points
predict
evaluate
fit_model
inner_selection
gain_rows
permutation
group_metrics
run</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.experiments.attempt_number_core</code>
<br>
<code>src.experiments.specialty_history</code>
<br>
<code>src.features.feature_contract</code>
<br>
<code>src.features.frozen_history</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-11">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/report.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>table
deltas
build</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.features.frozen_history</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-12">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/safeguards.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>sign_record
authenticate_record
authenticate_selection
publish_completion</pre>
</td>
<td>
أدوات مكتبة أو وحدات مساعدة محلية.
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-13">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/test_downstream.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>pool
test_exact_candidates_recompute_plan_and_peer_context
test_candidate_choice_and_context_are_outcome_independent</pre>
</td>
<td>
<code>src.features.temporal_features</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-14">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/test_safeguards.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>test_tuning_record_rejects_changed_rounds_and_unsigned_cache
test_failure_to_verify_cannot_leave_complete
test_complete_is_published_only_after_verification
test_tuning_selection_accepts_only_matching_context
test_signed_tuning_selection_cannot_be_transplanted</pre>
</td>
<td>
أدوات مكتبة أو وحدات مساعدة محلية.
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-15">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/test_workflow.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>test_subsets_preserve_other_features_and_order
test_inner_partition_never_sees_outer_or_holdout
test_plan_gpa_weights_credits_and_excludes_zero_denominator
test_signature_rejects_different_features_and_parameters
test_experiment_names_cannot_escape_isolated_roots
test_named_experiment_uses_both_isolated_roots</pre>
</td>
<td>
أدوات مكتبة أو وحدات مساعدة محلية.
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-16">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/verify_artifacts.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>run</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.features.frozen_history</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-17">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/experiments/student_progress_20261010/workflow.py</code>
</td>
<td>
بحث أو مساعدة أو اختبار تجربة معزولة.
</td>
<td>
<pre>write_json
feature_subset
temporal_partition
configuration_signature
validate_signature
experiment_directories
implementation_signature
protected_manifest
verify_protected
load_train
specs
matrix
aggregate_points
predict
evaluate
fit_model
selection_context
inner_selection
gain_rows
permutation
group_metrics
run</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.experiments.attempt_number_core</code>
<br>
<code>src.experiments.specialty_history</code>
<br>
<code>src.features.feature_contract</code>
<br>
<code>src.features.frozen_history</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-18">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/promote_shortlist_artifacts.py</code>
</td>
<td>
ترقية أصول معتمدة دون تدريب.
</td>
<td>
<pre>verify_training_sources
build_promotion_manifest
promote_shortlist_artifacts</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.features.frozen_history</code>
<br>
<code>src.recommendation.two_stage_artifacts</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-19">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/rebuild_common_students_v2.py</code>
</td>
<td>
بناء أو تحقق ترحيل له آثار كتابة.
</td>
<td>
<pre>digest
compare
main</pre>
</td>
<td>
<code>src</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-20">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/rerun_corrected_phase6.py</code>
</td>
<td>
تقييم أو قياس أو فحص جامعي محلي.
</td>
<td>
<pre>classify_old_evidence
corrected_jobs
validate_replacement
assemble_corrected_results
archive_old_evidence
_hash_file
protected_inventory
run_corrected_benchmarks
main</pre>
</td>
<td>
أدوات مكتبة أو وحدات مساعدة محلية.
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-21">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/scan_student_over_polict.py</code>
</td>
<td>
تقييم أو قياس أو فحص جامعي محلي.
</td>
<td>
<pre>cohort_counts
main</pre>
</td>
<td>
<code>src.data.cleaning_utils</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-22">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/scan_under_12_after_status_change.py</code>
</td>
<td>
تقييم أو قياس أو فحص جامعي محلي.
</td>
<td>
<pre>count
main</pre>
</td>
<td>
<code>src.data.cleaning_utils</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-23">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/verify_cleaning_policy_v2.py</code>
</td>
<td>
بناء أو تحقق ترحيل له آثار كتابة.
</td>
<td>
<pre>audit_policy
compare_tables
verify_policy_only
main</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.data.cleaning_utils</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-24">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>scripts/verify_data_features_v2.py</code>
</td>
<td>
بناء أو تحقق ترحيل له آثار كتابة.
</td>
<td>
<pre>signature
describe
compare
original_cleaner
main</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.data.clean_student_diploma</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-25">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>debugging/explain_recommendation.py</code>
</td>
<td>
تشخيص أو تتبع أو عرض أدلة؛ راجع آثار التنفيذ.
</td>
<td>
<pre>check
records
save
read_export
summarize_all
course_math
collect_term
main</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.data.clean_student_status</code>
<br>
<code>src.experiments.modeling</code>
<br>
<code>src.experiments.specialty_history</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-26">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>debugging/pipeline_audit.py</code>
</td>
<td>
تشخيص أو تتبع أو عرض أدلة؛ راجع آثار التنفيذ.
</td>
<td>
<pre>records
save
progress
metrics</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.data.clean_outliers</code>
<br>
<code>src.data.clean_student_status</code>
<br>
<code>src.data.cleaning_utils</code>
<br>
<code>src.experiments.modeling</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-27">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>debugging/pipeline_audit_details.py</code>
</td>
<td>
تشخيص أو تتبع أو عرض أدلة؛ راجع آثار التنفيذ.
</td>
<td>
<pre>records
save</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.data.clean_outliers</code>
<br>
<code>src.data.cleaning_utils</code>
<br>
<code>src.experiments.modeling</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-28">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>debugging/render_recommendation_explanation.py</code>
</td>
<td>
تشخيص أو تتبع أو عرض أدلة؛ راجع آثار التنفيذ.
</td>
<td>
<pre>fmt
p
formula
table
code
group_name
context_math
sections
main</pre>
</td>
<td>
<code>src.experiments.specialty_history</code>
<br>
<code>src.features.temporal_features</code>
<br>
<code>src.recommendation</code>
<br>
<code>src.recommendation.inputs</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-29">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>debugging/run_trace.py</code>
</td>
<td>
تشخيص أو تتبع أو عرض أدلة؛ راجع آثار التنفيذ.
</td>
<td>
<pre>main</pre>
</td>
<td>
أدوات مكتبة أو وحدات مساعدة محلية.
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-30">شرح الأداة</a>
</td>
</tr>
<tr>
<td>
<code>debugging/trace_student_29485_20251.py</code>
</td>
<td>
تشخيص أو تتبع أو عرض أدلة؛ راجع آثار التنفيذ.
</td>
<td>
<pre>check
show
save_json
records
source
read_export
capture_score_rows
family</pre>
</td>
<td>
<code>src</code>
<br>
<code>src.data.clean_student_status</code>
<br>
<code>src.experiments.modeling</code>
<br>
<code>src.experiments.specialty_history</code>
<br>
<code>src.features.feature_contract</code>
</td>
<td>
<a href="06_ENTRY_POINTS_AND_TOOLS.md#tool-31">شرح الأداة</a>
</td>
</tr>
</tbody>
</table>

## ما الذي لم يصنف على أنه غير مستعمل؟

لا تكفي قلة المستوردين الداخليين للحكم: بعض الوحدات تسجلها أداة المنظم بالاسم النصي، وبعضها نقطة تنفيذ مباشرة، وبعض الاختبارات تستوردها ديناميكيًا. ملفات التوافق القديمة تفوض إلى وحدات حالية.

لم يثبت الفحص الثابت وجود ملف مصدر يمكن الجزم أنه غير مستعمل في جميع أوامر التشغيل والبيئات. تظهر حدود العلاقة عند كل صفحة بدل استنتاج غير مدعوم.

