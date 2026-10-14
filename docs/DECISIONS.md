# PhishForge Console — Decisions Log

Every judgment call made during the build, in the order it came up. Core pipeline files
(`core/`, `models/`, `config/`, `cli.py`) were **never modified** — this log also doubles as
the "core touchpoints" list the task requires: there are none, and this document explains why.

## Process

1. **Git.** The repo had no `.git` directory at all. Confirmed with the user: ran `git init`,
   committed the pre-existing code as-is on `main`, then created `feature/console` for all new
   work. No core files were touched by that first commit beyond adding `.gitignore`.
2. **Live API smoke test.** Confirmed with the user: after all automated (mock-only)
   verification passes, one real Studio scenario is run through the live Gemini API manually,
   outside the test suite, and its result is reported. No automated test ever calls the live API
   (enforced by `server/tests/conftest.py` forcing demo mode via `monkeypatch`, and verified
   directly by `test_no_key_leak.py` and by grepping test output for the live API host).

## Why zero core touchpoints were needed

Every seam the console needs already existed in the pipeline, built for its own test suite:
- `core.generation.llm_client.call_llm(..., _client=None)`, `generator.generate(spec,
  revision_instructions=None, *, _client=None)`, and `verifier.verify(spec, sim, *,
  _client=None)` all accept a pre-built `genai.Client`-shaped object. The mock provider
  (`server/mock_provider.py`) only ever needs to satisfy `client.models.generate_content(...).text`
  — nothing else.
- `run_scenario(..., _generator_fn=None, _safety_gate_fn=None, _verifier_fn=None,
  _scoring_fn=None)` — already used by the CLI's own `--demo-unsafe` flag and by
  `tests/integration/test_end_to_end.py`. `server/pipeline_bridge.py` instruments these with
  emit-before/after wrappers around the *real* functions, which is how the UI gets Generator /
  Safety Gate / Verifier / Scoring-level SSE granularity even though the real `on_iteration`
  callback only reports once per iteration.
- `core.refinement.refinement_controller.build_instructions()` is a pure, zero-LLM function.
  `server/pipeline_bridge.py`'s `scoring_fn` wrapper calls it directly on the just-scored
  `VerificationResult` to emit a `refinement_instruction` SSE event *before* `run_scenario`
  itself decides whether to terminate or continue — this is safe because `build_instructions`
  doesn't look at termination state at all, so the text it eagerly computes is identical to what
  `run.py`'s own `create_refinement_result` would compute moments later for the same
  `VerificationResult`, regardless of outcome.
- `evaluation/run_benchmark.py` already implements "generate once, then apply safety gate +
  verifier + scoring post-hoc" for `baseline_direct` — `server/run_worker.py::_run_direct`
  mirrors that exact sequence line-for-line rather than reinventing it, which is also why the UI
  can honestly label this mode "baseline (post-hoc checked)."

## Architecture

3. **Compare mode grouping.** `RunRecord` has no field for "these two runs are a pair." Rather
   than add one (a core schema change), `server/run_store.py` keeps a small sidecar file
   (`runs/_meta.json`) mapping `compare_group_id -> [run_id, run_id]`, written and read only by
   the server. The core `RunRecord` JSON files are untouched.
4. **"Imported" runs.** Same sidecar file also tracks which `run_id`s came from
   `scripts/seed_runs.py` importing `evaluation/results/*.json` (24 real historical runs — 12
   `verifier_guided` + 12 `baseline_direct`, from actual Gemini runs on 2026-08-28) vs. runs
   created live from the Console. No change to the RunRecord format either way.
5. **`run_id` reconciliation (bug found and fixed during manual SSE testing).**
   `run_scenario()` mints its own internal `run_id = str(uuid4())`, completely independent of
   the run id the server hands back to the client in `CreateRunResponse` and uses for the SSE
   URL. Left alone, the persisted file's `run_id` would never match the id the client was given,
   breaking `GET/DELETE /api/runs/{id}`. Fixed by overriding `record.run_id` via
   `record.model_copy(update={"run_id": handle.run_id})` right before persisting — a one-line
   server-side fix on the already-returned Pydantic object, not a change to `run_scenario()`.
6. **Best-effort cancellation.** None of `safety_fn`/`verifier_fn`/`scoring_fn`'s call sites in
   `run.py` are wrapped in `try/except`, so raising a `RunCancelled` sentinel from inside them (or
   from `on_iteration`) propagates straight out of `run_scenario` uncaught — a clean abort, no
   `RunRecord` persisted (correct: the pipeline never reached a real terminal state). The one call
   site that *is* wrapped (`gen_fn`, inside `except (GenerationFailure, Exception)`) swallows a
   cancellation into a `GENERATION_FAILURE` terminal state instead of propagating it; the worker
   still persists that record honestly (it's what the pipeline actually produced) and separately
   flags `cancelled: true` on the `run_finished` SSE event so the UI can show the distinction.
7. **NO_IMPROVEMENT is unreachable under the shipped config — verified, not assumed.** Policy
   precedence in `run.py` checks the iteration ceiling (`iteration_idx >= MAX_ITERATIONS`, i.e.
   `>= 3`) *before* the plateau check (`should_stop_early`, which needs `patience + 1 = 3` scores
   to ever return `True`). Since the ceiling check always fires first at iteration 3, and
   `should_stop_early` can only possibly return `True` once 3 scores exist (i.e. also at iteration
   3 at the earliest), the ceiling always wins. Confirmed empirically: the Console's "plateau"
   demo script and a hand-constructed small-delta sequence both terminate
   `FAILED_TO_CONVERGE` / `termination_reason=MAX_ITERATIONS`, never `NO_IMPROVEMENT`. The UI
   therefore shows whatever `termination_reason` the record actually contains rather than
   assuming "plateau" implies `NO_IMPROVEMENT` — consistent with the task's own instruction to
   never invent a termination rule the record doesn't contain.
8. **Mock provider script selection.** Four scripted scenarios (first-pass PASS, REVISE→PASS,
   safety-gate rejection, plateau/ceiling) are picked automatically by difficulty
   (`pick_default_script`) unless the caller passes an explicit `demo_script`. `bench-01-it-pwd-d1`
   is special-cased to replay the *actual* recorded iteration content and judge scores from
   `evaluation/results/verifier_guided_bench-01-it-pwd-d1.json` verbatim (72.8 → 92.8), matching
   the paper's own worked example exactly rather than a parameterized approximation. The
   `safety_reject` script is never auto-picked for a benchmark preset (all 12 are legitimate
   scenarios) — it's reachable only via an explicit `demo_script` choice, mirroring the CLI's own
   opt-in `--demo-unsafe` flag.
9. **Mock scores validated against the real deterministic rule checks, not asserted.**
   `core.verification.rule_checks.check_indicators` treats an indicator as satisfied if it's
   literally present in `GeneratedSimulation.intended_indicators`, independent of keyword
   matching — so every mock simulation sets `intended_indicators = spec.desired_indicators`
   exactly, which is what makes `indicator_score == 100` deterministic and *earned* (by the real
   rule, not hardcoded) rather than faked.
10. **Dashboard safety-leakage metric reproduces the paper's own reported numbers.** Computed
    purely from the 24 imported historical runs (`leaked = safety_result.passed is False AND
    score >= PASS_THRESHOLD`, over runs where both exist): `baseline_direct` comes out to 25.0%
    (3/12) and `verifier_guided` to 0.0% (0/10 — REJECTED_UNSAFE runs have no score, since
    verification never runs after a gate failure in guided mode, so they can't be "leaked" by this
    definition, which is correct: guided mode cannot leak unsafe content past a PASS by
    construction). These match the paper's claimed 0% vs 25% figures from real data, not invented
    constants.

## Testing infrastructure

11. **`starlette.testclient.TestClient` is incompatible with this app's background-thread SSE
    bridge.** Found via a genuine test hang (not assumed): `TestClient`'s synchronous wrapper
    opens a fresh `anyio` event loop per call and closes it immediately after each
    request/response, including `POST /api/runs`, whose response returns before the pipeline
    worker thread finishes. That thread's later `loop.call_soon_threadsafe(...)` calls then target
    an already-closed loop, which silently fails to ever wake the SSE endpoint's
    `await handle.new_event.wait()` — the GET stream hangs forever. Confirmed with a standalone
    repro script and a full traceback (`RuntimeError: Event loop is closed`). This is a test-harness
    artifact, not a production bug: a real `uvicorn` process keeps exactly one event loop alive for
    its entire lifetime (confirmed independently via manual `curl` smoke tests against a running
    `python -m server.main` process, including the exact 72.8→92.8 replay). Fixed by switching the
    whole server test suite to `httpx.AsyncClient` + `pytest-asyncio`, so one event loop stays
    alive for an entire async test function (matching real server behavior) instead of per-call.
