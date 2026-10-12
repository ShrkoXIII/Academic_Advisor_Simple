# الإدارة الدائمة للتاريخ التراكمي

```text
src/recommendation/cumulative_history.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يضع حول مدير التاريخ آلية دائمة للوضع والموافقة والمؤشر النشط، مع تخزين مستقل لا يكتب داخل جذور التاريخ السابقة.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق التحقق والتوصية والإدارة](../api/service.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [مجاميع الدفعات ومدير اللقطة](history_update.md)

## ٣. المدخلات

جذر إعداد مستقل، مصدر قديم للقراءة، وفاحص توافق أصول. العمليات تحتاج بصمة وموافقة وتأكيدًا؛ الحدث الآلي يحتاج ثقة صريحة من حد النقل.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

الأنواع والبنى المستعملة في هذا الحد:

```text
root: Path-compatible
compatibility_check: callable(state, metadata)
history_payload: Mapping
approval_reference: str
confirmation: bool
```

## ٤. المخرجات

ملف تحكم صغير وحزم جديدة ثابتة، ونتائج حالة ومعاينة وإنشاء وتفعيل. لا يقرأ مودلًا ولا يصرح لمستخدم شبكة بنفسه.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
status / preview / commit / activate / finalize -> dict
capture(...) -> HistorySnapshot
serving_manager() -> _ServingHistoryManager | None
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
<code>HistoryUpdateError</code>
</td>
<td>
خطأ إدارة برمز آمن وحالة نقل.
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
<code>_approval</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>_confirmation</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.__init__</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._read</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._locked</code>
</td>
</tr>
<tr>
<td>
<code>_now</code>
</td>
<td>
وقت تسجيل عملية الإدارة وفق التوقيت العالمي.
</td>
<td>
<pre>_now()</pre>
</td>
<td>
<pre>datetime.now(timezone.utc).isoformat()</pre>
</td>
<td>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._locked</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.initialize</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._commit</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._activate</code>
</td>
</tr>
<tr>
<td>
<code>_digest</code>
</td>
<td>
بصمة قاموس معياري مرتب.
</td>
<td>
<pre>_digest(value)</pre>
</td>
<td>
<pre>sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()</pre>
</td>
<td>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._preview</code>
</td>
</tr>
<tr>
<td>
<code>_approval</code>
</td>
<td>
اشتراط مرجع موافقة وحفظ بصمته دون نصه الخاص.
</td>
<td>
<pre>_approval(value)</pre>
</td>
<td>
<pre>sha256(value.encode('utf-8')).hexdigest()</pre>
</td>
<td>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.initialize</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._commit</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.finalize</code>
</td>
</tr>
<tr>
<td>
<code>_confirmation</code>
</td>
<td>
اشتراط تأكيد صريح من المشرف.
</td>
<td>
<pre>_confirmation(value)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.initialize</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.commit</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.activate</code>
</td>
</tr>
<tr>
<td>
<code>_overlap</code>
</td>
<td>
كشف تداخل جذرين لمنع الكتابة على التاريخ القديم.
</td>
<td>
<pre>_overlap(a, b)</pre>
</td>
<td>
<pre>a == b or a in b.parents or b in a.parents</pre>
</td>
<td>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.__init__</code>
<br>
<a href="cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.initialize</code>
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore</code>
</td>
<td>
إدارة دائمة للأوضاع والنسخ والمؤشر والموافقات.
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
<code>ApiService.__init__</code>
</td>
</tr>
<tr>
<td>
<code>_ServingHistoryManager</code>
</td>
<td>
وكيل قراءة متوافق مع المحرك يلتقط المؤشر الدائم.
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
<code>CumulativeHistoryStore.serving_manager</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
CumulativeHistoryStore._locked
```

يجمع قفلًا للعمال داخل العملية وقفل نظام تشغيل بين العمليات؛ الكتابة المؤقتة مع تفريغ ثم استبدال ذري تحفظ المؤشر.

خطوة 2:

```text
CumulativeHistoryStore.initialize
```

يرحّل نسخة تراكمية معتمدة عبر نهاية الفصل الأول من سنة ألفين وخمس وعشرين؛ يشترط تاريخًا سابقًا وعدّادات مصدر مطابقة وبصمة الأصل.

خطوة 3:

```text
CumulativeHistoryStore.preview / commit
```

يحفظ معاينة مرتبطة بالبصمة والأساس والوضع؛ التأكيد المطابق ينشر نسخة جديدة دون تغيير المؤشر.

خطوة 4:

```text
CumulativeHistoryStore.activate
```

يعيد فحص النسخة والبصمة والتوافق والسلسلة ثم يبدل المؤشر ويسجل النسخ التي سبق تفعيلها.

خطوة 5:

```text
CumulativeHistoryStore.finalize
```

في الوضع الآلي فقط ينفذ التحقق والمعاينة والإنشاء والتفعيل لحدث موثوق مع مرجع اعتماد.

خطوة 6:

```text
CumulativeHistoryStore.capture / _ServingHistoryManager
```

يقرأ المؤشر الدائم ويتيح للمحرك لقطة محددة؛ النسخة المنشورة التي لم تُفعّل لا تصل إلى التوصية.

### ثلاث حدود مختلفة

التحقق للقراءة فقط لا يحفظ معاينة. المعاينة الإدارية تحفظ بصمة وتوقيت أساسها في ملف التحكم. الإنشاء ينشر حزمة ثابتة لكنه لا يبدل مؤشر الخدمة. التفعيل عملية لاحقة.

```text
validate -> no control write
preview -> pending_delta
commit -> as_of_<part>, activated=False
activate -> control.active, activated_versions
```

تأكيد قديم يرفض إذا تغيرت بصمة الأساس أو الدفعة أو الوضع. إعادة حدث نهائي مطابق لا تضيف الفصل مرتين؛ البصمة المختلفة للفصل نفسه تعارض.

التاريخ الذي سبق تفعيله قد يبقى متاحًا للاختبار التاريخي بعد رجوع المؤشر. النسخة التي أنشئت ولم تُفعّل قط لا يجوز اختيارها صراحةً للتوصية.

فشل تغيير المؤشر قد يترك نسخة صحيحة منشورة، وتبقى النسخة النشطة السابقة. إعادة تهيئة الأساس تستطيع تبني المنشور فقط عند تطابق المصدر والموافقة والمجاميع والبصمات بالكامل.

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
<code>HistoryUpdateError.__init__</code>
</td>
<td>
<pre>__init__(self, code, message, *, status_code=409)</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore.__init__</code>
</td>
<td>
<pre>__init__(self, root, *, default_mode='manual', compatibility_check=None, legacy_root=None)</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._read</code>
</td>
<td>
<pre>_read(self)</pre>
</td>
<td>
يقرأ ملف التحكم الدائم، أو حالة بدء لا تكتب شيئًا.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._write</code>
</td>
<td>
<pre>_write(self, control)</pre>
</td>
<td>
يكتب ملف تحكم مؤقتًا ثم يستبدل المؤشر ذريًا.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._locked</code>
</td>
<td>
<pre>_locked(self)</pre>
</td>
<td>
يطبق تسلسل العمال والعمليات ويسجل رموز الفشل آمنة.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._enabled</code>
</td>
<td>
<pre>_enabled(control, required_mode=None)</pre>
</td>
<td>
يرفض التحديث المعطل أو الوضع غير الملائم للعملية.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._load</code>
</td>
<td>
<pre>_load(self, cutoff, *, legacy=False)</pre>
</td>
<td>
يحمّل قطعًا دقيقًا من الجذر المناسب ويتحقق من حالته.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._active</code>
</td>
<td>
<pre>_active(self, control)</pre>
</td>
<td>
يطابق مؤشر النسخة النشطة مع بصمتها ودليل تفعيلها.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._compatible</code>
</td>
<td>
<pre>_compatible(self, snapshot, *, required=True)</pre>
</td>
<td>
يشترط فاحص توافق أصول الخدمة قبل النشر أو التفعيل.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore.status</code>
</td>
<td>
<pre>status(self)</pre>
</td>
<td>
يعرض الوضع الدائم والمؤشر والنسخ والمعاينة والفشل والتوافق، دون تغيير التاريخ.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore.set_mode</code>
</td>
<td>
<pre>set_mode(self, mode)</pre>
</td>
<td>
يحفظ الوضع الجديد ويمسح معاينة أصبحت خارج سياقها.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore.initialize</code>
</td>
<td>
<pre>initialize(self, *, source_root, expected_source_hash, approval_reference, confirmation=False, cumulative_history_confirmed=False)</pre>
</td>
<td>
يهيئ التبعيات بصورة مستقلة، أو يرحل أساس المخزن في صنف الإدارة حسب التوقيع.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._preview</code>
</td>
<td>
<pre>_preview(self, control, history_payload)</pre>
</td>
<td>
يبني معاينة مرتبطة بالبصمة والأساس والوضع.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore.preview</code>
</td>
<td>
<pre>preview(self, *, history_payload)</pre>
</td>
<td>
يتحقق ويخزن معاينة إدارية دون إنشاء نسخة.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._commit</code>
</td>
<td>
<pre>_commit(self, control, history_payload, token, approval_reference)</pre>
</td>
<td>
ينشر نسخة مطابقة لمعاينة واعتماد صحيحين، أو يتبنى نسخة مطابقة نُشرت قبل فشل المؤشر.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore.commit</code>
</td>
<td>
<pre>commit(self, *, history_payload, confirmation, approval_reference, preview_token=None, preview_sha256=None)</pre>
</td>
<td>
يشترط اليدوي والتأكيد ثم ينفذ نشرًا مستقلًا عن التفعيل.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore._activate</code>
</td>
<td>
<pre>_activate(self, control, cutoff, expected_history_sha256, *, rollback)</pre>
</td>
<td>
يطابق البصمة والسلسلة والتوافق ويبدل المؤشر فقط بعد الفحوص.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore.activate</code>
</td>
<td>
<pre>activate(self, *, cutoff, expected_history_sha256, confirmation, rollback=False)</pre>
</td>
<td>
يشترط اليدوي والتأكيد والرجوع الصريح عند القدم.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore.finalize</code>
</td>
<td>
<pre>finalize(self, *, history_payload, approval_reference, trusted_event=False)</pre>
</td>
<td>
ينسق المعاينة والنشر والتفعيل لحدث تثبيت موثوق فقط.
</td>
</tr>
<tr>
<td>
<code>CumulativeHistoryStore.capture</code>
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
<code>CumulativeHistoryStore.serving_manager</code>
</td>
<td>
<pre>serving_manager(self)</pre>
</td>
<td>
يعيد وكيل قراءة متوافقًا مع المحرك عندما يوجد مؤشر نشط صالح.
</td>
</tr>
<tr>
<td>
<code>_ServingHistoryManager.__init__</code>
</td>
<td>
<pre>__init__(self, store)</pre>
</td>
<td>
يحفظ التبعيات أو الحقول ويطبق فحوص البناء الموجودة؛ لا تفترض تحميل أصول ما لم يذكر مسار التهيئة ذلك.
</td>
</tr>
<tr>
<td>
<code>_ServingHistoryManager.capture</code>
</td>
<td>
<pre>capture(self, **kwargs)</pre>
</td>
<td>
يثبت نسخة واحدة، بالقطع المحدد أو المرجع النشط بحسب الواجهة.
</td>
</tr>
<tr>
<td>
<code>_ServingHistoryManager.preview_delta</code>
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
<code>_ServingHistoryManager.update_history_from_payload</code>
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
_approval

not isinstance(value, str) or not value.strip()
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
_confirmation

value is not True
```

## ٦. كيف تتغير البيانات؟

نسخة عبر نهاية ٢٠٢٥١ ثم دفعة ٢٠٢٥٢ تعطي نسخة تراكمية عبر ٢٠٢٥٢؛ يبقى المؤشر ٢٠٢٥١ حتى التفعيل. النسخة عبر ٢٠٢٦١ تستعمل أهدافًا بعده فقط.

## ٧. القواعد والافتراضات

الأوضاع معطل ويدوي وآلي عند التثبيت؛ اليدوي هو إعداد البداية. تغيير الوضع دائم بعد الحفظ. الرجوع يحتاج تصريحًا صريحًا ولا يحذف النسخ اللاحقة. النسخة الحالية تغطي جميع الفصول المعتمدة عبر القطع.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

إلغاء الربط ببصمة الأساس يسمح لتأكيد قديم بنشر على أساس تغير. تفعيل نسخة ناقصة أو غير متوافقة يغيّر التوقع. التاريخ النهائي لفصل لا يخدم الفصل نفسه.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [بناء وتحميل الحزم التاريخية الثابتة](../features/frozen_history.md)
- [مرجع المسارات والإصدارات](../paths.md)
- [مجاميع الدفعات ومدير اللقطة](history_update.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
pandas
msvcrt
fcntl
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[اختبار عبر وحدة وسيطة](../../../tests/test_cumulative_history.py)

```text
tests/test_cumulative_history.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_lazy_defaults_and_persistent_modes
test_approved_initialization_preserves_full_weighted_history_and_source
test_initialization_requires_exact_approved_cumulative_prefix
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert not root.exists()
```

## ١١. القيود المعروفة

المخزن منفذ لكنه غير مهيأ تشغيليًا في النسخة المحلية المفحوصة؛ لا مجلد تراكمي أو مؤشر فعلي. قفل الملفات آلية نشر محلي، وليس عقد توزيع عبر قواعد بيانات متعددة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- الأساس المعتمد تراكمي حتى نهاية أول فصل معتمد.
- النشر والتفعيل منفصلان، والمؤشر وحده يحدد النشط.
- الوضع الإداري دائم والتحديث مسلسَل والرجوع لا يحذف النسخ.

ثلاثة أسئلة للفهم:

1. كيف يثبت أن الأساس ليس نتائج فصل واحد فقط؟
2. لماذا لا تصبح النسخة المنشورة متاحة للخدمة قبل تفعيلها؟
3. ما الذي يبقى محفوظًا عند الرجوع إلى نسخة أقدم؟

تمرين قراءة آمن:

ارسم مجلدات ثلاث نسخ ومؤشرها، ثم حرك المؤشر على الورق إلى الأقدم مع بقاء جميع المجلدات.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
