# Data / Features V2 migration report — 2026-09-21

هذه الوثيقة تحتفظ بسجل النقل الأولي وتسوية قواعد التنظيف. الحالة الأحدث بعد سياسة الطلاب المشتركين موثقة في قسم `COMMON STUDENT POLICY` في آخر التقرير.

Moved files
-----------

- `src/cleaning_utils.py` → `src/data/cleaning_utils.py`
- `src/academic_calendar.py` → `src/data/academic_calendar.py`
- `src/clean_degree_course.py` → `src/data/clean_degree_course.py`
- `src/clean_student_course.py` → `src/data/clean_student_course.py`
- `src/clean_student_status.py` → `src/data/clean_student_status.py`
- `src/clean_student_diploma.py` → `src/data/clean_student_diploma.py`
- `src/clean_outliers.py` → `src/data/clean_outliers.py`
- `src/build_student_course_enriched.py` → `src/data/build_student_course_enriched.py`
- `src/build_registration_roster.py` → `src/data/build_registration_roster.py`
- `src/build_temporal_split.py` → `src/data/build_temporal_split.py`
- `src/temporal_features.py` → `src/features/temporal_features.py`
- `src/build_temporal_features.py` → `src/features/build_temporal_features.py`
- `src/feature_contract.py` → `src/features/feature_contract.py`
- `src/frozen_history.py` → `src/features/frozen_history.py`
- `src/build_frozen_history.py` → `src/features/build_frozen_history.py`

أُنشئ `src/data/__init__.py` و`src/features/__init__.py`. لم تُنقل أقسام التدريب أو التجارب أو التوصية أو التقييم أو التشخيص.

Updated imports
---------------

- أسلوب موحّد للاعتماد على الملفات المنقولة: `src.data.*` و`src.features.*`، وللمسارات داخلها: `src.paths`.
- حُدثت imports في الاختبارات، training/evaluation consumers، `src/experiments/`، التوصية، scripts، وdebugging.
- `src/experiment_degree_points.py` يستورد `src.experiments.degree_points` أصلًا؛ لم يحتج تعديلًا، وقد نجح استيراده.
- أضيف تهيئة مسار المشروع عند تشغيل ثلاثة consumers مباشرةً (`train_models`, `evaluate_plan_gpa`, `analyze_model_errors`) للحفاظ على أسلوب التشغيل السابق. جُرّبت imports دون تشغيل تدريب أو كتابة مودلات.
- قُيّدت قاعدة `.gitignore` من `data/` إلى `/data/` حتى لا تخفي `src/data/`.
- حُدثت مراجع الملفات وأوامر `python -m` في التوثيق؛ فُصلت أوامر بناء V2 عن أوامر تدريب V1 صراحةً.

Added versioned_path()
----------------------

Implementation:

```python
def versioned_path(path, version="v2"):
    """Return a sibling artifact path with the version before its extension."""
    return path.with_name(f"{path.stem}_{version}{path.suffix}")
```

Generated V2 paths:

كل constant أدناه معرّف فقط بـ `NAME_V2 = versioned_path(NAME)`؛ لا تغيير لتعريفات V1. وجود constant لا يعني أن artifact تولّد فعليًا.

| Constant | مسار V2 | حالة الملف الفعلي |
|---|---|---|
| `CLEAN_STUDENT_COURSE_PATH_V2` | `data/clean/student_course_v2.parquet` | Blocked |
| `CLEAN_STUDENT_STATUS_PATH_V2` | `data/clean/student_status_v2.parquet` | Blocked |
| `CLEAN_DEGREE_COURSE_PATH_V2` | `data/clean/degree_course_v2.parquet` | Generated |
| `STUDENT_COURSE_ENRICHED_PATH_V2` | `data/clean/student_course_enriched_v2.parquet` | Blocked |
| `CLEAN_STUDENT_DIPLOMA_PATH_V2` | `data/clean/student_diploma_v2.parquet` | Generated |
| `STUDENT_COURSE_DIPLOMA_PATH_V2` | `data/merged/student_course_enriched_with_diploma_v2.parquet` | Blocked |
| `STUDENT_COURSE_WITHOUT_OUTLIERS_PATH_V2` | `data/merged/student_course_enriched_without_outliers_v2.parquet` | Blocked |
| `OUTLIER_STUDENTS_AUDIT_PATH_V2` | `data/merged/outlier_students_v2.parquet` | Blocked |
| `TEMPORAL_TRAIN_PATH_V2` | `data/temporal/temporal_train_v2.parquet` | Blocked |
| `TEMPORAL_TEST_PATH_V2` | `data/temporal/temporal_test_v2.parquet` | Blocked |
| `CLEAN_REGISTRATION_ROSTER_PATH_V2` | `data/clean/registration_roster_v2.parquet` | Blocked |
| `TEMPORAL_TRAIN_ROSTER_PATH_V2` | `data/temporal/temporal_train_roster_v2.parquet` | Blocked |
| `TEMPORAL_TEST_ROSTER_PATH_V2` | `data/temporal/temporal_test_roster_v2.parquet` | Blocked |
| `TEMPORAL_TRAIN_FEATURES_PATH_V2` | `data/features/temporal_train_features_v2.parquet` | Blocked |
| `TEMPORAL_TEST_FEATURES_PATH_V2` | `data/features/temporal_test_features_v2.parquet` | Blocked |
| `COURSE_HISTORY_STATE_PATH_V2` | `data/artifacts/course_history_state_v2.pkl` | Blocked |
| `CATEGORY_LEVELS_PATH_V2` | `data/artifacts/category_levels_v2.json` | Not generated — training خارج النطاق |

- استثناء مقصود: `data/artifacts/history/as_of_<part>/` يحتفظ بآلية versioning/immutability الحالية؛ لم تُنشأ أو تُستبدل bundles موجودة. اجتاز تحميل نسختَي `20243` و`20251` وملف التاريخ القديم فحص التوافق.
- `CATEGORY_LEVELS_PATH_V2` معرّف وجاهز؛ إنتاج category levels يحدث في التدريب، الذي لم يُشغّل ولم تُعدّل مساراته.

Merge validations added
-----------------------

- status merge: `on=["student_id", "degree_id", "part_id"]`, `how="inner"`, `validate="many_to_one"`.
- plan merge: `on=["degree_id", "course_id"]`, `how="left"`, `validate="many_to_one"`.
- اختبارا duplicates يؤكدان `pandas.errors.MergeError` بدل تضاعف الصفوف. لم يتغير نوع join.

Tests
-----

| الفحص | النتيجة |
|---|---|
| Baseline قبل النقل | 250 passed / 30 failed |
| Data + paths + V2 chain | 244 passed / 0 failed |
| Features + frozen history + V2 chain | 26 passed / 0 failed |
| Full suite | 304 passed / 2 failed |
| Compile لكل src | PASS |
| Import لكل src — 38 module | PASS |
| Fresh-process imports للـ15 module المنقولة | PASS |
| Direct-script import compatibility للثلاثة consumers | PASS |
| AST parity للـ15 module بعد استثناء imports وأسماء المسارات وحارسي merge | PASS |
| SHA-256 لكل 461 ملف data/model أصلي | PASS — صفر ملفات محذوفة أو معدّلة |
| إعادة تشغيل سكربت التحقق مع وجود V2 | رُفضت الكتابة بـ FileExistsError |

Failures:

1. `tests/test_local_recommendation.py::ArtifactIntegrationTests::test_local_cli_without_snapshot`
2. `tests/test_local_recommendation.py::ArtifactIntegrationTests::test_snapshot_ignores_current_future_outcomes`

كلاهما فشل قبل النقل وبعده بسبب `Invalid part_id 20214: semester must be 1, 2, or 3`. ليست مشكلة dependency بيئية. لم تُحذف الاختبارات أو تُحوّل إلى skips/xfails.
الفشل السابق الآخر (28 اختبارًا) كان خطأ fixture: `st art_part_id`؛ صُحح إلى `start_part_id` دون تعديل قواعد تنظيف production.
اختبارات المسارات والـmerge الجديدة شوهدت تفشل أولًا: 25 failed، ثم نجحت بعد التنفيذ. الاختبار الشامل يستخدم Parquet حقيقيًا في مجلد مؤقت وملفات V1 تالفة عمدًا كحراس؛ أي رجوع إلى V1 يفشل، ويتحقق كذلك من بقاء raw/V1 بلا تغيير.

V1 vs V2 verification
---------------------

| Artifact | V1 rows | V2 rows | النتيجة |
|---|---:|---:|---|
| `student_course.parquet` | 456453 | — | Unavailable: upstream blocked |
| `student_status.parquet` | 95622 | — | Unavailable: upstream blocked |
| `degree_course.parquet` | 4006 | 4006 | Legacy dtype mismatch — see below |
| `student_course_enriched.parquet` | 456453 | — | Unavailable: upstream blocked |
| `student_diploma.parquet` | 32524 | 32524 | Exact match |
| `student_course_enriched_with_diploma.parquet` | 456453 | — | Unavailable: upstream blocked |
| `student_course_enriched_without_outliers.parquet` | 434168 | — | Unavailable: upstream blocked |
| `outlier_students.parquet` | 785 | — | Unavailable: upstream blocked |
| `temporal_train.parquet` | 365585 | — | Unavailable: upstream blocked |
| `temporal_test.parquet` | 68578 | — | Unavailable: upstream blocked |
| `registration_roster.parquet` | 463721 | — | Unavailable: upstream blocked |
| `temporal_train_roster.parquet` | 390134 | — | Unavailable: upstream blocked |
| `temporal_test_roster.parquet` | 73581 | — | Unavailable: upstream blocked |
| `temporal_train_features.parquet` | 365585 | — | Unavailable: upstream blocked |
| `temporal_test_features.parquet` | 68578 | — | Unavailable: upstream blocked |

- `student_diploma_v2.parquet`: تطابق كامل مع V1، بما فيه المحتوى المرتّب والأعمدة وdtypes وnull counts وعدد الطلاب. بُني مستقلًا من raw عبر دالة التنظيف نفسها؛ دمج الدبلوم بقي متوقفًا.
- `degree_course_v2.parquet`: 4,006 صفوف في الإصدارين. فرق dtype وحيد: `requirement_type_id` كان `string` في V1 المحفوظ، وصار `Int64` وفق الكود الموجود **قبل النقل**. بعد توحيد ذلك النوع في ذاكرة المقارنة فقط، تطابق المحتوى بالكامل؛ لم يُعدّل أي artifact V1.
- مخرجا degree والدبلوم متطابقان بالضبط مع تنفيذ نسخة source المحفوظة قبل النقل على نفس raw، بعد Parquet round-trip مماثل. هذا يميّز الاختلاف السابق في V1 عن regression ناتج عن النقل.
- تفاصيل row count، unique students، ترتيب الأعمدة، جميع dtypes، توزيع part_id، وnull counts محفوظة في `real_data_verification.json`. الجداول المتوقفة لها إحصاءات V1 فقط؛ لا تُدّعى لها مقارنة V2.

عوائق تشغيل البيانات الفعلية:

- `clean_student_course`: `Missing required key: course_id, part_id`. داخل تسجيلات R/E هناك قيمة ناقصة واحدة لكل من `course_id` و`part_id`. النسخة السابقة للنقل ترفع الاستثناء نفسه.
- `clean_student_status`: الفصول الخام المخالفة للحارس الحالي هي `20214` (3 صفوف)، `20224` (صفان)، و`20254` (3 صفوف). لم تُحذف أو تُحوّل هذه الصفوف.
- بناء enrichment ثم diploma merge/outliers/split/roster/features/history state متعذر لغياب مخرجات البداية V2. تغيير معالجة هذه الحالات يحتاج قرارًا يخص قواعد التنظيف، لذا بقي خارج المهمة.

V2 pipeline dependency check
----------------------------

**No mixed V1/V2 intermediates.**

- كل imports لمسارات الوسائط داخل `src/data/` و`src/features/` تستخدم `_V2`.
- raw inputs مشتركة كما طُلب. `build_temporal_features` ما زال ينظف كامل raw status history في الذاكرة عمدًا للحفاظ على تاريخ الفصول التي قد لا تملك مقررات؛ هذا ليس وسيط V1.
- الاختبار الشامل أثبت سلسلة V2 كاملة على بيانات اختبارية، ولم تُنسخ ملفات V1 لملء المخرجات الفعلية المفقودة.
- `TRAIN_PARTS`, `TEST_PARTS`, `INCOMPLETE_PARTS` وكل أجسام منطق features محفوظة. معادلات `prior_total_* = total_*` وحراس `CourseHistoryState.as_of_part` محفوظة.

Remaining old imports/references
--------------------------------

- Old executable imports: **none**؛ تم فحص src/tests/scripts/debugging، والمراجع في notebooks.
- مراجع المسارات القديمة داخل snapshots وتقارير تاريخية و`codex_changes.patch` محفوظة كسجل تاريخي؛ ليست imports نشطة.
- constants ومسارات V1 باقية عمدًا للمقارنة ولـconsumers خارج نطاق النقل.

Files modified
--------------

الملفات المنقولة مذكورة أعلاه. الملفات الأخرى التي عدّلتها هذه المهمة:

- `.gitignore`
- `LOCAL_RECOMMENDATION.md`
- `PIPELINE_README.md`
- `Readme.md`
- `START_HERE.md`
- `debugging/explain_recommendation.py`
- `debugging/pipeline_audit.py`
- `debugging/pipeline_audit_details.py`
- `debugging/render_recommendation_explanation.py`
- `debugging/trace_student_29485_20251.py`
- `docs/superpowers/plans/2026-09-21-data-features-v2.md`
- `read.md`
- `scripts/scan_student_over_polict.py`
- `scripts/scan_under_12_after_status_change.py`
- `scripts/verify_data_features_v2.py`
- `scripts/verify_cleaning_policy_v2.py`
- `src/analyze_model_errors.py`
- `src/data/__init__.py`
- `src/evaluate_plan_gpa.py`
- `src/evaluate_xml_recommendations.py`
- `src/experiments/degree_points.py`
- `src/experiments/modeling.py`
- `src/experiments/specialty_history.py`
- `src/features/__init__.py`
- `src/paths.py`
- `src/recommendation.py`
- `src/recommendation_inputs.py`
- `src/train_models.py`
- `tests/test_academic_calendar.py`
- `tests/test_build_registration_roster.py`
- `tests/test_build_student_course_enriched.py`
- `tests/test_clean_degree_course.py`
- `tests/test_clean_outliers.py`
- `tests/test_clean_student_course.py`
- `tests/test_clean_student_diploma.py`
- `tests/test_clean_student_status.py`
- `tests/test_clean_utils.py`
- `tests/test_feature_pipeline.py`
- `tests/test_frozen_history.py`
- `tests/test_local_recommendation.py`
- `tests/test_projected_recommendation.py`
- `tests/test_temporal_features.py`
- `tests/test_v2_paths.py`
- `tests/test_v2_pipeline.py`

أُعيد توليد مخرجات V2 الـ16: clean course/status/degree/diploma، enriched، diploma merge، outliers، temporal split، roster، temporal features، وcourse-history state. مخرجات V1 بقيت محفوظة.
أُضيفت أدلة التحقق والـsnapshot وهذا التقرير داخل `reports/data_features_v2_20260921/`. تعديل notebook الموجود قبل المهمة لم يُمس. لم يُنفّذ commit أو push أو تعديل في المشروع القديم.

Independent review
------------------

لم تجد المراجعة المستقلة regression في production. الملاحظة الوحيدة كانت تسلسل أوامر توثيق يجمع بناء V2 وتدريب V1؛ صُحّح بالفصل الصريح دون تغيير تدريب المودلات. لا ملاحظات Critical أو Minor معلقة.

قرارات النطاق: الحفاظ على guards الحالية خارج semester-4، حذف الحالات التي حُسمت صراحة فقط، والحفاظ على versioning تاريخ serving. لم يتغير feature/temporal/recommendation/model logic.

```text
DATA MOVE: PASS
FEATURES MOVE: PASS
V2 ARTIFACT ISOLATION: PASS
V1 vs V2 EQUIVALENCE: EXPECTED POLICY DIFFERENCES + STALE V1 BASELINE DRIFT
TESTS: PASS
```

هذه كانت نتيجة ما قبل حسم سياسة التنظيف. الحالة المحدّثة موثقة في قسم `FINAL STATUS AFTER POLICY RESOLUTION` أدناه.

Cleaning policy resolution
--------------------------

أُعيد بناء V2 بعد تطبيق القرار المعتمد في طبقة التنظيف فقط:

| الحالة | العدد |
|---|---:|
| Missing `course_id` في تسجيلات R/E | 1 |
| Missing `part_id` في تسجيلات R/E | 1 |
| الصفوف الفعلية المحذوفة من courses | 1 |
| الصف الذي يجمع المفتاحين المفقودين | 1 |
| Invalid semester-4 status rows | 8 |
| `20214` | 3 |
| `20224` | 2 |
| `20254` | 3 |
| الطلاب المتأثرون في courses | 1 |
| الطلاب المتأثرون في status | 8 |
| اتحاد الطلاب المتأثرين | 9 |

لا يوجد `fillna` أو `ffill` أو inference للمفاتيح. أُزيلت semester-4 قبل حساب تاريخ enrollment، بينما بقي `academic_calendar` صارمًا عند التحقق من part مفرد. ملفات raw لم تتغير.

أُعيد تشغيل كل مراحل V2 بالترتيب: `clean_degree_course`, `clean_student_status`, `clean_student_course`, `build_student_course_enriched`, `clean_student_diploma`/merge, `clean_outliers`, `build_temporal_split`, `build_registration_roster`, ثم `build_temporal_features`. جميع المراحل التسع نجحت، وتم إنشاء 16 artifact V2، بما فيها `course_history_state_v2.pkl`.

اختبار policy reference أعاد تشغيل نسخة ما قبل السياسة مع استبعاد الصفوف المصرّح بها فقط، وتطابق تمامًا مع `student_course_v2` و`student_status_v2`. هذا يثبت أن التغيير محصور في الحذف المعتمد.

Updated verification
--------------------

- Full suite: **317 passed**.
- Data/cleaning tests: **116 passed**.
- Feature and history tests: **26 passed**.
- Compile check: PASS.
- Import check: PASS.
- V2 I/O trace: كل قراءة وسيطة بعد أول مرحلتين كانت من `_v2`؛ raw فقط بقي مشتركًا، وكل كتابة كانت إلى output V2 معتمد.
- Protected original files: **0 changed**؛ بقيت raw وV1 artifacts محفوظة.

EXPECTED V1/V2 DIFFERENCES
--------------------------

الفرق المتوقع مباشرة من السياسة هو استبعاد صف course واحد وثمانية status rows (`20214`, `20224`, `20254`) وتأثيرها التابع على split/roster/features.

UNEXPECTED DIFFERENCES
----------------------

المقارنة مع ملفات V1 المحفوظة تحتوي فروقًا أكبر من هذه السياسة: مثلًا `student_course` هو 456,453 في V1 مقابل 459,620 في V2، و`student_status` هو 95,622 مقابل 108,974. اختبار policy reference يطابق V2، لذلك هذه ليست regression من التعديل الحالي؛ إنها تدل على أن V1 artifacts أُنشئت من baseline أقدم من source/cleaning code المحفوظ قبل هذه السياسة. لم أعدّل V1 لإخفاء هذا الفرق. التفاصيل الكاملة في `pipeline_verification.json`، والـraw/source hashes لم تتغير.

FINAL STATUS AFTER POLICY RESOLUTION
------------------------------------

```text
V2 PIPELINE: PASS
FULL TEST SUITE: PASS
EXPECTED V1/V2 DIFFERENCES: policy exclusions and their downstream effects
UNEXPECTED DIFFERENCES: stale V1 baseline contains additional pre-existing drift; no current-policy regression
```

COMMON STUDENT POLICY
=====================

المرحلة الحالية: `raw → independent cleaning → pre_common_v2 → filter_common_students(student_id) → final clean V2 → downstream`. لا يعتمد أي cleaner على output الآخر. بناء الخصائص يقرأ `student_status_v2.parquet` النهائي. نُقل سكربت المقارنة إلى `src/diagnostics/compare_student_status_course.py` وأصبح يقرأ V2 افتراضيًا.

| المؤشر | قبل | بعد |
|---|---:|---:|
| Status-only students | 623 | 0 |
| Course-only students | 290 | 0 |
| Status students | 13,415 | 12,792 |
| Course students | 13,082 | 12,792 |
| Status rows | 108,974 | 107,939 |
| Course rows | 459,620 | 456,595 |
| Status-only keys | 13,352 | 12,317 |
| Course-only keys | 715 | 34 |
| Both keys | 95,622 | 95,622 |

Removed from status: **623 students / 1,035 rows**. Removed from course: **290 students / 3,025 rows**. بقيت جميع صفوف الطلاب المشتركين حتى عند اختلاف degree/part. بعد السياسة، محاكاة الـinner merge أسقطت **142 من 456,595** صف مقرر (0.0311%)، ولم يُفقد أي طالب بالكامل.

تحققنا من تطابق محتوى جدولي V2 النهائيين بالكامل مع جدولي `pre_common_v2` بعد تطبيق تقاطع `student_id` فقط؛ لم تتغير القيم أو الأعمدة أو الأنواع في الصفوف الباقية. اختبارات السلسلة تستخدم ملفات V1 sentinel، وتتحقق أن بناء الخصائص يقرأ status V2 النهائي.

حُذفت 16 ملف V2 موجودًا بعد التحقق من قائمة مسارات صريحة وامتداد `_v2`، ثم أُعيد بناء 18 ملف V2 (بما فيها ملفا `pre_common_v2`) عبر عشر مراحل. لم يُحذف `CATEGORY_LEVELS_PATH_V2` لأنه غير موجود وينتجه التدريب خارج نطاق هذه السلسلة. بقيت مجلدات frozen history ومخرجات V1 وraw والنماذج كما هي. تطابقت SHA-256 لـ461 ملفًا محميًا قبل وبعد، وطابق manifest التاريخي للملفات الـ461 أيضًا.

التحقق الحالي: **260 data tests passed؛ 26 feature tests passed؛ 323 full-suite tests passed، 0 failed**. نجح compile لكل `src` واستيراد 40 module. تفاصيل إعادة البناء والقيم في `common_student_policy/rebuild_results.json`، والمقارنة في `student_status_course_comparison.md`.

```text
COMMON STUDENT POLICY: PASS
V2 REBUILD: PASS
V2 PIPELINE: PASS
FULL TEST SUITE: PASS
RAW DATA: UNCHANGED
V1 ARTIFACTS: UNCHANGED
```
