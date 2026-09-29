"""Behavioural feature families, eligibility rules and the similarity distance.

This module holds the frozen definitions used by the similarity module: the ten outfield feature
families, the three goalkeeper families, the minimum-exposure and coverage rules, and the robust
normalizer. It provides pairwise comparison tools only; it contains no full-dataset neighbour
search and produces no player ranking.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import exp, isfinite, log1p
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


MINUTES_PRIMARY = 900.0
MIN_FAMILY_FRACTION = 0.50
MIN_TOTAL_FRACTION = 0.70

OUTFIELD_FAMILIES = {
    "passing": ["per90_passes", "per90_successful_passes", "per90_forward_passes", "per90_long_passes"],
    "progression": ["per90_progressive_passes", "per90_passes_to_final_third", "per90_vertical_passes", "per90_progressive_run"],
    "creation": ["per90_key_passes", "per90_shot_assists", "per90_xg_assist", "per90_crosses"],
    "shooting": ["per90_shots", "per90_shots_on_target", "per90_xg_shot"],
    "dribbling": ["per90_dribbles", "per90_successful_dribbles", "per90_accelerations"],
    "defending": ["per90_defensive_actions", "per90_defensive_duels", "per90_interceptions", "per90_sliding_tackles"],
    "recoveries": ["per90_recoveries", "per90_opponent_half_recoveries", "per90_counterpressing_recoveries"],
    "receiving": ["per90_received_pass", "per90_touch_in_box", "per90_losses"],
    "aerial": ["per90_aerial_duels", "per90_aerial_duels_won"],
    "discipline": ["per90_fouls", "per90_yellow_cards"],
}

GK_FAMILIES = {
    "goalkeeping_shot_stopping": ["per90_gk_shots_against", "per90_gk_saves", "per90_gk_conceded_goals"],
    "goalkeeping_area_control": ["per90_gk_exits", "per90_gk_successful_exits", "per90_gk_aerial_duels"],
    "goalkeeping_distribution": ["per90_goal_kicks_short", "per90_goal_kicks_long", "per90_successful_goal_kicks"],
}

OUTFIELD_BOX_SCORE = [
    "per90_shots", "per90_shot_assists", "per90_passes", "per90_dribbles", "per90_defensive_actions"
]
GK_BOX_SCORE = ["per90_gk_saves", "per90_gk_conceded_goals", "per90_gk_exits", "per90_goal_kicks_long"]


class NoValidDistance(ValueError):
    """Raised when eligibility or feature support is inadequate."""


class RobustLogNormalizer:
    """Reference-only log1p + median/IQR normalizer with group/global fallback."""

    def __init__(self, features: Sequence[str], group_cols: Sequence[str] = ("competition_id", "super_season_id")):
        self.features = list(features)
        self.group_cols = list(group_cols)
        self.params_: dict[tuple, dict[str, tuple[float, float]]] | None = None
        self.global_params_: dict[str, tuple[float, float]] | None = None
        self.fit_provenance_: dict | None = None

    @staticmethod
    def _params(frame: pd.DataFrame, features: Sequence[str]) -> dict[str, tuple[float, float]]:
        result = {}
        for feature in features:
            values = pd.to_numeric(frame[feature], errors="coerce")
            values = np.log1p(values.where(values >= 0)).dropna()
            if values.empty:
                result[feature] = (np.nan, np.nan)
                continue
            q1, med, q3 = values.quantile([0.25, 0.50, 0.75]).tolist()
            result[feature] = (float(med), float(q3 - q1))
        return result

    def fit(self, reference_rows: pd.DataFrame, provenance: str = "SUPPLIED_REFERENCE_ONLY") -> "RobustLogNormalizer":
        required = set(self.features + self.group_cols)
        missing = required - set(reference_rows.columns)
        if missing:
            raise ValueError(f"missing reference columns: {sorted(missing)}")
        if reference_rows.empty:
            raise ValueError("reference_rows must not be empty")
        self.global_params_ = self._params(reference_rows, self.features)
        self.params_ = {}
        grouper = self.group_cols[0] if len(self.group_cols) == 1 else self.group_cols
        for key, group in reference_rows.groupby(grouper, dropna=False, sort=True):
            key = key if isinstance(key, tuple) else (key,)
            self.params_[key] = self._params(group, self.features)
        self.fit_provenance_ = {"source": provenance, "rows": int(len(reference_rows)), "group_cols": list(self.group_cols)}
        return self

    def transform(self, rows: pd.DataFrame) -> pd.DataFrame:
        if self.params_ is None or self.global_params_ is None:
            raise RuntimeError("normalizer must be fitted on supplied reference rows")
        out = rows.copy()
        for idx, row in rows.iterrows():
            key = tuple(row[c] for c in self.group_cols)
            params = self.params_.get(key, self.global_params_)
            for feature in self.features:
                value = row.get(feature)
                med, iqr = params[feature]
                if pd.isna(value) or float(value) < 0 or not isfinite(iqr) or iqr <= 0:
                    out.at[idx, feature] = np.nan
                else:
                    out.at[idx, feature] = (log1p(float(value)) - med) / iqr
        return out


def primary_eligible(row: Mapping, goalkeeper: bool) -> bool:
    position = str(row.get("position_group", "")).upper()
    is_gk = bool(row.get("goalkeeper_flag", False))
    return (
        float(row.get("minutes_played", 0) or 0) >= MINUTES_PRIMARY
        and position not in {"", "UNKNOWN", "NONE", "NAN"}
        and is_gk == goalkeeper
        and ((position == "GOALKEEPER") == goalkeeper)
    )


def _observed_fraction(row: Mapping, features: Sequence[str]) -> float:
    return sum(not pd.isna(row.get(f)) for f in features) / len(features)


def row_has_coverage(row: Mapping, families: Mapping[str, Sequence[str]]) -> bool:
    all_features = [f for values in families.values() for f in values]
    return (
        _observed_fraction(row, all_features) >= MIN_TOTAL_FRACTION
        and all(_observed_fraction(row, values) >= MIN_FAMILY_FRACTION for values in families.values())
    )


def pair_is_eligible(query: Mapping, candidate: Mapping, families: Mapping[str, Sequence[str]], goalkeeper: bool) -> bool:
    if not primary_eligible(query, goalkeeper) or not primary_eligible(candidate, goalkeeper):
        return False
    if str(query["position_group"]).upper() != str(candidate["position_group"]).upper():
        return False
    return row_has_coverage(query, families) and row_has_coverage(candidate, families)


def _common_values(a: Mapping, b: Mapping, features: Sequence[str]) -> tuple[list[float], list[float]]:
    left, right = [], []
    for f in features:
        if not pd.isna(a.get(f)) and not pd.isna(b.get(f)):
            left.append(float(a[f])); right.append(float(b[f]))
    return left, right


def compare_pair(
    query: Mapping,
    candidate: Mapping,
    baseline_id: str,
    *,
    exclude_exact_row: bool = True,
    exclude_same_player: bool = False,
) -> dict:
    """Compare one explicit pair; never searches or ranks a player universe."""
    goalkeeper = baseline_id.startswith("A-GK-")
    families = GK_FAMILIES if goalkeeper else OUTFIELD_FAMILIES
    if exclude_exact_row and query.get("canonical_similarity_key") == candidate.get("canonical_similarity_key"):
        raise NoValidDistance("exact row self-match excluded")
    if exclude_same_player and query.get("player_id") == candidate.get("player_id"):
        raise NoValidDistance("same-player comparison excluded by caller")
    if not pair_is_eligible(query, candidate, families, goalkeeper):
        raise NoValidDistance("eligibility or row-level family coverage failed")

    if baseline_id in {"A-B1", "A-GK-B1"}:
        features = GK_BOX_SCORE if goalkeeper else OUTFIELD_BOX_SCORE
        a, b = _common_values(query, candidate, features)
        required = 3 if goalkeeper else 4
        if len(a) < required:
            raise NoValidDistance("insufficient simple box-score overlap")
        distance = sum(abs(x-y) for x,y in zip(a,b)) / len(a)
        active_families = len(a)
    elif baseline_id in {"A-B2", "A-GK-B2"}:
        features = [f for values in families.values() for f in values]
        a, b = _common_values(query, candidate, features)
        if len(a) / len(features) < MIN_TOTAL_FRACTION:
            raise NoValidDistance("insufficient full-feature overlap")
        for fs in families.values():
            if len(_common_values(query, candidate, fs)[0]) / len(fs) < MIN_FAMILY_FRACTION:
                raise NoValidDistance("insufficient pairwise family overlap")
        distance = sum(abs(x-y) for x,y in zip(a,b)) / len(a)
        active_families = len(families)
    elif baseline_id in {"A-B3", "A-GK-B3", "A-B4", "A-GK-B4"}:
        family_distances = []
        for fs in families.values():
            a, b = _common_values(query, candidate, fs)
            if len(a) / len(fs) < MIN_FAMILY_FRACTION:
                raise NoValidDistance("insufficient pairwise family overlap")
            if baseline_id.endswith("B4"):
                na, nb = np.linalg.norm(a), np.linalg.norm(b)
                if na == 0 or nb == 0:
                    raise NoValidDistance("cosine undefined for zero family vector")
                family_distances.append(max(0.0, float(1 - np.dot(a,b)/(na*nb))))
            else:
                family_distances.append(sum(abs(x-y) for x,y in zip(a,b)) / len(a))
        distance = sum(family_distances) / len(family_distances)
        active_families = len(family_distances)
    else:
        raise ValueError(f"unsupported pairwise baseline: {baseline_id}")

    return {
        "query_unit_key": query.get("canonical_similarity_key"),
        "candidate_unit_key": candidate.get("canonical_similarity_key"),
        "distance": float(distance),
        "display_index": 100.0 * exp(-float(distance)),
        "baseline_id": baseline_id,
        "active_families": active_families,
        "coverage_flags": "PRIMARY_MINIMUMS_MET",
        "position_match": True,
        "query_minutes": float(query["minutes_played"]),
        "candidate_minutes": float(candidate["minutes_played"]),
    }


def deterministic_random_candidate(
    query: Mapping,
    candidates: Iterable[Mapping],
    *,
    seed: int = 20260926,
    exclude_exact_row: bool = True,
    exclude_same_player: bool = False,
) -> Mapping:
    """A-B0/A-GK-B0 deterministic position-matched random floor."""
    goalkeeper = bool(query.get("goalkeeper_flag", False))
    families = GK_FAMILIES if goalkeeper else OUTFIELD_FAMILIES
    eligible = []
    for candidate in candidates:
        if exclude_exact_row and query.get("canonical_similarity_key") == candidate.get("canonical_similarity_key"):
            continue
        if exclude_same_player and query.get("player_id") == candidate.get("player_id"):
            continue
        if pair_is_eligible(query, candidate, families, goalkeeper):
            eligible.append(candidate)
    if not eligible:
        raise NoValidDistance("no eligible random-floor candidate")
    eligible.sort(key=lambda x: str(x.get("canonical_similarity_key")))
    token = f"{seed}|{query.get('canonical_similarity_key')}".encode()
    index = int(sha256(token).hexdigest(), 16) % len(eligible)
    return eligible[index]


def random_floor_result(query: Mapping, candidates: Iterable[Mapping], **kwargs) -> dict:
    """Return A-B0/A-GK-B0 output in the common baseline-result schema."""
    candidate = deterministic_random_candidate(query, candidates, **kwargs)
    return {
        "query_unit_key": query.get("canonical_similarity_key"),
        "candidate_unit_key": candidate.get("canonical_similarity_key"),
        "distance": None,
        "display_index": None,
        "baseline_id": "A-GK-B0" if bool(query.get("goalkeeper_flag", False)) else "A-B0",
        "active_families": 0,
        "coverage_flags": "PRIMARY_MINIMUMS_MET_RANDOM_FLOOR",
        "position_match": True,
        "query_minutes": float(query["minutes_played"]),
        "candidate_minutes": float(candidate["minutes_played"]),
    }
