"""Provider and model options for the optional AI suggestions layer."""

from __future__ import annotations

PROVIDER_LABELS = {
    "gemini": "Gemini",
    "openai": "OpenAI",
    "claude": "Claude",
    "custom_openai_compatible": "Custom OpenAI-compatible",
}

STANDARD_PROVIDER_MODELS = {
    "gemini": [
        "gemini-3-flash",
        "gemini-3.1-pro",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
    ],
    "openai": [
        "gpt-5.4-mini",
        "gpt-5.4",
        "gpt-5.4-nano",
    ],
    "claude": [
        "claude-sonnet-4-6",
        "claude-opus-4-6",
        "claude-haiku-4-5",
    ],
}

DEFAULT_PROVIDER = "gemini"
DEFAULT_MODELS = {
    "gemini": "gemini-3-flash",
    "openai": "gpt-5.4-mini",
    "claude": "claude-sonnet-4-6",
}


def get_provider_choices() -> list[tuple[str, str]]:
    """Return provider choices for the UI dropdown."""
    return [(label, value) for value, label in PROVIDER_LABELS.items()]


def get_standard_model_options(provider: str) -> list[str]:
    """Return preset model options for a standard provider."""
    return STANDARD_PROVIDER_MODELS.get(provider, [])


def get_default_model(provider: str) -> str | None:
    """Return the preferred default model for a provider."""
    return DEFAULT_MODELS.get(provider)


def is_supported_provider(provider: str) -> bool:
    """Return whether the provider is recognised by the UI/service layer."""
    return provider in PROVIDER_LABELS


def is_supported_model(provider: str, model: str) -> bool:
    """Return whether a model is supported for a standard provider."""
    if provider == "custom_openai_compatible":
        return bool(model.strip())
    return model in STANDARD_PROVIDER_MODELS.get(provider, [])
