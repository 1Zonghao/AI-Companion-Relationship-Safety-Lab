"""Inter-rater agreement analysis — Cohen's kappa, Krippendorff's alpha, confusion matrix.

ALL pure Python — no pandas, no scipy, no numpy.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


def compute_raw_agreement(annotations_a: list[str], annotations_b: list[str]) -> float:
    """Compute raw agreement rate between two annotators."""
    if len(annotations_a) != len(annotations_b) or len(annotations_a) == 0:
        return 0.0
    matches = sum(1 for a, b in zip(annotations_a, annotations_b, strict=True) if a == b)
    return matches / len(annotations_a)


def compute_cohens_kappa(annotations_a: list[str], annotations_b: list[str]) -> float:
    """Compute Cohen's kappa for two annotators.

    Formula: kappa = (p_o - p_e) / (1 - p_e)
    where p_o = observed agreement, p_e = expected agreement by chance.
    """
    if len(annotations_a) != len(annotations_b) or len(annotations_a) == 0:
        return 0.0

    n = len(annotations_a)

    # Observed agreement
    p_o = sum(1 for a, b in zip(annotations_a, annotations_b, strict=True) if a == b) / n

    # Expected agreement — filter None values
    raw_labels = (set(annotations_a) | set(annotations_b)) - {None}
    all_labels = sorted(raw_labels)  # type: ignore[type-var]

    counts_a = Counter(annotations_a)
    counts_b = Counter(annotations_b)

    p_e = 0.0
    for label in all_labels:
        p_e += (counts_a.get(label, 0) / n) * (counts_b.get(label, 0) / n)

    if p_e == 1.0:
        return 1.0

    return (p_o - p_e) / (1.0 - p_e)


def compute_krippendorff_alpha(
    annotations: list[list[str | None]],
    labels: list[str] | None = None,
) -> float:
    """Compute Krippendorff's alpha for multiple annotators with possible missing values.

    Supports nominal data with missing values (None entries).

    Args:
        annotations: List of per-annotator label lists.
            Each inner list is one annotator's labels across items.
            Use None for missing annotations.
        labels: Pre-computed set of possible labels.

    Returns:
        Krippendorff's alpha value in [-1, 1].
    """
    if not annotations or len(annotations) < 2:
        return 0.0

    n_annotators = len(annotations)
    n_items = len(annotations[0])

    if n_items == 0:
        return 0.0

    # Collect all labels if not provided
    if labels is None:
        all_labels_set: set[str] = set()
        for ann in annotations:
            for val in ann:
                if val is not None:
                    all_labels_set.add(val)
        labels = sorted(all_labels_set)

    if not labels:
        return 0.0

    # Build coincidence matrix
    n_labels = len(labels)
    label_to_idx = {lab: i for i, lab in enumerate(labels)}

    # coincidence_matrix[i][j] = how many times label i and j co-occur
    coincidence: list[list[float]] = [[0.0] * n_labels for _ in range(n_labels)]

    for item_idx in range(n_items):
        # Get all non-None values for this item
        item_labels: list[int] = []
        for ann_idx in range(n_annotators):
            val = annotations[ann_idx][item_idx]
            if val is not None and val in label_to_idx:
                item_labels.append(label_to_idx[val])

        m = len(item_labels)
        if m <= 1:
            continue

        # Each pair of values gets weight 1/(m-1)
        for i in range(m):
            for j in range(m):
                if i != j:
                    coincidence[item_labels[i]][item_labels[j]] += 1.0 / (m - 1)

    # Total coincidences
    total = sum(sum(row) for row in coincidence)
    if total == 0:
        return 0.0

    # Expected disagreement
    marginals = [sum(row) for row in coincidence]

    # Observed disagreement
    d_o = 0.0
    for i in range(n_labels):
        for j in range(n_labels):
            if i != j:
                d_o += coincidence[i][j]
    d_o /= total

    # Expected disagreement
    d_e = 0.0
    for i in range(n_labels):
        for j in range(n_labels):
            if i != j:
                d_e += marginals[i] * marginals[j]
    if total > 1:
        d_e /= total * (total - 1)
    else:
        d_e = 0.0

    if d_e == 0:
        return 1.0 if d_o == 0 else 0.0

    return 1.0 - (d_o / d_e)


def compute_confusion_pairs(
    annotations_a: list[str],
    annotations_b: list[str],
) -> list[dict[str, Any]]:
    """Find label pairs that cause the most confusion between annotators.

    Returns:
        List of {label_a, label_b, count} sorted by count descending.
    """
    if len(annotations_a) != len(annotations_b):
        return []

    pair_counts: Counter = Counter()
    for a, b in zip(annotations_a, annotations_b, strict=True):
        if a != b:
            pair = tuple(sorted([a, b]))
            pair_counts[pair] += 1

    return [{"label_a": p[0], "label_b": p[1], "count": c} for p, c in pair_counts.most_common(20)]


def compute_per_label_agreement(
    annotations_a: list[str],
    annotations_b: list[str],
) -> dict[str, float]:
    """Compute agreement rate per label class."""
    if len(annotations_a) != len(annotations_b):
        return {}

    all_labels = sorted(set(annotations_a) | set(annotations_b) - {None})
    result: dict[str, float] = {}

    for label in all_labels:
        # For each label: how often do both annotators agree on this label?
        both_count = sum(
            1 for a, b in zip(annotations_a, annotations_b, strict=True) if a == b == label
        )
        # Either annotator used this label
        either_count = sum(
            1 for a, b in zip(annotations_a, annotations_b, strict=True) if a == label or b == label
        )
        result[label] = both_count / max(either_count, 1)

    return result
