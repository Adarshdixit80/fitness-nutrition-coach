"""Unit tests for safety guardrails, emergency detection, eating disorder detection, and disclaimers."""

import pytest
from fitness.models import UserProfile
from fitness.safety import (
    MEDICAL_DISCLAIMER,
    evaluate_user_safety,
    get_safety_system_prompt_addendum,
)


def test_medical_disclaimer_content():
    """Verify medical disclaimer clearly states educational scope and emergency advice."""
    assert "educational" in MEDICAL_DISCLAIMER.lower()
    assert "substitute for professional medical advice" in MEDICAL_DISCLAIMER.lower()
    assert "chest pain" in MEDICAL_DISCLAIMER.lower()


def test_acute_medical_symptom_detection():
    """Verify acute symptoms are flagged as emergencies."""
    queries = [
        "I feel severe chest pain while lifting heavy weights",
        "I blacked out after my last set of squats",
        "I am having tightness in chest and left arm numbness",
    ]
    for q in queries:
        result = evaluate_user_safety(q)
        assert result.is_safe is False
        assert result.warning_flag == "ACUTE_MEDICAL_EMERGENCY"
        assert "emergency" in result.recommended_action.lower()


def test_eating_disorder_and_starvation_detection():
    """Verify extreme restriction or disordered eating triggers protective warnings and helplines."""
    queries = [
        "I want to eat 500 calories a day to lose 20 pounds fast",
        "I struggle with bulimia and purge after meals",
        "How do I starve myself without feeling hungry?",
    ]
    for q in queries:
        result = evaluate_user_safety(q)
        assert result.is_safe is False
        assert result.warning_flag == "EATING_DISORDER_RISK"
        assert "NEDA" in result.recommended_action or "helpline" in result.recommended_action.lower()


def test_dangerous_substances_detection():
    """Verify banned anabolic steroids and dangerous fat burners are flagged."""
    queries = [
        "What is the best cycle of trenbolone and anavar for beginners?",
        "How much DNP should I take to burn belly fat?",
        "Should I buy SARMs rad140 online to get huge?",
    ]
    for q in queries:
        result = evaluate_user_safety(q)
        assert result.is_safe is False
        assert result.warning_flag == "UNSAFE_SUBSTANCES"
        assert "natural" in result.warning_message.lower()


def test_safe_fitness_query():
    """Verify normal fitness inquiries pass safety checks cleanly."""
    queries = [
        "How much protein should I eat for muscle recovery?",
        "Can you suggest a dumbbell leg workout?",
        "What are some healthy vegetarian breakfast options?",
    ]
    for q in queries:
        result = evaluate_user_safety(q)
        assert result.is_safe is True
        assert result.warning_flag is None


def test_special_population_caution():
    """Verify pregnancy or minor profiles receive advisory warnings."""
    result = evaluate_user_safety("Can I continue lifting heavy during pregnancy?")
    assert result.is_safe is True
    assert result.warning_flag == "SPECIAL_POPULATION_CAUTION"
    assert "obstetrician" in result.recommended_action.lower()


def test_safety_system_prompt_rules():
    """Verify system prompt injects strict safety boundaries."""
    prompt_text = get_safety_system_prompt_addendum()
    assert "NEVER diagnose medical conditions" in prompt_text
    assert "NEVER recommend extreme calorie deficits" in prompt_text
    assert "NEVER recommend anabolic steroids" in prompt_text
