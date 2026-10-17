"""Fixed-configuration isolated ablation. Run from repository root with -B."""
import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import lightgbm
import numpy as np
import pandas as pd

from src import paths
from src.features.feature_contract import prepare_model_matrix, learn_category_levels
from src.modeling.training_config import training_weights
from src.modeling.train_models import train_one, regression_metrics, classification_metrics
from src.recommendation.two_stage_artifacts import load_two_stage_artifacts
from .contract import FULL_FEATURES, SHORTLIST_FEATURES, REMOVED_FEATURES
from .evaluation import evaluate, paired_intervals

ROOT = paths.PROJECT_ROOT
KEYS = ['student_course_id','student_id','degree_id','part_id']

def fingerprint(frame):
    return hashlib.sha256(pd.util.hash_pandas_object(frame[KEYS],index=False).values.tobytes()).hexdigest()

def folds(rows):
    return [(f'train_through_{year}_validate_{year+1}',rows.part_id.le(year*10+3),
             rows.part_id.between((year+1)*10+1,(year+1)*10+3)) for year in (2022,2023)]

def family_configuration(stage, metadata):
    names = ['grade','fail'] if stage=='stage1' else ['grade_regressor','fail_risk_classifier']
    return {role:metadata[name] for role,name in zip(['grade','fail'],names)}

def _clean(value):
    if isinstance(value,dict): return {str(k):_clean(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [_clean(v) for v in value]
    if isinstance(value,np.generic): return _clean(value.item())
    if isinstance(value,float) and not np.isfinite(value): return None
    return value

def write_json(path,value):
    path.write_text(json.dumps(_clean(value),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def _history_counts(test):
    history=pd.read_parquet(paths.CLEAN_STUDENT_COURSE_PATH_V2,columns=['student_id','degree_id','part_id']).drop_duplicates()
    unique=test[['student_id','degree_id','part_id']].drop_duplicates()
    mapping=history.groupby(['student_id','degree_id'],observed=True).part_id.apply(lambda v:np.sort(v.unique())).to_dict()
    unique['prior_observed_completed_semesters']=[int(np.searchsorted(mapping.get((r.student_id,r.degree_id),np.array([])),r.part_id)) for r in unique.itertuples()]
    return test.merge(unique,on=['student_id','degree_id','part_id'],how='left',validate='many_to_one',sort=False)

def _fit(train,valid,features,levels,configuration,rounds,threads):
    matrix=prepare_model_matrix(train,levels,model_features=features)
    weights=training_weights(train).to_numpy(dtype='float32')
    models={}; predictions={}; times={}
    for role,target in [('grade','final_mark'),('fail','is_fail')]:
        parameters={**configuration[role]['parameters'],'num_threads':threads}
        started=time.perf_counter()
        models[role]=train_one(matrix,train[target].to_numpy(dtype='float32' if role=='grade' else 'int64'),weights,parameters,num_boost_round=rounds[role])
        times[role]=time.perf_counter()-started
        predictions[role]=np.clip(models[role].predict(prepare_model_matrix(valid,levels,model_features=features),num_threads=threads),0,100 if role=='grade' else 1)
    return models,predictions,times

def _predict(pair,rows,features,threads):
    matrix=prepare_model_matrix(rows,pair.category_levels,model_features=features)
    values={}
    elapsed={}
    for role,model in [('grade',pair.grade_model),('fail',pair.fail_model)]:
        model.predict(matrix.iloc[:min(len(matrix),100)],num_threads=threads)
        measurements=[]
        for _ in range(3):
            started=time.perf_counter(); result=model.predict(matrix,num_threads=threads)
            measurements.append(time.perf_counter()-started)
        values[role]=np.clip(result,0,100 if role=='grade' else 1)
        elapsed[role]=float(np.median(measurements))
    return values,elapsed

def decision(intervals):
    limits=[('overall','plan_gpa_mae',.01),('positive_prior_gpa_le_2','plan_gpa_mae',.02),
            ('overall','fail_log_loss',.002),('overall','fail_brier',.001)]
    checks=[]
    for cohort,metric,margin in limits:
        found=intervals[(intervals.cohort==cohort)&(intervals.metric==metric)]
        if len(found)!=1: return 'INCONCLUSIVE',checks
        row=found.iloc[0]; checks.append({'cohort':cohort,'metric':metric,'margin':margin,'delta':row.delta,'ci_low':row.ci_low,'ci_high':row.ci_high})
    if any(c['ci_low']>c['margin'] for c in checks): return 'WORSE',checks
    if all(c['ci_high']<=c['margin'] for c in checks):
        return ('BETTER' if checks[0]['ci_high']<-.01 else 'COMPARABLE'),checks
    return 'INCONCLUSIVE',checks

def run(threads=4,draws=2000):
    from .safeguards import snapshot, create_output_dirs, assert_unchanged
    from .compatibility import replay
    before=snapshot(ROOT)
    evidence,modeldir=create_output_dirs(ROOT)
    write_json(evidence/'protected_before.json',before)
    metadata={'experiment':'attempt_sum_removal','dataset_version':'V2','created_utc':datetime.now(timezone.utc).isoformat(),
              'python':platform.python_version(),'lightgbm':lightgbm.__version__,'pandas':pd.__version__,'numpy':np.__version__,
              'threads':threads,'bootstrap_draws':draws,'bootstrap_seed':42,'retuned':False,'families':{}}
    try:
        artifacts=load_two_stage_artifacts(target_part=20251)
        train=pd.read_parquet(paths.TEMPORAL_TRAIN_FEATURES_PATH_V2)
        test=pd.read_parquet(paths.TEMPORAL_TEST_FEATURES_PATH_V2)
        if train.part_id.max()!=20243 or set(test.part_id)!={20251,20252}: raise ValueError('Unexpected temporal split')
        if not np.array_equal(train.is_fail,train.final_mark.lt(50).astype(int)): raise ValueError('Fail target changed')
        test=_history_counts(test)
        metadata['rows']={'train':len(train),'test':len(test),'train_fingerprint':fingerprint(train),'test_fingerprint':fingerprint(test)}
        metadata['input_sha256']={str(p.relative_to(ROOT)):before[str(p.relative_to(ROOT)).replace('\\','/')] for p in [paths.TEMPORAL_TRAIN_FEATURES_PATH_V2,paths.TEMPORAL_TEST_FEATURES_PATH_V2]}
        print('Checking reduced historical replay...',flush=True)
        metadata['history_compatibility']=replay(train,test,evidence)
        allcomparisons=[]; validations=[]
        for stage,reduced in [('stage2',FULL_FEATURES),('stage1',SHORTLIST_FEATURES)]:
            print('Starting '+stage,flush=True)
            entry=artifacts.manifest['stages'][stage]; pair=getattr(artifacts,stage)
            original=entry['feature_contract']['model_features']
            config=family_configuration(stage,entry['provenance']['metadata'])
            rounds={role:config[role]['final_boost_rounds'] for role in config}
            fresh_levels=learn_category_levels(train)
            if fresh_levels!=pair.category_levels: raise ValueError('Pinned categories not reproduced')
            original_predictions,original_time=_predict(pair,test,original,threads)
            metrics_b,courses_b,plans_b,cohorts_b=evaluate(test,original_predictions['grade'],original_predictions['fail'],artifacts.grade_scale)
            saved_status={}
            for role,prefix in [('grade','grade_'),('fail','fail_')]:
                saved=config[role].get('test_2025_metrics',config[role].get('experimental_test_metrics'))
                if saved is None: saved_status[role]='UNVERIFIED: no saved metrics'
                else:
                    differences={k:abs(metrics_b[prefix+k]-v) for k,v in saved.items()}
                    if max(differences.values(),default=0)>1e-10: raise ValueError(f'{stage} saved baseline metrics mismatch {differences}')
                    saved_status[role]={'verified':True,'max_metric_difference':max(differences.values(),default=0)}
            replicas,replica_predictions,baseline_fit_time=_fit(train,test,original,pair.category_levels,config,rounds,threads)
            reproduction={role:float(np.max(np.abs(replica_predictions[role]-original_predictions[role]))) for role in config}
            if max(reproduction.values())>1e-9: raise ValueError(f'Baseline reproduction failed {stage} {reproduction}')
            models,predictions,candidate_fit_time=_fit(train,test,reduced,pair.category_levels,config,rounds,threads)
            for role,model in models.items(): model.save_model(str(modeldir/f'{stage}_{role}.txt'))
            for role,model in replicas.items(): model.save_model(str(modeldir/f'{stage}_baseline_replica_{role}.txt'))
            from types import SimpleNamespace
            predictions,candidate_time=_predict(SimpleNamespace(grade_model=models['grade'],fail_model=models['fail'],category_levels=pair.category_levels),test,reduced,threads)
            metrics_c,courses_c,plans_c,cohorts_c=evaluate(test,predictions['grade'],predictions['fail'],artifacts.grade_scale)
            print(stage+' bootstrap...',flush=True)
            intervals=paired_intervals(test,courses_b,courses_c,plans_b,plans_c,draws=draws)
            intervals.to_csv(evidence/f'{stage}_intervals.csv',index=False)
            for arm,metrics,courses,plans,cohorts in [('baseline',metrics_b,courses_b,plans_b,cohorts_b),('reduced',metrics_c,courses_c,plans_c,cohorts_c)]:
                write_json(evidence/f'{stage}_{arm}_metrics.json',metrics)
                courses.to_parquet(evidence/f'{stage}_{arm}_courses.parquet',index=False)
                plans.to_parquet(evidence/f'{stage}_{arm}_plans.parquet',index=False)
                cohorts.to_csv(evidence/f'{stage}_{arm}_cohorts.csv',index=False)
            for metric in metrics_b:
                if metric.startswith('n_'): continue
                allcomparisons.append({'family':stage,'metric':metric,'baseline':metrics_b[metric],'reduced':metrics_c[metric],'delta':metrics_c[metric]-metrics_b[metric]})
            # Identical chronological folds, fixed baseline-selected iteration per role; no early stopping/retuning.
            for name,fitmask,validmask in folds(train):
                fit=train.loc[fitmask]; valid=train.loc[validmask]; levels=learn_category_levels(fit)
                fold_rounds={role:next(f['best_iteration'] for f in config[role]['selected_candidate']['folds'] if f['fold']==name) for role in config}
                for arm,features in [('baseline',original),('reduced',reduced)]:
                    print(f'{stage} {name} {arm}',flush=True)
                    _,pred,timing=_fit(fit,valid,features,levels,config,fold_rounds,threads)
                    validation={'family':stage,'fold':name,'arm':arm,'fit_rows':len(fit),'valid_rows':len(valid),'rounds':fold_rounds,'seconds':timing,
                        'grade':regression_metrics(valid.final_mark,pred['grade']),'fail':classification_metrics(valid.is_fail,pred['fail'])}
                    validations.append(validation); write_json(evidence/'validation.json',validations)
            verdict,checks=decision(intervals)
            metadata['families'][stage]={'original_features':original,'reduced_features':reduced,'removed_features':[f for f in original if f not in reduced],
                'configuration':config,'effective_parameters':{r:{**config[r]['parameters'],'num_threads':threads} for r in config},'rounds':rounds,
                'saved_baseline_verification':saved_status,'baseline_replica_max_prediction_difference':reproduction,
                'training_seconds':{'baseline':baseline_fit_time,'reduced':candidate_fit_time},'prediction_seconds_median_3':{'baseline':original_time,'reduced':candidate_time},
                'model_size_bytes':{'baseline':{r:(ROOT/entry['models'][r]['path']).stat().st_size for r in config},'baseline_replica':{r:len(replicas[r].model_to_string().encode()) for r in config},'reduced':{r:(modeldir/f'{stage}_{r}.txt').stat().st_size for r in config}},
                'verdict':verdict,'decision_checks':checks}
            write_json(evidence/'metadata.json',metadata)
        pd.DataFrame(allcomparisons).to_csv(evidence/'comparison.csv',index=False)
        write_json(evidence/'comparison.json',allcomparisons)
        write_json(modeldir/'category_levels.json',artifacts.stage2.category_levels)
        write_json(modeldir/'feature_contract.json',{'full':FULL_FEATURES,'shortlist':SHORTLIST_FEATURES,'removed':list(REMOVED_FEATURES),'dataset_version':'V2'})
        metadata['status']='COMPLETE'
    except Exception as exc:
        metadata['status']='FAILED'; metadata['error']=repr(exc); raise
    finally:
        write_json(evidence/'metadata.json',metadata)
        assert_unchanged(ROOT,before)
        write_json(evidence/'protection.json',{'unchanged':True,'protected_file_count':len(before)})
    from .finalize import finalize
    finalize(evidence,modeldir,metadata)
    print(json.dumps({s:m['verdict'] for s,m in metadata['families'].items()}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--threads',type=int,default=4);parser.add_argument('--draws',type=int,default=2000)
    args=parser.parse_args()
    if args.threads<1 or args.draws<1: parser.error('threads and draws must be positive')
    run(args.threads,args.draws)
