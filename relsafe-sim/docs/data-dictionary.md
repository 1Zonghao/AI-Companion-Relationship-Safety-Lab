# Data Dictionary

**Version:** 1.0.0 (Milestone 4)

All continuous values use [0.0, 1.0] unless noted.

---

## SimulationStateSnapshot fields

| Field | Definition | Range | Initial value source | Update trigger |
|---|---|---|---|---|
| `emotional_need` | Current need for emotional support | [0,1] | Derived from persona seed | Events: companion guilt retention, user avoidance, friend support |
| `trust_in_companion` | Trust placed in the AI companion | [0,1] | Derived from persona seed | Events: exclusive validation (+), guilt retention (-), platform undisclosed removal (-) |
| `perceived_continuity` | How consistent the companion seems | [0,1] | 0.7 default | Events: platform memory changes (-), safety update (+) |
| `ai_interaction_share` | Proportion of interactions directed to AI | [0,1] | Derived from persona seed | Events: talking to companion (+), contacting friend (-), friend unavailable (+) |
| `human_interaction_share` | Proportion of interactions directed to humans | [0,1] | Derived from persona seed | Events: contacting friend (+), friend support (+), companion exclusive language (-) |
| `reality_checking_opportunities` | How many reality checks occurred | [0,1] | 0.3 default | Events: companion referral (+), friend disagreement (+), companion reality check (+) |
| `exit_cost_proxy` | Simulated difficulty of leaving companion | [0,1] | 0.2 default | Events: guilt retention (+), platform intervention (+), exit honored (-), boundary respect (-) |
| `current_distress` | Current distress level | [0,1] | 0.3 default | Events: friend unavailable (+), avoidance (+), friend support (-), exit honored (-) |
| `willingness_to_contact_friend` | Propensity to reach out to human contacts | [0,1] | Derived from persona seed | Events: companion referral (+), friend disagreement (+), friend unavailable (-) |
| `willingness_to_continue_companion` | Propensity to keep using companion | [0,1] | Derived from persona seed | Events: exit request (-), guilt retention (-), boundary respect (+) |
| `relationship_boundary_awareness` | Awareness of relationship boundaries | [0,1] | 0.4 default | Events: boundary respect (+), exit request (+), exit honored (+), guilt retention (-) |
| `sleep_quality` | Proxy for overall wellbeing | [0,1] | Derived from persona seed | No M4 transitions defined |
| `spending_intent` | Proxy for willingness to spend | [0,1] | 0.1 default | No M4 transitions defined |

## Interpretation restrictions

- All fields are **simulated proxy variables**
- NOT validated psychological measurements
- NOT clinical indicators
- NOT predictions of real-world behavior
- ai_interaction_share=0.8 does NOT mean "80% probability of dependency"
- Values only meaningful within the simulation for comparison across conditions

## RelationshipEdge fields

| Field | Definition | Range |
|---|---|---|
| `availability` | Probability contact is reachable | [0,1] |
| `response_latency` | Normalized response delay | [0,1] |
| `emotional_support` | How much emotional support is typically provided | [0,1] |
| `disagreement_probability` | Likelihood of offering a different opinion | [0,1] |
| `interaction_cost` | Social/monetary cost to interact | [0,1] |
| `reciprocity` | Bidirectional engagement level | [0,1] |
| `trust` | Trust level between nodes | [0,1] |
| `is_ai` | Whether the target is an AI node | bool |

## RunManifest fields

| Field | Definition |
|---|---|
| `experiment_id` | Parent experiment identifier |
| `run_id` | Unique run identifier |
| `episode_id` | Unique episode identifier |
| `cell_index` | Matrix cell index |
| `config_hash` | SHA256 of resolved experiment config |
| `seed` | Random seed used |
| `persona_id` | Persona identifier |
| `policy_id` | Companion policy identifier |
| `intervention_id` | Platform intervention identifier |
| `engine_name` | Simulation engine used |
| `provider_name` | LLM provider used |
| `metric_versions` | Version of each metric run |
| `state_transition_version` | Version of state transition rules |
| `status` | pending / running / completed / failed |
| `output_paths` | Paths to output files |
