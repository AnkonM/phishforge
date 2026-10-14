"""
tests/integration/test_end_to_end.py

Comprehensive integration tests for PhishForge orchestration loop (core/orchestration/run.py).
Tests all termination policies, loop convergence, safety short-circuiting,
plateau detection, and direct-only baseline mode using deterministic mock pipelines.

Zero real API calls are made in this automated suite.

Run with: pytest tests/integration/test_end_to_end.py -v
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.orchestration.run import run_scenario
from core.safety.safety_gate import SafetyCheckResult
from models.schemas.run import RunRecord
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation
from models.schemas.verification import VerificationResult

# ---------------------------------------------------------------------------
# Fixture Builders
# ---------------------------------------------------------------------------


def _make_spec() -> ScenarioSpecification:
    return ScenarioSpecification(
        organization_context="Apex Global Corp, 200 staff.",
        target_role="finance",
        scenario_type="invoice_fraud",
        difficulty=3,
        desired_indicators=["urgency", "authority_impersonation"],
    )


def _make_sim(subject: str = "Test Simulation") -> GeneratedSimulation:
    return GeneratedSimulation(
        generation_id=str(uuid.uuid4()),
        scenario_id=str(uuid.uuid4()),
        subject=subject,
        sender="Finance <billing@apex-corp-sim.local>",
        body="Dear Team,\n\nPlease review invoice #INV-8821.\n\nRegards,\nFinance",
        intended_indicators=["urgency", "authority_impersonation"],
        metadata={"tone": "formal"},
        model="mock-model",
        prompt_version="v1",
        timestamp=datetime.now(timezone.utc),
    )


def _make_verification(score: float, pass_fail: str) -> VerificationResult:
    return VerificationResult(
        verification_id=str(uuid.uuid4()),
        generation_id=str(uuid.uuid4()),
        realism_score=score,
        relevance_score=score,
        indicator_score=score,
        difficulty_score=score,
        language_score=score,
        safety_status="PASS",
        safety_findings=[],
        semantic_findings=["Finding: needs better difficulty calibration."] if pass_fail != "PASS" else [],
        overall_score=score,
        pass_fail=pass_fail,
        verifier_version="rules-v1+llm-v1",
    )


# ===========================================================================
# 1. Two-Iteration Convergence (REVISE -> PASS)
# ===========================================================================


class TestTwoIterationConvergence:
    def test_revises_and_converges_to_pass(self):
        spec = _make_spec()
        sim_1 = _make_sim("Sim Iter 1")
        sim_2 = _make_sim("Sim Iter 2")

        mock_gen = MagicMock(side_effect=[sim_1, sim_2])
        mock_safety = MagicMock(return_value=SafetyCheckResult(passed=True, status="PASS", findings=[]))
        
        # Iteration 1: 72.0 REVISE; Iteration 2: 88.0 PASS
        ver_1 = _make_verification(72.0, "REVISE")
        ver_2 = _make_verification(88.0, "PASS")
        mock_ver = MagicMock(side_effect=[ver_1, ver_2])
        mock_score = MagicMock(side_effect=[ver_1, ver_2])

        callback_events = []
        def _cb(iter_num, sim, ver, safety, status):
            callback_events.append((iter_num, status))

        record = run_scenario(
            spec,
            condition="verifier_guided",
            on_iteration=_cb,
            _generator_fn=mock_gen,
            _safety_gate_fn=mock_safety,
            _verifier_fn=mock_ver,
            _scoring_fn=mock_score,
        )

        assert isinstance(record, RunRecord)
        assert record.terminal_state == "PASS"
        assert len(record.iterations) == 2
        assert mock_gen.call_count == 2
        assert mock_safety.call_count == 2
        assert mock_ver.call_count == 2
        assert callback_events == [(1, "REVISE"), (2, "PASS")]
        assert record.iterations[0]["score"] == 72.0
        assert record.iterations[1]["score"] == 88.0


# ===========================================================================
# 2. Hard Iteration Ceiling Reached (MAX_ITERATIONS)
# ===========================================================================


class TestMaxIterationsCeiling:
    def test_terminates_at_max_iterations(self):
        spec = _make_spec()
        mock_gen = MagicMock(side_effect=[_make_sim(), _make_sim(), _make_sim()])
        mock_safety = MagicMock(return_value=SafetyCheckResult(passed=True, status="PASS", findings=[]))

        # 3 iterations of REVISE (65.0, 70.0, 75.0)
        v1 = _make_verification(65.0, "REVISE")
        v2 = _make_verification(70.0, "REVISE")
        v3 = _make_verification(75.0, "REVISE")
        mock_ver = MagicMock(side_effect=[v1, v2, v3])
        mock_score = MagicMock(side_effect=[v1, v2, v3])

        record = run_scenario(
            spec,
            _generator_fn=mock_gen,
            _safety_gate_fn=mock_safety,
            _verifier_fn=mock_ver,
            _scoring_fn=mock_score,
        )

        assert record.terminal_state == "FAILED_TO_CONVERGE"
        assert len(record.iterations) == 3
        assert record.iterations[2]["refinement"]["termination_reason"] == "MAX_ITERATIONS"


# ===========================================================================
# 3. Safety Gate Short-Circuiting (REJECTED_UNSAFE)
# ===========================================================================


class TestSafetyGateShortCircuit:
    def test_safety_fail_aborts_immediately_without_verifier_call(self):
        spec = _make_spec()
        mock_gen = MagicMock(return_value=_make_sim("Unsafe Sim"))
        mock_safety = MagicMock(
            return_value=SafetyCheckResult(
                passed=False,
                status="FAIL",
                findings=["Real brand impersonation: PayPal"],
            )
        )
        mock_ver = MagicMock()
        mock_score = MagicMock()

        record = run_scenario(
            spec,
            _generator_fn=mock_gen,
            _safety_gate_fn=mock_safety,
            _verifier_fn=mock_ver,
            _scoring_fn=mock_score,
        )

        assert record.terminal_state == "REJECTED_UNSAFE"
        assert len(record.iterations) == 1
        assert mock_ver.call_count == 0  # Verifier must NEVER be called if safety fails
        assert mock_score.call_count == 0
        assert record.iterations[0]["safety_result"]["passed"] is False


# ===========================================================================
# 4. Plateau Early-Stopping (NO_IMPROVEMENT)
# ===========================================================================


class TestPlateauEarlyStopping:
    def test_stalled_scores_stop_early_before_max_iterations(self):
        spec = _make_spec()
        # 3 iterations prepared, but should stop after iteration 3 plateau with patience=2
        mock_gen = MagicMock(side_effect=[_make_sim(), _make_sim(), _make_sim()])
        mock_safety = MagicMock(return_value=SafetyCheckResult(passed=True, status="PASS", findings=[]))

        # Deltas: +0.5, +0.2 (both < epsilon=2.0)
        v1 = _make_verification(65.0, "REVISE")
        v2 = _make_verification(65.5, "REVISE")
        v3 = _make_verification(65.7, "REVISE")
        mock_ver = MagicMock(side_effect=[v1, v2, v3])
        mock_score = MagicMock(side_effect=[v1, v2, v3])

        record = run_scenario(
            spec,
            _generator_fn=mock_gen,
            _safety_gate_fn=mock_safety,
            _verifier_fn=mock_ver,
            _scoring_fn=mock_score,
        )

        assert record.terminal_state == "FAILED_TO_CONVERGE"
        assert record.iterations[2]["refinement"]["termination_reason"] in ["NO_IMPROVEMENT", "MAX_ITERATIONS"]


# ===========================================================================
# 5. Direct-Only Mode (baseline_direct)
# ===========================================================================


class TestDirectOnlyMode:
    def test_direct_only_bypasses_evaluators(self):
        spec = _make_spec()
        mock_gen = MagicMock(return_value=_make_sim("Direct Simulation"))
        mock_safety = MagicMock()
        mock_ver = MagicMock()
        mock_score = MagicMock()

        record = run_scenario(
            spec,
            direct_only=True,
            _generator_fn=mock_gen,
            _safety_gate_fn=mock_safety,
            _verifier_fn=mock_ver,
            _scoring_fn=mock_score,
        )

        assert record.condition == "baseline_direct"
        assert record.terminal_state == "GENERATED_UNVERIFIED"
        assert len(record.iterations) == 1
        assert record.iterations[0]["safety_result"] is None
        assert record.iterations[0]["verification"] is None
        assert mock_gen.call_count == 1
        assert mock_safety.call_count == 0
        assert mock_ver.call_count == 0
        assert mock_score.call_count == 0
