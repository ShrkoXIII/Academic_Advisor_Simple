# المحرك المعتمد ذو المرحلتين

```text
src/recommendation/two_stage_engine.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

ينسق المحرك المرشحين والقيود والتاريخ ومودلات المرحلتين واختياري الترتيب المستقلين، ويحفظ مصدر القرار في البيانات الوصفية.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق التحقق والتوصية والإدارة](../api/service.md)
- [تصدير واجهات نواة التوصية](__init__.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [مكونات التوازن الناعم](balance_policy.md)
- [مجاميع الدفعات ومدير اللقطة](history_update.md)
- [عقود النواة والمدخلات المحلية](inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](plan_scoring.md)
- [الهوية والترتيب وجبهات المفاضلة](ranking.md)
- [التحقق من اعتماد سياسة الترتيب](ranking_policy.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](shortlist.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](two_stage_artifacts.md)

## ٣. المدخلات

غلاف نواة يحتوي لقطة طالب ومواد مطبّعة، وغلاف طلب بالهوية والساعات والسياسات. يحتاج أصولًا مطابقة ومدير تاريخ؛ عدد النتائج الافتراضي ثلاثة.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

الأنواع والبنى المستعملة في هذا الحد:

```text
student_payload: Mapping
request_payload: Mapping
top_k: int
history_as_of_part: optional academic part
```

## ٤. المخرجات

قاموس بالحالة والبيانات الوصفية وقائمة الخطط مع موادها وتوقعاتها. أفضل النتائج محسوبة داخل القائمة المختصرة، وليست ضمان أفضلية عالمية.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
recommend_from_payloads(...) -> dict
recommendations: list[dict]
metadata: dict
```

## ٥. الدوال والأصناف

الجدول يحصر جميع الدوال والأصناف المعرفة في المستوى الأعلى. عمود المستدعي يعتمد نداء رمز يمكن حله من الشفرة؛ الاستخدام عبر كائن محقون أو استيراد ديناميكي يُشرح في التسلسل، ولا يُنفى عند غياب رابط مباشر.

<table>
<thead>
<tr>
<th>
الدالة أو الصنف
</th>
<th>
الغرض
</th>
<th>
المدخل
</th>
<th>
المخرج أو تعبيره الفعلي
</th>
<th>
من يستدعيه
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>_json_value</code>
</td>
<td>
تهيئة ناتج النواة للتسلسل مع تحويل الفقدان.
</td>
<td>
<pre>_json_value(value)</pre>
</td>
<td>
<pre>{key: _json_value(item) for key, item in value.items()}</pre>
<pre>[_json_value(item) for item in value]</pre>
<pre>None</pre>
<pre>'0' if value == 0 else text</pre>
<pre>bool(value)</pre>
<pre>int(value)</pre>
<pre>float(value)</pre>
<pre>value</pre>
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>_json_value</code>
<br>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>_input_fingerprint</code>
<br>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.recommend_from_payloads</code>
</td>
</tr>
<tr>
<td>
<code>_input_fingerprint</code>
</td>
<td>
بصمة المدخل المعياري تشمل القيود المستخدمة.
</td>
<td>
<pre>_input_fingerprint(prepared, top_k)</pre>
</td>
<td>
<pre>sha256(canonical.encode('utf-8')).hexdigest()</pre>
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.recommend_from_payloads</code>
</td>
</tr>
<tr>
<td>
<code>TwoStagePlanRecommender</code>
</td>
<td>
المحرك المعتمد الذي ينفصل فيه توقع المادة عن توقع الخطط المختصرة.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="../api/service.md">صفحة المستدعي</a>
<br>
<code>ApiService._bind_history_manager</code>
<br>
<a href="../api/service.md">صفحة المستدعي</a>
<br>
<code>ApiService.initialize</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
TwoStagePlanRecommender.load
```

يحمل الأصول والسياسة المعتمدة والتاريخ؛ لا يرجع لمودل سابق عند الفشل.

خطوة 2:

```text
TwoStagePlanRecommender._ranking_metadata
```

يثبت اختياري ترتيب المرحلتين ويتأكد أنهما يطابقان الاعتماد المسجل.

خطوة 3:

```text
prepare_recommendation_payloads / FrozenHistoryManager.capture
```

يرفض المدخل غير الصالح قبل التوقع، ثم يثبت لقطة تاريخ واحدة والقطع الصحيح.

خطوة 4:

```text
TwoStagePlanRecommender._prepare_candidates
```

ينسخ ميزات الطالب إلى كل مادة ويضيف سبع ميزات تاريخ من النسخة المثبتة.

خطوة 5:

```text
score_course_rows / build_stage1_shortlist
```

يستعمل ثلاثة وثلاثين مدخلًا لكل مادة، يولّد جميع الخطط الممكنة تحت القيود، ويلخصها ثم يحتفظ بخمسين على الأكثر.

خطوة 6:

```text
build_plan_rows / TwoStagePlanRecommender._score_stage2
```

يوسع عضوية الخطط المختصرة ويعيد حساب أربع عشرة ميزة خطة وأقران، ثم يتوقع بسبعة وأربعين مدخلًا.

خطوة 7:

```text
summarize_scored_plans / rank_evaluation_plans
```

يحمل هوية الخطة ومكونات التوازن فقط من المرحلة الأولى؛ ترتيب النهائي يستعمل توقع المرحلة الثانية ثم يعيد العدد المطلوب.

### شكل الصف في المرحلتين

قبل الأولى، صف واحد لكل مادة، لا لكل خطة. سبع ميزات تاريخ مادة تطبق من النسخة نفسها، مع ميزات الطالب والمادة والعناصر الفئوية. الأربع عشرة التي تصف الخطة والأقران مستبعدة.

بعد الاختصار، صف لكل عضوية مادة في خطة. المادة المشتركة في خطتين تظهر مرتين، لأن سياق أقرانها وحمل الخطة قد يختلفان.

```text
Stage 1: N candidates x 33 features
Stage 2: sum(len(plan) for plan in shortlist) x 47 features
```

انتقال بيانات التوازن والهوية لا يحمل توقعات الأولى إلى هدف النهائي. جبهة المفاضلة للأولى ليست الجبهة النهائية؛ يحسب النهائي من توقعات ثانية مستقلة.

بصمة الطلب تحسب من المدخل المعياري وعدد النتائج. القيود الجديدة تدخل عند استخدامها، مع حفظ البصمات القديمة للاستدعاءات التي لا ترسلها.

### طرق الأصناف الموجودة

هذه الطرق جزء من السلوك الأساسي؛ الترتيب أعلاه يبين ما يستدعى منها في المسار الفعلي.

<table>
<thead>
<tr>
<th>
الطريقة
</th>
<th>
التوقيع
</th>
<th>
وظيفتها
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
<code>TwoStagePlanRecommender.__init__</code>
</td>
<td>
<pre>__init__(self, artifacts, history_manager, *, stage1_shortlist_strategy, final_ranking_strategy, num_threads=4)</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
<tr>
<td>
<code>TwoStagePlanRecommender.load</code>
</td>
<td>
<pre>load(cls, *, project_root=paths.PROJECT_ROOT, history_root=None, num_threads=4)</pre>
</td>
<td>
يحمل النسخة أو الأصول المطلوبة ويتحقق منها؛ التفاصيل تختلف بحسب الصنف وتوضحها الصفحة.
</td>
</tr>
<tr>
<td>
<code>TwoStagePlanRecommender.from_loaded_artifacts</code>
</td>
<td>
<pre>from_loaded_artifacts(cls, artifacts, manager, *, num_threads=4)</pre>
</td>
<td>
ينشئ محركًا من أصول محملة بعد إثبات سياسة اعتمادها.
</td>
</tr>
<tr>
<td>
<code>TwoStagePlanRecommender._ranking_metadata</code>
</td>
<td>
<pre>_ranking_metadata(self, stage1_strategy, final_strategy)</pre>
</td>
<td>
يثبت هوية الاستراتيجيتين ويمنع تبديلها بعد الاعتماد.
</td>
</tr>
<tr>
<td>
<code>TwoStagePlanRecommender.load_for_evaluation</code>
</td>
<td>
<pre>load_for_evaluation(cls, *, stage1_shortlist_strategy, final_ranking_strategy, project_root=paths.PROJECT_ROOT, history_root=None, num_threads=4)</pre>
</td>
<td>
ينشئ مسار تقييم باستراتيجيات صريحة غير معتمدة للتشغيل.
</td>
</tr>
<tr>
<td>
<code>TwoStagePlanRecommender.update_history_from_payload</code>
</td>
<td>
<pre>update_history_from_payload(self, *, history_payload)</pre>
</td>
<td>
يفوض إلى مدير التاريخ؛ وكيل المخزن الدائم يرفضه خارج مسار الإدارة.
</td>
</tr>
<tr>
<td>
<code>TwoStagePlanRecommender._prepare_candidates</code>
</td>
<td>
<pre>_prepare_candidates(self, prepared, history_snapshot)</pre>
</td>
<td>
ينسخ اللقطة ويطبق تاريخ النسخة المثبتة على المرشحين.
</td>
</tr>
<tr>
<td>
<code>TwoStagePlanRecommender._score_stage2</code>
</td>
<td>
<pre>_score_stage2(self, rows)</pre>
</td>
<td>
يعيد حساب سياق العضوية ثم يتوقع بالعقد الكامل.
</td>
</tr>
<tr>
<td>
<code>TwoStagePlanRecommender.recommend_from_payloads</code>
</td>
<td>
<pre>recommend_from_payloads(self, *, student_payload, request_payload, top_k=3, history_as_of_part=None, allow_older_history=None)</pre>
</td>
<td>
ينسق المرحلتين على لقطة واحدة ويختار النتائج داخل المختصر.
</td>
</tr>
</tbody>
</table>

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
_json_value

isinstance(value, Mapping)
isinstance(value, (list, tuple))
value is None or value is pd.NA
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
_input_fingerprint

constraints.requirement_group_policies is not None
constraints.max_new_courses is not None
```

## ٦. كيف تتغير البيانات؟

لمادتين متاحتين من ثلاث ساعات وهدف ست ساعات، تتولد خطة واحدة تضم المادتين. الأولى تتوقع صفين؛ الثانية تتوقع صفين أيضًا لأن قائمة الخطط المختصرة تضم خطة واحدة.

## ٧. القواعد والافتراضات

استراتيجية الأولى واستراتيجية النهائي مستقلتان. الاعتماد الحالي جبهات المفاضلة في المرحلتين، نسختهما الأولى. القطع التدريبي والتاريخي يسبقان الهدف. لا تدريب داخل الطلب.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

إعادة استعمال توقع المرحلة الأولى في النهائي يفسد معنى المرحلة الثانية. إعادة التقاط التاريخ لكل مرحلة يخلط نسختين. تغيير الاستراتيجية بعد التحميل يرفض قبل التوقع.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [مكونات التوازن الناعم](balance_policy.md)
- [مجاميع الدفعات ومدير اللقطة](history_update.md)
- [عقود النواة والمدخلات المحلية](inputs.md)
- [البحث عن مجموعات بالساعات الدقيقة](plan_generation.md)
- [توقع المواد وتلخيص جودة الخطط](plan_scoring.md)
- [الهوية والترتيب وجبهات المفاضلة](ranking.md)
- [التحقق من اعتماد سياسة الترتيب](ranking_policy.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](shortlist.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](two_stage_artifacts.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/benchmark_two_stage.py)

```text
scripts/benchmark_two_stage.py
```

[الأداة المرجعية](../../../scripts/evaluate_corrected_phase6.py)

```text
scripts/evaluate_corrected_phase6.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_api_core_extensions.py)

```text
tests/test_api_core_extensions.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_loaded_artifact_factory_enforces_approval_without_reloading
```

[ملف اختبار مرتبط](../../../tests/test_api_cumulative_integration.py)

```text
tests/test_api_cumulative_integration.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_worker_started_before_migration_adopts_shared_active_pointer
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert response.status_code == 200
```

[ملف اختبار مرتبط](../../../tests/test_api_integration.py)

```text
tests/test_api_integration.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_api_calls_actual_core_with_33_and_47_features_and_group_caps
test_original_gpa_calculation_and_helper_are_identical_on_full_schema
test_all_history_identity_rows_checked_even_when_first_schema_incomplete
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert result['status'] == 'ok'
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_activation.py)

```text
tests/test_two_stage_activation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_verified_artifact_loader_accepts_complete_human_approval
test_incomplete_or_inconsistent_approval_still_refuses_assets
test_approval_does_not_bypass_existing_feature_or_model_hash_checks
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert bundle.stage1.grade_model.num_feature() == 33
```

[اختبار باستيراد ديناميكي](../../../tests/test_two_stage_engine.py)

```text
tests/test_two_stage_engine.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_two_stage_orchestration_has_an_explicit_evaluation_entrypoint
test_production_activation_refuses_unapproved_independent_strategies
test_evaluation_factory_loads_assets_and_history_once_for_reused_requests
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert callable(engine.load_for_evaluation)
```

[اختبار باستيراد ديناميكي](../../../tests/test_two_stage_shortlist.py)

```text
tests/test_two_stage_shortlist.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_complete_feasibility_before_shortlist_fractional_and_optional_zero
test_no_lower_credit_fallback_and_no_prefiltering_of_failed_availability
test_shared_scoring_rejects_nonfinite_or_wrong_shape_before_clip
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert set(result.all_plans.course_tuple) == expected == {('C',), ('C', 'D'), ('E', 'F'), ('D', 'E', 'F')}
```

## ١١. القيود المعروفة

البحث شامل وقد يتضخم مع عدد المواد. حدود الخدمة غير معتمدة. لا ضمان للأفضلية العالمية بعد الاختصار، ولا سياسة مؤكدة لاستبدال درجات الإعادة في المعدل.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- التوقع الأول يستعمل صفًا لكل مادة وثلاثًا وثلاثين ميزة.
- الثاني يستعمل عضوية المادة في كل خطة وسبعًا وأربعين ميزة.
- قائمة مختصرة واستراتيجيتان مستقلتان تحددان نطاق النتيجة النهائية.

ثلاثة أسئلة للفهم:

1. لماذا قد تتغير توقعات مادة واحدة بين خطتين في الثانية؟
2. أين تثبت لقطة تاريخ واحدة طوال الطلب؟
3. لماذا لا يعني أفضل المختصر أفضل جميع الخطط الممكنة؟

تمرين قراءة آمن:

ارسم ثلاث مواد وخطتين تشتركان في مادة؛ احسب عدد الصفوف في كل مرحلة دون مودل.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
