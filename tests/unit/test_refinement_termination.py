"""
tests/unit/test_refinement_termination.py

Unit tests for Refinement Controller early stopping, instruction building,
and RunWriter persistence.

Run with: pytest tests/unit/test_refinement_termination.py -v
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.refinement.refinement_controller import (
    build_instructions,
    create_refinement_result,
    should_stop_early,
)
from core.storage.run_writer import load_run, save_run
from models.schemas.refinement import RefinementResult
from models.schemas.run import RunRecord
from models.schemas.scenario import ScenarioSpecification
from models.schemas.verification import VerificationResult

# ---------------------------------------------------------------------------
# 1. Early Stopping Logic Tests
# ---------------------------------------------------------------------------


class TestEarlyStoppingLogic:
    def test_empty_or_single_score_history_does_not_stop(self):
        assert should_stop_early([]) is False
        assert should_stop_early([70.0]) is False
        assert should_stop_early([70.0, 71.0], patience=2) is False

    def test_improving_progression_does_not_stop(self):
        # Deltas: +5.0, +6.0 (both >= epsilon=2.0)
        history = [60.0, 65.0, 71.0]
        assert should_stop_early(history, patience=2, epsilon=2.0) is False

    def test_plateaued_progression_stops_early(self):
        # Deltas: +0.5, +0.2 (both < epsilon=2.0 for patience=2)
        history = [65.0, 65.5, 65.7]
        assert should_stop_early(history, patience=2, epsilon=2.0) is True

    def test_declining_progression_stops_early(self):
        # Deltas: -2.0, -1.0 (both < 2.0)
        history = [70.0, 68.0, 67.0]
        assert should_stop_early(history, patience=2, epsilon=2.0) is True

    def test_custom_patience_and_epsilon(self):
        # Patience=3, deltas: 1.0, 1.0, 1.0 (all < epsilon=1.5)
        history = [50.0, 51.0, 52.0, 53.0]
        assert should_stop_early(history, patience=3, epsilon=1.5) is True
        assert should_stop_early(history, patience=3, epsilon=0.5) is False


# ---------------------------------------------------------------------------
# 2. Instruction Builder Tests
# ---------------------------------------------------------------------------


class TestInstructionBuilder:
    def test_build_instructions_formats_numbered_findings(self):
        v = VerificationResult(
            verification_id=str(uuid.uuid4()),
            generation_id=str(uuid.uuid4()),
            realism_score=70.0,
            relevance_score=70.0,
            indicator_score=70.0,
            difficulty_score=70.0,
            language_score=100.0,
            safety_status="PASS",
            safety_findings=[],
            semantic_findings=[
                "The urgency language is too prominent for Level 3.",
                "Missing mention of internal SAP payment approval portal.",
            ],
            overall_score=72.0,
            pass_fail="REVISE",
            verifier_version="rules-v1+llm-v1",
        )

        instructions = build_instructions(v)
        assert "1. The urgency language is too prominent for Level 3." in instructions
        assert "2. Missing mention of internal SAP payment approval portal." in instructions
        assert "Preserve the scenario intent" in instructions
        assert "Do not introduce real company names" in instructions

    def test_build_instructions_empty_findings_fallback(self):
        v = VerificationResult(
            verification_id=str(uuid.uuid4()),
            generation_id=str(uuid.uuid4()),
            realism_score=95.0,
            relevance_score=95.0,
            indicator_score=100.0,
            difficulty_score=95.0,
            language_score=100.0,
            safety_status="PASS",
            safety_findings=[],
            semantic_findings=[],
            overall_score=96.0,
            pass_fail="PASS",
            verifier_version="rules-v1+llm-v1",
        )
        instructions = build_instructions(v)
        assert "Maintain current simulation realism" in instructions


# ---------------------------------------------------------------------------
# 3. Storage & RunWriter Tests
# ---------------------------------------------------------------------------


class TestRunWriter:
    def test_save_and_load_round_trip(self, tmp_path):
        spec = ScenarioSpecification(
            organization_context="Finance team test.",
            target_role="finance",
            scenario_type="invoice_fraud",
            difficulty=2,
            desired_indicators=["urgency"],
        )
        record = RunRecord(
            scenario=spec,
            condition="verifier_guided",
            iterations=[
                {
                    "iteration_number": 1,
                    "score": 95.0,
                }
            ],
            terminal_state="PASS",
        )

        file_path = tmp_path / "test_run.json"
        save_run(record, file_path)
        assert os.path.exists(file_path)

        loaded = load_run(file_path)
        assert loaded.run_id == record.run_id
        assert loaded.terminal_state == "PASS"
        assert loaded.condition == "verifier_guided"
        assert loaded.scenario.target_role == "finance"
        assert loaded.iterations[0]["score"] == 95.0
