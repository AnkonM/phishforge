"""
tests/unit/test_scoring.py

Unit tests for the Deterministic Scoring Engine (Phase 5).
Validates mathematical formula precision, boundary classifications,
and real live Phase 4 verification results.

Run with: pytest tests/unit/test_scoring.py -v
"""

import json
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import config
from core.scoring.scoring_engine import classify_band, compute
from models.schemas.verification import VerificationResult

# ---------------------------------------------------------------------------
# Fixture Helpers
# ---------------------------------------------------------------------------


def _make_verification(**kwargs) -> VerificationResult:
    base = {
        "verification_id": str(uuid.uuid4()),
        "generation_id": str(uuid.uuid4()),
        "realism_score": 80.0,
        "relevance_score": 80.0,
        "indicator_score": 80.0,
        "difficulty_score": 80.0,
        "language_score": 80.0,
        "safety_status": "PASS",
        "safety_findings": [],
        "semantic_findings": [],
        "overall_score": 0.0,
        "pass_fail": "FAIL",
        "verifier_version": "rules-v1+llm-v1",
    }
    base.update(kwargs)
    return VerificationResult(**base)


# ===========================================================================
# 1. Config Weights Integrity
# ===========================================================================


class TestScoringWeightsIntegrity:
    def test_weights_sum_to_one(self):
        total = sum(config.SCORING_WEIGHTS.values())
        assert total == pytest.approx(1.0, rel=1e-5)

    def test_all_five_dimensions_present(self):
        expected_keys = {
            "realism",
            "role_relevance",
            "indicator_coverage",
            "difficulty_match",
            "language_quality",
        }
        assert set(config.SCORING_WEIGHTS.keys()) == expected_keys


# ===========================================================================
# 2. Mathematical Formula Precision (Hand-calculated checks)
# ===========================================================================


class TestFormulaCorrectness:
    def test_all_100s_produces_100_pass(self):
        v = _make_verification(
            realism_score=100.0,
            relevance_score=100.0,
            indicator_score=100.0,
            difficulty_score=100.0,
            language_score=100.0,
        )
        res = compute(v)
        assert res.overall_score == 100.0
        assert res.pass_fail == "PASS"

    def test_hand_calculated_mixture_revise(self):
        # 0.25*80 (20) + 0.25*70 (17.5) + 0.20*60 (12) + 0.20*90 (18) + 0.10*50 (5) = 72.5
        v = _make_verification(
            realism_score=80.0,
            relevance_score=70.0,
            indicator_score=60.0,
            difficulty_score=90.0,
            language_score=50.0,
        )
        res = compute(v)
        assert res.overall_score == 72.5
        assert res.pass_fail == "REVISE"

    def test_hand_calculated_low_score_fail(self):
        # 0.25*30 (7.5) + 0.25*40 (10) + 0.20*20 (4) + 0.20*30 (6) + 0.10*50 (5) = 32.5
        v = _make_verification(
            realism_score=30.0,
            relevance_score=40.0,
            indicator_score=20.0,
            difficulty_score=30.0,
            language_score=50.0,
        )
        res = compute(v)
        assert res.overall_score == 32.5
        assert res.pass_fail == "FAIL"


# ===========================================================================
# 3. Exact Threshold Boundary Tests
# ===========================================================================


class TestThresholdBoundaries:
    def test_boundary_80_0_is_pass(self):
        assert classify_band(80.0) == "PASS"

    def test_boundary_79_9_is_revise(self):
        assert classify_band(79.9) == "REVISE"

    def test_boundary_60_0_is_revise(self):
        assert classify_band(60.0) == "REVISE"

    def test_boundary_59_9_is_fail(self):
        assert classify_band(59.9) == "FAIL"


# ===========================================================================
# 4. Real Phase 4 Live Verification Results
# ===========================================================================


class TestRealPhase4Scoring:
    def test_strong_live_verification_scores_pass(self):
        """
        Strong live result from Phase 4:
        realism=92, relevance=96, indicator=100, difficulty=92, language=100
        Expected: 0.25*92 + 0.25*96 + 0.20*100 + 0.20*92 + 0.10*100 = 95.4 (PASS)
        """
        strong_v = _make_verification(
            realism_score=92.0,
            relevance_score=96.0,
            indicator_score=100.0,
            difficulty_score=92.0,
            language_score=100.0,
        )
        res = compute(strong_v)
        assert res.overall_score == 95.4
        assert res.pass_fail == "PASS"

    def test_weak_live_verification_scores_fail(self):
        """
        Weak live result from Phase 4:
        realism=15, relevance=20, indicator=66.7, difficulty=15, language=95
        Expected: 0.25*15 + 0.25*20 + 0.20*66.7 + 0.20*15 + 0.10*95 = 34.6 (FAIL)
        """
        weak_v = _make_verification(
            realism_score=15.0,
            relevance_score=20.0,
            indicator_score=66.7,
            difficulty_score=15.0,
            language_score=95.0,
        )
        res = compute(weak_v)
        assert res.overall_score == 34.6
        assert res.pass_fail == "FAIL"
