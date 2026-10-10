"""Candidate sensitivity must rebuild plan context without reading outcomes."""
import pandas as pd
from scripts.experiments.student_progress_20261010.downstream import candidate_rows
from src.features.temporal_features import PLAN_CONTEXT_COLUMNS


def pool():
    return pd.DataFrame({'course_id':list('abcde'),'course_credits':[3.]*5,
        'course_history_avg_mark':[60.]*5,'course_history_fail_rate':[.2]*5,
        'course_history_avg_attempt':[1.1]*5,'course_history_missing':[0]*5,
        'final_mark':[80.]*5})


def test_exact_candidates_recompute_plan_and_peer_context():
    proposals,target=candidate_rows(pool())
    assert target==9.
    assert proposals.plan_id.nunique()==10
    assert proposals.groupby('plan_id').course_credits.sum().eq(target).all()
    assert proposals.plan_course_count.eq(3).all()
    assert proposals.plan_total_credits.eq(9).all()
    assert proposals.peer_course_count.eq(2).all()
    assert proposals.peer_total_credits.eq(6).all()


def test_candidate_choice_and_context_are_outcome_independent():
    original=pool()
    changed=original.assign(final_mark=[0.,20.,40.,60.,100.])
    before,target_a=candidate_rows(original)
    after,target_b=candidate_rows(changed)
    assert target_a==target_b
    pd.testing.assert_frame_equal(before[['course_id','plan_id',*PLAN_CONTEXT_COLUMNS]],
                                  after[['course_id','plan_id',*PLAN_CONTEXT_COLUMNS]])
