"""Nested temporal progress-feature ablation; never load 2025 target rows."""
import argparse
import hashlib
import json
import platform
from time import perf_counter

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, log_loss, brier_score_loss

from src import paths
from src.experiments.attempt_number_core import paired_cluster_interval, row_fingerprint
from src.experiments.specialty_history import add_specialty_history_features, SPECIALTY_HISTORY_FEATURES
from src.features.feature_contract import BASE_FEATURES, learn_category_levels, prepare_model_matrix, require_current_features
from src.features.frozen_history import file_sha256
from src.features.temporal_features import compute_plan_context_features, PLAN_CONTEXT_COLUMNS
from src.grade_scale import GradeScale
from src.modeling import train_models as official
from src.modeling.training_config import training_weights

FIELDS = ['start_total_in_credits', 'start_total_in_courses', 'prior_total_reg_credits', 'prior_total_reg_courses']
VARIANTS = {
    'A': [], 'B': [FIELDS[1], FIELDS[3]], 'C': [FIELDS[0], FIELDS[1], FIELDS[3]],
    'D': [FIELDS[1], FIELDS[2], FIELDS[3]], 'E': FIELDS,
    **{f'F{i+1}': [field] for i, field in enumerate(FIELDS)},
}
NAME = 'student_progress_20261010'
OUTPUT = paths.EVALUATION_DIR / 'experiments' / NAME
MODELS = paths.MODEL_DIR / 'experiments' / NAME
HERE = paths.PROJECT_ROOT / 'scripts/experiments' / NAME
KEYS = ['student_id', 'degree_id', 'part_id']


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    def default(obj):
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, paths.Path):
            return obj.as_posix()
        raise TypeError(type(obj).__name__)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=default), encoding='utf-8')


def feature_subset(features, variant):
    if variant not in VARIANTS:
        raise ValueError(f'Unknown variant: {variant}')
    return [f for f in features if f not in VARIANTS[variant]]


def temporal_partition(frame, outer_year):
    """Inner validation is the last year entirely inside outer training."""
    inner_year = outer_year - 1
    return (frame.loc[frame.part_id.le((inner_year - 1)*10+3)],
            frame.loc[frame.part_id.between(inner_year*10+1, inner_year*10+3)])


def configuration_signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_signature(saved, expected):
    if saved != expected:
        raise ValueError('Experimental cache signature mismatch')


def protected_manifest():
    roots = ['data', 'models', 'src', 'scripts', 'tests', 'json', 'docs', 'plan_explanation']
    result = {}
    for root in roots:
        for path in (paths.PROJECT_ROOT / root).rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts or '.pytest_cache' in path.parts:
                continue
            if any(path.is_relative_to(p) for p in [OUTPUT, MODELS, HERE]):
                continue
            result[path.relative_to(paths.PROJECT_ROOT).as_posix()] = file_sha256(path)
    return result


def verify_protected():
    before = json.loads((OUTPUT / 'protected_before.json').read_text())
    after = protected_manifest()
    changed = [k for k in before if before[k] != after.get(k)]
    added = sorted(set(after) - set(before))
    result = {'protected_files': len(before), 'changed': changed, 'added': added,
              'removed': sorted(set(before)-set(after)), 'production_modified': bool(changed or added)}
    write_json(OUTPUT / 'protected_after.json', after)
    write_json(OUTPUT / 'isolation_verification.json', result)
    if changed or added:
        raise ValueError(f'Protected inventory changed: {result}')
    return result


def load_train():
    """Read training table only; final holdout features/labels are never loaded."""
    frame = pd.read_parquet(paths.TEMPORAL_TRAIN_FEATURES_PATH_V2)
    require_current_features(frame.attrs)
    if frame.part_id.max() != 20243 or frame.part_id.ge(20251).any():
        raise ValueError('Unexpected training temporal bounds')
    if frame.student_course_id.isna().any() or frame.student_course_id.duplicated().any():
        raise ValueError('Missing or duplicate modeling keys')
    if not frame.is_fail.eq(frame.final_mark.lt(50).astype(int)).all():
        raise ValueError('Incorrect failure labels')
    frame, _ = add_specialty_history_features(frame, frame.iloc[:0].copy())
    return frame


def specs():
    course_only = json.loads((paths.COURSE_ONLY_MODEL_DIR / 'model_metadata.json').read_text())['feature_contract']['model_features']
    if len(course_only) != 33 or not set(FIELDS).issubset(course_only):
        raise ValueError('Unexpected stage-1 contract')
    return [
        {'name': '47_grade', 'target': 'final_mark', 'features': BASE_FEATURES, 'credit_weighted': False},
        {'name': '47_fail', 'target': 'is_fail', 'features': BASE_FEATURES, 'credit_weighted': False},
        {'name': '33_grade', 'target': 'final_mark', 'features': course_only, 'credit_weighted': False},
        {'name': '33_fail', 'target': 'is_fail', 'features': course_only, 'credit_weighted': False},
        {'name': '47_points', 'target': 'points', 'features': BASE_FEATURES, 'credit_weighted': False},
        {'name': '57_degree_history_grade', 'target': 'final_mark',
         'features': [*BASE_FEATURES, *SPECIALTY_HISTORY_FEATURES], 'credit_weighted': False},
    ]


def matrix(frame, levels, features):
    base = [f for f in features if f in BASE_FEATURES]
    result = prepare_model_matrix(frame, levels, model_features=base)
    for field in features:
        if field not in BASE_FEATURES:
            result[field] = pd.to_numeric(frame[field], errors='coerce').astype('float32')
    return result[features]


def aggregate_points(frame, predicted_points):
    work = frame[KEYS + ['course_credits', 'points']].copy()
    work['actual_quality'] = work.course_credits * work.points
    work['predicted_quality'] = work.course_credits * np.asarray(predicted_points)
    result = work.groupby(KEYS, sort=True, as_index=False).agg(
        credits=('course_credits', 'sum'), actual_quality=('actual_quality', 'sum'),
        predicted_quality=('predicted_quality', 'sum'))
    result = result[result.credits.gt(0)].copy()
    result['actual_plan_gpa'] = result.actual_quality / result.credits
    result['predicted_plan_gpa'] = result.predicted_quality / result.credits
    return result


def predict(model, x, target):
    return np.clip(model.predict(x, num_threads=4), 0, {'final_mark':100, 'is_fail':1, 'points':4}[target])


def evaluate(frame, prediction, target, scale):
    actual = frame[target].to_numpy(dtype=float)
    if target == 'is_fail':
        probability = np.clip(prediction, 1e-7, 1-1e-7)
        losses = -(actual*np.log(probability)+(1-actual)*np.log1p(-probability))
        metrics = {'pr_auc': float(average_precision_score(actual, probability)),
                   'roc_auc': float(roc_auc_score(actual, probability)) if len(np.unique(actual)) == 2 else None,
                   'log_loss': float(log_loss(actual, probability, labels=[0,1])),
                   'brier': float(brier_score_loss(actual, probability))}
        return metrics, losses, None
    points = scale.convert(prediction, frame.grade_version_id)[0] if target == 'final_mark' else prediction
    point_error = np.asarray(points) - frame.points.to_numpy(dtype=float)
    plans = aggregate_points(frame, points)
    error = (plans.predicted_plan_gpa-plans.actual_plan_gpa).to_numpy()
    metrics = {'course_points_mae': float(np.abs(point_error).mean()),
               'course_points_rmse': float(np.sqrt(np.square(point_error).mean())),
               'plan_gpa_mae': float(np.abs(error).mean()), 'plan_gpa_rmse': float(np.sqrt(np.square(error).mean())),
               'plan_gpa_bias': float(error.mean()), 'plans': len(plans)}
    if target == 'final_mark':
        mark_error = prediction-actual
        metrics.update(grade_mae=float(np.abs(mark_error).mean()), grade_rmse=float(np.sqrt(np.square(mark_error).mean())),
                       grade_bias=float(mark_error.mean()))
    # Evaluate additive projection vs matched observed end GPA, not official repeat replacement.
    status = frame.groupby(KEYS, sort=True, as_index=False).agg(
        start_gpa=('start_agpa_points','first'), prior_credits=('prior_total_reg_credits','first'),
        end_gpa=('end_agpa_points','first'), start_credits=('start_total_in_credits','first'))
    plans = plans.merge(status, on=KEYS, validate='one_to_one')
    mask = (np.isfinite(plans[['start_gpa','prior_credits','end_gpa']]).all(axis=1)
            & plans.prior_credits.ge(0) & plans.end_gpa.between(0,4) & plans.start_gpa.between(0,4))
    projected = (plans.start_gpa*plans.prior_credits+plans.predicted_quality)/(plans.prior_credits+plans.credits)
    observed_projection = (plans.start_gpa*plans.prior_credits+plans.actual_quality)/(plans.prior_credits+plans.credits)
    metrics['projected_cumulative_gpa_mae_vs_end'] = float(np.abs(projected[mask]-plans.end_gpa[mask]).mean())
    metrics['additive_observed_gpa_mae_vs_end'] = float(np.abs(observed_projection[mask]-plans.end_gpa[mask]).mean())
    metrics['projected_comparable_plans'] = int(mask.sum())
    return metrics, np.abs(prediction-actual) if target == 'final_mark' else np.abs(point_error), plans


def fit_model(fit, x, spec, config, valid=None, vx=None):
    weight = training_weights(fit).to_numpy(dtype='float32')
    if spec['credit_weighted']:
        weight *= fit.course_credits.to_numpy(dtype='float32')
    return official.train_one(x, fit[spec['target']].to_numpy(dtype=float), weight,
                              config['parameters'], vx, None if valid is None else valid[spec['target']].to_numpy(dtype=float),
                              num_boost_round=config['rounds'])


def inner_selection(train, year, spec, scale):
    fit, valid = temporal_partition(train, year)
    levels = learn_category_levels(fit)
    tx, vx = matrix(fit, levels, spec['features']), matrix(valid, levels, spec['features'])
    results = []
    for candidate in official.PARAMETER_CANDIDATES:
        parameters = {**official.shared_parameters(candidate), 'num_threads': 4,
                      'objective': 'binary' if spec['target']=='is_fail' else 'regression',
                      'metric': 'binary_logloss' if spec['target']=='is_fail' else 'l1'}
        config = {'parameters': parameters, 'rounds': official.MAX_BOOST_ROUNDS}
        model = fit_model(fit, tx, spec, config, valid, vx)
        metrics, _, _ = evaluate(valid, predict(model, vx, spec['target']), spec['target'], scale)
        primary = 'log_loss' if spec['target']=='is_fail' else 'plan_gpa_mae'
        results.append({'candidate': candidate, 'score': metrics[primary], 'primary': primary,
                        'rounds': int(model.best_iteration), 'parameters': parameters})
    selected = min(results, key=lambda r:r['score'])
    output = {'inner_fit_max_part': int(fit.part_id.max()), 'inner_validation_parts': sorted(valid.part_id.unique().tolist()),
              'candidates': results, 'selected': selected}
    write_json(OUTPUT / str(year) / spec['name'] / 'inner_selection.json', output)
    print(f"SELECT {year} {spec['name']} {selected['candidate']['name']} {selected['rounds']} rounds", flush=True)
    return {'parameters':selected['parameters'], 'rounds': selected['rounds']}


def gain_rows(model, label):
    gains = model.feature_importance(importance_type='gain')
    total = gains.sum()
    return [{'model':label, 'feature':f, 'gain':float(g), 'gain_share_percent':float(100*g/total) if total else 0,
             'rank': int((gains>g).sum()+1)} for f,g in zip(model.feature_name(), gains)]


def permutation(model, frame, x, spec, scale, year):
    sampled = frame.sample(n=min(6000,len(frame)),random_state=42).sort_index()
    sx = x.loc[sampled.index].copy()
    base, _, _ = evaluate(sampled,predict(model,sx,spec['target']),spec['target'],scale)
    metric = 'log_loss' if spec['target']=='is_fail' else 'plan_gpa_mae'
    rows=[]
    for fields in [[f] for f in FIELDS]+[FIELDS]:
        for repeat in range(3):
            order=np.random.default_rng(42+repeat).permutation(len(sx))
            shuffled=sx.copy()
            for field in fields:
                shuffled[field]=sx[field].to_numpy()[order]
            score,_,_=evaluate(sampled,predict(model,shuffled,spec['target']),spec['target'],scale)
            rows.append({'year':year,'model':spec['name'],'fields':'+'.join(fields),'repeat':repeat,
                         'metric':metric,'baseline':base[metric],'delta':score[metric]-base[metric],
                         'rows':len(sampled),'sampling':'course rows; sampled partial historical plans'})
    return rows


def group_metrics(valid, prediction, spec, scale, year, variant):
    rows=[]
    # Fixed progress boundaries describe start snapshot credits, not verified earned hours.
    progress = pd.cut(valid.start_total_in_credits,[-np.inf,30,60,90,np.inf],right=False).astype('string')
    for kind, grouping in [('degree',valid.degree_id),('progress',progress)]:
        for value,index in grouping.groupby(grouping,observed=True).groups.items():
            part=valid.loc[index]
            if len(part)<100:
                continue
            position=valid.index.get_indexer(index)
            metrics,_,_=evaluate(part,prediction[position],spec['target'],scale)
            rows.append({'year':year,'model':spec['name'],'variant':variant,'group_kind':kind,
                         'group':str(value),'rows':len(part),**metrics})
    return rows


def run(resume=False):
    OUTPUT.mkdir(parents=True,exist_ok=True)
    setup_path=OUTPUT/'setup.json'
    inputs=[paths.TEMPORAL_TRAIN_FEATURES_PATH_V2,paths.MODEL_METADATA_PATH_V2,
            paths.COURSE_ONLY_MODEL_DIR/'model_metadata.json',paths.GRADE_SCALE_PATH]
    setup={'sources':{p.relative_to(paths.PROJECT_ROOT).as_posix():file_sha256(p) for p in inputs},
           'workflow_sha256':file_sha256(__file__),'variants':VARIANTS,'specs':specs(),
           'protocol':'Nested baseline-only 3-candidate tuning on inner previous year; freeze across nine variants',
           'outer_years':[2023,2024],'seed':42,'num_threads':4,'holdout_evaluated':False,
           'versions':{'python':platform.python_version(),'lightgbm':lgb.__version__,'pandas':pd.__version__},
           'derived_features_unchanged':['prior_fail_credit_ratio'],
           'selection_policy':'No production promotion; no 2025 evaluation in this exploratory audit'}
    signature=configuration_signature(setup)
    if setup_path.exists():
        if not resume:
            raise FileExistsError('Use --resume only for identical source signatures')
        validate_signature(json.loads(setup_path.read_text())['signature'],signature)
    else:
        if MODELS.exists() and any(MODELS.iterdir()):
            raise FileExistsError('Experimental model directory already populated')
        write_json(OUTPUT/'protected_before.json',protected_manifest())
        write_json(setup_path,{'signature':signature,**setup})
    started=perf_counter()
    rows,intervals,groups,importance,permutations=[],[],[],[],[]
    try:
        train=load_train()
        scale=GradeScale.from_parquet(paths.GRADE_SCALE_PATH)
        write_json(OUTPUT/'rows.json',{'rows':len(train),'parts':sorted(train.part_id.unique().tolist()),
                                     'fingerprint':row_fingerprint(train),'2025_targets_loaded':False})
        for year in [2023,2024]:
            fit=train.loc[train.part_id.le((year-1)*10+3)]
            valid=train.loc[train.part_id.between(year*10+1,year*10+3)]
            levels=learn_category_levels(fit)
            for spec in specs():
                evidence=OUTPUT/str(year)/spec['name']
                config_path=evidence/'inner_selection.json'
                if resume and config_path.exists():
                    selected=json.loads(config_path.read_text())['selected']
                    config={'parameters':selected['parameters'],'rounds':selected['rounds']}
                else:
                    config=inner_selection(train,year,spec,scale)
                model_dir=MODELS/str(year)/spec['name']
                model_dir.mkdir(parents=True,exist_ok=True)
                write_json(model_dir/'categories.json',levels)
                tx,vx=matrix(fit,levels,spec['features']),matrix(valid,levels,spec['features'])
                predictions=valid[['student_course_id',*KEYS,'points','final_mark','is_fail','course_credits','grade_version_id']].copy()
                base_loss,base_plans=None,None
                for variant in VARIANTS:
                    features=feature_subset(spec['features'],variant)
                    mx=tx[features]; ex=vx[features]
                    model_path=model_dir/f'{variant}.txt'
                    model_signature=configuration_signature({'run':signature,'year':year,'spec':spec,'variant':variant,
                        'features':features,'config':config,'fit_rows':row_fingerprint(fit),'valid_rows':row_fingerprint(valid)})
                    if resume and model_path.exists():
                        record=json.loads(model_path.with_suffix('.json').read_text())
                        validate_signature(record['signature'],model_signature)
                        if file_sha256(model_path)!=record['sha256']:
                            raise ValueError('Changed experimental model')
                        model=lgb.Booster(model_file=str(model_path))
                    else:
                        print(f"FIT {year} {spec['name']} {variant}: {len(fit)} rows, {len(features)} features",flush=True)
                        model=fit_model(fit,mx,spec,config)
                        model.save_model(str(model_path))
                        write_json(model_path.with_suffix('.json'),{'signature':model_signature,'sha256':file_sha256(model_path),
                                   'features':features,'configuration':config})
                    if model.feature_name()!=features:
                        raise ValueError('Model features differ from experiment input')
                    prediction=predict(model,ex,spec['target'])
                    predictions[variant]=prediction
                    metrics,loss,plans=evaluate(valid,prediction,spec['target'],scale)
                    rows.append({'year':year,'model':spec['name'],'variant':variant,'features':len(features),
                                 'fit_rows':len(fit),'rows':len(valid),**metrics})
                    groups.extend(group_metrics(valid,prediction,spec,scale,year,variant))
                    if variant=='A':
                        base_loss=loss; base_plans=plans
                        importance.extend(gain_rows(model,f"{year}_{spec['name']}_A"))
                        permutations.extend(permutation(model,valid,ex,spec,scale,year))
                    else:
                        primary='log_loss' if spec['target']=='is_fail' else ('grade_mae' if spec['target']=='final_mark' else 'course_points_mae')
                        intervals.append({'year':year,'model':spec['name'],'variant':variant,'metric':primary,
                            **paired_cluster_interval(valid.student_id,loss-base_loss)})
                        if plans is not None:
                            paired=plans.merge(base_plans[KEYS+['predicted_plan_gpa']],on=KEYS,suffixes=('','_A'),validate='one_to_one')
                            delta=(paired.predicted_plan_gpa-paired.actual_plan_gpa).abs()-(paired.predicted_plan_gpa_A-paired.actual_plan_gpa).abs()
                            intervals.append({'year':year,'model':spec['name'],'variant':variant,'metric':'plan_gpa_mae',
                                **paired_cluster_interval(paired.student_id,delta.to_numpy())})
                    print(f"DONE {year} {spec['name']} {variant}: {metrics}",flush=True)
                predictions.to_parquet(evidence/'predictions.parquet',index=False)
                pd.DataFrame(rows).to_csv(OUTPUT/'metrics.csv',index=False)
                pd.DataFrame(intervals).to_csv(OUTPUT/'paired_intervals.csv',index=False)
                pd.DataFrame(groups).to_csv(OUTPUT/'groups.csv',index=False)
                pd.DataFrame(importance).to_csv(OUTPUT/'baseline_gain.csv',index=False)
                pd.DataFrame(permutations).to_csv(OUTPUT/'permutation.csv',index=False)
        # Selected existing model importance is descriptive; never predict outer years with full-trained artifacts.
        selected=[]
        for label,path in [('official_grade',paths.GRADE_MODEL_PATH_V2),('official_fail',paths.FAIL_MODEL_PATH_V2),
                ('stage1_grade',paths.SHORTLIST_GRADE_MODEL_PATH),('stage1_fail',paths.SHORTLIST_FAIL_MODEL_PATH),
                ('selected_degree_history_mark',paths.DEGREE_POINTS_SELECTED_MODEL_PATH_V2)]:
            selected.extend(gain_rows(lgb.Booster(model_file=str(path)),label))
        pd.DataFrame(selected).to_csv(OUTPUT/'selected_gain.csv',index=False)
        write_json(OUTPUT/'execution.json',{'status':'COMPLETE','seconds':perf_counter()-started,
                    'ablation_fits':108,'inner_tuning_fits':36,'holdout_evaluated':False})
    finally:
        print('Isolation:',verify_protected(),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    if args.verify_only:
        print(verify_protected())
    else:
        run(args.resume)
