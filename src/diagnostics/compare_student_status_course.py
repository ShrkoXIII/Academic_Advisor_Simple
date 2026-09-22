"""Compare the final V2 status and course populations and semester keys."""

import pandas as pd

from src.paths import CLEAN_STUDENT_COURSE_PATH_V2, CLEAN_STUDENT_STATUS_PATH_V2


KEY_COLUMNS = ["student_id", "degree_id", "part_id"]


def main():
    student_status = pd.read_parquet(CLEAN_STUDENT_STATUS_PATH_V2)
    student_course = pd.read_parquet(CLEAN_STUDENT_COURSE_PATH_V2)
    status_ids = set(student_status["student_id"].dropna())
    course_ids = set(student_course["student_id"].dropna())

    print("Students in status:", len(status_ids))
    print("Students in course:", len(course_ids))
    print("Students in both:", len(status_ids & course_ids))
    print("Only in status:", len(status_ids - course_ids))
    print("Only in course:", len(course_ids - status_ids))

    status_keys = student_status[KEY_COLUMNS].drop_duplicates()
    course_keys = student_course[KEY_COLUMNS].drop_duplicates()
    comparison = status_keys.merge(
        course_keys,
        on=KEY_COLUMNS,
        how="outer",
        indicator=True,
        validate="one_to_one",
    )
    counts = comparison["_merge"].value_counts()
    print("\nStatus keys:", len(status_keys))
    print("Course keys:", len(course_keys))
    print("Both:", int(counts.get("both", 0)))
    print("Status-only:", int(counts.get("left_only", 0)))
    print("Course-only:", int(counts.get("right_only", 0)))

    merged = student_course.merge(
        student_status,
        on=KEY_COLUMNS,
        how="inner",
        validate="many_to_one",
        suffixes=("_course", "_status"),
    )
    dropped = len(student_course) - len(merged)
    print("\nCourse rows before merge:", len(student_course))
    print("Course rows after merge:", len(merged))
    print("Dropped rows:", dropped)
    print("Dropped percentage:", round(dropped / len(student_course) * 100, 4) if len(student_course) else 0)
    print("Students before:", len(course_ids))
    print("Students after:", merged["student_id"].nunique())
    print("Students completely lost:", len(course_ids - set(merged["student_id"].dropna())))

    print("\nStatus-only examples:")
    print(comparison[comparison["_merge"].eq("left_only")].head(20).to_string(index=False))
    print("\nCourse-only examples:")
    print(comparison[comparison["_merge"].eq("right_only")].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
