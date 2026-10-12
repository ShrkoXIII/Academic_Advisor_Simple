# تحميل أصول المرحلتين والتحقق من مصدرها

```text
src/recommendation/two_stage_artifacts.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يحمي التشغيل من تحميل مودل تجريبي أو ترتيب ميزات أو أهداف أو نسخ فئات لا تطابق الاعتماد.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق التحقق والتوصية والإدارة](../api/service.md)
- [المحرك المعتمد ذو المرحلتين](two_stage_engine.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [تحويل العلامة إلى نقاط وفق النسخة](../grade_scale.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [التحقق من اعتماد سياسة الترتيب](ranking_policy.md)

## ٣. المدخلات

جذر مشروع وملف بيان أصول، وقطع هدف اختياري. يقرأ مودلات المرحلة الأولى المعزولة ومودلات المرحلة الثانية الرسمية ومستويات الفئات وسلم العلامات.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

الأنواع والبنى المستعملة في هذا الحد:

```text
manifest: dict
project_root: Path-compatible
target_part: optional academic part
```

## ٤. المخرجات

كائنان لزوجي مودلات وسلّم وبيان في بنية أصول واحدة، بعد فحص البصمات والعقود. الفشل لا يتحول إلى اختيار آخر.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
load_two_stage_artifacts(...) -> TwoStageArtifacts
load_model_pair(...) -> ModelPair
stage_feature_contract(...) -> dict
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
<code>ModelPair</code>
</td>
<td>
زوج توقع علامة ورسوب ومستويات فئاته.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_model_pair</code>
</td>
</tr>
<tr>
<td>
<code>TwoStageArtifacts</code>
</td>
<td>
زوجا المرحلتين وسلم العلامات وبيان المصدر.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_manifest_assets</code>
</td>
</tr>
<tr>
<td>
<code>stage_feature_contract</code>
</td>
<td>
اشتقاق العقد المرتب الخاص بكل مرحلة.
</td>
<td>
<pre>stage_feature_contract(stage)</pre>
</td>
<td>
<pre>contract</pre>
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.recommend_from_payloads</code>
<br>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>validate_stage_metadata</code>
<br>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>validate_artifact_manifest</code>
</td>
</tr>
<tr>
<td>
<code>artifact_relative_paths</code>
</td>
<td>
اختيار مسارات أصول المرحلة الرسمية المعروفة.
</td>
<td>
<pre>artifact_relative_paths(stage)</pre>
</td>
<td>
<pre>dict(zip(('grade', 'fail', 'category_levels'), (path.relative_to(paths.PROJECT_ROOT).as_posix() for path in selected)))</pre>
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>validate_stage_metadata</code>
<br>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>validate_artifact_manifest</code>
<br>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_manifest_assets</code>
</td>
</tr>
<tr>
<td>
<code>project_file</code>
</td>
<td>
منع مرجع أصل يهرب خارج جذر المشروع.
</td>
<td>
<pre>project_file(root, relative)</pre>
</td>
<td>
<pre>path</pre>
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_manifest_assets</code>
<br>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_two_stage_artifacts</code>
</td>
</tr>
<tr>
<td>
<code>read_artifact_json</code>
</td>
<td>
قراءة بيانات أصول مع رفض الأعداد غير المحدودة.
</td>
<td>
<pre>read_artifact_json(path)</pre>
</td>
<td>
<pre>json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject_constant)</pre>
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_model_pair</code>
<br>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_manifest_assets</code>
<br>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_two_stage_artifacts</code>
</td>
</tr>
<tr>
<td>
<code>_is_sha256</code>
</td>
<td>
تحقق شكل بصمة سداسية بطول ثابت.
</td>
<td>
<pre>_is_sha256(value)</pre>
</td>
<td>
<pre>isinstance(value, str) and len(value) == 64 and all((character in '0123456789abcdef' for character in value))</pre>
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>verify_artifact_hash</code>
<br>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>validate_archived_provenance</code>
</td>
</tr>
<tr>
<td>
<code>verify_artifact_hash</code>
</td>
<td>
اشتراط ملف موجود وبصمة محتوى مطابقة.
</td>
<td>
<pre>verify_artifact_hash(path, expected)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_model_pair</code>
<br>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_manifest_assets</code>
</td>
</tr>
<tr>
<td>
<code>validate_stage_metadata</code>
</td>
<td>
مطابقة عقد وهدف ومصدر وقطع تدريب المرحلة.
</td>
<td>
<pre>validate_stage_metadata(stage, metadata)</pre>
</td>
<td>
<pre>(paths.academic_part(cutoff), basis)</pre>
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>validate_artifact_manifest</code>
</td>
</tr>
<tr>
<td>
<code>load_model_pair</code>
</td>
<td>
تحميل المودلين وفحص رؤوسهما وفئاتهما.
</td>
<td>
<pre>load_model_pair(entry, model_paths)</pre>
</td>
<td>
<pre>ModelPair(*models, levels)</pre>
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_manifest_assets</code>
</td>
</tr>
<tr>
<td>
<code>validate_archived_provenance</code>
</td>
<td>
فحص مصدر التدريب المؤرشف وبصماته عند الترقية.
</td>
<td>
<pre>validate_archived_provenance(stage, evidence)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>validate_artifact_manifest</code>
</td>
</tr>
<tr>
<td>
<code>validate_artifact_manifest</code>
</td>
<td>
فحص بيان كامل يشمل السياسة والأصول والقطع.
</td>
<td>
<pre>validate_artifact_manifest(manifest)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_manifest_assets</code>
</td>
</tr>
<tr>
<td>
<code>load_manifest_assets</code>
</td>
<td>
تحميل أصول البيان بعد التحقق من ملفاتها وعقودها.
</td>
<td>
<pre>load_manifest_assets(manifest, *, project_root, shortlist_directory=None, target_part=None)</pre>
</td>
<td>
<pre>TwoStageArtifacts(*pairs, GradeScale.from_parquet(scale_path), manifest)</pre>
</td>
<td>
<a href="two_stage_artifacts.md">صفحة المستدعي</a>
<br>
<code>load_two_stage_artifacts</code>
</td>
</tr>
<tr>
<td>
<code>load_two_stage_artifacts</code>
</td>
<td>
قراءة البيان الرسمي وتحميل أصوله دون بدائل.
</td>
<td>
<pre>load_two_stage_artifacts(*, project_root=paths.PROJECT_ROOT, target_part=None)</pre>
</td>
<td>
<pre>load_manifest_assets(manifest, project_root=project_root, target_part=target_part)</pre>
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.load</code>
<br>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.load_for_evaluation</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
stage_feature_contract
```

يشتق عقد الأولى باستبعاد ميزات الخطة الأربع عشرة، ويثبت العددين ثلاثة وثلاثين وسبعة وأربعين.

خطوة 2:

```text
validate_artifact_manifest / validate_stage_metadata
```

يتحقق من الإصدار والأهداف وقطع التدريب وهويات الملفات والمصدر المؤرشف والسياسة.

خطوة 3:

```text
project_file / verify_artifact_hash
```

يمنع مرجعًا خارج جذر المشروع ويتحقق من بصمة كل ملف.

خطوة 4:

```text
load_model_pair
```

يطابق أسماء الميزات وعددها وترتيب فئات المودل وهدفه الفعلي مع البيان.

خطوة 5:

```text
load_manifest_assets / load_two_stage_artifacts
```

يجمع الأصول بعد فحص سلم العلامات؛ الهدف يجب أن يلي قطع تدريب المرحلتين.

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
stage_feature_contract

stage not in {'stage1', 'stage2'}
stage == 'stage1'
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
project_file

value.is_absolute() or '..' in value.parts or (not path.is_relative_to(root))
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
verify_artifact_hash

not Path(path).is_file()
not _is_sha256(expected) or file_sha256(path) != expected
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
validate_stage_metadata

metadata.get('dataset_version', 'V2' if stage == 'stage2' else None) != 'V2'
any((recorded.get(key) != expected[key] for key in checked))
stage == 'stage1'
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
load_model_pair

('grade', 'fail')
model.feature_name() != contract['model_features'] or model.num_feature() != contract['feature_count']
model.pandas_categorical != [levels[name] for name in CATEGORICAL_FEATURES]
```

## ٦. كيف تتغير البيانات؟

مودل يعلن العدد الصحيح لكن ترتيب الميزات مختلف يُرفض. اسم مرشح العلامة الرسمي هو الاسم المصحح الحالي، لا التهجئة القديمة.

## ٧. القواعد والافتراضات

المرحلة الثانية تحافظ على المودلين الرسميين. المصدر المؤرشف مطلوب ولا يساوي تدريبًا جديدًا. ملفات تقارير الاعتماد لا تُقرأ أثناء التوقع لتقرير السياسة.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

نقل مودل دون مستويات فئاته أو تغيير ملف بعد اعتماد البصمة ينتج رفضًا. خلط تاريخ الخدمة بقطع التدريب قد يمنع تحديثًا صحيحًا أو يسمح بتسرب.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [تحويل العلامة إلى نقاط وفق النسخة](../grade_scale.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [التحقق من اعتماد سياسة الترتيب](ranking_policy.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
lightgbm
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

[الأداة المرجعية](../../../scripts/promote_shortlist_artifacts.py)

```text
scripts/promote_shortlist_artifacts.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_two_stage_engine.py)

```text
tests/test_two_stage_engine.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_pinned_official_stage_two_models_match_legacy_on_identical_synthetic_plans
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_matrix.py)

```text
tests/test_two_stage_matrix.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_stage1_matches_legacy_slice_without_requiring_plan_context
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert levels == original_levels
```

[اختبار باستيراد ديناميكي](../../../tests/test_two_stage_artifacts.py)

```text
tests/test_two_stage_artifacts.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_stage_contracts_derive_33_and_47_from_the_official_order
test_promotion_copies_exact_bytes_and_archives_original_provenance
test_promoted_pair_produces_the_same_synthetic_predictions
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert first['model_features'] == [name for name in BASE_FEATURES if name not in PLAN_CONTEXT_COLUMNS]
```

## ١١. القيود المعروفة

تحميل الأصول والتحقق منها لا يثبت جاهزية بيانات الطالب ولا اعتماد حدود الأداء.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يحمي التشغيل من تحميل مودل تجريبي أو ترتيب ميزات أو أهداف أو نسخ فئات لا تطابق الاعتماد.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: تحميل الأصول والتحقق منها لا يثبت جاهزية بيانات الطالب ولا اعتماد حدود الأداء.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.
