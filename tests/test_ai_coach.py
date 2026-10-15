"""Unit tests for OpenAI AI Coach service, mocking API calls to ensure zero billing and robust error handling."""

from unittest import mock
import pytest
import openai
from fitness.ai_coach import AICoachService, build_system_prompt
from fitness.models import (
    ActivityLevel,
    BiologicalSex,
    DietaryPreference,
    FitnessGoal,
    UserProfile,
    WorkoutExperience,
)


def test_build_system_prompt_with_profile():
    """Verify system prompt accurately integrates user metrics and target macros."""
    profile = UserProfile(
        age=30,
        biological_sex=BiologicalSex.MALE,
        height_cm=180.0,
        weight_kg=80.0,
        fitness_goal=FitnessGoal.WEIGHT_LOSS,
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        dietary_preference=DietaryPreference.VEGETARIAN,
        allergies=["peanuts"],
        workout_experience=WorkoutExperience.INTERMEDIATE,
        available_equipment=["dumbbells"],
    )
    prompt = build_system_prompt(profile)
    assert "30 years old" in prompt
    assert "180.0 cm" in prompt
    assert "80.0 kg" in prompt
    assert "Weight Loss" in prompt
    assert "Vegetarian" in prompt
    assert "peanuts" in prompt
    assert "Mifflin-St Jeor" in prompt
    assert "CORE SAFETY & ETHICAL RULES" in prompt


def test_missing_api_key_handling():
    """Verify missing API key returns clear error without making external API calls."""
    service = AICoachService(api_key="")
    response, error = service.generate_chat_response(
        messages=[{"role": "user", "content": "Hello coach"}],
        profile=None,
        stream=False,
    )
    assert response == ""
    assert error is not None
    assert "missing" in error.lower()


def test_safety_interception_before_api_call():
    """Verify acute emergencies or eating disorders are intercepted prior to calling OpenAI API."""
    service = AICoachService(api_key="sk-test-mocked-key-1234567890abcdef")
    
    with mock.patch("openai.OpenAI") as mock_openai:
        response, error = service.generate_chat_response(
            messages=[{"role": "user", "content": "I am having chest pain while doing bench press"}],
            profile=None,
            stream=False,
        )
        # OpenAI client should NOT have been called
        mock_openai.assert_not_called()
        assert "Safety Notice" in response
        assert "emergency" in response.lower()
        assert error is None


def test_mocked_successful_chat_completion():
    """Verify successful response generation using a mocked OpenAI client."""
    service = AICoachService(api_key="sk-test-mocked-key-1234567890abcdef", model="gpt-4o-mini")

    mock_choice = mock.MagicMock()
    mock_choice.message.content = "Great question! Aim for 25-30g of protein per meal to optimize muscle protein synthesis."
    
    mock_completion = mock.MagicMock()
    mock_completion.choices = [mock_choice]

    with mock.patch("fitness.ai_coach.openai.OpenAI") as mock_client_cls:
        mock_instance = mock.MagicMock()
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_client_cls.return_value = mock_instance

        messages = [{"role": "user", "content": "How much protein should I eat per meal?"}]
        response, error = service.generate_chat_response(messages=messages, stream=False)

        assert error is None
        assert "protein synthesis" in response
        mock_instance.chat.completions.create.assert_called_once()
        call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert len(call_kwargs["messages"]) == 2  # 1 system + 1 user


def test_mocked_authentication_error_handling():
    """Verify AuthenticationError is caught and handled with user-friendly message."""
    service = AICoachService(api_key="sk-test-mocked-key-1234567890abcdef")

    with mock.patch("fitness.ai_coach.openai.OpenAI") as mock_client_cls:
        mock_instance = mock.MagicMock()
        mock_instance.chat.completions.create.side_effect = openai.AuthenticationError(
            message="Invalid API Key",
            response=mock.MagicMock(status_code=401),
            body=None,
        )
        mock_client_cls.return_value = mock_instance

        messages = [{"role": "user", "content": "Hi"}]
        response, error = service.generate_chat_response(messages=messages, stream=False)

        assert response == ""
        assert error is not None
        assert "Authentication failed" in error


def test_mocked_rate_limit_error_handling():
    """Verify RateLimitError is handled cleanly."""
    service = AICoachService(api_key="sk-test-mocked-key-1234567890abcdef")

    with mock.patch("fitness.ai_coach.openai.OpenAI") as mock_client_cls:
        mock_instance = mock.MagicMock()
        mock_instance.chat.completions.create.side_effect = openai.RateLimitError(
            message="Quota exceeded",
            response=mock.MagicMock(status_code=429),
            body=None,
        )
        mock_client_cls.return_value = mock_instance

        messages = [{"role": "user", "content": "Hi"}]
        response, error = service.generate_chat_response(messages=messages, stream=False)

        assert response == ""
        assert error is not None
        assert "Rate limit exceeded" in error
