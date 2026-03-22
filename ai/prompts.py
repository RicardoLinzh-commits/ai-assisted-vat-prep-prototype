"""Prompt helpers for the optional AI suggestions layer."""

from __future__ import annotations

import json

FIXED_REMINDER_SENTENCE = (
    "This is only a statistical prompt based on the data. "
    "Please make sure you check the original invoice before making any final decision."
)

FIXED_BOUNDARY_PROMPT = (
    "You explain only the existing findings snapshot. You do not perform detection, "
    "you do not provide tax evasion, avoidance, or concealment advice, you do not make "
    "filing or compliance decisions, you do not treat anomaly flags as confirmed errors, "
    "and you do not suggest deceptive record changes. "
    f"You must end the response with this exact sentence: {FIXED_REMINDER_SENTENCE}"
)

DEFAULT_EDITABLE_EXPLANATION_PROMPT = (
    "Please explain the findings in clear and natural English for a non-technical UK micro-business owner. "
    "Summarize the most important problems first, then explain what should be checked first. "
    "Keep the explanation concise and practical. Use UK business language where appropriate. "
    "If anomaly values are mentioned, explain that they are prompts for review rather than confirmed errors."
)


def build_prompt_package(
    snapshot: dict,
    editable_explanation_prompt: str,
    advanced_instructions: str | None = None,
) -> dict[str, str]:
    """Build the final prompt package in the required order."""
    user_parts = [
        "Findings snapshot:",
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        "Editable explanation prompt:",
        editable_explanation_prompt.strip(),
    ]

    if advanced_instructions and advanced_instructions.strip():
        user_parts.extend(
            [
                "Advanced instructions:",
                advanced_instructions.strip(),
            ]
        )

    return {
        "system_prompt": FIXED_BOUNDARY_PROMPT,
        "user_prompt": "\n\n".join(user_parts),
    }


def enforce_fixed_reminder(text: str) -> str:
    """Ensure the AI output ends with the fixed reminder sentence."""
    cleaned = text.strip()
    if cleaned.endswith(FIXED_REMINDER_SENTENCE):
        return cleaned
    if cleaned:
        return f"{cleaned}\n\n{FIXED_REMINDER_SENTENCE}"
    return FIXED_REMINDER_SENTENCE
