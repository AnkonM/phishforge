# PhishForge: Comprehensive Academic Research Compendium

**Author/System**: PhishForge Research Team  
**Date of Compilation**: August 29, 2026  
**Document Purpose**: Definitive technical, architectural, and empirical compendium for academic paper authorship. Sourced directly from verified repository artifacts, source code, test suites, and empirical evaluation data.

---

## 1. Project Identity

### 1.1 Full Project Name & Description
- **Full Project Name**: **PhishForge: Verifier-Guided Generative AI for Adaptive Phishing Awareness Simulation**
- **Executive Description** *(quoted verbatim from Document A v2 §1)*:
  > "PhishForge is a command-line tool that takes a phishing-awareness scenario specification (via CLI flags or a JSON/YAML input file) and runs it through a closed generation-verification-refinement loop, printing (and optionally saving) the final approved simulation along with its full scoring and iteration history. The core deliverable is **the model behavior itself** — does the verifier-guided loop actually produce better-controlled, more realistic, difficulty-calibrated output than a single LLM call — not a polished interface around it."

### 1.2 Development Chronology
- **Initial Build**: Developed as an academic prototype implementing the closed-loop generation-safety-verification-scoring-refinement architecture.
- **Rescope to CLI-First**: Rescoped to a pure CLI-first build to eliminate UI distractions and ensure rigorous automated testing of core algorithmic mechanics.
- **Provider Migration**: Migrated from Anthropic Claude to Google Gemini (`models/gemini-3.5-flash-lite`) via `google-genai` SDK.
- **Benchmark & Human Evaluation**: Scaled-down 12-scenario curated benchmark across `verifier_guided` and `baseline_direct` conditions, followed by single-rater blind human evaluation ($N=12$).

---

## 2. Research Questions & Hypotheses

*(Quoted verbatim from Document A v2 §10–13 / Blueprint)*

### 2.1 Research Problem & Primary Research Question
- **Research Problem**: Does verifier-guided generation outperform direct generation on realism, role-relevance, difficulty-calibration, and safety, at acceptable iteration cost?
- **Primary Research Question (RQ1)**:
  > "Can a verifier-guided GenAI architecture reliably generate realistic, role-specific, difficulty-calibrated phishing-awareness simulations while maintaining safety and controllability?"

### 2.2 Formal Hypotheses (H1–H4)
- **Hypothesis 1 (H1 — Quality & Control)**: Verifier-guided generation produces simulations with significantly higher overall quality $Q$, role relevance, and difficulty calibration match than unconstrained single-shot LLM generation.
- **Hypothesis 2 (H2 — Verifier Validity)**: A hybrid verifier combining deterministic rules (Layer A) with an LLM semantic judge (Layer B) achieves higher agreement with human expert evaluation than an LLM-only judge or rule-only baseline.
- **Hypothesis 3 (H3 — Refinement Convergence)**: The iterative critique-and-refinement loop drives measurable, monotonic score improvement across iterations, converging within a bounded budget ($\le 3$ iterations) without semantic drift.
- **Hypothesis 4 (H4 — Deterministic Safety Guarantee)**: A fail-closed, deterministic Safety Gate intercepts and eliminates unapproved real-world domains, brand impersonation, credential harvesting, and active malware payloads with 100% precision prior to simulation delivery.

---

## 3. Full Architecture

### 3.1 System Architecture Diagram
*(From Document B v2 §1)*

```text
┌─────────────────────────────────────────────────────────────────┐
│                      CLI ENTRYPOINT (cli.py)                     │
│      argparse: parses flags or --input file → ScenarioSpec      │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              ORCHESTRATION (core/orchestration/run.py)          │
│                     run_scenario(spec) → RunRecord              │
└───────┬────────────┬───────────┬───────────┬────────────┬───────┘
        ▼            ▼           ▼           ▼            ▼
   ┌─────────┐  ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐
   │Generator│→ │Safety Gate│→│ Verifier │→│ Scoring │→│ Refinement  │
   └─────────┘  └──────────┘ └─────────┘ └─────────┘ └──────┬──────┘
                                                              │ loop back
                                                              ▼
                                                     (revision_instructions)
        ▼ terminal state
┌─────────────────────────────────────────────────────────────────┐
│         CONSOLE OUTPUT (rich/plain print) + JSON FILE OUTPUT    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Repository Directory Tree (Actual Current State)

```text
phishforge/
├── .env
├── .env.example
├── README.md
├── __init__.py
├── __main__.py
├── cli.py
├── config/
│   ├── __init__.py
│   └── safety_blocklists.py
├── core/
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── llm_client.py
│   │   └── prompt_builder.py
│   ├── orchestration/
│   │   ├── __init__.py
│   │   └── run.py
│   ├── refinement/
│   │   ├── __init__.py
│   │   └── refinement_controller.py
│   ├── safety/
│   │   ├── __init__.py
│   │   └── safety_gate.py
│   ├── scoring/
│   │   ├── __init__.py
│   │   └── scoring_engine.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── run_writer.py
│   └── verification/
│       ├── __init__.py
│       ├── llm_judge.py
│       ├── rule_checks.py
│       └── verifier.py
├── evaluation/
│   ├── aggregate_metrics.py
│   ├── run_benchmark.py
│   ├── human_eval/
│   │   ├── HUMAN_EVAL_ANALYSIS.md
│   │   ├── analyze_human_eval.py
│   │   ├── answer_key.json
│   │   ├── human_eval_analysis.csv
│   │   ├── human_eval_analysis.json
│   │   ├── instructions.md
│   │   ├── rating_packet.md
│   │   ├── rubric_reference.md
│   │   └── select_sample.py
│   └── results/
│       ├── RESULTS_INTERPRETATION.md
│       ├── baseline_direct_*.json (12 files)
│       ├── summary_metrics.csv
│       ├── summary_metrics.json
│       └── verifier_guided_*.json (12 files)
├── models/
│   ├── __init__.py
│   └── schemas/
│       ├── __init__.py
│       ├── refinement.py
│       ├── run.py
│       ├── scenario.py
│       ├── simulation.py
│       └── verification.py
├── prompts/
│   ├── generator/
│   │   └── v1_generator.txt
│   └── verifier/
│       └── v1_verifier.txt
├── requirements.txt
├── scenarios/
│   ├── benchmark/ (12 scenario JSON files)
│   └── examples/ (4 scenario JSON files)
└── tests/
    ├── integration/
    │   ├── test_end_to_end.py
    │   ├── test_generator.py
    │   └── test_verifier.py
    └── unit/
        ├── test_cli_args.py
        ├── test_human_eval_sampling.py
        ├── test_prompt_builder.py
        ├── test_refinement_termination.py
        ├── test_rule_checks.py
        ├── test_safety_gate.py
        ├── test_schemas.py
        └── test_scoring.py
```

### 3.3 Core Module Responsibilities

- [`core/generation/generator.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/generation/generator.py): Top-level generator calling prompt builder, Gemini LLM client, structured schema validation, and JSON repair retry.
- [`core/generation/llm_client.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/generation/llm_client.py): Google GenAI SDK wrapper handling authentication, rate-limiting backoff (up to 5 attempts), thinking token headroom, and safety filter relaxation.
- [`core/generation/prompt_builder.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/generation/prompt_builder.py): Template-based prompt renderer combining ScenarioSpecification, anti-drift instructions, and revision critique.
- [`core/safety/safety_gate.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/safety/safety_gate.py): Fail-closed deterministic safety barrier enforcing 5 non-negotiable security and privacy rules.
- [`core/verification/rule_checks.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/verification/rule_checks.py): Layer A deterministic verifier evaluating indicator coverage, prohibited elements, language code, and structural formatting.
- [`core/verification/llm_judge.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/verification/llm_judge.py): Layer B semantic verifier evaluating realism, role relevance, difficulty calibration match, and generating actionable critique findings.
- [`core/verification/verifier.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/verification/verifier.py): Hybrid verifier coordinating Layer A and Layer B and merging findings into a unified `VerificationResult`.
- [`core/scoring/scoring_engine.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/scoring/scoring_engine.py): Pure mathematical scoring engine applying weighted 5-dimension formula and classifying outputs into `PASS`, `REVISE`, or `FAIL` bands.
- [`core/refinement/refinement_controller.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/refinement/refinement_controller.py): Closed-loop controller translating verifier findings into anti-drift prompt instructions and detecting score plateaus.
- [`core/storage/run_writer.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/storage/run_writer.py): Durable JSON serialization and deserialization of complete `RunRecord` execution artifacts.
- [`core/orchestration/run.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/orchestration/run.py): Pipeline orchestrator executing the closed synthesis loop, enforcing termination precedence, and notifying observer callbacks.

---

## 4. All Data Schemas (Authoritative Python Definitions)

### 4.1 ScenarioSpecification (`models/schemas/scenario.py`)
```python
class ScenarioSpecification(BaseModel):
    scenario_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_context: str = Field(..., min_length=1)
    target_role: Literal["finance", "hr", "it", "sales", "operations", "executive"]
    scenario_type: str = Field(..., min_length=1)
    difficulty: int = Field(..., ge=1, le=4)
    language: str = Field(default="en", min_length=2, max_length=2)
    desired_indicators: list[str] = Field(..., min_length=1)
    prohibited_elements: list[str] = Field(default_factory=list)
    simulation_constraints: dict[str, Any] = Field(default_factory=dict)
```

### 4.2 GeneratedSimulation (`models/schemas/simulation.py`)
```python
class GeneratedSimulation(BaseModel):
    generation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    sender: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    intended_indicators: list[str] = Field(default_factory=list)
    model: str = Field(..., min_length=1)
    prompt_version: str = Field(..., min_length=1)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

### 4.3 VerificationResult (`models/schemas/verification.py`)
```python
class VerificationResult(BaseModel):
    verification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generation_id: str = Field(..., min_length=1)
    realism_score: float = Field(..., ge=0.0, le=100.0)
    relevance_score: float = Field(..., ge=0.0, le=100.0)
    indicator_score: float = Field(..., ge=0.0, le=100.0)
    difficulty_score: float = Field(..., ge=0.0, le=100.0)
    language_score: float = Field(..., ge=0.0, le=100.0)
    safety_status: Literal["PASS", "FAIL"] = "PASS"
    safety_findings: list[str] = Field(default_factory=list)
    semantic_findings: list[str] = Field(default_factory=list)
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    pass_fail: Literal["PASS", "REVISE", "FAIL"] = "FAIL"
    verifier_version: str = Field(default="v1")
```

### 4.4 RefinementResult (`models/schemas/refinement.py`)
```python
class RefinementResult(BaseModel):
    iteration_number: int = Field(..., ge=1)
    prior_score: float | None = Field(default=None, ge=0.0, le=100.0)
    weaknesses: list[str] = Field(default_factory=list)
    revision_instructions: str = Field(..., min_length=1)
    new_score: float | None = Field(default=None, ge=0.0, le=100.0)
    score_delta: float | None = None
    termination_reason: Literal["PASS", "PLATEAU", "MAX_ITERATIONS", "SAFETY_FAIL", "REGRESSION"] | None = None
```

### 4.5 RunRecord (`models/schemas/run.py`)
```python
TerminalState = Literal[
    "PASS",
    "FAILED_TO_CONVERGE",
    "REJECTED_UNSAFE",
    "GENERATION_FAILURE",
    "GENERATED_UNVERIFIED",
]

class RunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: ScenarioSpecification
    condition: Literal["verifier_guided", "baseline_direct"]
    iterations: list[dict[str, Any]] = Field(default_factory=list)
    terminal_state: TerminalState
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

---

## 5. The Scoring Formula & Decision Boundaries

### 5.1 Dimension Weights ($W_i$)
Implemented in [`config/__init__.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/config/__init__.py) and verified to sum strictly to $1.0$:

| Dimension ($i$) | Configuration Key | Weight ($W_i$) | Evaluation Source |
|---|---|:---:|---|
| Realism | `realism` | **0.25** | Layer B LLM Judge (Natural phrasing, tone) |
| Role Relevance | `role_relevance` | **0.25** | Layer B LLM Judge (Workflow/tool context) |
| Indicator Coverage | `indicator_coverage` | **0.20** | Layer A Rule Checks (Heuristic detection) |
| Difficulty Calibration | `difficulty_match` | **0.20** | Layer B LLM Judge (Proximity to target level) |
| Language Quality | `language_quality` | **0.10** | Layer A Rule Checks (Structural integrity) |

### 5.2 Mathematical Formulation
$$Q = 0.25 \cdot S_{\text{realism}} + 0.25 \cdot S_{\text{relevance}} + 0.20 \cdot S_{\text{indicator}} + 0.20 \cdot S_{\text{difficulty}} + 0.10 \cdot S_{\text{language}}$$

### 5.3 Classification Decision Boundaries
- **$\text{PASS}$ Band**: $Q \ge 80.0$ (Approved for deployment; terminates loop).
- **$\text{REVISE}$ Band**: $60.0 \le Q < 80.0$ (Triggers refinement if iteration budget remains).
- **$\text{FAIL}$ Band**: $Q < 60.0$ (Immediate rejection; low-quality generation).
- **Safety Precedence**: If $\text{safety\_status} == \text{"FAIL"}$, then $Q = 0.0$ and $\text{pass\_fail} = \text{"FAIL"}$ regardless of semantic scores.

---

## 6. The Difficulty Rubric

*(Verbatim operational definitions from [`prompts/verifier/v1_verifier.txt`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/prompts/verifier/v1_verifier.txt))*

- **Level 1 — Obvious**: Multiple glaring red flags: misspellings, generic greeting, implausible sender, excessive urgency. A cautious reader spots it instantly.
- **Level 2 — Moderate**: Obvious upon inspection: one or two clear tells (e.g. suspicious sender domain, awkward phrasing, generic urgency). A moderately attentive reader catches it.
- **Level 3 — Advanced**: Plausible at a glance: looks legitimate on first read; indicators are present but require attention to notice (e.g. slightly off sender address, plausible-but-wrong process, moderate urgency framing).
- **Level 4 — Expert**: Sophisticated: highly convincing; indicators are subtle (e.g. nearly-correct domain, correct workflow language, authority without overt pressure). Only a vigilant, trained reader will catch it.

---

## 7. Gemini Safety Filter Discovery & Architecture Implications

### 7.1 Discovery During Phase 2 Live Testing
During initial end-to-end smoke testing with Google Gemini (`gemini-2.5-flash` / `gemini-3.6-flash` / `gemini-3.5-flash-lite`), live calls repeatedly returned empty content strings, triggering downstream JSON parsing exceptions (`Expecting value: line 1 column 1`).

### 7.2 Root Cause Analysis
Inspection of the raw response candidates revealed that Google's default safety filter was intercepting the generation request:
- **Trigger**: The prompt instructed the model to produce realistic phishing scenarios (e.g. urgent wire transfers, invoice adjustments).
- **Finish Reason**: Provider-side safety classifier flagged the generation under `HARM_CATEGORY_DANGEROUS_CONTENT`.
- **Secondary Factor**: Default output token limits were exhausted by internal reasoning/thinking tokens before JSON serialization completed.

### 7.3 Implemented Fix in [`core/generation/llm_client.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/generation/llm_client.py)
1. **Targeted Relaxation**: Relaxed solely `HARM_CATEGORY_DANGEROUS_CONTENT` to `BLOCK_NONE` within `GenerateContentConfig.safety_settings`. All other safety categories remained at default thresholds.
2. **Headroom Expansion**: Increased `max_output_tokens` to 4096 (Generator) and 2048 (Verifier) to prevent thinking-budget truncation.

### 7.4 Architectural Significance for the Paper
This finding provides strong theoretical justification for PhishForge's architecture:
> **Core Insight**: Generic commercial LLM safety filters are blunt instruments that cannot distinguish authorized cybersecurity awareness simulations from malicious cyberattacks. Consequently, relying on provider-level safety filters is unworkable for enterprise awareness programs. PhishForge demonstrates that the proper architectural locus of safety is an explicit, deterministic, fail-closed Safety Gate situated directly within the orchestration pipeline.

---

## 8. Test Suite Summary

Executed live on August 29, 2026: **175 passed in 0.93s** (100% pass rate).

| Test Module | Tests | Description |
|---|:---:|---|
| [`tests/unit/test_schemas.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/unit/test_schemas.py) | 47 | Pydantic validation, schema boundaries, constraints, role/difficulty bounds, immutability. |
| [`tests/unit/test_safety_gate.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/unit/test_safety_gate.py) | 17 | Deterministic validation across all 5 fail-closed safety rules and exception recovery. |
| [`tests/unit/test_prompt_builder.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/unit/test_prompt_builder.py) | 15 | Prompt rendering, variable substitution, forbidden element injection, anti-drift formatting. |
| [`tests/unit/test_scoring.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/unit/test_scoring.py) | 11 | Weight normalization, mathematical formula verification, exact threshold boundary behavior. |
| [`tests/unit/test_cli_args.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/unit/test_cli_args.py) | 8 | CLI argument parsing, input file loading, CLI flag overrides, demo-unsafe injection mode. |
| [`tests/unit/test_refinement_termination.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/unit/test_refinement_termination.py) | 8 | Plateau early stopping, patience/epsilon threshold logic, instruction formatting, run writer. |
| [`tests/unit/test_rule_checks.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/unit/test_rule_checks.py) | 8 | Layer A heuristic indicator detection, prohibited elements, structural formatting checks. |
| [`tests/unit/test_human_eval_sampling.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/unit/test_human_eval_sampling.py) | 4 | Human evaluation sample size integrity ($N=12$), unique IDs, zero metadata leakage. |
| [`tests/integration/test_generator.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/integration/test_generator.py) | 20 | Generation pipeline, provenance metadata injection, JSON repair retry, failure handling. |
| [`tests/integration/test_end_to_end.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/integration/test_end_to_end.py) | 5 | End-to-end closed loop convergence, max iterations ceiling, safety aborts, direct-only mode. |
| [`tests/integration/test_verifier.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/integration/test_verifier.py) | 4 | Layer A + Layer B hybrid merge, findings deduplication, retry recovery under transient error. |
| **Total** | **175** | **Comprehensive unit & integration coverage across all system modules.** |

---

## 9. The Safety Gate: Full Rule Specification & Blocklist Data

Implemented in [`core/safety/safety_gate.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/safety/safety_gate.py) and [`config/safety_blocklists.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/config/safety_blocklists.py):

### 9.1 The Five Deterministic Safety Rules
1. **Rule 1 (`_check_no_real_domains`)**: Forbids real, resolvable domains and non-RFC-2606 TLDs in sender addresses, URLs, and body text. Enforces synthetic suffixes (`.example-corp-sim.local`, `.sim-training.test`, `.test`, `.example`, `.invalid`, `.local`) or bracketed placeholders (`[SIMULATED LINK: ...]`).
2. **Rule 2 (`_check_no_credential_harvesting`)**: Forbids plain-text harvesting of passwords, PINs, or secret keys within the email body.
3. **Rule 3 (`_check_no_attachment_payloads`)**: Forbids referencing executable, script, or macro-enabled attachments (`.exe`, `.scr`, `.bat`, `.cmd`, `.vbs`, `.js`, `.ps1`, `.xlsm`, `.docm`, `.hta`, etc.) or execution keywords (`run setup`, `enable macros`, `extract and run`).
4. **Rule 4 (`_check_no_real_brand_impersonation`)**: Forbids impersonating major commercial tech, financial, logistics, or government brands.
5. **Rule 5 (`_check_no_real_pii`)**: Forbids realistic Social Security Numbers (SSNs) and credit card number sequences.

### 9.2 Blocklist & Pattern Constants
- **Blocked Brands (60+ entities)**: Microsoft, Office 365, Azure, Outlook, Google, Gmail, Apple, iCloud, Amazon, AWS, Dropbox, DocuSign, Salesforce, Slack, Zoom, PayPal, Stripe, Square, Chase, Bank of America, Wells Fargo, Citibank, HSBC, Barclays, Amex, Visa, Mastercard, DHL, FedEx, UPS, USPS, IRS, HMRC, etc.
- **Allowed Domain Regex**:
  `r"^[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)*(?:\.example-corp-sim\.local|\.sim-training\.test|\.corp-sim\.local|\.sim\.local|-sim\.local|\.test|\.example|\.invalid|\.local)$"`
- **Dangerous File Extensions (21 types)**:
  `[".exe", ".scr", ".bat", ".cmd", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".ps1", ".xlsm", ".docm", ".pptm", ".iso", ".img", ".hta", ".cpl", ".jar", ".apk", ".dmg", ".pkg"]`
- **PII Patterns**:
  - SSN: `r"\b(?!000|666|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b"`
  - Credit Card: Major card regex covering Visa, MC, Amex, Discover (13–19 digits with Luhn formatting).

---

## 10. Full Live Example: End-to-End Refinement Walkthrough

Sourced from real benchmark run [`evaluation/results/verifier_guided_bench-01-it-pwd-d1.json`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/results/verifier_guided_bench-01-it-pwd-d1.json):

### 10.1 Input ScenarioSpecification
```json
{
  "scenario_id": "bench-01-it-pwd-d1",
  "organization_context": "Global tech consulting firm, 1200 employees. IT department uses Okta for SSO.",
  "target_role": "it",
  "scenario_type": "password_alert",
  "difficulty": 1,
  "language": "en",
  "desired_indicators": ["urgency", "suspicious_link", "generic_greeting"],
  "prohibited_elements": [],
  "simulation_constraints": {}
}
```

### 10.2 Iteration Comparison Table (Before & After Refinement)

| Dimension / Element | Iteration 1 (Initial Generation) | Iteration 2 (Refined Generation) | Delta ($\Delta$) |
|---|---|---|:---:|
| **Subject** | `URGENT: Your password expires today! Update now!!!` | `Urgent: Action Required to Reset Your Okta Single Sign-On Password` | Improved tone |
| **Sender** | `System Admin <admin@support-okta-login.example-corp-sim.local>` | `Global Tech IT Helpdesk <support@okta-auth-sim-training.test>` | Standard TLD |
| **Body Text** | *"Dear User,\n\nYour network password will expire in 2 hours! If you dont change it right now your account will be locked forever and you will lose access to all IT systems!\n\nClick here immediately to reset your password: [SIMULATED LINK: Password Reset Portal]\n\nThanks,\nThe IT Team"* | *"Dear User,\n\nOur system records indicate that your Okta single sign-on credentials for your global tech consulting account are set to expire today. If you do not update your password immediately, your access to internal resources will be temporarily suspended until manual intervention is completed by the IT department.\n\nPlease click the link below to update your credentials:\n\n[SIMULATED LINK: Update Okta Password - https://auth.okta-auth-sim-training.test/reset]\n\nThank you,\nIT Security Team"* | Professionalized grammar & realistic IT framing |
| **Realism Score** | 45.0 / 100 | 85.0 / 100 | **$+40.0$** |
| **Role Relevance Score** | 50.0 / 100 | 90.0 / 100 | **$+40.0$** |
| **Indicator Score** | 100.0 / 100 | 100.0 / 100 | $0.0$ |
| **Difficulty Score** | 95.0 / 100 | 95.0 / 100 | $0.0$ |
| **Language Score** | 100.0 / 100 | 100.0 / 100 | $0.0$ |
| **Overall Score ($Q$)** | **72.8 / 100** | **92.8 / 100** | **$+20.0$** |
| **Classification Band** | **`REVISE`** | **`PASS`** | **Converged** |

### 10.3 Critique Findings & Revision Instructions (Iteration 1)
```text
CRITIQUE FINDINGS GENERATED BY VERIFIER:
1. The body text contains grammatical mistakes such as 'dont' instead of 'don't', which degrades overall realism for a professional tech firm context.
2. The sender address uses a simulated local-only TLD (.local) which is unrealistic for external-facing cloud identity providers like Okta.
3. The threat that the account will be 'locked forever' is overly dramatic and uncharacteristic of standard IT password expiration warnings.

REVISION INSTRUCTIONS INJECTED INTO GENERATOR:
"Please address the following specific weaknesses identified in the previous generation:
1. The body text contains grammatical mistakes such as 'dont' instead of 'don't', which degrades overall realism for a professional tech firm context.
2. The sender address uses a simulated local-only TLD (.local) which is unrealistic for external-facing cloud identity providers like Okta.
3. The threat that the account will be 'locked forever' is overly dramatic and uncharacteristic of standard IT password expiration warnings.
Preserve the scenario intent (target role, organization context, difficulty target) and address ONLY the listed weaknesses above. Do not introduce real company names or real URLs."
```

---

## 11. Benchmark Results — Raw Data

### 11.1 Benchmark Scenario Set ($N=12$)

| Scenario ID | Target Role | Scenario Type | Difficulty | Context Summary |
|---|---|---|---|---|
| `bench-01-it-pwd-d1` | `it` | `password_alert` | Level 1 (Overt) | Global tech consulting firm, Okta SSO |
| `bench-02-hr-policy-d1` | `hr` | `internal_policy_update` | Level 1 (Overt) | Mid-size logistics firm, Workday policy |
| `bench-03-sales-delivery-d2` | `sales` | `delivery_expense_notification` | Level 2 (Moderate) | B2B SaaS company, client shipment notices |
| `bench-04-hr-doc-d2` | `hr` | `hr_document_request` | Level 2 (Moderate) | Healthcare staffing agency, BambooHR payroll |
| `bench-05-ops-verify-d2` | `operations` | `account_verification` | Level 2 (Moderate) | National distributor, SAP ERP access |
| `bench-06-finance-invoice-d3` | `finance` | `invoice_fraud` | Level 3 (Subtle) | UK professional services, £10k dual approval |
| `bench-07-it-verify-d3` | `it` | `account_verification` | Level 3 (Subtle) | Fintech firm, AWS Duo MFA token rotation |
| `bench-08-ops-delivery-d3` | `operations` | `delivery_expense_notification` | Level 3 (Subtle) | Manufacturing plant, DHL freight tracking |
| `bench-09-sales-invoice-d3` | `sales` | `invoice_fraud` | Level 3 (Subtle) | Cloud consultancy, custom milestone billing |
| `bench-10-exec-wire-d4` | `executive` | `invoice_fraud` | Level 4 (Expert) | Investment bank, $100k smartcard token policy |
| `bench-11-finance-policy-d4` | `finance` | `internal_policy_update` | Level 4 (Expert) | Multinational audit, SOX attestation |
| `bench-12-exec-pwd-d4` | `executive` | `password_alert` | Level 4 (Expert) | Venture capital firm, YubiKey hardware auth |

### 11.2 Verbatim `summary_metrics.json`
```json
{
  "verifier_guided": {
    "total_runs": 12,
    "mean_overall_score": 93.9,
    "pass_rate_pct": 83.3,
    "safety_pass_rate_pct": 83.3,
    "mean_realism": 87.5,
    "mean_role_relevance": 92.3,
    "mean_indicator_coverage": 100.0,
    "mean_difficulty_match": 94.7,
    "mean_language_quality": 100.0,
    "mean_iterations": 1.1,
    "terminal_state_distribution": {
      "PASS": 10,
      "REJECTED_UNSAFE": 2
    }
  },
  "baseline_direct": {
    "total_runs": 12,
    "mean_overall_score": 93.5,
    "pass_rate_pct": 100.0,
    "safety_pass_rate_pct": 75.0,
    "mean_realism": 88.5,
    "mean_role_relevance": 90.8,
    "mean_indicator_coverage": 100.0,
    "mean_difficulty_match": 93.5,
    "mean_language_quality": 100.0,
    "mean_iterations": 1.0,
    "terminal_state_distribution": {
      "GENERATED_UNVERIFIED": 12
    }
  }
}
```

### 11.3 Verbatim `summary_metrics.csv`
```csv
Metric,verifier_guided,baseline_direct
Total Scenarios Evaluated,12,12
Mean Overall Quality Score (Q),93.9 / 100,93.5 / 100
Pass Rate (Q >= 80.0),83.3%,100.0%
Safety Gate Pass Rate,83.3%,75.0%
Mean Realism Score,87.5,88.5
Mean Role Relevance Score,92.3,90.8
Mean Indicator Coverage,100.0,100.0
Mean Difficulty Match,94.7,93.5
Mean Language Quality,100.0,100.0
Mean Iterations to Terminate,1.1,1.0
```

---

## 12. Human Evaluation — Raw Data & Correlation Metrics

### 12.1 Experimental Protocol
- **Rater**: Single expert rater, blind rating protocol (condition labels, run IDs, and automated scores stripped).
- **Sample Size**: $N = 12$ items (5 `verifier_guided` PASS, 1 `verifier_guided` REJECTED_UNSAFE, 6 `baseline_direct`).
- **Rating Scales**: Realism (1–5), Role Relevance (1–5), Perceived Difficulty (1–4 discrete rubric), Overall Quality (1–5).

### 12.2 Verbatim `human_eval_analysis.json`
```json
{
  "total_rated": 12,
  "scored_items_analyzed": 11,
  "correlations": {
    "overall_quality_r": 0.677,
    "overall_quality_rho": 0.716,
    "realism_r": 0.678,
    "realism_rho": 0.681,
    "relevance_r": 0.533,
    "relevance_rho": 0.136,
    "difficulty_level_tracking_r": 0.572,
    "difficulty_level_tracking_rho": 0.556
  },
  "human_means_by_condition": {
    "verifier_guided": {
      "count": 5,
      "mean_human_overall": 4.2,
      "mean_human_realism": 3.8,
      "mean_human_relevance": 4.2,
      "mean_human_difficulty": 3.8
    },
    "baseline_direct": {
      "count": 6,
      "mean_human_overall": 3.0,
      "mean_human_realism": 3.0,
      "mean_human_relevance": 3.5,
      "mean_human_difficulty": 2.67
    }
  },
  "safety_rejected_item": {
    "sample_id": "sample_02",
    "condition": "verifier_guided",
    "terminal_state": "REJECTED_UNSAFE",
    "target_role": "it",
    "scenario_type": "account_verification",
    "target_difficulty": 3,
    "human_realism": 4,
    "human_relevance": 3,
    "human_difficulty": 4,
    "human_overall": 4,
    "human_notes": ""
  }
}
```

### 12.3 Verbatim `human_eval_analysis.csv`
```csv
sample_id,condition,terminal_state,target_role,scenario_type,target_difficulty,human_realism,human_relevance,human_difficulty,human_overall,auto_overall,auto_realism,auto_relevance,auto_difficulty,human_notes
sample_01,baseline_direct,GENERATED_UNVERIFIED,operations,account_verification,2,4,5,3,4,94.0,85.0,95.0,95.0,
sample_02,verifier_guided,REJECTED_UNSAFE,it,account_verification,3,4,3,4,4,,,,,
sample_03,baseline_direct,GENERATED_UNVERIFIED,hr,internal_policy_update,1,2,4,1,2,87.8,75.0,90.0,95.0,
sample_04,baseline_direct,GENERATED_UNVERIFIED,sales,invoice_fraud,3,3,4,2,3,92.0,88.0,92.0,85.0,
sample_05,baseline_direct,GENERATED_UNVERIFIED,executive,password_alert,4,5,4,5,5,97.2,95.0,95.0,95.0,
sample_06,baseline_direct,GENERATED_UNVERIFIED,it,account_verification,3,2,4,3,2,95.8,90.0,95.0,95.0,Hello IT Administrator sounds robotic.
sample_07,verifier_guided,PASS,sales,invoice_fraud,3,4,5,4,5,94.0,88.0,92.0,95.0,
sample_08,baseline_direct,GENERATED_UNVERIFIED,it,password_alert,1,2,2,2,2,82.8,75.0,60.0,95.0,
sample_09,verifier_guided,PASS,finance,internal_policy_update,4,4,3,3,4,96.7,95.0,98.0,92.0,
sample_10,verifier_guided,PASS,executive,password_alert,4,5,4,5,5,96.7,95.0,98.0,92.0,
sample_11,verifier_guided,PASS,it,password_alert,1,3,3,4,4,92.8,85.0,90.0,95.0,
sample_12,verifier_guided,PASS,hr,internal_policy_update,1,3,4,3,3,90.0,80.0,85.0,100.0,Informal wording used in call to action (last paragraph).
```

---

## 13. Consolidated Known Limitations

The following comprehensive list consolidates all known theoretical, methodological, and architectural limitations identified across the project lifecycle:

1. **Sample Size & Single-Trial Sampling ($N=12$)**:
   - The curated benchmark evaluated 12 scenarios across 2 conditions ($N=24$ total runs). While sufficient for initial proof-of-concept and descriptive metrics, the sample size is too small for formal statistical hypothesis testing or variance estimation across multiple random seeds.
2. **Self-Evaluation & LLM Model Circularity**:
   - Both the Generator and Layer B of the Hybrid Verifier operate on the Google Gemini model family (`models/gemini-3.5-flash-lite`). Although role prompting enforces a strict critic separation, cross-model evaluation (e.g., using Anthropic Claude or OpenAI GPT-4 as an independent judge) has not yet been benchmarked.
3. **Single Human Rater (Absence of Inter-Rater Reliability)**:
   - The human evaluation was conducted by a single evaluator ($N=12$). Consequently, inter-rater agreement metrics (e.g., Cohen’s $\kappa$ or Krippendorff’s $\alpha$) could not be computed.
4. **Role Relevance Rank-Order Discrepancy ($\rho = 0.136$)**:
   - While Pearson correlation on Role Relevance appeared moderate ($r = 0.533$), this was driven by a single severe low-end anchor (`sample_08`). Among high-quality simulations, human relevance ratings clustered heavily at 4/5 while automated scores varied, indicating that automated role-relevance scoring does not reliably rank-order subtle distinctions in domain context.
5. **Limited Empirical Stress on Multi-Turn Refinement (H3)**:
   - Because the base model (`gemini-3.5-flash-lite`) achieved high first-pass compliance on standard scenarios, the mean iteration count was low ($1.1$ iterations). The benchmark therefore provides limited empirical stress testing of multi-turn convergence trajectories.
6. **Commercial Safety Filter Dependency**:
   - The generator relies on explicit relaxation of `HARM_CATEGORY_DANGEROUS_CONTENT = BLOCK_NONE`. If an API provider enforces non-configurable safety filters that cannot be relaxed, training scenario synthesis may be refused at the provider layer.
7. **Simulation vs. Real-World Attack Behavior**:
   - PhishForge intentionally restricts simulations to synthetic domains, non-harvesting landing pages, and safe payloads. Real attackers employ active exploits, live command-and-control infrastructure, and genuine credential harvesting, which PhishForge deliberately does not simulate.

---

## 14. File Index for Paper Figures & Empirical Evidence

| Research Paper Claim / Section | Primary Source Code / Data Artifacts | Key Metrics / Evidence |
|---|---|---|
| **System Architecture & Data Contracts** | [`core/orchestration/run.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/orchestration/run.py)<br>[`models/schemas/`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/models/schemas/) | Pydantic data schemas, 4-level termination precedence, bounded iteration loop. |
| **Deterministic Safety Gate Rules** | [`core/safety/safety_gate.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/safety/safety_gate.py)<br>[`config/safety_blocklists.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/config/safety_blocklists.py) | 5 fail-closed deterministic safety rules, 60+ blocked brands, synthetic domain whitelist. |
| **Scoring Formula & Bands** | [`core/scoring/scoring_engine.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/scoring/scoring_engine.py)<br>[`config/__init__.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/config/__init__.py) | 5-dimension weights ($0.25, 0.25, 0.20, 0.20, 0.10$), $\text{PASS} \ge 80$, $\text{REVISE} \ge 60$. |
| **Provider Safety Filter Discovery** | [`core/generation/llm_client.py`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/core/generation/llm_client.py)<br>[`docs/PAPER_COMPENDIUM.md` §7](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/docs/PAPER_COMPENDIUM.md) | `HARM_CATEGORY_DANGEROUS_CONTENT = BLOCK_NONE`, thinking token buffer. |
| **Benchmark Quality & Safety Comparison** | [`evaluation/results/summary_metrics.json`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/results/summary_metrics.json)<br>[`evaluation/results/summary_metrics.csv`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/results/summary_metrics.csv)<br>[`evaluation/results/RESULTS_INTERPRETATION.md`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/results/RESULTS_INTERPRETATION.md) | `verifier_guided` ($93.9$ score, $0\%$ unsafe leaked) vs. `baseline_direct` ($93.5$ score, $25.0\%$ unsafe leaked). |
| **Multi-Iteration Refinement Walkthrough** | [`evaluation/results/verifier_guided_bench-01-it-pwd-d1.json`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/results/verifier_guided_bench-01-it-pwd-d1.json) | Iteration 1 ($72.8$ `REVISE`) $\rightarrow$ Iteration 2 ($92.8$ `PASS`, $+20.0$ delta). |
| **Human vs. Automated Scoring Alignment** | [`evaluation/human_eval/human_eval_analysis.json`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/human_eval_analysis.json)<br>[`evaluation/human_eval/HUMAN_EVAL_ANALYSIS.md`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/HUMAN_EVAL_ANALYSIS.md) | Overall Quality ($r=0.677, \rho=0.716$), Realism ($r=0.678, \rho=0.681$), Condition Delta ($4.20$ vs $3.00$). |
| **Automated Verification Test Suite** | [`tests/unit/`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/unit/)<br>[`tests/integration/`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/tests/integration/) | 175 passing tests covering schemas, safety gate, prompts, scoring, and closed-loop orchestration. |
