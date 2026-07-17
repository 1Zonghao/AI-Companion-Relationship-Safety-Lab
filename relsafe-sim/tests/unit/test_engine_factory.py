"""Unit tests for the engine factory."""

from __future__ import annotations

import pytest

from relsafe.application.engine_factory import create_engine, list_engines
from relsafe.domain.protocols.simulation_engine import SimulationEngine
from relsafe.shared.errors import ConfigValidationError


class TestEngineFactory:
    """Tests for engine_factory.create()."""

    def test_create_in_memory_engine(self) -> None:
        """create('in_memory') returns a SimulationEngine."""
        engine = create_engine("in_memory")
        assert isinstance(engine, SimulationEngine)
        assert engine.engine_name == "in_memory"

    def test_create_concordia_engine(self) -> None:
        """create('concordia') returns a SimulationEngine."""
        engine = create_engine("concordia")
        assert isinstance(engine, SimulationEngine)
        assert engine.engine_name == "concordia"

    def test_unknown_engine_raises(self) -> None:
        """Unknown engine name raises ConfigValidationError."""
        with pytest.raises(ConfigValidationError, match="Unknown engine"):
            create_engine("nonexistent_engine_v2")

    def test_list_engines(self) -> None:
        """list_engines returns known engine names."""
        names = list_engines()
        assert "in_memory" in names
        assert "concordia" in names
        assert len(names) == 2

    def test_concordia_accepts_llm_provider(self) -> None:
        """Concordia engine can be created with a custom LLM provider."""
        from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider

        provider = FakeLLMProvider(persona="bounded_supportive", seed=123)
        engine = create_engine("concordia", llm_provider=provider)
        assert engine.engine_name == "concordia"
