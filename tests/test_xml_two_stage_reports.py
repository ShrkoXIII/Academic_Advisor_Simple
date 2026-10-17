"""Behavioral checks for portable, escaped XML experiment reports."""
from copy import deepcopy
from html.parser import HTMLParser
import math


class _Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.values = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.values.append(data)


def _case():
    plans = [
        {"rank": rank, "course_ids": [f"course-{rank}"], "total_credits": 3,
         "expected_plan_gpa": 3 + rank / 10, "projected_cumulative_gpa": 2.8,
         "courses": [{"course_id": f"course-{rank}", "course_name": f"مقرر {rank}",
                      "course_credits": 3, "predicted_mark": 80 + rank,
                      "expected_points": 3 + rank / 10}]}
        for rank in (1, 2, 3)
    ]
    result = {"status": "success", "recommendations": plans,
              "counts": {"generated": 100, "scored33": 0, "scored47": 100},
              "timings": {"total_seconds": 1.25}}
    return {"case_id": "student-1", "xml_file": "student.xml", "student_id": "123.111",
            "degree_id": "1.111", "target_part": 20252, "history_as_of_part": 20251,
            "candidate_count": 4, "snapshot": {"current_gpa": 2.7},
            "candidates": [{"course_id": "candidate-1", "course_name": "مرشح مستقل",
                            "eligible": True, "allow_register": True}],
            "input_audit": {"raw_course_count": 5, "cleaned_course_count": 4},
            "warnings": [],
            "observed": {"status": "available", "actual_plan_gpa": 2.25,
                         "predicted_actual_plan_gpa": 2.5,
                         "actual_raw_course_count": 5, "actual_cleaned_course_count": 4,
                         "courses": [{"course_id": "observed-only", "course_name": "مقرر فعلي مستقل",
                                      "course_credits": 3, "predicted_points": 2.5,
                                      "actual_points": 2.25, "points_error": 0.25,
                                      "gpa_included": True}]},
            "experiment_01": result,
            "experiment_02": {**deepcopy(result), "shortlist": plans,
                              "counts": {"generated": 100, "scored33": 100, "scored47": 50},
                              "timings": {"total_seconds": 0.5}},
            "comparison": {"top_1_match": True, "top_3_overlap": 3,
                           "top_3_overlap_fraction": 1,
                           "baseline_top_3_recall_at_50_count": 3,
                           "baseline_top_3_recall_at_50": 1,
                           "gpa_regret": 0, "speedup": 2.5,
                           "prediction_parity": {"all_match": True, "compared_plan_count": 3,
                                                 "compared_course_count": 12,
                                                 "max_abs_points_difference": 0}}}


def _render(tmp_path, cases=None, manifest=None, summary=None):
    from src.experiments.xml_two_stage_reports import write_reports

    write_reports(tmp_path, [_case()] if cases is None else cases,
                  {} if manifest is None else manifest,
                  {} if summary is None else summary)
    return {path.name: path.read_text(encoding="utf-8") for path in tmp_path.glob("*.html")}


def test_reports_are_three_self_contained_arabic_documents(tmp_path):
    documents = _render(tmp_path)
    assert set(documents) == {"experiment_01_47_exhaustive.html",
                              "experiment_02_33_to_47.html", "comparison.html"}
    for source in documents.values():
        parsed = _Document(source)
        assert ("html", {"lang": "ar", "dir": "rtl"}) in parsed.tags
        assert any(tag == "style" for tag, _ in parsed.tags)
        assert not any(tag in {"script", "iframe"} for tag, _ in parsed.tags)
        assert not any(attrs.get("src") or attrs.get("href", "").startswith(("http:", "https:"))
                       for _, attrs in parsed.tags)
        assert "@import" not in source


def test_reports_escape_input_at_every_nested_display_boundary(tmp_path):
    case = _case()
    hostile = '<script>alert("bad")</script><img src=x onerror=alert(1)>'
    case["xml_file"] = hostile
    case["warnings"] = [hostile]
    case["snapshot"][hostile] = hostile
    case["input_audit"][hostile] = hostile
    case["candidates"][0]["course_name"] = hostile
    case["observed"]["courses"][0]["course_name"] = hostile
    for name in ("experiment_01", "experiment_02"):
        case[name]["recommendations"][0]["courses"][0]["course_name"] = hostile
    documents = _render(tmp_path, [case], {"note": hostile})
    for source in documents.values():
        assert hostile not in source
        assert "&lt;script&gt;" in source
        assert not any(tag in {"script", "img"} for tag, _ in _Document(source).tags)


def test_missing_metrics_render_as_unavailable_and_never_as_zero(tmp_path):
    documents = _render(tmp_path, [{"case_id": "missing", "experiment_01": {"status": "blocked"},
                                   "experiment_02": {"status": "blocked"}}])
    for source in documents.values():
        assert "—" in source
        assert "0.000" not in source
        assert "0.00" not in source
        assert "غير متاح" in source


def test_top_three_courses_and_observed_plan_are_displayed_separately(tmp_path):
    documents = _render(tmp_path)
    for name in ("experiment_01_47_exhaustive.html", "experiment_02_33_to_47.html"):
        source = documents[name]
        for rank in (1, 2, 3):
            assert f"course-{rank}" in source
        assert "observed-only" in source
        assert "مقرر فعلي مستقل" in source
        assert "فرق النقاط" in source
        assert "الخطة الفعلية" in source
        assert "عدد المقررات الخام" in source
        assert "عدد المقررات بعد التنظيف" in source


def test_shortlist_keeps_both_stage_ranks_and_gpas(tmp_path):
    case = _case()
    case["experiment_02"]["shortlist"] = [{"course_ids": ["shortlisted-only"],
                                           "stage1_rank": 7, "stage1_GPA": 2.125,
                                           "stage2_rank": 12, "stage2_GPA": 2.875}]
    source = _render(tmp_path, [case])["experiment_02_33_to_47.html"]
    assert "shortlisted-only" in source
    assert "2.125" in source and "2.875" in source
    assert any(tag == "details" for tag, _ in _Document(source).tags)


def test_comparison_charts_only_include_available_finite_measurements(tmp_path):
    case = _case()
    unavailable = {"case_id": "unmeasured", "comparison": {"gpa_regret": math.nan},
                   "experiment_01": {"timings": {"total_seconds": math.inf}},
                   "experiment_02": {"timings": {"total_seconds": None}}}
    source = _render(tmp_path, [case, unavailable])["comparison.html"]
    assert sum(tag == "svg" for tag, _ in _Document(source).tags) >= 3
    assert "nan" not in source.lower() and "infinity" not in source.lower()
    assert "2.500" in source
    assert "prediction_parity" in source
    assert "baseline_top_3_recall_at_50" in source


def test_failures_and_diagnostics_remain_visible(tmp_path):
    case = _case()
    case["experiment_01"] = {"status": "failed", "diagnostics": {"reason": "تجاوز حد الموارد"}}
    case["warnings"] = ["السجل أقدم من الفصل السابق"]
    source = _render(tmp_path, [case])["experiment_01_47_exhaustive.html"]
    assert "failed" in source
    assert "تجاوز حد الموارد" in source
    assert "السجل أقدم من الفصل السابق" in source


def test_comparison_distinguishes_recall_counts_fractions_and_parity_status(tmp_path):
    case = _case()
    case["comparison"]["baseline_top_3_recall_at_50_count"] = 2
    case["comparison"]["baseline_top_3_recall_at_50"] = 2 / 3
    source = _render(tmp_path, [case])["comparison.html"]
    assert "0.667" in source
    assert "compared_plan_count" in source
    assert "عدد المقارنات المشتركة" in source


def test_policy_aligned_error_is_not_conflated_with_full_roster_error(tmp_path):
    case = _case()
    source = _render(tmp_path, [case], summary={"actual_plan_mae": 0.55,
                                               "policy_aligned_actual_plan_mae": 0.15})[
                                                   "experiment_01_47_exhaustive.html"]
    assert "0.550" in source and "0.150" in source
    assert "مقام" in source
    assert "F/FE/FA/P" in source
    assert "D/W" in source


def test_comparison_describes_recorded_cumulative_gpa_regret(tmp_path):
    source = _render(tmp_path)["comparison.html"]
    assert "فقد المعدل التراكمي" in source
    assert "المعدل التراكمي لأفضل خطة كاملة" in source


def test_observed_policy_aligned_gpa_and_both_error_measures_are_visible(tmp_path):
    case = _case()
    case["observed"].update(predicted_actual_gpa_bearing_plan_gpa=2.375,
                            policy_aligned_plan_gpa_error=0.125,
                            policy_aligned_absolute_plan_gpa_error=0.125)
    source = _render(tmp_path, [case])["experiment_01_47_exhaustive.html"]
    assert "2.375" in source
    assert "الخطأ الفصلي المتوافق مع سياسة GPA" in source


def test_completed_and_non_feasible_cases_are_distinct_from_recommendation_success(tmp_path):
    summary = {"requested_students": 10, "selected_students": 10,
               "experiment_01_completed": 10, "experiment_01_successful": 6,
               "experiment_01_no_feasible": 4, "experiment_01_mean_seconds": 5.38}
    source = _render(tmp_path, summary=summary)["experiment_01_47_exhaustive.html"]
    assert "حالات اكتمل بحثها" in source
    assert "حالات بلا خطة تحقق 18 ساعة" in source
    assert "5.380" in source
