"""Unit tests for config.py environment and API key configuration handling."""

import os
from unittest import mock
import pytest
from config import (
    DEFAULT_OPENAI_MODEL,
    get_openai_api_key,
    get_openai_model,
    validate_api_key_configuration,
)


def test_default_model():
    """Verify default model fallback is gpt-4o-mini."""
    with mock.patch.dict(os.environ, {}, clear=True):
        model = get_openai_model()
        assert model == DEFAULT_OPENAI_MODEL


def test_custom_model_env():
    """Verify OPENAI_MODEL environment variable is respected."""
    with mock.patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4o"}, clear=True):
        model = get_openai_model()
        assert model == "gpt-4o"


def test_model_override():
    """Verify override_model argument takes highest precedence."""
    with mock.patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4o"}, clear=True):
        model = get_openai_model("gpt-3.5-turbo")
        assert model == "gpt-3.5-turbo"


def test_missing_api_key():
    """Verify behavior when no API key is provided."""
    with mock.patch.dict(os.environ, {}, clear=True):
        key = get_openai_api_key()
        assert key is None
        is_valid, msg = validate_api_key_configuration(key)
        assert is_valid is False
        assert "missing" in msg.lower()


def test_placeholder_api_key_rejected():
    """Verify placeholder keys from template are flagged as invalid."""
    placeholders = [
        "your_openai_api_key_here",
        "your_new_api_key_here",
        "sk-...",
    ]
    for ph in placeholders:
        is_valid, msg = validate_api_key_configuration(ph)
        assert is_valid is False
        assert "placeholder" in msg.lower()


def test_short_api_key_rejected():
    """Verify structurally truncated keys are rejected without revealing secrets."""
    is_valid, msg = validate_api_key_configuration("sk-short123")
    assert is_valid is False
    assert "too short" in msg.lower()
    # Ensure key itself is NOT printed in the error message
    assert "sk-short123" not in msg


def test_valid_format_api_key():
    """Verify valid-looking API key string is accepted."""
    test_key = "sk-proj-1234567890abcdefghijklmnopqrstuvwxyz"
    is_valid, msg = validate_api_key_configuration(test_key)
    assert is_valid is True
    assert "configured" in msg.lower()
    # Ensure key itself is not leaked
    assert test_key not in msg


def test_api_key_override_precedence():
    """Verify explicit override key supersedes environment variable."""
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-1234567890abcdef12345"}, clear=True):
        override = "sk-override-1234567890abcdef12345"
        key = get_openai_api_key(override_key=override)
        assert key == override
