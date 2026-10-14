# PhishForge

> **Verifier-Guided Generative AI for Adaptive Phishing-Awareness Simulation**

PhishForge is a closed-loop synthesis framework that creates personalized, difficulty-calibrated, and guaranteed-safe phishing-awareness training simulations. Given an organizational scenario specification, PhishForge evaluates each generated simulation through deterministic safety gates, hybrid verification (heuristic rules + LLM critic), multi-dimensional scoring, and automated anti-drift refinement.

---

## Closed-Loop Architecture

```
                                  +------------------------------------+
                                  |       ScenarioSpecification        |
                                  +-----------------+------------------+
                                                    |
                                                    v
+------------------+   Revision Instructions    +---+------------------+
|    Refinement    |<---------------------------| Hybrid Verifier &    |
|    Controller    |  (Weaknesses & Findings)   | Scoring Engine       |
+--------+---------+                            +---+------------------+
         |                                          ^
         v                                          | (PASS / REVISE)
+--------+---------+                            +---+------------------+
|    Generator     |--------------------------->|    Safety Gate       |
| (Prompt Builder) |    GeneratedSimulation     | (Deterministic Gate) |
+------------------+                            +---+------------------+
                                                    | (FAIL -> REJECTED_UNSAFE)
                                                    v
                                         [ Hard Fail-Closed Exit ]
```

### Core Execution Flow
1. **Generator**: Dynamically constructs structured prompts with anti-drift revision instructions. Generates schema-validated email simulations with repair-retry logic.
2. **Safety Gate (Deterministic Prior)**: Fail-closed rule engine enforcing domain allowlisting, brand blocklists, PII redacting, and attachment payload bans.
3. **Hybrid Verifier (Layer A + Layer B)**:
   - **Layer A**: Deterministic regex and rule checks for requested indicators, prohibited content, structural heuristics, and language match.
   - **Layer B**: LLM judge (`temperature=0.2`) evaluating contextual realism, role relevance, difficulty calibration (4-level rubric), and qualitative weaknesses.
4. **Scoring Engine**: Computes weighted overall quality score $Q \in [0, 100]$ across 5 dimensions and assigns classification bands (`PASS` $\ge 80$, `REVISE` $60\text{--}79$, `FAIL` $< 60$).
5. **Refinement Controller**: Translates evaluation findings into targeted critique prompts and enforces early-stopping policies (plateau detection with patience/epsilon thresholds).
6. **Orchestration**: Manages iteration loops (max 3 iterations) and outputs a comprehensive, serializable `RunRecord` JSON artifact.

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Google Gemini API Key (available via [Google AI Studio](https://aistudio.google.com/))

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-org/phishforge.git
cd phishforge
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Edit `.env` and add your Gemini API key:
```ini
GEMINI_API_KEY=your_google_ai_studio_api_key_here
```

---

## CLI Usage Guide

PhishForge is invoked via the `phishforge run` command. It supports flag-based scenario definitions, JSON scenario files, live verbose tracing, baseline modes, and safety demonstrations.

### 1. File-Based Run (Recommended)
Run a pre-configured scenario from `scenarios/examples/`:
```bash
python -m phishforge run --input scenarios/examples/finance_invoice_fraud.json --out result.json
```

### 2. Flag-Based Run with Live Verbose Tracing
Specify all scenario parameters directly from the command line and view the per-iteration evaluation:
```bash
python -m phishforge run \
    --role finance \
    --scenario-type invoice_fraud \
    --difficulty 3 \
    --indicators urgency,authority_impersonation,suspicious_link \
    --org-context "Mid-size UK accounting firm (~350 staff). Uses SAP for AP. Dual approval required above £10k." \
    --verbose \
    --out run_trace.json
```

### 3. Hybrid Flag Overriding
Load a scenario template and override specific parameters:
```bash
python -m phishforge run \
    --input scenarios/examples/finance_invoice_fraud.json \
    --difficulty 4 \
    --role executive \
    --verbose
```

### 4. Direct-Only Baseline Mode
Generate a single-shot simulation bypassing the Safety Gate, Verifier, and Refinement loops:
```bash
python -m phishforge run \
    --input scenarios/examples/finance_invoice_fraud.json \
    --direct-only \
    --out baseline_output.json
```

### 5. Deterministic Safety Gate Demo
Execute a deterministic demonstration of the fail-closed Safety Gate intercepting unsafe elements (real brands, active domains, PII requests, executable attachments):
```bash
python -m phishforge run \
    --input scenarios/examples/unsafe_test_case.json \
    --demo-unsafe \
    --verbose \
    --out unsafe_demo.json
```

---

## CLI Options Reference

```text
usage: phishforge run [-h] [--input INPUT_FILE]
                      [--role {finance,hr,it,sales,operations,executive}]
                      [--scenario-type SCENARIO_TYPE] [--difficulty {1,2,3,4}]
                      [--indicators INDICATORS] [--org-context ORG_CONTEXT]
                      [--language LANGUAGE] [--prohibited PROHIBITED]
                      [--constraints CONSTRAINTS] [--out OUT_PATH] [--verbose]
                      [--direct-only] [--demo-unsafe]

options:
  --input, -i FILE      Path to scenario JSON specification file.
  --role ROLE           Target role: finance, hr, it, sales, operations, executive.
  --scenario-type TYPE  Scenario type (e.g. invoice_fraud, password_alert, hr_document_request).
  --difficulty 1-4      Difficulty level: 1 (Overt) to 4 (Advanced Targeted Spear-Phishing).
  --indicators LIST     Comma-separated phishing indicators (e.g. 'urgency,suspicious_link').
  --org-context TEXT    Organizational context and background constraints.
  --language LANG       ISO 639-1 language code (default: 'en').
  --prohibited LIST     Comma-separated prohibited elements.
  --constraints JSON    JSON dictionary of simulation constraints.
  --out, -o FILE        Destination path to write the full RunRecord JSON artifact.
  --verbose, -v         Print live per-iteration quality scores, dimensions, and findings.
  --direct-only         Single-shot unverified generation (baseline_direct condition).
  --demo-unsafe         Demo flag: injects known unsafe payload to demonstrate Safety Gate rejection.
```

---

## Running the Automated Test Suite

PhishForge includes a comprehensive suite of 170+ automated unit and integration tests. All automated tests run offline with zero external network or API calls.

```bash
# Run all unit and integration tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run end-to-end integration tests
pytest tests/integration/ -v
```

---

## Provider Architecture Note

- **Active Model**: `models/gemini-3.5-flash-lite` via the official `google-genai` Python SDK (v2.20.0).
- **Safety Settings**: Frontier LLM provider safety filters conflate legitimate cybersecurity awareness training simulations with malicious attacks. PhishForge configures `HARM_CATEGORY_DANGEROUS_CONTENT = BLOCK_NONE` at the API client level so the model can generate training pretexts, while delegating authoritative, deterministic enforcement to PhishForge's own internal **Safety Gate** (`core/safety/safety_gate.py`).

---

## Project Scope (CLI-First Rescope)

Per Document A v2 §16 and Document C v2:
- **Current Scope**: CLI-first closed-loop generation, safety gating, hybrid verification, scoring, refinement controller, JSON artifact storage, and test suites.
- **Future Scope (Deferred)**: ~~Web UI~~ (see **Console** below, added as a separate additive
  layer — the pipeline itself is unchanged), SQLite persistence, multi-model comparative
  baselines, and human evaluation trials.

---

## Console

A web UI and dashboard for PhishForge: FastAPI backend (`server/`) wrapping the pipeline above
with **zero changes to any file in `core/`, `models/`, `config/`, or `cli.py`**, and a React +
TypeScript frontend (`web/`). See `docs/DECISIONS.md` for every judgment call and exactly why no
core touchpoints were needed, `docs/API.md` for the endpoint/SSE contract, and `docs/DESIGN.md`
for the visual design system.

### Install

```bash
make install        # creates .venv, installs Python + server deps, npm installs web/
```

### Run — development (backend + frontend, both live-reloading)

```bash
make dev             # Live mode if GEMINI_API_KEY is set in .env, else Demo mode
make demo            # Forces Demo mode (mock provider) regardless of key presence
```
Opens the frontend at `http://127.0.0.1:5173` (proxies `/api` to the backend at `:8000`).

### Run — production (one process serves the built SPA + API)

```bash
make start           # builds web/dist, then serves it from the same FastAPI process on :8000
```

### Seed historical data

```bash
make seed            # imports the 24 real evaluation/results/*.json runs into runs/ (idempotent)
```

### Test

```bash
make test            # original pipeline suite (175 tests, unmodified) + server (26 tests) + web (tsc/lint/vitest)
```

Demo mode is fully offline and deterministic — four scripted scenarios (first-pass PASS,
REVISE→PASS replaying the paper's 72.8→92.8 worked example, a safety-gate rejection, and a
FAILED_TO_CONVERGE plateau) exercise every terminal state and every page without ever calling
the live Gemini API, which is also how all automated verification works.

### Screenshots

Captured via `web/e2e/smoke.cjs` (Playwright) — Studio (live pipeline run), Runs, Dashboard, and
Settings & About, each in light/dark theme at desktop and tablet widths. Not committed to the
repo (generated artifacts); run the script locally against `make demo` to regenerate them under
`web/e2e/screenshots/`.

### Pages

- **Studio** — scenario builder (with the 12 benchmark presets one click away), a
  Verifier-guided / Direct-baseline / Compare mode switch, and the live pipeline view: a 5-stage
  stepper, an email preview card (always watermarked "SIMULATION," never a clickable link),
  Safety Gate / Verifier / Score panels, and the iteration convergence chart.
- **Runs** — searchable/filterable history of every stored run, with delete, download, re-run,
  and two-run compare actions.
- **Run Detail** — the same shared components as Studio's live view, replayed from a stored
  `RunRecord`, plus a raw-JSON toggle.
- **Dashboard** — KPI cards, terminal-state distribution, a safety-leakage chart (reproduces the
  paper's 0% vs. 25% figures from the 24 imported real runs), quality-by-condition, score and
  iteration histograms, role/difficulty breakdowns, and the 12-preset × 2-condition benchmark
  runner (behind an explicit confirmation dialog, since Live mode makes 24 real API calls).
- **Settings & About** — provider status and a reachability test, read-only pipeline
  configuration, the Live/Demo toggle, an inline-SVG architecture diagram, and the paper's own
  stated limitations.
