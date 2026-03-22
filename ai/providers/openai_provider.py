"""Minimal OpenAI provider adapter for structured suggestions."""

from __future__ import annotations

import json
from urllib import error, request

from ai.types import AIRequestConfig, AIServiceError

OPENAI_BASE_URL = "https://api.openai.com/v1"


def _extract_message_content(response_payload: dict) -> str:
    """Extract plain text content from a chat completions response."""
    try:
        message = response_payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIServiceError("AI response did not contain a usable message.") from exc

    if isinstance(message, str):
        return message.strip()

    if isinstance(message, list):
        parts: list[str] = []
        for item in message:
            if isinstance(item, dict) and item.get("type") == "text":
                text_value = item.get("text")
                if text_value:
                    parts.append(str(text_value))
        if parts:
            return "\n".join(parts).strip()

    raise AIServiceError("AI response format was not recognised.")


def generate_openai_suggestions(prompt_package: dict[str, str], config: AIRequestConfig) -> str:
    """Request AI suggestions using an OpenAI-compatible chat completions route."""
    base_url = (config.base_url or OPENAI_BASE_URL).rstrip("/")
    endpoint = f"{base_url}/chat/completions"

    payload = {
        "model": config.model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": prompt_package["system_prompt"]},
            {"role": "user", "content": prompt_package["user_prompt"]},
        ],
    }

    request_body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        endpoint,
        data=request_body,
        headers={
            "Authorization": f"Bearer {config.api_key}",
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

    return _extract_message_content(response_payload)
