"""Read-only pipeline diagnostics. Writes only a new timestamped audit folder.

Run from the project root with .venv/Scripts/python.exe -B debugging/pipeline_audit.py.
Does not fit models, change production code, or overwrite existing artifacts.
"""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
from itertools import islice
from collections import Counter
from decimal import Decimal
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / 'src'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from src import paths
from src.data.cleaning_utils import clean_id_columns
from src.data.clean_student_status import clean_student_status
from src.data.clean_outliers import build_outlier_audit
from src.features.feature_contract import BASE_FEATURES, NUMERIC_FEATURES, prepare_model_matrix
from src.recommendation import AcademicPlanRecommender, enumerate_plan_indices, build_plan_rows, rank_plans
from src.recommendation.inputs import load_local_inputs
from src.experiments.modeling import prepare_matrix, aggregate_plans, course_predictions
from src.features.temporal_features import COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS, CourseHistoryState

OUT = paths.EVALUATION_DIR / 'pipeline_audits' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
OUT.mkdir(parents=True, exist_ok=False)

def records(df):
    return json.loads(df.to_json(orient='records', force_ascii=False, double_precision=15))

def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def progress(msg):
    print(msg, flush=True)

def metrics(df, actual='actual_plan_gpa', predicted='predicted_plan_gpa'):
    d=df[[actual,predicted]].dropna().astype(float)
    err=d[predicted]-d[actual]
    return {'n':len(d),'mae':float(err.abs().mean()), 'rmse':float(np.sqrt((err**2).mean())),
            'bias':float(err.mean()),'actual_mean':float(d[actual].mean()),
            'predicted_mean':float(d[predicted].mean()),'within_0_25':float(err.abs().le(.25).mean()),
            'within_0_5':float(err.abs().le(.5).mean())}

progress(f'OUTPUT: {OUT}')
protected = [*sorted((ROOT/'src').rglob('*.py')), *sorted((ROOT/'models').rglob('*')),
             paths.COURSE_HISTORY_STATE_PATH, paths.TEMPORAL_TRAIN_FEATURES_PATH, paths.TEMPORAL_TEST_FEATURES_PATH]
protected = [p for p in protected if p.is_file()]
before = {str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in protected}
save('protected_before.json',before)
inventory=[]
for folder in ['raw','clean','merged','temporal','features']:
    for p in sorted((paths.DATA_DIR/folder).glob('*.parquet')):
        pf=pq.ParquetFile(p)
        inventory.append({'path':str(p.relative_to(ROOT)), 'rows':pf.metadata.num_rows,
                          'columns':len(pf.schema_arrow.names),'bytes':p.stat().st_size})
save('inventory.json',inventory)
progress('Inventory complete; auditing outlier selection before temporal split')
merged=pd.read_parquet(paths.STUDENT_COURSE_DIPLOMA_PATH)
all_audit=build_outlier_audit(merged)
past_audit=build_outlier_audit(merged.loc[merged.part_id.le(20243)])
all_ids=set(all_audit.student_id); past_ids=set(past_audit.student_id)
future_only=all_ids-past_ids
future_rows=merged.loc[merged.student_id.isin(future_only)]
future_rows[['student_id','student_status_id','part_id']].drop_duplicates().to_parquet(OUT/'future_only_outlier_cases.parquet',index=False)
outlier_summary={'all_removed_students':len(all_ids),'removed_using_through_2024':len(past_ids),
                 'removed_only_due_to_later_records':len(future_only),
                 'pre_2025_rows_removed_due_to_later_records':int((future_rows.part_id<=20243).sum()),
                 'total_removed_rows':int(merged.student_id.isin(all_ids).sum()),
                 'before_rows':len(merged),
                 'by_rule':records(all_audit.groupby('rule',as_index=False).agg(students=('student_id','nunique')))}
cohort=[]
for part,g in merged.groupby('part_id'):
    for name,gg in [('before_outliers',g),('after_outliers',g.loc[~g.student_id.isin(all_ids)])]:
        cohort.append({'part_id':int(part),'cohort':name,'rows':len(gg),'students':gg.student_id.nunique(),
                       'mark_fail_rate':float(gg.final_mark.lt(50).mean()),'mean_points':float(gg.points.mean())})
save('outliers.json',outlier_summary); save('cohorts_by_part.json',cohort)
progress(str({k:v for k,v in outlier_summary.items() if k!='by_rule'}))

train=pd.read_parquet(paths.TEMPORAL_TRAIN_FEATURES_PATH)
test=pd.read_parquet(paths.TEMPORAL_TEST_FEATURES_PATH)
feature_stats=[]
for split,df in [('train',train),('test',test)]:
    for c in NUMERIC_FEATURES:
        s=pd.to_numeric(df[c],errors='coerce').astype(float)
        feature_stats.append({'split':split,'feature':c,'missing':int(s.isna().sum()),
                              'min':float(s.min()),'p01':float(s.quantile(.01)),
                              'median':float(s.median()),'p99':float(s.quantile(.99)),'max':float(s.max())})
save('feature_distributions.json',feature_stats)
save('feature_integrity.json',{'train_rows':len(train),'test_rows':len(test),
     'train_parts':sorted(train.part_id.astype(int).unique().tolist()),
     'test_parts':sorted(test.part_id.astype(int).unique().tolist()),
     'overlapping_student_course_ids':len(set(train.student_course_id)&set(test.student_course_id)),
     'duplicate_train_ids':int(train.student_course_id.duplicated().sum()),
     'duplicate_test_ids':int(test.student_course_id.duplicated().sum()),
     'same_student_multiple_degrees_same_term':int(pd.concat([train,test]).drop_duplicates(['student_id','degree_id','part_id']).duplicated(['student_id','part_id'],keep=False).sum()),
     'train_outcome_disagreement':int(train.is_fail.ne(train.course_outcome_status.eq('fail')).sum()),
     'test_outcome_disagreement':int(test.is_fail.ne(test.course_outcome_status.eq('fail')).sum()),
     'negative_prior_values':{c:int(train[c].lt(0).sum()+test[c].lt(0).sum()) for c in NUMERIC_FEATURES if c.startswith('prior_')},
     'train_feature_version':train.attrs,'test_feature_version':test.attrs})

progress('Loading current models; reproducing saved 2025 predictions without fitting')
engine=AcademicPlanRecommender.load(num_threads=4)
enriched_test=engine.specialty_history.apply(test)
contract=engine.metadata['feature_contract']
matrix=prepare_matrix(enriched_test,contract['numeric_features'],contract['categorical_features'],engine.points_levels)
pred=np.clip(engine.points_model.predict(matrix,num_threads=4),0,4)
predictions=course_predictions(test,pred,'points',None)
plans=aggregate_plans(predictions)
saved=pd.read_parquet(paths.DEGREE_POINTS_HOLDOUT_COURSES_PATH)
check=predictions[['student_course_id','predicted_points']].merge(saved[['student_course_id','predicted_points']],on='student_course_id',validate='one_to_one',suffixes=('_now','_saved'))
status=clean_student_status(pd.read_parquet(paths.STUDENT_STATUS_PATH))
key=['student_id','degree_id','part_id']
plans=plans.merge(test[key+['start_agpa_points','gpa_prev_1','gpa_prev_2','gpa_trend_delta','gpa_points','plan_total_credits','plan_course_count']].drop_duplicates(key),on=key,validate='one_to_one')
plans['actual_improves']=plans.actual_plan_gpa.gt(plans.start_agpa_points)
plans['predicted_improves']=plans.predicted_plan_gpa.gt(plans.start_agpa_points)
plans.to_parquet(OUT/'observed_plan_diagnostics.parquet',index=False)
baseline=pd.read_parquet(paths.PLAN_GPA_EVALUATION_PATH)
comparison=plans[key+['actual_plan_gpa','predicted_plan_gpa']].merge(baseline[key+['actual_plan_gpa','predicted_plan_gpa']],on=key,validate='one_to_one',suffixes=('_selected','_baseline'))
by_degree=[]
for did,g in plans.groupby('degree_id'):
    by_degree.append({'degree_id':str(did),'degree_name':str(g.degree_name.iloc[0]),**metrics(g)})
by_gpa=[]
for label,g in plans.groupby(pd.cut(plans.start_agpa_points,[-.001,1,2,2.5,3,3.5,4],include_lowest=True),observed=True):
    by_gpa.append({'start_gpa_bin':str(label),**metrics(g),'actual_improves_rate':float(g.actual_improves.mean()),'predicted_improves_rate':float(g.predicted_improves.mean())})
naive=[]
for col in ['start_agpa_points','gpa_prev_1','gpa_prev_2']:
    naive.append({'predictor':col,**metrics(plans,predicted=col)})
holdout={'selected':metrics(plans),'baseline_same_keys':metrics(comparison,actual='actual_plan_gpa_baseline',predicted='predicted_plan_gpa_baseline'),
         'saved_predictions_max_abs_difference':float((check.predicted_points_now-check.predicted_points_saved).abs().max()),
         'shared_keys':len(comparison),'actual_gpa_same_keys_max_difference':float((comparison.actual_plan_gpa_selected-comparison.actual_plan_gpa_baseline).abs().max()),
         'naive_comparators':naive,'by_degree':by_degree,'by_start_gpa':by_gpa,
         'actual_improves_rate':float(plans.actual_improves.mean()),'predicted_improves_rate':float(plans.predicted_improves.mean()),
         'false_no_improvement':int((plans.actual_improves & ~plans.predicted_improves).sum()),
         'actual_improved_plans':int(plans.actual_improves.sum()),
         'false_improvement':int((~plans.actual_improves & plans.predicted_improves).sum()),
         'predicted_improved_plans':int(plans.predicted_improves.sum()),
         'formula_vs_source_gpa':metrics(plans,actual='gpa_points',predicted='actual_plan_gpa'),
         'roster_vs_scored_credit_mismatch_plans':int((plans.total_credits-plans.plan_total_credits).abs().gt(1e-6).sum())}
save('holdout_recomputed.json',holdout)
prob=np.clip(engine.fail_model.predict(prepare_model_matrix(test,engine.fail_levels),num_threads=4),0,1)
from src.modeling.train_models import classification_metrics,calibration_table
save('failure_risk.json',{'metrics':classification_metrics(test.is_fail,prob),
    'actual_rate':float(test.is_fail.mean()),'predicted_rate':float(prob.mean()),
    'recall_at_0_5':float((prob[test.is_fail.eq(1)]>=.5).mean()),
    'calibration':calibration_table(test.is_fail,prob)})
progress(str(holdout['selected']))

progress('Comparing rolling validation history with a history frozen at each fold start')
fold_history=[]
for cutoff,begin,end in [(20223,20231,20233),(20233,20241,20243)]:
    state=CourseHistoryState(); state.update(train.loc[train.part_id.le(cutoff)])
    valid=train.loc[train.part_id.between(begin,end)]
    frozen=state.apply(valid)
    for part,g in valid.groupby('part_id'):
        delta=(g[COURSE_HISTORY_COLUMNS].astype(float)-frozen.loc[g.index].astype(float)).abs()
        fold_history.append({'cutoff':cutoff,'part_id':int(part),'rows':len(g),
                             'rows_with_changed_history':int(delta.gt(1e-9).any(axis=1).sum()),
                             'mean_abs_avg_mark_change':float(delta.course_history_avg_mark.mean())})
save('validation_history_protocol.json',fold_history)

progress('Scoring complete supplied candidate lists for the four requested students at 20251')
pilot=[]
for number,sid,did in [(14,'10021.111','13.111'),(13,'10011.111','13.111'),(15,'10079.111','1.111'),(16,'10095.111','1.111')]:
    folder=OUT/sid;folder.mkdir()
    source=ROOT/'json'/f'exportdata ({number}).json'
    candidates,snapshot,report=load_local_inputs(source,sid,did,20251)
    prepared=engine.prepare_candidates(snapshot,candidates,20251)
    prepared.to_parquet(folder/'prepared_candidates.parquet',index=False)
    save(f'{sid}/snapshot.json',json.loads(pd.Series(snapshot).to_json(double_precision=15)))
    save(f'{sid}/import_report.json',report)
    distribution=Counter({Decimal(0):1})
    for credits in candidates.course_credits:
        for total,n in list(distribution.items()):distribution[total+Decimal(str(credits))]+=n
    dp_count=sum(n for total,n in distribution.items() if 12<=total<=18)
    chunks=[];best=None;best_rows=None;best_prepared_rows=None;count=0
    iterator=enumerate_plan_indices(prepared,min_credits=12,max_credits=18)
    while batch:=list(islice(iterator,2000)):
        scored=engine.score_rows(build_plan_rows(prepared,batch,count))
        sm=scored.assign(q=scored.course_credits*scored.expected_points,f=scored.course_credits*scored.fail_probability).groupby('plan_id',as_index=False).agg(
            course_count=('course_id','size'),total_credits=('course_credits','sum'),quality_points=('q','sum'),expected_failed_credits=('f','sum'))
        sm['expected_plan_gpa']=sm.quality_points/sm.total_credits
        sm['gpa_gain']=sm.expected_plan_gpa-float(snapshot['start_agpa_points'])
        chunks.append(sm)
        winner=rank_plans(sm).iloc[0]
        if best is None or winner.expected_plan_gpa>best.expected_plan_gpa:
            best=winner
            best_rows=scored.loc[scored.plan_id.eq(winner.plan_id)].copy()
        count+=len(batch)
        if count%50000==0:progress(f'{sid}: {count}/{dp_count} plans')
    all_plans=rank_plans(pd.concat(chunks,ignore_index=True)) if chunks else pd.DataFrame()
    assert count==dp_count,(count,dp_count)
    all_plans.to_parquet(folder/'all_plans_before_filter.parquet',index=False)
    if best_rows is not None:best_rows.to_parquet(folder/'best_plan_features_and_predictions.parquet',index=False)
    history=pd.read_parquet(paths.CLEAN_STUDENT_COURSE_PATH)
    past=history.loc[history.student_id.eq(sid)&history.part_id.lt(20251)]
    observed=history.loc[history.student_id.eq(sid)&history.degree_id.eq(did)&history.part_id.eq(20251)]
    observed.to_parquet(folder/'observed_courses_20251.parquet',index=False)
    previous_status=status.loc[status.student_id.eq(sid)&status.degree_id.eq(did)&status.part_id.le(20251)]
    previous_status.to_parquet(folder/'status_history.parquet',index=False)
    candidate_ids=set(candidates.course_id);observed_ids=set(observed.course_id)
    row={'file':source.name,'source_sha256':sha256(source.read_bytes()).hexdigest(),'student_id':sid,'degree_id':did,'part_id':20251,
         'current_gpa':float(snapshot['start_agpa_points']),'candidate_count':len(candidates),'matching_plan_count':count,
         'above_current_gpa_count':int(all_plans.gpa_gain.gt(0).sum()) if count else 0,
         'best_expected_gpa':float(best.expected_plan_gpa) if best is not None else None,
         'gpa_distribution':{str(q):float(all_plans.expected_plan_gpa.quantile(q)) for q in [0,.1,.5,.9,1]} if count else {},
         'observed_course_count':len(observed_ids),'observed_courses_in_candidates':len(observed_ids&candidate_ids),
         'candidates_previously_passed':sorted(candidate_ids&set(past.loc[past.course_outcome_status.eq('pass'),'course_id'])),
         'observed_plan_actual_gpa':float((observed.course_credits*observed.points).sum()/observed.course_credits.sum()) if len(observed) else None,
         'in_outlier_exclusion':sid in all_ids,'train_rows':int(train.student_id.eq(sid).sum()),'test_rows':int(test.student_id.eq(sid).sum()),
         'direct_course_history_count':int(prepared.course_history_fallback_level.le(2).sum()),
         'history_missing_count':int(prepared.course_history_missing.sum()),'attempt_numbers':sorted(candidates.attempt_number.unique().tolist())}
    if best_rows is not None:
        bmatrix=prepare_matrix(best_rows,contract['numeric_features'],contract['categorical_features'],engine.points_levels)
        contributions=engine.points_model.predict(bmatrix,pred_contrib=True,num_threads=4)
        contrib=pd.DataFrame(contributions,columns=[*bmatrix.columns,'base_value'])
        contrib.insert(0,'course_id',best_rows.course_id.to_numpy())
        contrib.to_parquet(folder/'best_plan_model_contributions.parquet',index=False)
        domain=[]
        for c in NUMERIC_FEATURES:
            low,high=train[c].quantile([.01,.99]).astype(float)
            v=best_rows[c].astype(float)
            if (v.lt(low)|v.gt(high)).any():domain.append({'feature':c,'train_p01':low,'train_p99':high,'case_min':float(v.min()),'case_max':float(v.max())})
        row['outside_train_p01_p99']=domain
        best_rows[['course_id','course_name','course_credits','expected_points','fail_probability']].to_json(folder/'best_plan_courses.json',orient='records',force_ascii=False,indent=2)
    pilot.append(row);save('pilot_summary.json',pilot)
    progress(str({k:v for k,v in row.items() if k in ['student_id','candidate_count','matching_plan_count','above_current_gpa_count','best_expected_gpa','current_gpa','observed_courses_in_candidates','observed_course_count','in_outlier_exclusion']}))

after={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in protected}
save('protected_after.json',after)
assert before==after,'Protected inputs changed during audit'
save('completion.json',{'completed_at_utc':datetime.now(timezone.utc).isoformat(),'protected_files_unchanged':True,
     'protected_file_count':len(before),'notes':'2025 results are diagnostic, not a new untouched holdout. No tuning or training performed. Candidate eligibility at 20251 is not established by the supplied JSON.'})
progress('Audit completed; production inputs unchanged')
