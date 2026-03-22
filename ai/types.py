"""Shared types for the optional AI suggestions layer."""

from __future__ import annotations

from dataclasses import dataclass


class AIServiceError(RuntimeError):
    """Raised when the optional AI suggestions service cannot complete a request."""

    def __init__(self, message: str, code: str = "service_error") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class AIRequestConfig:
    """Configuration for an optional AI suggestion request."""

    provider: str
    model: str
    api_key: str
    base_url: str | None = None
    timeout_seconds: int = 20
