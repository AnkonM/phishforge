"""
server/mock_provider.py

Deterministic, scripted LLM provider for Demo mode. Implements exactly the
interface core.generation.llm_client.call_llm reads from its `_client`
parameter: `client.models.generate_content(model=, contents=, config=)`
returning an object with a `.text` attribute. No core file is touched --
this is purely an external, additive stand-in object injected through the
`_client` kwarg that generate()/verify() already accept.

Four scripted outcomes are provided (see docs/DECISIONS.md for why these
four and how they map to real pipeline code paths):
  - "first_pass":    one iteration, immediate PASS.
  - "revise_pass":   two iterations, REVISE -> PASS. For the exact scenario
                      bench-01-it-pwd-d1 this replays the *real* recorded
                      benchmark run (72.8 -> 92.8) verbatim; for any other
                      spec it's a parameterized version of the same arc.
  - "safety_reject":  a simulation containing a real brand name + real
                      domain, run through the REAL (unmodified) safety gate,
                      which genuinely rejects it -- no verifier call happens.
  - "plateau":        three non-passing iterations with small score deltas
                      each time. Under the shipped config (MAX_ITERATIONS=3,
                      IMPROVEMENT_PATIENCE=2) the iteration-ceiling check
                      always fires before the plateau check can ever see 3
                      scores, so this genuinely terminates FAILED_TO_CONVERGE
                      with termination_reason=MAX_ITERATIONS, not
                      NO_IMPROVEMENT -- see docs/DECISIONS.md for why that
                      reason is unreachable in the shipped pipeline and why
                      this script does not claim otherwise.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from models.schemas.scenario import ScenarioSpecification

DemoScript = str  # "first_pass" | "revise_pass" | "safety_reject" | "plateau"

_GREETING = "Dear Team,"
_SIGNOFF = "Regards,\nIT Support"


class FakeGenaiClient:
    """Scripted stand-in for google.genai.Client, scoped to one call-site family
    (either all generator calls or all judge calls for a single run)."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._idx = 0
        self.models = SimpleNamespace(generate_content=self._generate_content)

    def _generate_content(self, model: str, contents: str, config: Any = None) -> SimpleNamespace:
        if self._idx < len(self._responses):
            text = self._responses[self._idx]
            self._idx += 1
        else:
            # Repair-retry defensive fallback: never happens with well-formed
            # scripted JSON, but keeps the fake client total rather than
            # raising IndexError if it ever did.
            text = self._responses[-1] if self._responses else "{}"
        return SimpleNamespace(text=text)


@dataclass
class IterationScript:
    simulation: dict[str, Any]
    layer_b: dict[str, Any]


@dataclass
class RunScript:
    name: DemoScript
    iterations: list[IterationScript] = field(default_factory=list)
    is_unsafe: bool = False  # True for "safety_reject": the real safety gate rejects iterations[0]


def _sim_json(
    subject: str,
    sender: str,
    body: str,
    spec: ScenarioSpecification,
    notes: str,
) -> dict[str, Any]:
    return {
        "subject": subject,
        "sender": sender,
        "body": body,
        # Matching intended_indicators to desired_indicators exactly makes
        # the REAL deterministic rule_checks.check_indicators() score 100 --
        # it treats an indicator as satisfied if it is literally present in
        # intended_indicators, independent of keyword matching in body text.
        "intended_indicators": list(spec.desired_indicators),
        "metadata": {"scenario_notes": notes, "demo": True},
    }


def _layer_b_json(
    realism: float,
    relevance: float,
    difficulty: float,
    spec: ScenarioSpecification,
    findings: list[str],
) -> dict[str, Any]:
    return {
        "realism_score": realism,
        "relevance_score": relevance,
        "difficulty_score": difficulty,
        "assessed_difficulty": spec.difficulty,
        "difficulty_rationale": "Scripted demo-mode judge output.",
        "semantic_findings": findings,
    }


def _generic_body(spec: ScenarioSpecification, variant: str) -> str:
    pretext = {
        "invoice_fraud": "an outstanding invoice that requires urgent review",
        "password_alert": "your account password, which is set to expire today",
        "hr_document_request": "a document HR needs from you before end of day",
        "delivery_expense_notification": "a package held pending a small customs fee",
        "account_verification": "a routine account verification step",
        "internal_policy_update": "an internal policy update you must acknowledge",
    }.get(spec.scenario_type, "an item that needs your immediate attention")

    if variant == "revised":
        urgency = "Please review and confirm by end of day."
        extra = (
            f"This relates to {spec.organization_context.rstrip('.')}. "
            "If you have questions, contact your IT department through normal channels."
        )
    else:
        urgency = "This is time-sensitive -- action is required immediately!"
        extra = "Please do not delay."

    return (
        f"{_GREETING}\n\n"
        f"We are writing about {pretext}. {urgency}\n\n"
        f"[SIMULATED LINK: {spec.scenario_type.replace('_', ' ').title()} Portal]\n\n"
        f"{extra}\n\n"
        f"{_SIGNOFF}"
    )


def _script_first_pass(spec: ScenarioSpecification) -> RunScript:
    sim = _sim_json(
        subject=f"Action needed: {spec.scenario_type.replace('_', ' ')} update",
        sender=f"IT Helpdesk <helpdesk@support.sim-training.test>",
        body=_generic_body(spec, "revised"),
        spec=spec,
        notes="Demo script: first-pass PASS.",
    )
    layer_b = _layer_b_json(88.0, 90.0, 88.0, spec, [])
    return RunScript(name="first_pass", iterations=[IterationScript(sim, layer_b)])


def _script_revise_pass(spec: ScenarioSpecification) -> RunScript:
    if spec.scenario_id == "bench-01-it-pwd-d1":
        # Exact replay of evaluation/results/verifier_guided_bench-01-it-pwd-d1.json
        iter1_sim = {
            "subject": "URGENT: Your password expires today! Update now!!!",
            "sender": "System Admin <admin@support-okta-login.example-corp-sim.local>",
            "body": (
                "Dear User,\n\nYour network password will expire in 2 hours! If you dont change it "
                "right now your account will be locked forever and you will lose access to all IT "
                "systems!\n\nClick here immediately to reset your password: "
                "[SIMULATED LINK: Password Reset Portal]\n\nThanks,\nThe IT Team"
            ),
            "intended_indicators": ["urgency", "suspicious_link", "generic_greeting"],
            "metadata": {
                "difficulty_rationale": "Glaring red flags: excessive urgency, generic greeting, suspicious domain.",
                "tone": "informal",
            },
        }
        iter1_layer_b = _layer_b_json(
            45.0, 50.0, 95.0, spec,
            [
                "The body text contains grammatical mistakes such as 'dont' instead of 'don't', which degrades overall realism for a professional tech firm context.",
                "The sender address uses a simulated local-only TLD (.local) which is unrealistic for external-facing cloud identity providers like Okta.",
                "The threat that the account will be 'locked forever' is overly dramatic and uncharacteristic of standard IT password expiration warnings.",
            ],
        )
        iter2_sim = {
            "subject": "Urgent: Action Required to Reset Your Okta Single Sign-On Password",
            "sender": "Global Tech IT Helpdesk <support@okta-auth-sim-training.test>",
            "body": (
                "Dear User,\n\nOur system records indicate that your Okta single sign-on credentials "
                "for your global tech consulting account are set to expire today. If you do not update "
                "your password immediately, your access to internal resources will be temporarily "
                "suspended until manual intervention is completed by the IT department.\n\n"
                "Please click the link below to update your credentials:\n\n"
                "[SIMULATED LINK: Update Okta Password - https://auth.okta-auth-sim-training.test/reset]\n\n"
                "Thank you,\nIT Security Team"
            ),
            "intended_indicators": ["urgency", "suspicious_link", "generic_greeting"],
            "metadata": {
                "difficulty_rationale": "Obvious red flags, grammar corrected, realistic cloud TLD.",
                "tone": "semi-formal",
            },
        }
        iter2_layer_b = _layer_b_json(85.0, 90.0, 95.0, spec, [])
        return RunScript(
            name="revise_pass",
            iterations=[IterationScript(iter1_sim, iter1_layer_b), IterationScript(iter2_sim, iter2_layer_b)],
        )

    # Generic parameterized REVISE -> PASS arc for any other spec.
    iter1_sim = _sim_json(
        subject=f"URGENT: {spec.scenario_type.replace('_', ' ').title()} -- act now!!!",
        sender="Notifications <alerts@sim-training.test>",
        body=_generic_body(spec, "initial"),
        spec=spec,
        notes="Demo script: iteration 1 of revise_pass.",
    )
    iter1_layer_b = _layer_b_json(
        52.0, 55.0, 80.0, spec,
        [
            "Tone reads as generic and slightly implausible for the stated organization context.",
            "Role relevance could be sharpened with more specific references to the target role's workflow.",
        ],
    )
    iter2_sim = _sim_json(
        subject=f"Action required: {spec.scenario_type.replace('_', ' ')} for {spec.target_role} team",
        sender="Notifications <alerts@sim-training.test>",
        body=_generic_body(spec, "revised"),
        spec=spec,
        notes="Demo script: iteration 2 of revise_pass (revised).",
    )
    iter2_layer_b = _layer_b_json(86.0, 88.0, 85.0, spec, [])
    return RunScript(
        name="revise_pass",
        iterations=[IterationScript(iter1_sim, iter1_layer_b), IterationScript(iter2_sim, iter2_layer_b)],
    )


def _script_safety_reject(spec: ScenarioSpecification) -> RunScript:
    unsafe_sim = _sim_json(
        subject="PayPal Account Verification Required",
        sender="PayPal Security <security@paypal.com>",
        body=(
            f"{_GREETING}\n\nWe detected unusual activity on your PayPal account. "
            "Please verify your account immediately at http://paypal.com/verify to avoid suspension.\n\n"
            f"{_SIGNOFF}"
        ),
        spec=spec,
        notes="Demo script: deliberately unsafe (real brand + real domain) to exercise the safety gate.",
    )
    return RunScript(name="safety_reject", iterations=[IterationScript(unsafe_sim, {})], is_unsafe=True)


def _script_plateau(spec: ScenarioSpecification) -> RunScript:
    scores = [(55.0, 58.0, 60.0), (57.0, 59.0, 62.0), (58.5, 60.5, 63.0)]
    iterations = []
    for i, (r, rel, diff) in enumerate(scores, start=1):
        sim = _sim_json(
            subject=f"Notice: {spec.scenario_type.replace('_', ' ')} (attempt {i})",
            sender="Notifications <alerts@sim-training.test>",
            body=_generic_body(spec, "initial"),
            spec=spec,
            notes=f"Demo script: plateau iteration {i} -- minimal improvement by design.",
        )
        layer_b = _layer_b_json(
            r, rel, diff, spec,
            ["Realism and role relevance remain below the bar; revisions are not meaningfully improving the simulation."],
        )
        iterations.append(IterationScript(sim, layer_b))
    return RunScript(name="plateau", iterations=iterations)


_BUILDERS = {
    "first_pass": _script_first_pass,
    "revise_pass": _script_revise_pass,
    "safety_reject": _script_safety_reject,
    "plateau": _script_plateau,
}


def build_script(spec: ScenarioSpecification, script_name: DemoScript) -> RunScript:
    builder = _BUILDERS.get(script_name)
    if builder is None:
        raise ValueError(f"Unknown demo script: {script_name!r}")
    return builder(spec)


def pick_default_script(spec: ScenarioSpecification) -> DemoScript:
    """Deterministic auto-pick used when the caller doesn't explicitly choose
    a demo script (Studio default, and the Demo-mode Benchmark runner)."""
    if spec.scenario_id == "bench-01-it-pwd-d1":
        return "revise_pass"
    return {1: "first_pass", 2: "revise_pass", 3: "plateau", 4: "plateau"}.get(spec.difficulty, "first_pass")


def make_clients_for_script(script: RunScript) -> tuple[FakeGenaiClient, FakeGenaiClient]:
    """Build the (generator_client, judge_client) pair whose scripted response
    sequences line up 1:1 with the real call order inside run_scenario()."""
    gen_texts = [json.dumps(it.simulation) for it in script.iterations]
    judge_texts = [json.dumps(it.layer_b) for it in script.iterations]
    return FakeGenaiClient(gen_texts), FakeGenaiClient(judge_texts)
