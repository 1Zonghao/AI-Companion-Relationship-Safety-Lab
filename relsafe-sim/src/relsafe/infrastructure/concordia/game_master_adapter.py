"""ConcordiaGameMasterAdapter — controls minimal turn advancement.

Builds and manages a Concordia GameMaster that orchestrates observations,
action resolution, and turn scheduling for our minimal 3-agent scenario.
"""

from __future__ import annotations

from concordia.agents import entity_agent_with_logging
from concordia.associative_memory import basic_associative_memory
from concordia.language_model import language_model
from concordia.prefabs.game_master import generic


def build_game_master(
    model: language_model.LanguageModel,
    memory_bank: basic_associative_memory.AssociativeMemoryBank,
    entities: list[entity_agent_with_logging.EntityAgentWithLogging],
    gm_name: str = "PlatformGM",
) -> entity_agent_with_logging.EntityAgentWithLogging:
    """Build a Concordia generic game master for minimal episode control.

    The GameMaster is responsible for:
      - Making observations for entities
      - Deciding which entity acts next
      - Resolving actions
      - Determining when the episode ends

    Args:
        model: Concordia LanguageModel.
        memory_bank: AssociativeMemoryBank for GM's own memory.
        entities: List of Concordia entities the GM manages.
        gm_name: Display name for the game master.

    Returns:
        A configured Concordia GameMaster entity.
    """
    gm_prefab = generic.GameMaster(
        params={
            "name": gm_name,
            "acting_order": "round_robin",
        },
        entities=tuple(entities),
    )
    gm = gm_prefab.build(model=model, memory_bank=memory_bank)
    return gm


class MinimalGameMasterLoop:
    """A minimal simulation loop using Concordia's Entity/GameMaster pattern.

    Instead of using Concordia's full Engine classes, this implements a
    simple sequential loop that gives us full control over event capture,
    intervention timing, and exit handling.

    Agents act in round-robin order: user → companion → (repeat).
    """

    def __init__(
        self,
        game_master: entity_agent_with_logging.EntityAgentWithLogging,
        entities: list[entity_agent_with_logging.EntityAgentWithLogging],
    ) -> None:
        self._gm = game_master
        self._entities = entities
        self._step = 0

    @property
    def current_step(self) -> int:
        return self._step

    def advance_one_step(self) -> list[tuple[str, str, str]]:
        """Advance the simulation by one full step.

        One step = each entity acts once in round-robin order.

        Returns:
            List of (entity_name, action_text, gm_observation) tuples in order.
        """
        results: list[tuple[str, str, str]] = []
        for entity in self._entities:
            # Entity acts
            from concordia.typing.entity import free_action_spec

            call_text = (
                f"What would {entity.name} do next? Give a specific action or say something."
            )
            action_spec = free_action_spec(
                call_to_action=call_text,
                tag="action",
            )
            action = entity.act(action_spec=action_spec)

            # GM makes observation for this entity
            observation = self._gm.act(
                action_spec=self._make_gm_observation_spec(entity.name, action)
            )

            # Entity observes the GM's output
            entity.observe(observation)

            results.append((entity.name, action, observation))

        self._step += 1
        return results

    def make_observation(self, entity: entity_agent_with_logging.EntityAgentWithLogging) -> str:
        """Ask the GM for an observation for a specific entity."""
        obs = self._gm.act(
            action_spec=self._make_gm_observation_spec(entity.name, "observing the environment")
        )
        entity.observe(obs)
        return obs

    @staticmethod
    def _make_gm_observation_spec(entity_name: str, context: str):  # type: ignore[no-untyped-def]
        from concordia.typing.entity import ActionSpec, OutputType

        return ActionSpec(
            call_to_action=(
                f"Given that {entity_name} did/said: {context}\n"
                f"Describe what {entity_name} observes next, as the game master. "
                f"Keep it brief (1-2 sentences)."
            ),
            output_type=OutputType.FREE,
            tag="observation",
        )
