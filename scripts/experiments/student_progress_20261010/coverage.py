"""Quantify evaluation-plan coverage of existing full registration context."""
import numpy as np
import pandas as pd
from src import paths
from .workflow import OUTPUT, KEYS, write_json


def run():
    frame=pd.read_parquet(paths.TEMPORAL_TRAIN_FEATURES_PATH_V2,
                          columns=[*KEYS,'course_credits','plan_total_credits','plan_course_count','course_id'])
    frame=frame[frame.part_id.between(20231,20243)]
    plans=frame.groupby(KEYS,as_index=False).agg(
        modeled_credits=('course_credits','sum'),modeled_courses=('course_id','size'),
        roster_credits=('plan_total_credits','first'),roster_courses=('plan_course_count','first'))
    plans['year']=plans.part_id//10
    rows=[]
    for year,part in plans.groupby('year'):
        same_credits=np.isclose(part.modeled_credits,part.roster_credits,rtol=0,atol=1e-8)
        same_courses=part.modeled_courses.eq(part.roster_courses)
        rows.append({'year':int(year),'plans':len(part),'exact_credits_plans':int(same_credits.sum()),
                     'exact_course_count_plans':int(same_courses.sum()),
                     'complete_registration_context_plans':int((same_credits&same_courses).sum()),
                     'coverage_pct':float(100*(same_credits&same_courses).mean()),
                     'mean_roster_minus_modeled_credits':float((part.roster_credits-part.modeled_credits).mean())})
    pd.DataFrame(rows).to_csv(OUTPUT/'plan_coverage.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__=='__main__':
    run()
