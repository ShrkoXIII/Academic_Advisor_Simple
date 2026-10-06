# COURSE-ONLY 33-FEATURE EXPERIMENT

**Recommendation: KEEP EXPERIMENTAL.** أثر حذف السياق على مقاييس المودلين صغير، وتقليل صفوف التنبؤ كبير. لكن تطابق أفضل الخطط منخفض، والتسريع الفعلي محدود بكلفة البحث الشامل. لا تكفي هذه العينة لترقية النظام. لم تتم أي promotion أو كتابة فوق artifacts رسمية.

## Requested final summary

```text
COURSE-ONLY 33-FEATURE EXPERIMENT

Features:
Official: 47
Experimental: 33
Removed plan/peer features: 14

Grade:
Official test MAE: 9.707697595
Experimental test MAE: 9.718016591
Delta: +0.010318996

Fail:
Official LogLoss: 0.274022790
Experimental LogLoss: 0.275495015
Delta: +0.001472225
Official PR-AUC: 0.305109961
Experimental PR-AUC: 0.299132432
Delta: -0.005977530

Plan-context sensitivity (80 student-course pairs in six additional test scenarios):
Median predicted-mark range: 0.444743136
P90: 1.857870033
P95: 2.295167724

Student 29485.111:
Candidates: 15
Official course-in-plan prediction rows: 21235
Experimental course prediction rows: 15

Official Top 3:
1. 1032.111, 309.111, 310.111, 311.111, 317.111, 328.111, 346.111, 350.111, 354.111
2. 309.111, 311.111, 314.111, 317.111, 318.111, 328.111, 346.111, 350.111, 354.111
3. 1032.111, 310.111, 311.111, 314.111, 317.111, 318.111, 328.111, 346.111, 350.111, 354.111

Experimental Top 3:
1. 1032.111, 308.111, 309.111, 310.111, 314.111, 317.111, 346.111, 350.111, 354.111
2. 308.111, 309.111, 310.111, 311.111, 314.111, 317.111, 346.111, 350.111, 354.111
3. 1032.111, 308.111, 309.111, 311.111, 314.111, 317.111, 346.111, 350.111, 354.111

Exact Top-1 match: NO
Official Top-1 in experimental Top-3: NO
Official Top-3 recall@3: 0.000000000
Official Top-3 recall@10: 0.000000000

Official best projected GPA: 3.103604651
Experimental best projected GPA: 3.100697674
Regret (requested cross-model gap): 0.002906977

Runtime official: 0.337826600 seconds
Runtime experimental: 0.110837500 seconds
Speedup: 3.048x

Batch: 6 additional cases
Top-1 recall@1: 0.166666667
Top-1 recall@3: 0.500000000
Top-1 recall@10: 0.833333333
Top-3 recall@10: 0.777777778
Median projected-GPA regret: 0.002739461
P95 regret: 0.015543559
Prediction reduction (median): 99.810987%
Runtime speedup (median): 1.919x

Official artifacts modified: NO
Official Recommendation modified: NO

Recommendation: KEEP EXPERIMENTAL
```

## Training and feature contract

Train: **356,816** rows through **20243**; holdout: **67,536** rows in 20251/20252. المصدران هما `data/features/temporal_train_features_v2.parquet` و`data/features/temporal_test_features_v2.parquet`. لم نعد بناء البيانات أو Frozen History؛ نستعمل الخصائص الزمنية الرسمية كما هي، مع بروتوكول الاختبار sequential roll-forward.

الأهداف: Grade=`final_mark` وFail=`is_fail`. نفس folds: حتى 20223→20231–20233، وحتى 20233→20241–20243. نفس weights: 0.25 قبل 2022 و1.0 بعدها أثناء fit فقط. نفس seed=42 وlearning_rate=0.04، سقف 900 boosting rounds وearly stopping=75، ونفس configs الثلاثة والفئات مع missing/unknown. لم نجرب hyperparameters خارج الشبكة الرسمية. الاختيار من CV فقط، قبل تقييم holdout.

Experimental Grade winner: **regularized_47**, 125 rounds; Fail winner: **capaciy_63**, 85 rounds. الزمن الكلي للتدريب والتقييم: 61.52 seconds. الاسم `capaciy_63` في كود التدريب الحالي يحمل typo؛ قيمه العددية هي config الـ63 الرسمية. حافظنا على الكود الرسمي.

القائمة مشتقة برمجيًا من BASE_FEATURES مع الحفاظ على ترتيبها. الحارس يثبت 47−14=33 ويثبت أن الفرق الوحيد هو مجموعة الـ14 المطلوبة. لا يحتاج بناء مصفوفة inference إلى أي plan/peer columns.

```text
gpa_prev_1
gpa_prev_2
gpa_trend_delta
gpa_trend_missing
start_agpa_points
start_total_in_courses
start_total_in_credits
prior_total_reg_courses
prior_total_reg_credits
prior_total_fail_courses
prior_total_fail_credits
prior_fail_credit_ratio
prior_registered_semesters
observed_gap_semesters
diploma_gpa
course_credits
attempt_number
plan_year_order
plan_semester_order
plan_credits_count
degree_credits_count
course_history_avg_mark
course_history_fail_rate
course_history_avg_attempt
course_history_retake_rate
course_history_effective_support
course_history_fallback_level
course_history_missing
plan_course_type_id
plan_requirement_type_id
diploma_type_id
grade_version_id
part_semester
```

Removed:

```text
peer_course_count
peer_credit_weighted_avg_attempt
peer_credit_weighted_avg_mark
peer_credit_weighted_fail_rate
peer_difficulty_credit_load
peer_difficulty_missing
peer_max_fail_rate
peer_total_credits
plan_course_count
plan_credit_weighted_avg_attempt
plan_credit_weighted_avg_mark
plan_credit_weighted_fail_rate
plan_difficulty_credit_load
plan_total_credits
```

## Grade and Fail holdout comparisons

كل أرقام holdout أدناه حُسبت مجددًا من المودلين الرسميين والتجريبيين على الصفوف نفسها. الأرقام غير موزونة عند التقييم، مثل التدريب الرسمي، والعلامات clipped إلى [0,100]. أما Official CV فهو محفوظ في metadata الرسمية ولم نعد تدريب baseline. Experimental CV جديد. لا نسمي CV الرسمي إعادة قياس جديدة.

| Grade metric | Official 47 | Experimental 33 | Delta 33 minus 47 |
| --- | --- | --- | --- |
| mae | 9.707697595 | 9.718016591 | 0.010318996 |
| rmse | 13.045275785 | 13.079372453 | 0.034096668 |
| within_5 | 0.349976309 | 0.350672234 | 0.000695925 |
| within_10 | 0.625888415 | 0.624481758 | -0.001406657 |
| CV mean MAE (official saved) | 9.522407057 | 9.505863980 | -0.016543076 |

| Fail metric | Official 47 | Experimental 33 | Delta 33 minus 47 |
| --- | --- | --- | --- |
| pr_auc | 0.305109961 | 0.299132432 | -0.005977530 |
| roc_auc | 0.809762571 | 0.807971082 | -0.001791489 |
| brier | 0.081176685 | 0.081472778 | 0.000296093 |
| log_loss | 0.274022790 | 0.275495015 | 0.001472225 |
| calibration_error_10_bins | 0.021415814 | 0.022241706 | 0.000825891 |
| CV mean LogLoss (official saved) | 0.227316517 | 0.227307105 | -0.000009411 |

## Direct plan-context sensitivity

التجميع لكل (student_id, course_id) عبر جميع الخطط المطابقة، وليس Top K فقط. std يستخدم population ddof=0. العينة الرئيسية منفصلة عن عينة batch لتجنب مضاعفة الطالب.

| cohort | metric | mean | median | p90 | p95 | max |
| --- | --- | --- | --- | --- | --- | --- |
| student 29485.111 (15 pairs) | predicted_mark_range | 0.146193173 | 0.127520326 | 0.251078258 | 0.271346088 | 0.271346088 |
| student 29485.111 (15 pairs) | fail_probability_range | 0.000451690 | 0.000316425 | 0.000617979 | 0.001004506 | 0.001887351 |
| batch (80 pairs) | predicted_mark_range | 0.678791704 | 0.444743136 | 1.857870033 | 2.295167724 | 2.868426796 |
| batch (80 pairs) | fail_probability_range | 0.020444662 | 0.008763527 | 0.046007711 | 0.103958566 | 0.156929202 |

| student_id | course_id | prediction_rows | predicted_mark_std | predicted_mark_min | predicted_mark_max | predicted_mark_range | fail_probability_std | fail_probability_min | fail_probability_max | fail_probability_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 29485.111 | 1032.111 | 1324 | 0.016196584 | 84.921123891 | 84.966999908 | 0.045876018 | 0.000059159 | 0.008017864 | 0.008334290 | 0.000316425 |
| 29485.111 | 308.111 | 1405 | 0.040247428 | 80.483959746 | 80.677124709 | 0.193164963 | 0.000024688 | 0.006610025 | 0.006761744 | 0.000151719 |
| 29485.111 | 309.111 | 1405 | 0.032843565 | 80.711199351 | 80.804616448 | 0.093417096 | 0.000065991 | 0.007834419 | 0.008095212 | 0.000260793 |
| 29485.111 | 310.111 | 1324 | 0.040514760 | 80.979758568 | 81.251104656 | 0.271346088 | 0.000064585 | 0.008262863 | 0.008537795 | 0.000274932 |
| 29485.111 | 311.111 | 1324 | 0.031715069 | 84.919150726 | 85.012567822 | 0.093417096 | 0.000070602 | 0.008419077 | 0.008699162 | 0.000280085 |
| 29485.111 | 314.111 | 1324 | 0.017400764 | 83.020092579 | 83.147612905 | 0.127520326 | 0.000026031 | 0.006689211 | 0.006825203 | 0.000135992 |
| 29485.111 | 317.111 | 1405 | 0.017766079 | 86.859955691 | 86.905831709 | 0.045876018 | 0.000040276 | 0.007663514 | 0.007939006 | 0.000275492 |
| 29485.111 | 318.111 | 1324 | 0.031633713 | 81.652028252 | 81.845193214 | 0.193164963 | 0.000079955 | 0.010147283 | 0.010484254 | 0.000336970 |
| 29485.111 | 319.111 | 1405 | 0.025063430 | 79.148478860 | 79.369155374 | 0.220676513 | 0.000145050 | 0.014105609 | 0.014731752 | 0.000626144 |
| 29485.111 | 328.111 | 1405 | 0.020550290 | 81.473003073 | 81.609167690 | 0.136164617 | 0.000136627 | 0.013639006 | 0.014244737 | 0.000605731 |
| 29485.111 | 332.111 | 1614 | 0.033395405 | 81.362897935 | 81.456315031 | 0.093417096 | 0.000107359 | 0.011074927 | 0.011503979 | 0.000429053 |
| 29485.111 | 346.111 | 1494 | 0.031876678 | 81.481533434 | 81.574950530 | 0.093417096 | 0.000096212 | 0.010023628 | 0.010470499 | 0.000446870 |
| 29485.111 | 350.111 | 1494 | 0.030189456 | 81.144068622 | 81.237485718 | 0.093417096 | 0.000102996 | 0.010517049 | 0.010985673 | 0.000468624 |
| 29485.111 | 354.111 | 1494 | 0.045908725 | 80.949928467 | 81.221274556 | 0.271346088 | 0.000072529 | 0.008391294 | 0.008670462 | 0.000279168 |
| 29485.111 | 359.111 | 1494 | 0.034859130 | 76.866439437 | 77.087115950 | 0.220676513 | 0.000567754 | 0.015034254 | 0.016921605 | 0.001887351 |

**السياق الصغير قد يغيّر نقاط السلم.** للمادة `311.111` يتراوح التوقع الرسمي بين 84.919151 و85.012568، فينتقل expected_points من 3.00 إلى 3.25 عند threshold=85. توقع 33-feature للمادة 84.746962، أي 3.00 points. فرق 0.25 quality points لمادة ساعة واحدة يكفي هنا لفرق projected GPA يساوي 0.25/86=0.002906977. لذلك range صغير في العلامة لا يعني أن Plan Context بلا أثر على ترتيب الخطط.

## Student 29485.111: all 15 course predictions

الطلب نفسه: degree=42.111، target=20251، exportdata (7).json، مطلوب 12–18→exact18، history_v2/as_of_20243، current GPA=3.12 وprior registered credits=68. GradeScale الرسمي باستخدام grade_version_id=3.111 بعد clip، دون direct-points model.

| course_id | course_name | credits | predicted_mark_33 | expected_grade_33 | expected_points_33 | fail_probability_33 |
| --- | --- | --- | --- | --- | --- | --- |
| 1032.111 | طب الأسنان الشرعي | 1 | 84.980932179 | B | 3.000000000 | 0.009433161 |
| 308.111 | الإسعافات الأولية | 2 | 81.568652561 | B | 3.000000000 | 0.008704570 |
| 309.111 | علم الأدوية | 2 | 80.260032357 | B | 3.000000000 | 0.010459477 |
| 310.111 | التغذية | 1 | 81.443824155 | B | 3.000000000 | 0.009317832 |
| 311.111 | تدبير الأمراض العامة | 1 | 84.746961669 | B | 3.000000000 | 0.010218095 |
| 314.111 | علم الإطباق | 1 | 83.356564363 | B | 3.000000000 | 0.008208469 |
| 317.111 | العلوم السلوكية ومهارات التواصل | 2 | 87.211243919 | B+ | 3.250000000 | 0.008621445 |
| 318.111 | مكافحة العدوى | 1 | 81.390059542 | B | 3.000000000 | 0.013814604 |
| 319.111 | الصحة السنية العامة وطب الأسنان الوقائي | 2 | 79.686400170 | B- | 2.750000000 | 0.016082913 |
| 328.111 | علم الأشعة و التصوير في طب الأسنان (2) | 2 | 82.157067859 | B | 3.000000000 | 0.015978330 |
| 332.111 | التشريح المرضي الخاص بالفم والأسنان | 4 | 82.690995027 | B | 3.000000000 | 0.018331462 |
| 346.111 | تقويم الأسنان (1) | 3 | 82.734914175 | B | 3.000000000 | 0.011775345 |
| 350.111 | تعويض الأسنان الثابتة (3) | 3 | 82.281152058 | B | 3.000000000 | 0.012772577 |
| 354.111 | تعويض الأسنان المتحركة (2) | 3 | 81.467596843 | B | 3.000000000 | 0.010214112 |
| 359.111 | مداواة أسنان ترميمية (2) | 3 | 76.893246978 | B- | 2.750000000 | 0.018243411 |

## Official Top 3 versus experimental Top 10

plan_id أدناه للتتبع فقط؛ كل التطابقات محسوبة من مجموعات course_ids.

| rank | trace_plan_id | course_ids | total_credits | expected_quality_points | expected_plan_gpa | projected_cumulative_gpa | expected_failed_credits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 797 | 1032.111, 309.111, 310.111, 311.111, 317.111, 328.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.750000000 | 3.041666667 | 3.103604651 | 0.173434142 |
| 2 | 2173 | 309.111, 311.111, 314.111, 317.111, 318.111, 328.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.750000000 | 3.041666667 | 3.103604651 | 0.174463725 |
| 3 | 1080 | 1032.111, 310.111, 311.111, 314.111, 317.111, 318.111, 328.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.750000000 | 3.041666667 | 3.103604651 | 0.174751484 |

| rank | course_ids | total_credits | expected_quality_points | expected_plan_gpa | projected_cumulative_gpa | expected_failed_credits |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1032.111, 308.111, 309.111, 310.111, 314.111, 317.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.186816547 |
| 2 | 308.111, 309.111, 310.111, 311.111, 314.111, 317.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.187601481 |
| 3 | 1032.111, 308.111, 309.111, 311.111, 314.111, 317.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.187716809 |
| 4 | 1032.111, 308.111, 309.111, 310.111, 311.111, 317.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.188826172 |
| 5 | 1032.111, 308.111, 310.111, 311.111, 314.111, 317.111, 318.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.189930292 |
| 6 | 1032.111, 308.111, 309.111, 310.111, 311.111, 314.111, 317.111, 328.111, 346.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.190673572 |
| 7 | 308.111, 309.111, 310.111, 314.111, 317.111, 318.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.191197990 |
| 8 | 1032.111, 308.111, 309.111, 314.111, 317.111, 318.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.191313318 |
| 9 | 308.111, 309.111, 311.111, 314.111, 317.111, 318.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.192098252 |
| 10 | 1032.111, 308.111, 309.111, 310.111, 317.111, 318.111, 346.111, 350.111, 354.111 | 18.000000000 | 54.500000000 | 3.027777778 | 3.100697674 | 0.192422681 |

جميع الخطط 18 ساعة؛ تعظيم Q يعظم المعدل الفصلي والتراكمي لنفس الطالب. محسّن التجربة يبحث في جميع المرشحين وجميع 2,503 combinations، ثم يرتب Q DESC، expected_failed_credits ASC، ثم tuple معرّفات المواد ترتيبًا ثابتًا. يحتفظ بـTop 10 ويصدر Top 3 منفصلًا. الحساب الدقيق يحافظ على الساعات الكسرية والمواد الاختيارية ذات الصفر ساعة.

| comparison | value |
| --- | --- |
| top1_recall_at_1 | 0.000000000 |
| top1_recall_at_3 | 0.000000000 |
| top1_recall_at_10 | 0.000000000 |
| top3_recall_at_3 | 0.000000000 |
| top3_recall_at_10 | 0.000000000 |
| projected_gpa_regret_cross_model | 0.002906977 |
| expected_plan_gpa_regret_cross_model | 0.013888889 |
| expected_failed_credits_difference_exp_minus_official | 0.013382405 |
| official_rescored_projected_gpa_regret | 0.002906977 |
| official_rescored_plan_gpa_regret | 0.013888889 |

## Runtime

الزمن هو median لثلاث تشغيلات in-memory لكل سيناريو، بترتيب رسمي/تجريبي متناوب، 4 inference threads لكلا المسارين. يدخل بناء rows/السياق والتنبؤ وتلخيص/ترتيب الخطط؛ يستثني تحميل المدخلات والمودلز والتاريخ والكتابة على القرص لأنها مشتركة/خارج hot path. هذا ليس قياس latency شاملًا للـCLI. صفوف التنبؤ محسوبة لكل مودل: الرسمي 21,235 Grade و21,235 Fail؛ التجريبي 15 Grade و15 Fail. لا نقارن عددًا مضاعفًا في جانب بغير مضاعف في الآخر.

| metric | Official | Experimental |
| --- | --- | --- |
| candidate courses | 15.000000000 | 15.000000000 |
| prediction rows per model | 21235.000000000 | 15.000000000 |
| model prediction calls | 4.000000000 | 2.000000000 |
| matching combinations | 2503.000000000 | 2503.000000000 |
| runtime seconds median | 0.337826600 | 0.110837500 |

Prediction row reduction: **1415.667× / 99.929362%**; runtime speedup: **3.048×**. البحث الشامل نفسه ما زال موجودًا؛ لا نتوقع أن تنخفض كلفة end-to-end بنسبة صفوف المودل نفسها.

Measured runtime repetitions:

```json
{
  "official_seconds": [
    0.31001140002626926,
    0.3378266000072472,
    0.4161846999777481
  ],
  "experimental_seconds": [
    0.10068360000150278,
    0.11083750001853332,
    0.1335149999940768
  ]
}
```

## Batch distributions

ستة طلاب إضافيين من test 20251؛ عينة convenience حتمية من قوائم export المتاحة، وليست عينة عشوائية من الجامعة. الطالب الرئيسي خارج إحصاءات batch. المقبول 2–18 candidates مع snapshot صالح وخطة exact18؛ تفاصيل اختيار/استبعاد جميع المصادر محفوظة في batch_selection.json.

| student_id | degree_id | candidate_courses | official_matching_plans | top1_recall_at_1 | top1_recall_at_3 | top1_recall_at_10 | top3_recall_at_10 | projected_gpa_regret_cross_model | official_rescored_projected_gpa_regret | runtime_speedup | prediction_row_reduction_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10021.111 | 13.111 | 9 | 10 | 1 | 1 | 1 | 1.000000000 | 0.002077562 | -0.000000000 | 1.603663888 | 87.323943662 |
| 10079.111 | 1.111 | 14 | 1118 | 0 | 1 | 1 | 1.000000000 | 0.000000000 | 0.000000000 | 2.112580481 | 99.852553976 |
| 10095.111 | 1.111 | 13 | 233 | 0 | 0 | 0 | 0.000000000 | 0.000000000 | 0.000673854 | 1.168086962 | 99.404489235 |
| 29616.111 | 53.111 | 13 | 1716 | 0 | 1 | 1 | 1.000000000 | 0.014705882 | 0.000000000 | 1.748363821 | 99.873737374 |
| 4861.111 | 41.111 | 16 | 1321 | 0 | 0 | 1 | 1.000000000 | 0.015822785 | 0.009493671 | 2.088647303 | 99.769419225 |
| 23685.111 | 26.111 | 15 | 2640 | 0 | 0 | 1 | 0.666666667 | 0.003401361 | 0.003401361 | 2.682905310 | 99.918619792 |

| metric | mean | median | p90 | p95 | max |
| --- | --- | --- | --- | --- | --- |
| top1_recall_at_1 | 0.166666667 | 0.000000000 | 0.500000000 | 0.750000000 | 1.000000000 |
| top1_recall_at_3 | 0.500000000 | 0.500000000 | 1.000000000 | 1.000000000 | 1.000000000 |
| top1_recall_at_10 | 0.833333333 | 1.000000000 | 1.000000000 | 1.000000000 | 1.000000000 |
| top3_recall_at_3 | 0.555555556 | 0.666666667 | 1.000000000 | 1.000000000 | 1.000000000 |
| top3_recall_at_10 | 0.777777778 | 1.000000000 | 1.000000000 | 1.000000000 | 1.000000000 |
| projected_gpa_regret_cross_model | 0.006001265 | 0.002739461 | 0.015264334 | 0.015543559 | 0.015822785 |
| expected_plan_gpa_regret_cross_model | 0.037037037 | 0.034722222 | 0.076388889 | 0.079861111 | 0.083333333 |
| official_rescored_projected_gpa_regret | 0.002261481 | 0.000336927 | 0.006447516 | 0.007970593 | 0.009493671 |
| official_rescored_plan_gpa_regret | 0.013888889 | 0.006944444 | 0.034722222 | 0.038194444 | 0.041666667 |
| expected_failed_credits_difference_exp_minus_official | 0.043613417 | -0.066241581 | 0.391234732 | 0.466832016 | 0.542429299 |
| runtime_speedup | 1.900707961 | 1.918505562 | 2.397742896 | 2.540324103 | 2.682905310 |
| prediction_row_reduction_factor | 551.418958588 | 555.950892857 | 1010.400000000 | 1119.600000000 | 1228.800000000 |
| prediction_row_reduction_percent | 97.690460544 | 99.810986600 | 99.896178583 | 99.907399187 | 99.918619792 |

الأعمدة cross_model تحقق الفرق المطلوب: official_best − experimental_best باستخدام توقعات كل مودل نفسه؛ قد يكون الفرق سالبًا ولا يعد تقدير خسارة فعلية. لذلك أضفنا official_rescored: قيّمنا خطة التجربة الأفضل تحت المودل الرسمي نفسه، ثم طرحناها من optimum الرسمي. هذا يعزل خسارة اختيار خطة وفق criterion رسمي، ولا يجعله حقيقة مستقبلية للطالب. Quantiles لعينة من ستة أرقام وصفية وغير مستقرة إحصائيًا.

Excluded during candidate/snapshot selection:

| source | student_id | reason |
| --- | --- | --- |
| exportdata (10).json | 27547.111 | candidate count 19 outside bounded sample [2,18] |
| exportdata (11).json | 20335.111 | student-degree absent from 20251 V2 model holdout |
| exportdata (12).json | 29485.111 | duplicate student scenario / primary case excluded from batch |
| exportdata (13).json | 10011.111 | candidate count 23 outside bounded sample [2,18] |
| exportdata (4).json | 31082.111 | candidate count 20 outside bounded sample [2,18] |
| exportdata (6).json | 12849.111 | student-degree absent from 20251 V2 model holdout |
| exportdata (7).json | 29485.111 | duplicate student scenario / primary case excluded from batch |

No-feasible-plan cases (excluded from ranking overlap, retained in audit):

| student_id | reason |
| --- | --- |
| 17098.111 | No feasible exact-18-credit plan. |
| 17464.111 | No feasible exact-18-credit plan. |
| 14861.111 | No feasible exact-18-credit plan. |

## Decision evidence

**A — Model loss:** Grade MAE +0.010319; Fail LogLoss +0.001472; PR-AUC -0.005978. خسارة صغيرة على holdout نفسه، دون مجال ثقة أو تحقق إضافي يثبت تكافؤًا إحصائيًا.

**B — Context effect:** primary median mark range=0.127520 وP95=0.271346؛ batch median=0.444743 وP95=2.295168. عبور حدود GradeScale يفسر أهمية تغيرات صغيرة لبعض المواد.

**C — Same best plan:** primary Top-1 غير موجود حتى في Experimental Top-10؛ batch التطابق exact Top-1 في 1/6، ووجوده في Top-3 في 3/6، وTop-10 في 5/6. تطابق course sets صارم وقد ينخفض بين خطط متعادلة GPA لكن مختلفة المخاطر.

**D — Difference cost:** primary projected GPA gap=0.002906977. Batch cross-model median=0.002739461 وP95=0.015543559؛ official-rescored median=0.000336927 وP95=0.007970593. الأرقام توقعات نماذج وسيناريو additive؛ سياسة إعادة المواد وتحقق النتائج الفعلية غير مقاسين هنا.

**E — Runtime:** primary 3.048×؛ batch median 1.919×. تقليل صفوف التنبؤ ممتاز لكن search exhaustive يحد كسب الزمن. هذه النسخة البسيطة مناسبة لهذه الأعداد؛ لا توجد دعوى scalability على عشرات كثيرة من المرشحين.

**الحكم: KEEP EXPERIMENTAL.** هناك دليل يدعم متابعة architecture الأبسط، لكن overlap المنخفض والعينة الصغيرة يمنعان اعتماد بديل رسمي تلقائيًا. لا تغيير في Recommendation V2 ولا proposal لتنفيذ promotion.

## Isolation, provenance and validation

تمت مقارنة SHA-256 قبل/بعد لـ**110** ملفًا محميًا؛ changed=[]. يشمل المصدر الرسمي والمودلز V1/V2 والمدخلات وcategory artifacts وFrozen History والـtrace السابق. التعديلات السابقة في working tree حافظنا عليها. المضاف في src/paths.py ثوابت namespace التجربة فقط.

Dependency test يسمح فقط لثلاث ملفات workflow تجريبية جديدة بقراءة src/recommendation، مثل استثناء XML evaluator الحالي. لم نخف الاستيراد ولم نغير اعتماد Features أو Modeling على التجارب.

Validation: انظر `validation_summary.json` وlogs في مجلد نتائج التجربة. الفشل السابق في اختبار trainer بسبب capacity_63محفوظ ومذكور منفصلًا؛ لم نعدل config الرسمي لحل typo.

Provenance: training_signature يسجل SHA-256 لملفي features، المصدر التدريبي الرسمي، العقد الرسمي، كود التدريب/المصفوفة التجريبي، والـbaseline الرسمي وفئاته. مدخل JSON له بصمة في import_report.json لكل حالة. إعادة التحميل --skip-training ترفض تغير signature أو model headers/hashes. استقلال المسارات لا يلغي أي selection bias موروث في البيانات الرسمية؛ لا ندعي معالجة cleaning أو قياس causal outcomes.

```powershell
.\.venv\Scripts\python.exe -m src.experiments.course_only_recommendation --skip-training
```

Artifacts and evidence:

- Report: `reports/course_only_33_feature_experiment.md`
- Experimental models: `models/experiments/course_only_recommendation`
- Evaluation results: `data/evaluation/experiments/course_only_recommendation`
- Student details / CSV / Top 3 / Top 10: `data/debug/course_only_29485_111`

Fresh verification results:

Focused: **20 passed, 0 failed**. Full suite: **557 passed, 1 failed**, 6 subtests passed.

Remaining pre-existing failure: `tests/test_train_models.py::test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`. Pre-existing capacity_63typo, also present in HEAD; official trainer left unchanged.

