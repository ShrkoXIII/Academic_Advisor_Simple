# Student status/course V2 comparison

The section below is the **before-policy audit** retained for comparison. The current results after rebuilding V2 are in `COMMON STUDENT POLICY` at the end of this report.

Source files:
- `data/clean/student_status_v2.parquet`
- `data/clean/student_course_v2.parquet`

No production code, raw input, V1 artifact, or V2 artifact was modified. The two unmatched-key Parquet files are diagnostic outputs only.

STUDENT LEVEL
=============

Students in status: 13,415
Students in course: 13,082
Students in both: 12,792
Only in status: 623
Only in course: 290

Status-only student examples (first 20 summaries):

```text
student_id  number_of_rows  number_of_degrees  first_part  last_part
 10175.111               2                  1       20201      20202
 10340.111               1                  1       20201      20201
 10364.111               1                  1       20201      20201
 10501.111               4                  1       20201      20212
 10536.111               1                  1       20201      20201
 10539.111              14                  1       20201      20252
 10579.111               1                  1       20211      20211
 10606.111               9                  1       20201      20232
 10609.111               2                  1       20201      20202
 10865.111               3                  1       20201      20211
 11168.111               1                  1       20201      20201
 11211.111               2                  1       20201      20202
 11384.111               1                  1       20201      20201
 11433.111               1                  1       20201      20201
 11497.111               2                  1       20201      20202
 11506.111               3                  1       20201      20211
 11517.111               1                  1       20201      20201
 11523.111               1                  1       20201      20201
 11573.111               1                  1       20201      20201
 11683.111               1                  1       20201      20201
```

Course-only student examples (first 20 summaries):

```text
student_id  number_of_rows  number_of_degrees  first_part  last_part
 10952.111              12                  1       20201      20213
 11265.111              10                  1       20201      20202
 11972.111              26                  1       20201      20222
 12597.111               5                  1       20201      20201
 12713.111               8                  1       20201      20202
 13325.111               5                  1       20201      20201
 13358.111              11                  1       20201      20202
 13372.111              29                  1       20201      20221
 13509.111               8                  1       20201      20202
 13580.111               3                  1       20201      20201
 13980.111               7                  1       20201      20202
 14004.111              40                  1       20201      20233
 14032.111              15                  1       20201      20211
 14052.111               7                  1       20201      20202
 14066.111               3                  1       20201      20201
 14082.111               5                  1       20201      20201
 14099.111              10                  1       20201      20203
 14133.111              27                  1       20201      20232
 14223.111               8                  1       20201      20203
 14336.111               2                  1       20201      20201
```

KEY LEVEL
=========

Key = `student_id + degree_id + part_id`

Status keys: 108,974
Course keys: 96,337
Both: 95,622
Status-only: 13,352
Course-only: 715
Status-only percentage: 12.2525%
Course-only percentage: 0.7422%

Status-only keys (first 30):

```text
student_id degree_id  part_id
 10011.111    13.111    20232
 10011.111    13.111    20252
 10017.111     2.111    20211
 10018.111     2.111    20212
 10020.111     2.111    20221
 10021.111    13.111    20253
 10024.111     2.111    20211
 10043.111     1.111    20212
 10046.111     2.111    20201
 10046.111     2.111    20202
 10053.111     2.111    20202
 10056.111    13.111    20232
 10056.111    13.111    20242
 10056.111    13.111    20243
 10056.111    13.111    20251
 10056.111    13.111    20252
 10062.111     1.111    20221
 10062.111     1.111    20222
 10071.111     2.111    20202
 10076.111     2.111    20201
 10076.111     2.111    20202
 10078.111     2.111    20201
 10078.111     2.111    20202
 10079.111     1.111    20212
 10079.111     1.111    20221
 10079.111     1.111    20222
 10079.111     1.111    20223
 10079.111     1.111    20231
 10079.111     1.111    20253
 10092.111     2.111    20202
```

Course-only keys (first 30):

```text
student_id degree_id  part_id
 10952.111    13.111    20201
 10952.111    13.111    20202
 10952.111    13.111    20203
 10952.111    13.111    20212
 10952.111    13.111    20213
 11265.111    13.111    20201
 11265.111    13.111    20202
 11972.111    24.111    20201
 11972.111    24.111    20202
 11972.111    24.111    20203
 11972.111    24.111    20211
 11972.111    24.111    20212
 11972.111    24.111    20213
 11972.111    24.111    20221
 11972.111    24.111    20222
 12597.111    24.111    20201
 12713.111     3.111    20201
 12713.111     3.111    20202
 13325.111    13.111    20201
 13358.111     6.111    20201
 13358.111     6.111    20202
 13372.111    13.111    20201
 13372.111    13.111    20202
 13372.111    13.111    20203
 13372.111    13.111    20211
 13372.111    13.111    20212
 13372.111    13.111    20213
 13372.111    13.111    20221
 13509.111    24.111    20201
 13509.111    24.111    20202
```

STATUS-ONLY CLASSIFICATION
==========================

Completely absent students: 1,035 keys / 623 students
Existing students with unmatched degree/part: 12,317 keys / 7,493 students

Detailed classification:

```text
                                   classification  key_count  unique_students
       same student and degree, different part_id      12279             7486
       student completely absent from other table       1035              623
       same student, different degree + part combination         38               16
```

No status-only or course-only key was classified as “same student and part, different degree”: **0 keys in both directions**.

COURSE-ONLY CLASSIFICATION
==========================

Completely absent students: 681 keys / 290 students
Existing students with unmatched degree/part: 34 keys / 21 students

Detailed classification:

```text
                                   classification  key_count  unique_students
       student completely absent from other table        681              290
same student, different degree + part combination         23               10
       same student and degree, different part_id         11               11
```

BY PART
=======

Status-only:

```text
 part_id  key_count  unique_students  unique_degrees
   20253       4659             4659              47
   20251       1269             1269              47
   20242       1047             1047              39
   20252       1013             1013              47
   20211        599              599              17
   20241        575              575              31
   20231        539              539              34
   20222        526              526              24
   20221        495              495              20
   20232        477              477              34
   20212        457              457              15
   20201        348              348              14
   20202        322              322              15
   20233        246              246              31
   20223        242              242              21
   20213        205              205              15
   20243        202              202              30
   20203        129              129              13
   20261          2                2               2
```

Course-only:

```text
 part_id  key_count  unique_students  unique_degrees
   20231         89               89              18
   20211         82               82               8
   20232         82               82              20
   20201         70               70               9
   20221         58               58              13
   20202         57               57               9
   20212         50               50               8
   20222         45               45              13
   20241         36               36              14
   20233         26               26              16
   20242         24               24              10
   20213         22               22               7
   20203         20               20               7
   20251         19               19              11
   20223         17               17              10
   20252         11               11               6
   20243          7                7               6
```

BY DEGREE (top 20)
==================

Status-only:

```text
degree_id  key_count  unique_students  first_part  last_part
    2.111       2044             1348       20201      20253
   13.111       1359              670       20201      20253
    1.111       1303              688       20201      20253
   41.111       1018              881       20231      20253
   24.111        734              388       20201      20253
   42.111        721              597       20231      20253
   22.111        658              283       20201      20253
   40.111        560              354       20231      20253
    3.111        538              249       20201      20253
   44.111        476              362       20231      20253
    8.111        287              130       20201      20253
   26.111        275              166       20221      20253
   50.111        262              178       20231      20253
   11.111        246              125       20201      20253
   21.111        238              142       20201      20232
    6.111        224               87       20201      20253
   29.111        204              123       20221      20253
   27.111        171              100       20221      20253
   47.111        163              105       20231      20253
   48.111        155              101       20231      20253
```

Course-only:

```text
degree_id  key_count  unique_students  first_part  last_part
   22.111        119               45       20201      20243
   13.111         82               37       20201      20233
   44.111         48               24       20231      20252
    1.111         43               21       20201      20222
    2.111         43               13       20201      20241
   40.111         40               25       20231      20251
   24.111         39               18       20201      20222
   21.111         37               19       20201      20212
   39.111         26               11       20221      20232
   42.111         26               15       20231      20252
    3.111         25                7       20201      20242
   41.111         24               10       20231      20252
   26.111         20                5       20221      20233
   49.111         19                6       20231      20251
   45.111         18                9       20231      20251
   27.111         16                6       20221      20233
   47.111         16                8       20231      20251
   48.111         14                7       20231      20252
   30.111         11                3       20221      20241
   50.111         11                7       20231      20252
```

KEY DIFFERENCE REASONS
======================

Classification priority for students present in both tables: same student+part with different degree, then same student+degree with different part, then a different degree+part combination.

Status-only detailed classification:

```text
                                   classification  key_count  unique_students
       same student and degree, different part_id      12279             7486
       student completely absent from other table       1035              623
same student, different degree + part combination         38               16
```

Course-only detailed classification:

```text
                                   classification  key_count  unique_students
       student completely absent from other table        681              290
same student, different degree + part combination         23               10
       same student and degree, different part_id         11               11
```

INNER MERGE IMPACT
==================

Course rows before: 459,620
Course rows after: 456,453
Dropped rows: 3,167
Dropped percentage: 0.6890%

Students before: 13,082
Students after: 12,792
Students completely lost: 290

Course row coverage by status key
---------------------------------
Matched course rows: 456,453
Unmatched course rows: 3,167
Coverage: 99.3110%

Status row coverage by course key
---------------------------------
Matched status rows: 95,622
Unmatched status rows: 13,352
Coverage: 87.7475%

CURRENT CLEANER DEPENDENCY
==========================

student_course depends on student_status keys: NO
student_status depends on course keys: NO

The two cleaners read raw inputs independently. The status/course key merge occurs later in `build_student_course_enriched.py`.

LEGACY DIAGNOSTIC SCRIPT
========================

At the time of this read-only audit, `src/compare_student_status_course.py` read V1 constants. It has since moved to `src/diagnostics/compare_student_status_course.py` and reads V2 constants by default.

CONCLUSION
==========

- Complete students present only in status: 623; complete students present only in course: 290.
- At key level, 13,352 status keys and 715 course keys are unmatched.
- The simulated inner merge drops 3,167 course rows (0.6890%) and completely loses 290 course students.
- Status row coverage by course key is 87.7475%; course row coverage by status key is 99.3110%.
- The mismatch is measured on the composite student+degree+part key; student-level presence and key-level alignment are materially different questions.

Potential data issue:

- 290 students are completely absent from `student_status_v2` while contributing 3,025 rows and 681 keys to `student_course_v2`; these rows are lost by the simulated inner merge.
- A further 142 course rows belong to students present in status but have an unmatched degree/part key.
- `status_only` is concentrated in `20253` (4,659 keys), while only 2 status-only keys occur in `20261`; review whether the semester pattern reflects the intended status snapshot coverage.
- Review the part/degree distributions below before treating all unmatched keys as missing students. The classification distinguishes absent students from existing students whose degree/part key differs.

Artifacts:
- `reports/data_features_v2_20260921/student_status_only_keys_v2.parquet`
- `reports/data_features_v2_20260921/student_course_only_keys_v2.parquet`
- `reports/data_features_v2_20260921/student_status_course_comparison_metrics.json`

COMMON STUDENT POLICY
=====================

Independent cleaning now writes `student_course_pre_common_v2.parquet` and `student_status_pre_common_v2.parquet`. `src/data/filter_common_students.py` intersects **student_id only** and writes the final V2 clean tables. Students shared by the tables retain every row, including rows with unmatched degree/part keys. The independent cleaner functions and cleaning rules did not change.

| Student comparison | Before | After |
|---|---:|---:|
| Status students | 13,415 | 12,792 |
| Course students | 13,082 | 12,792 |
| Both | 12,792 | 12,792 |
| Status-only students | 623 | 0 |
| Course-only students | 290 | 0 |
| Status rows | 108,974 | 107,939 |
| Course rows | 459,620 | 456,595 |

Removed from status: **623 students and 1,035 rows**. Removed from course: **290 students and 3,025 rows**. The pre-common V2 counts and key/merge metrics reproduce the previous V2 baseline; this is a metrics comparison, not a full-content equality claim.

For the rebuilt files, both final V2 tables were also compared column by column with their corresponding pre-common tables filtered on the shared student IDs. Both comparisons passed with exact pandas value/dtype equality after resetting row indexes.

KEY ALIGNMENT AFTER STUDENT FILTER
==================================

| Composite key `(student_id, degree_id, part_id)` | Before | After |
|---|---:|---:|
| Status keys | 108,974 | 107,939 |
| Course keys | 96,337 | 95,656 |
| Both | 95,622 | 95,622 |
| Status-only | 13,352 | 12,317 |
| Course-only | 715 | 34 |

The remaining unmatched keys belong to students present in both tables. They were intentionally retained under this policy. The previous diagnostic unmatched-key Parquet files above describe the **before** snapshot; they were not rewritten as current outputs.

INNER MERGE AFTER POLICY
========================

The V2 diagnostic script simulated `course.merge(status, on=["student_id", "degree_id", "part_id"], how="inner", validate="many_to_one")`.

- Course rows before merge: **456,595**
- Course rows after merge: **456,453**
- Dropped rows: **142 (0.0311%)**
- Students before and after merge: **12,792**
- Students completely lost: **0**

Rebuild evidence: `common_student_policy/rebuild_results.json` records all 10 stages, 16 deleted old V2 files, 18 rebuilt V2 files, and unchanged SHA-256 for 461 protected data/model files. The 461 files include the six raw files and all V1 artifacts. The original 461-file manifest also matches current files exactly. Full test suite: **323 passed, 0 failed**; data: **260 passed**; features: **26 passed**. Compile and import checks passed for all 40 `src` Python modules.
