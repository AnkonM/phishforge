from __future__ import annotations

from datetime import datetime, timezone

from models.schemas.run import RunRecord
from models.schemas.scenario import ScenarioSpecification
from server.stats import compute_stats


def _spec(role="it", difficulty=1) -> ScenarioSpecification:
    return ScenarioSpecification(
        organization_context="Test org.",
        target_role=role,
        scenario_type="password_alert",
        difficulty=difficulty,
        desired_indicators=["urgency"],
    )


def _record(condition, terminal_state, score, safety_passed, role="it", difficulty=1, n_iter=1) -> RunRecord:
    iterations = []
    for i in range(1, n_iter + 1):
        is_last = i == n_iter
        iterations.append({
            "iteration_number": i,
            "simulation": {"subject": "x"},
            "safety_result": {"passed": safety_passed, "status": "PASS" if safety_passed else "FAIL", "findings": []},
            "verification": {
                "realism_score": 80.0, "relevance_score": 80.0, "indicator_score": 100.0,
                "difficulty_score": 80.0, "language_score": 100.0, "overall_score": score,
                "pass_fail": "PASS" if score >= 80 else "REVISE",
            } if (is_last and score is not None) else None,
            "score": score if is_last else None,
            "refinement": None,
        })
    return RunRecord(
        run_id=f"r-{condition}-{terminal_state}-{score}-{role}-{difficulty}-{n_iter}",
        scenario=_spec(role, difficulty),
        condition=condition,
        iterations=iterations,
        terminal_state=terminal_state,
        created_at=datetime.now(timezone.utc),
    )


def test_pass_rate_and_mean_score():
    records = [
        _record("verifier_guided", "PASS", 90.0, True),
        _record("verifier_guided", "PASS", 85.0, True),
        _record("verifier_guided", "FAILED_TO_CONVERGE", 70.0, True, n_iter=3),
    ]
    stats = compute_stats(records)
    assert stats["total_runs"] == 3
    assert stats["pass_rate_pct"] == round(2 / 3 * 100, 1)
    assert stats["mean_final_score"] == round((90.0 + 85.0 + 70.0) / 3, 1)
    assert stats["mean_iterations"] == round((1 + 1 + 3) / 3, 1)


def test_rejected_unsafe_rate():
    # REJECTED_UNSAFE runs genuinely have no score -- the safety gate fails
    # before verification ever runs, so score=None here mirrors reality.
    records = [
        _record("verifier_guided", "REJECTED_UNSAFE", None, False),
        _record("verifier_guided", "PASS", 90.0, True),
    ]
    stats = compute_stats(records)
    assert stats["rejected_unsafe_rate_pct"] == 50.0


def test_safety_leakage_only_counts_runs_with_both_safety_and_score():
    # A baseline run that violates the gate but would have scored >= 80 is
    # "leaked"; a guided run can never leak by construction (no score exists
    # when the gate fails -- verification is skipped before any PASS).
    leaked = _record("baseline_direct", "GENERATED_UNVERIFIED", 85.0, False)
    not_leaked = _record("baseline_direct", "GENERATED_UNVERIFIED", 60.0, False)
    safe_pass = _record("baseline_direct", "GENERATED_UNVERIFIED", 90.0, True)
    stats = compute_stats([leaked, not_leaked, safe_pass])
    leakage = stats["safety_leakage"]["baseline_direct"]
    assert leakage["total"] == 3
    assert leakage["leaked"] == 1
    assert leakage["rate_pct"] == round(1 / 3 * 100, 1)


def test_quality_by_condition_means():
    records = [_record("verifier_guided", "PASS", 90.0, True) for _ in range(2)]
    stats = compute_stats(records)
    assert stats["quality_by_condition"]["verifier_guided"]["realism_score"] == 80.0


def test_by_role_and_by_difficulty_breakdowns():
    records = [
        _record("verifier_guided", "PASS", 90.0, True, role="it", difficulty=1),
        _record("verifier_guided", "FAILED_TO_CONVERGE", 70.0, True, role="hr", difficulty=2, n_iter=3),
    ]
    stats = compute_stats(records)
    assert stats["by_role"]["it"]["total"] == 1
    assert stats["by_role"]["it"]["pass_rate_pct"] == 100.0
    assert stats["by_difficulty"]["2"]["total"] == 1
    assert stats["by_difficulty"]["2"]["pass_rate_pct"] == 0.0


def test_empty_records_do_not_divide_by_zero():
    stats = compute_stats([])
    assert stats["total_runs"] == 0
    assert stats["pass_rate_pct"] == 0.0
    assert stats["mean_final_score"] == 0.0
