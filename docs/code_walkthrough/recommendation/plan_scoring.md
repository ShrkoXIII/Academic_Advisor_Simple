# توقع المواد وتلخيص جودة الخطط

```text
src/recommendation/plan_scoring.py
```

هذه الصفحة تصف الشفرة الموجودة في النسخة المفحوصة. الشفرة لم تُشغّل لتوليد توصية أو تدريب أثناء إعداد الشرح.

[العودة إلى مسار التعلم](../00_START_HERE.md)

## ١. لماذا يوجد هذا الملف؟

يجمع الحسابات المشتركة للتوقع ومعدل الخطة والمعدل التراكمي المتوقع، كي تستخدمها المرحلتان والمحرك المحلي بتعريف واحد.

الدور في الخريطة:
نواة التوصية

تصنيف الاستعمال:
نشط في مسار خدمة أو بناء أو تقييم أو أداة موثقة

## ٢. أين يقع في النظام؟

ما قبل هذه الوحدة يُعرف من الاستدعاءات والاستيرادات المباشرة؛ الاستيراد وحده لا يثبت تنفيذًا في كل طلب.

- [حساب البحث على ميزات المادة فقط](../experiments/course_only_core.md)
- [تصدير واجهات نواة التوصية](__init__.md)
- [المحرك المحلي ذو الزوج الواحد](engine.md)
- [قائمة الخطط المختصرة للمرحلة الأولى](shortlist.md)
- [المحرك المعتمد ذو المرحلتين](two_stage_engine.md)
- [مقارنة توقعات وخطط الحالة السابقة](../recommendation_experiments/previous_course_status_inference.md)

الوحدات التي يعتمد عليها بعد ذلك:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)

## ٣. المدخلات

صفوف مواد مع عقد الميزات المناسب، زوج مودلات، مستويات الفئات وسلم العلامات، ثم معدل سابق ومقام تسجيل سابق.

تواقيع الجدول أدناه مأخوذة من تعريفات الملف. نوع أو دلالة حقل لا يظهر في التوقيع يُفسر من الحسابات وشروط التحقق، ولا يفترض من الاسم وحده.

أسماء الحقول المعرّفة في الملف:

```text
SUMMARY_COLUMNS
plan_id
course_count
total_credits
expected_quality_points
expected_plan_gpa
projected_cumulative_gpa
expected_cumulative_gpa_gain
is_expected_cumulative_improvement
expected_failed_credits
projected_gpa_requires_repeat_policy
gpa_gain
```

أسماء الحقول المعرّفة في الملف:

```text
COURSE_OUTPUT_COLUMNS
plan_id
course_id
course_name
course_credits
predicted_mark
expected_points
expected_grade
fail_probability
```

الأنواع والبنى المستعملة في هذا الحد:

```text
rows: pandas.DataFrame
grade_model / fail_model: predict-capable models
category_levels: dict
grade_scale: GradeScale
```

## ٤. المخرجات

صفوف بمارك متوقع ونقاط وسلم واحتمال رسوب، وجداول تلخيص فيها ساعات الخطة وجودتها وساعات الرسوب المتوقعة والمعدل التراكمي.

مخرجات كل تابع التي تعاد صراحةً تظهر في جدول التعريفات. التعبير المعروض مقتطف من مسار إرجاع فعلي؛ ليس بديلًا عن شروط الوصول إليه.

أعمدة الملخص وأعمدة مواد النتيجة الفعلية:

```text
SUMMARY_COLUMNS
plan_id
course_count
total_credits
expected_quality_points
expected_plan_gpa
projected_cumulative_gpa
expected_cumulative_gpa_gain
is_expected_cumulative_improvement
expected_failed_credits
projected_gpa_requires_repeat_policy
gpa_gain

COURSE_OUTPUT_COLUMNS
plan_id
course_id
course_name
course_credits
predicted_mark
expected_points
expected_grade
fail_probability
```

أنواع المخرجات الأساسية:

```text
score_course_rows(...) -> pandas.DataFrame
summarize_scored_plans(...) -> pandas.DataFrame
project_cumulative_gpa(...) -> numpy result (scalar or vector)
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
<code>score_course_rows</code>
</td>
<td>
توقع العلامة والرسوب وتحويل النقاط مع فحص المدى والشكل.
</td>
<td>
<pre>score_course_rows(rows, grade_model, fail_model, category_levels, grade_scale, *, features=None, num_threads=4)</pre>
</td>
<td>
<pre>rows</pre>
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender._score_stage2</code>
<br>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.recommend_from_payloads</code>
<br>
<a href="engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.score_rows</code>
</td>
</tr>
<tr>
<td>
<code>rank_plans</code>
</td>
<td>
الترتيب الأكاديمي المرجعي للمحرك المحلي.
</td>
<td>
<pre>rank_plans(summaries)</pre>
</td>
<td>
<pre>summaries.sort_values(['projected_cumulative_gpa', 'expected_failed_credits', 'expected_plan_gpa', 'plan_id'], ascending=[False, True, False, True], kind='stable').reset_index(drop=True)</pre>
</td>
<td>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
<br>
<a href="engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.recommend</code>
<br>
<a href="plan_scoring.md">صفحة المستدعي</a>
<br>
<code>summarize_scored_plans</code>
</td>
</tr>
<tr>
<td>
<code>project_cumulative_gpa</code>
</td>
<td>
حساب تراكمي إضافي بمقام سابق موثق.
</td>
<td>
<pre>project_cumulative_gpa(current_gpa, current_gpa_credits, expected_quality_points, plan_total_credits)</pre>
</td>
<td>
<pre>(gpa * credits + quality) / (credits + plan_credits)</pre>
</td>
<td>
<a href="../experiments/course_only_core.md">صفحة المستدعي</a>
<br>
<code>optimize_exact_credits</code>
<br>
<a href="plan_scoring.md">صفحة المستدعي</a>
<br>
<code>summarize_scored_plans</code>
<br>
<a href="shortlist.md">صفحة المستدعي</a>
<br>
<code>build_stage1_shortlist</code>
</td>
</tr>
<tr>
<td>
<code>summarize_scored_plans</code>
</td>
<td>
جمع جودة وساعات رسوب ومعدلات كل خطة.
</td>
<td>
<pre>summarize_scored_plans(scored_courses, current_gpa, current_gpa_credits)</pre>
</td>
<td>
<pre>rank_plans(summary[SUMMARY_COLUMNS])</pre>
</td>
<td>
<a href="two_stage_engine.md">صفحة المستدعي</a>
<br>
<code>TwoStagePlanRecommender.recommend_from_payloads</code>
<br>
<a href="../recommendation_experiments/previous_course_status_inference.md">صفحة المستدعي</a>
<br>
<code>run_student_comparison</code>
<br>
<a href="engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.recommend</code>
</td>
</tr>
<tr>
<td>
<code>empty_summaries</code>
</td>
<td>
جدول ملخص فارغ بالأنواع المناسبة.
</td>
<td>
<pre>empty_summaries()</pre>
</td>
<td>
<pre>pd.DataFrame({c: pd.Series(dtype='bool' if c in ['is_expected_cumulative_improvement', 'projected_gpa_requires_repeat_policy'] else 'int64' if c in ['plan_id', 'course_count'] else 'float64') for c in SUMMARY_COLUMNS})</pre>
</td>
<td>
<a href="engine.md">صفحة المستدعي</a>
<br>
<code>AcademicPlanRecommender.recommend</code>
</td>
</tr>
</tbody>
</table>

### تسلسل المنطق وأسباب الخطوات

خطوة 1:

```text
score_course_rows
```

ينشئ مصفوفة مرتبة بالعقد، يتوقع العلامة والرسوب، يفحص الشكل والقيم ثم يقص العلامة والاحتمال في مداهما.

خطوة 2:

```text
GradeScale.convert
```

يحوّل العلامة المتوقعة إلى نقاط؛ لا يضرب النقاط في احتمال النجاح.

خطوة 3:

```text
summarize_scored_plans
```

يجمع حاصل الساعات والنقاط والجمع المرجح باحتمال الرسوب حسب الخطة.

خطوة 4:

```text
project_cumulative_gpa
```

يجمع جودة الخطة مع جودة الماضي تحت مقام تسجيل موثق؛ الحساب إضافي بلا استبدال درجة إعادة.

خطوة 5:

```text
rank_plans
```

ترتيب مرجعي للمحرك المحلي؛ المحرك ذو المرحلتين يستعمل ترتيب سياسته المستقلة.

### الحسابات المشتركة

```text
quality_points = sum(course_credits * expected_points)
expected_failed_credits = sum(course_credits * fail_probability)
expected_plan_gpa = quality_points / total_credits
projected_cumulative_gpa = (current_gpa * current_gpa_credits + quality_points) / (current_gpa_credits + total_credits)
```

احتمال الرسوب بعد مستقل، ولا يقلل نقاط المادة داخل صيغة المعدل. هذه التعريفات نفسها تستعملها مرحلتا النواة.

الحقل القديم لفجوة المعدل الفصلي محفوظ للتوافق، لكنه ليس التحسن التراكمي.

```text
gpa_gain = expected_plan_gpa - current_gpa
expected_cumulative_gpa_gain = projected_cumulative_gpa - current_gpa
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
score_course_rows

marks.shape != (len(rows),) or failures.shape != (len(rows),)
not np.isfinite(marks).all() or not np.isfinite(failures).all()
not np.isfinite(rows[['expected_points', 'fail_probability']].to_numpy()).all()
```

شروط تحكم فعلية للتابع التالي؛ يتحدد أثرها من تسلسل التحقق المشرح:

```text
project_cumulative_gpa

not np.isfinite([gpa, credits]).all() or not 0 <= gpa <= 4 or credits < 0
```

## ٦. كيف تتغير البيانات؟

مثال تعليمي لتوقعات مفترضة: ثلاث ساعات بنقاط ثلاثة وثلاث ساعات بنقاط أربعة تعطي جودة إحدى وعشرين ومعدل خطة ثلاثة ونصف. مع معدل سابق ثلاثة ومقام ثلاثين يكون التراكمي مئة وإحدى عشرة على ست وثلاثين.

## ٧. القواعد والافتراضات

جودة الخطة مجموع الساعات في النقاط. ساعات الرسوب المتوقعة مجموع الساعات في احتمال الرسوب. وجود إعادة يضع تنبيه الحاجة إلى سياسة استبدال.

- القواعد الأكاديمية المؤكدة يُصرح بها عند توفر مصدرها؛ وجود شرط في الكود لا يمنحه اعتمادًا جامعيًا جديدًا.
- السياسات القابلة للإعداد والمصادر الخارجية يجب قراءتها مع صفحة الخدمة أو التدريب بحسب المسار.
- الدقة العددية والتفرد وترتيب الفصول افتراضات تقنية يفحصها الملف أو حدوده المجاورة.

## ٨. مخاطر التسرب والصحة

استعمال ساعات النجاح مقامًا للتراكمي أو وزن النقاط باحتمال النجاح يغيّر التعريف. مخرجات مودل غير محدودة أو بطول مختلف تُرفض.

أي قيمة أو قطع غير مطابق يجب أن يرفض أو يسجل غير متاح حسب العقد، قبل تحويله إلى توقع. لا تعالج هذه الصفحة نقص المصدر بتغيير ميزة أو وضع قيمة افتراضية.

## ٩. التبعيات

الاستيرادات الداخلية الموجودة في الشفرة، بما فيها ما قد يحدث عند استدعاء وظيفة فقط:

- [العقد المرتب لميزات المودل](../features/feature_contract.md)

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

[الأداة المرجعية](../../../scripts/experiments/attempt_number_recommendation.py)

```text
scripts/experiments/attempt_number_recommendation.py
```

## ١٠. الاختبارات

[فهرس الاختبارات وعلاقتها بالشفرة](../05_TEST_INDEX.md)

لم تُشغّل الاختبارات في مهمة التوثيق. آخر سجل متاح يذكر ألفًا وثلاثمئة وتسعة وستين اختبارًا وستة اختبارات فرعية ناجحة؛ السجل لا يثبت تشغيلًا جديدًا لهذه الصفحة.

[ملف اختبار مرتبط](../../../tests/test_local_recommendation.py)

```text
tests/test_local_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_mixed_credit_totals_rank_by_gpa_not_quality_point_sum
test_gpa_improvement_flag_and_risk_only_tiebreak
```

[ملف اختبار مرتبط](../../../tests/test_projected_recommendation.py)

```text
tests/test_projected_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_additive_example_and_zero_prior_credits
test_invalid_or_unknown_denominators_are_rejected
test_larger_load_can_win_despite_lower_semester_gpa
```

[ملف اختبار مرتبط](../../../tests/test_recommendation.py)

```text
tests/test_recommendation.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_ranking_uses_gpa_then_failure_without_risk_exclusion
```

[ملف اختبار مرتبط](../../../tests/test_two_stage_engine.py)

```text
tests/test_two_stage_engine.py
```

أسماء أمثلة من الاختبارات الموجودة:

```text
test_stage_two_context_matrix_predictions_and_summaries_match_legacy_path
test_pinned_official_stage_two_models_match_legacy_on_identical_synthetic_plans
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

المعدل المتوقع تقريبي وإضافي؛ لا يفترض قواعد استبدال جامعية. الترتيب المرجعي هنا لا يعني أنه ترتيب واجهة المرحلتين النهائي.

العلاقات المستخرجة من الاستيراد لا تثبت حركة طلب حي. تم تمييز مسار الخدمة والبناء والتقييم والتجربة من المستدعين ونقاط التنفيذ، لا من وجود الملف فقط.

## ١٢. مراجعة سريعة

ثلاث خلاصات:

- العلامة المتوقعة تتحول إلى نقاط عبر سلم العلامات.
- مخاطر الرسوب والنقاط تقديران منفصلان.
- المعدل التراكمي المتوقع يحتاج مقامًا سابقًا موثوقًا.

ثلاثة أسئلة للفهم:

1. كيف تدخل ساعات المادة في نقاط الخطة وساعات الرسوب المتوقعة؟
2. لماذا لا يستبدل احتمال الرسوب بتحويل العلامة وحده؟
3. أين يظهر افتراض الجمع الإضافي في التراكمي المتوقع؟

تمرين قراءة آمن:

باستخدام ساعات ونقاط واحتمالات تعليمية، احسب معدل خطة ومجموع ساعات الرسوب المتوقعة ثم راجع صيغ الملف.

التمرين قراءة وحساب على الورق؛ لا يغير المشروع ولا يشغّل بناءً أو توقعًا أو تحديث تاريخ.
