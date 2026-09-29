"""The four transparent retention baselines, each fitted on training data only.

B-B0 predicts no change, B-B1 the training median, B-B2 the median within pre-transfer minute
bands, and B-B3 the median within age-by-minute bands. All four were fixed before the held-out
evaluation was opened.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite
from typing import Iterable, Mapping, Sequence

import numpy as np


MINUTE_BANDS = ((450, 899), (900, 1799), (1800, 2699), (2700, None))
AGE_BANDS = ((None, 21), (22, 24), (25, 28), (29, 31), (32, None))


def minute_band(minutes: float) -> str:
    value = float(minutes)
    if value < 450:
        raise ValueError("primary baseline eligibility requires at least 450 pre minutes")
    for low, high in MINUTE_BANDS:
        if value >= low and (high is None or value <= high):
            return f"{low}+" if high is None else f"{low}-{high}"
    raise AssertionError("unreachable minute band")


def age_band(age: float) -> str:
    value = float(age)
    if not isfinite(value) or value < 0:
        raise ValueError("valid age required for age-band prediction")
    value = floor(value)
    for low, high in AGE_BANDS:
        if (low is None or value >= low) and (high is None or value <= high):
            return f"<={high}" if low is None else f">={low}" if high is None else f"{low}-{high}"
    raise AssertionError("unreachable age band")


class NoChangeBaseline:
    baseline_id = "B-B0"
    requires_fit = False

    def fit(self, reference_rows=None, reference_y=None, provenance=None):
        return self

    def predict(self, rows: Sequence[Mapping]) -> np.ndarray:
        return np.zeros(len(rows), dtype=float)


class TrainMedianBaseline:
    baseline_id = "B-B1"
    requires_fit = True

    def __init__(self):
        self.global_median_: float | None = None
        self.fit_provenance_: dict | None = None

    def fit(self, reference_rows: Sequence[Mapping], reference_y: Sequence[float], provenance: str = "SUPPLIED_REFERENCE_ONLY"):
        values = np.asarray(reference_y, dtype=float)
        if len(reference_rows) == 0 or len(reference_rows) != len(values) or not np.isfinite(values).all():
            raise ValueError("non-empty aligned finite reference rows and targets required")
        self.global_median_ = float(np.median(values))
        self.fit_provenance_ = {"source": provenance, "rows": len(values)}
        return self

    def predict(self, rows: Sequence[Mapping]) -> np.ndarray:
        if self.global_median_ is None:
            raise RuntimeError("baseline must be fitted on supplied reference data")
        return np.full(len(rows), self.global_median_, dtype=float)


class PreMinutesMedianBaseline(TrainMedianBaseline):
    baseline_id = "B-B2"

    def __init__(self):
        super().__init__()
        self.minute_medians_: dict[str, float] = {}

    def fit(self, reference_rows: Sequence[Mapping], reference_y: Sequence[float], provenance: str = "SUPPLIED_REFERENCE_ONLY"):
        super().fit(reference_rows, reference_y, provenance)
        cells: dict[str, list[float]] = {}
        for row, target in zip(reference_rows, reference_y):
            cells.setdefault(minute_band(row["pre_minutes"]), []).append(float(target))
        self.minute_medians_ = {k: float(np.median(v)) for k,v in cells.items()}
        return self

    def predict(self, rows: Sequence[Mapping]) -> np.ndarray:
        if self.global_median_ is None:
            raise RuntimeError("baseline must be fitted on supplied reference data")
        return np.asarray([self.minute_medians_.get(minute_band(r["pre_minutes"]), self.global_median_) for r in rows])


class AgeMinutesMedianBaseline(PreMinutesMedianBaseline):
    baseline_id = "B-B3"

    def __init__(self):
        super().__init__()
        self.age_minute_medians_: dict[tuple[str,str], float] = {}

    def fit(self, reference_rows: Sequence[Mapping], reference_y: Sequence[float], provenance: str = "SUPPLIED_REFERENCE_ONLY"):
        super().fit(reference_rows, reference_y, provenance)
        cells: dict[tuple[str,str], list[float]] = {}
        for row, target in zip(reference_rows, reference_y):
            if row.get("age") is None or not isfinite(float(row["age"])):
                continue
            key = (age_band(row["age"]), minute_band(row["pre_minutes"]))
            cells.setdefault(key, []).append(float(target))
        self.age_minute_medians_ = {k: float(np.median(v)) for k,v in cells.items()}
        return self

    def predict(self, rows: Sequence[Mapping]) -> np.ndarray:
        if self.global_median_ is None:
            raise RuntimeError("baseline must be fitted on supplied reference data")
        predictions = []
        for row in rows:
            mb = minute_band(row["pre_minutes"])
            age = row.get("age")
            key = None if age is None or not isfinite(float(age)) else (age_band(age), mb)
            predictions.append(self.age_minute_medians_.get(key, self.minute_medians_.get(mb, self.global_median_)))
        return np.asarray(predictions)
