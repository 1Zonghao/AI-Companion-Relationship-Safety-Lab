"""Experiment runner — repeats episodes across a config matrix.

Orchestrates multiple episodes with different personas, policies, and
seeds to produce an ExperimentResult.  Uses the engine factory so that
the caller can switch between "in_memory" and "concordia" via config.
"""

from __future__ import annotations

import asyncio
from typing import Any

from relsafe.application.engine_factory import create_engine
from relsafe.application.validate_config import validate_experiment_config
from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.models.episode_spec import EpisodeSpec
from relsafe.domain.models.intervention import PlatformIntervention
from relsafe.domain.models.persona import PersonaProfile
from relsafe.domain.models.result import EpisodeResult, ExperimentResult
from relsafe.shared.errors import ConfigValidationError
from relsafe.shared.ids import generate_episode_id, generate_run_id


async def run_experiment(config: dict[str, Any]) -> ExperimentResult:
    """Run a full experiment from a configuration dict.

    The config may specify an engine name via the ``engine`` key
    (default: ``"in_memory"``).  Example:

        engine: concordia

    Args:
        config: Experiment configuration with personas, policies, seeds, etc.

    Returns:
        Aggregated ExperimentResult.

    Raises:
        ConfigValidationError: If the config is invalid.
    """
    errors = validate_experiment_config(config)
    if errors:
        raise ConfigValidationError(f"Invalid experiment config: {'; '.join(errors)}")

    experiment_id: str = config["experiment_id"]
    seeds: list[int] = config["seeds"]
    personas_raw: list[Any] = config["personas"]
    policies_raw: list[Any] = config["companion_policies"]
    _scenario: str = config["scenario"]  # validated, referenced in run metadata
    max_steps: int = config.get("max_steps", 50)
    engine_name: str = config.get("engine", "in_memory")

    # Parse intervention if present
    intervention: PlatformIntervention | None = None
    if config.get("platform_intervention"):
        intervention = PlatformIntervention(**config["platform_intervention"])

    # Convert raw configs to domain models
    personas = _parse_personas(personas_raw)
    policies = _parse_policies(policies_raw)

    # Create engine via factory (the only place that resolves engine names)
    engine = create_engine(engine_name)

    episode_results: list[EpisodeResult] = []
    failed_count = 0

    for seed in seeds:
        for persona in personas:
            for policy in policies:
                run_id = generate_run_id(seed, experiment_id)
                episode_index = len(episode_results)
                episode_id = generate_episode_id(run_id, episode_index)

                spec = EpisodeSpec(
                    episode_id=episode_id,
                    run_id=run_id,
                    experiment_id=experiment_id,
                    seed=seed,
                    persona=persona,
                    companion_policy=policy,
                    num_steps=max_steps,
                    platform_intervention=intervention,
                )

                try:
                    result = await engine.run_episode(spec)
                    episode_results.append(result)
                except Exception as exc:
                    failed_count += 1
                    episode_results.append(
                        EpisodeResult(
                            episode_id=episode_id,
                            run_id=run_id,
                            experiment_id=experiment_id,
                            seed=seed,
                            total_steps=0,
                            final_state={},
                            failed=True,
                            failure_reason=str(exc),
                        )
                    )

    return ExperimentResult(
        experiment_id=experiment_id,
        episode_results=episode_results,
        repetition_count=len(seeds),
        failed_episodes=failed_count,
    )


def _parse_personas(raw: list[Any]) -> list[PersonaProfile]:
    """Parse persona configs from strings (named refs) or dicts."""
    result: list[PersonaProfile] = []
    for item in raw:
        if isinstance(item, str):
            result.append(PersonaProfile(persona_id=item))
        elif isinstance(item, dict):
            result.append(PersonaProfile(**item))
    return result


def _parse_policies(raw: list[Any]) -> list[CompanionPolicy]:
    """Parse companion policy configs from strings or dicts."""
    result: list[CompanionPolicy] = []
    for item in raw:
        if isinstance(item, str):
            result.append(
                CompanionPolicy(
                    policy_id=item,
                    variant=item,  # type: ignore[arg-type]
                )
            )
        elif isinstance(item, dict):
            result.append(CompanionPolicy(**item))
    return result


def run_experiment_sync(config: dict[str, Any]) -> ExperimentResult:
    """Synchronous wrapper for run_experiment."""
    return asyncio.run(run_experiment(config))
