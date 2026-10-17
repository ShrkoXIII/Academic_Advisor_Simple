"""Observed-course/plan evaluation; paired uncertainty resamples whole students.

Prior observed outcomes are descriptive, evaluation-only information. A zero
count is left-censored by available history and does not prove a new student.
"""
import numpy as np
import pandas as pd

from src.evaluation.evaluate_plan_gpa import (
    AUDIT_COLUMNS, PLAN_KEY, aggregate_plan_gpa, summarize_plan_errors,
)
from src.modeling.train_models import regression_metrics, classification_metrics

ROW_KEY = ['student_course_id']
CONTEXT = ['start_agpa_points', 'gpa_prev_1', 'prior_registered_semesters',
           'prior_observed_completed_semesters']
HISTORY_CAVEAT = ('Observed history is left-censored; no observed prior outcomes '
                  'does not establish a genuinely new student.')


def _keys(frame, keys):
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError(f'Null or duplicate keys: {keys}')


def _prediction(value, n, name, probability=False):
    a = np.asarray(value, dtype=float)
    if a.shape != (n,) or not np.isfinite(a).all():
        raise ValueError(f'{name} must contain one finite prediction per source row')
    if probability and ((a < 0) | (a > 1)).any():
        raise ValueError('fail_probability must be within [0, 1]')
    return a


def _failure_metrics(actual, probability):
    if len(np.unique(actual)) > 1:
        return classification_metrics(actual, probability)
    # Official function raises for ROC-AUC on one class; keep its clipping and
    # calibration definitions, and explicitly mark both ranking AUCs unavailable.
    p = np.clip(np.asarray(probability, dtype=float), 1e-7, 1-1e-7)
    y = np.asarray(actual, dtype=float)
    bins = np.minimum((p*10).astype(int), 9)
    calibration = sum(np.mean(bins == b) * abs(p[bins == b].mean()-y[bins == b].mean())
                      for b in range(10) if (bins == b).any())
    return {'pr_auc': np.nan, 'roc_auc': np.nan,
            'log_loss': float(-(y*np.log(p)+(1-y)*np.log1p(-p)).mean()),
            'brier': float(np.mean((p-y)**2)),
            'calibration_error_10_bins': float(calibration)}


def _macro(frame, column):
    return float(frame.assign(_absolute=frame[column].abs())
                 .groupby('student_id', observed=True)['_absolute'].mean().mean())


def _metrics(courses, plans):
    m = {'n_course_rows': len(courses), 'n_plans': len(plans),
         'n_students': courses.student_id.nunique()}
    if not len(courses):
        return m
    m.update({'grade_'+k: v for k,v in regression_metrics(
        courses.actual_mark.to_numpy(), courses.predicted_mark.to_numpy()).items()})
    m['grade_bias'] = float(courses.mark_error.mean())
    m.update({'fail_'+k:v for k,v in _failure_metrics(
        courses.actual_fail, courses.fail_probability).items()})
    m.update({'points_mae': float(courses.points_error.abs().mean()),
              'points_rmse': float(np.sqrt(np.mean(courses.points_error**2))),
              'points_bias': float(courses.points_error.mean()),
              'student_macro_grade_mae': _macro(courses, 'mark_error'),
              'student_macro_points_mae': _macro(courses, 'points_error'),
              'student_macro_plan_mae': _macro(plans, 'plan_gpa_error')})
    m.update({'plan_gpa_'+k:v for k,v in summarize_plan_errors(plans).items()})
    return m


def _cohort_masks(plans):
    g = plans.start_agpa_points
    observed = plans.prior_observed_completed_semesters
    yield 'overall', pd.Series(True, index=plans.index)
    for part in sorted(plans.part_id.unique()):
        yield f'part_{part}', plans.part_id.eq(part)
    for lower in range(4):
        yield f'positive_prior_gpa_{lower}_{lower+1}', g.gt(lower) & g.le(lower+1)
    yield 'positive_prior_gpa_le_2', g.gt(0) & g.le(2)
    yield 'zero_with_observed_prior_outcomes', g.eq(0) & observed.gt(0)
    yield 'zero_no_observed_prior_outcomes', g.eq(0) & observed.eq(0)
    yield 'zero_history_unknown', g.eq(0) & observed.isna()
    yield 'missing_prior_gpa', g.isna()
    yield 'prior_gpa_out_of_range', g.notna() & (g.lt(0) | g.gt(4))


def evaluate(rows, grade_prediction, fail_probability, grade_scale):
    """Return flat metrics, official-style course/plan frames, and cohort table."""
    _keys(rows, ROW_KEY)
    if rows[PLAN_KEY+['course_id']].isna().any().any():
        raise ValueError('Source contains null plan/course keys')
    grade = _prediction(grade_prediction,len(rows),'grade_prediction')
    probability = _prediction(fail_probability,len(rows),'fail_probability',True)
    if not len(rows):
        raise ValueError('Evaluation needs observed rows')
    numeric = rows[['course_credits','points','final_mark','is_fail']].to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or not rows.is_fail.isin([0,1]).all():
        raise ValueError('Observed outcomes and credits must be finite; fail target binary')
    if rows.course_credits.le(0).any():
        raise ValueError('Observed course credits must be positive')
    source = rows.copy()
    if 'prior_observed_completed_semesters' not in source:
        source['prior_observed_completed_semesters'] = np.nan
    for column in CONTEXT:
        if source.groupby(PLAN_KEY,observed=True)[column].nunique(dropna=False).gt(1).any():
            raise ValueError(f'Inconsistent within-plan context: {column}')
    observed = source.prior_observed_completed_semesters.dropna()
    if (observed.lt(0) | ~np.isfinite(observed) | observed.mod(1).ne(0)).any():
        raise ValueError('Observed prior-semester counts must be nonnegative integers')
    courses = source[list(dict.fromkeys(AUDIT_COLUMNS+CONTEXT))].copy().rename(columns={
        'final_mark':'actual_mark','points':'actual_points','gpa_points':'source_semester_gpa'})
    courses['predicted_mark'] = np.clip(grade,0,100)
    courses['predicted_points'], courses['predicted_grade'] = grade_scale.convert(
        courses.predicted_mark,courses.grade_version_id)
    courses['fail_probability'] = probability
    courses['actual_fail'] = source.is_fail.to_numpy()
    courses['mark_error'] = courses.predicted_mark-courses.actual_mark
    courses['points_error'] = courses.predicted_points-courses.actual_points
    courses['actual_quality_points'] = courses.course_credits*courses.actual_points
    courses['predicted_quality_points'] = courses.course_credits*courses.predicted_points
    plans = aggregate_plan_gpa(courses).merge(
        source[PLAN_KEY+CONTEXT].drop_duplicates(PLAN_KEY),on=PLAN_KEY,
        how='left',validate='one_to_one')
    metrics = _metrics(courses,plans)
    cohorts = []
    for name,mask in _cohort_masks(plans):
        subset = plans[mask]
        c = courses.merge(subset[PLAN_KEY],on=PLAN_KEY,how='inner',validate='many_to_one')
        cohorts.append({'cohort':name, 'scope':'part' if name.startswith('part_') else 'cohort',
            **_metrics(c,subset), 'history_caveat':HISTORY_CAVEAT,
            'plans_with_registered_prior_semesters':int(subset.prior_registered_semesters.gt(0).sum()),
            'plans_without_registered_prior_semesters':int(subset.prior_registered_semesters.eq(0).sum()),
            'plans_with_unknown_registered_history':int(subset.prior_registered_semesters.isna().sum())})
    return metrics,courses,plans,pd.DataFrame(cohorts)


def _pair(baseline,candidate,keys,source):
    for frame in [baseline,candidate,source]:
        _keys(frame,keys)
    expected = pd.MultiIndex.from_frame(source[keys])
    for frame in [baseline,candidate]:
        actual = pd.MultiIndex.from_frame(frame[keys])
        if len(expected)!=len(actual) or len(expected.difference(actual)):
            raise ValueError(f'Exact paired source key coverage required: {keys}')
    # Merge on the actual key, never compare by prediction row position.
    pair = baseline.merge(candidate,on=keys,suffixes=('_baseline','_candidate'),
                           how='inner',validate='one_to_one',sort=False)
    # Restore a canonical source order, ensuring deterministic clustered draws.
    return source[keys].merge(pair,on=keys,validate='one_to_one',sort=False)


def paired_intervals(rows, baseline_courses, candidate_courses,
                     baseline_plans, candidate_plans, draws=2000):
    """Candidate-minus-baseline percentile CIs, paired student clusters, seed 42.

    Course and plan means retain their observation denominators on each draw;
    student macro gives every sampled student equal weight. No row bootstrap.
    """
    if not isinstance(draws,int) or draws < 1:
        raise ValueError('draws must be a positive integer')
    course = _pair(baseline_courses,candidate_courses,ROW_KEY,rows)
    plan_source = rows[PLAN_KEY].drop_duplicates()
    plan = _pair(baseline_plans,candidate_plans,PLAN_KEY,plan_source)
    # Prediction identity and observed targets must agree, including context.
    for frame,columns in [(course,PLAN_KEY+['course_id','actual_mark','actual_points','actual_fail']),
                          (plan,['actual_plan_gpa','total_credits']+CONTEXT)]:
        for col in columns:
            if col in (ROW_KEY if frame is course else PLAN_KEY):
                continue
            a,b = frame[col+'_baseline'],frame[col+'_candidate']
            if not (a.eq(b) | (a.isna() & b.isna())).all():
                raise ValueError(f'Paired observed identity/context differs: {col}')
    course['student_id'] = course.student_id_baseline
    for col in CONTEXT:
        plan[col] = plan[col+'_baseline']
    # Ensure source identities have not been reassigned by both arms together.
    check = rows[ROW_KEY+PLAN_KEY+['course_id']].merge(
        course[ROW_KEY+[c+'_baseline' for c in PLAN_KEY+['course_id']]],on=ROW_KEY)
    if any(not check[c].eq(check[c+'_baseline']).all() for c in PLAN_KEY+['course_id']):
        raise ValueError('Paired course identity differs from source')
    results = []
    for name,mask in _cohort_masks(plan):
        subset = plan[mask]
        if not len(subset):
            continue
        c = course.merge(subset[PLAN_KEY],left_on=[k+'_baseline' for k in PLAN_KEY],
                         right_on=PLAN_KEY,validate='many_to_one')
        # Merge adds student_id suffixes because course already has that column.
        c['student_id'] = c.student_id_baseline
        students = pd.Index(subset.student_id.unique())
        n = len(students)
        totals,denominators,observations = [],[],[]
        names = ['grade_mae','points_mae','fail_log_loss','fail_brier',
                 'plan_gpa_mae','plan_gpa_bias','student_macro_plan_mae']
        for metric in names:
            frame = c if metric in names[:4] else subset
            if metric == 'grade_mae':
                delta = frame.mark_error_candidate.abs()-frame.mark_error_baseline.abs()
            elif metric == 'points_mae':
                delta = frame.points_error_candidate.abs()-frame.points_error_baseline.abs()
            elif metric in ['fail_log_loss','fail_brier']:
                y = frame.actual_fail_baseline.to_numpy(dtype=float)
                p = np.clip(frame.fail_probability_baseline.to_numpy(),1e-7,1-1e-7)
                q = np.clip(frame.fail_probability_candidate.to_numpy(),1e-7,1-1e-7)
                loss = lambda x: -(y*np.log(x)+(1-y)*np.log1p(-x))
                delta = loss(q)-loss(p) if metric=='fail_log_loss' else (q-y)**2-(p-y)**2
            else:
                a,b = frame.plan_gpa_error_baseline,frame.plan_gpa_error_candidate
                delta = b-a if metric=='plan_gpa_bias' else b.abs()-a.abs()
            group = pd.DataFrame({'student_id':frame.student_id.to_numpy(),
                                  'delta':np.asarray(delta)}).groupby('student_id').delta
            sums = group.sum().reindex(students).to_numpy()
            counts = group.size().reindex(students).to_numpy()
            if metric=='student_macro_plan_mae':
                sums,counts = sums/counts,np.ones(n)
            totals.append(sums)
            denominators.append(counts)
            observations.append(len(frame))
        total,denom = np.asarray(totals).T,np.asarray(denominators).T
        delta = total.sum(axis=0)/denom.sum(axis=0)
        rng = np.random.default_rng(42)
        samples = []
        for start in range(0,draws,32):
            multiplicity = rng.multinomial(n,np.full(n,1/n),size=min(32,draws-start))
            samples.append((multiplicity@total)/(multiplicity@denom))
        intervals = np.quantile(np.concatenate(samples),[.025,.975],axis=0)
        for j,metric in enumerate(names):
            results.append({'cohort':name,'metric':metric,'delta':float(delta[j]),
                'ci_low':float(intervals[0,j]),'ci_high':float(intervals[1,j]),
                'n_students':n,'n_observations':observations[j],'draws':draws,
                'resampling_unit':'student','seed':42})
    return pd.DataFrame(results)
