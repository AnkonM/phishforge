"""
tests/integration/test_generator.py

Integration tests for core/generation/generator.py using a mocked
Gemini client (via llm_client.call_llm). No real API calls are made.

Three scenarios tested:
  (a) Successful first-try parse
  (b) Failure on first try, successful repair retry
  (c) Failure on both tries -- raises GenerationFailure

Run with: pytest tests/integration/test_generator.py -v
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.generation.generator import GenerationFailure, generate
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_spec(**kwargs) -> ScenarioSpecification:
    base = {
        "organization_context": "Mock Corp, 100 employees.",
        "target_role": "finance",
        "scenario_type": "invoice_fraud",
        "difficulty": 2,
        "desired_indicators": ["urgency", "suspicious_link"],
    }
    base.update(kwargs)
    return ScenarioSpecification(**base)


def _valid_llm_json_response(spec: ScenarioSpecification | None = None) -> str:
    """Return a JSON string that represents a valid LLM payload (no provenance fields)."""
    return json.dumps({
        "subject": "URGENT: Invoice #INV-2024-001 requires your approval",
        "sender": "AP System <ap-system@mock-corp-sim.sim-training.test>",
        "body": (
            "Dear Finance Team,\n\n"
            "An invoice requires your immediate approval. "
            "Please click [SIMULATED LINK: invoice approval portal] to review.\n\n"
            "Regards,\nMock AP System"
        ),
        "intended_indicators": ["urgency", "suspicious_link"],
        "metadata": {
            "difficulty_rationale": "Urgency language is present but not extreme for difficulty 2.",
            "tone": "semi-formal",
            "scenario_notes": "None.",
        },
    })


def _make_mock_client(responses: list[str]) -> MagicMock:
    """
    Build a mock Gemini client whose models.generate_content returns successive
    responses from the `responses` list.

    Each response is wrapped in a mock object that matches the shape
    client.models.generate_content(...).text
    (which is what llm_client.call_llm reads).
    """
    client = MagicMock()
    side_effects = []
    for text in responses:
        response_mock = MagicMock()
        response_mock.text = text
        side_effects.append(response_mock)
    client.models.generate_content.side_effect = side_effects
    return client


# ===========================================================================
# (a) Successful first-try parse
# ===========================================================================


class TestSuccessfulFirstTry:
    def test_returns_generated_simulation(self):
        spec = _make_spec()
        mock_client = _make_mock_client([_valid_llm_json_response(spec)])

        result = generate(spec, _client=mock_client)

        assert isinstance(result, GeneratedSimulation)

    def test_subject_preserved(self):
        spec = _make_spec()
        mock_client = _make_mock_client([_valid_llm_json_response(spec)])
        result = generate(spec, _client=mock_client)
        assert "Invoice" in result.subject or "invoice" in result.subject.lower()

    def test_provenance_fields_populated_by_code(self):
        """generation_id, scenario_id, model, prompt_version, timestamp must be set in code."""
        spec = _make_spec()
        mock_client = _make_mock_client([_valid_llm_json_response(spec)])
        result = generate(spec, _client=mock_client)

        assert result.generation_id  # non-empty UUID
        assert result.scenario_id == spec.scenario_id
        assert result.model  # non-empty model name
        assert result.prompt_version == "v1"
        assert result.timestamp is not None

    def test_scenario_id_matches_spec(self):
        spec = _make_spec()
        mock_client = _make_mock_client([_valid_llm_json_response(spec)])
        result = generate(spec, _client=mock_client)
        assert result.scenario_id == spec.scenario_id

    def test_generation_id_is_unique_per_call(self):
        spec = _make_spec()
        mock_client = _make_mock_client([
            _valid_llm_json_response(spec),
            _valid_llm_json_response(spec),
        ])
        r1 = generate(spec, _client=mock_client)
        r2 = generate(spec, _client=mock_client)
        assert r1.generation_id != r2.generation_id

    def test_api_called_exactly_once_on_success(self):
        spec = _make_spec()
        mock_client = _make_mock_client([_valid_llm_json_response(spec)])
        generate(spec, _client=mock_client)
        assert mock_client.models.generate_content.call_count == 1

    def test_with_revision_instructions(self):
        spec = _make_spec()
        mock_client = _make_mock_client([_valid_llm_json_response(spec)])
        result = generate(spec, revision_instructions="Improve role relevance.", _client=mock_client)
        assert isinstance(result, GeneratedSimulation)

    def test_intended_indicators_preserved(self):
        spec = _make_spec()
        mock_client = _make_mock_client([_valid_llm_json_response(spec)])
        result = generate(spec, _client=mock_client)
        assert isinstance(result.intended_indicators, list)
        assert len(result.intended_indicators) > 0


# ===========================================================================
# (b) Failure on first try, successful repair retry
# ===========================================================================


class TestRepairRetrySuccess:
    def test_returns_valid_simulation_after_retry(self):
        spec = _make_spec()
        mock_client = _make_mock_client([
            "This is not JSON at all.",          # first response — bad
            _valid_llm_json_response(spec),       # repair retry — good
        ])
        result = generate(spec, _client=mock_client)
        assert isinstance(result, GeneratedSimulation)

    def test_api_called_twice_on_repair(self):
        spec = _make_spec()
        mock_client = _make_mock_client([
            "not json",
            _valid_llm_json_response(spec),
        ])
        generate(spec, _client=mock_client)
        assert mock_client.models.generate_content.call_count == 2

    def test_repair_retry_on_invalid_json_schema(self):
        """Response is valid JSON but missing required fields — triggers repair."""
        spec = _make_spec()
        bad_json = json.dumps({"subject": "Only subject, missing everything else"})
        mock_client = _make_mock_client([
            bad_json,
            _valid_llm_json_response(spec),
        ])
        result = generate(spec, _client=mock_client)
        assert isinstance(result, GeneratedSimulation)

    def test_repair_retry_on_json_with_markdown_fence(self):
        """LLM wraps JSON in a markdown code block — triggers repair."""
        spec = _make_spec()
        fenced = "```json\n" + _valid_llm_json_response(spec) + "\n```"
        mock_client = _make_mock_client([
            fenced,
            _valid_llm_json_response(spec),
        ])
        result = generate(spec, _client=mock_client)
        assert isinstance(result, GeneratedSimulation)

    def test_provenance_fields_populated_after_retry(self):
        spec = _make_spec()
        mock_client = _make_mock_client([
            "bad first response",
            _valid_llm_json_response(spec),
        ])
        result = generate(spec, _client=mock_client)
        assert result.scenario_id == spec.scenario_id
        assert result.prompt_version == "v1"


# ===========================================================================
# (c) Both tries fail — raises GenerationFailure
# ===========================================================================


class TestBothTriesFail:
    def test_raises_generation_failure(self):
        spec = _make_spec()
        mock_client = _make_mock_client([
            "not json at all",
            "still not json",
        ])
        with pytest.raises(GenerationFailure):
            generate(spec, _client=mock_client)

    def test_generation_failure_has_reason(self):
        spec = _make_spec()
        mock_client = _make_mock_client([
            "bad response 1",
            "bad response 2",
        ])
        with pytest.raises(GenerationFailure) as exc_info:
            generate(spec, _client=mock_client)
        assert exc_info.value.reason  # non-empty string

    def test_generation_failure_carries_raw_response(self):
        """The raw_response attribute should hold the last failed response."""
        spec = _make_spec()
        mock_client = _make_mock_client([
            "bad response 1",
            "bad response 2",
        ])
        with pytest.raises(GenerationFailure) as exc_info:
            generate(spec, _client=mock_client)
        assert exc_info.value.raw_response == "bad response 2"

    def test_api_called_exactly_twice_before_raising(self):
        spec = _make_spec()
        mock_client = _make_mock_client([
            "bad response 1",
            "bad response 2",
        ])
        with pytest.raises(GenerationFailure):
            generate(spec, _client=mock_client)
        assert mock_client.models.generate_content.call_count == 2

    def test_raises_on_empty_json_object(self):
        """An empty JSON object {} is missing required fields — both retries fail."""
        spec = _make_spec()
        mock_client = _make_mock_client(["{}", "{}"])
        with pytest.raises(GenerationFailure):
            generate(spec, _client=mock_client)

    def test_raises_on_json_array_instead_of_object(self):
        spec = _make_spec()
        mock_client = _make_mock_client(["[]", "[]"])
        with pytest.raises(GenerationFailure):
            generate(spec, _client=mock_client)


# ===========================================================================
# Missing API key
# ===========================================================================


class TestMissingApiKey:
    def test_raises_generation_failure_when_no_key_and_no_client(self):
        """Without a _client and without a GEMINI_API_KEY, generate() must raise GenerationFailure."""
        spec = _make_spec()
        # Patch the attribute as seen by generator.py (which does `import config`).
        with patch.object(__import__("config"), "GEMINI_API_KEY", None), patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            with pytest.raises(GenerationFailure) as exc_info:
                generate(spec)  # no _client passed
        assert "GEMINI_API_KEY" in exc_info.value.reason
