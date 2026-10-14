"""
PhishForge configuration package.

All configuration constants are defined here at the package level so that
import config; config.MODEL_NAME works correctly.

Provider: Google Gemini (switched from Anthropic, approved 2026-08-28).
Model: models/gemini-3.6-flash -- current stable Flash-tier model.

The config/ directory also contains safety_blocklists.py (Phase 3),
accessible as from config.safety_blocklists import ...

Source of truth: Document B v2 SS18 (provider swap approved).
"""

import os

# LLM / Model settings
# Provider: Google Gemini (google-genai SDK v2.20.0)
# gemini-3.6-flash chosen: stable, free-tier eligible, good instruction-following.

MODEL_NAME = "models/gemini-3.5-flash-lite"

GENERATOR_TEMPERATURE = 0.8
VERIFIER_TEMPERATURE = 0.2

# Token limits increased for Gemini reasoning/thought token headroom
GENERATOR_MAX_TOKENS = 4096
VERIFIER_MAX_TOKENS = 2048

# Scoring thresholds / bands

PASS_THRESHOLD = 80
REVISE_THRESHOLD = 60
DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 4

BAND_PASS = "PASS"
BAND_REVISE = "REVISE"
BAND_FAIL = "FAIL"

# Refinement / loop control

MAX_ITERATIONS = 3
IMPROVEMENT_EPSILON = 2.0
IMPROVEMENT_PATIENCE = 2

# Scoring weights (must sum to 1.0)

SCORING_WEIGHTS = {
    "realism": 0.25,
    "role_relevance": 0.25,
    "indicator_coverage": 0.20,
    "difficulty_match": 0.20,
    "language_quality": 0.10,
}

# Supported enumeration values

SUPPORTED_ROLES = [
    "finance",
    "hr",
    "it",
    "sales",
    "operations",
    "executive",
]

SUPPORTED_SCENARIO_TYPES = [
    "invoice_fraud",
    "password_alert",
    "hr_document_request",
    "delivery_expense_notification",
    "account_verification",
    "internal_policy_update",
]

# API keys (read from environment / .env - never hard-coded)
# GEMINI_API_KEY: active provider key (Google AI Studio)
# ANTHROPIC_API_KEY: retained for documentation / future re-use

def _load_dotenv_if_present() -> None:
    # Look for .env in repo root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    if k not in os.environ:
                        os.environ[k] = v.strip()

_load_dotenv_if_present()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")