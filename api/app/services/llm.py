"""Unified LLM client. v1 backs onto OpenAI.

The interface is provider-neutral: callers ask for a JSON-shaped completion
with a system prompt and a user prompt. This wrapper handles model selection,
retries, JSON parsing, and graceful fallback when no key is present.

Architecture note for the panel: this is intentionally provider-flexible.
Switching to a self-hosted Llama or Mistral for data-residency mandates is a
single-file change.
"""
from __future__ import annotations

import json
import os
from typing import Any

from app.config import get_settings


class LLMUnavailable(Exception):
    """Raised when no LLM key is configured."""


def _get_client():
    settings = get_settings()
    key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return None, None, None
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=key)
        return client, settings.openai_model_strong, settings.openai_model_fast
    except Exception:
        return None, None, None


def is_available() -> bool:
    client, _, _ = _get_client()
    return client is not None


def chat_json(
    *,
    system_prompt: str,
    user_prompt: str,
    use_fast_model: bool = False,
    max_tokens: int = 2000,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Call the LLM and parse a JSON response.

    Returns the parsed JSON. Raises LLMUnavailable if no client. On parse error,
    raises ValueError with the offending text. Caller should fall back gracefully.
    """
    client, strong, fast = _get_client()
    if client is None:
        raise LLMUnavailable("No OPENAI_API_KEY configured")

    model = fast if use_fast_model else strong
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = resp.choices[0].message.content or ""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}; first 500 chars: {text[:500]}")


def get_strong_model_label() -> str:
    settings = get_settings()
    return settings.openai_model_strong


def get_fast_model_label() -> str:
    settings = get_settings()
    return settings.openai_model_fast
