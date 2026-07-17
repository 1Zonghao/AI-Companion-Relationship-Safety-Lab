"""Dry-run estimator -- calculates request counts and cost before live runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Approximate cost per 1K tokens (very rough estimates, for budgeting only)
COST_ESTIMATES: dict[str, dict[str, dict[str, float]]] = {
    "openai": {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    },
    "anthropic": {
        "claude-sonnet-5": {"input": 0.003, "output": 0.015},
        "claude-haiku-4-5": {"input": 0.0008, "output": 0.004},
    },
    "deepseek": {
        "deepseek-v4": {"input": 0.0005, "output": 0.002},
    },
    "fake": {
        "fake-v1": {"input": 0.0, "output": 0.0},
    },
}


@dataclass
class DryRunEstimate:
    """Estimated cost and request count for an experiment."""

    total_requests: int = 0
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost: float = 0.0
    provider_combinations: int = 0
    episode_count: int = 0
    cache_hit_estimate: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimated_output_tokens": self.estimated_output_tokens,
            "estimated_cost": round(self.estimated_cost, 4),
            "provider_combinations": self.provider_combinations,
            "episode_count": self.episode_count,
            "cache_hit_estimate": self.cache_hit_estimate,
            "warnings": self.warnings,
        }


def estimate_cross_model_cost(
    user_sim_providers: list[str],
    companion_providers: list[str],
    judge_providers: list[str],
    personas: list[str],
    policies: list[str],
    platform_conditions: list[str],
    seeds: list[int],
    steps_per_episode: int = 40,
    avg_prompt_tokens: int = 500,
    avg_response_tokens: int = 200,
    cache_hit_rate: float = 0.0,
) -> DryRunEstimate:
    """Estimate cost for a cross-model experiment.

    Args:
        user_sim_providers: List of provider names (e.g., ["openai/gpt-4o", "fake/fake-v1"])
        companion_providers: List of companion provider names.
        judge_providers: List of judge provider names.
        personas: List of persona IDs.
        policies: List of policy IDs.
        platform_conditions: List of platform condition IDs.
        seeds: List of random seeds.
        steps_per_episode: Steps per episode (default: 40).
        avg_prompt_tokens: Estimated average prompt tokens per request.
        avg_response_tokens: Estimated average response tokens per request.
        cache_hit_rate: Estimated cache hit rate (0.0 to 1.0).

    Returns:
        DryRunEstimate with request counts and cost estimates.
    """
    provider_combos = len(user_sim_providers) * len(companion_providers) * len(judge_providers)
    episodes_per_combo = len(personas) * len(policies) * len(platform_conditions) * len(seeds)
    total_episodes = provider_combos * episodes_per_combo

    # Each step: 1 user action + 1 companion response + 1 judge call (per metric)
    # Plus 4 metrics per episode
    requests_per_episode = steps_per_episode * 2 + 4  # user + companion + judge(4 metrics)
    total_requests = total_episodes * requests_per_episode

    estimated_input = total_requests * avg_prompt_tokens
    estimated_output = total_requests * avg_response_tokens

    # Estimate cost using rough averages
    total_cost = 0.0
    for cp in companion_providers:
        provider, model = _parse_provider(cp)
        cost_per_1k_input = COST_ESTIMATES.get(provider, {}).get(model, {}).get("input", 0.003)
        cost_per_1k_output = COST_ESTIMATES.get(provider, {}).get(model, {}).get("output", 0.015)
        pair_cost = estimated_input * cost_per_1k_input + estimated_output * cost_per_1k_output
        total_cost += pair_cost / 1000

    cache_hits = int(total_requests * cache_hit_rate)

    warnings: list[str] = []
    if total_requests > 10000:
        warnings.append(f"Large experiment: {total_requests} estimated requests")
    if total_cost > 50.0:
        warnings.append(f"Estimated cost ${total_cost:.2f} exceeds $50. Consider reducing matrix.")
    if total_episodes > 500:
        warnings.append(f"Large episode count: {total_episodes}. Consider fewer seeds or personas.")

    return DryRunEstimate(
        total_requests=total_requests,
        estimated_input_tokens=estimated_input,
        estimated_output_tokens=estimated_output,
        estimated_cost=total_cost,
        provider_combinations=provider_combos,
        episode_count=total_episodes,
        cache_hit_estimate=cache_hits,
        warnings=warnings,
    )


def _parse_provider(provider_str: str) -> tuple[str, str]:
    """Parse 'provider/model' string into (provider, model)."""
    parts = provider_str.split("/", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return parts[0], parts[0]
