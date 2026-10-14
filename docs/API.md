# PhishForge Console API

FastAPI backend under `server/`, mounted at `/api`. Binds to `127.0.0.1` only. Single local
user, no auth. CORS allows only the Vite dev origin (`http://127.0.0.1:5173`). The Gemini API
key is read server-side from `config.GEMINI_API_KEY` (loaded from `.env` at repo root) and is
**never** returned by any endpoint or logged (see `server/tests/test_no_key_leak.py`).

All request/response bodies are JSON. Pydantic request models use `extra="forbid"` — unknown
fields are rejected with 422.

## Endpoints

### `GET /api/health`
Liveness + current provider mode.
```json
{"status": "ok", "mode": "demo" | "live", "key_configured": true}
```

### `PUT /api/health/mode`
Switches the global Live/Demo toggle (also settable from the Settings page).
Request: `{"mode": "demo" | "live"}` → same shape as `GET /api/health`.

### `POST /api/health/reachability`
Lightweight check that the configured key can reach the Gemini API (lists models; does not run
the pipeline or spend generation tokens). `{"reachable": bool, "detail": str}`.

### `GET /api/config`
Read-only pipeline configuration, derived directly from the real source (never hand-duplicated):
`scoring_weights`, `pass_threshold`, `revise_threshold`, `max_iterations`, `improvement_epsilon`,
`improvement_patience`, `supported_roles`, `supported_scenario_types`, `safety_rules` (name +
description, from each safety-gate function's own docstring), `difficulty_rubric` (level, label,
description, parsed from the verifier prompt template), `model_name`.

### `GET /api/presets`
The 12 benchmark scenario specs from `scenarios/benchmark/*.json`, as an array of
`ScenarioSpecification`.

### `POST /api/runs`
Starts a run. Body:
```json
{"spec": ScenarioSpecification, "mode": "guided" | "direct" | "compare", "demo_script": "first_pass" | "revise_pass" | "safety_reject" | "plateau" | null}
```
`demo_script` is Demo-mode only; omitted/`null` picks automatically by difficulty (see
`server/mock_provider.py::pick_default_script`; `bench-01-it-pwd-d1` always replays the paper's
exact worked example). Ignored in Live mode.

Returns `202` immediately:
- `guided` / `direct`: `{"run_id": "<uuid>", "compare_group_id": null, "run_ids": null}`
- `compare`: `{"run_id": null, "compare_group_id": "<uuid>", "run_ids": ["<guided-id>", "<direct-id>"]}`
  — starts two independent runs (one `verifier_guided`, one `baseline_direct` on the same spec).

### `GET /api/runs/{run_id}/events`
`text/event-stream`. Replays every buffered event for that run (so a late or reconnecting
client gets full history) then streams live until `run_finished`. See **SSE event schema** below.

### `GET /api/runs`
List stored run summaries. Query params (all optional, AND-combined): `state` (terminal state),
`role`, `difficulty` (int), `mode` (condition), `q` (free-text search over org context, scenario
type, run id, role). Sorted newest first.

### `GET /api/runs/{run_id}`
Full record: `{"record": RunRecord, "compare_group_id": str | null, "imported": bool}`.
`RunRecord` is exactly the core pipeline's own schema (`models/schemas/run.py`), unmodified.

### `DELETE /api/runs/{run_id}`
204 on success, 404 if not found.

### `POST /api/runs/{run_id}/cancel`
Best-effort. `{"cancelled": bool}` — `false` if the run already finished or doesn't exist.

### `GET /api/stats`
Dashboard aggregates computed over every stored `RunRecord` (live + imported). See
`server/stats.py`. Always includes `n_note` reminding the UI this is descriptive-only.

### `POST /api/benchmark`
Body: `{"mode": "live" | "demo"}`. Runs all 12 presets × 2 conditions (24 pipeline runs)
sequentially in the background. Returns `{"benchmark_id": "<uuid>"}` immediately.

### `GET /api/benchmark/{benchmark_id}/events`
`text/event-stream` of benchmark progress — see **Benchmark event schema** below.

## SSE event schema (run events)

One JSON object per `data:` frame. Every event carries `event`, `run_id`, `ts` (ISO 8601 UTC),
and `iteration` where applicable.

| event | payload (beyond the common fields) | fires |
|---|---|---|
| `run_started` | `condition`, `demo_script` | once, immediately |
| `iteration_started` | — | once per generation attempt |
| `generation_started` | — | before calling the real `generate()` |
| `generation_complete` | `simulation: GeneratedSimulation` | after `generate()` returns |
| `safety_result` | `result: SafetyCheckResult` | after the real, unmodified safety gate runs |
| `verification_result` | `result: VerificationResult` | after the real verifier runs (skipped if safety failed) |
| `score_result` | `overall_score`, `pass_fail`, `result: VerificationResult` | after the real scoring engine runs |
| `refinement_instruction` | `instructions`, `weaknesses` | computed via the real, pure `build_instructions()` right after scoring — accurate for both continuing and terminal iterations (see docs/DECISIONS.md) |
| `iteration_status` | `status` (one of the real callback's own values: `GENERATED_UNVERIFIED`, `GENERATION_FAILURE`, `REJECTED_UNSAFE`, `PASS`, `FAILED_TO_CONVERGE`, `REVISE`) | mirrors the real `on_iteration` callback |
| `error` | `stage`, `message` | on a caught failure (e.g. generation failure) |
| `run_finished` | `terminal_state` (a real `TerminalState`, or `CANCELLED`/`ERROR`), `cancelled: bool`, `record: RunRecord` (omitted if cancelled before any record existed) | once, terminates the stream |

A `safety_reject` run emits `run_started → iteration_started → generation_started →
generation_complete → safety_result → run_finished` — no `verification_result`/`score_result`,
matching the real pipeline's short-circuit.

## Benchmark event schema

| event | payload |
|---|---|
| `benchmark_started` | `total` (24), `mode` |
| `scenario_started` | `index`, `total`, `scenario_id`, `condition` |
| `scenario_finished` | `index`, `total`, `scenario_id`, `condition`, `run_id`, `terminal_state`, `score` |
| `scenario_error` | `scenario_id`, `condition`, `message` |
| `benchmark_finished` | — |

## Frontend consumption

`web/src/lib/runReducer.ts` is the single typed reducer that turns a `RunEvent` stream into a
`RunViewState` (stepper stage states, per-iteration data, terminal state). `buildViewStateFromRecord()`
in the same file builds the identical shape directly from a stored `RunRecord`, so every shared
component (`PipelineStepper`, `EmailCard`, `GatePanel`, `VerifierPanel`, `ScorePanel`,
`ConvergenceView`, `DiffView`) renders live Studio runs and static Run Detail pages with zero
duplicated logic.
