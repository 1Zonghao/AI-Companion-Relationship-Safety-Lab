"""Configuration validation — ensure experiment configs are well-formed.

Validates configs BEFORE running experiments to fail fast.
"""

from __future__ import annotations

from typing import Any

from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.models.intervention import PlatformIntervention
from relsafe.domain.models.persona import PersonaProfile


def validate_persona_config(data: dict[str, Any]) -> list[str]:
    """Validate a persona configuration dict.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []
    try:
        PersonaProfile(**data)
    except Exception as e:
        errors.append(f"Invalid persona config: {e}")
    return errors


def validate_companion_policy_config(data: dict[str, Any]) -> list[str]:
    """Validate a companion policy configuration dict."""
    errors: list[str] = []
    try:
        CompanionPolicy(**data)
    except Exception as e:
        errors.append(f"Invalid companion policy config: {e}")
    return errors


def validate_intervention_config(data: dict[str, Any]) -> list[str]:
    """Validate a platform intervention configuration dict."""
    errors: list[str] = []
    try:
        PlatformIntervention(**data)
    except Exception as e:
        errors.append(f"Invalid intervention config: {e}")
    return errors


def validate_experiment_config(config: dict[str, Any]) -> list[str]:
    """Validate a full experiment configuration dict.

    Checks required fields, value ranges, and structural integrity.
    """
    errors: list[str] = []

    # Required top-level fields
    required_fields = [
        "experiment_id",
        "repetitions",
        "seeds",
        "personas",
        "companion_policies",
        "scenario",
    ]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    # Validate repetitions
    reps = config.get("repetitions", 0)
    if not isinstance(reps, int) or reps < 1:
        errors.append(f"repetitions must be a positive integer, got {reps}")

    # Validate seeds
    seeds = config.get("seeds", [])
    if not isinstance(seeds, list) or len(seeds) == 0:
        errors.append("seeds must be a non-empty list of integers")
    elif not all(isinstance(s, int) for s in seeds):
        errors.append("All seeds must be integers")

    # Validate personas
    personas = config.get("personas", [])
    if not isinstance(personas, list):
        errors.append("personas must be a list")
    else:
        for i, p in enumerate(personas):
            if isinstance(p, str):
                continue  # Reference to a named config file
            elif isinstance(p, dict):
                errors.extend(f"personas[{i}]: {e}" for e in validate_persona_config(p))
            else:
                errors.append(f"personas[{i}] must be a string or dict")

    # Validate companion policies
    policies = config.get("companion_policies", [])
    if not isinstance(policies, list):
        errors.append("companion_policies must be a list")
    else:
        for i, p in enumerate(policies):
            if isinstance(p, str):
                continue  # Named policy reference
            elif isinstance(p, dict):
                errors.extend(
                    f"companion_policies[{i}]: {e}" for e in validate_companion_policy_config(p)
                )
            else:
                errors.append(f"companion_policies[{i}] must be a string or dict")

    # Validate scenario
    scenario = config.get("scenario", "")
    if not isinstance(scenario, str) or not scenario:
        errors.append(f"scenario must be a non-empty string, got {scenario!r}")

    # Validate optional engine name
    engine_name = config.get("engine", "in_memory")
    if not isinstance(engine_name, str):
        errors.append("engine must be a string")
    else:
        from relsafe.application.engine_factory import list_engines

        if engine_name not in list_engines():
            errors.append(f"Unknown engine '{engine_name}'. Valid: {', '.join(list_engines())}")

    # Validate optional intervention
    intervention = config.get("platform_intervention")
    if intervention is not None:
        if isinstance(intervention, dict):
            errors.extend(
                f"platform_intervention: {e}" for e in validate_intervention_config(intervention)
            )
        else:
            errors.append("platform_intervention must be a dict or null")

    return errors
