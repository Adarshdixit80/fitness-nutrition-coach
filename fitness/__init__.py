"""Fitness & Nutrition Coach package."""

from fitness.models import (
    UserProfile,
    FitnessGoal,
    BiologicalSex,
    ActivityLevel,
    DietaryPreference,
    WorkoutExperience,
)
from fitness.nutrition import (
    calculate_bmr,
    calculate_tdee,
    calculate_target_calories,
    calculate_macronutrients,
    generate_sample_meal_plan,
    estimate_food_nutrition,
    get_food_substitutions,
)
from fitness.workouts import (
    generate_workout_plan,
    get_exercise_alternatives,
    get_warmup_cooldown_routine,
)
from fitness.safety import (
    evaluate_user_safety,
    MEDICAL_DISCLAIMER,
)

__all__ = [
    "UserProfile",
    "FitnessGoal",
    "BiologicalSex",
    "ActivityLevel",
    "DietaryPreference",
    "WorkoutExperience",
    "calculate_bmr",
    "calculate_tdee",
    "calculate_target_calories",
    "calculate_macronutrients",
    "generate_sample_meal_plan",
    "estimate_food_nutrition",
    "get_food_substitutions",
    "generate_workout_plan",
    "get_exercise_alternatives",
    "get_warmup_cooldown_routine",
    "evaluate_user_safety",
    "MEDICAL_DISCLAIMER",
]
