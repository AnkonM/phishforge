# PhishForge

> **Verifier-Guided Generative AI for Adaptive Phishing-Awareness Simulation**

PhishForge is a closed-loop synthesis framework that creates personalized,
difficulty-calibrated, and **guaranteed-safe** phishing-awareness training simulations. Given an
organizational scenario specification, it generates a candidate training email and iteratively
evaluates it through a deterministic safety gate, a hybrid verifier (rule checks + LLM judge),
multi-dimensional scoring, and automated anti-drift refinement — until the simulation passes, or
the pipeline gives up and says so.

The repository has two parts:

- **The pipeline** (`core/`, `models/`, `config/`, `cli.py`) — a Python CLI tool. This is the
  original system and is unmodified by everything below.
- **The Console** (`server/`, `web/`) — a web UI and dashboard built on top of the pipeline, added
  as a separate, additive layer with **zero changes to any pipeline file**.

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Installation](#installation)
- [Usage — CLI](#usage--cli)
- [Usage — Console](#usage--console)
- [Testing](#testing)
- [Configuration](#configuration)
- [Safety design](#safety-design)
- [Documentation](#documentation)
- [Limitations](#limitations)

---

## Features

**Pipeline**
- Closed-loop generate → safety-check → verify → score → refine cycle, capped at 3 iterations
- Deterministic, fail-closed **Safety Gate**: 5 zero-LLM rule checks (no real domains, no
  credential harvesting, no dangerous attachments, no real brand impersonation, no real PII) that
  run before anything else and cannot be talked around by the generator or the judge
- Hybrid **Verifier**: Layer A deterministic rule checks (indicator coverage, language/structure)
  + Layer B LLM judge (realism, role relevance, difficulty calibration against a 4-level rubric)
- Weighted 5-dimension **Scoring Engine** (`Q ∈ [0, 100]`) with PASS/REVISE/FAIL bands
- **Refinement Controller** that turns verifier findings into targeted revision instructions, with
  plateau-based early stopping
- Two execution conditions: `verifier_guided` (full loop) and `baseline_direct` (single-shot, for
  methodology comparison)
- Serializable `RunRecord` JSON artifact for every run; 12-scenario curated benchmark suite
- 175 automated tests, 100% offline (no network calls)

**Console**
- **Studio** — build a scenario (with the 12 benchmark presets one click away), pick
  Verifier-guided / Direct-baseline / Compare mode, and watch the pipeline run live: a 5-stage
  stepper, a watermarked email preview, Safety Gate / Verifier / Score panels, and the iteration
  convergence chart, all streamed over Server-Sent Events
- **Runs** — searchable, filterable history with delete / download / re-run / compare
- **Run Detail** — the exact same live-view components, replayed from a stored record, plus a
  raw-JSON toggle and a word-level email diff between iterations
- **Dashboard** — KPIs, terminal-state distribution, a safety-leakage chart (reproduces the
  paper's reported 0% vs. 25% leakage from real historical runs), quality-by-condition, score and
  convergence histograms, role/difficulty breakdowns, and a one-click 12-preset × 2-condition
  benchmark runner (Demo or Live, behind a confirmation dialog)
- **Settings & About** — provider status, a reachability test, read-only pipeline configuration,
  a Live/Demo toggle, and an inline architecture diagram
- Fully offline **Demo mode**: four deterministic scripted scenarios (including an exact replay
  of the paper's 72.8 → 92.8 worked example) exercise every terminal state without ever touching
  the live Gemini API
- Light/dark theme, colorblind-safe status palette, responsive down to tablet width

---

## Architecture

### Pipeline — closed-loop synthesis

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

1. **Generator** — builds a structured prompt (with anti-drift revision instructions after
   iteration 1) and generates a schema-validated email simulation, with one JSON-repair retry.
2. **Safety Gate** — deterministic, zero-LLM, fail-closed. Any violation is an immediate hard
   stop (`REJECTED_UNSAFE`) — the verifier never even runs.
3. **Hybrid Verifier** — Layer A (deterministic rules) + Layer B (LLM judge at `temperature=0.2`).
4. **Scoring Engine** — weighted `Q = 0.25·realism + 0.25·relevance + 0.20·indicators +
   0.20·difficulty + 0.10·language`; bands at `PASS ≥ 80`, `REVISE 60–79`, `FAIL < 60`.
5. **Refinement Controller** — turns findings into imperative revision instructions; stops the
   loop on PASS, a 3-iteration ceiling, or a score-plateau (patience/epsilon thresholds).
6. **Orchestration** (`core/orchestration/run.py`) — drives the loop and emits a serializable
   `RunRecord`.

### Console — a wrapper, not a rewrite

```
                 ┌─────────────────────────┐        ┌──────────────────────────┐
                 │   web/ (React + TS)      │        │   server/ (FastAPI)      │
                 │                          │  HTTP  │                          │
                 │  Studio · Runs · Run     │◄──────►│  routers/*.py            │
                 │  Detail · Dashboard ·    │  SSE   │  run_worker.py           │
                 │  Settings                │◄──────►│  pipeline_bridge.py      │
                 └─────────────────────────┘        │  mock_provider.py        │
                                                      │  run_store.py            │
                                                      └────────────┬─────────────┘
                                                                   │ in-process calls,
                                                                   │ zero modifications
                                                                   ▼
                                                      ┌──────────────────────────┐
                                                      │  core/ · models/ · config/│
                                                      │  (the pipeline, above)    │
                                                      └──────────────────────────┘
```

`server/pipeline_bridge.py` wraps the pipeline's own stage functions with emit-before/after
instrumentation (using the `_generator_fn` / `_safety_gate_fn` / `_verifier_fn` / `_scoring_fn`
injection points the pipeline's own test suite already relies on) to turn its single
once-per-iteration callback into a fine-grained Server-Sent-Events stream. `run_worker.py` runs
the synchronous pipeline in a background thread per request and bridges it to that stream.
`run_store.py` persists `RunRecord`s as the exact same JSON files the CLI's `--out` flag already
produces. Full rationale for every design decision — and why no pipeline file needed to
change — is in [`docs/DECISIONS.md`](docs/DECISIONS.md).

---

## Project structure

```
phishforge/
├── core/                    # pipeline stages (generation, safety, verification, scoring, refinement, orchestration)
├── models/schemas/          # Pydantic schemas (ScenarioSpecification, RunRecord, ...)
├── config/                  # weights, thresholds, safety blocklists
├── prompts/                 # generator + verifier prompt templates
├── scenarios/               # example scenarios + the 12 benchmark presets
├── evaluation/               # benchmark runner, aggregate metrics, stored results
├── cli.py, __main__.py       # CLI entrypoint
├── tests/                   # 175 pipeline unit + integration tests
│
├── server/                  # FastAPI backend for the Console (additive, wraps core/ only)
│   ├── routers/              # health, config, presets, runs, benchmark
│   ├── pipeline_bridge.py    # instruments the real pipeline functions for SSE
│   ├── mock_provider.py      # scripted fake LLM client for Demo mode
│   ├── run_worker.py         # background-thread run execution + SSE bridging
│   ├── run_store.py          # RunRecord persistence (runs/*.json)
│   └── tests/                # 26 backend tests (mock-only)
│
├── web/                     # React + TypeScript frontend for the Console
│   ├── src/pages/             # Studio, Runs, RunDetail, Dashboard, Settings
│   ├── src/components/        # PipelineStepper, EmailCard, ConvergenceView, ...
│   ├── src/lib/                # api client, SSE handling, event reducer, formatting
│   └── e2e/smoke.cjs          # Playwright end-to-end smoke test + screenshots
│
├── runs/                    # persisted RunRecords (generated; gitignored)
├── docs/
│   ├── API.md                 # Console REST + SSE contract
│   ├── DESIGN.md               # Console visual design system
│   ├── DECISIONS.md            # every build judgment call, incl. why zero pipeline files changed
│   └── PAPER_COMPENDIUM.md     # the underlying research write-up
├── scripts/                 # dev.sh, seed_runs.py
└── Makefile                 # install / dev / demo / test / build / start
```

---

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm (only needed for the Console's frontend)
- A Google Gemini API key for Live mode ([Google AI Studio](https://aistudio.google.com/)) — not
  required for Demo mode or for running any of the test suites

### 1. Clone and configure
```bash
git clone <this-repo-url>
cd phishforge
cp .env.example .env
```
Edit `.env` and add your key:
```ini
GEMINI_API_KEY=your_google_ai_studio_api_key_here
```

### 2. Install

**Pipeline only (CLI usage):**
```bash
pip install -r requirements.txt
```

**Everything, including the Console** (creates a venv, installs Python + server deps, and runs
`npm install` for the frontend):
```bash
make install
```

---

## Usage — CLI

Run via `python -m phishforge run` (or `python cli.py run`).

```bash
# File-based run
python -m phishforge run --input scenarios/examples/finance_invoice_fraud.json --out result.json

# Flag-based run with live verbose tracing
python -m phishforge run \
    --role finance --scenario-type invoice_fraud --difficulty 3 \
    --indicators urgency,authority_impersonation,suspicious_link \
    --org-context "Mid-size UK accounting firm (~350 staff). Uses SAP for AP. Dual approval required above £10k." \
    --verbose --out run_trace.json

# Load a scenario template and override specific fields
python -m phishforge run --input scenarios/examples/finance_invoice_fraud.json --difficulty 4 --role executive --verbose

# Direct-only baseline (single-shot, bypasses Safety Gate/Verifier/Refinement)
python -m phishforge run --input scenarios/examples/finance_invoice_fraud.json --direct-only --out baseline_output.json

# Deterministic Safety Gate demonstration
python -m phishforge run --input scenarios/examples/unsafe_test_case.json --demo-unsafe --verbose --out unsafe_demo.json
```

<details>
<summary><strong>Full CLI options reference</strong></summary>

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
  --difficulty 1-4      Difficulty level: 1 (Obvious) to 4 (Expert).
  --indicators LIST     Comma-separated phishing indicators (e.g. 'urgency,suspicious_link').
  --org-context TEXT    Organizational context and background constraints.
  --language LANG       ISO 639-1 language code (default: 'en').
  --prohibited LIST     Comma-separated prohibited elements.
  --constraints JSON    JSON dictionary of simulation constraints.
  --out, -o FILE        Destination path to write the full RunRecord JSON artifact.
  --verbose, -v         Print live per-iteration quality scores, dimensions, and findings.
  --direct-only         Single-shot unverified generation (baseline_direct condition).
  --demo-unsafe         Demo flag: injects a known unsafe payload to demonstrate Safety Gate rejection.
```
</details>

---

## Usage — Console

```bash
make seed            # one-time: imports 24 real historical runs so Runs/Dashboard aren't empty

make dev             # backend (:8000) + frontend (:5173), both live-reloading
make demo            # same, but forces Demo mode (mock provider) regardless of key presence

make start           # production: builds web/dist, serves SPA + API from one process on :8000
```
Open `http://127.0.0.1:5173` (dev) or `http://127.0.0.1:8000` (production/`make start`).

Demo mode is fully offline and deterministic, driving four scripted scenarios — a first-pass
PASS, a REVISE→PASS arc (replaying the paper's 72.8 → 92.8 worked example for the matching
preset), a safety-gate rejection, and a FAILED_TO_CONVERGE plateau — so every page, chart, and
terminal state is explorable without an API key.

---

## Testing

```bash
make test            # everything: pipeline + server + web
make test-core        # original pipeline suite (175 tests)
make test-server       # Console backend suite (26 tests, mock-only, no network calls)
make test-web           # tsc --noEmit + lint + Vitest (19 tests)
```

All automated testing — pipeline and Console alike — runs entirely offline. The Console's
end-to-end smoke test (`web/e2e/smoke.cjs`, Playwright) drives all four Demo scenarios through
the real UI and captures screenshots of every page in both themes at desktop and tablet widths;
run it against `make demo` to regenerate them locally.

---

## Configuration

| Setting | Where | Notes |
|---|---|---|
| `GEMINI_API_KEY` | `.env` | Required for Live mode; never required for tests or Demo mode |
| Scoring weights, thresholds, iteration ceiling | `config/__init__.py` | Read-only from the Console (Settings page); never injectable per-run |
| Safety blocklists | `config/safety_blocklists.py` | Brand/domain/PII/attachment rules |
| `PHISHFORGE_DEMO` | env var | Forces the Console to Demo mode on startup |
| `PHISHFORGE_SERVER_PORT` | env var | Backend port (default `8000`) |

---

## Safety design

The Safety Gate is deterministic and fail-closed by construction — it runs zero LLM calls, cannot
be bypassed by a generator or judge that disagrees with it, and any rule-execution exception is
itself treated as a failure. The Console never softens, hides, or routes around it: a
`REJECTED_UNSAFE` run is shown honestly, with its findings, everywhere. Generated content is
always treated as untrusted display text (plain text only, never `dangerouslySetInnerHTML`),
sender addresses and links are never clickable, and every email preview carries a persistent
"SIMULATION — training content only" watermark.

---

## Documentation

- [`docs/API.md`](docs/API.md) — Console REST endpoints and the full SSE event schema
- [`docs/DESIGN.md`](docs/DESIGN.md) — Console visual design system (color, type, motion, charts)
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — every judgment call made building the Console, and
  why zero pipeline files needed to change
- [`docs/PAPER_COMPENDIUM.md`](docs/PAPER_COMPENDIUM.md) — the underlying research write-up

---

## Limitations

From the underlying research (surfaced in the Console's Settings & About page too):
- Small benchmark N (12 scenarios) — all statistics are descriptive, not inferential
- Human evaluation used a single rater
- The Layer B LLM judge is the same model family as the generator, which can share blind spots

Console-specific:
- Best-effort cancellation is implemented but not covered by an automated mid-run test (Demo-mode
  runs complete in well under a second)
- No automated accessibility audit (ARIA/focus/contrast were implemented by construction and
  reviewed manually, not run through an axe-core-style checker)
