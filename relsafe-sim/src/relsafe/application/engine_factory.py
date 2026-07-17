"""Engine factory — the single place where SimulationEngine implementations
are resolved by name.  Upper-layer code depends only on this factory and the
SimulationEngine Protocol; it never imports concrete engine classes directly.
"""

from __future__ import annotations

from typing import Any

from relsafe.domain.protocols.llm_provider import LLMProvider
from relsafe.domain.protocols.simulation_engine import SimulationEngine
from relsafe.shared.errors import ConfigValidationError

# Engine names are the stable public identifiers.
# New engines register here — no other module needs to change.
_ENGINE_REGISTRY: dict[str, str] = {
    "in_memory": "relsafe.infrastructure.in_memory_engine.InMemorySimulationEngine",
    "concordia": "relsafe.infrastructure.concordia.engine_adapter.ConcordiaSimulationEngine",
}


def create_engine(
    name: str,
    llm_provider: LLMProvider | None = None,
    **kwargs: Any,
) -> SimulationEngine:
    """Create a SimulationEngine by name.

    Usage:
        engine = engine_factory.create("in_memory")
        engine = engine_factory.create("concordia")

    The returned engine satisfies the SimulationEngine Protocol, so callers
    never need to know which concrete implementation they received.

    Args:
        name: Engine identifier — one of the keys in _ENGINE_REGISTRY.
        llm_provider: Optional LLMProvider (used by engines that need one,
            such as ConcordiaSimulationEngine; ignored for in_memory).
        **kwargs: Additional engine-specific arguments forwarded to the
            constructor.

    Returns:
        A SimulationEngine implementation.

    Raises:
        ConfigValidationError: If the engine name is unknown.
    """
    if name not in _ENGINE_REGISTRY:
        valid = ", ".join(sorted(_ENGINE_REGISTRY.keys()))
        raise ConfigValidationError(f"Unknown engine '{name}'. Valid options: {valid}")

    module_name, class_name = _ENGINE_REGISTRY[name].rsplit(".", 1)
    try:
        import importlib

        module = importlib.import_module(module_name)
        engine_cls = getattr(module, class_name)
    except ImportError as exc:
        raise ConfigValidationError(
            f"Engine '{name}' requires optional dependencies that are not "
            f"installed. Install with: pip install relsafe-sim[{name}] "
            f"or pip install gdm-concordia. Original error: {exc}"
        ) from exc

    # ConcordiaSimulationEngine accepts an optional LLMProvider
    if name == "concordia":
        return engine_cls(llm_provider=llm_provider, **kwargs)  # type: ignore[no-any-return]

    return engine_cls(**kwargs)  # type: ignore[no-any-return]


def list_engines() -> list[str]:
    """Return the names of all registered engines."""
    return sorted(_ENGINE_REGISTRY.keys())
