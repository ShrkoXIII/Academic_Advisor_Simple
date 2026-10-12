# مجاميع الدفعات ومدير اللقطة

```text
src/recommendation/history_update.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يضيف نتائج فصل نهائي مجمّعة إلى نسخة من التاريخ بدل إعادة بناء الصفوف الفردية، ويمنع التكرار والتعارض ويحفظ اتساق اللقطة طوال الطلب.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [المعاينة التشخيصية لدفعة التاريخ](../api/history_adapter.md)
- [تنسيق التحقق والتوصية والإدارة](../api/service.md)
- [تصدير واجهات نواة التوصية](__init__.md)
- [الإدارة الدائمة للتاريخ التراكمي](cumulative_history.md)
- [المحرك المعتمد ذو المرحلتين](two_stage_engine.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

غلاف نواة بفصل دفعة وتأكيد تثبيت وقائمة مجاميع، وحالة تاريخ أساسية وبيانات مصدرها.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

أسماء الحقول المعرّفة في الملف:

```text
DELTA_ID_COLUMNS
degree_id
course_id
faculty_id
plan_requirement_type_id
```

أسماء الحقول المعرّفة في الملف:

```text
DELTA_NUMERIC_COLUMNS
course_credits
count
fail_count
retake_count
mark_sum
attempt_sum
```

الأنواع والبنى المستعملة في هذا الحد:

```text
history_payload: Mapping
state: CourseHistoryState
metadata: dict
```

## ٤. المخرجات

دفعة معيارية ثابتة ببصمة، أو حالة مستنسخة محدثة، أو نتيجة معاينة أو نشر. المدير يحتفظ بمرجع نسخة متحقق منها.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
normalize_history_delta(...) -> HistoryDelta
apply_history_delta(...) -> CourseHistoryState (clone)
capture(...) -> HistorySnapshot
preview_delta / update_history_from_payload -> dict
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
<code>_number</code>
</td>
<td>
تحقق عدد غير سالب ودقيق للمجاميع.
</td>
<td>
<pre>_number(value, name, *, integer=False)</pre>
</td>
<td>
<pre>result</pre>
</td>
<td>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>_part</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>normalize_history_delta</code>
</td>
</tr>
<tr>
<td>
<code>_part</code>
</td>
<td>
تحقق فصل الدفعة والتقويم المدعوم.
</td>
<td>
<pre>_part(value)</pre>
</td>
<td>
<pre>paths.academic_part(int(number))</pre>
</td>
<td>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>normalize_history_delta</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>HistorySnapshot.metadata_for_target</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>_validate_update_metadata</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.capture</code>
</td>
</tr>
<tr>
<td>
<code>_canonical_number</code>
</td>
<td>
تمثيل عددي ثابت لبصمة المجاميع.
</td>
<td>
<pre>_canonical_number(number)</pre>
</td>
<td>
<pre>(text.rstrip('0').rstrip('.') if '.' in text else text) if number else '0'</pre>
</td>
<td>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>normalize_history_delta</code>
</td>
</tr>
<tr>
<td>
<code>HistoryDelta</code>
</td>
<td>
صفوف معيارية ثابتة وبصمة دفعة.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>normalize_history_delta</code>
</td>
</tr>
<tr>
<td>
<code>normalize_history_delta</code>
</td>
<td>
تطبيع والتحقق وبصمة صفوف مجاميع نهائية.
</td>
<td>
<pre>normalize_history_delta(payload, *, require_finalized=True)</pre>
</td>
<td>
<pre>HistoryDelta(part, rows, sha256(canonical.encode('utf-8')).hexdigest())</pre>
</td>
<td>
<a href="../api/history_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_history_delta</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._preview</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._commit</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.finalize</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>apply_history_delta</code>
</td>
</tr>
<tr>
<td>
<code>validate_history_state</code>
</td>
<td>
فحص المخطط واتساق المستويات والمجاميع العامة.
</td>
<td>
<pre>validate_history_state(state)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._load</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.initialize</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>_apply_normalized_delta</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.load</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.capture</code>
</td>
</tr>
<tr>
<td>
<code>apply_history_delta</code>
</td>
<td>
إضافة دفعة إلى نسخة من الحالة.
</td>
<td>
<pre>apply_history_delta(state, history_payload)</pre>
</td>
<td>
<pre>_apply_normalized_delta(state, normalize_history_delta(history_payload))</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>_apply_normalized_delta</code>
</td>
<td>
التطبيق الداخلي للصفوف التي تحققت هويتها بالفعل.
</td>
<td>
<pre>_apply_normalized_delta(state, delta)</pre>
</td>
<td>
<pre>cloned</pre>
</td>
<td>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>apply_history_delta</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.update_history_from_payload</code>
</td>
</tr>
<tr>
<td>
<code>HistorySnapshot</code>
</td>
<td>
تثبيت حالة ومصدر واحدين للطلب.
</td>
<td>
مدخلات بناء الصنف وحقوله؛ الطرق أدناه تفصل تواقيعها.
</td>
<td>
كائن من الصنف؛ حقوله وسلوكه في تعريفه وطرق استعماله أدناه.
</td>
<td>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._load</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.initialize</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.load</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.capture</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.update_history_from_payload</code>
</td>
</tr>
<tr>
<td>
<code>_validate_update_metadata</code>
</td>
<td>
فحص سجل الدفعات وبصمات سلسلة المصدر.
</td>
<td>
<pre>_validate_update_metadata(metadata)</pre>
</td>
<td>
<pre>None</pre>
</td>
<td>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._load</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.initialize</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.load</code>
<br>
<a href="history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.capture</code>
</td>
</tr>
<tr>
<td>
<code>FrozenHistoryManager</code>
</td>
<td>
تسلسل التحديث والنشر وتثبيت لقطة قراءته.
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
<code>ApiService._load_history</code>
<br>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.load</code>
<br>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.load_for_evaluation</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._preview</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._commit</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
normalize_history_delta
```

يفحص المفاتيح والأعداد وحدود المجاميع، يمنع تكرار حبة التجميع، ويرتب الصفوف ثم يبصم تمثيلًا معياريًا.

خطوة 2:

```text
validate_history_state
```

يراجع مخطط المستويات الخمسة والستة مجاميع وإعدادات الدعم؛ مجموع كل مستوى يجب أن يطابق العام.

خطوة 3:

```text
_apply_normalized_delta
```

يستنسخ الحالة ويضيف المجاميع مباشرة عبر مفاتيح التاريخ، بلا إعادة وزن الماضي وبلا إرسالها إلى تحديث الصفوف الخام.

خطوة 4:

```text
HistorySnapshot
```

يمسك حالة ومصدرًا واحدين؛ بيانات المصدر تُعاد بنسخة منفصلة.

خطوة 5:

```text
FrozenHistoryManager.preview_delta
```

يميز الدفعة الجديدة من المطبقة بنفس البصمة ومن تعارض فصل بنفس الهوية.

خطوة 6:

```text
FrozenHistoryManager.update_history_from_payload
```

يسلسل الكتابة، يبني سلسلة المصدر، يحفظ مرحليًا ويعيد التحميل والتحقق ثم ينشر ويبدل مرجع المدير المحلي.

### المجاميع التي يسمح بها العقد

العداد هو عدد النتائج النهائية، وليس عدد مواد السجل المسجلة كيفما كانت حالتها. مجموع المحاولات صحيح؛ كل إعادة تضيف محاولة إضافية على الأقل. الرسوب مرتبط بعلامة أقل من خمسين.

```text
count > 0
0 <= fail_count <= count
0 <= retake_count <= count
0 <= mark_sum <= 100 * count
attempt_sum >= count + retake_count
```

توجد قيود أدق تربط مجموع العلامات بعدد الراسبين والناجحين، فلا يكفي فحص كل عدد وحده. الدفعة الفارغة مسموحة بنيويًا ويمكن أن تتقدم بالقطع، لكنها لا تثبت نهائية جامعية بنفسها.

المجاميع الجديدة تدخل بمجموعها الفعلي ووزن واحد، لا كمتوسطات مصطنعة ولا كصفوف أفراد. لا يضاف مجموع نقاط تقديري.

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
<code>HistoryDelta.to_frame</code>
</td>
<td>
<pre>to_frame(self)</pre>
</td>
<td>
يحول صفوف الدفعة المعيارية إلى جدول بأنواع محددة.
</td>
</tr>
<tr>
<td>
<code>HistorySnapshot.as_of_part</code>
</td>
<td>
<pre>as_of_part(self)</pre>
</td>
<td>
يعرض قطع الحالة المثبتة.
</td>
</tr>
<tr>
<td>
<code>HistorySnapshot.metadata</code>
</td>
<td>
<pre>metadata(self)</pre>
</td>
<td>
يعيد نسخة منفصلة من بيانات المصدر.
</td>
</tr>
<tr>
<td>
<code>HistorySnapshot.apply</code>
</td>
<td>
<pre>apply(self, frame)</pre>
</td>
<td>
ينتج ميزات للصفوف من الحالة السابقة دون إدخال نتائجها إلى التاريخ.
</td>
</tr>
<tr>
<td>
<code>HistorySnapshot.metadata_for_target</code>
</td>
<td>
<pre>metadata_for_target(self, target_part)</pre>
</td>
<td>
يضيف علاقة القطع بالهدف وعمر التاريخ إلى مصدر منفصل.
</td>
</tr>
<tr>
<td>
<code>FrozenHistoryManager.__init__</code>
</td>
<td>
<pre>__init__(self, snapshot, *, root, skipped_bundles=())</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
<tr>
<td>
<code>FrozenHistoryManager.load</code>
</td>
<td>
<pre>load(cls, *, root=None)</pre>
</td>
<td>
يحمل النسخة أو الأصول المطلوبة ويتحقق منها؛ التفاصيل تختلف بحسب الصنف وتوضحها الصفحة.
</td>
</tr>
<tr>
<td>
<code>FrozenHistoryManager.capture</code>
</td>
<td>
<pre>capture(self, *, target_part, history_as_of_part=None, allow_older_history=None)</pre>
</td>
<td>
يثبت نسخة واحدة، بالقطع المحدد أو المرجع النشط بحسب الواجهة.
</td>
</tr>
<tr>
<td>
<code>FrozenHistoryManager.preview_delta</code>
</td>
<td>
<pre>preview_delta(self, *, history_payload)</pre>
</td>
<td>
يقارن بصمة الدفعة بالسلسلة دون نشر.
</td>
</tr>
<tr>
<td>
<code>FrozenHistoryManager.update_history_from_payload</code>
</td>
<td>
<pre>update_history_from_payload(self, *, history_payload)</pre>
</td>
<td>
يفوض إلى مدير التاريخ؛ وكيل المخزن الدائم يرفضه خارج مسار الإدارة.
</td>
</tr>
</tbody>
</table>

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
_number

isinstance(value, (bool, np.bool_))
not result.is_finite() or result < 0 or (not np.isfinite(float(result))) or (integer and result != result.to_integral_value())
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
_part

not 10000 <= number <= 99999
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
normalize_history_delta

not isinstance(payload, Mapping) or (require_finalized and payload.get('finalized') is not True)
part < 20221
not isinstance(records, (list, tuple))
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
validate_history_state

state.tables.values()
not np.isfinite(values).all() or (values < 0).any()
not np.allclose(values.sum(axis=0), global_values[0], rtol=1e-10, atol=1e-07)
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
_apply_normalized_delta

delta.delta_part <= state.as_of_part
not frame.empty
build_history_keys(frame).items()
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
_validate_update_metadata

metadata.get('update_method') != 'aggregate_delta_v1'
applied.items()
not isinstance(digest, str) or len(digest) != 64 or any((c not in '0123456789abcdef' for c in digest))
```

## ٦. كيف تتغير البيانات؟

صف تجميع لمحاولتين بعلامتي أربعين وثمانين له عداد اثنين، مجموع علامات مئة وعشرين، رسوب واحد، مجموع محاولات ثلاثة وإعادة واحدة. إضافته تعادل جمع نتيجتين نهائيتين اصطناعيتين.

## ٧. القواعد والافتراضات

الدفعات الجديدة المدعومة أوزانها واحد منذ بداية سنة ألفين واثنتين وعشرين. الرسوب علامة أقل من خمسين والإعادة محاولة أكبر من واحدة. المعاينة لا تنشر. اختيار قطع صريح لا يستبدل بنسخة أخرى.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

تطبيق الدفعة مرتين يضاعف الدعم. إعادة وزن الماضي مع كل فصل يغيّر التدريب. عدم تثبيت مرجع طلب قد يخلط الإحصاءات.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [أدوات تنظيف الأعمدة والمعرفات](../data/cleaning_utils.md)
- [العقد المرتب لميزات المودل](../features/feature_contract.md)
- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [هندسة الميزات الزمنية المشتركة](../features/temporal_features.md)
- [مرجع المسارات والإصدارات](../paths.md)

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
test_exact_history_selection_and_explicit_backtesting
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert manager.capture(target_part=20252).as_of_part == 20243
```

[ملف اختبار مرتبط](../../../tests/test_api_integration.py)

```text
tests/test_api_integration.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_delta_aggregates_equal_individual_outcomes_without_estimated_points
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert actual.global_sums == expected.global_sums
```

[ملف اختبار مرتبط](../../../tests/test_cumulative_history.py)

```text
tests/test_cumulative_history.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_preexisting_bundle_without_activation_record_cannot_be_served
test_readonly_proxy_rejects_skipped_semester_without_changing_control
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert error.value.code == 'HISTORY_VERSION_NOT_ACTIVATED'
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_engine.py)

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

[اختبار باستيراد ديناميكي](../../../tests/test_history_update.py)

```text
tests/test_history_update.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_aggregate_addition_preserves_weighted_prefix_and_matches_raw_oracle
test_delta_identity_is_canonical_and_state_bytes_are_deterministic
test_invalid_aggregate_is_rejected_without_mutating_prefix
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert updated.global_sums == {'effective_support': 4.25, 'raw_count': 5.0, 'mark_sum': 270.0, 'fail_sum': 1.25, 'attempt_sum': 5.5, 'retake_sum': 1.25}
```

## ١١. القيود المعروفة

المدير المحلي ليس مؤشر إدارة دائمًا؛ فصل النشر والتفعيل الدائم وظيفة المخزن التراكمي. الثقة في التثبيت تأتي من جهة مخولة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- الدفعة تحمل مجاميع مثبتة، ولا تحتاج صفوف طلاب فردية.
- تطبق على نسخة ثم تفحص قبل نشر حزمة جديدة.
- البصمة تمنع إعادة الدفعة المطابقة وتكشف المتعارضة.

ثلاثة أسئلة للفهم:

1. ما الفرق بين إعادة طلب مطابق ودفعة مختلفة للفصل نفسه؟
2. كيف يثبت اتساق مجاميع الرسوب والمحاولات؟
3. لماذا لا يغير التحديث لقطة طلب بدأ قبل اكتماله؟

تمرين قراءة آمن:

اكتب على الورق حالة المدير قبل تحديث ناجح ثم إعادة الدفعة ثم دفعة متعارضة؛ حدد أين تتوقف كل محاولة.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
