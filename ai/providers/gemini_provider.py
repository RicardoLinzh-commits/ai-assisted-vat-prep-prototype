"""Minimal Gemini provider adapter for structured suggestions."""

from __future__ import annotations

import json
from urllib import error, request

from ai.types import AIRequestConfig, AIServiceError

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def _extract_gemini_text(response_payload: dict) -> str:
    """Extract text content from a Gemini generateContent response."""
    try:
        candidates = response_payload["candidates"]
        parts = candidates[0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIServiceError("AI response did not contain a usable message.") from exc

    text_parts = [str(part.get("text")) for part in parts if isinstance(part, dict) and part.get("text")]
    if not text_parts:
        raise AIServiceError("AI response did not contain a usable text part.")

    return "\n".join(text_parts).strip()


def generate_gemini_suggestions(prompt_package: dict[str, str], config: AIRequestConfig) -> str:
    """Request AI suggestions using Gemini generateContent."""
    base_url = (config.base_url or GEMINI_BASE_URL).rstrip("/")
    endpoint = f"{base_url}/models/{config.model}:generateContent"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"{prompt_package['system_prompt']}\n\n{prompt_package['user_prompt']}",
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
        },
    }

    request_body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        endpoint,
        data=request_body,
        headers={
            "x-goog-api-key": config.api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=config.timeout_seconds) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            error_body = ""
        raise AIServiceError(
            f"AI service request failed with HTTP {exc.code}. {error_body[:200]}".strip(),
            code="provider_request_failed",
        ) from exc
    except error.URLError as exc:
        raise AIServiceError("AI service network connection failed.", code="network_error") from exc
    except TimeoutError as exc:
        raise AIServiceError("AI service request timed out.", code="network_error") from exc
    except json.JSONDecodeError as exc:
        raise AIServiceError("AI service returned an unreadable response.", code="provider_response_error") from exc

    return _extract_gemini_text(response_payload)
