"""Configuration module for the Fitness & Nutrition Coach.

Handles loading of environment variables, secure retrieval of OpenAI
credentials, and configuration validation without exposing secrets.
"""

import os
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

# Default fallback model if OPENAI_MODEL is not explicitly defined
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def get_openai_api_key(override_key: Optional[str] = None) -> Optional[str]:
    """Retrieve the OpenAI API key securely.

    Priority:
    1. UI override provided by user in active session (not stored on disk)
    2. Environment variable OPENAI_API_KEY from .env or system environment

    Never prints, logs, or exposes the key.
    """
    if override_key and override_key.strip():
        return override_key.strip()
    key = os.getenv("OPENAI_API_KEY")
    if key and key.strip():
        return key.strip()
    return None


def get_openai_model(override_model: Optional[str] = None) -> str:
    """Retrieve the configured OpenAI model name.

    Priority:
    1. UI override provided by user
    2. Environment variable OPENAI_MODEL
    3. DEFAULT_OPENAI_MODEL (gpt-4o-mini)
    """
    if override_model and override_model.strip():
        return override_model.strip()
    model = os.getenv("OPENAI_MODEL")
    if model and model.strip():
        return model.strip()
    return DEFAULT_OPENAI_MODEL


def validate_api_key_configuration(api_key: Optional[str] = None) -> Tuple[bool, str]:
    """Validate whether an API key is configured and appears structurally plausible.

    Returns:
        (is_valid, status_message) - The status message never reveals the key content.
    """
    key = api_key if api_key is not None else get_openai_api_key()
    if not key:
        return (
            False,
            "OpenAI API key is missing. Set OPENAI_API_KEY in your .env file or enter it in the sidebar.",
        )

    # Basic structural verification without exposing content
    cleaned = key.strip()
    if cleaned in {"your_openai_api_key_here", "your_new_api_key_here", "sk-..."}:
        return (
            False,
            "Placeholder API key detected. Please configure a valid OpenAI API key in your .env file.",
        )

    if len(cleaned) < 20:
        return (
            False,
            "API key appears too short to be a valid OpenAI key format.",
        )

    return (True, "API key is configured.")
