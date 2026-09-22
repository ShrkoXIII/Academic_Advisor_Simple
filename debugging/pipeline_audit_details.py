"""Additional read-only checks; pass an existing pipeline audit directory."""
from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(1,str(ROOT/'src'))
import pandas as pd
import numpy as np
from src import paths
from src.data.cleaning_utils import clean_id_columns
from src.data.clean_outliers import build_outlier_audit
from src.recommendation import AcademicPlanRecommender
from src.recommendation_inputs import load_local_inputs
from src.experiments.modeling import prepare_matrix
from src.features.feature_contract import NUMERIC_FEATURES

OUT=Path(sys.argv[1]).resolve()
assert OUT.is_relative_to((paths.EVALUATION_DIR/'pipeline_audits').resolve())
def records(f):return json.loads(f.to_json(orient='records',force_ascii=False,double_precision=15))
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

raw=pd.read_parquet(paths.STUDENT_COURSE_PATH)
raw=clean_id_columns(raw,['student_id','degree_id','course_id','student_course_id'])
for c in ['register_status','finish_status','in_gpa','in_agpa','in_credits']:
    raw[c]=raw[c].astype('string').str.strip().str.upper()
raw['part_id']=pd.to_numeric(raw.part_id)
outcomes=raw.loc[raw.register_status.isin(['R','E'])&raw.finish_status.isin(['P','F','FE','FA'])&raw.part_id.gt(20193)].copy()
outcomes['gpa_flag_excluded']=outcomes[['in_gpa','in_agpa','in_credits']].eq('N').any(axis=1)
flags=outcomes.groupby(['finish_status','gpa_flag_excluded'],as_index=False).agg(rows=('course_id','size'),students=('student_id','nunique'))
save('raw_outcome_flag_counts.json',records(flags))
clean=pd.read_parquet(paths.CLEAN_STUDENT_COURSE_PATH)
train=pd.read_parquet(paths.TEMPORAL_TRAIN_FEATURES_PATH)
test=pd.read_parquet(paths.TEMPORAL_TEST_FEATURES_PATH)
merged=pd.read_parquet(paths.STUDENT_COURSE_DIPLOMA_PATH)
future_outliers=[]
for cutoff in [20223,20233,20243]:
    all_ids=set(build_outlier_audit(merged).student_id)
    old_ids=set(build_outlier_audit(merged.loc[merged.part_id.le(cutoff)]).student_id)
    excluded=all_ids-old_ids
    future_outliers.append({'cutoff':cutoff,'future_only_removed_students':len(excluded),
        'prior_rows_removed':int((merged.part_id.le(cutoff)&merged.student_id.isin(excluded)).sum())})
save('outlier_fold_selection.json',future_outliers)

pf=pd.read_parquet(OUT/'observed_plan_diagnostics.parquet')
naive_matched=[]
for c in ['start_agpa_points','gpa_prev_1','gpa_prev_2']:
    g=pf.loc[pf[c].notna()]
    naive_matched.append({'predictor':c,'plans':len(g),
        'naive_mae':float((g[c]-g.actual_plan_gpa).abs().mean()),
        'model_mae_same_plans':float((g.predicted_plan_gpa-g.actual_plan_gpa).abs().mean())})
save('naive_same_plan_comparison.json',naive_matched)
engine=AcademicPlanRecommender.load(num_threads=4)
roster=pd.read_parquet(paths.TEMPORAL_TEST_ROSTER_PATH)
result=[]
for number,sid,did in [(14,'10021.111','13.111'),(13,'10011.111','13.111'),(15,'10079.111','1.111'),(16,'10095.111','1.111')]:
    folder=OUT/sid
    ca,snap,_=load_local_inputs(ROOT/'json'/f'exportdata ({number}).json',sid,did,20251)
    prior_all=raw.loc[raw.student_id.eq(sid)&raw.part_id.lt(20251)&raw.register_status.isin(['R','E'])]
    prior_complete=prior_all.loc[prior_all.finish_status.isin(['P','F','FE','FA'])]
    selected=test.loc[test.student_id.eq(sid)&test.degree_id.eq(did)&test.part_id.eq(20251)]
    target_roster=roster.loc[roster.student_id.eq(sid)&roster.degree_id.eq(did)&roster.part_id.eq(20251)].copy()
    entry={'student_id':sid,'roster_courses':len(target_roster),'roster_credits':float(target_roster.course_credits.sum()),
           'scored_observed_courses':len(selected),'scored_observed_credits':float(selected.course_credits.sum()),
           'prior_registered_records':len(prior_all),'prior_completed_records':len(prior_complete)}
    # Reconstruct the complete observed plan using the same candidate adapter and historical snapshot.
    observed_source=folder/'observed_roster_candidates.json'
    target_roster[['course_id','course_credits']].to_json(observed_source,orient='records',indent=2)
    try:
        rc,rs,_=load_local_inputs(observed_source,sid,did,20251)
        rr=engine.prepare_candidates(rs,rc,20251).assign(plan_id=0)
        scored=engine.score_rows(rr)
        expected=engine.specialty_history.apply(selected)
        contract=engine.metadata['feature_contract']
        expected['saved_feature_prediction']=np.clip(engine.points_model.predict(prepare_matrix(expected,contract['numeric_features'],contract['categorical_features'],engine.points_levels),num_threads=4),0,4)
        joined=scored.merge(expected,on='course_id',suffixes=('_local','_test'),validate='one_to_one')
        differences=[]
        for c in contract['numeric_features']:
            a=joined[c+'_local'].astype(float);b=joined[c+'_test'].astype(float)
            neq=~np.isclose(a,b,rtol=0,atol=1e-8,equal_nan=True)
            if neq.any():differences.append({'feature':c,'different_rows':int(neq.sum()),'local':a.loc[neq].tolist(),'test':b.loc[neq].tolist()})
        entry['observed_feature_differences']=differences
        entry['observed_prediction_max_difference']=float((joined.expected_points-joined.saved_feature_prediction).abs().max())
        entry['observed_expected_gpa']=float((joined.course_credits_test*joined.expected_points).sum()/joined.course_credits_test.sum())
        entry['observed_actual_gpa']=float((selected.course_credits*selected.points).sum()/selected.course_credits.sum())
    except (ValueError,KeyError) as e:entry['observed_reconstruction_error']=str(e)
    attempts=[]
    for _,r in ca.iterrows():
        past=prior_complete.loc[prior_complete.course_id.eq(r.course_id)]
        attempts.append({'course_id':r.course_id,'model_attempt':int(r.attempt_number),
             'all_raw_completed_prior_attempts':len(past),'pre2020_attempts':int(past.part_id.lt(20201).sum()),
             'excluded_by_flags':int(past[['in_gpa','in_agpa','in_credits']].eq('N').any(axis=1).sum()),
             'last_mark':float(past.sort_values('part_id').final_mark.iloc[-1]) if len(past) else None})
    entry['candidate_attempt_audit']=attempts
    contribution=pd.read_parquet(folder/'best_plan_model_contributions.parquet')
    best=pd.read_parquet(folder/'best_plan_features_and_predictions.parquet')
    weighted=contribution.drop(columns='course_id').mul(best.course_credits.to_numpy(),axis=0).sum()/best.course_credits.sum()
    entry['best_plan_contributions']=weighted.sort_values().to_dict()
    result.append(entry)
save('pilot_details.json',result)

academic=pd.read_parquet(paths.ACADEMIC_INFO_PATH)
save('diploma_missingness.json',{'raw_rows':len(academic),'missing_gpa':int(academic.diploma_gpa.isna().sum()),
     'missing_type':int(academic.diploma_type_id.isna().sum()),
     'missing_gpa_with_known_type':int((academic.diploma_gpa.isna()&academic.diploma_type_id.notna()).sum())})
print(json.dumps({'outlier_folds':future_outliers,'naive_matched':naive_matched,
    'pilots':[{k:v for k,v in r.items() if k not in ['candidate_attempt_audit','best_plan_contributions']} for r in result]},ensure_ascii=False))
