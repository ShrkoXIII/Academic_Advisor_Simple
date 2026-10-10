"""Validation-only candidate ranking sensitivity and full-plan permutation."""
from collections import defaultdict
from itertools import combinations
import json

import lightgbm as lgb
import numpy as np
import pandas as pd

from src import paths
from src.features.temporal_features import compute_plan_context_features, PLAN_CONTEXT_COLUMNS
from src.features.frozen_history import file_sha256
from src.grade_scale import GradeScale
from .workflow import (OUTPUT, MODELS, VARIANTS, FIELDS, KEYS, load_train, specs,
                       matrix, predict, evaluate, configuration_signature, write_json,
                       verify_protected, feature_subset, validate_signature, row_fingerprint,
                       learn_category_levels)


def validated_model(year, name, variant, train, setup, provenance):
    """Validate every loaded model against the exact executed row/config signature."""
    spec = next(s for s in setup['specs'] if s['name'] == name)
    fit = train[train.part_id.le((year-1)*10+3)]
    valid = train[train.part_id.between(year*10+1,year*10+3)]
    folder = MODELS / str(year) / name
    model_path = folder / f'{variant}.txt'
    record = json.loads(model_path.with_suffix('.json').read_text())
    selected = json.loads((OUTPUT / str(year) / name / 'inner_selection.json').read_text())['selected']
    config = {'parameters': selected['parameters'], 'rounds': selected['rounds']}
    features = feature_subset(spec['features'], variant)
    expected = configuration_signature({'run': setup['signature'], 'year': year, 'spec': spec,
        'variant': variant, 'features': features, 'config': config,
        'fit_rows': row_fingerprint(fit), 'valid_rows': row_fingerprint(valid)})
    validate_signature(record['signature'], expected)
    if file_sha256(model_path) != record['sha256'] or record['features'] != features or record['configuration'] != config:
        raise ValueError('Model artifact/configuration differs from experiment evidence')
    levels = json.loads((folder / 'categories.json').read_text())
    if levels != learn_category_levels(fit):
        raise ValueError('Experimental categories differ from training-only levels')
    model = lgb.Booster(model_file=str(model_path))
    if model.feature_name() != features:
        raise ValueError('Experimental model feature order mismatch')
    provenance[f'{year}_{name}_{variant}'] = {'sha256':record['sha256'], 'signature':expected,
                                            'categories_sha256':file_sha256(folder / 'categories.json')}
    return model


def candidate_rows(pool):
    """Choose the credit target yielding most alternatives, from at most 8 finalized courses."""
    pool=pool.drop_duplicates('course_id').sort_values('course_id',kind='stable').iloc[:8].copy()
    if len(pool)<5 or not pool.course_credits.gt(0).all():
        return None
    buckets=defaultdict(list)
    for size in range(2,len(pool)):
        for indices in combinations(range(len(pool)),size):
            credit=float(pool.iloc[list(indices)].course_credits.sum())
            if 6<=credit<=18:
                buckets[credit].append(indices)
    buckets={credit:plans for credit,plans in buckets.items() if len(plans)>=4}
    if not buckets:
        return None
    target=max(buckets,key=lambda credit:(len(buckets[credit]),credit))
    rows=[]
    for plan_id,indices in enumerate(buckets[target]):
        part=pool.iloc[list(indices)].copy()
        part['plan_id']=plan_id
        rows.append(part)
    proposals=pd.concat(rows,ignore_index=True)
    context=compute_plan_context_features(proposals,group_columns=['plan_id'])
    proposals[PLAN_CONTEXT_COLUMNS]=context[PLAN_CONTEXT_COLUMNS].to_numpy()
    return proposals,target


def run():
    if json.loads((OUTPUT/'execution.json').read_text())['status']!='COMPLETE':
        raise ValueError('Finish the controlled experiment before downstream analysis')
    verify_protected()
    setup = json.loads((OUTPUT/'setup.json').read_text())
    for relative, digest in setup['sources'].items():
        if file_sha256(paths.PROJECT_ROOT / relative) != digest:
            raise ValueError('Source artifact changed since experiment execution')
    train=load_train(); scale=GradeScale.from_parquet(paths.GRADE_SCALE_PATH)
    ranking=[]; permutation=[]; pools=[]
    specmap={s['name']:s for s in specs()}
    used_models={}
    for year in [2023,2024]:
        valid=train[train.part_id.between(year*10+1,year*10+3)]
        # Complete student/degree/semester groups, not a partial course-row sample.
        eligible=valid.groupby(KEYS,sort=True).size().reset_index(name='size')
        chosen=eligible.sample(n=min(1000,len(eligible)),random_state=42)
        complete=valid.merge(chosen[KEYS],on=KEYS,how='inner',validate='many_to_one').reset_index(drop=True)
        for name,spec in specmap.items():
            folder=MODELS/str(year)/name
            levels=json.loads((folder/'categories.json').read_text())
            model=validated_model(year,name,'A',train,setup,used_models)
            x=matrix(complete,levels,spec['features'])
            base,_,_=evaluate(complete,predict(model,x,spec['target']),spec['target'],scale)
            primary='log_loss' if spec['target']=='is_fail' else 'plan_gpa_mae'
            # Shared within-status inputs are permuted as a block between status groups.
            status=complete[KEYS+FIELDS].drop_duplicates(KEYS).reset_index(drop=True)
            for fields in [[f] for f in FIELDS]+[FIELDS]:
                for repeat in range(3):
                    order=np.random.default_rng(42+repeat).permutation(len(status))
                    replacement=status[KEYS].copy()
                    for field in fields:
                        replacement[field]=status[field].to_numpy()[order]
                    shuffled_frame=complete.drop(columns=fields).merge(replacement,on=KEYS,validate='many_to_one',sort=False)
                    shuffled=matrix(shuffled_frame,levels,spec['features'])
                    metrics,_,_=evaluate(shuffled_frame,predict(model,shuffled,spec['target']),spec['target'],scale)
                    permutation.append({'year':year,'model':name,'fields':'+'.join(fields),'repeat':repeat,
                         'metric':primary,'baseline':base[primary],'delta':metrics[primary]-base[primary],
                         'rows':len(complete),'complete_plans':len(status),
                         'limitation':'Dependent ratio unchanged; diagnostic breaks feature correlations'})
        # Select pools by available course features only, before scoring any variant.
        ranking_models = {(family, task, variant): validated_model(year,f'{family}_{task}',variant,train,setup,used_models)
                          for family in ['47','33'] for task in ['grade','fail'] for variant in VARIANTS}
        count=0
        for key,pool in valid.groupby(KEYS,sort=True):
            item=candidate_rows(pool)
            if item is None:
                continue
            proposals,target=item
            count+=1
            case=f'{year}_case_{count:02d}'
            pools.append({'case':case,'year':year,'pool_courses':pool.course_id.nunique(),
                          'courses_used':proposals.course_id.nunique(),'plans':proposals.plan_id.nunique(),
                          'credit_target':target,'selection':'first 12 sorted eligible historical finalized-course pools'})
            for family in ['47','33']:
                levels=json.loads((MODELS/str(year)/f'{family}_grade'/'categories.json').read_text())
                grade_spec=specmap[f'{family}_grade']; fail_spec=specmap[f'{family}_fail']
                full=matrix(proposals,levels,grade_spec['features'])
                rankings={}; scores={}
                for variant in VARIANTS:
                    grade=ranking_models[(family,'grade',variant)]
                    fail=ranking_models[(family,'fail',variant)]
                    names=grade.feature_name(); x=full[names]
                    marks=predict(grade,x,grade_spec['target'])
                    probability=predict(fail,x,fail_spec['target'])
                    points=scale.convert(marks,proposals.grade_version_id)[0]
                    work=proposals[['plan_id','course_credits']].assign(
                        quality=proposals.course_credits*np.asarray(points),
                        failed=proposals.course_credits*probability)
                    summary=work.groupby('plan_id').agg(credits=('course_credits','sum'),quality=('quality','sum'),failed=('failed','sum'))
                    start=pool.start_agpa_points.iloc[0]; prior=pool.prior_total_reg_credits.iloc[0]
                    summary['gpa']=summary.quality/summary.credits
                    summary['cumulative']=(start*prior+summary.quality)/(prior+summary.credits)
                    summary=summary.reset_index().sort_values(['cumulative','failed','gpa','plan_id'],ascending=[False,True,False,True],kind='stable')
                    rankings[variant]=summary.plan_id.tolist(); scores[variant]=summary.set_index('plan_id')
                for variant in VARIANTS:
                    ranking.append({'case':case,'year':year,'family':family,'variant':variant,
                        'plans':len(rankings[variant]),'top1_changed':rankings[variant][0]!=rankings['A'][0],
                        'top3_set_changed':set(rankings[variant][:3])!=set(rankings['A'][:3]),
                        'top3_order_changed':rankings[variant][:3]!=rankings['A'][:3],
                        'max_plan_gpa_delta':float((scores[variant].gpa-scores['A'].gpa).abs().max())})
            if count==12:
                break
    pd.DataFrame(ranking).to_csv(OUTPUT/'ranking_sensitivity.csv',index=False)
    pd.DataFrame(pools).to_csv(OUTPUT/'ranking_pools.csv',index=False)
    pd.DataFrame(permutation).to_csv(OUTPUT/'complete_plan_permutation.csv',index=False)
    write_json(OUTPUT/'downstream_provenance.json',{'script_sha256':file_sha256(__file__),'loaded_models':used_models,
              'experiment_signature':json.loads((OUTPUT/'setup.json').read_text())['signature'],
              'candidate_pools':len(pools),'2025_evaluated':False,
              'quality_claim':False,'production_recommender_executed':False,
              'policy':'Isolated single-stage additive GPA ranking, then failed credits, plan GPA, plan ID',
              'limitations':['Historical finalized-course pools are not true requestable universes',
                            'No production two-stage shortlist, Balance policy or ranking quality evaluation',
                            'Registered-credit denominator is unverified; selected identical credit targets']})
    verify_protected()
    print('Downstream complete:',len(pools),'pools;',len(permutation),'permutation observations',flush=True)


if __name__=='__main__':
    run()
