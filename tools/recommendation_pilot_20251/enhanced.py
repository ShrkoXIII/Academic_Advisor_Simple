"""Individually testable research features; no production feature additions.

These helpers do not turn an invalid University History into a usable model.
No B/C model is trained until the history and serving prerequisites pass.
"""
import math

import numpy as np
import pandas as pd

from src.features.feature_contract import BASE_FEATURES


REMOVED_ATTEMPT_FEATURES = ["course_history_avg_attempt", "plan_credit_weighted_avg_attempt",
                            "peer_credit_weighted_avg_attempt"]
B_FEATURES = [f for f in BASE_FEATURES if f not in REMOVED_ATTEMPT_FEATURES]
PEER_FIELDS = ["start_agpa_points", "start_total_in_credits", "academic_progress",
               "gpa_trend_delta", "prior_total_fail_courses"]


class PointInTimePeers:
    """Uniform KNN within course/degree/grade version, using earlier peers only.

Distances use standardized shared nonmissing beginning-of-semester features;
at least three dimensions are required. One latest earlier record per peer
student is retained. Missing trend is omitted, never inferred as zero trend.
"""

    def __init__(self, rows, *, k=20, min_support=5):
        self.rows = pd.DataFrame(rows).copy()
        self.k, self.min_support = k, min_support
        if k < 1 or min_support < 1:
            raise ValueError("Positive peer limits are required.")
        required = {"student_id", "degree_id", "course_id", "part_id", "grade_version_id", "points",
                    "degree_credits_count", *[f for f in PEER_FIELDS if f != "academic_progress"]}
        if not required.issubset(self.rows):
            raise ValueError("Individual peer records lack required columns.")

    def predict(self, student, course_id, *, target_part):
        rows = self.rows
        mask = (pd.to_numeric(rows.part_id).lt(target_part)
                & rows.degree_id.astype(str).eq(str(student["degree_id"]))
                & rows.course_id.astype(str).eq(str(course_id))
                & rows.grade_version_id.astype(str).eq(str(student["grade_version_id"]))
                & rows.student_id.astype(str).ne(str(student["student_id"])))
        work = rows.loc[mask].sort_values("part_id", kind="stable").drop_duplicates("student_id", keep="last").copy()
        points = pd.to_numeric(work.points, errors="coerce")
        work = work.loc[points.between(0, 4)].copy()
        base = {"status": "NOT_AVAILABLE", "peer_expected_points": None, "similar_peer_support": 0,
                "max_source_part": None, "method": "prior_only_distinct_student_knn", "k": self.k,
                "minimum_support": self.min_support}
        if work.empty:
            return base
        denom = pd.to_numeric(work.degree_credits_count, errors="coerce")
        work["academic_progress"] = pd.to_numeric(work.start_total_in_credits, errors="coerce") / denom.where(denom.gt(0))
        reference = dict(student)
        total = reference.get("degree_credits_count")
        completed = reference.get("start_total_in_credits")
        reference["academic_progress"] = (float(completed) / float(total)
                                           if total is not None and not pd.isna(total) and float(total) > 0
                                           and completed is not None and not pd.isna(completed) else None)
        values = work[PEER_FIELDS].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        query = np.array([float(reference[f]) if reference.get(f) is not None and not pd.isna(reference[f]) else np.nan
                          for f in PEER_FIELDS])
        valid = np.isfinite(values) & np.isfinite(query)
        scales = np.array([np.std(values[np.isfinite(values[:, i]), i]) if np.isfinite(values[:, i]).any() else 1
                           for i in range(len(PEER_FIELDS))])
        scales[~np.isfinite(scales) | (scales == 0)] = 1
        differences = np.where(valid, (values - query) / scales, 0)
        shared = valid.sum(axis=1)
        distance = np.sqrt((differences ** 2).sum(axis=1) / np.maximum(shared, 1))
        distance[shared < 3] = np.inf
        order = np.argsort(distance, kind="stable")
        order = [i for i in order if math.isfinite(distance[i])][:self.k]
        selected = work.iloc[order]
        support = len(selected)
        base.update(similar_peer_support=support,
                    max_source_part=int(selected.part_id.max()) if support else None)
        if support >= self.min_support:
            base.update(status="AVAILABLE", peer_expected_points=float(pd.to_numeric(selected.points).mean()))
        return base


def difficulty_gap(student_reference_mark, course_average_mark):
    """Difference on the same 0..100 mark scale, never mean marks -> points."""
    if student_reference_mark is None or course_average_mark is None:
        return None
    values = [float(student_reference_mark), float(course_average_mark)]
    if not all(math.isfinite(v) and 0 <= v <= 100 for v in values):
        raise ValueError("Both references must be marks on the 0..100 scale.")
    return values[0] - values[1]


def plan_difficulty_balance(courses, *, high_risk_threshold=.5):
    """Post-prediction metrics, weighted risk standard deviation, threshold .5."""
    if not 0 < high_risk_threshold < 1 or not courses:
        raise ValueError("Courses and a probability threshold in (0,1) are required.")
    credits = np.array([float(c["course_credits"]) for c in courses])
    risks = np.array([float(c["fail_probability"]) for c in courses])
    if (not np.isfinite(credits).all() or not np.isfinite(risks).all() or np.any(credits < 0)
            or credits.sum() <= 0 or np.any((risks < 0) | (risks > 1))):
        raise ValueError("Valid credits and probabilities are required.")
    mean = float(np.average(risks, weights=credits))
    return {"max_fail_probability": float(risks.max()), "credit_weighted_fail_probability": mean,
            "risk_dispersion": float(np.sqrt(np.average((risks - mean) ** 2, weights=credits))),
            "high_risk_course_count": int((risks >= high_risk_threshold).sum()),
            "high_risk_threshold": high_risk_threshold}


def select_improving_plans(plans, *, top_n=3):
    valid = [p for p in plans if p.get("is_expected_cumulative_improvement") is True
             and p.get("projected_cumulative_gpa") is not None]
    return sorted(valid, key=lambda p: (-p["projected_cumulative_gpa"],
                                       p.get("expected_failed_credits", 0), str(p["plan_id"])))[:top_n]


def feature_readiness():
    return {
        "student_relative_course_strength": {"status": "NOT_AVAILABLE", "reason": "No trusted academic-domain taxonomy; curriculum requirement types are not academic domains."},
        "peer_expected_points": {"status": "TESTED_HELPER_NOT_TRAINED", "reason": "Individual historical data exists; C retraining is blocked by University History integrity."},
        "similar_peer_support": {"status": "TESTED_HELPER_NOT_TRAINED", "minimum_support": 5},
        "course_difficulty_gap": {"status": "BLOCKED", "reason": "University average marks are not validated across all15 sources; compatible mark references required."},
        "plan_difficulty_balance": {"status": "AVAILABLE_POST_PREDICTION", "high_risk_threshold": .5,
                                    "usage": "diagnostics only until C can be trained and ablated"},
    }
