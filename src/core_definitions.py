"""Pure mathematical definitions shared by both modules.

Per-90 rates, the robust standardization, the family-balanced distance, the log playing-time
retention target, and the eligibility predicates. No estimator is fitted here: callers supply
transformation parameters estimated from an authorized reference or training pool only.
"""

from __future__ import annotations

from math import exp, isfinite, log, log1p
from typing import Mapping, Sequence


def per90(count: float, minutes: float) -> float:
    """Return count per 90 minutes; reject non-positive exposure."""
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    return float(count) * 90.0 / float(minutes)


def success_share(successes: float, attempts: float) -> float | None:
    """Return a bounded success share, or missing when no attempt occurred."""
    if attempts < 0 or successes < 0 or successes > attempts:
        raise ValueError("invalid success/attempt counts")
    return None if attempts == 0 else float(successes) / float(attempts)


def heavy_tail_transform(value: float) -> float:
    """Pre-specified log1p transform for non-negative heavy-tailed rates."""
    if value < 0:
        raise ValueError("heavy-tail transform requires a non-negative value")
    return log1p(float(value))


def robust_z(value: float, median: float, iqr: float) -> float:
    """Robustly standardize with externally supplied median and IQR."""
    if not isfinite(iqr) or iqr <= 0:
        raise ValueError("IQR must be finite and positive")
    return (float(value) - float(median)) / float(iqr)


def family_l1(a: Sequence[float], b: Sequence[float]) -> float:
    """Mean absolute difference within one family."""
    if not a or len(a) != len(b):
        raise ValueError("family vectors must be non-empty and aligned")
    return sum(abs(float(x) - float(y)) for x, y in zip(a, b)) / len(a)


def family_l2(a: Sequence[float], b: Sequence[float]) -> float:
    """Root-mean-square difference within one family."""
    if not a or len(a) != len(b):
        raise ValueError("family vectors must be non-empty and aligned")
    return (sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)) / len(a)) ** 0.5


def family_cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine distance within one family."""
    if not a or len(a) != len(b):
        raise ValueError("family vectors must be non-empty and aligned")
    dot = sum(float(x) * float(y) for x, y in zip(a, b))
    na = sum(float(x) ** 2 for x in a) ** 0.5
    nb = sum(float(y) ** 2 for y in b) ** 0.5
    if na == 0 or nb == 0:
        raise ValueError("cosine distance is undefined for a zero vector")
    return 1.0 - dot / (na * nb)


def family_balanced_distance(
    family_distances: Mapping[str, float],
    weights: Mapping[str, float] | None = None,
) -> float:
    """Combine family distances without allowing larger families to dominate."""
    if not family_distances:
        raise ValueError("at least one family is required")
    if any(v < 0 or not isfinite(v) for v in family_distances.values()):
        raise ValueError("distances must be finite and non-negative")
    if weights is None:
        w = {k: 1.0 / len(family_distances) for k in family_distances}
    else:
        if set(weights) != set(family_distances):
            raise ValueError("weights and distances must have identical families")
        total = sum(weights.values())
        if total <= 0 or any(v < 0 for v in weights.values()):
            raise ValueError("weights must be non-negative with positive sum")
        w = {k: weights[k] / total for k in weights}
    return sum(w[k] * family_distances[k] for k in family_distances)


def similarity_display(distance: float) -> float:
    """Optional 0-100 presentation transform; never a probability."""
    if distance < 0 or not isfinite(distance):
        raise ValueError("distance must be finite and non-negative")
    return 100.0 * exp(-float(distance))


def minutes_log_retention(pre_minutes: float, post_minutes: float) -> float:
    """Primary adaptation target: ln(post minutes / pre minutes)."""
    if pre_minutes <= 0 or post_minutes <= 0:
        raise ValueError("pre and post minutes must be positive")
    return log(float(post_minutes) / float(pre_minutes))


def eligible_similarity_unit(
    minutes: float,
    position_group: str | None,
    is_goalkeeper: bool,
    observed_family_fractions: Mapping[str, float],
    minimum_minutes: float = 900,
    minimum_family_fraction: float = 0.5,
) -> bool:
    """Primary eligibility check; GK and outfield family sets are caller-defined."""
    if minutes < minimum_minutes or not position_group:
        return False
    if is_goalkeeper != (position_group.lower() == "goalkeeper"):
        return False
    return bool(observed_family_fractions) and all(
        fraction >= minimum_family_fraction
        for fraction in observed_family_fractions.values()
    )


def eligible_adaptation_event(
    pre_minutes: float,
    post_minutes: float,
    full_post_followup: bool,
    duplicate_event: bool = False,
    minimum_minutes: float = 450,
) -> bool:
    """Frozen retention-target eligibility check."""
    return (
        pre_minutes >= minimum_minutes
        and post_minutes >= minimum_minutes
        and full_post_followup
        and not duplicate_event
    )
