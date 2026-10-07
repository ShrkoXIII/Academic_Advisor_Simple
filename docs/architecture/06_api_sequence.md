# 06 — API Sequence

**FastAPI وPHP Backend غير منفذين داخل هذا repository وقت الفحص2026-10-06.** يوجد core محلي ومساعدات payload جاهزة، لكن لا HTTP endpoints أو Pydantic transport schema أو authentication/client/retry implementation. `pyproject.toml` لا يعلن FastAPI أو Uvicorn dependency. عدم وجودهما هنا لا يحكم على repository آخر تابع للشركة.

## A. التسلسل المنفذ محليًا — 6 أطراف

```mermaid
sequenceDiagram
    actor U as User / local operator
    participant CLI as Local CLI
    participant I as Local input adapters
    participant E as AcademicPlanRecommender
    participant A as Models / Frozen History
    participant O as Local output files
    U->>CLI: Candidates file + identity + target + credits + history cutoff
    CLI->>I: load_local_inputs
    I->>I: Normalize candidates / catalog / prior attempts
    I->>I: Build or validate target-start snapshot
    I-->>CLI: Normalized candidates + snapshot + import report
    CLI->>E: AcademicPlanRecommender.load(history_as_of_part)
    E->>A: Load Grade47 / Fail47 / categories / GradeScale / V2 bundle
    A-->>E: Existing validated assets + provenance
    CLI->>O: Save candidate / snapshot / import inputs
    CLI->>E: recommend(snapshot, candidates, target, credits)
    E->>A: Apply course history; predict per-plan course rows
    A-->>E: History features / mark / fail probability
    E->>E: Plan context / GradeScale / GPA projection / ranking
    E-->>CLI: All summaries + Top N + status / provenance
    CLI->>O: save_recommendations streams courses and saves plans / result
    CLI-->>U: Status and output directory
```

الرسم يلخص artifacts خلف طرف واحد؛ `GradeScale` يُحمّل أيضًا، ثم التحويل يتم ضمن `score_rows`. أثناء `save_recommendations` يجري streaming بالتزامن مع scoring؛ رسم الحفظ النهائي يلخص ذلك ولا يؤخر جميع الكتابات إلى نهاية الطلب.

| التسلسل | الدليل |
| --- | --- |
| User → CLI → adapters | [recommend_local.py](../../src/recommend_local.py) → [local_cli.py](../../src/recommendation/local_cli.py): `main` → [inputs.py](../../src/recommendation/inputs.py): `load_local_inputs`. |
| Load → assets | [engine.py](../../src/recommendation/engine.py): `load` → [artifacts.py](../../src/recommendation/artifacts.py): `load_recommendation_artifacts` → [frozen_history.py](../../src/features/frozen_history.py): `load_frozen_history`. |
| Request → inference → ranking | `engine.recommend/prepare_candidates/score_rows` → [plan_generation.py](../../src/recommendation/plan_generation.py)، [temporal_features.py](../../src/features/temporal_features.py)، [plan_scoring.py](../../src/recommendation/plan_scoring.py). |
| Response → files | [output.py](../../src/recommendation/output.py): `save_recommendations` و`write_json`؛ CLI يعرض path/status فقط. لا PHP response منشور. |

## B. Planned Integration — 7 أطراف

**كل تفاعل في الرسم التالي مخطط**. الأسماء التي تقابل كودًا موجودًا موضحة في جدول الأدلة؛ ليس وجود `recommend` دليلًا على أن FastAPI يستدعيه الآن. لا تُقترح هنا أسماء endpoints أو HTTP methods/status codes كعقد معتمد.

```mermaid
sequenceDiagram
    actor S as Student
    participant PHP as PHP Backend - Planned
    participant API as FastAPI - Planned Integration
    participant E as Recommendation Engine
    participant M as Models
    participant H as Frozen History
    participant R as Response adapter - Planned
    Note over PHP,API: Transport, authentication, errors and versions are not implemented here
    Note over API,H: Planned startup loads assets once per worker
    API->>M: Planned: load pinned compatible models / categories / GradeScale
    API->>H: Planned: load selected valid V2 history
    S->>PHP: Planned: request a recommendation
    PHP->>PHP: Planned: authorize identity; supply eligible courses / snapshot / policies
    PHP->>API: Planned: versioned student context + request
    API->>API: Planned: validate transport and adapt core payloads
    API->>E: Planned: call selected engine with prepared context
    E->>H: Planned: apply finalized history before target
    H-->>E: Planned: seven course-history features
    E->>E: Planned invocation of existing plan generation / plan context
    E->>M: Planned: grade / fail batch inference
    M-->>E: Planned: predicted marks / probabilities
    E->>E: Planned invocation of GPA projection / ranking
    E-->>R: Planned: Top N / status / provenance
    R-->>API: Planned: serializable response under agreed schema
    API-->>PHP: Planned: response
    PHP-->>S: Planned: show recommendations
```

هذا اتجاه فصل PHP عن ML service، وليس إعلان اختيار baseline47 أو Two-Stage غير المكتمل للتشغيل المنتج. يمكن تغليف المحرك الحالي لاحقًا، لكن request الجديد ذو constraints يحتاج ربطًا فعليًا؛ لا يكفي تمرير payload إلى baseline لإعمال تلك القيود.

## دليل الموجود مقابل المخطط

| خطوة متوقعة | ما يوجد فعليًا | ما لم يُنفذ / يُثبت |
| --- | --- | --- |
| Student → PHP | اتجاه المنتج في [PRODUCTION_CONTRACT.md](../PRODUCTION_CONTRACT.md). | Login/session/UI وPHP source خارج هذا checkout. |
| PHP → context | exports فعلية في `data/raw/` وحقول View في [api_request_column_mapping.md](../../reports/api_request_column_mapping.md). | Live queries وتعريفات Views وتوقيت تحديثها ومعنى الأهلية النهائي وسياسات الجامعة. |
| PHP → FastAPI | الاتجاه موثق في [LOCAL_RECOMMENDATION.md](../../LOCAL_RECOMMENDATION.md) و[PRODUCTION_CONTRACT.md](../PRODUCTION_CONTRACT.md). | لا FastAPI app/route أو PHP HTTP client أو منشور request/response contract. |
| API → normalize | [inputs.py](../../src/recommendation/inputs.py): `prepare_recommendation_payloads` و`normalize_*_payload` تعمل in-process بلا I/O. | Transport/schema adapter الذي يستدعيها؛ لا route موجودة. |
| Context → policies | [course_status.py](../../src/recommendation/course_status.py) و[constraints.py](../../src/recommendation/constraints.py) يفصلان status والحدود. | Engine orchestration الذي يطبقها؛ baseline يستخدم enumerator غير المقيد بها. |
| Engine → models | `AcademicPlanRecommender.load/score_rows` منفذان؛ `load_two_stage_artifacts` منفذ للأصول فقط. | خدمة worker lifecycle، واختيار/تفعيل Two-Stage أو اعتماد استراتيجياته. |
| Engine → history | `CourseHistoryState.apply` + frozen loader منفذان؛ manager/Delta موجودان محليًا. | ربط manager بـbaseline أو endpoint update/admin job؛ latest-valid manager لا يغير سياسة baseline الصريحة. |
| Engine → Response | `recommend` ينتج dict والـCLI يحفظ `result.json`؛ [output.py](../../src/recommendation/output.py). | Published HTTP response adapter/version/errors/serialization contract. |
| Response → PHP → Student | لا تنفيذ مثبت. | Display وregistration writeback؛ recommendation ليست تسجيلًا تلقائيًا. |

## فصل التحديث عن الطلب

البناء offline في [build_frozen_history.py](../../src/features/build_frozen_history.py) مستقل عن التدريب. المكون المحلي [history_update.py](../../src/recommendation/history_update.py) يقبل finalized aggregate payload، ينسخ state ويضيف المجاميع، ثم يستدعي `save_frozen_history_atomic` ويتحقق وينشر إصدارًا immutable قبل تبديل reference. لا يجلب raw rows، ولا يعيد تدريب المودلات، ولا ينفذ scoring.

هذا implementation جديد وغير موصول بالـAPI أو `AcademicPlanRecommender`؛ سجلت الخطة إتمام Phase3 أثناء العمل المتزامن. إقرار `finalized=True` لا يثبت أن الجامعة أغلقت الفصل. البروتوكول لتحديث service/admin scheduling ومصدر الإقرار غير منفذين هنا. كذلك إعادة التدريب الحالية تكتب في official paths؛ لا ينبغي رسمها كعملية request-time أو endpoint نشر مكتمل.

## Flows لا يمكن إثباتها من الكود

1. University DB → PHP → raw/ML service عبر connector حي؛ الموجود exports ومكتبة `oracledb` فقط.
2. Student HTTP request → PHP → FastAPI endpoint → engine فعليًا.
3. Offer capacity أو prerequisites أو استثناءات الجامعة تتحقق تلقائيًا داخل ML engine؛ ملفات offer/prerequisite المطلوبة غير موجودة.
4. Constraints/Balance/shortlist33 → ≤50 → final47 في طلب متكامل؛ المكونات الجزئية لا تساوي engine.
5. History Delta تُرسل تلقائيًا عند finalization أو تُبدّل history المستخدمة في baseline الحالي.
6. نتائج Top N تُسجل في نظام الجامعة، أو يتحسن GPA الفعلي لخطط لم يسجلها الطالب.

لم نفترض URLs أو endpoints أو قواعد أهلية أو سياسات إحلال درجات لحل هذه الفجوات.

عودة إلى [Architecture Map](README.md).
