"""Unit tests for workout plan generation, progression rules, and equipment adaptation."""

import pytest
from fitness.models import (
    FitnessGoal,
    UserProfile,
    WorkoutExperience,
)
from fitness.workouts import (
    generate_workout_plan,
    get_exercise_alternatives,
    get_warmup_cooldown_routine,
)


def test_beginner_workout_plan():
    """Verify beginner plan produces 3-day full body structure."""
    profile = UserProfile(
        age=22,
        height_cm=175.0,
        weight_kg=70.0,
        fitness_goal=FitnessGoal.GENERAL_FITNESS,
        workout_experience=WorkoutExperience.BEGINNER,
        available_equipment=["dumbbells"],
    )
    plan = generate_workout_plan(profile)
    assert plan.frequency_days == 3
    assert len(plan.sessions) == 3
    assert "Full-Body" in plan.title or "Beginner" in plan.title
    assert len(plan.sessions[0].exercises) >= 4
    assert plan.progression_advice is not None
    assert "STOP IF YOU FEEL PAIN" in plan.safety_reminder


def test_intermediate_workout_plan():
    """Verify intermediate plan produces 4-day upper/lower split."""
    profile = UserProfile(
        age=29,
        height_cm=180.0,
        weight_kg=82.0,
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
        workout_experience=WorkoutExperience.INTERMEDIATE,
        available_equipment=["full gym"],
    )
    plan = generate_workout_plan(profile)
    assert plan.frequency_days == 4
    assert len(plan.sessions) == 4
    assert "Upper / Lower" in plan.title or "Intermediate" in plan.title
    assert "Progressive Overload" in plan.progression_advice


def test_advanced_workout_plan():
    """Verify advanced plan produces 5-day periodized split."""
    profile = UserProfile(
        age=32,
        height_cm=182.0,
        weight_kg=85.0,
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
        workout_experience=WorkoutExperience.ADVANCED,
        available_equipment=["full gym"],
    )
    plan = generate_workout_plan(profile)
    assert plan.frequency_days == 5
    assert len(plan.sessions) == 5
    assert "Advanced" in plan.title


def test_bodyweight_only_exercises():
    """Verify plan accommodates home bodyweight-only equipment."""
    profile = UserProfile(
        age=26,
        height_cm=168.0,
        weight_kg=62.0,
        fitness_goal=FitnessGoal.WEIGHT_LOSS,
        workout_experience=WorkoutExperience.BEGINNER,
        available_equipment=["bodyweight"],
    )
    plan = generate_workout_plan(profile)
    session = plan.sessions[0]
    # Check that exercises are bodyweight appropriate
    for ex in session.exercises:
        assert "barbell" not in ex.name.lower()


def test_exercise_alternatives():
    """Verify exercise substitution suggestions based on equipment."""
    bench_alts = get_exercise_alternatives("Barbell Bench Press", ["dumbbells"])
    assert len(bench_alts) > 0
    assert any("dumbbell" in alt.lower() for alt in bench_alts)

    squat_alts = get_exercise_alternatives("Barbell Back Squat", ["bodyweight"])
    assert len(squat_alts) > 0
    assert any("bodyweight" in alt.lower() or "split squat" in alt.lower() for alt in squat_alts)


def test_warmup_cooldown_routine():
    """Verify warm-up and cool-down guides."""
    routine = get_warmup_cooldown_routine()
    assert "warmup" in routine
    assert "cooldown" in routine
    assert "mobility" in routine["warmup"].lower()
    assert "stretching" in routine["cooldown"].lower()
