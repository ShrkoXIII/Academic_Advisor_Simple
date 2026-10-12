# مرجع المسارات والإصدارات

```text
src/paths.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يجمع أسماء أصول البيانات والمودلات والتاريخ ويمنع توزيع مسارات متعارضة بين الطبقات.

الدور في الخريطة:
مشترك وأدوات

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [تنسيق التحقق والتوصية والإدارة](api/service.md)
- [الإعدادات ومصادرها البيئية](api/settings.md)
- [أدوات الهوية والأرقام والتشخيص الآمن](api/validation.md)
- [إنشاء سجل التسجيل الكامل](data/build_registration_roster.md)
- [ربط النتائج بحالة الطالب والخطة](data/build_student_course_enriched.md)
- [تقسيم التدريب والاختبار زمنيًا](data/build_temporal_split.md)
- [تنظيف كتالوج الاختصاص](data/clean_degree_course.md)
- [تدقيق القيم المتطرفة واستبعاد الطلاب](data/clean_outliers.md)

## ٣. المدخلات

إعدادات ثابتة وجذر المشروع، ورقم فصل وجذر اختياري للدوال التاريخية.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

## ٤. المخرجات

مسارات محلية وإصدارات مشتقة؛ لا قراءة أو كتابة ملفات عند استعمال دوال المسار.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

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
<code>versioned_path</code>
</td>
<td>
اشتقاق اسم ملف النسخة الثانية من مسار الأصل.
</td>
<td>
<pre>versioned_path(path, version='v2')</pre>
</td>
<td>
<pre>path.with_name(f'{path.stem}_{version}{path.suffix}')</pre>
</td>
<td>
لا نداء رمز مباشر محسوم في الفهرس؛ قد يكون واجهة عامة أو نداء كائن أو موضع اختبار.
</td>
</tr>
<tr>
<td>
<code>academic_part</code>
</td>
<td>
تحقق رقم فصل خماسي بنوع فصل مدعوم.
</td>
<td>
<pre>academic_part(value)</pre>
</td>
<td>
<pre>int(text)</pre>
</td>
<td>
<a href="api/validation.md">صفحة المستدعي</a>
<br>
<code>part</code>
<br>
<a href="features/build_frozen_history.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>previous_academic_part</code>
<br>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>validate_history_selection</code>
<br>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>validate_history_pair</code>
</td>
</tr>
<tr>
<td>
<code>frozen_history_dir</code>
</td>
<td>
مسار مجلد نسخة التاريخ للقطع المحدد.
</td>
<td>
<pre>frozen_history_dir(as_of_part, root=None)</pre>
</td>
<td>
<pre>Path(root if root is not None else FROZEN_HISTORY_DIR) / f'as_of_{academic_part(as_of_part)}'</pre>
</td>
<td>
<a href="features/build_frozen_history.md">صفحة المستدعي</a>
<br>
<code>main</code>
<br>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history</code>
<br>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history_atomic</code>
<br>
<a href="paths.md">صفحة المستدعي</a>
<br>
<code>course_history_state_path</code>
<br>
<a href="paths.md">صفحة المستدعي</a>
<br>
<code>specialty_history_state_path</code>
</td>
</tr>
<tr>
<td>
<code>course_history_state_path</code>
</td>
<td>
مسار حالة تاريخ المادة داخل النسخة.
</td>
<td>
<pre>course_history_state_path(as_of_part, root=None)</pre>
</td>
<td>
<pre>frozen_history_dir(as_of_part, root) / 'course_history_state.pkl'</pre>
</td>
<td>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history</code>
<br>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>load_frozen_history</code>
</td>
</tr>
<tr>
<td>
<code>specialty_history_state_path</code>
</td>
<td>
مسار حالة تاريخ الاختصاص الاختياري.
</td>
<td>
<pre>specialty_history_state_path(as_of_part, root=None)</pre>
</td>
<td>
<pre>frozen_history_dir(as_of_part, root) / 'specialty_history_state.pkl'</pre>
</td>
<td>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history</code>
<br>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>load_frozen_history</code>
</td>
</tr>
<tr>
<td>
<code>history_metadata_path</code>
</td>
<td>
مسار علامة اكتمال الحزمة وبيانات مصدرها.
</td>
<td>
<pre>history_metadata_path(as_of_part, root=None)</pre>
</td>
<td>
<pre>frozen_history_dir(as_of_part, root) / 'metadata.json'</pre>
</td>
<td>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history</code>
<br>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>load_frozen_history</code>
<br>
<a href="features/frozen_history.md">صفحة المستدعي</a>
<br>
<code>save_frozen_history_atomic</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
versioned_path
```

يشتق أسماء النسخة الثانية من الأصل، ويتحقق من رقم الفصل ثم يصنع مسارات مجلد النسخة وحالتها وبياناتها الوصفية.

## ٦. كيف تتغير البيانات؟

التحول الرئيسي هو من المدخل الموصوف إلى المخرج الموصوف عبر الخطوات أعلاه. لم تتوفر عينة مستقلة موثقة تصلح لعرض قيم أكاديمية كاملة لهذا الملف؛ لذلك لا تُختلق بيانات جامعة أو درجات مودل.

## ٧. القواعد والافتراضات

يشتق أسماء النسخة الثانية من الأصل، ويتحقق من رقم الفصل ثم يصنع مسارات مجلد النسخة وحالتها وبياناتها الوصفية.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

خلط مسار النسخة الأولى بالثانية يغير البيانات والمودل والتاريخ رغم تشابه الأسماء.

لم يجر تعديل سلوك هذا الملف. المخاطر المذكورة حدود تفسير واستخدام وليست إعلانًا عن عطل جديد.

## ٩. التبعيات

لا توجد استيرادات داخلية من وحدات المشروع في هذا الملف.


مراجع خارج شجرة المصدر تستورد هذه الوحدة؛ ليست دليل تشغيل إنتاج:
[الأداة المرجعية](../../scripts/experiments/attempt_number_experiment.py)

```text
scripts/experiments/attempt_number_experiment.py
```

[الأداة المرجعية](../../scripts/experiments/attempt_number_recommendation.py)

```text
scripts/experiments/attempt_number_recommendation.py
```

[الأداة المرجعية](../../scripts/experiments/attempt_number_removal_recheck.py)

```text
scripts/experiments/attempt_number_removal_recheck.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../tests/test_evaluation_v2_io.py)

```text
tests/test_evaluation_v2_io.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_plan_evaluation_reads_and_writes_v2_with_shared_grade_scale
test_error_analysis_uses_v2_in_historical_holdout_and_shap_paths
test_missing_v2_input_fails_without_v1_fallback_or_output
```

[ملف اختبار مرتبط](../../tests/test_experiment_io.py)

```text
tests/test_experiment_io.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_signature_hashes_current_dependencies_deterministically
test_validation_cache_reuses_only_matching_signature
test_metadata_retains_protocol_and_artifact_contract
```

[ملف اختبار مرتبط](../../tests/test_experiments_v2_io.py)

```text
tests/test_experiments_v2_io.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_coordinator_uses_v2_baseline_cache_outputs_and_metadata_candidate
test_missing_v2_input_fails_without_using_v1
test_path_constants_are_v2_and_grade_scale_is_shared
```

[ملف اختبار مرتبط](../../tests/test_frozen_history.py)

```text
tests/test_frozen_history.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_new_version_preserves_original_hashes_and_values
test_history_selection_requires_explicit_stale_opt_in
test_legacy_optional_course_specialty_mismatch_refused_by_save_and_load
```

## ١١. القيود المعروفة

وجود ثابت لمسار لا يعني وجود الملف أو أنه يُستخدم في الطلب الحالي.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- مسؤولية الملف: يجمع أسماء أصول البيانات والمودلات والتاريخ ويمنع توزيع مسارات متعارضة بين الطبقات.
- مدخله ومخرجه مرتبطان بالدور المبين؛ لا تستعمله بدل طبقة التحقق المجاورة.
- أهم حد عملي: وجود ثابت لمسار لا يعني وجود الملف أو أنه يُستخدم في الطلب الحالي.

ثلاثة أسئلة للفهم:

1. ما الدليل المطلوب لصحة المدخل قبل استعمال هذا الملف؟
2. أي وحدة تستهلك المخرج، وما الذي يجب أن يظل ثابتًا عند انتقاله؟
3. أين يحدث الرفض أو الفقدان، وما الفرق بينهما في هذا المسار؟

تمرين قراءة آمن:

تتبع على الورق مدخلًا صغيرًا إلى المخرج عبر التسلسل أعلاه، وافتح تعريفًا واحدًا واختبارًا مرتبطًا لتحديد شرط رفضه. لا تنفذ نقطة تدريب أو توصية ولا تحفظ أو تفعّل تاريخًا.

