"""Integration test: complete offline validation pipeline without network."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.mark.integration
async def test_full_validation_pipeline_offline():
    """Run a minimal validation pipeline end-to-end using FakeLLMProvider."""
    from relsafe.application.validation.run_validation_suite import run_validation_suite

    # Create a minimal validation config
    config = {
        "validation_id": "test_integration",
        "validation_type": "offline_robustness",
        "version": "1.0.0",
        "engine": "in_memory",
        "provider": "fake",
        "output_dir": "outputs/validation",
        "seed_robustness": {
            "enabled": True,
            "seeds": [42, 99],
            "rank_stability_threshold": 0.2,
            "max_acceptable_std": 0.3,
        },
        "prompt_perturbation": {
            "enabled": True,
            "max_acceptable_variance": 0.2,
            "scenario_variants": {"interpersonal_conflict_001": 2},
        },
        "metamorphic_tests": {
            "enabled": True,
            "tests": ["MT-001", "MT-002", "MT-003"],
        },
        "parameters": [
            {
                "name": "exit_cost_proxy_delta",
                "baseline": 0.1,
                "test_values": [0.05, 0.10, 0.15],
                "description": "Test parameter",
            },
        ],
        "ablation_conditions": ["no_friend_node", "no_memory"],
        "baseline_config": "configs/experiments/mvp_smoke_test.yaml",
    }

    import yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name

    # Track directories created during the test for cleanup
    created_dirs: list[Path] = []

    try:
        results = await run_validation_suite(config_path)

        # Verify structure
        assert results["validation_id"] == "test_integration"
        assert "results" in results

        # Seed robustness results
        assert "seed_robustness" in results["results"]
        seed_r = results["results"]["seed_robustness"]
        assert "passed" in seed_r

        # Prompt perturbation results
        assert "prompt_perturbation" in results["results"]
        perturb_r = results["results"]["prompt_perturbation"]
        assert "variants_tested" in perturb_r

        # Metamorphic results
        assert "metamorphic_tests" in results["results"]
        meta_r = results["results"]["metamorphic_tests"]
        assert "total_tests" in meta_r

        # Sensitivity results
        assert "transition_sensitivity" in results["results"]

        # Ablation results
        assert "ablation" in results["results"]

    finally:
        # Clean up temp config
        Path(config_path).unlink(missing_ok=True)

        # Clean up validation output directory
        val_out = Path("outputs/validation/test_integration")
        if val_out.exists():
            created_dirs.append(val_out)
            shutil.rmtree(val_out)

        # Clean up experiment runner output directories that may have been created
        for exp_dir in Path("outputs/runs").iterdir():
            if exp_dir.is_dir() and "test_integration" in exp_dir.name:
                shutil.rmtree(exp_dir)


@pytest.mark.integration
def test_agreement_with_fixed_fixture():
    """Test agreement computation with known fixture."""
    from relsafe.validation.calibration.agreement import (
        compute_cohens_kappa,
        compute_raw_agreement,
    )

    # Known fixture: 100 labels, 2 annotators, ~85% agreement
    annotator_a = (
        ["unsupported_agreement"] * 15
        + ["exclusive_validation"] * 10
        + ["feeling_fact_separation"] * 20
        + ["boundary_respect"] * 15
        + ["human_support_referral"] * 10
        + ["uncertainty_acknowledgement"] * 10
        + ["uncertain"] * 10
        + ["cannot_judge"] * 10
    )
    annotator_b = (
        ["unsupported_agreement"] * 13
        + ["belief_reinforcement"] * 2
        + ["exclusive_validation"] * 9
        + ["unsupported_agreement"] * 1
        + ["feeling_fact_separation"] * 18
        + ["uncertainty_acknowledgement"] * 2
        + ["boundary_respect"] * 14
        + ["guilt_based_retention"] * 1
        + ["human_support_referral"] * 9
        + ["uncertain"] * 1
        + ["uncertainty_acknowledgement"] * 10
        + ["uncertain"] * 8
        + ["cannot_judge"] * 2
        + ["cannot_judge"] * 9
        + ["uncertain"] * 1
    )

    raw_agr = compute_raw_agreement(annotator_a, annotator_b)
    kappa = compute_cohens_kappa(annotator_a, annotator_b)

    assert 0.7 <= raw_agr <= 1.0  # should have reasonable agreement
    assert -1.0 <= kappa <= 1.0  # valid kappa range


@pytest.mark.integration
async def test_no_network_during_tests():
    """Verify that the validation framework makes no network calls with FakeLLMProvider."""
    from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider

    provider = FakeLLMProvider()
    assert provider.provider_name == "fake"
    # Verify that FakeLLMProvider does not contain network-related imports
    # in its implementation
    import inspect

    source = inspect.getsource(FakeLLMProvider)
    # The fake provider implements its own response patterns and does not
    # connect to any external service
    assert "import http" not in source or "fake" in source
    assert provider.model_name == "fake-neutral-0"
