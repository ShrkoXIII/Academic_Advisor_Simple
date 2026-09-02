import pandas as pd

from paths import (
    CLEAN_DEGREE_COURSE_PATH,
    CLEAN_STUDENT_COURSE_PATH,
    CLEAN_STUDENT_STATUS_PATH,
)


AFTER_2022_PART = 20221


def normalize_name(series):
    values = series.astype("string").str.normalize("NFKC").str.strip().str.lower()
    values = values.str.replace(r"[\u064b-\u065f\u0670]", "", regex=True)
    values = values.str.replace("ـ", "", regex=False)
    values = values.str.replace(r"[أإآ]", "ا", regex=True)
    values = values.str.replace("ى", "ي", regex=False)
    values = values.str.replace(r"[^\w\s]", " ", regex=True)
    values = values.str.replace(r"\s+", " ", regex=True).str.strip()
    return values.mask(values.isin(["", "nan", "none", "null", "<na>"]))


def print_table(title, df):
    print(f"\n{title}")
    print(df.to_string(index=False))


def main():
    courses = pd.read_parquet(CLEAN_STUDENT_COURSE_PATH)
    status = pd.read_parquet(CLEAN_STUDENT_STATUS_PATH)
    degree_courses = pd.read_parquet(CLEAN_DEGREE_COURSE_PATH)

    plan_keys = degree_courses[["degree_id", "course_id"]].drop_duplicates()
    course_plan = courses.merge(
        plan_keys,
        on=["degree_id", "course_id"],
        how="left",
        indicator=True,
        validate="many_to_one",
    )
    print_table(
        "Course-to-plan coverage",
        course_plan["_merge"].value_counts().rename_axis("match").reset_index(name="rows"),
    )
    print_table(
        "Unmatched course-plan pairs",
        course_plan[course_plan["_merge"].eq("left_only")]
        .groupby(["degree_id", "course_id"], as_index=False)
        .agg(
            course_name_sl=("course_name_sl", "first"),
            rows=("student_course_id", "size"),
            students=("student_id", "nunique"),
            first_part=("part_id", "min"),
            last_part=("part_id", "max"),
        )
        .sort_values("rows", ascending=False)
        .head(50),
    )

    usage = courses.assign(course_name_key=normalize_name(courses["course_name_sl"]))
    usage = (
        usage.dropna(subset=["course_name_key"])
        .groupby(["course_name_key", "course_id"], as_index=False)
        .agg(
            course_name_sl=("course_name_sl", "first"),
            first_part=("part_id", "min"),
            last_part=("part_id", "max"),
            degrees=("degree_id", "nunique"),
            students=("student_id", "nunique"),
            rows=("student_course_id", "size"),
            credits=("course_credits", "median"),
        )
    )

    old = usage[usage["last_part"] < AFTER_2022_PART].rename(
        columns={
            "course_id": "old_course_id",
            "first_part": "old_first_part",
            "last_part": "old_last_part",
            "degrees": "old_degrees",
            "students": "old_students",
            "rows": "old_rows",
            "credits": "old_credits",
        }
    )
    new = usage[usage["first_part"] >= AFTER_2022_PART].rename(
        columns={
            "course_id": "new_course_id",
            "first_part": "new_first_part",
            "last_part": "new_last_part",
            "degrees": "new_degrees",
            "students": "new_students",
            "rows": "new_rows",
            "credits": "new_credits",
        }
    )
    candidates = old.merge(
        new.drop(columns=["course_name_sl"]),
        on="course_name_key",
        how="inner",
    )
    candidates = candidates[candidates["old_course_id"].ne(candidates["new_course_id"])]
    print_table(
        "Strict pre/post-2022 same-name ID candidates",
        candidates.sort_values(["new_rows", "old_rows"], ascending=False).head(50),
    )

    pairs = usage.merge(usage, on="course_name_key", suffixes=("_left", "_right"))
    coexist = pairs[
        pairs["course_id_left"].lt(pairs["course_id_right"])
        & pairs["first_part_left"].le(pairs["last_part_right"])
        & pairs["first_part_right"].le(pairs["last_part_left"])
    ]
    print_table(
        "Same-name IDs with overlapping usage (do not auto-map)",
        pd.DataFrame(
            [{"pairs": len(coexist), "course_name_families": coexist["course_name_key"].nunique()}]
        ),
    )

    print_table(
        "Plan and degree change status flags",
        status["finish_status"]
        .value_counts(dropna=False)
        .rename_axis("finish_status")
        .reset_index(name="rows")
        .query("finish_status in ['CHANGE_PLAN', 'CHANGE_DEGREE', 'CHANGE_FACULTY']"),
    )

    trajectory = status.sort_values(
        ["student_id", "part_id", "student_status_id"],
        kind="stable",
    ).copy()
    trajectory["next_degree_id"] = trajectory.groupby("student_id")["degree_id"].shift(-1)
    changes = trajectory[trajectory["finish_status"].eq("CHANGE_DEGREE")].copy()
    changes["next_degree_is_different"] = (
        changes["next_degree_id"].notna()
        & changes["next_degree_id"].ne(changes["degree_id"])
    )
    print_table(
        "CHANGE_DEGREE audit",
        pd.DataFrame(
            [
                {
                    "change_degree_rows": len(changes),
                    "students": changes["student_id"].nunique(),
                    "followed_by_different_degree": int(changes["next_degree_is_different"].sum()),
                }
            ]
        ),
    )
    print_table(
        "High-confidence degree transitions",
        changes[changes["next_degree_is_different"]]
        .groupby(["degree_id", "next_degree_id"], as_index=False)
        .agg(events=("student_id", "size"), students=("student_id", "nunique"))
        .sort_values("events", ascending=False)
        .head(50),
    )


if __name__ == "__main__":
    main()
