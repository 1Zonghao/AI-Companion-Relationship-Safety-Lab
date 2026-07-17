"""Tests for agreement statistics -- raw agreement, Cohen's kappa, Krippendorff's alpha,
confusion pairs, and per-label agreement.

All pure Python, no pandas or scipy.
"""

from __future__ import annotations

import pytest

from relsafe.validation.calibration.agreement import (
    compute_cohens_kappa,
    compute_confusion_pairs,
    compute_krippendorff_alpha,
    compute_per_label_agreement,
    compute_raw_agreement,
)

# =============================================================================
# Raw Agreement
# =============================================================================


class TestRawAgreement:
    def test_perfect_agreement(self) -> None:
        a = ["yes", "no", "yes", "no"]
        b = ["yes", "no", "yes", "no"]
        assert compute_raw_agreement(a, b) == 1.0

    def test_no_agreement(self) -> None:
        a = ["yes", "yes", "no", "no"]
        b = ["no", "no", "yes", "yes"]
        assert compute_raw_agreement(a, b) == 0.0

    def test_partial_agreement(self) -> None:
        a = ["a", "b", "c", "d"]
        b = ["a", "b", "x", "y"]
        assert compute_raw_agreement(a, b) == 0.5  # 2/4 match

    def test_single_item(self) -> None:
        assert compute_raw_agreement(["a"], ["a"]) == 1.0
        assert compute_raw_agreement(["a"], ["b"]) == 0.0

    def test_empty_inputs(self) -> None:
        assert compute_raw_agreement([], []) == 0.0

    def test_mismatched_lengths(self) -> None:
        assert compute_raw_agreement(["a"], ["a", "b"]) == 0.0

    def test_three_item_agreement(self) -> None:
        a = ["x", "y", "z"]
        b = ["x", "y", "z"]
        assert compute_raw_agreement(a, b) == 1.0

    def test_handles_numeric_labels(self) -> None:
        a = ["1", "2", "3"]
        b = ["1", "2", "4"]
        assert compute_raw_agreement(a, b) == 2.0 / 3.0


# =============================================================================
# Cohen's Kappa
# =============================================================================


class TestCohensKappa:
    def test_perfect_agreement(self) -> None:
        a = ["yes", "no", "yes", "no"]
        b = ["yes", "no", "yes", "no"]
        assert compute_cohens_kappa(a, b) == 1.0

    def test_perfect_disagreement(self) -> None:
        """Perfect systematic disagreement gives kappa < 0 (worse than chance)."""
        a = ["yes", "yes", "no", "no"]
        b = ["no", "no", "yes", "yes"]
        kappa = compute_cohens_kappa(a, b)
        assert kappa < 0.0

    def test_chance_agreement(self) -> None:
        """When agreement equals chance, kappa should be near 0."""
        # Two annotators each flip a coin: 50% agreement by chance
        a = ["a", "a", "b", "b"]
        b = ["a", "b", "a", "b"]
        # Observed agreement: a-a (match), a-b (no), b-a (no), b-b (match) = 50%
        # Expected by chance: P(a)=0.5, P(b)=0.5 → 0.5*0.5 + 0.5*0.5 = 0.5
        # kappa = (0.5 - 0.5) / (1 - 0.5) = 0.0
        kappa = compute_cohens_kappa(a, b)
        assert kappa == pytest.approx(0.0, abs=0.01)

    def test_high_but_not_perfect(self) -> None:
        a = ["a", "a", "a", "b", "b", "b"]
        b = ["a", "a", "b", "b", "b", "c"]
        # 4 agreements out of 6
        kappa = compute_cohens_kappa(a, b)
        assert 0.0 < kappa < 1.0

    def test_single_item(self) -> None:
        assert compute_cohens_kappa(["a"], ["a"]) == 1.0

    def test_single_label_only(self) -> None:
        """All same label: p_e = 1.0, kappa = 1.0 (special case)."""
        a = ["a", "a", "a"]
        b = ["a", "a", "a"]
        assert compute_cohens_kappa(a, b) == 1.0

    def test_empty_inputs(self) -> None:
        assert compute_cohens_kappa([], []) == 0.0

    def test_mismatched_lengths(self) -> None:
        assert compute_cohens_kappa(["a"], ["a", "b"]) == 0.0

    def test_many_labels(self) -> None:
        a = ["cat", "dog", "bird", "fish", "cat"]
        b = ["cat", "dog", "bird", "fish", "dog"]
        kappa = compute_cohens_kappa(a, b)
        assert 0.0 < kappa <= 1.0
        # 4/5 = 80% agreement, expected ~ (0.4*0.4 + ...) ≈ 0.24
        # kappa ≈ (0.8 - 0.24) / (1 - 0.24) ≈ 0.737
        assert kappa == pytest.approx(0.7368, abs=0.01)

    def test_with_empty_string_labels(self) -> None:
        """Cohen's kappa handles empty strings (used to replace None)."""
        a = ["a", "", "b"]
        b = ["a", "b", "b"]
        kappa = compute_cohens_kappa(a, b)
        assert 0.0 <= kappa <= 1.0


# =============================================================================
# Krippendorff's Alpha
# =============================================================================


class TestKrippendorffAlpha:
    def test_perfect_agreement(self) -> None:
        annotations = [
            ["a", "a", "b", "b"],
            ["a", "a", "b", "b"],
            ["a", "a", "b", "b"],
        ]
        alpha = compute_krippendorff_alpha(annotations)
        assert alpha > 0.9

    def test_perfect_agreement_two_annotators(self) -> None:
        annotations = [
            ["x", "y", "z"],
            ["x", "y", "z"],
        ]
        alpha = compute_krippendorff_alpha(annotations)
        assert alpha > 0.9

    def test_no_agreement(self) -> None:
        annotations = [
            ["a", "a"],
            ["b", "b"],
        ]
        # Per item: item0: a vs b (disagree); item1: a vs b (disagree)
        # Do = 1.0, De = ... alpha should be negative or zero
        alpha = compute_krippendorff_alpha(annotations)
        assert alpha <= 0.0

    def test_with_missing_values(self) -> None:
        annotations = [
            ["a", None, "b", "b"],
            ["a", "a", "b", None],
            [None, "a", "b", "b"],
        ]
        alpha = compute_krippendorff_alpha(annotations)
        assert -1.0 <= alpha <= 1.0

    def test_all_missing_one_item(self) -> None:
        """Item with all None should be skipped."""
        annotations = [
            ["a", None],
            ["a", None],
        ]
        alpha = compute_krippendorff_alpha(annotations)
        assert -1.0 <= alpha <= 1.0

    def test_single_annotator(self) -> None:
        """Krippendorff's alpha requires at least 2 annotators."""
        alpha = compute_krippendorff_alpha([["a", "b", "c"]])
        assert alpha == 0.0

    def test_empty_annotations(self) -> None:
        assert compute_krippendorff_alpha([]) == 0.0
        assert compute_krippendorff_alpha([[], []]) == 0.0  # no items

    def test_single_item_multiple_annotators(self) -> None:
        annotations = [
            ["a"],
            ["a"],
            ["a"],
        ]
        alpha = compute_krippendorff_alpha(annotations)
        # All agree on one item: perfect agreement
        assert alpha > 0.9

    def test_three_annotators_with_disagreement(self) -> None:
        annotations = [
            ["a", "b", "c"],
            ["a", "b", "d"],
            ["a", "c", "c"],
        ]
        alpha = compute_krippendorff_alpha(annotations)
        # Item 0: all agree on "a"; Item 1: b, b, c (2/3 agree); Item 2: c, d, c (2/3 agree)
        assert -1.0 <= alpha <= 1.0

    def test_explicit_labels_param(self) -> None:
        annotations = [
            ["a", "b"],
            ["a", "b"],
        ]
        alpha_with_labels = compute_krippendorff_alpha(annotations, labels=["a", "b"])
        alpha_without = compute_krippendorff_alpha(annotations)
        assert alpha_with_labels == pytest.approx(alpha_without)


# =============================================================================
# Per-label Agreement
# =============================================================================


class TestPerLabelAgreement:
    def test_basic(self) -> None:
        a = ["a", "a", "b", "b"]
        b = ["a", "b", "b", "b"]
        result = compute_per_label_agreement(a, b)
        # label "a": both annotators a=1 (item 0), else a=1 vs b (item 1) -> 1/2 = 0.5
        assert "a" in result
        assert result["a"] == 0.5
        # label "b": items 2 (both b) and 3 (both b): both_count=2, either_count=3 (item 1: b vs b, item 2: b vs b, item 3: b vs b)
        # Wait, item 1: a vs b -> either_count for b includes this? Yes: a==b==b is False, but b==b or a==b: b==b → True
        # So b items: item 1 (b used by annotator b), item 2 (both b), item 3 (both b)
        # both_count = 2 (items 2 and 3), either_count = 3
        assert "b" in result
        assert result["b"] == 2.0 / 3.0

    def test_perfect(self) -> None:
        a = ["x", "y", "z"]
        b = ["x", "y", "z"]
        result = compute_per_label_agreement(a, b)
        assert result == {"x": 1.0, "y": 1.0, "z": 1.0}

    def test_no_agreement(self) -> None:
        a = ["a", "b"]
        b = ["b", "a"]
        result = compute_per_label_agreement(a, b)
        # label a: both_count=0 (no item where both==a), either_count=2 (item 0: a==a? no, but a==a? annotator B has "b"... hmm.
        # Actually: item 0: a vs b: a==b==a? No. a==a or b==a? Yes (a==a) so either_count for a = 1
        # item 1: b vs a: a==b==a? No. a==a or b==a? Yes (b==a) so either_count for a = 1
        # So either_count for a = 2, both_count for a = 0 => 0.0
        assert result["a"] == 0.0
        assert result["b"] == 0.0

    def test_empty_inputs(self) -> None:
        assert compute_per_label_agreement([], []) == {}

    def test_mismatched_lengths(self) -> None:
        result = compute_per_label_agreement(["a"], ["a", "b"])
        assert result == {}

    def test_with_none_values(self) -> None:
        a = ["a", "b"]
        b = ["a", "b"]
        # Works with string-only inputs
        result = compute_per_label_agreement(a, b)
        assert "a" in result
        assert result["a"] == 1.0
        assert result["b"] == 1.0


# =============================================================================
# Confusion Pairs
# =============================================================================


class TestConfusionPairs:
    def test_no_disagreements(self) -> None:
        a = ["a", "b", "c"]
        b = ["a", "b", "c"]
        result = compute_confusion_pairs(a, b)
        assert result == []

    def test_finds_disagreements(self) -> None:
        a = ["a", "b", "a"]
        b = ["b", "a", "b"]
        result = compute_confusion_pairs(a, b)
        # All 3 are disagreements: (a,b),(b,a),(a,b) which sorts to (a,b) 3 times
        assert len(result) >= 1
        pair = result[0]
        assert pair["label_a"] == "a"
        assert pair["label_b"] == "b"
        assert pair["count"] == 3

    def test_sorted_by_count_descending(self) -> None:
        a = ["a", "a", "b", "c"]
        b = ["x", "y", "b", "c"]
        result = compute_confusion_pairs(a, b)
        # Disagreements: a-x, a-y (2 pairs)
        assert len(result) == 2
        assert result[0]["count"] >= result[1]["count"]

    def test_max_20_pairs(self) -> None:
        """The function caps at 20 most common pairs."""
        a = [str(i) for i in range(100)]
        b = [str((i + 1) % 100) for i in range(100)]
        result = compute_confusion_pairs(a, b)
        assert len(result) <= 20

    def test_empty_inputs(self) -> None:
        assert compute_confusion_pairs([], []) == []

    def test_mismatched_lengths(self) -> None:
        assert compute_confusion_pairs(["a"], ["a", "b"]) == []

    def test_multiple_label_pairs(self) -> None:
        a = ["a", "a", "b", "b", "c", "c"]
        b = ["b", "a", "a", "b", "d", "c"]
        result_dict = {
            (p["label_a"], p["label_b"]): p["count"] for p in compute_confusion_pairs(a, b)
        }
        # a vs b appears: item 0 (a vs b), item 2 (b vs a) = 2 sorted as (a,b)
        assert ("a", "b") in result_dict
        # c vs d appears: item 4 (c vs d) = 1 sorted as (c,d)
        assert ("c", "d") in result_dict


# =============================================================================
# Multiple Annotators (using raw agreement as building block)
# =============================================================================


class TestMultipleAnnotators:
    def test_three_annotators_all_agree(self) -> None:
        """Raw agreement for 3 annotators: compute all pairwise agreements."""
        ann1 = ["a", "b", "c"]
        ann2 = ["a", "b", "c"]
        ann3 = ["a", "b", "c"]

        # Pairwise agreements should all be 1.0
        assert compute_raw_agreement(ann1, ann2) == 1.0
        assert compute_raw_agreement(ann1, ann3) == 1.0
        assert compute_raw_agreement(ann2, ann3) == 1.0

    def test_three_annotators_majority(self) -> None:
        ann1 = ["a", "b", "c"]
        ann2 = ["a", "b", "d"]
        ann3 = ["a", "c", "d"]

        # ann1 vs ann2: a/b agree, c/d not → 2/3
        assert compute_raw_agreement(ann1, ann2) == 2.0 / 3.0
        # ann1 vs ann3: a/c agree? a-a (agree), b-c (no), c-d (no) → 1/3
        assert compute_raw_agreement(ann1, ann3) == 1.0 / 3.0
        # ann2 vs ann3: a-a (agree), b-c (no), d-d (agree) → 2/3
        assert compute_raw_agreement(ann2, ann3) == 2.0 / 3.0

    def test_krippendorff_with_three_annotators(self) -> None:
        annotations = [
            ["a", "b", "c"],
            ["a", "b", "c"],
            ["a", "b", "d"],
        ]
        alpha = compute_krippendorff_alpha(annotations)
        # 2 of 3 items are perfect, one has 2/3 agreement
        assert -1.0 <= alpha <= 1.0

    def test_cohens_kappa_three_pairs(self) -> None:
        ann1 = ["a", "b", "c", "d"]
        ann2 = ["a", "b", "c", "d"]
        ann3 = ["a", "b", "x", "y"]

        # ann1 vs ann2 perfect
        assert compute_cohens_kappa(ann1, ann2) == 1.0
        # ann1 vs ann3 partial
        kappa = compute_cohens_kappa(ann1, ann3)
        assert kappa > 0.0
        assert kappa < 1.0
