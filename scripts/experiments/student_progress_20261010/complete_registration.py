"""Supplement metrics on observed plans matching their full roster context."""
import numpy as np
import pandas as pd
from src.grade_scale import GradeScale
from src import paths
from .workflow import OUTPUT, KEYS, VARIANTS, specs, load_train, evaluate, paired_cluster_interval


def run():
    train=load_train(); scale=GradeScale.from_parquet(paths.GRADE_SCALE_PATH)
    rows=[]; intervals=[]
    for year in [2023,2024]:
        valid=train[train.part_id.between(year*10+1,year*10+3)]
        counts=valid.groupby(KEYS,as_index=False).agg(
            credits=('course_credits','sum'),count=('course_id','size'),
            roster_credits=('plan_total_credits','first'),roster_count=('plan_course_count','first'))
        keys=counts[np.isclose(counts.credits,counts.roster_credits,rtol=0,atol=1e-8)&counts['count'].eq(counts.roster_count)][KEYS]
        for spec in specs():
            predictions=pd.read_parquet(OUTPUT/str(year)/spec['name']/'predictions.parquet')
            columns=['student_course_id',*VARIANTS]
            part=valid.merge(keys,on=KEYS,validate='many_to_one').merge(predictions[columns],on='student_course_id',validate='one_to_one')
            baseline_loss=None; baseline_plans=None
            for variant in VARIANTS:
                metrics,loss,plans=evaluate(part,part[variant].to_numpy(),spec['target'],scale)
                rows.append({'year':year,'model':spec['name'],'variant':variant,'rows':len(part),**metrics})
                if variant=='A':
                    baseline_loss=loss; baseline_plans=plans
                else:
                    primary='log_loss' if spec['target']=='is_fail' else ('grade_mae' if spec['target']=='final_mark' else 'course_points_mae')
                    intervals.append({'year':year,'model':spec['name'],'variant':variant,'metric':primary,
                        **paired_cluster_interval(part.student_id,loss-baseline_loss)})
                    if plans is not None:
                        paired=plans.merge(baseline_plans[KEYS+['predicted_plan_gpa']],on=KEYS,suffixes=('','_A'),validate='one_to_one')
                        delta=(paired.predicted_plan_gpa-paired.actual_plan_gpa).abs()-(paired.predicted_plan_gpa_A-paired.actual_plan_gpa).abs()
                        intervals.append({'year':year,'model':spec['name'],'variant':variant,'metric':'plan_gpa_mae',
                            **paired_cluster_interval(paired.student_id,delta.to_numpy())})
    pd.DataFrame(rows).to_csv(OUTPUT/'complete_registration_metrics.csv',index=False)
    pd.DataFrame(intervals).to_csv(OUTPUT/'complete_registration_intervals.csv',index=False)
    print('Complete-roster comparison:',len(rows),'model/variant/year cells')


if __name__=='__main__':
    run()
