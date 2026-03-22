"""Service layer for optional AI suggestions."""

from __future__ import annotations

import os
import logging

from ai.provider_catalog import DEFAULT_MODELS, DEFAULT_PROVIDER, is_supported_model, is_supported_provider
from ai.prompts import build_prompt_package, enforce_fixed_reminder
from ai.providers.claude_provider import generate_claude_suggestions
from ai.providers.gemini_provider import generate_gemini_suggestions
from ai.providers.openai_provider import generate_openai_suggestions
from ai.types import AIRequestConfig, AIServiceError

LOGGER = logging.getLogger(__name__)

DEFAULT_UNAVAILABLE_MESSAGE = (
    "Enhanced AI suggestions are currently unavailable. The local explanation is still available."
)
DEFAULT_SERVICE_ERROR_MESSAGE = (
    "Enhanced AI suggestions are currently unavailable right now. The local explanation is still available."
)
ADVANCED_MISSING_INPUT_MESSAGE = (
    "To request enhanced suggestions, select a provider, choose a model, and enter an API key after running the analysis."
)
ADVANCED_NO_SNAPSHOT_MESSAGE = (
    "Run the analysis first so enhanced suggestions can use the current findings snapshot."
)
ADVANCED_PROVIDER_REQUIRED_MESSAGE = "Select a provider before requesting enhanced suggestions."
ADVANCED_MODEL_REQUIRED_MESSAGE = "Select a model before requesting enhanced suggestions."
ADVANCED_CUSTOM_MODEL_REQUIRED_MESSAGE = "Enter a custom model before requesting enhanced suggestions."
ADVANCED_API_KEY_REQUIRED_MESSAGE = "Enter an API key before requesting enhanced suggestions."
ADVANCED_UNSUPPORTED_PROVIDER_MESSAGE = "The selected AI provider is not supported by this prototype configuration."
ADVANCED_UNSUPPORTED_MODEL_MESSAGE = "The selected model is not available for that provider in this prototype."
ADVANCED_PROVIDER_FAILED_MESSAGE = "The provider request failed. Please check the model, API key, or provider service."
ADVANCED_NETWORK_ERROR_MESSAGE = "The provider request could not be completed because the network or AI service is unavailable."
SUCCESS_PREFIX = "_Suggestions generated from the current findings snapshot._"


def _parse_timeout(value: str | None) -> int:
    """Parse a timeout value conservatively."""
    try:
        return max(5, int(value)) if value is not None else 20
    except ValueError:
        return 20


def get_default_ai_config() -> AIRequestConfig | None:
    """Return a default AI configuration when one is available through environment variables."""
    provider = os.getenv("VAT_AI_PROVIDER")
    timeout_seconds = _parse_timeout(os.getenv("VAT_AI_TIMEOUT_SECONDS"))

    if provider:
        resolved_provider = provider.strip().lower()
        return _build_default_config_for_provider(resolved_provider, timeout_seconds)

    for candidate_provider in [DEFAULT_PROVIDER, "openai", "claude"]:
        config = _build_default_config_for_provider(candidate_provider, timeout_seconds)
        if config is not None:
            return config

    return None


def _build_default_config_for_provider(provider: str, timeout_seconds: int) -> AIRequestConfig | None:
    """Build a default config for a specific provider from environment variables."""
    provider_specific_api_keys = {
        "gemini": [os.getenv("GEMINI_API_KEY"), os.getenv("GOOGLE_API_KEY"), os.getenv("VAT_AI_API_KEY")],
        "openai": [os.getenv("OPENAI_API_KEY"), os.getenv("VAT_AI_API_KEY")],
        "claude": [os.getenv("ANTHROPIC_API_KEY"), os.getenv("VAT_AI_API_KEY")],
        "custom_openai_compatible": [os.getenv("VAT_AI_API_KEY"), os.getenv("OPENAI_API_KEY")],
    }
    provider_specific_models = {
        "gemini": [os.getenv("GEMINI_MODEL"), os.getenv("VAT_AI_MODEL")],
        "openai": [os.getenv("OPENAI_MODEL"), os.getenv("VAT_AI_MODEL")],
        "claude": [os.getenv("CLAUDE_MODEL"), os.getenv("ANTHROPIC_MODEL"), os.getenv("VAT_AI_MODEL")],
        "custom_openai_compatible": [os.getenv("VAT_AI_MODEL"), os.getenv("OPENAI_MODEL")],
    }
    provider_specific_base_urls = {
        "gemini": [os.getenv("GEMINI_BASE_URL"), os.getenv("VAT_AI_BASE_URL")],
        "openai": [os.getenv("OPENAI_BASE_URL"), os.getenv("VAT_AI_BASE_URL")],
        "claude": [os.getenv("ANTHROPIC_BASE_URL"), os.getenv("VAT_AI_BASE_URL")],
        "custom_openai_compatible": [os.getenv("VAT_AI_BASE_URL"), os.getenv("OPENAI_BASE_URL")],
    }

    api_key = next((value for value in provider_specific_api_keys.get(provider, []) if value), None)
    if not api_key:
        return None

    model = next((value for value in provider_specific_models.get(provider, []) if value), None)
    if not model:
        model = DEFAULT_MODELS.get(provider)
    if not model:
        return None

    base_url = next((value for value in provider_specific_base_urls.get(provider, []) if value), None)
    return AIRequestConfig(
        provider=provider,
        model=model.strip(),
        api_key=api_key,
        base_url=base_url.strip() if base_url else None,
        timeout_seconds=timeout_seconds,
    )


def _generate_suggestions(prompt_package: dict[str, str], config: AIRequestConfig) -> str:
    """Route a suggestion request to the configured provider."""
    provider_name = config.provider.strip().lower()
    if provider_name == "gemini":
        return generate_gemini_suggestions(prompt_package, config)
    if provider_name == "openai":
        return generate_openai_suggestions(prompt_package, config)
    if provider_name == "claude":
        return generate_claude_suggestions(prompt_package, config)
    if provider_name == "custom_openai_compatible":
        return generate_openai_suggestions(prompt_package, config)

    raise AIServiceError(f"Unsupported AI provider: {config.provider}", code="unsupported_provider")


def _map_advanced_error_to_message(error: AIServiceError) -> str:
    """Convert service-layer errors into calm user-facing messages."""
    if error.code == "unsupported_provider":
        return ADVANCED_UNSUPPORTED_PROVIDER_MESSAGE
    if error.code == "network_error":
        return ADVANCED_NETWORK_ERROR_MESSAGE
    if error.code in {"provider_request_failed", "provider_response_error"}:
        return ADVANCED_PROVIDER_FAILED_MESSAGE
    return DEFAULT_SERVICE_ERROR_MESSAGE


def try_generate_default_ai_suggestions(
    snapshot: dict,
    editable_explanation_prompt: str,
    advanced_instructions: str | None = None,
) -> str:
    """Attempt default AI suggestions and return a calm fallback on failure."""
    config = get_default_ai_config()
    if config is None:
        return DEFAULT_UNAVAILABLE_MESSAGE

    prompt_package = build_prompt_package(snapshot, editable_explanation_prompt, advanced_instructions)

    try:
        LOGGER.info("Default AI suggestions attempting provider call: provider=%s model=%s", config.provider, config.model)
        suggestion_text = _generate_suggestions(prompt_package, config)
        LOGGER.info("Default AI suggestions provider call succeeded: provider=%s model=%s", config.provider, config.model)
    except AIServiceError as exc:
        LOGGER.warning(
            "Default AI suggestions provider call failed: provider=%s model=%s code=%s",
            config.provider,
            config.model,
            exc.code,
        )
        return DEFAULT_SERVICE_ERROR_MESSAGE

    return f"{SUCCESS_PREFIX}\n\n{enforce_fixed_reminder(suggestion_text)}"


def generate_advanced_ai_suggestions(
    snapshot: dict | None,
    provider: str,
    model: str,
    custom_model: str,
    base_url: str,
    api_key: str,
    editable_explanation_prompt: str,
    advanced_instructions: str | None = None,
) -> str:
    """Attempt enhanced AI suggestions using user-supplied settings."""
    LOGGER.info("Advanced AI suggestions handler entered")
    LOGGER.info("Advanced AI suggestions snapshot available: %s", bool(snapshot))
    if not snapshot:
        LOGGER.info("Advanced AI suggestions provider call not attempted: missing snapshot")
        return ADVANCED_NO_SNAPSHOT_MESSAGE

    if not provider.strip():
        LOGGER.info("Advanced AI suggestions provider call not attempted: missing provider")
        return ADVANCED_PROVIDER_REQUIRED_MESSAGE
    if not editable_explanation_prompt.strip():
        LOGGER.info("Advanced AI suggestions provider call not attempted: missing editable prompt")
        return ADVANCED_MISSING_INPUT_MESSAGE
    if not api_key:
        LOGGER.info("Advanced AI suggestions provider call not attempted: missing API key")
        return ADVANCED_API_KEY_REQUIRED_MESSAGE

    provider_name = provider.strip().lower()
    LOGGER.info("Advanced AI suggestions selected provider: %s", provider_name)
    if not is_supported_provider(provider_name):
        LOGGER.info("Advanced AI suggestions provider call not attempted: unsupported provider=%s", provider_name)
        return ADVANCED_UNSUPPORTED_PROVIDER_MESSAGE

    final_model = custom_model.strip() if provider_name == "custom_openai_compatible" else model.strip()
    if not final_model:
        LOGGER.info("Advanced AI suggestions provider call not attempted: missing model")
        if provider_name == "custom_openai_compatible":
            return ADVANCED_CUSTOM_MODEL_REQUIRED_MESSAGE
        return ADVANCED_MODEL_REQUIRED_MESSAGE

    LOGGER.info("Advanced AI suggestions selected model: %s", final_model)
    if not is_supported_model(provider_name, final_model):
        LOGGER.info(
            "Advanced AI suggestions provider call not attempted: unsupported provider/model combination provider=%s model=%s",
            provider_name,
            final_model,
        )
        return ADVANCED_UNSUPPORTED_MODEL_MESSAGE

    config = AIRequestConfig(
        provider=provider_name,
        model=final_model,
        api_key=api_key,
        base_url=base_url.strip() or None,
        timeout_seconds=20,
    )
    prompt_package = build_prompt_package(snapshot, editable_explanation_prompt, advanced_instructions)

    try:
        LOGGER.info("Advanced AI suggestions provider call attempted: provider=%s model=%s", config.provider, config.model)
        suggestion_text = _generate_suggestions(prompt_package, config)
        LOGGER.info("Advanced AI suggestions provider call succeeded: provider=%s model=%s", config.provider, config.model)
    except AIServiceError as exc:
        LOGGER.warning(
            "Advanced AI suggestions provider call failed: provider=%s model=%s code=%s",
            config.provider,
            config.model,
            exc.code,
        )
        return _map_advanced_error_to_message(exc)

    return f"{SUCCESS_PREFIX}\n\n{enforce_fixed_reminder(suggestion_text)}"
