# بناء وتحميل الحزم التاريخية الثابتة

```text
src/features/frozen_history.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يفصل نسخة تاريخ الخدمة النهائية عن أصول التدريب، ويضمن أن اسم القطع والبيانات والبصمات تصف النسخة نفسها.

الدور في الخريطة:
ميزات مشتركة

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق التحقق والتوصية والإدارة](../api/service.md)
- [تحويل الطالب إلى لقطة بداية الفصل](../api/student_adapter.md)
- [أدوات تجربة رقم المحاولة](../experiments/attempt_number_core.md)
- [ملاءمة صيغ تجربة المحاولة](../experiments/attempt_number_training.md)
- [حساب البحث على ميزات المادة فقط](../experiments/course_only_core.md)
- [مقارنة تجربة المادة بالمحرك المحلي](../experiments/course_only_evaluation.md)
- [تدريب تجربة المواد المستقلة](../experiments/course_only_training.md)
- [تدريب الحالة السابقة كميزة إضافية](../experiments/previous_course_status_training.md)
- [أداة إنشاء لقطة نهائية محددة](build_frozen_history.md)
- [تحميل أصول المحرك المحلي الرسمي](../recommendation/artifacts.md)
- [الإدارة الدائمة للتاريخ التراكمي](../recommendation/cumulative_history.md)
- [المحرك المحلي ذو الزوج الواحد](../recommendation/engine.md)
- [مجاميع الدفعات ومدير اللقطة](../recommendation/history_update.md)
- [تحميل أصول المرحلتين والتحقق من مصدرها](../recommendation/two_stage_artifacts.md)
- [تنسيق تجربة توصيات الحالة السابقة](../recommendation_experiments/previous_course_status_experiment.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [العقد المرتب لميزات المودل](feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](temporal_features.md)
- [مرجع المسارات والإصدارات](../paths.md)

## ٣. المدخلات

نتائج نهائية عبر قطع مصرح به عند البناء، أو جذر وقطع محددان عند القراءة. التاريخ الرسمي الجديد أساسي فقط، وتاريخ الاختصاص التجريبي اختياري للواجهات القديمة الصريحة.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

أسماء الحقول المعرّفة في الملف:

```text
HISTORY_SOURCE_COLUMNS
student_course_id
part_id
degree_id
course_id
faculty_id
plan_requirement_type_id
course_credits
attempt_number
final_mark
```

الأنواع والبنى المستعملة في هذا الحد:

```text
outcomes: pandas.DataFrame
as_of_part / finalized_through_part: academic parts
root: optional Path-compatible
```

## ٤. المخرجات

حالة تاريخ ومصدر، أو مجلد نسخة يحتوي حالة ومؤشر اكتمال ببيانات وصفية وبصمات. الحفظ الذري يعيد حالة أعيد تحميلها والتحقق منها.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أنواع المخرجات الأساسية:

```text
build_frozen_history -> (CourseHistoryState, optional specialty, dict)
load_frozen_history -> (CourseHistoryState, optional specialty, dict)
save_frozen_history_atomic -> (CourseHistoryState, dict)
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
<code>file_sha256</code>
</td>
<td>
حساب بصمة محتوى ملف.
</td>
<td>
<pre>file_sha256(path)</pre>
</td>
<td>
<pre>digest.hexdigest()</pre>
</td>
<td>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>select_batch_cases</code>
<br>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>run_comparisons</code>
<br>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>capture_protected_files</code>
<br>
<a href="../experiments/course_only_evaluation.md">صفحة المستدعي</a>
<br>
<code>verify_protected_files</code>
<br>
<a href="../experiments/course_only_training.md">صفحة المستدعي</a>
<br>
<code>training_signature</code>
</td>
</tr>
<tr>
<td>
<code>previous_academic_part</code>
</td>
<td>
حساب الفصل الأكاديمي السابق وفق الرزنامة.
</td>
<td>
<pre>previous_academic_part(target_part)</pre>
</td>
<td>
<pre>target - 1 if target % 10 &gt; 1 else (target // 10 - 1) * 10 + 3</pre>
</td>
<td>
<a href="../api/student_adapter.md">صفحة المستدعي</a>
<br>
<code>adapt_student</code>
<br>
<a href="../api/student_adapter.md">صفحة المستدعي</a>
<br>
<code>_official_gpa_credits</code>
<br>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>validate_history_selection</code>
<br>
<a href="../recommendation/cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._preview</code>
<br>
<a href="../recommendation/cumulative_history.md">صفحة المستدعي</a>
<br>
<code>_ServingHistoryManager.preview_delta</code>
</td>
</tr>
<tr>
<td>
<code>validate_history_selection</code>
</td>
<td>
التحقق من علاقة قطع التاريخ بالهدف ووضع القدم.
</td>
<td>
<pre>validate_history_selection(target_part, history_as_of_part, *, allow_older_history=False)</pre>
</td>
<td>
<pre>{'target_part': target, 'history_as_of_part': cutoff, 'previous_academic_part': previous, 'history_is_previous_part': cutoff == previous, 'allow_older_history': bool(allow_older_history)}</pre>
</td>
<td>
<a href="../api/service.md">صفحة المستدعي</a>
<br>
<code>ApiService.recommend</code>
<br>
<a href="../experiments/course_only_core.md">صفحة المستدعي</a>
<br>
<code>prepare_course_rows</code>
<br>
<a href="../recommendation/cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.capture</code>
<br>
<a href="../recommendation/engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.prepare_candidates</code>
<br>
<a href="../recommendation/engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.recommend</code>
</td>
</tr>
<tr>
<td>
<code>validate_history_pair</code>
</td>
<td>
اشتراط قطع موحد للحالة الأساسية والاختيارية.
</td>
<td>
<pre>validate_history_pair(course, specialty, as_of_part)</pre>
</td>
<td>
لا يعيد قيمة صريحة؛ أثره أو ملفاته موضحة في قسم المخرجات.
</td>
<td>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>build_frozen_history</code>
<br>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history</code>
<br>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>load_frozen_history</code>
<br>
<a href="../experiments/course_only_core.md">صفحة المستدعي</a>
<br>
<code>prepare_course_rows</code>
<br>
<a href="../recommendation/engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.__init__</code>
</td>
</tr>
<tr>
<td>
<code>build_frozen_history</code>
</td>
<td>
بناء كامل بادئة النتائج النهائية حتى القطع المطلوب.
</td>
<td>
<pre>build_frozen_history(outcomes, as_of_part, *, finalized_through_part, specialty_history_type=None, dataset_version=None)</pre>
</td>
<td>
<pre>(course, specialty, metadata)</pre>
</td>
<td>
<a href="build_frozen_history.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>verify_legacy_course_history</code>
</td>
<td>
مقارنة حالة أصل قديم مع إعادة بناء موثقة.
</td>
<td>
<pre>verify_legacy_course_history(legacy_path, rebuilt)</pre>
</td>
<td>
<pre>legacy</pre>
</td>
<td>
<a href="build_frozen_history.md">صفحة المستدعي</a>
<br>
<code>main</code>
</td>
</tr>
<tr>
<td>
<code>save_frozen_history</code>
</td>
<td>
حجز وحفظ نسخة جديدة لا تستبدل الموجودة.
</td>
<td>
<pre>save_frozen_history(course, specialty, metadata, *, root=None)</pre>
</td>
<td>
<pre>payload</pre>
</td>
<td>
<a href="build_frozen_history.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history_atomic</code>
</td>
</tr>
<tr>
<td>
<code>load_frozen_history</code>
</td>
<td>
تحميل القطع الدقيق بعد فحص الإصدار والبصمات.
</td>
<td>
<pre>load_frozen_history(as_of_part, *, root=None, specialty_history_type=None, dataset_version=None)</pre>
</td>
<td>
<pre>(course, specialty, provenance)</pre>
</td>
<td>
<a href="build_frozen_history.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history_atomic</code>
<br>
<a href="../recommendation/artifacts.md">صفحة المستدعي</a>
<br>
<code>load_recommendation_artifacts</code>
<br>
<a href="../recommendation/cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore._load</code>
<br>
<a href="../recommendation/cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.initialize</code>
</td>
</tr>
<tr>
<td>
<code>save_frozen_history_atomic</code>
</td>
<td>
حفظ مرحلي وإعادة تحقق ونشر حصري للنسخة.
</td>
<td>
<pre>save_frozen_history_atomic(course, metadata, *, root=None)</pre>
</td>
<td>
<pre>(loaded, provenance)</pre>
</td>
<td>
<a href="../recommendation/cumulative_history.md">صفحة المستدعي</a>
<br>
<code>CumulativeHistoryStore.initialize</code>
<br>
<a href="../recommendation/history_update.md">صفحة المستدعي</a>
<br>
<code>FrozenHistoryManager.update_history_from_payload</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
previous_academic_part / validate_history_selection
```

يحسب السابق بالرزنامة ذات ثلاثة فصول، ويرفض تداخل الهدف أو تاريخًا أقدم دون تصريح.

خطوة 2:

```text
build_frozen_history
```

يفحص أعمدة النتائج والنهائية والفصل الفعلي والهوية الفريدة؛ يختار كامل بادئة النتائج عبر القطع ثم يحدث الحالة زمنيًا.

خطوة 3:

```text
save_frozen_history
```

يحجز مجلدًا جديدًا حصريًا ويكتب الحالة ثم بيانات الاكتمال أخيرًا؛ الموجود لا يستبدل.

خطوة 4:

```text
load_frozen_history
```

يفحص المصدر والإصدار والقطع وبصمات الملفات ثم يحمّل الحالة؛ طلب النسخة الثانية يمنع تاريخ الاختصاص.

خطوة 5:

```text
save_frozen_history_atomic
```

ينشر فقط بعد حفظ مرحلي وإعادة تحميل وتطابق المجاميع والجداول؛ النقل إلى اسم النسخة لا يستخدم الاستبدال.

خطوة 6:

```text
verify_legacy_course_history
```

يقارن نسخة سابقة بحالة معاد بناؤها لأجل ترحيل مطابق، دون تعديل الأصل.

### علامة اكتمال النسخة

اسم المجلد ليس كافيًا. بياناته الوصفية يجب أن تتوافق مع القطع الفعلي وإصدار الميزات وآخر فصل نهائي وبصمة كل ملف.

```text
as_of_<part>/
  course_history_state.pkl
  metadata.json
```

تاريخ الاختصاص الاختياري يخص الواجهات القديمة الصريحة. الحزمة الرسمية الثانية لا تحتويه وتُرفض إذا ظهرت فيها آثاره.

النشر الذري يبني تحت مجلد مؤقت في نظام الملفات نفسه، يعيد القراءة ويقارن الجداول والمجاميع، يحجز اسم النشر حصريًا، ثم ينقل مجلد النسخة. تنظيف مؤقت فاشل بعد نشر صحيح يصبح تنبيه تنظيف ولا يلغي النجاح.

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
file_sha256

iter(lambda: stream.read(1024 * 1024), b'')
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
validate_history_selection

cutoff >= target
cutoff != previous and (not allow_older_history)
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
validate_history_pair

course.as_of_part != cutoff or (specialty is not None and specialty.as_of_part != cutoff)
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
build_frozen_history

dataset_version not in (None, 'V2')
dataset_version == 'V2'
cutoff > finalized
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
verify_legacy_course_history

rebuilt.tables
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
save_frozen_history

metadata.get('dataset_version') == 'V2'
metadata.get('source_max_part') != cutoff
finalized < cutoff
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
load_frozen_history

dataset_version not in (None, 'V2')
dataset_version == 'V2'
dataset_version is not None and metadata.get('dataset_version') != dataset_version
```

## ٦. كيف تتغير البيانات؟

اختيار قطع ٢٠٢٥١ من مصدر يتضمن فصولًا لاحقة لا يضيفها. غياب نتائج القطع نفسه يرفض البناء بدل إنتاج نسخة باسم غير مطابق.

## ٧. القواعد والافتراضات

القطع يحدد نهاية تاريخ نهائي، والهدف بعده. التاريخ الأساسي لا يحتاج نقاطًا تقديرية. بيانات الاكتمال تُكتب بعد الملفات.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

الاسم وحده ليس إثبات تاريخ صحيح. الملفات التسلسلية من مصدر غير موثوق غير آمنة. حزمة فاشلة أو بصمة مختلفة لا تُحمّل.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [العقد المرتب لميزات المودل](feature_contract.md)
- [هندسة الميزات الزمنية المشتركة](temporal_features.md)
- [مرجع المسارات والإصدارات](../paths.md)

تبعيات خارجية مهمة بحسب الاستيراد، وليست كلها لازمة لاستيراد الحزمة العامة:

```text
numpy
pandas
```


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../../scripts/experiments/attempt_number_experiment.py)

```text
scripts/experiments/attempt_number_experiment.py
```

[الأداة المرجعية](../../../scripts/experiments/attempt_number_removal_recheck.py)

```text
scripts/experiments/attempt_number_removal_recheck.py
```

[الأداة المرجعية](../../../scripts/experiments/student_progress_20261010/downstream.py)

```text
scripts/experiments/student_progress_20261010/downstream.py
```

[الأداة المرجعية](../../../scripts/experiments/student_progress_20261010/evidence/executed_workflow.py)

```text
scripts/experiments/student_progress_20261010/evidence/executed_workflow.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_api_cumulative_integration.py)

```text
tests/test_api_cumulative_integration.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_http_migration_manual_auto_rollback_and_existing_pareto_contract
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert status['active_as_of_part'] == 20251
```

[ملف اختبار مرتبط](../../../tests/test_cumulative_history.py)

```text
tests/test_cumulative_history.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_approved_initialization_preserves_full_weighted_history_and_source
test_preview_commit_activation_separate_and_sequential_raw_equivalence
test_rollback_exact_selection_and_reload_do_not_delete_later_versions
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert loaded.global_sums == baseline.global_sums
```

[ملف اختبار مرتبط](../../../tests/test_frozen_history.py)

```text
tests/test_frozen_history.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_new_version_preserves_original_hashes_and_values
test_target_and_future_outcomes_cannot_enter_prefix
test_prefix_fingerprint_survives_row_order_and_future_dtype_change
```

[ملف اختبار مرتبط](../../../tests/test_frozen_history_v2.py)

```text
tests/test_frozen_history_v2.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_v2_load_default_uses_isolated_root_and_missing_v2_never_falls_back
test_v2_rejects_unversioned_or_wrong_version_bundle
test_v2_rejects_specialty_artifacts_without_opening_them
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert loaded.global_sums['raw_count'] == 2
```

[ملف اختبار مرتبط](../../../tests/test_history_update.py)

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

[ملف اختبار مرتبط](../../../tests/test_recommendation_inputs_v2.py)

```text
tests/test_recommendation_inputs_v2.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_local_loader_reads_only_cleaned_v2_and_preserves_history
test_local_missing_v2_fails_without_legacy_fallback
test_local_supplied_snapshot_reads_only_v2_catalog_and_attempts
```

قضية فعلية يفحصها أحد هذه الاختبارات:

```python
assert set(reads) == set(paths.values())
```

## ١١. القيود المعروفة

منشئ الحزمة يعتمد شهادة المستدعي على النهائية. الحفظ المعتاد قد يترك مجلدًا ناقصًا غير قابل للتحميل؛ الحفظ الذري يخفي المرحلة المؤقتة.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- القطع التاريخي دقيق ولا يستبدل بنسخة أقرب صامتة.
- الحزمة تراجع الإصدار والبصمات ومجاميعها.
- الحفظ الذري لا يكتب فوق نسخة مكتملة قائمة.

ثلاثة أسئلة للفهم:

1. ما الفرق بين نهاية التدريب ونهاية التاريخ المسموح للهدف؟
2. متى يحتاج التاريخ الأقدم إلى وضع اختبار تاريخي مصرح؟
3. كيف يظل المجلد النهائي غير ظاهر أثناء الكتابة المرحلية؟

تمرين قراءة آمن:

حدد على الورق القطع السابق لأهداف في الفصول الأول والثاني والثالث، وفسر رفض لقطة الهدف نفسه.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
