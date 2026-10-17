"""Ordered ablation subsets; the official contract remains untouched."""
from src.features.feature_contract import BASE_FEATURES
from src.features.temporal_features import COURSE_HISTORY_COLUMNS, PLAN_CONTEXT_COLUMNS
from src.experiments.course_only_core import COURSE_ONLY_FEATURES

REMOVED_FEATURES = frozenset({
    'course_history_avg_attempt', 'plan_credit_weighted_avg_attempt',
    'peer_credit_weighted_avg_attempt',
})
FULL_FEATURES = [name for name in BASE_FEATURES if name not in REMOVED_FEATURES]
SHORTLIST_FEATURES = [name for name in COURSE_ONLY_FEATURES if name not in REMOVED_FEATURES]
HISTORY_COLUMNS = [name for name in COURSE_HISTORY_COLUMNS if name not in REMOVED_FEATURES]
PLAN_COLUMNS = [name for name in PLAN_CONTEXT_COLUMNS if name not in REMOVED_FEATURES]
SUM_COLUMNS = ['effective_support', 'raw_count', 'mark_sum', 'fail_sum', 'retake_sum']
assert (len(FULL_FEATURES), len(SHORTLIST_FEATURES), len(HISTORY_COLUMNS), len(PLAN_COLUMNS)) == (44, 32, 6, 12)
