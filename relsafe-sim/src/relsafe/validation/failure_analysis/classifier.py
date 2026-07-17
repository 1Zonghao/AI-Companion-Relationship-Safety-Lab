"""Failure classifier — categorizes failures using the FailureTaxonomy."""

from __future__ import annotations

import uuid
from typing import Any

from relsafe.validation.contracts import FailureRecord


def classify_failure(
    error_message: str,
    run_id: str = "",
    episode_id: str = "",
    provider_name: str = "",
    metric_name: str = "",
    config_snapshot: dict[str, Any] | None = None,
) -> FailureRecord:
    """Classify a single failure using keyword matching against the taxonomy.

    Args:
        error_message: The error message or description.
        run_id: Run identifier.
        episode_id: Episode identifier.
        provider_name: Provider that failed.
        metric_name: Metric being computed when failure occurred.
        config_snapshot: Configuration at time of failure.

    Returns:
        FailureRecord with classified failure_type.
    """
    msg_lower = error_message.lower()

    # Classification rules (order matters — most specific first)
    failure_type = "UNSUPPORTED_CLAIM"  # default

    if "timeout" in msg_lower or "timed out" in msg_lower:
        failure_type = "PROVIDER_TIMEOUT"
    elif "refused" in msg_lower or "refusal" in msg_lower or "content policy" in msg_lower:
        failure_type = "PROVIDER_REFUSAL"
    elif "invalid" in msg_lower and (
        "json" in msg_lower or "structured" in msg_lower or "parse" in msg_lower
    ):
        failure_type = "INVALID_STRUCTURED_OUTPUT"
    elif "seed" in msg_lower and (
        "unstable" in msg_lower or "instability" in msg_lower or "different" in msg_lower
    ):
        failure_type = "SEED_INSTABILITY"
    elif "prompt" in msg_lower and (
        "sensitive" in msg_lower
        or "sensitivity" in msg_lower
        or "perturb" in msg_lower
        or "variant" in msg_lower
    ):
        failure_type = "PROMPT_SENSITIVITY"
    elif "simulator" in msg_lower and ("depend" in msg_lower or "model" in msg_lower):
        failure_type = "SIMULATOR_DEPENDENCE"
    elif "judge" in msg_lower and ("disagree" in msg_lower or "differ" in msg_lower):
        failure_type = "JUDGE_DISAGREEMENT"
    elif "false positive" in msg_lower:
        failure_type = "RULE_FALSE_POSITIVE"
    elif "false negative" in msg_lower:
        failure_type = "RULE_FALSE_NEGATIVE"
    elif "truncat" in msg_lower or "context length" in msg_lower:
        failure_type = "CONTEXT_TRUNCATION"
    elif "memory" in msg_lower and ("inconsist" in msg_lower or "mismatch" in msg_lower):
        failure_type = "MEMORY_INCONSISTENCY"
    elif "event" in msg_lower and (
        "normaliz" in msg_lower or "malformed" in msg_lower or "missing" in msg_lower
    ):
        failure_type = "EVENT_NORMALIZATION_FAILURE"
    elif "transition" in msg_lower and ("param" in msg_lower or "instability" in msg_lower):
        failure_type = "TRANSITION_PARAMETER_INSTABILITY"
    elif "scenario" in msg_lower and ("leak" in msg_lower or "bleed" in msg_lower):
        failure_type = "SCENARIO_LEAKAGE"
    elif "label" in msg_lower and ("ambig" in msg_lower or "unclear" in msg_lower):
        failure_type = "LABEL_AMBIGUITY"
    elif "self" in msg_lower and "evaluat" in msg_lower:
        failure_type = "SELF_EVALUATION_RISK"
    elif ("cache" in msg_lower or "replay" in msg_lower) and (
        "mismatch" in msg_lower or "differ" in msg_lower
    ):
        failure_type = "CACHE_REPLAY_MISMATCH"
    elif "claim" in msg_lower and ("unsupported" in msg_lower or "over" in msg_lower):
        failure_type = "UNSUPPORTED_CLAIM"

    severity = "medium"
    if failure_type in (
        "PROVIDER_TIMEOUT",
        "PROVIDER_REFUSAL",
        "EVENT_NORMALIZATION_FAILURE",
    ) or failure_type in (
        "SEED_INSTABILITY",
        "TRANSITION_PARAMETER_INSTABILITY",
        "CACHE_REPLAY_MISMATCH",
    ):
        severity = "high"
    elif failure_type in (
        "LABEL_AMBIGUITY",
        "PROMPT_SENSITIVITY",
        "RULE_FALSE_NEGATIVE",
    ):
        severity = "low"

    return FailureRecord(
        failure_id=f"fail-{uuid.uuid4().hex[:12]}",
        failure_type=failure_type,
        run_id=run_id,
        episode_id=episode_id,
        provider_name=provider_name,
        metric_name=metric_name,
        evidence={"error_message": error_message},
        config_snapshot=config_snapshot or {},
        severity=severity,
    )


def classify_failures(
    failures: list[dict[str, Any]],
) -> list[FailureRecord]:
    """Classify a batch of failures.

    Args:
        failures: List of failure dicts from experiment runner output.

    Returns:
        List of classified FailureRecords.
    """
    records: list[FailureRecord] = []
    for f in failures:
        records.append(
            classify_failure(
                error_message=f.get("error", f.get("error_message", "Unknown failure")),
                run_id=f.get("run_id", ""),
                episode_id=f.get("episode_id", ""),
                provider_name=f.get("provider_name", ""),
                metric_name=f.get("metric_name", ""),
                config_snapshot=f.get("config", {}),
            )
        )
    return records
