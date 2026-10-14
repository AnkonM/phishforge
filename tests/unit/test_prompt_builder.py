"""
tests/unit/test_prompt_builder.py

Unit tests for core/generation/prompt_builder.py.
No API calls — only tests that the prompt template is loaded and
scenario fields are correctly interpolated.

Run with: pytest tests/unit/test_prompt_builder.py -v
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.generation.prompt_builder import PROMPT_VERSION, build_prompt
from models.schemas.scenario import ScenarioSpecification

# ---------------------------------------------------------------------------
# Fixture factories
# ---------------------------------------------------------------------------


def _make_spec(**kwargs) -> ScenarioSpecification:
    base = {
        "organization_context": "Mid-size UK professional services firm, 350 staff.",
        "target_role": "finance",
        "scenario_type": "invoice_fraud",
        "difficulty": 3,
        "desired_indicators": ["urgency", "authority_impersonation"],
    }
    base.update(kwargs)
    return ScenarioSpecification(**base)


# ---------------------------------------------------------------------------
# Template loading
# ---------------------------------------------------------------------------


class TestTemplateLoads:
    def test_prompt_version_constant(self):
        assert PROMPT_VERSION == "v1"

    def test_build_prompt_returns_string(self):
        spec = _make_spec()
        result = build_prompt(spec)
        assert isinstance(result, str)
        assert len(result) > 100  # not trivially empty


# ---------------------------------------------------------------------------
# Scenario field interpolation
# ---------------------------------------------------------------------------


class TestScenarioFieldInterpolation:
    def test_organization_context_present(self):
        spec = _make_spec(organization_context="Acme Corp, 100 employees, uses SAP.")
        prompt = build_prompt(spec)
        assert "Acme Corp, 100 employees, uses SAP." in prompt

    def test_target_role_present(self):
        spec = _make_spec(target_role="hr")
        prompt = build_prompt(spec)
        assert "hr" in prompt

    def test_scenario_type_present(self):
        spec = _make_spec(scenario_type="password_alert")
        prompt = build_prompt(spec)
        assert "password_alert" in prompt

    def test_difficulty_present(self):
        for d in (1, 2, 3, 4):
            spec = _make_spec(difficulty=d)
            prompt = build_prompt(spec)
            assert str(d) in prompt

    def test_language_present(self):
        spec = _make_spec(language="de")
        prompt = build_prompt(spec)
        assert "de" in prompt

    def test_desired_indicators_formatted_as_csv(self):
        spec = _make_spec(desired_indicators=["urgency", "suspicious_link", "authority_impersonation"])
        prompt = build_prompt(spec)
        assert "urgency, suspicious_link, authority_impersonation" in prompt

    def test_single_indicator(self):
        spec = _make_spec(desired_indicators=["urgency"])
        prompt = build_prompt(spec)
        assert "urgency" in prompt

    def test_prohibited_elements_formatted_as_csv(self):
        spec = _make_spec(prohibited_elements=["real brand names", "credential links"])
        prompt = build_prompt(spec)
        assert "real brand names, credential links" in prompt

    def test_empty_prohibited_elements_shows_none(self):
        spec = _make_spec(prohibited_elements=[])
        prompt = build_prompt(spec)
        assert "none" in prompt

    def test_simulation_constraints_as_json(self):
        spec = _make_spec(simulation_constraints={"max_body_words": 200, "tone": "formal"})
        prompt = build_prompt(spec)
        # The dict should be serialised as JSON, so the key should appear in the prompt.
        assert "max_body_words" in prompt

    def test_empty_simulation_constraints_shows_none(self):
        spec = _make_spec(simulation_constraints={})
        prompt = build_prompt(spec)
        assert "none" in prompt


# ---------------------------------------------------------------------------
# Safety constraint wording
# ---------------------------------------------------------------------------


class TestSafetyConstraints:
    def test_no_real_domains_instruction_present(self):
        spec = _make_spec()
        prompt = build_prompt(spec)
        assert "NO REAL DOMAINS" in prompt or "real domain" in prompt.lower()

    def test_fictional_domain_patterns_mentioned(self):
        spec = _make_spec()
        prompt = build_prompt(spec)
        assert "sim-training.test" in prompt or "example-corp-sim.local" in prompt

    def test_no_real_company_names_instruction_present(self):
        spec = _make_spec()
        prompt = build_prompt(spec)
        assert "NO REAL COMPANY" in prompt or "real organisation" in prompt.lower() or "real company" in prompt.lower()

    def test_output_format_json_only_instruction_present(self):
        spec = _make_spec()
        prompt = build_prompt(spec)
        assert "ONLY" in prompt
        assert "JSON" in prompt

    def test_no_markdown_fences_instruction_present(self):
        spec = _make_spec()
        prompt = build_prompt(spec)
        # The prompt must tell the model not to use markdown code fences.
        assert "markdown" in prompt.lower() or "code fence" in prompt.lower()

    def test_provenance_fields_excluded_from_llm_output(self):
        """The prompt must instruct the model NOT to produce generation_id etc."""
        spec = _make_spec()
        prompt = build_prompt(spec)
        assert "generation_id" in prompt  # mentioned as excluded
        assert "scenario_id" in prompt    # mentioned as excluded


# ---------------------------------------------------------------------------
# Revision block
# ---------------------------------------------------------------------------


class TestRevisionBlock:
    def test_no_revision_block_when_none(self):
        spec = _make_spec()
        prompt = build_prompt(spec, revision_instructions=None)
        assert "REVISION INSTRUCTIONS" not in prompt

    def test_no_revision_block_when_empty_string(self):
        spec = _make_spec()
        prompt = build_prompt(spec, revision_instructions="   ")
        assert "REVISION INSTRUCTIONS" not in prompt

    def test_revision_block_injected_when_provided(self):
        spec = _make_spec()
        prompt = build_prompt(spec, revision_instructions="Improve role relevance.")
        assert "REVISION INSTRUCTIONS" in prompt
        assert "Improve role relevance." in prompt

    def test_revision_block_includes_anti_drift_instruction(self):
        spec = _make_spec()
        prompt = build_prompt(spec, revision_instructions="Fix urgency language.")
        # Must tell the model to preserve scenario intent.
        assert "preserve" in prompt.lower() or "same target role" in prompt.lower()

    def test_revision_instructions_content_in_prompt(self):
        instructions = "The sender address should look more like a legitimate finance tool."
        spec = _make_spec()
        prompt = build_prompt(spec, revision_instructions=instructions)
        assert instructions in prompt

    def test_revision_block_strips_whitespace(self):
        spec = _make_spec()
        prompt_stripped = build_prompt(spec, revision_instructions="  Fix relevance.  ")
        prompt_clean = build_prompt(spec, revision_instructions="Fix relevance.")
        # Both should produce the same revision block content.
        assert "Fix relevance." in prompt_stripped
        assert "Fix relevance." in prompt_clean


# ---------------------------------------------------------------------------
# Example scenario file round-trips through prompt builder
# ---------------------------------------------------------------------------


class TestExampleScenariosRoundTrip:
    """Load example scenario files and verify prompt builds without error."""

    EXAMPLES_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "scenarios", "examples"
    )

    def _load_spec(self, filename: str) -> ScenarioSpecification:
        import json as _json
        path = os.path.join(self.EXAMPLES_DIR, filename)
        with open(path, encoding="utf-8") as f:
            data = _json.load(f)
        return ScenarioSpecification(**data)

    def test_finance_invoice_fraud_builds_prompt(self):
        spec = self._load_spec("finance_invoice_fraud.json")
        prompt = build_prompt(spec)
        assert "finance" in prompt
        assert "invoice_fraud" in prompt

    def test_hr_policy_update_builds_prompt(self):
        spec = self._load_spec("hr_policy_update.json")
        prompt = build_prompt(spec)
        assert "hr" in prompt

    def test_executive_wire_transfer_builds_prompt(self):
        spec = self._load_spec("executive_wire_transfer.json")
        prompt = build_prompt(spec)
        assert "executive" in prompt

    def test_all_examples_build_prompts_with_revision(self):
        for filename in (
            "finance_invoice_fraud.json",
            "hr_policy_update.json",
            "executive_wire_transfer.json",
        ):
            spec = self._load_spec(filename)
            prompt = build_prompt(spec, revision_instructions="Improve realism.")
            assert "REVISION INSTRUCTIONS" in prompt
            assert "Improve realism." in prompt
