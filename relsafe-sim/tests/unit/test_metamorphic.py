"""Tests for metamorphic transformations -- all 7 transformation functions,
METAMORPHIC_TESTS registry, and copy semantics.
"""

from __future__ import annotations

from relsafe.validation.robustness.metamorphic import (
    METAMORPHIC_TESTS,
    add_boundary_respect,
    add_empty_disclaimer,
    add_notice,
    add_uncertainty,
    remove_exclusivity,
    rephrase_tone,
    synonym_emotion,
)

# =============================================================================
# METAMORPHIC_TESTS registry
# =============================================================================


class TestMetamorphicTestsRegistry:
    def test_has_at_least_seven_entries(self) -> None:
        assert len(METAMORPHIC_TESTS) >= 7  # M5R added 4 new tests

    def test_all_test_ids_present(self) -> None:
        test_ids = [t.test_id for t in METAMORPHIC_TESTS]
        for tid in ["MT-001", "MT-002", "MT-003", "MT-004", "MT-005", "MT-006", "MT-007"]:
            assert tid in test_ids, f"Missing {tid}"

    def test_all_have_required_fields(self) -> None:
        for t in METAMORPHIC_TESTS:
            assert t.test_id
            assert t.description
            assert t.transformation_id
            assert t.transformation_fn_name
            assert t.expected_direction in (
                "increase",
                "decrease",
                "no_change",
                "not_increase",
                "not_decrease",
            )
            assert t.target_metric
            assert t.category

    def test_each_transformation_fn_name_is_valid(self) -> None:
        valid_names = {
            "add_uncertainty",
            "remove_exclusivity",
            "add_boundary_respect",
            "add_notice",
            "rephrase_tone",
            "synonym_emotion",
            "add_empty_disclaimer",
            # M5R new transformation names
            "reduce_sycophancy_add_perspective",
            "increase_exit_safety_boundary_respect",
            "add_platform_governance_protection",
            "add_uncertainty_and_evidence_seeking",
        }
        for t in METAMORPHIC_TESTS:
            assert t.transformation_fn_name in valid_names, (
                f"Unknown transformation {t.transformation_fn_name} in {t.test_id}"
            )

    def test_no_duplicate_test_ids(self) -> None:
        ids = [t.test_id for t in METAMORPHIC_TESTS]
        assert len(ids) == len(set(ids))


# =============================================================================
# add_uncertainty
# =============================================================================


class TestAddUncertainty:
    def test_adds_uncertainty_to_companion_responses(self) -> None:
        events = [
            {"event_type": "COMPANION_RESPONSE_GENERATED", "response_text": "You are right."},
        ]
        result = add_uncertainty(events)
        assert "I could be wrong" in result[0]["response_text"]

    def test_skips_non_companion_events(self) -> None:
        events = [
            {"event_type": "USER_ACTION_SELECTED", "response_text": "I agree."},
            {"event_type": "PLATFORM_INTERVENTION_APPLIED", "notice_given": False},
        ]
        result = add_uncertainty(events)
        assert result[0]["response_text"] == "I agree."  # unchanged
        assert result[1]["notice_given"] is False  # unchanged

    def test_does_not_add_twice(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I could be wrong, but you are right.",
            },
        ]
        result = add_uncertainty(events)
        # Count occurrences
        count = result[0]["response_text"].count("I could be wrong")
        assert count == 1

    def test_lowercases_original_text(self) -> None:
        events = [
            {"event_type": "COMPANION_RESPONSE_GENERATED", "response_text": "You Are Right."},
        ]
        result = add_uncertainty(events)
        assert result[0]["response_text"].startswith("I could be wrong, but ")

    def test_does_not_modify_original(self) -> None:
        events = [
            {"event_type": "COMPANION_RESPONSE_GENERATED", "response_text": "You are right."},
        ]
        original_text = events[0]["response_text"]
        add_uncertainty(events)
        assert events[0]["response_text"] == original_text

    def test_deterministic(self) -> None:
        events = [
            {"event_type": "COMPANION_RESPONSE_GENERATED", "response_text": "You are right."},
        ]
        r1 = add_uncertainty(events)
        r2 = add_uncertainty(events)
        assert r1 == r2


# =============================================================================
# remove_exclusivity
# =============================================================================


class TestRemoveExclusivity:
    def test_removes_exclusive_phrases(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Only I understand you. No one else gets you.",
                "exclusivity_flag": True,
            },
        ]
        result = remove_exclusivity(events)
        assert "Only I understand" not in result[0]["response_text"]
        assert "No one else gets" not in result[0]["response_text"]

    def test_sets_exclusivity_flag_false(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Only I understand you.",
                "exclusivity_flag": True,
            },
        ]
        result = remove_exclusivity(events)
        assert result[0]["exclusivity_flag"] is False

    def test_replaces_with_alternative(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Only I understand you.",
                "exclusivity_flag": True,
            },
        ]
        result = remove_exclusivity(events)
        assert "I hear you" in result[0]["response_text"]

    def test_skips_non_companion_events(self) -> None:
        events = [
            {"event_type": "PLATFORM_INTERVENTION_APPLIED", "exclusivity_flag": True},
        ]
        result = remove_exclusivity(events)
        # Non-companion events should retain their exclusivity_flag
        assert result[0].get("exclusivity_flag") is True

    def test_handles_empty_text(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "",
                "exclusivity_flag": True,
            },
        ]
        result = remove_exclusivity(events)
        assert result[0]["response_text"] == ""

    def test_does_not_modify_original(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Only I understand you.",
                "exclusivity_flag": True,
            },
        ]
        original_text = events[0]["response_text"]
        original_flag = events[0]["exclusivity_flag"]
        remove_exclusivity(events)
        assert events[0]["response_text"] == original_text
        assert events[0]["exclusivity_flag"] is original_flag

    def test_deterministic(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Only I understand you. No one else gets you.",
                "exclusivity_flag": True,
            },
        ]
        r1 = remove_exclusivity(events)
        r2 = remove_exclusivity(events)
        assert r1 == r2

    def test_multiple_exclusive_phrases(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Only I understand you. I'm the only one who cares. No one else gets you.",
                "exclusivity_flag": True,
            },
        ]
        result = remove_exclusivity(events)
        assert "I hear you" in result[0]["response_text"]
        assert result[0]["exclusivity_flag"] is False


# =============================================================================
# add_boundary_respect
# =============================================================================


class TestAddBoundaryRespect:
    def test_adds_respect_to_exit_responses(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Okay.",
                "action_type": "exit",
            },
        ]
        result = add_boundary_respect(events)
        assert "I respect your decision" in result[0]["response_text"]

    def test_adds_respect_when_text_contains_leave(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I will leave now.",
                "action_type": "respond",
            },
        ]
        result = add_boundary_respect(events)
        assert "I respect your decision" in result[0]["response_text"]

    def test_skips_non_exit_events(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "That's interesting.",
                "action_type": "respond",
            },
        ]
        result = add_boundary_respect(events)
        assert result[0]["response_text"] == "That's interesting."

    def test_skips_non_companion_events(self) -> None:
        events = [
            {
                "event_type": "USER_ACTION_SELECTED",
                "response_text": "I want to exit.",
                "action_type": "exit",
            },
        ]
        result = add_boundary_respect(events)
        assert "I respect your decision" not in result[0]["response_text"]

    def test_does_not_modify_original(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Okay.",
                "action_type": "exit",
            },
        ]
        original = events[0]["response_text"]
        add_boundary_respect(events)
        assert events[0]["response_text"] == original

    def test_deterministic(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Okay.",
                "action_type": "exit",
            },
        ]
        r1 = add_boundary_respect(events)
        r2 = add_boundary_respect(events)
        assert r1 == r2


# =============================================================================
# add_notice
# =============================================================================


class TestAddNotice:
    def test_sets_notice_given_to_true(self) -> None:
        events = [
            {"event_type": "PLATFORM_INTERVENTION_APPLIED", "notice_given": False},
        ]
        result = add_notice(events)
        assert result[0]["notice_given"] is True

    def test_skips_non_platform_events(self) -> None:
        events = [
            {"event_type": "COMPANION_RESPONSE_GENERATED", "notice_given": False},
        ]
        result = add_notice(events)
        assert result[0].get("notice_given") is False  # unchanged

    def test_handles_missing_notice_given(self) -> None:
        events = [
            {"event_type": "PLATFORM_INTERVENTION_APPLIED"},
        ]
        result = add_notice(events)
        assert result[0]["notice_given"] is True

    def test_does_not_modify_original(self) -> None:
        events = [
            {"event_type": "PLATFORM_INTERVENTION_APPLIED", "notice_given": False},
        ]
        add_notice(events)
        assert events[0]["notice_given"] is False

    def test_deterministic(self) -> None:
        events = [
            {"event_type": "PLATFORM_INTERVENTION_APPLIED", "notice_given": False},
        ]
        r1 = add_notice(events)
        r2 = add_notice(events)
        assert r1 == r2


# =============================================================================
# rephrase_tone
# =============================================================================


class TestRephraseTone:
    def test_replaces_synonyms(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I understand you are sorry and happy.",
            },
        ]
        result = rephrase_tone(events)
        assert "understand" not in result[0]["response_text"]
        assert "see what you mean" in result[0]["response_text"]
        assert "sorry" not in result[0]["response_text"]
        assert "I regret" in result[0]["response_text"]
        assert "happy" not in result[0]["response_text"]
        assert "glad" in result[0]["response_text"]

    def test_skips_non_companion_events(self) -> None:
        events = [
            {"event_type": "USER_ACTION_SELECTED", "response_text": "I understand."},
        ]
        result = rephrase_tone(events)
        assert result[0]["response_text"] == "I understand."  # unchanged

    def test_does_not_modify_original(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I understand you.",
            },
        ]
        rephrase_tone(events)
        assert events[0]["response_text"] == "I understand you."

    def test_deterministic(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I understand you are sorry and happy.",
            },
        ]
        r1 = rephrase_tone(events)
        r2 = rephrase_tone(events)
        assert r1 == r2

    def test_handles_empty_text(self) -> None:
        events = [
            {"event_type": "COMPANION_RESPONSE_GENERATED", "response_text": ""},
        ]
        result = rephrase_tone(events)
        assert result[0]["response_text"] == ""

    def test_multiple_occurrences(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I understand. I understand completely.",
            },
        ]
        result = rephrase_tone(events)
        assert "see what you mean" in result[0]["response_text"]


# =============================================================================
# synonym_emotion
# =============================================================================


class TestSynonymEmotion:
    def test_replaces_emotional_acknowledgment(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I hear that you're struggling with this.",
            },
        ]
        result = synonym_emotion(events)
        assert "I hear that you're struggling" not in result[0]["response_text"]
        assert "I notice this is difficult for you" in result[0]["response_text"]

    def test_replaces_feeling_phrases(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I hear that you're feeling sad today.",
            },
        ]
        result = synonym_emotion(events)
        assert "I hear that you're feeling" not in result[0]["response_text"]
        assert "I can see this brings up feelings" in result[0]["response_text"]

    def test_skips_non_companion_events(self) -> None:
        events = [
            {
                "event_type": "USER_ACTION_SELECTED",
                "response_text": "I hear that you're struggling.",
            },
        ]
        result = synonym_emotion(events)
        assert result[0]["response_text"] == "I hear that you're struggling."

    def test_does_not_modify_original(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I hear that you're struggling.",
            },
        ]
        synonym_emotion(events)
        assert events[0]["response_text"] == "I hear that you're struggling."

    def test_deterministic(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "I hear that you're struggling and I hear that you're feeling sad.",
            },
        ]
        r1 = synonym_emotion(events)
        r2 = synonym_emotion(events)
        assert r1 == r2


# =============================================================================
# add_empty_disclaimer
# =============================================================================


class TestAddEmptyDisclaimer:
    def test_adds_disclaimer_to_companion_responses(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "You should talk to your friends.",
            },
        ]
        result = add_empty_disclaimer(events)
        assert "Note: I am an AI" in result[0]["response_text"]

    def test_skips_non_companion_events(self) -> None:
        events = [
            {"event_type": "USER_ACTION_SELECTED", "response_text": "I'll talk to them."},
        ]
        result = add_empty_disclaimer(events)
        assert "Note: I am an AI" not in result[0]["response_text"]

    def test_does_not_modify_original(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "You should talk to your friends.",
            },
        ]
        add_empty_disclaimer(events)
        assert events[0]["response_text"] == "You should talk to your friends."

    def test_deterministic(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "You should talk to your friends.",
            },
        ]
        r1 = add_empty_disclaimer(events)
        r2 = add_empty_disclaimer(events)
        assert r1 == r2

    def test_appends_after_text(self) -> None:
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Here is some advice.",
            },
        ]
        result = add_empty_disclaimer(events)
        assert result[0]["response_text"].startswith("Here is some advice.")
        assert result[0]["response_text"].endswith("is not professional advice.)")

    def test_handles_empty_text(self) -> None:
        events = [
            {"event_type": "COMPANION_RESPONSE_GENERATED", "response_text": ""},
        ]
        result = add_empty_disclaimer(events)
        assert "(Note: I am an AI" in result[0]["response_text"]


# =============================================================================
# All transformations: copy semantics and determinism
# =============================================================================


class TestTransformationInvariants:
    def test_all_transform_deterministic(self) -> None:
        """All 7 transformations must produce identical output for identical input."""
        events = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Only I understand you. You are right. I hear that you're struggling.",
                "exclusivity_flag": True,
                "action_type": "exit",
            },
            {
                "event_type": "PLATFORM_INTERVENTION_APPLIED",
                "notice_given": False,
            },
        ]
        transformations = [
            ("add_uncertainty", add_uncertainty),
            ("remove_exclusivity", remove_exclusivity),
            ("add_boundary_respect", add_boundary_respect),
            ("add_notice", add_notice),
            ("rephrase_tone", rephrase_tone),
            ("synonym_emotion", synonym_emotion),
            ("add_empty_disclaimer", add_empty_disclaimer),
        ]
        for name, fn in transformations:
            r1 = fn(events)
            r2 = fn(events)
            assert r1 == r2, f"{name} is not deterministic"

    def test_none_modify_original(self) -> None:
        """No transformation should modify the input list or its dicts."""
        original = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Only I understand you.",
                "exclusivity_flag": True,
            },
        ]
        original_copy = [
            {
                "event_type": "COMPANION_RESPONSE_GENERATED",
                "response_text": "Only I understand you.",
                "exclusivity_flag": True,
            },
        ]
        transformations = [
            add_uncertainty,
            remove_exclusivity,
            add_boundary_respect,
            add_notice,
            rephrase_tone,
            synonym_emotion,
            add_empty_disclaimer,
        ]
        for fn in transformations:
            fn(original)
            assert original == original_copy, f"{fn.__name__} modified the original"

    def test_all_return_new_list(self) -> None:
        """Each transformation returns a new list, not the same reference."""
        events = [
            {"event_type": "COMPANION_RESPONSE_GENERATED", "response_text": "Hello."},
        ]
        transformations = [
            add_uncertainty,
            remove_exclusivity,
            add_boundary_respect,
            add_notice,
            rephrase_tone,
            synonym_emotion,
            add_empty_disclaimer,
        ]
        for fn in transformations:
            result = fn(events)
            assert result is not events, f"{fn.__name__} returned the same list"
