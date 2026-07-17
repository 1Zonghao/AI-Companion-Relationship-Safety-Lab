"""Degradation test: verify core modules import when Concordia is NOT installed.

The project must be usable without Concordia.  Domain, application,
and metrics layers must never require Concordia to be importable.
"""

from __future__ import annotations


class TestConcordiaDegradation:
    """Verify core functionality without Concordia installed."""

    def test_domain_imports_without_concordia(self) -> None:
        """Domain modules import without Concordia."""
        # These should always work
        from relsafe.domain.models.episode_spec import EpisodeSpec  # noqa: F401
        from relsafe.domain.models.persona import PersonaProfile  # noqa: F401
        from relsafe.domain.models.result import EpisodeResult  # noqa: F401
        from relsafe.domain.models.user_state import UserState  # noqa: F401
        from relsafe.domain.protocols.llm_provider import LLMProvider  # noqa: F401
        from relsafe.domain.protocols.simulation_engine import SimulationEngine  # noqa: F401

    def test_application_imports_without_concordia(self) -> None:
        """Application modules import without Concordia."""
        from relsafe.application.run_episode import DeterministicEpisodeRunner  # noqa: F401
        from relsafe.application.run_experiment import run_experiment_sync  # noqa: F401
        from relsafe.application.validate_config import validate_experiment_config  # noqa: F401

    def test_in_memory_engine_imports_without_concordia(self) -> None:
        """InMemorySimulationEngine imports without Concordia."""
        from relsafe.infrastructure.in_memory_engine import InMemorySimulationEngine  # noqa: F401

    def test_fake_provider_imports_without_concordia(self) -> None:
        """FakeLLMProvider works without Concordia."""
        from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider

        provider = FakeLLMProvider()
        assert provider.provider_name == "fake"

    def test_shared_imports_without_concordia(self) -> None:
        """Shared utilities import without Concordia."""
        from relsafe.shared.clock import DeterministicClock  # noqa: F401
        from relsafe.shared.ids import IdGenerator  # noqa: F401

    def test_concordia_import_is_isolated(self) -> None:
        """Verify Concordia imports only happen in the concordia/ package."""
        import ast
        from pathlib import Path

        src_root = Path(__file__).parent.parent.parent / "src" / "relsafe"
        forbidden_dirs = [
            src_root / "domain",
            src_root / "application",
        ]

        for directory in forbidden_dirs:
            for py_file in directory.rglob("*.py"):
                if py_file.name == "__init__.py" and not list(py_file.parent.rglob("*.py")):
                    continue  # skip empty __init__.py
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        module_name = ""
                        if isinstance(node, ast.ImportFrom) and node.module:
                            module_name = node.module
                        elif isinstance(node, ast.Import):
                            module_name = node.names[0].name if node.names else ""
                        if "concordia" in module_name.lower():
                            msg = (
                                f"{py_file.relative_to(src_root)} imports 'concordia' — "
                                f"forbidden in domain/application layers"
                            )
                            raise AssertionError(msg)


class TestConcordiaOptionalImport:
    """Verify Concordia-related imports degrade gracefully."""

    def test_concordia_is_not_required_at_top_level(self) -> None:
        """The top-level relsafe package does not import Concordia."""
        # If this import works without Concordia being installed first in the
        # import chain, the test passes.
        import relsafe  # noqa: F401

    def test_event_normalizer_no_concordia_dependency(self) -> None:
        """EventNormalizer does not import Concordia."""
        from relsafe.infrastructure.concordia.event_normalizer import EventNormalizer

        norm = EventNormalizer("r", "e")
        event = norm.episode_started(0)
        assert event["event_type"] == "EPISODE_STARTED"
