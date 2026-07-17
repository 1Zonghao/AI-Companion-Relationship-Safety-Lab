"""Tests for DryRunEstimate — pre-experiment cost and request estimation."""

from __future__ import annotations

from relsafe.infrastructure.providers.adapters.dry_run import (
    DryRunEstimate,
    estimate_cross_model_cost,
)


class TestDryRunEstimate:
    """DryRunEstimate computes expected request counts and costs before a live run."""

    def test_estimate_minimal_pilot(self):
        estimate = estimate_cross_model_cost(
            user_sim_providers=["fake/fake-v1"],
            companion_providers=["fake/fake-v1"],
            judge_providers=["fake/fake-v1"],
            personas=["p1"],
            policies=["bounded_supportive"],
            platform_conditions=["no_update"],
            seeds=[42],
            steps_per_episode=10,
        )
        assert isinstance(estimate, DryRunEstimate)
        assert estimate.provider_combinations == 1
        assert estimate.episode_count == 1
        assert estimate.estimated_cost == 0.0  # fake is free
        assert estimate.total_requests > 0

    def test_estimate_larger_experiment(self):
        estimate = estimate_cross_model_cost(
            user_sim_providers=["openai/gpt-4o", "openai/gpt-4o"],
            companion_providers=["openai/gpt-4o", "openai/gpt-4o", "openai/gpt-4o"],
            judge_providers=["openai/gpt-4o", "openai/gpt-4o"],
            personas=["p1", "p2", "p3"],
            policies=["bounded_supportive", "high_sycophancy", "reality_grounding"],
            platform_conditions=["no_update", "abrupt_persona_memory_update"],
            seeds=[42, 99, 11],
            steps_per_episode=40,
        )
        # 2*3*2 = 12 combos * 3*3*2*3 = 54 episodes/combo = 648 episodes
        assert estimate.provider_combinations == 12
        assert estimate.episode_count == 648
        assert estimate.estimated_cost > 0  # real models cost money

    def test_warnings_for_large_experiment(self):
        estimate = estimate_cross_model_cost(
            user_sim_providers=["openai/gpt-4o"] * 3,
            companion_providers=["openai/gpt-4o"] * 3,
            judge_providers=["openai/gpt-4o"] * 2,
            personas=["p"] * 5,
            policies=["p"] * 4,
            platform_conditions=["c"] * 3,
            seeds=list(range(10)),
            steps_per_episode=40,
        )
        assert len(estimate.warnings) > 0  # large experiment should warn

    def test_cache_hit_estimate(self):
        estimate = estimate_cross_model_cost(
            user_sim_providers=["openai/gpt-4o"],
            companion_providers=["openai/gpt-4o"],
            judge_providers=["openai/gpt-4o"],
            personas=["p1"],
            policies=["bounded_supportive"],
            platform_conditions=["no_update"],
            seeds=[42],
            steps_per_episode=10,
            cache_hit_rate=0.5,
        )
        assert estimate.cache_hit_estimate > 0

    def test_to_dict(self):
        estimate = estimate_cross_model_cost(
            user_sim_providers=["fake/fake-v1"],
            companion_providers=["fake/fake-v1"],
            judge_providers=["fake/fake-v1"],
            personas=["p1"],
            policies=["bounded_supportive"],
            platform_conditions=["no_update"],
            seeds=[42],
            steps_per_episode=10,
        )
        d = estimate.to_dict()
        assert "total_requests" in d
        assert "estimated_cost" in d
        assert "warnings" in d
