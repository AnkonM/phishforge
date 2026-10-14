"""
tests/unit/test_cli_args.py

Unit tests for PhishForge CLI argument parsing and ScenarioSpecification construction.

Run with: pytest tests/unit/test_cli_args.py -v
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from cli import _build_parser, build_scenario_from_args
from models.schemas.scenario import ScenarioSpecification

# ---------------------------------------------------------------------------
# Test CLI Argument Parsing and Scenario Building
# ---------------------------------------------------------------------------


class TestCliScenarioBuilder:
    def test_build_scenario_from_flags_only(self):
        parser = _build_parser()
        args = parser.parse_args([
            "run",
            "--role", "finance",
            "--scenario-type", "invoice_fraud",
            "--difficulty", "3",
            "--indicators", "urgency, authority_impersonation",
            "--org-context", "Mid-size accounting firm.",
            "--language", "en",
            "--prohibited", "real domains, live credentials",
            "--constraints", '{"max_words": 150}',
        ])

        spec = build_scenario_from_args(args)
        assert isinstance(spec, ScenarioSpecification)
        assert spec.target_role == "finance"
        assert spec.scenario_type == "invoice_fraud"
        assert spec.difficulty == 3
        assert spec.desired_indicators == ["urgency", "authority_impersonation"]
        assert spec.organization_context == "Mid-size accounting firm."
        assert spec.language == "en"
        assert spec.prohibited_elements == ["real domains", "live credentials"]
        assert spec.simulation_constraints == {"max_words": 150}

    def test_build_scenario_from_input_file_only(self, tmp_path):
        scenario_data = {
            "organization_context": "Tech startup, 50 employees.",
            "target_role": "it",
            "scenario_type": "password_alert",
            "difficulty": 2,
            "desired_indicators": ["urgency", "suspicious_link"],
        }
        file_path = tmp_path / "test_scenario.json"
        file_path.write_text(json.dumps(scenario_data), encoding="utf-8")

        parser = _build_parser()
        args = parser.parse_args(["run", "--input", str(file_path)])

        spec = build_scenario_from_args(args)
        assert isinstance(spec, ScenarioSpecification)
        assert spec.target_role == "it"
        assert spec.scenario_type == "password_alert"
        assert spec.difficulty == 2
        assert spec.desired_indicators == ["urgency", "suspicious_link"]
        assert spec.organization_context == "Tech startup, 50 employees."

    def test_flags_override_input_file_fields(self, tmp_path):
        scenario_data = {
            "organization_context": "Original Org Context",
            "target_role": "hr",
            "scenario_type": "hr_document_request",
            "difficulty": 1,
            "desired_indicators": ["urgency"],
        }
        file_path = tmp_path / "test_scenario.json"
        file_path.write_text(json.dumps(scenario_data), encoding="utf-8")

        parser = _build_parser()
        args = parser.parse_args([
            "run",
            "--input", str(file_path),
            "--role", "executive",
            "--difficulty", "4",
            "--indicators", "wire_transfer, executive_pressure",
        ])

        spec = build_scenario_from_args(args)
        # Overridden fields
        assert spec.target_role == "executive"
        assert spec.difficulty == 4
        assert spec.desired_indicators == ["wire_transfer", "executive_pressure"]
        # Preserved file fields
        assert spec.scenario_type == "hr_document_request"
        assert spec.organization_context == "Original Org Context"

    def test_missing_required_fields_raises_error(self):
        parser = _build_parser()
        # Missing role, difficulty, indicators, org-context
        args = parser.parse_args([
            "run",
            "--scenario-type", "invoice_fraud",
        ])

        with pytest.raises(ValueError) as exc_info:
            build_scenario_from_args(args)
        err_msg = str(exc_info.value)
        assert "Missing required scenario specification field(s)" in err_msg
        assert "--role" in err_msg
        assert "--difficulty" in err_msg
        assert "--indicators" in err_msg
        assert "--org-context" in err_msg

    def test_nonexistent_input_file_raises_error(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "--input", "nonexistent_file_xyz.json"])

        with pytest.raises(ValueError) as exc_info:
            build_scenario_from_args(args)
        assert "Input scenario file not found" in str(exc_info.value)

    def test_invalid_constraints_json_raises_error(self):
        parser = _build_parser()
        args = parser.parse_args([
            "run",
            "--role", "finance",
            "--scenario-type", "invoice_fraud",
            "--difficulty", "3",
            "--indicators", "urgency",
            "--org-context", "Mid-size firm.",
            "--constraints", "{invalid_json}",
        ])

        with pytest.raises(ValueError) as exc_info:
            build_scenario_from_args(args)
        assert "Invalid JSON in --constraints" in str(exc_info.value)

    def test_invalid_difficulty_choice_rejected_by_parser(self):
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["run", "--difficulty", "5"])  # Choices are 1, 2, 3, 4

    def test_demo_unsafe_flag_parsed(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "--input", "some_path.json", "--demo-unsafe"])
        assert args.demo_unsafe is True
