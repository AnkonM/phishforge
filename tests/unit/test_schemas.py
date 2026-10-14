"""
tests/unit/test_schemas.py

Unit tests for all five Pydantic schemas.
Coverage: at least one valid and one invalid payload per schema.

Run with:  pytest tests/unit/test_schemas.py -v
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Path setup: ensure the phishforge package root is importable when tests are
# run from the repository root (pytest invoked as: pytest tests/).
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.schemas.refinement import RefinementResult
from models.schemas.run import RunRecord
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation
from models.schemas.verification import VerificationResult

# ===========================================================================
# Helpers / fixture factories
# ===========================================================================


def _valid_scenario_payload(**kwargs) -> dict:
    base = {
        "organization_context": "Mid-size UK professional services firm, 350 staff. Finance uses SAP.",
        "target_role": "finance",
        "scenario_type": "invoice_fraud",
        "difficulty": 3,
        "desired_indicators": ["urgency", "authority_impersonation"],
    }
    base.update(kwargs)
    return base


def _valid_simulation_payload(**kwargs) -> dict:
    base = {
        "generation_id": str(uuid.uuid4()),
        "scenario_id": str(uuid.uuid4()),
        "subject": "ACTION REQUIRED: Approve invoice #INV-2024-0892",
        "sender": "Accounts Payable Team <ap-noreply@accts-training.example>",
        "body": "Please review and approve the attached invoice at your earliest convenience.",
        "intended_indicators": ["urgency", "authority_impersonation"],
        "model": "claude-opus-4-5",
        "prompt_version": "v1",
    }
    base.update(kwargs)
    return base


def _valid_verification_payload(**kwargs) -> dict:
    base = {
        "verification_id": str(uuid.uuid4()),
        "generation_id": str(uuid.uuid4()),
        "realism_score": 80.0,
        "relevance_score": 75.0,
        "difficulty_score": 70.0,
        "indicator_score": 90.0,
        "language_score": 85.0,
        "safety_status": "PASS",
        "safety_findings": [],
        "semantic_findings": [],
        "overall_score": 80.0,
        "pass_fail": "PASS",
        "verifier_version": "v1",
    }
    base.update(kwargs)
    return base


def _valid_refinement_payload(**kwargs) -> dict:
    base = {
        "iteration_number": 1,
        "prior_score": None,
        "weaknesses": ["role relevance weak: request does not match finance AP workflow"],
        "revision_instructions": "Improve role relevance: align the request with SAP invoice approval workflow.",
        "new_score": 72.5,
        "score_delta": None,
        "termination_reason": None,
    }
    base.update(kwargs)
    return base


def _valid_run_record_payload(**kwargs) -> dict:
    base = {
        "scenario": _valid_scenario_payload(),
        "condition": "verifier_guided",
        "terminal_state": "PASS",
    }
    base.update(kwargs)
    return base


# ===========================================================================
# ScenarioSpecification
# ===========================================================================


class TestScenarioSpecification:
    def test_valid_minimal(self):
        """Minimal valid payload — omits all defaulted fields."""
        spec = ScenarioSpecification(**_valid_scenario_payload())
        assert spec.target_role == "finance"
        assert spec.difficulty == 3
        assert spec.language == "en"           # default
        assert spec.prohibited_elements == []  # default
        assert spec.simulation_constraints == {}  # default
        assert spec.scenario_id  # auto-generated

    def test_valid_with_all_fields(self):
        spec = ScenarioSpecification(
            **_valid_scenario_payload(
                language="de",
                prohibited_elements=["real brand names"],
                simulation_constraints={"max_body_words": 200},
            )
        )
        assert spec.language == "de"
        assert spec.prohibited_elements == ["real brand names"]
        assert spec.simulation_constraints == {"max_body_words": 200}

    def test_valid_all_difficulty_levels(self):
        for d in (1, 2, 3, 4):
            spec = ScenarioSpecification(**_valid_scenario_payload(difficulty=d))
            assert spec.difficulty == d

    def test_invalid_role_not_in_literal(self):
        with pytest.raises(ValidationError):
            ScenarioSpecification(**_valid_scenario_payload(target_role="marketing"))

    def test_invalid_role_legal_removed(self):
        """'legal' was in the old schema but is NOT in the authoritative spec."""
        with pytest.raises(ValidationError):
            ScenarioSpecification(**_valid_scenario_payload(target_role="legal"))

    def test_invalid_role_general_removed(self):
        """'general' was in the old schema but is NOT in the authoritative spec."""
        with pytest.raises(ValidationError):
            ScenarioSpecification(**_valid_scenario_payload(target_role="general"))

    def test_invalid_difficulty_5_out_of_range(self):
        """difficulty=5 is explicitly out of range — Literal[1,2,3,4] only."""
        with pytest.raises(ValidationError):
            ScenarioSpecification(**_valid_scenario_payload(difficulty=5))

    def test_invalid_difficulty_0_out_of_range(self):
        with pytest.raises(ValidationError):
            ScenarioSpecification(**_valid_scenario_payload(difficulty=0))

    def test_invalid_empty_desired_indicators(self):
        with pytest.raises(ValidationError):
            ScenarioSpecification(**_valid_scenario_payload(desired_indicators=[]))

    def test_invalid_blank_indicator_string(self):
        with pytest.raises(ValidationError):
            ScenarioSpecification(**_valid_scenario_payload(desired_indicators=["urgency", "  "]))

    def test_invalid_language_not_two_letters(self):
        with pytest.raises(ValidationError):
            ScenarioSpecification(**_valid_scenario_payload(language="english"))

    def test_language_is_lowercased(self):
        spec = ScenarioSpecification(**_valid_scenario_payload(language="EN"))
        assert spec.language == "en"

    def test_indicators_are_stripped(self):
        spec = ScenarioSpecification(**_valid_scenario_payload(desired_indicators=["  urgency  "]))
        assert spec.desired_indicators == ["urgency"]

    def test_scenario_id_is_unique_per_instance(self):
        s1 = ScenarioSpecification(**_valid_scenario_payload())
        s2 = ScenarioSpecification(**_valid_scenario_payload())
        assert s1.scenario_id != s2.scenario_id

    def test_scenario_type_is_plain_string(self):
        """scenario_type is an open str, not a Literal enum."""
        spec = ScenarioSpecification(**_valid_scenario_payload(scenario_type="custom_scenario"))
        assert spec.scenario_type == "custom_scenario"


# ===========================================================================
# GeneratedSimulation
# ===========================================================================


class TestGeneratedSimulation:
    def test_valid_full_payload(self):
        sim = GeneratedSimulation(**_valid_simulation_payload())
        assert sim.subject.startswith("ACTION REQUIRED")
        assert sim.sender.endswith(".example>")
        assert sim.model == "claude-opus-4-5"
        assert sim.prompt_version == "v1"
        assert sim.timestamp  # auto-generated

    def test_valid_with_explicit_timestamp(self):
        ts = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        sim = GeneratedSimulation(**_valid_simulation_payload(timestamp=ts))
        assert sim.timestamp == ts

    def test_valid_with_metadata(self):
        sim = GeneratedSimulation(**_valid_simulation_payload(metadata={"tone": "formal"}))
        assert sim.metadata["tone"] == "formal"

    def test_invalid_missing_generation_id(self):
        payload = _valid_simulation_payload()
        del payload["generation_id"]
        with pytest.raises(ValidationError):
            GeneratedSimulation(**payload)

    def test_invalid_missing_scenario_id(self):
        payload = _valid_simulation_payload()
        del payload["scenario_id"]
        with pytest.raises(ValidationError):
            GeneratedSimulation(**payload)

    def test_invalid_missing_subject(self):
        payload = _valid_simulation_payload()
        del payload["subject"]
        with pytest.raises(ValidationError):
            GeneratedSimulation(**payload)

    def test_invalid_missing_sender(self):
        payload = _valid_simulation_payload()
        del payload["sender"]
        with pytest.raises(ValidationError):
            GeneratedSimulation(**payload)

    def test_invalid_missing_body(self):
        payload = _valid_simulation_payload()
        del payload["body"]
        with pytest.raises(ValidationError):
            GeneratedSimulation(**payload)

    def test_invalid_missing_intended_indicators(self):
        payload = _valid_simulation_payload()
        del payload["intended_indicators"]
        with pytest.raises(ValidationError):
            GeneratedSimulation(**payload)

    def test_invalid_missing_model(self):
        payload = _valid_simulation_payload()
        del payload["model"]
        with pytest.raises(ValidationError):
            GeneratedSimulation(**payload)

    def test_invalid_missing_prompt_version(self):
        payload = _valid_simulation_payload()
        del payload["prompt_version"]
        with pytest.raises(ValidationError):
            GeneratedSimulation(**payload)


# ===========================================================================
# VerificationResult
# ===========================================================================


class TestVerificationResult:
    def test_valid_pass_result(self):
        result = VerificationResult(**_valid_verification_payload())
        assert result.safety_status == "PASS"
        assert result.pass_fail == "PASS"
        assert result.overall_score == 80.0

    def test_valid_revise_result(self):
        result = VerificationResult(
            **_valid_verification_payload(
                overall_score=72.0,
                pass_fail="REVISE",
                semantic_findings=["role relevance weak"],
            )
        )
        assert result.pass_fail == "REVISE"
        assert result.semantic_findings == ["role relevance weak"]

    def test_valid_safety_fail_result(self):
        result = VerificationResult(
            **_valid_verification_payload(
                safety_status="FAIL",
                safety_findings=["real brand name detected"],
            )
        )
        assert result.safety_status == "FAIL"
        assert len(result.safety_findings) == 1

    def test_invalid_score_above_100(self):
        with pytest.raises(ValidationError):
            VerificationResult(**_valid_verification_payload(realism_score=150.0))

    def test_invalid_score_below_0(self):
        with pytest.raises(ValidationError):
            VerificationResult(**_valid_verification_payload(indicator_score=-5.0))

    def test_invalid_safety_status_value(self):
        with pytest.raises(ValidationError):
            VerificationResult(**_valid_verification_payload(safety_status="UNKNOWN"))

    def test_invalid_pass_fail_value(self):
        with pytest.raises(ValidationError):
            VerificationResult(**_valid_verification_payload(pass_fail="MAYBE"))

    def test_invalid_missing_verification_id(self):
        payload = _valid_verification_payload()
        del payload["verification_id"]
        with pytest.raises(ValidationError):
            VerificationResult(**payload)

    def test_invalid_missing_generation_id(self):
        payload = _valid_verification_payload()
        del payload["generation_id"]
        with pytest.raises(ValidationError):
            VerificationResult(**payload)

    def test_semantic_findings_deduplicated(self):
        payload = _valid_verification_payload(
            semantic_findings=["duplicate finding", "unique finding", "duplicate finding"]
        )
        result = VerificationResult(**payload)
        assert result.semantic_findings.count("duplicate finding") == 1
        assert len(result.semantic_findings) == 2


# ===========================================================================
# RefinementResult
# ===========================================================================


class TestRefinementResult:
    def test_valid_first_iteration_no_prior_score(self):
        result = RefinementResult(**_valid_refinement_payload())
        assert result.iteration_number == 1
        assert result.prior_score is None
        assert result.termination_reason is None  # loop continues

    def test_valid_converging_iteration(self):
        result = RefinementResult(
            **_valid_refinement_payload(
                iteration_number=2,
                prior_score=65.0,
                new_score=80.5,
                score_delta=15.5,
                termination_reason="PASS",
            )
        )
        assert result.termination_reason == "PASS"
        assert result.score_delta == pytest.approx(15.5)

    def test_valid_all_termination_reasons(self):
        for reason in ("PASS", "MAX_ITERATIONS", "NO_IMPROVEMENT", "SAFETY_FAIL"):
            result = RefinementResult(
                **_valid_refinement_payload(termination_reason=reason)
            )
            assert result.termination_reason == reason

    def test_invalid_iteration_number_zero(self):
        with pytest.raises(ValidationError):
            RefinementResult(**_valid_refinement_payload(iteration_number=0))

    def test_invalid_prior_score_out_of_range(self):
        with pytest.raises(ValidationError):
            RefinementResult(**_valid_refinement_payload(prior_score=110.0))

    def test_invalid_new_score_out_of_range(self):
        with pytest.raises(ValidationError):
            RefinementResult(**_valid_refinement_payload(new_score=-1.0))

    def test_invalid_termination_reason_value(self):
        with pytest.raises(ValidationError):
            RefinementResult(**_valid_refinement_payload(termination_reason="TIMEOUT"))

    def test_invalid_missing_revision_instructions(self):
        """revision_instructions is required (not Optional)."""
        payload = _valid_refinement_payload()
        del payload["revision_instructions"]
        with pytest.raises(ValidationError):
            RefinementResult(**payload)


# ===========================================================================
# RunRecord
# ===========================================================================


class TestRunRecord:
    def test_valid_minimal_record(self):
        record = RunRecord(**_valid_run_record_payload())
        assert record.terminal_state == "PASS"
        assert record.condition == "verifier_guided"
        assert record.run_id  # auto-generated UUID
        assert record.created_at  # auto-set timestamp
        assert record.iterations == []  # default

    def test_valid_baseline_direct_condition(self):
        record = RunRecord(**_valid_run_record_payload(condition="baseline_direct"))
        assert record.condition == "baseline_direct"

    def test_valid_rejected_unsafe_state(self):
        record = RunRecord(
            **_valid_run_record_payload(terminal_state="REJECTED_UNSAFE")
        )
        assert record.terminal_state == "REJECTED_UNSAFE"

    def test_valid_generated_unverified_state(self):
        record = RunRecord(
            **_valid_run_record_payload(
                condition="baseline_direct",
                terminal_state="GENERATED_UNVERIFIED",
            )
        )
        assert record.terminal_state == "GENERATED_UNVERIFIED"

    def test_valid_with_iteration_dicts(self):
        """iterations is list[dict] — any dict shape is accepted at schema level."""
        iterations = [
            {
                "simulation": {"subject": "Test"},
                "safety_result": {"status": "PASS"},
                "verification": {"overall_score": 72.0},
                "score": 72.0,
                "refinement": {"iteration_number": 1},
            }
        ]
        record = RunRecord(**_valid_run_record_payload(iterations=iterations))
        assert len(record.iterations) == 1
        assert record.iterations[0]["score"] == 72.0

    def test_invalid_terminal_state_value(self):
        with pytest.raises(ValidationError):
            RunRecord(**_valid_run_record_payload(terminal_state="TIMEOUT"))

    def test_invalid_condition_value(self):
        with pytest.raises(ValidationError):
            RunRecord(**_valid_run_record_payload(condition="manual_run"))

    def test_run_id_is_unique_across_instances(self):
        r1 = RunRecord(**_valid_run_record_payload())
        r2 = RunRecord(**_valid_run_record_payload())
        assert r1.run_id != r2.run_id

    def test_invalid_missing_scenario(self):
        payload = _valid_run_record_payload()
        del payload["scenario"]
        with pytest.raises(ValidationError):
            RunRecord(**payload)

    def test_invalid_missing_condition(self):
        payload = _valid_run_record_payload()
        del payload["condition"]
        with pytest.raises(ValidationError):
            RunRecord(**payload)


# ===========================================================================
# Example scenario files round-trip
# ===========================================================================


class TestExampleScenarioFiles:
    """Verify each example JSON file validates cleanly as a ScenarioSpecification."""

    EXAMPLES_DIR = os.path.join(
        os.path.dirname(__file__),  # tests/unit/
        "..",                        # tests/
        "..",                        # phishforge/
        "scenarios",
        "examples",
    )

    def _load_example(self, filename: str) -> ScenarioSpecification:
        path = os.path.join(self.EXAMPLES_DIR, filename)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return ScenarioSpecification(**data)

    def test_finance_invoice_fraud_loads(self):
        spec = self._load_example("finance_invoice_fraud.json")
        assert spec.target_role == "finance"
        assert spec.scenario_type == "invoice_fraud"
        assert spec.difficulty == 3

    def test_hr_policy_update_loads(self):
        spec = self._load_example("hr_policy_update.json")
        assert spec.target_role == "hr"
        assert spec.scenario_type == "internal_policy_update"
        assert spec.difficulty == 2

    def test_executive_wire_transfer_loads(self):
        """difficulty was 5 (invalid) — now corrected to 4 (max valid)."""
        spec = self._load_example("executive_wire_transfer.json")
        assert spec.target_role == "executive"
        assert spec.difficulty == 4
        assert spec.difficulty in (1, 2, 3, 4)  # explicit range check

    def test_all_examples_have_non_empty_desired_indicators(self):
        for filename in (
            "finance_invoice_fraud.json",
            "hr_policy_update.json",
            "executive_wire_transfer.json",
        ):
            spec = self._load_example(filename)
            assert len(spec.desired_indicators) >= 1, (
                f"{filename}: desired_indicators must not be empty"
            )
