"""
tests/unit/test_rule_checks.py

Unit tests for Layer A deterministic rule checks (core/verification/rule_checks.py).
Zero LLM calls, deterministic execution.

Run with: pytest tests/unit/test_rule_checks.py -v
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.verification.rule_checks import (
    LayerAResult,
    check_indicators,
    check_prohibited_elements,
    check_structural_and_language,
    run_rule_checks,
)
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation

# ---------------------------------------------------------------------------
# Fixture Helpers
# ---------------------------------------------------------------------------


def _make_spec(**kwargs) -> ScenarioSpecification:
    base = {
        "organization_context": "Mid-size law firm, 150 staff. Finance uses SAP.",
        "target_role": "finance",
        "scenario_type": "invoice_fraud",
        "difficulty": 3,
        "desired_indicators": ["urgency", "authority_impersonation", "suspicious_link"],
        "prohibited_elements": ["real bank names"],
        "simulation_constraints": {},
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


# ===========================================================================
# 1. Indicator Presence Check
# ===========================================================================


class TestIndicatorChecks:
    def test_all_desired_indicators_detected(self):
        spec = _make_spec(desired_indicators=["urgency", "authority_impersonation", "suspicious_link"])
        sim = _make_sim()
        score, findings = check_indicators(spec, sim)
        assert score == 100.0
        assert findings == []

    def test_missing_indicator_produces_finding_and_deduction(self):
        spec = _make_spec(desired_indicators=["urgency", "delivery_expense_pretext"])
        sim = _make_sim(
            subject="Standard AP Notification",
            body="Dear Colleague,\n\nPlease review the invoice at your convenience.\n\nRegards,\nAP Team",
            intended_indicators=["urgency"],
        )
        score, findings = check_indicators(spec, sim)
        assert score < 100.0
        assert len(findings) >= 1
        assert any("delivery_expense_pretext" in f for f in findings)


# ===========================================================================
# 2. Prohibited Elements Check
# ===========================================================================


class TestProhibitedElementsCheck:
    def test_no_prohibited_elements_passes(self):
        spec = _make_spec(prohibited_elements=["chase bank", "paypal"])
        sim = _make_sim()
        findings = check_prohibited_elements(spec, sim)
        assert findings == []

    def test_prohibited_element_detected(self):
        spec = _make_spec(prohibited_elements=["chase bank"])
        sim = _make_sim(body="Please wire funds to Chase Bank immediately.")
        findings = check_prohibited_elements(spec, sim)
        assert len(findings) == 1
        assert "chase bank" in findings[0].lower()


# ===========================================================================
# 3. Structural & Language Check
# ===========================================================================


class TestStructuralAndLanguageCheck:
    def test_clean_structure_and_english_passes(self):
        spec = _make_spec(language="en")
        sim = _make_sim()
        score, findings = check_structural_and_language(spec, sim)
        assert score == 100.0
        assert findings == []

    def test_missing_subject_penalized(self):
        spec = _make_spec()
        sim = _make_sim(subject="Hi")
        score, findings = check_structural_and_language(spec, sim)
        assert score < 100.0
        assert any("Subject line" in f for f in findings)

    def test_malformed_sender_penalized(self):
        spec = _make_spec()
        sim = _make_sim(sender="InvalidSenderWithoutAtSign")
        score, findings = check_structural_and_language(spec, sim)
        assert score < 100.0
        assert any("Sender field" in f for f in findings)


# ===========================================================================
# 4. End-to-End Layer A Run with Live Smoke Test Output
# ===========================================================================


class TestRunRuleChecksIntegration:
    def test_real_live_smoke_output_passes_rule_checks(self):
        output_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "smoke_test_output.json"
        )
        assert os.path.exists(output_path), "smoke_test_output.json required"

        with open(output_path, "r", encoding="utf-8") as f:
            sim_data = json.load(f)

        spec = ScenarioSpecification(
            organization_context="Mid-size UK firm. Finance uses SAP. £10k dual approval.",
            target_role="finance",
            scenario_type="invoice_fraud",
            difficulty=3,
            desired_indicators=["urgency", "authority_impersonation", "suspicious_link"],
        )
        sim = GeneratedSimulation(**sim_data)

        result = run_rule_checks(spec, sim)
        assert isinstance(result, LayerAResult)
        assert result.indicator_score == 100.0
        assert result.language_score == 100.0
        assert result.rule_findings == []
