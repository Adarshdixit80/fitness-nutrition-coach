"""Unit tests for nutrition calculations, formulas, macro distribution, and profile validation."""

import pytest
from pydantic import ValidationError
from fitness.models import (
    ActivityLevel,
    BiologicalSex,
    DietaryPreference,
    FitnessGoal,
    UserProfile,
    WorkoutExperience,
)
from fitness.nutrition import (
    calculate_bmr,
    calculate_macronutrients,
    calculate_target_calories,
    calculate_tdee,
    estimate_food_nutrition,
    generate_sample_meal_plan,
    get_food_substitutions,
)


def test_bmr_calculation_male():
    """Verify Mifflin-St Jeor formula for a 30yo, 80kg, 180cm male:
    10*80 + 6.25*180 - 5*30 + 5 = 800 + 1125 - 150 + 5 = 1780 kcal.
    """
    bmr = calculate_bmr(weight_kg=80.0, height_cm=180.0, age=30, sex=BiologicalSex.MALE)
    assert bmr == 1780.0


def test_bmr_calculation_female():
    """Verify Mifflin-St Jeor formula for a 25yo, 60kg, 165cm female:
    10*60 + 6.25*165 - 5*25 - 161 = 600 + 1031.25 - 125 - 161 = 1345.25 kcal.
    """
    bmr = calculate_bmr(weight_kg=60.0, height_cm=165.0, age=25, sex=BiologicalSex.FEMALE)
    assert bmr == 1345.25


def test_bmr_calculation_other():
    """Verify average midpoint assumption for BiologicalSex.OTHER."""
    bmr_other = calculate_bmr(weight_kg=70.0, height_cm=170.0, age=30, sex=BiologicalSex.OTHER)
    bmr_male = calculate_bmr(weight_kg=70.0, height_cm=170.0, age=30, sex=BiologicalSex.MALE)
    bmr_female = calculate_bmr(weight_kg=70.0, height_cm=170.0, age=30, sex=BiologicalSex.FEMALE)
    assert round(bmr_other, 1) == round((bmr_male + bmr_female) / 2.0, 1)


def test_tdee_calculation():
    """Verify TDEE with moderate activity factor (1.55)."""
    bmr = 1780.0
    tdee = calculate_tdee(bmr, ActivityLevel.MODERATELY_ACTIVE)
    assert round(tdee, 1) == 2759.0


def test_target_calories_for_goals():
    """Verify calorie adjustment for weight loss (-450) and muscle gain (+350)."""
    tdee = 2500.0
    loss, is_safe, _ = calculate_target_calories(tdee, FitnessGoal.WEIGHT_LOSS, BiologicalSex.MALE)
    assert loss == 2050
    assert is_safe is True

    gain, is_safe, _ = calculate_target_calories(tdee, FitnessGoal.MUSCLE_GAIN, BiologicalSex.MALE)
    assert gain == 2850
    assert is_safe is True

    maint, is_safe, _ = calculate_target_calories(tdee, FitnessGoal.MAINTENANCE, BiologicalSex.MALE)
    assert maint == 2500
    assert is_safe is True


def test_minimum_safe_calorie_floor():
    """Verify that calculated calories are never allowed to fall below biological minimum safety floors."""
    # A low TDEE that would result in < 1200 kcal for female
    low_tdee = 1300.0
    target, is_safe, note = calculate_target_calories(low_tdee, FitnessGoal.WEIGHT_LOSS, BiologicalSex.FEMALE)
    # 1300 - 450 = 850 -> must floor at 1200
    assert target == 1200
    assert is_safe is False
    assert note is not None
    assert "minimum safe intake" in note.lower()


def test_macronutrient_distribution():
    """Verify macronutrient calculation and proportions."""
    profile = UserProfile(
        age=28,
        biological_sex=BiologicalSex.MALE,
        height_cm=175.0,
        weight_kg=75.0,
        fitness_goal=FitnessGoal.WEIGHT_LOSS,
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        dietary_preference=DietaryPreference.NON_VEGETARIAN,
    )
    macros = calculate_macronutrients(profile)
    assert macros.bmr > 1500
    assert macros.tdee > macros.bmr
    assert macros.protein_grams > 0
    assert macros.fat_grams > 0
    assert macros.carbs_grams > 0
    # Percentages sum to approx 100
    assert 98 <= (macros.protein_pct + macros.carbs_pct + macros.fat_pct) <= 102
    assert "Mifflin-St Jeor" in macros.explanation


def test_user_profile_validation():
    """Verify Pydantic profile validation rules."""
    # Valid profile
    profile = UserProfile(
        age=25,
        height_cm=170.0,
        weight_kg=68.0,
        allergies=["peanuts", "milk"],
    )
    assert profile.bmi == 23.5
    assert profile.bmi_category == "Normal weight"
    assert "peanuts" in profile.allergies

    # Invalid age (< 13)
    with pytest.raises(ValidationError):
        UserProfile(age=10, height_cm=170.0, weight_kg=65.0)

    # Invalid age (> 100)
    with pytest.raises(ValidationError):
        UserProfile(age=105, height_cm=170.0, weight_kg=65.0)

    # Invalid height (< 100cm)
    with pytest.raises(ValidationError):
        UserProfile(age=25, height_cm=80.0, weight_kg=65.0)

    # Invalid weight (< 30kg)
    with pytest.raises(ValidationError):
        UserProfile(age=25, height_cm=170.0, weight_kg=20.0)


def test_food_nutrition_estimates():
    """Verify food nutrition estimate lookup."""
    info = estimate_food_nutrition("chicken breast")
    assert info is not None
    assert info["calories"] == 165
    assert info["protein"] == 31.0
    assert "disclaimer" in info

    oats = estimate_food_nutrition("rolled oats")
    assert oats is not None
    assert oats["calories"] == 150

    unknown = estimate_food_nutrition("random_nonexistent_item_xyz")
    assert unknown is None


def test_food_substitutions():
    """Verify food substitution helper."""
    subs = get_food_substitutions("chicken breast")
    assert len(subs) > 0
    assert any("tofu" in s.lower() for s in subs)

    peanut_subs = get_food_substitutions("peanut butter")
    assert any("sunflower" in s.lower() for s in peanut_subs)


def test_sample_meal_plan_allergies():
    """Verify that user allergies are removed from meal plans."""
    profile = UserProfile(
        age=30,
        biological_sex=BiologicalSex.FEMALE,
        height_cm=165.0,
        weight_kg=60.0,
        fitness_goal=FitnessGoal.MAINTENANCE,
        dietary_preference=DietaryPreference.VEGAN,
        allergies=["nuts", "peanuts"],
    )
    plan = generate_sample_meal_plan(profile, target_calories=1800)
    assert plan.target_calories == 1800
    assert len(plan.breakfast) > 0
    assert len(plan.lunch) > 0
    assert len(plan.dinner) > 0
    assert len(plan.snacks) > 0
    # Check that allergen is flagged or replaced
    for meal in plan.breakfast + plan.lunch + plan.dinner + plan.snacks:
        assert "peanut" not in meal.name.lower()
