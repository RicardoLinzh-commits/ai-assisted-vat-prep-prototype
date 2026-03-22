"""Minimal Claude provider adapter for structured suggestions."""

from __future__ import annotations

import json
from urllib import error, request

from ai.types import AIRequestConfig, AIServiceError

CLAUDE_BASE_URL = "https://api.anthropic.com/v1"


def _extract_claude_text(response_payload: dict) -> str:
    """Extract text content from a Claude messages response."""
    try:
        content_items = response_payload["content"]
    except (KeyError, TypeError) as exc:
        raise AIServiceError("AI response did not contain a usable message.") from exc

    text_parts = [str(item.get("text")) for item in content_items if isinstance(item, dict) and item.get("text")]
    if not text_parts:
        raise AIServiceError("AI response did not contain a usable text part.")

    return "\n".join(text_parts).strip()


def generate_claude_suggestions(prompt_package: dict[str, str], config: AIRequestConfig) -> str:
    """Request AI suggestions using the Claude messages endpoint."""
    base_url = (config.base_url or CLAUDE_BASE_URL).rstrip("/")
    endpoint = f"{base_url}/messages"

    payload = {
        "model": config.model,
        "max_tokens": 800,
        "messages": [
            {
                "role": "user",
                "content": f"{prompt_package['system_prompt']}\n\n{prompt_package['user_prompt']}",
            }
        ],
    }

    request_body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        endpoint,
        data=request_body,
        headers={
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
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

    return _extract_claude_text(response_payload)
