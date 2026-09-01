import pandas as pd

from paths import CLEAN_STUDENT_COURSE_PATH, CLEAN_STUDENT_STATUS_PATH


KEY_COLUMNS = ["student_id", "degree_id", "part_id"]


def main():
    student_status = pd.read_parquet(
        CLEAN_STUDENT_STATUS_PATH,
        columns=KEY_COLUMNS,
    ).drop_duplicates()

    student_course = pd.read_parquet(
        CLEAN_STUDENT_COURSE_PATH,
        columns=KEY_COLUMNS,
    ).drop_duplicates()

    comparison = student_status.merge(
        student_course,
        on=KEY_COLUMNS,
        how="outer",
        indicator=True,
        validate="one_to_one",
    )

    print("Student-status keys:", len(student_status))
    print("Student-course keys:", len(student_course))
    print("\nComparison:")
    print(comparison["_merge"].value_counts().to_string())

    print("\nStatus-only examples:")
    print(comparison[comparison["_merge"].eq("left_only")].head(20).to_string(index=False))

    print("\nCourse-only examples:")
    print(comparison[comparison["_merge"].eq("right_only")].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
