"""
core/verification/rule_checks.py

Layer A of the Hybrid Verifier: Deterministic, rule-based checks.
Zero LLM calls, zero external I/O.

Evaluates:
  1. Indicator presence: verifies desired_indicators are plausibly represented.
  2. Prohibited elements absence: verifies prohibited elements are not present.
  3. Structural validity: verifies email structure (subject, sender, greeting, body, signoff).
  4. Language quality/match: verifies language matches requested code.

Produces:
  - indicator_score (0–100)
  - language_score (0–100)
  - rule_findings (list[str])

Source of truth: Document B v2 §12.
"""

from __future__ import annotations

import json
import re
from pydantic import BaseModel, Field

from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation

# ---------------------------------------------------------------------------
# Result Data Structure
# ---------------------------------------------------------------------------


class LayerAResult(BaseModel):
    """Output of Layer A deterministic rule checks."""

    indicator_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Deterministic score (0–100) measuring requested indicator coverage.",
    )
    language_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Deterministic score (0–100) measuring language match and structural quality.",
    )
    rule_findings: list[str] = Field(
        default_factory=list,
        description="Deterministic findings or missing element descriptions.",
    )


# ---------------------------------------------------------------------------
# Indicator Heuristics & Keywords
# (Documented Limitation: Keyword-based heuristic for deterministic baseline)
# ---------------------------------------------------------------------------

_INDICATOR_KEYWORDS: dict[str, list[str]] = {
    "urgency": [
        "urgent",
        "immediately",
        "asap",
        "overdue",
        "past due",
        "today",
        "deadline",
        "expiring",
        "critical",
        "action required",
        "final notice",
        "promptly",
        "time-sensitive",
    ],
    "authority_impersonation": [
        "director",
        "executive",
        "cfo",
        "ceo",
        "vp",
        "manager",
        "head of",
        "management",
        "administrator",
        "compliance",
        "legal",
        "authorized",
        "president",
    ],
    "suspicious_link": [
        "[simulated link",
        "http://",
        "https://",
        "portal",
        "click here",
        "link below",
        "login",
        "sign in",
        "access your",
    ],
    "unusual_request": [
        "bypass",
        "off-site",
        "emergency",
        "confidential",
        "exception",
        "unusual",
        "special request",
        "manual",
        "wire transfer",
        "new account",
    ],
    "credential_harvesting_pretext": [
        "verify your account",
        "password",
        "login",
        "credentials",
        "sign-in",
        "authenticate",
        "portal",
        "confirm identity",
    ],
    "delivery_expense_pretext": [
        "shipment",
        "tracking",
        "delivery",
        "courier",
        "customs fee",
        "dispatch",
        "package",
    ],
}


# ---------------------------------------------------------------------------
# Individual Check Functions
# ---------------------------------------------------------------------------


def check_indicators(
    spec: ScenarioSpecification,
    sim: GeneratedSimulation,
) -> tuple[float, list[str]]:
    """
    Check for the plausible presence of desired indicators in the simulation text.

    Returns (indicator_score, findings).
    """
    if not spec.desired_indicators:
        return 100.0, []

    content = f"{sim.subject}\n{sim.body}\n{' '.join(sim.intended_indicators)}".lower()
    matched_count = 0
    findings: list[str] = []

    for indicator in spec.desired_indicators:
        clean_ind = indicator.strip().lower()
        keywords = _INDICATOR_KEYWORDS.get(clean_ind, [clean_ind.replace("_", " ")])
        
        # Check if any associated keyword or the indicator name itself matches
        matched = any(kw in content for kw in keywords) or clean_ind in [i.lower() for i in sim.intended_indicators]
        
        if matched:
            matched_count += 1
        else:
            findings.append(
                f"Missing or weak indicator: Requested indicator '{indicator}' was not detected in simulation content."
            )

    score = round((matched_count / len(spec.desired_indicators)) * 100.0, 1)
    return score, findings


def check_prohibited_elements(
    spec: ScenarioSpecification,
    sim: GeneratedSimulation,
) -> list[str]:
    """Check that elements listed in spec.prohibited_elements are absent."""
    findings: list[str] = []
    content = f"{sim.subject}\n{sim.sender}\n{sim.body}".lower()

    for prohibited in spec.prohibited_elements:
        clean_elem = prohibited.strip().lower()
        if clean_elem and clean_elem in content:
            findings.append(
                f"Prohibited element present: Found '{prohibited}' in simulation content."
            )

    return findings


def check_structural_and_language(
    spec: ScenarioSpecification,
    sim: GeneratedSimulation,
) -> tuple[float, list[str]]:
    """
    Check structural completeness (subject, sender, greeting, body, signoff)
    and language match against spec.language.

    Returns (language_score, findings).
    """
    findings: list[str] = []
    score = 100.0

    # 1. Structural checks
    if not sim.subject or len(sim.subject.strip()) < 5:
        findings.append("Structural flaw: Subject line is missing or unreasonably short.")
        score -= 20.0

    if not sim.sender or "@" not in sim.sender:
        findings.append("Structural flaw: Sender field is missing a valid address format.")
        score -= 20.0

    body_lines = [line.strip() for line in sim.body.strip().split("\n") if line.strip()]
    if len(body_lines) < 2:
        findings.append("Structural flaw: Email body is too brief (lacks standard paragraph/greeting structure).")
        score -= 20.0

    # Check for basic greeting heuristic
    has_greeting = any(
        re.match(r"^(hi|hello|dear|good\s+morning|good\s+afternoon|greetings|team|all)\b", line, re.IGNORECASE)
        for line in body_lines[:3]
    )
    if not has_greeting and len(body_lines) > 2:
        # Slight penalty / notice for missing opening
        score -= 5.0

    # Check for signoff heuristic across closing block (last 6 lines to allow multi-line signatures)
    closing_block = "\n".join(body_lines[-6:])
    has_signoff = bool(
        re.search(r"\b(regards|best|sincerely|thanks|thank\s+you|cheers|yours|cordially)\b", closing_block, re.IGNORECASE)
    )
    if not has_signoff and len(body_lines) > 2:
        score -= 5.0

    # 2. Language check (English baseline heuristic)
    if spec.language == "en":
        english_stopwords = {"the", "to", "and", "is", "for", "in", "of", "you", "your", "this", "please", "with"}
        body_words = set(re.findall(r"\b[a-zA-Z]{2,}\b", sim.body.lower()))
        overlap = english_stopwords.intersection(body_words)
        if len(overlap) < 2 and len(body_words) > 10:
            findings.append("Language mismatch: Body text does not appear to match expected English ('en') vocabulary.")
            score -= 30.0

    score = max(0.0, min(100.0, score))
    return score, findings


# ---------------------------------------------------------------------------
# Layer A Primary Runner
# ---------------------------------------------------------------------------


def run_rule_checks(
    spec: ScenarioSpecification,
    sim: GeneratedSimulation,
) -> LayerAResult:
    """
    Execute all Layer A deterministic rule checks.

    Parameters
    ----------
    spec:
        The target scenario specification.
    sim:
        The generated simulation artifact under evaluation.

    Returns
    -------
    LayerAResult
        Deterministic indicator_score, language_score, and rule_findings.
    """
    indicator_score, ind_findings = check_indicators(spec, sim)
    proh_findings = check_prohibited_elements(spec, sim)
    lang_score, struct_findings = check_structural_and_language(spec, sim)

    # If prohibited elements were found, reflect that as a deduction on indicator/quality score
    if proh_findings:
        indicator_score = max(0.0, indicator_score - 20.0 * len(proh_findings))

    all_findings = ind_findings + proh_findings + struct_findings

    return LayerAResult(
        indicator_score=indicator_score,
        language_score=lang_score,
        rule_findings=all_findings,
    )
