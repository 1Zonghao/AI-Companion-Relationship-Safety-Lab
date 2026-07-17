"""Domain-specific exception hierarchy."""

from __future__ import annotations


class RelSafeError(Exception):
    """Base exception for all RelSafe errors."""


class ConfigValidationError(RelSafeError):
    """Raised when experiment or scenario configuration is invalid."""


class SimulationError(RelSafeError):
    """Raised when simulation execution encounters an error."""


class StateTransitionError(RelSafeError):
    """Raised when a state transition rule is violated."""


class EventStoreError(RelSafeError):
    """Raised when event persistence fails."""


class LLMProviderError(RelSafeError):
    """Raised when an LLM provider call fails."""


class MetricEvaluationError(RelSafeError):
    """Raised when a metric cannot be computed."""


class SimulationInitializationError(SimulationError):
    """Raised when a simulation engine cannot be initialized."""


class AgentExecutionError(SimulationError):
    """Raised when an agent fails during execution."""


class EventNormalizationError(SimulationError):
    """Raised when events cannot be normalized from engine output."""


class SimulationDependencyError(RelSafeError):
    """Raised when an optional simulation dependency is not available."""
