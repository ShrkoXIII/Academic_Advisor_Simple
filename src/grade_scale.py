from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class GradeScale:
    pass_bands: pd.DataFrame

    @classmethod
    def from_parquet(cls, path):
        grades = pd.read_parquet(path)
        return cls(grades[grades["finish_status"].eq("P")].copy())

    def convert(self, predicted_marks, grade_version_ids):
        marks = np.asarray(predicted_marks, dtype="float64")
        versions = pd.to_numeric(
            pd.Series(grade_version_ids), errors="coerce"
        ).to_numpy(dtype="float64")
        points = np.zeros(len(marks), dtype="float64")
        grade_labels = np.full(len(marks), "F", dtype=object)

        for version in np.unique(versions[~np.isnan(versions)]):
            bands = self.pass_bands[
                pd.to_numeric(
                    self.pass_bands["grade_version_id"], errors="coerce"
                ).eq(version)
            ].sort_values("from_percent")
            thresholds = bands["from_percent"].to_numpy(dtype="float64")
            band_points = bands["points"].to_numpy(dtype="float64")
            band_labels = bands["grade_show"].astype("string").to_numpy(dtype=object)

            row_mask = versions == version
            row_positions = np.flatnonzero(row_mask)
            selected = np.searchsorted(
                thresholds,
                marks[row_mask],
                side="right",
            ) - 1
            passed = selected >= 0
            points[row_positions[passed]] = band_points[selected[passed]]
            grade_labels[row_positions[passed]] = band_labels[selected[passed]]

        return points, grade_labels
