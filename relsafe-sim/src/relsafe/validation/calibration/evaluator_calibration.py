"""Evaluator calibration — compare automated evaluators against human labels."""

from __future__ import annotations


def compute_precision_recall_f1(
    predicted_labels: list[str],
    true_labels: list[str],
    positive_label: str,
) -> dict[str, float]:
    """Compute precision, recall, F1 for a binary label.

    Args:
        predicted_labels: Labels from the automated evaluator.
        true_labels: Ground-truth labels from human annotators.
        positive_label: Which label to treat as "positive".

    Returns:
        {"precision": ..., "recall": ..., "f1": ...}
    """
    if len(predicted_labels) != len(true_labels) or len(predicted_labels) == 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    tp = sum(
        1
        for p, t in zip(predicted_labels, true_labels, strict=True)
        if p == positive_label and t == positive_label
    )
    fp = sum(
        1
        for p, t in zip(predicted_labels, true_labels, strict=True)
        if p == positive_label and t != positive_label
    )
    fn = sum(
        1
        for p, t in zip(predicted_labels, true_labels, strict=True)
        if p != positive_label and t == positive_label
    )

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 0.001)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def compute_per_label_confusion(
    predicted_labels: list[str],
    true_labels: list[str],
) -> dict[str, dict[str, float]]:
    """Compute per-label precision, recall, F1 for all labels.

    Returns:
        {label: {"precision": ..., "recall": ..., "f1": ...}}
    """
    all_labels = sorted(set(predicted_labels) | set(true_labels))
    result: dict[str, dict[str, float]] = {}

    for label in all_labels:
        result[label] = compute_precision_recall_f1(predicted_labels, true_labels, label)

    return result


def find_false_positives(
    predicted_labels: list[str],
    true_labels: list[str],
    positive_label: str,
    case_ids: list[str] | None = None,
) -> list[str]:
    """Find cases where evaluator flagged positive but human said negative."""
    if case_ids is None:
        case_ids = [f"case_{i}" for i in range(len(predicted_labels))]

    return [
        case_ids[i]
        for i in range(len(predicted_labels))
        if predicted_labels[i] == positive_label and true_labels[i] != positive_label
    ]


def find_false_negatives(
    predicted_labels: list[str],
    true_labels: list[str],
    positive_label: str,
    case_ids: list[str] | None = None,
) -> list[str]:
    """Find cases where evaluator missed a positive that human flagged."""
    if case_ids is None:
        case_ids = [f"case_{i}" for i in range(len(predicted_labels))]

    return [
        case_ids[i]
        for i in range(len(predicted_labels))
        if predicted_labels[i] != positive_label and true_labels[i] == positive_label
    ]
