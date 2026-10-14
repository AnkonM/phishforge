"""
core/safety/safety_gate.py

Deterministic Safety Gate for PhishForge.

Source of truth: Document B v2 §11.

Executes deterministic, rule-based safety checks on generated simulations
prior to verification and refinement. Zero LLM calls, zero external I/O.
Runs in sub-millisecond time.

Safety rules:
  1. check_no_real_domains
  2. check_no_credential_harvesting
  3. check_no_attachment_payloads
  4. check_no_real_brand_impersonation
  5. check_no_real_pii

Architecture rules (Document B v2 §7):
  - No print() statements.
  - No CLI-specific logic.
  - Fail-closed: any unhandled rule exception results in an explicit FAIL.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from config.safety_blocklists import (
    ALLOWED_DOMAIN_REGEX,
    ALLOWED_SIMULATED_DOMAIN_SUFFIXES,
    BLOCKED_BRANDS,
    CREDIT_CARD_PATTERN,
    DANGEROUS_ATTACHMENT_EXTENSIONS,
    EXECUTION_ACTION_KEYWORDS,
    SIMULATED_LINK_PATTERN,
    SSN_PATTERN,
)
from models.schemas.simulation import GeneratedSimulation

# ---------------------------------------------------------------------------
# Result Model
# ---------------------------------------------------------------------------


class SafetyCheckResult(BaseModel):
    """Result of the deterministic Safety Gate evaluation."""

    passed: bool = Field(
        ...,
        description="True if all safety checks passed without violations.",
    )
    status: Literal["PASS", "FAIL"] = Field(
        ...,
        description="PASS if safe, FAIL if any safety violation was detected.",
    )
    findings: list[str] = Field(
        default_factory=list,
        description="List of specific safety violation descriptions (empty if passed).",
    )


# ---------------------------------------------------------------------------
# Internal Helpers for Parsing & Extraction
# ---------------------------------------------------------------------------

_EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
    re.IGNORECASE,
)

_URL_PATTERN = re.compile(
    r"https?://([a-zA-Z0-9.-]+)(?::\d+)?(?:/[^\s<>'\"\)\]]*)?",
    re.IGNORECASE,
)

_STANDALONE_DOMAIN_PATTERN = re.compile(
    r"\b(?:www\.)?([a-zA-Z0-9-]+\.(?:com|org|net|io|co|uk|de|ca|us|info|biz|ru|cn|gov|edu))\b",
    re.IGNORECASE,
)


def _is_allowed_domain(domain: str) -> bool:
    """Check if a domain matches the allowed simulated domain whitelist."""
    domain = domain.strip().lower().rstrip(".")
    if ALLOWED_DOMAIN_REGEX.match(domain):
        return True
    for suffix in ALLOWED_SIMULATED_DOMAIN_SUFFIXES:
        if domain.endswith(suffix.lstrip(".")):
            return True
    return False


# ---------------------------------------------------------------------------
# Individual Safety Rule Checks
# ---------------------------------------------------------------------------


def check_no_real_domains(sim: GeneratedSimulation) -> list[str]:
    """
    Check that all email addresses, URLs, and domains strictly adhere to
    the synthetic domain whitelist (*.example-corp-sim.local, *.sim-training.test, etc.).
    """
    findings: list[str] = []
    text_to_check = f"{sim.subject}\n{sim.sender}\n{sim.body}"

    # 1. Check all email addresses
    for match in _EMAIL_PATTERN.finditer(text_to_check):
        domain = match.group(1).lower()
        if not _is_allowed_domain(domain):
            findings.append(
                f"Unapproved or real domain in email address: '{match.group(0)}' (domain: '{domain}')"
            )

    # 2. Check all URLs (including URLs inside simulated link placeholders)
    for match in _URL_PATTERN.finditer(text_to_check):
        domain = match.group(1).lower()
        if not _is_allowed_domain(domain):
            findings.append(
                f"Unapproved or real domain in URL: '{match.group(0)}' (domain: '{domain}')"
            )

    # 3. Check for standalone real TLD references not enclosed in simulated placeholders
    # Strip bracketed placeholders first to avoid double-flagging
    cleaned_body = SIMULATED_LINK_PATTERN.sub("", text_to_check)
    for match in _STANDALONE_DOMAIN_PATTERN.finditer(cleaned_body):
        full_match = match.group(0).lower()
        if not _is_allowed_domain(full_match):
            findings.append(
                f"Unapproved or real web domain detected: '{match.group(0)}'"
            )

    return findings


def check_no_credential_harvesting(sim: GeneratedSimulation) -> list[str]:
    """
    Check that simulation does not solicit direct raw password / PIN submission
    into unmonitored plain-text channels (e.g. 'reply with your password').
    """
    findings: list[str] = []
    body_lower = sim.body.lower()

    direct_credential_phrases = [
        "reply with your password",
        "email back your password",
        "reply with your pin",
        "send your credentials to",
        "reply with your current credentials",
        "type your password in the reply",
        "reply with your login details",
    ]

    for phrase in direct_credential_phrases:
        if phrase in body_lower:
            findings.append(
                f"Direct credential harvesting solicitation detected: '{phrase}'"
            )

    return findings


def check_no_attachment_payloads(sim: GeneratedSimulation) -> list[str]:
    """
    Check that simulation does not reference dangerous executable/macro attachments
    or instruct the recipient to run/execute untrusted software.
    """
    findings: list[str] = []
    text_to_check = f"{sim.subject}\n{sim.body}".lower()

    # Check for dangerous file extension references
    for ext in DANGEROUS_ATTACHMENT_EXTENSIONS:
        # Match word boundary before filename and exact extension (e.g. invoice.exe)
        ext_pattern = re.compile(rf"\b[a-zA-Z0-9_\-]+\{ext}\b", re.IGNORECASE)
        match = ext_pattern.search(text_to_check)
        if match:
            findings.append(
                f"Dangerous attachment payload detected with extension '{ext}': '{match.group(0)}'"
            )

    # Check for execution action keywords
    for keyword in EXECUTION_ACTION_KEYWORDS:
        if keyword in text_to_check:
            findings.append(
                f"Potentially dangerous payload execution instruction detected: '{keyword}'"
            )

    return findings


def check_no_real_brand_impersonation(sim: GeneratedSimulation) -> list[str]:
    """
    Check that sender display name and content do not impersonate known real-world
    protected brands or financial/government institutions from the blocklist.
    """
    findings: list[str] = []
    sender_lower = sim.sender.lower()
    subject_lower = sim.subject.lower()

    # Priority check: sender identity impersonating real brands
    for brand in BLOCKED_BRANDS:
        pattern = re.compile(rf"\b{re.escape(brand)}\b", re.IGNORECASE)
        if pattern.search(sender_lower):
            findings.append(
                f"Real brand impersonation in sender field: '{brand}'"
            )
        elif pattern.search(subject_lower):
            # If subject explicitly impersonates brand security/accounts
            if any(term in subject_lower for term in ["security", "account", "verification", "support", "billing", "official"]):
                findings.append(
                    f"Real brand impersonation in subject field: '{brand}'"
                )

    return findings


def check_no_real_pii(sim: GeneratedSimulation) -> list[str]:
    """
    Check for real-looking PII patterns (SSNs, credit card numbers) anywhere
    in the generated simulation.
    """
    findings: list[str] = []
    text_to_check = f"{sim.subject}\n{sim.sender}\n{sim.body}"

    # Check Social Security Numbers
    for match in SSN_PATTERN.finditer(text_to_check):
        findings.append(
            f"Real-looking Social Security Number (SSN) pattern detected: '{match.group(0)}'"
        )

    # Check Credit Card numbers
    for match in CREDIT_CARD_PATTERN.finditer(text_to_check):
        raw_cc = re.sub(r"[- ]", "", match.group(0))
        # Additional sanity check on digit length to avoid false positives on 4-digit numbers
        if len(raw_cc) in [13, 14, 15, 16, 19]:
            findings.append(
                f"Real-looking Credit Card number pattern detected: '{match.group(0)}'"
            )

    return findings


# ---------------------------------------------------------------------------
# Primary Safety Gate Entry Point (Fail-Closed)
# ---------------------------------------------------------------------------


def check(sim: GeneratedSimulation) -> SafetyCheckResult:
    """
    Run all deterministic safety checks against a GeneratedSimulation.

    Fail-closed implementation: if any individual check raises an unexpected
    exception, the gate fails immediately and records the error as a finding.

    Parameters
    ----------
    sim:
        The GeneratedSimulation artifact to evaluate.

    Returns
    -------
    SafetyCheckResult
        Passed status (True/False), status ('PASS'/'FAIL'), and finding strings.
    """
    findings: list[str] = []

    rule_checks = [
        check_no_real_domains,
        check_no_credential_harvesting,
        check_no_attachment_payloads,
        check_no_real_brand_impersonation,
        check_no_real_pii,
    ]

    try:
        for rule in rule_checks:
            try:
                rule_findings = rule(sim)
                if rule_findings:
                    findings.extend(rule_findings)
            except Exception as rule_err:
                # Fail-closed on rule-level exception
                rule_name = getattr(rule, "__name__", str(rule))
                findings.append(
                    f"Safety rule execution failed in {rule_name}: {rule_err}"
                )
    except Exception as fatal_err:
        # Fail-closed on top-level unexpected exception
        findings.append(
            f"Fatal safety gate execution error: {fatal_err}"
        )

    if findings:
        return SafetyCheckResult(
            passed=False,
            status="FAIL",
            findings=findings,
        )

    return SafetyCheckResult(
        passed=True,
        status="PASS",
        findings=[],
    )
