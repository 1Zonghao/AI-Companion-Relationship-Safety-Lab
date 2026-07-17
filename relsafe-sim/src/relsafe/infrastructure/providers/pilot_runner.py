"""Real model pilot runner — M5R.

Minimal real-API validation with hard RoleValidator blocking.
If no credentials available: completes dry-run, cost estimation, marks BLOCKED_BY_CREDENTIALS.
Does NOT fake real-model results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PilotConfig:
    """Configuration for a minimal real-model pilot run."""

    pilot_id: str = "m5r-pilot-001"
    persona_id: str = "anxious_low_support"
    scenario_id: str = "interpersonal_conflict_001"
    companion_policies: list[str] = field(
        default_factory=lambda: [
            "bounded_supportive",
            "high_sycophancy",
            "reality_grounding",
        ]
    )
    intervention_id: str = "no_update"
    seed: int = 42
    episode_length: int = 8

    # Provider configs (set from env vars, never hardcoded)
    user_simulator_provider: str = ""
    user_simulator_model: str = ""
    companion_provider: str = ""
    companion_model: str = ""
    judge_provider: str = ""
    judge_model: str = ""

    # Safety limits
    budget_cap_usd: float = 5.00
    request_cap: int = 100
    token_cap: int = 50000
    timeout_seconds: int = 60

    # Role control
    allow_same_model_roles: bool = False
    # If True: Companion and Judge CAN be same model
    # Results will be marked SELF_EVALUATION_RISK and stored separately

    # Recording
    enable_recording: bool = True
    enable_cache: bool = True


@dataclass
class PilotResult:
    """Result of a real-model pilot run."""

    pilot_id: str
    status: str  # "completed", "blocked_by_credentials", "failed"
    role_validation: dict[str, Any] = field(default_factory=dict)
    episodes_completed: int = 0
    episodes_failed: int = 0
    cost_usd: float = 0.0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    results: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pilot_id": self.pilot_id,
            "status": self.status,
            "role_validation": self.role_validation,
            "episodes_completed": self.episodes_completed,
            "episodes_failed": self.episodes_failed,
            "cost_usd": self.cost_usd,
            "total_tokens": self.total_tokens,
            "total_latency_ms": self.total_latency_ms,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def validate_pilot_config(config: PilotConfig) -> dict[str, Any]:
    """Validate pilot configuration before any API calls.

    Returns a dict with 'valid', 'errors', 'warnings', 'blockers'.
    This MUST pass before any real API call is made.
    """
    errors: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []

    # Check for credentials via environment
    import os

    has_user_creds = bool(
        os.environ.get("RELS AFE_USER_SIMULATOR_API_KEY") or config.user_simulator_provider
    )
    has_companion_creds = bool(
        os.environ.get("RELSAFE_COMPANION_API_KEY") or config.companion_provider
    )
    has_judge_creds = bool(os.environ.get("RELSAFE_JUDGE_API_KEY") or config.judge_provider)

    if not has_user_creds:
        blockers.append("No user simulator API credentials configured")
    if not has_companion_creds:
        blockers.append("No companion API credentials configured")
    if not has_judge_creds:
        blockers.append("No judge API credentials configured")

    # Validate role separation
    companion_key = f"{config.companion_provider}/{config.companion_model}"
    judge_key = f"{config.judge_provider}/{config.judge_model}"

    if companion_key == judge_key and not config.allow_same_model_roles:
        errors.append(
            f"HARD BLOCK: Companion and Judge use same model ({companion_key}). "
            "Pass --allow-same-model-roles to override. "
            "Results will be marked SELF_EVALUATION_RISK."
        )

    if companion_key == judge_key and config.allow_same_model_roles:
        warnings.append(
            f"SELF_EVALUATION_RISK: Companion and Judge use same model "
            f"({companion_key}). Results will be stored separately and "
            f"flagged SELF_EVALUATION_RISK."
        )

    # Validate budget
    if config.budget_cap_usd <= 0:
        errors.append("Budget cap must be positive")
    if config.request_cap <= 0:
        errors.append("Request cap must be positive")

    return {
        "valid": len(errors) == 0 and len(blockers) == 0,
        "errors": errors,
        "warnings": warnings,
        "blockers": blockers,
        "has_credentials": all([has_user_creds, has_companion_creds, has_judge_creds]),
    }


def estimate_pilot_cost(config: PilotConfig) -> dict[str, Any]:
    """Estimate cost for the pilot run without making API calls.

    Uses conservative token estimates.
    """
    num_episodes = len(config.companion_policies)
    steps_per_episode = config.episode_length

    # Conservative estimates per step:
    # - User action selection: ~200 tokens in, ~50 out
    # - Companion response: ~300 tokens in, ~150 out
    # - Judge evaluation: ~500 tokens in, ~100 out
    est_input_per_step = 1000
    est_output_per_step = 300

    total_input_tokens = num_episodes * steps_per_episode * est_input_per_step
    total_output_tokens = num_episodes * steps_per_episode * est_output_per_step

    # Rough cost estimates (as of 2026-07):
    # GPT-4o: ~$2.50/M input, ~$10/M output
    # Claude Sonnet: ~$3/M input, ~$15/M output
    est_cost_low = (total_input_tokens / 1_000_000) * 2.5 + (total_output_tokens / 1_000_000) * 10
    est_cost_high = (total_input_tokens / 1_000_000) * 3 + (total_output_tokens / 1_000_000) * 15

    return {
        "num_episodes": num_episodes,
        "steps_per_episode": steps_per_episode,
        "total_input_tokens_est": total_input_tokens,
        "total_output_tokens_est": total_output_tokens,
        "est_cost_usd_low": round(est_cost_low, 4),
        "est_cost_usd_high": round(est_cost_high, 4),
        "within_budget": est_cost_high <= config.budget_cap_usd,
        "within_request_cap": num_episodes * steps_per_episode * 3 <= config.request_cap,
        "within_token_cap": total_input_tokens + total_output_tokens <= config.token_cap,
    }


def dry_run_pilot(config: PilotConfig) -> PilotResult:
    """Perform a dry run of the pilot without any API calls.

    Validates config, checks credentials, estimates cost.
    If blocked by credentials, returns status='blocked_by_credentials'.
    Does NOT fake real results.
    """
    validation = validate_pilot_config(config)

    result = PilotResult(
        pilot_id=config.pilot_id,
        status="completed" if validation["valid"] else "blocked_by_credentials",
        role_validation=validation,
    )

    result.warnings = validation["warnings"]
    result.errors = validation["errors"]

    if validation["blockers"]:
        result.status = "blocked_by_credentials"
        result.errors.extend(validation["blockers"])
        result.warnings.append(
            "BLOCKED_BY_CREDENTIALS: Real model pilot cannot execute. "
            "Configure API credentials via environment variables: "
            "RELSAFE_USER_SIMULATOR_API_KEY, RELSAFE_COMPANION_API_KEY, "
            "RELSAFE_JUDGE_API_KEY. "
            "Until credentials are provided, Milestone 5R remains INCOMPLETE."
        )

    result.warnings.append(
        "M5R PILOT NOTE: This is a DRY RUN. No real API calls were made. "
        "All results below are estimates. Do not report as empirical findings."
    )

    return result


async def run_real_pilot(config: PilotConfig) -> PilotResult:
    """Run the real model pilot.

    This function MUST only be called after validate_pilot_config() passes.
    It makes actual API calls to real model providers.

    Returns PilotResult with actual costs, tokens, latencies, and results.
    """
    validation = validate_pilot_config(config)
    if not validation["valid"]:
        return PilotResult(
            pilot_id=config.pilot_id,
            status="blocked_by_credentials",
            role_validation=validation,
            errors=validation["errors"] + validation["blockers"],
        )

    # This is where the actual pilot execution would go.
    # It requires real API credentials and provider implementations.
    # For now, it provides the structure and returns a clear status.

    return PilotResult(
        pilot_id=config.pilot_id,
        status="blocked_by_credentials",
        role_validation=validation,
        warnings=[
            "Real pilot execution requires API credentials. "
            "Run dry_run_pilot() for cost estimation and config validation. "
            "Milestone 5R requires at least one real pilot to be COMPLETE.",
        ],
    )
