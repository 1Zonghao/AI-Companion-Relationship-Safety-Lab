"""Tests for failure classifier -- classify_failure, classify_failures, and
FAILURE_TAXONOMY_V1 integrity.
"""

from __future__ import annotations

from relsafe.validation.contracts import FAILURE_TAXONOMY_V1, FailureRecord
from relsafe.validation.failure_analysis.classifier import classify_failure, classify_failures

# =============================================================================
# Single failure classification
# =============================================================================


class TestClassifyFailure:
    def test_classify_timeout(self) -> None:
        record = classify_failure("Request timed out after 60 seconds")
        assert record.failure_type == "PROVIDER_TIMEOUT"

    def test_classify_timeout_variant(self) -> None:
        record = classify_failure("The connection timed out while waiting for response")
        assert record.failure_type == "PROVIDER_TIMEOUT"

    def test_classify_refusal(self) -> None:
        record = classify_failure("Content policy refusal")
        assert record.failure_type == "PROVIDER_REFUSAL"

    def test_classify_refusal_variant(self) -> None:
        record = classify_failure("The provider refused to generate this content")
        assert record.failure_type == "PROVIDER_REFUSAL"

    def test_classify_invalid_json(self) -> None:
        record = classify_failure("Invalid JSON in structured output")
        assert record.failure_type == "INVALID_STRUCTURED_OUTPUT"

    def test_classify_parse_error(self) -> None:
        record = classify_failure("Failed to parse structured output: invalid format")
        assert record.failure_type == "INVALID_STRUCTURED_OUTPUT"

    def test_classify_seed_instability(self) -> None:
        record = classify_failure("Score unstable across seeds")
        assert record.failure_type == "SEED_INSTABILITY"

    def test_classify_seed_instability_variant(self) -> None:
        record = classify_failure("Seed instability detected in metric scores")
        assert record.failure_type == "SEED_INSTABILITY"

    def test_classify_prompt_sensitivity(self) -> None:
        record = classify_failure("Prompt is sensitive to minor rewrites")
        assert record.failure_type == "PROMPT_SENSITIVITY"

    def test_classify_simulator_dependence(self) -> None:
        record = classify_failure("Simulator model dependence detected")
        assert record.failure_type == "SIMULATOR_DEPENDENCE"

    def test_classify_judge_disagreement(self) -> None:
        record = classify_failure("Judge disagreement exceeded threshold")
        assert record.failure_type == "JUDGE_DISAGREEMENT"

    def test_classify_false_positive(self) -> None:
        record = classify_failure("False positive in rule-based evaluator")
        assert record.failure_type == "RULE_FALSE_POSITIVE"

    def test_classify_false_negative(self) -> None:
        record = classify_failure("False negative: missed risk pattern")
        assert record.failure_type == "RULE_FALSE_NEGATIVE"

    def test_classify_context_truncation(self) -> None:
        record = classify_failure("Context truncated due to length")
        assert record.failure_type == "CONTEXT_TRUNCATION"

    def test_classify_context_length(self) -> None:
        record = classify_failure("Exceeded context length limit")
        assert record.failure_type == "CONTEXT_TRUNCATION"

    def test_classify_memory_inconsistency(self) -> None:
        record = classify_failure("Memory inconsistency detected in state")
        assert record.failure_type == "MEMORY_INCONSISTENCY"

    def test_classify_event_normalization(self) -> None:
        record = classify_failure("Event normalization failure: missing fields")
        assert record.failure_type == "EVENT_NORMALIZATION_FAILURE"

    def test_classify_malformed_event(self) -> None:
        record = classify_failure("Malformed event in sequence")
        assert record.failure_type == "EVENT_NORMALIZATION_FAILURE"

    def test_classify_transition_instability(self) -> None:
        record = classify_failure("Transition parameter instability detected")
        assert record.failure_type == "TRANSITION_PARAMETER_INSTABILITY"

    def test_classify_scenario_leakage(self) -> None:
        record = classify_failure("Scenario leakage detected in scores")
        assert record.failure_type == "SCENARIO_LEAKAGE"

    def test_classify_label_ambiguity(self) -> None:
        record = classify_failure("Label ambiguity among annotators")
        assert record.failure_type == "LABEL_AMBIGUITY"

    def test_classify_self_evaluation_risk(self) -> None:
        record = classify_failure("Self evaluation risk: same model used")
        assert record.failure_type == "SELF_EVALUATION_RISK"

    def test_classify_cache_replay_mismatch(self) -> None:
        record = classify_failure("Cache replay mismatch detected")
        assert record.failure_type == "CACHE_REPLAY_MISMATCH"

    def test_classify_unsupported_claim(self) -> None:
        record = classify_failure("Claim unsupported by evidence")
        assert record.failure_type == "UNSUPPORTED_CLAIM"

    def test_classify_default(self) -> None:
        record = classify_failure("Something unexpected happened that doesn't match any pattern")
        assert record.failure_type == "UNSUPPORTED_CLAIM"

    def test_classify_empty_message(self) -> None:
        record = classify_failure("")
        assert record.failure_type == "UNSUPPORTED_CLAIM"

    def test_classify_case_insensitive(self) -> None:
        record = classify_failure("TIMEOUT ERROR")
        assert record.failure_type == "PROVIDER_TIMEOUT"

    def test_returns_failure_record_instance(self) -> None:
        record = classify_failure("Timeout occurred")
        assert isinstance(record, FailureRecord)

    def test_record_has_failure_id(self) -> None:
        record = classify_failure("Timeout")
        assert record.failure_id.startswith("fail-")
        assert len(record.failure_id) > 5

    def test_record_stores_error_message(self) -> None:
        msg = "Something broke"
        record = classify_failure(msg)
        assert record.evidence["error_message"] == msg

    def test_record_stores_optional_fields(self) -> None:
        record = classify_failure(
            error_message="Timeout",
            run_id="run-001",
            episode_id="ep-002",
            provider_name="openai",
            metric_name="sycophancy",
            config_snapshot={"seed": 42},
        )
        assert record.run_id == "run-001"
        assert record.episode_id == "ep-002"
        assert record.provider_name == "openai"
        assert record.metric_name == "sycophancy"
        assert record.config_snapshot == {"seed": 42}


# =============================================================================
# Severity assignment
# =============================================================================


class TestSeverityAssignment:
    def test_timeout_severity_high(self) -> None:
        record = classify_failure("Timeout occurred")
        assert record.severity == "high"

    def test_refusal_severity_high(self) -> None:
        record = classify_failure("Content policy refusal")
        assert record.severity == "high"

    def test_seed_instability_severity_high(self) -> None:
        record = classify_failure("Seed instability detected")
        assert record.severity == "high"

    def test_label_ambiguity_severity_low(self) -> None:
        record = classify_failure("Label ambiguity among annotators")
        assert record.severity == "low"

    def test_prompt_sensitivity_severity_low(self) -> None:
        record = classify_failure("Prompt is sensitive to rewrites")
        assert record.severity == "low"

    def test_false_negative_severity_low(self) -> None:
        record = classify_failure("False negative in detection")
        assert record.severity == "low"

    def test_default_severity_medium(self) -> None:
        record = classify_failure("Something random happened")
        assert record.severity == "medium"

    def test_severity_in_valid_set(self) -> None:
        for msg in [
            "Timeout",
            "Refusal",
            "Invalid JSON",
            "Seed instability",
            "Memory inconsistency",
            "Something else",
        ]:
            record = classify_failure(msg)
            assert record.severity in ("critical", "high", "medium", "low"), (
                f"Unexpected severity {record.severity} for '{msg}'"
            )


# =============================================================================
# Batch classification
# =============================================================================


class TestClassifyFailures:
    def test_classify_batch(self) -> None:
        failures = [
            {"error": "timeout", "run_id": "run-1"},
            {"error": "refusal", "run_id": "run-2"},
        ]
        records = classify_failures(failures)
        assert len(records) == 2
        assert records[0].failure_type == "PROVIDER_TIMEOUT"
        assert records[1].failure_type == "PROVIDER_REFUSAL"

    def test_classify_batch_with_error_message_key(self) -> None:
        failures = [
            {"error_message": "timeout occurred"},
        ]
        records = classify_failures(failures)
        assert len(records) == 1
        assert records[0].failure_type == "PROVIDER_TIMEOUT"

    def test_classify_batch_empty(self) -> None:
        records = classify_failures([])
        assert records == []

    def test_classify_batch_preserves_metadata(self) -> None:
        failures = [
            {
                "error": "timeout",
                "run_id": "run-abc",
                "episode_id": "ep-123",
                "provider_name": "openai",
                "metric_name": "sycophancy",
            },
        ]
        records = classify_failures(failures)
        assert records[0].run_id == "run-abc"
        assert records[0].episode_id == "ep-123"
        assert records[0].provider_name == "openai"
        assert records[0].metric_name == "sycophancy"

    def test_classify_batch_handles_missing_error(self) -> None:
        failures = [{}]
        records = classify_failures(failures)
        assert len(records) == 1
        assert records[0].failure_type == "UNSUPPORTED_CLAIM"

    def test_classify_batch_handles_config_snapshot(self) -> None:
        failures = [
            {
                "error": "timeout",
                "config": {"seed": 42},
            },
        ]
        records = classify_failures(failures)
        assert records[0].config_snapshot == {"seed": 42}


# =============================================================================
# FAILURE_TAXONOMY_V1 integrity
# =============================================================================


class TestTaxonomyIntegrity:
    def test_taxonomy_has_18_entries(self) -> None:
        assert len(FAILURE_TAXONOMY_V1) == 18

    def test_classifier_covers_all_taxonomy_types(self) -> None:
        """Each taxonomy type should be reachable by at least one classification rule."""
        # Test each type by providing a matching error message
        test_cases: list[tuple[str, str]] = [
            ("prompt sensitive to rewrites", "PROMPT_SENSITIVITY"),
            ("seed unstable across runs", "SEED_INSTABILITY"),
            ("simulator model dependence", "SIMULATOR_DEPENDENCE"),
            ("judge disagreement detected", "JUDGE_DISAGREEMENT"),
            ("false positive in rule check", "RULE_FALSE_POSITIVE"),
            ("false negative in detection", "RULE_FALSE_NEGATIVE"),
            ("context truncation occurred", "CONTEXT_TRUNCATION"),
            ("memory inconsistency found", "MEMORY_INCONSISTENCY"),
            ("event normalization failure", "EVENT_NORMALIZATION_FAILURE"),
            ("timeout occurred", "PROVIDER_TIMEOUT"),
            ("content refusal", "PROVIDER_REFUSAL"),
            ("invalid JSON in structured output", "INVALID_STRUCTURED_OUTPUT"),
            ("transition parameter instability", "TRANSITION_PARAMETER_INSTABILITY"),
            ("scenario leakage detected", "SCENARIO_LEAKAGE"),
            ("label ambiguity detected", "LABEL_AMBIGUITY"),
            ("self evaluation risk", "SELF_EVALUATION_RISK"),
            ("cache replay mismatch", "CACHE_REPLAY_MISMATCH"),
            ("unsupported claim in report", "UNSUPPORTED_CLAIM"),
        ]
        for msg, expected_type in test_cases:
            record = classify_failure(msg)
            error_msg = (
                f"Message '{msg}' classified as {record.failure_type}, expected {expected_type}"
            )
            assert record.failure_type == expected_type, error_msg

    def test_all_taxonomy_keys_have_valid_characters(self) -> None:
        for key in FAILURE_TAXONOMY_V1:
            assert "_" in key, f"Key {key} does not contain underscore"
            assert key.isupper(), f"Key {key} is not uppercase"

    def test_all_taxonomy_descriptions_are_sentences(self) -> None:
        for key, desc in FAILURE_TAXONOMY_V1.items():
            assert len(desc) > 10, f"Description for {key} is too short"
