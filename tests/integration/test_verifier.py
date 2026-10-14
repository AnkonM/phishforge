"""
tests/integration/test_verifier.py

Integration tests for the Hybrid Verifier (core/verification/verifier.py)
and Layer B LLM Judge (core/verification/llm_judge.py) using mocked LLM responses.

Zero real API calls are made in this automated suite.

Run with: pytest tests/integration/test_verifier.py -v
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.verification.llm_judge import VerificationFailure, run_llm_judge
from core.verification.verifier import VERIFIER_VERSION, verify
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation
from models.schemas.verification import VerificationResult

# ---------------------------------------------------------------------------
# Helpers & Mocks
# ---------------------------------------------------------------------------


def _make_spec(**kwargs) -> ScenarioSpecification:
    base = {
        "organization_context": "Mid-size law firm, 150 staff. Finance uses SAP.",
        "target_role": "finance",
        "scenario_type": "invoice_fraud",
        "difficulty": 3,
        "desired_indicators": ["urgency", "authority_impersonation", "suspicious_link"],
    }
    base.update(kwargs)
    return ScenarioSpecification(**base)


def _make_sim(**kwargs) -> GeneratedSimulation:
    base = {
        "generation_id": str(uuid.uuid4()),
        "scenario_id": str(uuid.uuid4()),
        "subject": "URGENT: Overdue Invoice #INV-8821 Payment Required",
        "sender": "Finance Director <fd@apex-legal-sim.local>",
        "body": (
            "Dear Finance Team,\n\n"
            "Invoice #INV-8821 is past due and requires immediate authorization. "
            "Please review and submit sign-off via [SIMULATED LINK: SAP AP Portal].\n\n"
            "Regards,\nFinance Director"
        ),
        "intended_indicators": ["urgency", "authority_impersonation", "suspicious_link"],
        "metadata": {"tone": "formal"},
        "model": "models/gemini-3.6-flash",
        "prompt_version": "v1",
        "timestamp": datetime.now(timezone.utc),
    }
    base.update(kwargs)
    return GeneratedSimulation(**base)


def _valid_llm_judge_json() -> str:
    return json.dumps({
        "realism_score": 85.0,
        "relevance_score": 90.0,
        "difficulty_score": 88.0,
        "assessed_difficulty": 3,
        "difficulty_rationale": "Matches level 3 well with subtle domain indicator.",
        "semantic_findings": [
            "The urgency phrasing is slightly direct for an executive sender."
        ],
    })


def _make_mock_client(responses: list[str]) -> MagicMock:
    client = MagicMock()
    side_effects = []
    for text in responses:
        resp = MagicMock()
        resp.text = text
        side_effects.append(resp)
    client.models.generate_content.side_effect = side_effects
    return client


# ===========================================================================
# 1. Full Hybrid Verifier Integration
# ===========================================================================


class TestHybridVerifierMerge:
    def test_verify_returns_valid_verification_result(self):
        spec = _make_spec()
        sim = _make_sim()
        mock_client = _make_mock_client([_valid_llm_judge_json()])

        result = verify(spec, sim, _client=mock_client)

        assert isinstance(result, VerificationResult)
        assert result.generation_id == sim.generation_id
        assert result.realism_score == 85.0
        assert result.relevance_score == 90.0
        assert result.difficulty_score == 88.0
        assert result.indicator_score == 100.0
        assert result.language_score == 100.0
        assert result.safety_status == "PASS"
        assert result.safety_findings == []
        assert result.verifier_version == VERIFIER_VERSION
        assert len(result.semantic_findings) >= 1
        assert "urgency phrasing" in result.semantic_findings[0].lower()

    def test_findings_deduplication_and_merging(self):
        spec = _make_spec(prohibited_elements=["forbidden_phrase"])
        sim = _make_sim(body="Here is a forbidden_phrase in text.")
        mock_client = _make_mock_client([_valid_llm_judge_json()])

        result = verify(spec, sim, _client=mock_client)

        # Should contain findings from both Layer A (prohibited element) and Layer B (LLM critique)
        findings_text = " ".join(result.semantic_findings)
        assert "forbidden_phrase" in findings_text
        assert "urgency phrasing" in findings_text


# ===========================================================================
# 2. Layer B Repair Retry & Exception Handling
# ===========================================================================


class TestLayerBJudgeRetryAndFailure:
    def test_layer_b_recovers_after_retry(self):
        spec = _make_spec()
        sim = _make_sim()
        mock_client = _make_mock_client([
            "bad response not json",
            _valid_llm_judge_json(),
        ])

        result = run_llm_judge(spec, sim, _client=mock_client)
        assert result.realism_score == 85.0
        assert result.relevance_score == 90.0
        assert mock_client.models.generate_content.call_count == 2

    def test_layer_b_fails_after_exhausted_retry(self):
        spec = _make_spec()
        sim = _make_sim()
        mock_client = _make_mock_client([
            "bad response 1",
            "bad response 2",
        ])

        with pytest.raises(VerificationFailure) as exc_info:
            run_llm_judge(spec, sim, _client=mock_client)

        assert "Verifier Layer B failed" in str(exc_info.value)
        assert mock_client.models.generate_content.call_count == 2
