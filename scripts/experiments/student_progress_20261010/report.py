"""Build the requested report from executed, authenticated local evidence."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src import paths
from src.features.frozen_history import file_sha256
from .workflow import OUTPUT, MODELS, HERE, FIELDS, VARIANTS, verify_protected, write_json


def table(frame, digits=6):
    def cell(value):
        if pd.isna(value):
            return '—'
        if isinstance(value,(float,np.floating)):
            return f'{value:.{digits}g}'
        return str(value).replace('|','/')
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |',
                      '| '+' | '.join(['---']*len(frame.columns))+' |',
                      *['| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None)]])


def deltas(frame):
    metrics=[c for c in frame.select_dtypes(include='number').columns
             if c not in ['year','features','fit_rows','rows','plans','projected_comparable_plans']]
    baseline=frame[frame.variant.eq('A')][['year','model',*metrics]]
    merged=frame.merge(baseline,on=['year','model'],suffixes=('','_A'),validate='many_to_one')
    for metric in metrics:
        merged[f'{metric}_delta']=merged[metric]-merged[f'{metric}_A']
        merged[f'{metric}_relative_pct']=100*merged[f'{metric}_delta']/merged[f'{metric}_A'].replace(0,np.nan)
    return merged


def build():
    execution=json.loads((OUTPUT/'execution.json').read_text())
    if execution['status']!='COMPLETE':
        raise ValueError('No complete experiment evidence')
    protection=verify_protected()
    setup=json.loads((OUTPUT/'setup.json').read_text())
    integrity=json.loads((OUTPUT/'artifact_integrity.json').read_text())
    if (integrity['status']!='PASS' or integrity['models_verified']!=108
            or integrity['executed_source_sha256']!=setup['workflow_sha256']
            or integrity['current_runner_sha256']!=file_sha256(HERE/'workflow.py')):
        raise ValueError('Artifact verification must match the completed study and current runner')
    metrics=pd.read_csv(OUTPUT/'metrics.csv')
    if len(metrics)!=108 or metrics[['year','model','variant']].duplicated().any():
        raise ValueError('Incomplete or duplicate ablation cells')
    compared=deltas(metrics)
    compared.to_csv(OUTPUT/'metric_deltas.csv',index=False)
    intervals=pd.read_csv(OUTPUT/'paired_intervals.csv')
    group=deltas(pd.read_csv(OUTPUT/'groups.csv').rename(columns={'group':'cohort'}).assign(
        model=lambda x:x.model+' / '+x.group_kind+' / '+x.cohort))
    group.to_csv(OUTPUT/'group_deltas.csv',index=False)
    subgroup_rows=[]
    cells=group[group.variant.eq('C')].assign(model=lambda x:x.model.str.split(' / ').str[0])
    for (year,model,kind),part in cells.groupby(['year','model','group_kind'],sort=False):
        metric='log_loss' if model.endswith('fail') else 'plan_gpa_mae'
        changes=part[metric+'_delta'].dropna()
        subgroup_rows.append({'year':year,'model':model,'slice':kind,'metric':metric,
            'evaluated_slices':len(changes),'worse_slices':int(changes.gt(0).sum()),
            'better_slices':int(changes.lt(0).sum()),'minimum_delta':changes.min(),
            'maximum_delta':changes.max()})
    subgroup_summary=pd.DataFrame(subgroup_rows)
    subgroup_summary.to_csv(OUTPUT/'C_subgroup_summary.csv',index=False)
    pooled=compared.groupby(['model','variant'],sort=False).agg(
        grade_mae=('grade_mae','mean'),grade_delta_pct=('grade_mae_relative_pct','mean'),
        points_mae=('course_points_mae','mean'),plan_gpa_mae=('plan_gpa_mae','mean'),
        plan_delta=('plan_gpa_mae_delta','mean'),plan_delta_pct=('plan_gpa_mae_relative_pct','mean'),
        log_loss=('log_loss','mean'),logloss_delta_pct=('log_loss_relative_pct','mean'),
        pr_auc=('pr_auc','mean'),roc_auc=('roc_auc','mean')).reset_index()
    pooled.to_csv(OUTPUT/'fold_mean_summary.csv',index=False)
    # Conservative retention is distinct from proving every explicit feature indispensable.
    decision='KEEP_ALL'
    write_json(OUTPUT/'decision.json',{'decision':decision,'production_action':'KEEP existing four features',
        '2025_evaluated':False,'reason':'C has small paired direct-points losses in both folds; grade/fail effects vary by family/year; no tested reduced set establishes universally harmless removal; no agreed tolerance',
        'api_removal_approved':False,'gpa_denominator_removal_approved':False})
    defs=pd.DataFrame([
        ['start_total_in_credits','start_total_in_credits','float; direct status join','Source start credit counter; earned/passed/GPA-counted rules UNVERIFIED'],
        ['start_total_in_courses','start_total_in_courses','integer; direct status join','Source start course counter; inclusion/repeats rules UNVERIFIED'],
        ['prior_total_reg_credits','total_reg_credits','float; exact direct alias, no shift','Code treats cumulative registration credits as prior state; official rules UNVERIFIED'],
        ['prior_total_reg_courses','total_reg_courses','integer; exact direct alias, no shift','Code treats cumulative registration course count as prior state; official rules UNVERIFIED'],
    ],columns=['Model input','Raw view column','Transformation','Supported interpretation'])
    summary=pd.read_csv(HERE/'evidence/summary.csv')
    pair=pd.read_csv(HERE/'evidence/pairwise.csv')
    examples=pd.read_csv(HERE/'evidence/anonymized_examples.csv')
    configurations=[]
    for year in [2023,2024]:
        for spec in setup['specs']:
            selection=json.loads((OUTPUT/str(year)/spec['name']/'inner_selection.json').read_text())
            selected=selection['selected']; p=selected['parameters']
            configurations.append({'year':year,'model':spec['name'],'inner_fit_through':selection['inner_fit_max_part'],
                'inner_validation':','.join(map(str,selection['inner_validation_parts'])),
                'candidate':selected['candidate']['name'],'rounds':selected['rounds'],
                'leaves':p['num_leaves'],'min_leaf':p['min_data_in_leaf'],'feature_fraction':p['feature_fraction'],
                'bagging_fraction':p['bagging_fraction'],
                'L1':p['lambda_l1'],'L2':p['lambda_l2']})
    configurations=pd.DataFrame(configurations)
    configurations.to_csv(OUTPUT/'configurations.csv',index=False)
    ranking=pd.read_csv(OUTPUT/'ranking_sensitivity.csv')
    rank_summary=ranking.groupby(['family','variant'],sort=False).agg(
        cases=('case','size'),top1_changes=('top1_changed','sum'),top3_set_changes=('top3_set_changed','sum'),
        maximum_plan_gpa_delta=('max_plan_gpa_delta','max')).reset_index()
    rank_summary.to_csv(OUTPUT/'ranking_summary.csv',index=False)
    importance=pd.read_csv(OUTPUT/'selected_gain.csv')
    importance=importance[importance.feature.isin(FIELDS)]
    perm=pd.read_csv(OUTPUT/'complete_plan_permutation.csv').groupby(['year','model','fields','metric'],sort=False).agg(
        mean_delta=('delta','mean'),min_delta=('delta','min'),max_delta=('delta','max')).reset_index()
    perm.to_csv(OUTPUT/'permutation_summary.csv',index=False)
    c=pooled[pooled.variant.eq('C')]
    lines=['# Student Academic Progress Feature Audit and Ablation',
        '\nDate: 2026-10-10. Audit status: **PARTIAL**. Experimental matrix: **COMPLETE**. Final recommendation: **KEEP_ALL** for now. Production action: retain the existing four features pending a separately approved simplification decision.',
        '\n## 1. Executive Summary',
        '\nExecuted 108 outer ablation fits (nine configurations × six model tasks/profiles × two years) and 36 baseline-only inner tuning fits on existing V2 tables. No new 2025 model evaluation occurred. Source/alias/join checks, empirical statistics, Plan GPA, paired uncertainty, subgroup analysis, importance and fixed-candidate sensitivity are recorded. University view definitions, snapshot mutability and official cumulative-GPA denominators are **UNVERIFIED**, so the audit cannot receive an unconditional PASS.',
        '\nHigh aggregate correlation does not imply equivalence: on 356,816 training course rows, start versus registration credits correlate 0.898350 (Spearman 0.935258), but are exactly equal on only 27.3968%; course counts correlate 0.901001 and are equal on 28.2173%. No deterministic mapping between any pair was found. Removing explicit inputs leaves `prior_fail_credit_ratio` and other progress/GPA proxies intact.',
        '\nVariant C (registered credits only), equal-weight mean across the two validation folds:', table(c[['model','grade_mae','grade_delta_pct','plan_gpa_mae','plan_delta_pct','log_loss','logloss_delta_pct']]),
        '\nThese fold means are descriptive; the actual per-fold results and student-cluster confidence intervals govern interpretation. They do not establish official denominator correctness or counterfactual ranking quality.',
        '\n## 2. Feature Definitions',table(defs),
        '\nAll four raw fields are doubles in `data/raw/v_add_student_degree_status.parquet` (189,158 physical rows), named by `src/paths.py:35`. The upstream source is the exported view `v_add_student_degree_status`; its underlying tables, SELECT expression, stored procedure and business definitions are absent. Do not relabel any field as earned, passed, attempted or GPA-counted solely from its name.',
        '\nSource-to-model lineage:',
        '\n| Raw Source | Cleaning | Feature Engineering | Training Matrix | Model | Recommendation |\n|---|---|---|---|---|---|\n| `v_add_student_degree_status.start_total_in_credits` | `clean_student_status.py:156–173`, numeric cast, retained | `build_student_course_enriched.py:28–34`, exact `(student,degree,part)` status join | `feature_contract.py:35–38,138–165`, float32 | Official V2 47; shortlist 33; degree-history 57; direct-points research | `inputs.py:133–154,196–199,251–272`; `engine.py:65–82`; `two_stage_engine.py:154–171` |\n| `v_add_student_degree_status.start_total_in_courses` | `clean_student_status.py:141–154`, integer cast, retained | Same status join, no cumulative reconstruction | Same ordered numeric contract | Same consumers | Same required snapshot; no substitution from candidate counts |\n| `v_add_student_degree_status.total_reg_credits` | `clean_student_status.py:156–173`, numeric cast, retained | `temporal_features.py:316`, direct `prior_total_reg_credits`; ratio at `:319–322` | Same matrix conversion | Same consumers | Snapshot plus local GPA denominator fallback at `engine.py:21–34` |\n| `v_add_student_degree_status.total_reg_courses` | `clean_student_status.py:141–154`, integer cast, retained | `temporal_features.py:315`, direct `prior_total_reg_courses`; cold-start counter at `:325–330` | Same matrix conversion | Same consumers | Required current snapshot |',
        '\nLine references refer to current untouched source. Full evidence: [lineage audit](../scripts/experiments/student_progress_20261010/lineage_audit.md). Outlier checks `clean_outliers.py:201–225` and cleaning initial-GPA fallback `clean_student_status.py:67–84` also depend on these source columns.',
        '\n## 3. Temporal Availability',
        '\n| Class | Fields | Finding |\n|---|---|---|\n| `START_SNAPSHOT` under the implemented contract | `start_agpa_points`, `start_total_in_credits`, `start_total_in_courses`, diploma/catalog properties, explicit `current_gpa_credits` | Exact target-start snapshot; DB immutability, inclusion rules and finalized timing require confirmation |\n| `HISTORICAL_STATE` under the implemented contract | `prior_total_reg_*`, `prior_total_fail_*`, `prior_fail_credit_ratio`, earlier GPA, prior registered semesters, course/specialty history | Registration/failure totals are aliases of source start-state totals, not computed shifts; GPA/history apply strict prior-part cutoffs |\n| `CURRENT_PLAN` | `plan_*` / `peer_*` context, total candidate credits, course count | Calculated from each proposed combination; no outcome needed |\n| `END_OUTCOME` | `final_mark`, `is_fail`, `points`, `gpa_points`, `end_agpa_points`, `end_total_in_*`, semester pass/fail counters, finish fields | Evaluation labels/update inputs only; explicitly excluded from BASE_FEATURES |\n| `UNCERTAIN` at DB boundary | Official meaning and mutable/recomputed nature of all four counters; GPA denominator policy | Names and code comments are insufficient to certify the university view |',
        '\nEmpirical timing supports prior registration credits: among 70,054 adjacent clean V2 status transitions, `current total_reg_credits = previous total_reg_credits + previous semester_reg_credits` has one mismatch (0.001427%). Substituting current-semester registration produces 62,302 mismatches (88.9343%). Start credits versus previous end credits differ in 4,158 transitions (5.9354%); course-count registration transitions differ in 1,753 (2.5024%). These discrepancies need business-rule explanations; they are not automatically leakage.',
        '\nAll four training features match clean status on all 356,816 rows. V1/V2 common 2020–2024 status rows (82,300) have zero mismatches for 18 checked fields; V2 adds 5,592 status rows. Definitions/aliases agree on shared rows; cohorts and historical protocols differ. Current training, degree-points experiments and serving actually consume V2, despite stale V1 statements in AGENTS/older pipeline documentation. Source truth: `train_models.py:369–374,416–429`, `degree_points.py:42–48`, `recommendation/artifacts.py:47–51,74–77`.',
        '\nV2 course history applies then updates each finalized semester: 20251 sees 20243; 20252 sees 20251 (`temporal_features.py:228–270`). Earlier 20251 outcomes may enter 20252 only after finalization. V1 saved metadata uses history frozen after 20243. Student progress snapshots remain separate: publishing a 20251 course-difficulty Delta does not update student GPA/progress for 20252. Existing leakage/version/cutoff guards were preserved. No invalid prediction-time feature was demonstrated; external snapshot semantics remain uncertified.',
        '\nExact backend questions: provide the view SQL and base tables for the four columns; list inclusion rules for repeats, failures, withdrawals, transfers, exemptions and flags `in_credits/in_gpa/in_agpa`; confirm whether rows are historical immutable snapshots or recalculated live; state capture/finalization timestamps and degree-transfer rules; explain the transition exceptions; provide the official GPA credit denominator and repeat replacement policy.',
        '\n## 4. Correlation and Redundancy',
        '\nStatistical grain matters. Course rows weight semesters by finalized-course count. Unique training status groups number 75,076; their fields are constant within each group. Raw 2020–2024 has 92,741 rows (11 missing per field, 0.011861%); cleaned V2 has 87,892 rows. Training has no missing values for the four fields. Summary statistics below use sample standard deviation.',
        table(summary[summary.dataset.eq('train_v2_course')]),
        '\nAll six training-course pair correlations/equality/difference summaries:',table(pair[pair.dataset.eq('train_v2_course')]),
        '\nAt status grain, credit correlation is 0.900141 and equality 24.1569%; course-count correlation 0.896312 and equality 24.9547%. Within degree groups with ≥100 rows, credit correlations range 0.426–0.956 and course correlations 0.433–0.959. Within progress quartiles, ranges shrink to 0.400–0.680 and 0.518–0.700. Overall high correlation partly reflects the shared progress range. Year, degree, progress-quartile distributions, missing percentages, correlations, target relationships and directed deterministic tests are in the [descriptive audit](../scripts/experiments/student_progress_20261010/data_findings.md) and its [CSV evidence](../scripts/experiments/student_progress_20261010/evidence/stratified_pairwise.csv).',
        '\nThe four concepts cannot be collapsed through simple identities: in cleaned V2, start credits equal total passed credits in only about half the rows; registered credits differ from passed+failed credits in 55.3782%. Target relationships even change sign: course-points Pearson is +0.070779 for start credits versus −0.065524 for registered credits; failure correlations are −0.089245 versus +0.000239. Neither low univariate target correlation nor a high interfeature correlation establishes uselessness.',
        '\nRepresentative real source records (student keys are SHA-256 pseudonyms, shortened here; no original student/status identifiers):',
        table(examples.assign(student=lambda x:x.student_sha256.str[:12])[['reason','student','degree_id','part_id','start_total_in_credits','total_reg_credits','start_total_in_courses','total_reg_courses']].head(12)),
        '\nThe differences demonstrate distinct values, not a verified explanation such as repeated failures or transfers. Raw high extremes are source examples, not necessarily modeling-eligible records. Full pseudonymized records and differences are in [anonymized_examples.csv](../scripts/experiments/student_progress_20261010/evidence/anonymized_examples.csv); pseudonymization is not a guarantee of irreversible anonymity.',
        '\n## 5. Experimental Setup',
        '\nExisting `data/features/temporal_train_features_v2.parquet`: 356,816 rows, 20201–20243; SHA-256 `'+setup['sources']['data/features/temporal_train_features_v2.parquet']+'`. No pipeline rebuild. Outer 2023 fits through 20223; outer 2024 fits through 20233. Inner selection fits through 20213/20223 and validates 2022/2023 respectively. Categories come only from each training frame; weights are 0.25 before 2022 and 1.0 from 2022; seed 42; deterministic CPU LightGBM, four threads.',
        '\n| Variant | Model-input change only |\n|---|---|\n| A | Retain all four |\n| B | Retain both credits, drop both counts |\n| C | Retain only prior_total_reg_credits |\n| D | Retain only start_total_in_credits |\n| E | Drop all four explicit inputs |\n| F1 | Drop start_total_in_credits |\n| F2 | Drop start_total_in_courses |\n| F3 | Drop prior_total_reg_credits |\n| F4 | Drop prior_total_reg_courses |',
        '\nSix model specifications: 47 grade/fail, 33 grade/fail, 47 unweighted direct points (points_temporal research variant), and 57 unweighted degree-history grade matching the selected research profile. Direct points is not the selected production predictor; existing selected degree-points artifact predicts marks. Other research catalogs, including credit-weighted/direct-points degree-ID combinations, were audited but not all retrained; those are follow-ups if adopted. All remaining model inputs, raw columns and `prior_fail_credit_ratio` stay unchanged.',
        '\nNested baseline-only selection compares the existing `balanced_31`, `capaciy_63`, `regularized_47` grid on the inner year. Grade/points configurations are selected by historical Plan GPA MAE; failure by Log Loss. Early stopping uses the existing l1/binary_logloss metric (maximum 900 rounds, patience 75). The selected configuration and tree count are then frozen for A–F in the outer fit. This is a controlled fixed-configuration ablation, not independently tuned variant optimization. Baseline A is a nested retrained reference, not an exact reproduction of saved full-2024 production models.',table(configurations),
        '\nCommon parameters: learning rate .04, bagging frequency 1, max_bin 255, deterministic/force_col_wise true. Bagging fraction is .85 or .90 according to the selected candidate. The full parameter dictionaries, categories, ordered keys, dataset/source hashes and per-model feature/config/signature/SHA records are saved. Cache namespaces are isolated. Existing 2025 research results predate this task, so 2025 cannot be represented as a fresh blind holdout; this study performed no new 2025 model metrics or selection.',
        '\nRepeat the protocol from the root with `.\\.venv\\Scripts\\python.exe -m scripts.experiments.student_progress_20261010.workflow --output-name student_progress_followup`; a fresh isolated namespace is required. An existing output rejects an accidental overwrite. The 144 numerical fits used [executed_workflow.py](../scripts/experiments/student_progress_20261010/evidence/executed_workflow.py), whose SHA matches the recorded setup. Subsequent reusable-runner hardening pins imported implementation sources, authenticates inner selection with run/year/specification/ordered temporal-row context, publishes COMPLETE only after protection checks, and uses complete-plan permutation sampling. These safeguards were not retroactively used for the original fits. The original run did not resume a cache; all 108 saved outer models were independently verified against the archived protocol, exact features/order, categories, configuration, row fingerprints and SHA. The current runner correctly rejects the old namespace on `--resume`; no signatures were migrated and no fits were repeated after hardening. Models: `models/experiments/student_progress_20261010/`. Numerical evidence: `data/evaluation/experiments/student_progress_20261010/`.',
        '\n## 6. Model Performance',
        '\nPositive error/Log Loss/Brier differences mean harm; positive AUC differences mean improvement. PR-AUC here is sklearn average precision, matching the existing evaluator; ROC-AUC is omitted in any single-class subgroup. Bias retains its sign, so a relative bias change is not an improvement measure. Detailed [metric_deltas.csv](../data/evaluation/experiments/student_progress_20261010/metric_deltas.csv) contains every absolute and relative change. Equal-weight fold means below do not replace separate folds.',table(pooled),
    ]
    for name,part in compared.groupby('model',sort=False):
        cols=['year','variant']
        if name.endswith('fail'):
            cols+=['pr_auc','pr_auc_delta','roc_auc','roc_auc_delta','log_loss','log_loss_delta','log_loss_relative_pct','brier','brier_delta']
        else:
            if name.endswith('grade'):
                cols+=['grade_mae','grade_mae_delta','grade_rmse','grade_bias']
            cols+=['course_points_mae','course_points_rmse','plan_gpa_mae','plan_gpa_mae_delta','plan_gpa_mae_relative_pct','plan_gpa_rmse','plan_gpa_bias']
        lines.extend([f'\n### {name}',table(part[cols])])
    lines.extend([
        '\nPaired uncertainty resamples students with all corresponding course rows/observed plans, 1,000 draws, seed 42, percentile 95% intervals. This captures evaluation-case uncertainty conditional on one fitted model/configuration; it does not capture seed or hyperparameter uncertainty. Multiple exploratory comparisons were not multiplicity-adjusted. No product noninferiority margin was supplied; zero-overlap alone is not an approval policy. All cells in [paired_intervals.csv](../data/evaluation/experiments/student_progress_20261010/paired_intervals.csv).',
        '\nVariant C paired intervals:',table(intervals[intervals.variant.eq('C')][['year','model','metric','delta','low','high','students']]),
        '\nDegree and progress slices use ≥100 rows and fixed start-credit intervals `[0,30)`, `[30,60)`, `[60,90)`, `[90,∞)`. These bands describe the supplied counter, not certified earned hours. Full paired subgroup deltas: [group_deltas.csv](../data/evaluation/experiments/student_progress_20261010/group_deltas.csv). Descriptive quartiles and modeling bands deliberately use different summaries; neither is selected using performance.',
        '\nVariant C consistency by slice (positive loss changes mean worse; degree/progress summaries overlap the same evaluation students and are not independent replications). Minimum/maximum are observed point-estimate deltas, not uncertainty bounds; small cohorts cannot establish subgroup safety:',table(subgroup_summary),
        '\nCurrently selected relevant models: LightGBM gain importance (all four fields):',table(importance[['model','feature','gain_share_percent','rank']]),
        '\nNested baseline gain for all inputs: [baseline_gain.csv](../data/evaluation/experiments/student_progress_20261010/baseline_gain.csv). Reported validation permutation uses 1,000 complete observed student-semester plans per year, three repeats, changing each field or all four together at status level. Whole-plan group sampling preserves its Plan GPA interpretation. The original diagnostic partial-course sample is saved but is not the reported Plan GPA importance evidence. Dependent ratio stays unchanged; permutation breaks correlations and can create implausible feature combinations. The joint diagnostic tests four explicit columns only, not all progress information. Results: [permutation_summary.csv](../data/evaluation/experiments/student_progress_20261010/permutation_summary.csv). Low individual gain can reflect correlated competitors; gain/permutation alone cannot authorize removal.',
        '\nJoint four-field permutation increases the primary loss in every model/fold below, supporting joint predictive information conditional on the retained inputs. This does not establish that each individual feature is necessary or provide causal evidence:',table(perm[perm.fields.str.contains('\\+',regex=True)][['year','model','metric','mean_delta','min_delta','max_delta']]),
        '\n## 7. Downstream Recommendation Impact',
        '\nHistorical Plan GPA is credit-weighted predicted points over exactly the same modeled finalized-course records; zero-total-credit groups are excluded consistently. It is not necessarily the complete registration roster or official semester GPA. Plan-context training uses the fuller registration roster, whereas evaluation targets exist only for modeled finalized courses. This distinction applies identically to every variant.',
        '\nMeasured registration-context coverage:',table(pd.read_csv(OUTPUT/'plan_coverage.csv')),
        '\nSupplementary complete-registration comparison (course count and credits both match the existing roster context):',
        table(deltas(pd.read_csv(OUTPUT/'complete_registration_metrics.csv')).query("variant in ['A','C']")[[
            'year','model','variant','grade_mae','plan_gpa_mae','plan_gpa_mae_delta','log_loss','log_loss_delta']]),
        '\nAll nine configurations on this matched subset, and paired student intervals, are retained in [complete_registration_metrics.csv](../data/evaluation/experiments/student_progress_20261010/complete_registration_metrics.csv) and [complete_registration_intervals.csv](../data/evaluation/experiments/student_progress_20261010/complete_registration_intervals.csv). Matching roster context reduces coverage confounding but still does not certify official GPA counting rules.',
        '\nProjected cumulative GPA error against matched source end_agpa_points:',table(compared[compared.variant.isin(['A','C','E']) & compared.model.str.contains('grade|points')][['year','model','variant','projected_cumulative_gpa_mae_vs_end','projected_cumulative_gpa_mae_vs_end_delta','additive_observed_gpa_mae_vs_end','projected_comparable_plans']]),
        '\nThe observed-points additive control is nonzero even without model error. This is a separate policy/coverage/denominator reconciliation issue: registered credits need not equal official GPA credits; incomplete modeled rosters, repeats/replacement, exemptions and source semantics can also explain discrepancies. It does not identify the denominator alone as the cause, and improved projection under this policy does not establish official AGPA accuracy.',
        '\nExecuted fixed-candidate sensitivity: 12 eligible finalized-course pools per outer year, at most eight courses per pool, exact same credit target selected by most available alternatives before scoring; plan/peer context recomputed for each subset. Grade/fail 47 and 33 models rank standalone proposals by additive projected GPA, then failed credits, plan GPA, plan ID. No production engine, production two-stage shortlist, Balance strategy or active request was executed. This tests sensitivity under an explicitly fixed policy:',table(rank_summary),
        '\nPools are selected in deterministic key order and are not a representative live requestable universe. No observed outcomes exist for each alternative plan; Top-1/Top-3 changes demonstrate sensitivity, not superiority or harm in counterfactual recommendation quality. Exact pools/model SHA/signatures/caveats are saved in [downstream_provenance.json](../data/evaluation/experiments/student_progress_20261010/downstream_provenance.json).',
        '\n## 8. Backend Contract Implications',
        '\nThis is a recommended ownership contract, not an HTTP/PHP implementation. Current in-process ready payloads require all four snapshot fields; isolated matrix exclusion does not relax that validator.',
        '\n| Boundary | Field / information | Owner and timing |\n|---|---|---|\n| A: beginning request | student_id, degree_id, part_id, grade_version_id | Backend supplies exact target identity/version; Python validates |\n| A: beginning request | start_agpa_points and explicit current_gpa_credits | Backend supplies official start GPA and certified denominator; do not equate progress columns without university confirmation |\n| A: beginning request | start_total_in_credits, start_total_in_courses | Backend supplies verified target-start snapshot; currently required even for a proposed model removal |\n| A/B | prior_total_reg_credits/courses, prior_total_fail_credits/courses, prior_registered_semesters | Backend supplies ready finalized prior-state values, or a separately approved Python history adapter derives from finalized status records; existing course bundles cannot reconstruct these |\n| A/B | gpa_prev_1/2, observed_gap_semesters, diploma_gpa/type | Backend ready snapshot currently supplies; Python local adapter can derive GPA/gap only with correctly ordered finalized status history |\n| A: beginning request | degree_credits_count, course IDs/credits, plan course/requirement type, year/semester, plan_credits_count, attempt_number, previous_course_status | Backend supplies eligible catalog/candidate records; attempts/status have their own history contracts |\n| A: beginning request | exact credit target, requirement counts, repeat allowances and other supported policy inputs | Backend/request supplies; Python validates against existing constraints |\n| B: finalized history | Course and specialty difficulty states, category levels, model/scaler/version provenance, explicit as_of_part | Existing immutable V2 artifacts available to Python; select strictly before target |\n| C: semester update | finalized marks/status/points, student semester GPA, end cumulative GPA/counters and official GPA credits | Backend/university persists finalized student records for the next snapshot and offline training; not beginning request features |\n| C: existing history Delta | finalized flag, delta_part, aggregates with IDs/credits/count/fail/retake/mark/attempt sums | Backend supplies finalized aggregates; Python validates/idempotently publishes difficulty history; no student progress snapshot update here |\n| D: internally derived | prior_* aliases, prior_fail_credit_ratio, GPA trend/missing, part_semester | Offline Python derives from verified source; ready API currently accepts ratio/GPA history and derives trend/part, not the whole history |\n| D: internally derived | course/specialty history features, plan/peer context, expected quality points, Plan GPA, additive projected GPA | Python derives from artifacts/candidate combination; do not request per-plan context directly from PHP |',
        '\n`current_gpa_credits` precedence locally is explicit override → snapshot value → prior registration credits (`engine.py:21–34`). Backend ready adapter requires explicit `current_gpa_credits` (`inputs.py:251–279`), and both two-stage projections use it. Keep this separate from feature removal. Start credits participate in cleaning/outlier checks and isolated graduation-hour diagnostics (`scripts/scan_under_12_after_status_change.py:100–101`, `scripts/scan_student_over_polict.py:84–85`). Actual recommendation requirement-credit caps use explicit `requirement_policies` in `src/recommendation/constraints.py`, not those diagnostics. Model-only removal changes none of these paths.',
        '\n## 9. Final Recommendation',
        '\n**KEEP_ALL** for now. This is a conservative retention decision, not proof that every column is individually indispensable. The proposed registered-credits-only variant C has mixed grade/Plan GPA effects across years and the 47/33 families. Direct-points Plan GPA MAE worsens by +0.000714 (+0.176%) in 2023 and +0.001328 (+0.309%) in 2024; student-cluster 95% intervals are [+0.000147,+0.001287] and [+0.000878,+0.001803]. These are small detectable changes, not established substantial practical harm. No accepted noninferiority tolerance was supplied, and no tested reduced configuration establishes harmlessness across all affected profiles/folds. The broader best-subset question remains inconclusive; individual leave-one-out signals can motivate a separately specified follow-up.',
        '\nKeep the present inputs while agreeing a Plan GPA tolerance/subgroup risk policy and resolving university source semantics. Comparisons are conditional on retained ratios/GPA/history and fixed configurations. Historical-plan results and candidate sensitivity do not validate recommendation quality. API-field removal and GPA-denominator replacement remain independently unapproved regardless of model metrics.',
        '\nThree independent decisions: (1) a model matrix/contract change requires retraining and artifact validation; (2) API/source field removal needs independent dependency and data-availability review; (3) GPA denominator/policy change needs official university confirmation and separate academic-calculation validation. No approval for any of them is inferred from this report.',
        '\n## 10. Required Follow-up Actions',
        '\nObtain view SQL, historical snapshot/finalization guarantees, official GPA inclusion/repeat rules and explanations for transition exceptions. Agree a meaningful product tolerance and subgroup risk policy before final selection; extend temporal years/repeated seeds or a prospective term if needed. Freeze any selected feature subset and protocol before a separately authorized final evaluation; existing 2025 prior exposure must be disclosed.',
        '\nIf a subset is approved later, change/revalidate `src/features/feature_contract.py` ordered model lists; `src/experiments/course_only_core.py` and `src/recommendation/two_stage_artifacts.py` stage contracts; modeling and relevant research matrix builders; `src/recommendation/artifacts.py`, `engine.py`, `two_stage_engine.py` loaders/scoring and any payload validator intentionally relaxed; contract/temporal/recommendation tests and documentation. Source cleaning/status and GPA columns stay unless separately approved.',
        '\nRetrain/promote under new provenance: `models/grade_regressor_v2.txt`, `fail_risk_classifier_v2.txt`, `model_metadata_v2.json`, `data/artifacts/category_levels_v2.json`; course-only reference metadata/categories/models; `models/shortlist_v2/{grade_model.txt,fail_model.txt,category_levels.json,manifest.json}`; selected degree-points research artifacts only if its profile is adopted. Re-run stage compatibility, ranking/benchmark approval and policy checks. Feature-order changes invalidate current strict loaders/manifests; replacing model text alone is insufficient. Rebuild feature tables/history only if definitions change, under new approved versions; not needed for matrix-only removal.',
        '\n### Verification and changes',
        f'\nProtected inventory: {protection["protected_files"]} files; changed={protection["changed"]}, added={protection["added"]}, removed={protection["removed"]}. Existing production Python/data/V1/V2/model manifests/selected models/history are **NOT CHANGED**. Experimental scripts/tests/audit notes, isolated numerical/model outputs and this report were added. Graphify AST outputs are generated navigation updates. No commit, API implementation or feature promotion.',
        '\nValidation: related production suites **110 passed** ([related_suite.log](../scripts/experiments/student_progress_20261010/related_suite.log)); combined existing/experimental suite **1,185 passed, 1 failed, 6 subtests passed** ([final_full_suite.log](../scripts/experiments/student_progress_20261010/final_full_suite.log)). Its only failure is the pre-existing `test_tune_model_evaluates_every_candidate_fold_and_selects_mean_metric[grade-capacity_63-mae]`: source spells `capaciy_63`, test expects `capacity_63`. It was also present in the initial full run (1,169 passed, 1 failed, 6 subtests). This is a BASELINE FAILURE, not an ablation regression; the suite is not green and the mismatch was not repaired.',
        '\nAfter the final cache-context guard change, all **22 experimental tests passed** ([final_focused.log](../scripts/experiments/student_progress_20261010/final_focused.log)); the earlier combined suite contained 16 experimental tests. Six new tests failed before implementation and passed afterward, covering acceptance plus signed cross-run/year/specification/fit-row/validation-row transplant rejection ([context_red.log](../scripts/experiments/student_progress_20261010/context_red.log)). Checks also cover feature-order isolation, holdout partitioning, zero-credit GPA, hash/config changes, safe output namespaces, truthful completion and fixed-plan context. No later production code change occurred. Windows TEMP/TMP and pytest basetemp were rooted under isolated report validation directories.',
        '\nArtifact verification: **PASS, 108 models** ([artifact_integrity.json](../data/evaluation/experiments/student_progress_20261010/artifact_integrity.json)); archived executed source and categories/config/rows checked ([artifact_verification.log](../scripts/experiments/student_progress_20261010/artifact_verification.log)). Old-cache rejection was executed before any fit ([old_cache_rejection.log](../scripts/experiments/student_progress_20261010/old_cache_rejection.log)). Three independent audit/review tasks completed; the final review found no remaining material issue. Graphify AST update is recorded in [graphify_update.log](../scripts/experiments/student_progress_20261010/graphify_update.log). Training log: [training.log](../scripts/experiments/student_progress_20261010/training.log); final byte protection: [isolation_verification.json](../data/evaluation/experiments/student_progress_20261010/isolation_verification.json).',
    ])
    report=paths.PROJECT_ROOT/'reports/student_progress_feature_ablation.md'
    report.write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
    print('Report:',report)


if __name__=='__main__':
    build()
