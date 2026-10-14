"""
core/generation/llm_client.py

Minimal shared LLM client wrapper for the Google Gemini API.

Exposes a single function: call_llm(prompt, temperature, max_tokens, json_mode) -> str

Kept minimal and shared here so the Verifier's Layer B judge (Phase 4) can
reuse the same call site without duplicating provider-specific setup.

Architecture rules (Document B v2 SS7):
  - No print() statements.
  - No CLI-specific logic.
  - Raises exceptions; callers handle presentation.
"""

from __future__ import annotations

import google.genai as genai
import google.genai.types as genai_types

import config


def call_llm(
    prompt: str,
    temperature: float,
    max_tokens: int,
    *,
    json_mode: bool = True,
    _client: genai.Client | None = None,
) -> str:
    """
    Send a single-turn prompt to the Gemini model and return the raw text response.

    Parameters
    ----------
    prompt:
        The complete prompt string to send.
    temperature:
        Sampling temperature (0.0-2.0 for Gemini; 0.8 for generator, 0.2 for verifier).
    max_tokens:
        Maximum number of output tokens (including thought tokens for reasoning models).
    json_mode:
        Whether to enforce application/json structured output from Gemini. Defaults to True.
    _client:
        Optional pre-constructed Gemini client -- used by tests to inject a mock
        without touching the real API. If None, a real client is created from
        config.GEMINI_API_KEY.

    Returns
    -------
    str
        The raw text content of the model's response.

    Raises
    ------
    ValueError
        If GEMINI_API_KEY is not set and no _client is provided, or if the model
        response is blocked/empty.
    google.genai.errors.APIError
        Propagated as-is for network/auth errors.
    """
    if _client is None:
        api_key = config.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Copy .env.example to .env and set your API key."
            )
        _client = genai.Client(api_key=api_key)

    # Relax DANGEROUS_CONTENT category to BLOCK_NONE specifically to allow
    # cybersecurity awareness training simulations (phishing lures with synthetic domains).
    # Other harm categories remain at their default protective thresholds.
    safety_settings = [
        genai_types.SafetySetting(
            category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
        ),
    ]

    gen_config = genai_types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        safety_settings=safety_settings,
        response_mime_type="application/json" if json_mode else None,
    )

    import time
    last_err = None
    for attempt in range(5):
        try:
            response = _client.models.generate_content(
                model=config.MODEL_NAME,
                contents=prompt,
                config=gen_config,
            )
            if response.text:
                return response.text
            finish_reason = None
            if hasattr(response, "candidates") and response.candidates:
                finish_reason = response.candidates[0].finish_reason
            raise ValueError(
                f"Gemini API returned an empty response. Finish reason: {finish_reason}"
            )
        except Exception as err:
            last_err = err
            err_str = str(err)
            if any(code in err_str for code in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "overloaded", "demand"]):
                time.sleep(3.0 * (attempt + 1))
                continue
            raise err

    raise last_err
