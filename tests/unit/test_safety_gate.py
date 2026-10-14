"""
tests/unit/test_safety_gate.py

Comprehensive unit tests for the deterministic Safety Gate (Phase 3).
Highest-priority test file in PhishForge per Document B risk assessment.

Test Coverage:
  1. Individual rule tests (trigger vs pass for each rule)
  2. Real live smoke-test output validation (must pass)
  3. Multi-rule aggregation test (verifies no short-circuiting)
  4. Fail-closed behavior test (exception handling returns FAIL)

Run with: pytest tests/unit/test_safety_gate.py -v
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.safety.safety_gate import (
    SafetyCheckResult,
    check,
    check_no_attachment_payloads,
    check_no_credential_harvesting,
    check_no_real_brand_impersonation,
    check_no_real_domains,
    check_no_real_pii,
)
from models.schemas.simulation import GeneratedSimulation

# ---------------------------------------------------------------------------
# Helpers & Fixture Factories
# ---------------------------------------------------------------------------


def _make_sim(**kwargs) -> GeneratedSimulation:
    """Construct a clean, valid simulation fixture."""
    base = {
        "generation_id": str(uuid.uuid4()),
        "scenario_id": str(uuid.uuid4()),
        "subject": "Action Required: Quarterly Vendor Invoice #INV-2024",
        "sender": "Accounts Payable <ap-notify@finance.sim-training.test>",
        "body": (
            "Dear Colleague,\n\n"
            "Please review the attached quarterly invoice for compliance.\n"
            "Submit confirmation via [SIMULATED LINK: Internal SAP Confirmation Portal].\n\n"
            "Thank you,\nFinance Department"
        ),
        "intended_indicators": ["urgency", "authority_impersonation"],
        "metadata": {"tone": "formal"},
        "model": "models/gemini-3.6-flash",
        "prompt_version": "v1",
        "timestamp": datetime.now(timezone.utc),
    }
    base.update(kwargs)
    return GeneratedSimulation(**base)


# ===========================================================================
# 1. Rule 1: No Real Domains
# ===========================================================================


class TestNoRealDomainsRule:
    def test_clean_synthetic_domains_pass(self):
        sim = _make_sim(
            sender="Billing <billing@apex-corp-sim.local>",
            body="Review your portal at [SIMULATED LINK: https://portal.apex-corp-sim.local/view]",
        )
        findings = check_no_real_domains(sim)
        assert findings == []

    def test_real_domain_in_sender_triggers_finding(self):
        sim = _make_sim(
            sender="Accounts <billing@company-payroll.com>",
        )
        findings = check_no_real_domains(sim)
        assert len(findings) >= 1
        assert any("company-payroll.com" in f for f in findings)

    def test_real_domain_in_url_triggers_finding(self):
        sim = _make_sim(
            body="Please log in at https://secure-login.suspicious-bank.com/verify to continue.",
        )
        findings = check_no_real_domains(sim)
        assert len(findings) >= 1
        assert any("suspicious-bank.com" in f for f in findings)

    def test_standalone_real_tld_in_body_triggers_finding(self):
        sim = _make_sim(
            body="Visit www.verify-invoice-now.net for urgent verification.",
        )
        findings = check_no_real_domains(sim)
        assert len(findings) >= 1
        assert any("verify-invoice-now.net" in f for f in findings)


# ===========================================================================
# 2. Rule 2: No Direct Credential Harvesting
# ===========================================================================


class TestNoCredentialHarvestingRule:
    def test_clean_body_passes(self):
        sim = _make_sim(
            body="Please acknowledge the policy update on your internal portal.",
        )
        findings = check_no_credential_harvesting(sim)
        assert findings == []

    def test_soliciting_plain_text_password_triggers_finding(self):
        sim = _make_sim(
            body="To keep your account active, please reply with your password immediately.",
        )
        findings = check_no_credential_harvesting(sim)
        assert len(findings) >= 1
        assert any("reply with your password" in f for f in findings)

    def test_soliciting_pin_triggers_finding(self):
        sim = _make_sim(
            body="For security verification, reply with your PIN to the sender.",
        )
        findings = check_no_credential_harvesting(sim)
        assert len(findings) >= 1
        assert any("reply with your pin" in f for f in findings)


# ===========================================================================
# 3. Rule 3: No Dangerous Attachment Payloads
# ===========================================================================


class TestNoAttachmentPayloadsRule:
    def test_safe_non_executable_attachment_passes(self):
        sim = _make_sim(
            body="Please find attached invoice_summary.pdf for your records.",
        )
        findings = check_no_attachment_payloads(sim)
        assert findings == []

    def test_executable_extension_triggers_finding(self):
        sim = _make_sim(
            body="Download and open the attached payment_update.exe to apply the patch.",
        )
        findings = check_no_attachment_payloads(sim)
        assert len(findings) >= 1
        assert any(".exe" in f for f in findings)

    def test_macro_enabled_document_triggers_finding(self):
        sim = _make_sim(
            body="Open report_macro.xlsm and click enable macros to view financial tables.",
        )
        findings = check_no_attachment_payloads(sim)
        assert len(findings) >= 1
        assert any(".xlsm" in f or "enable macros" in f for f in findings)

    def test_dangerous_execution_instruction_triggers_finding(self):
        sim = _make_sim(
            body="Double click the attached payload to run setup on your workstation.",
        )
        findings = check_no_attachment_payloads(sim)
        assert len(findings) >= 1


# ===========================================================================
# 4. Rule 4: No Real Brand Impersonation
# ===========================================================================


class TestNoRealBrandImpersonationRule:
    def test_fictional_company_name_passes(self):
        sim = _make_sim(
            sender="Meridian Procurement Services <orders@meridian-corp-sim.local>",
            subject="Invoice #88492 Confirmation",
        )
        findings = check_no_real_brand_impersonation(sim)
        assert findings == []

    def test_impersonating_paypal_triggers_finding(self):
        sim = _make_sim(
            sender="PayPal Security Team <security-alert@billing.sim-training.test>",
            subject="Unauthorized Transaction Detected",
        )
        findings = check_no_real_brand_impersonation(sim)
        assert len(findings) >= 1
        assert any("paypal" in f.lower() for f in findings)

    def test_impersonating_microsoft_triggers_finding(self):
        sim = _make_sim(
            sender="Microsoft 365 Support <admin@support.sim-training.test>",
            subject="Your Office 365 Password Expires Today",
        )
        findings = check_no_real_brand_impersonation(sim)
        assert len(findings) >= 1
        assert any("microsoft" in f.lower() or "office 365" in f.lower() for f in findings)


# ===========================================================================
# 5. Rule 5: No Real PII (SSNs, Credit Cards)
# ===========================================================================


class TestNoRealPiiRule:
    def test_content_without_pii_passes(self):
        sim = _make_sim(
            body="The total invoice amount is £14,250.00 for order reference #88492.",
        )
        findings = check_no_real_pii(sim)
        assert findings == []

    def test_ssn_pattern_triggers_finding(self):
        sim = _make_sim(
            body="Confirm your employee identity by verifying SSN: 123-45-6789.",
        )
        findings = check_no_real_pii(sim)
        assert len(findings) >= 1
        assert any("Social Security Number" in f for f in findings)

    def test_credit_card_pattern_triggers_finding(self):
        sim = _make_sim(
            body="Payment will be charged to card 4532-1188-9902-3341 on file.",
        )
        findings = check_no_real_pii(sim)
        assert len(findings) >= 1
        assert any("Credit Card" in f for f in findings)


# ===========================================================================
# 6. Overall Safety Gate Integration & Real Smoke Test Output
# ===========================================================================


class TestSafetyGateIntegration:
    def test_real_live_smoke_test_output_passes_safety_gate(self):
        """
        Verify the actual live smoke-test output from Phase 2
        (smoke_test_output.json with apex-consulting.sim-training.test)
        passes the Safety Gate cleanly.
        """
        output_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "smoke_test_output.json"
        )
        assert os.path.exists(output_path), "smoke_test_output.json must exist"

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sim = GeneratedSimulation(**data)
        result = check(sim)

        assert isinstance(result, SafetyCheckResult)
        assert result.passed is True
        assert result.status == "PASS"
        assert result.findings == []

    def test_multi_rule_violation_aggregates_findings(self):
        """
        Confirm multiple concurrent safety violations aggregate into findings
        rather than short-circuiting on the first failure.
        """
        unsafe_sim = _make_sim(
            sender="PayPal Security <fraud-prevention@real-bank.com>",
            subject="Official Account Security Alert: Update Password",
            body=(
                "Dear Customer,\n\n"
                "We detected an unauthorized charge on card 4532 8899 1234 5678.\n"
                "Please reply with your password and download the attached fix_tool.exe.\n"
                "You can also visit https://paypal-security-update.com/login.\n\n"
                "Regards,\nPayPal Team"
            ),
        )

        result = check(unsafe_sim)

        assert result.passed is False
        assert result.status == "FAIL"
        assert len(result.findings) >= 4  # domain, credential harvesting, dangerous attachment, brand impersonation, pii

        # Ensure findings cover distinct categories
        findings_text = " ".join(result.findings).lower()
        assert "domain" in findings_text
        assert "credential" in findings_text
        assert ".exe" in findings_text
        assert "paypal" in findings_text
        assert "credit card" in findings_text

    def test_fail_closed_on_unhandled_exception(self):
        """
        Confirm fail-closed behavior: if an individual rule raises an unhandled
        exception, check() must return FAIL (passed=False), never a crash or silent pass.
        """
        sim = _make_sim()
        import core.safety.safety_gate as sg_mod

        with patch.object(
            sg_mod,
            "check_no_real_domains",
            side_effect=RuntimeError("Unexpected parsing failure in domain check"),
        ):
            result = sg_mod.check(sim)

            assert isinstance(result, SafetyCheckResult)
            assert result.passed is False
            assert result.status == "FAIL"
            assert len(result.findings) >= 1
            assert any("Safety rule execution failed" in f or "Unexpected parsing failure" in f for f in result.findings)
