"""
tests/unit/test_human_eval_sampling.py

Sanity unit tests for human evaluation sample generation and blind anonymization integrity.

Run with: pytest tests/unit/test_human_eval_sampling.py -v
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKET_PATH = REPO_ROOT / "evaluation" / "human_eval" / "rating_packet.md"
ANSWER_KEY_PATH = REPO_ROOT / "evaluation" / "human_eval" / "answer_key.json"


class TestHumanEvalSamplingIntegrity:
    def test_files_exist(self):
        assert PACKET_PATH.exists(), "rating_packet.md must exist"
        assert ANSWER_KEY_PATH.exists(), "answer_key.json must exist"

    def test_sample_size_and_keys(self):
        with open(ANSWER_KEY_PATH, "r", encoding="utf-8") as f:
            answer_key = json.load(f)

        assert len(answer_key) == 12, "Must contain exactly 12 sample items"
        expected_keys = [f"sample_{i:02d}" for i in range(1, 13)]
        assert list(answer_key.keys()) == expected_keys

    def test_blind_anonymization_no_leaked_metadata(self):
        packet_content = PACKET_PATH.read_text(encoding="utf-8")

        # Must NOT contain experimental condition labels
        assert "verifier_guided" not in packet_content
        assert "baseline_direct" not in packet_content

        # Must NOT contain automated score variable names or terminal states
        assert "overall_score" not in packet_content
        assert "REJECTED_UNSAFE" not in packet_content
        assert "GENERATED_UNVERIFIED" not in packet_content
        assert "semantic_findings" not in packet_content

        # Must NOT mention answer_key
        assert "answer_key" not in packet_content

    def test_packet_has_twelve_items(self):
        packet_content = PACKET_PATH.read_text(encoding="utf-8")
        for i in range(1, 13):
            sample_id = f"sample_{i:02d}"
            assert sample_id in packet_content, f"Missing {sample_id} in rating packet"
