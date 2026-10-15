"""Data validation models using Pydantic for user profiles, workouts, and nutrition."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class BiologicalSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class FitnessGoal(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    GENERAL_FITNESS = "general_fitness"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"  # Little or no exercise (desk job)
    LIGHTLY_ACTIVE = "lightly_active"  # Light exercise 1-3 days/week
    MODERATELY_ACTIVE = "moderately_active"  # Moderate exercise 3-5 days/week
    VERY_ACTIVE = "very_active"  # Hard exercise 6-7 days/week
    EXTRA_ACTIVE = "extra_active"  # Very hard exercise, physical job or training twice a day


class DietaryPreference(str, Enum):
    NON_VEGETARIAN = "non_vegetarian"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"


class WorkoutExperience(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class UserProfile(BaseModel):
    """User profile data model with thorough field validation."""

    age: int = Field(
        ...,
        ge=13,
        le=100,
        description="Age of the user in years (must be between 13 and 100).",
    )
    biological_sex: BiologicalSex = Field(
        default=BiologicalSex.MALE,
        description="Biological sex used for Mifflin-St Jeor metabolic baseline calculation.",
    )
    height_cm: float = Field(
        ...,
        ge=100.0,
        le=250.0,
        description="Height in centimetres (must be between 100cm and 250cm).",
    )
    weight_kg: float = Field(
        ...,
        ge=30.0,
        le=300.0,
        description="Weight in kilograms (must be between 30kg and 300kg).",
    )
    fitness_goal: FitnessGoal = Field(
        default=FitnessGoal.GENERAL_FITNESS,
        description="Primary fitness objective.",
    )
    activity_level: ActivityLevel = Field(
        default=ActivityLevel.MODERATELY_ACTIVE,
        description="Lifestyle physical activity factor.",
    )
    dietary_preference: DietaryPreference = Field(
        default=DietaryPreference.NON_VEGETARIAN,
        description="Dietary lifestyle preference.",
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="List of food allergies or dietary restrictions (e.g. peanuts, dairy, gluten).",
    )
    workout_experience: WorkoutExperience = Field(
        default=WorkoutExperience.BEGINNER,
        description="Training background and lifting experience level.",
    )
    available_equipment: List[str] = Field(
        default_factory=lambda: ["bodyweight"],
        description="Available workout equipment (e.g., dumbbells, resistance bands, full gym).",
    )
    medical_notes: Optional[str] = Field(
        default=None,
        description="Optional health, past injury, or medical context.",
    )

    @field_validator("allergies", mode="before")
    @classmethod
    def sanitize_allergies(cls, v):
        if isinstance(v, str):
            items = [item.strip().lower() for item in v.split(",") if item.strip()]
            return items
        if isinstance(v, list):
            return [str(item).strip().lower() for item in v if str(item).strip()]
        return []

    @field_validator("available_equipment", mode="before")
    @classmethod
    def sanitize_equipment(cls, v):
        if isinstance(v, str):
            items = [item.strip().lower() for item in v.split(",") if item.strip()]
            return items if items else ["bodyweight"]
        if isinstance(v, list):
            items = [str(item).strip().lower() for item in v if str(item).strip()]
            return items if items else ["bodyweight"]
        return ["bodyweight"]

    @property
    def bmi(self) -> float:
        """Calculate Body Mass Index (BMI = kg / m^2)."""
        height_m = self.height_cm / 100.0
        return round(self.weight_kg / (height_m * height_m), 1)

    @property
    def bmi_category(self) -> str:
        """Return conventional WHO BMI category."""
        val = self.bmi
        if val < 18.5:
            return "Underweight"
        elif val < 25.0:
            return "Normal weight"
        elif val < 30.0:
            return "Overweight"
        else:
            return "Obesity"


class MacronutrientTargets(BaseModel):
    """Estimated macronutrient breakdown and daily energy targets."""

    bmr: int
    tdee: int
    target_calories: int
    protein_grams: int
    carbs_grams: int
    fat_grams: int
    protein_pct: int
    carbs_pct: int
    fat_pct: int
    explanation: str
    is_safe_threshold: bool = True
    safety_notes: Optional[str] = None


class MealItem(BaseModel):
    """Estimated food and meal entry."""

    name: str
    portion: str
    calories_est: int
    protein_est: float
    carbs_est: float
    fat_est: float
    substitutes: List[str] = Field(default_factory=list)


class DailyMealPlan(BaseModel):
    """Full day sample meal plan."""

    title: str
    dietary_preference: str
    target_calories: int
    total_calories_est: int
    total_protein_est: float
    total_carbs_est: float
    total_fat_est: float
    breakfast: List[MealItem]
    lunch: List[MealItem]
    dinner: List[MealItem]
    snacks: List[MealItem]
    disclaimer: str


class Exercise(BaseModel):
    """Individual exercise detail."""

    name: str
    target_muscle: str
    sets: int
    reps: str
    rest_seconds: int
    guidance: str
    alternatives: List[str] = Field(default_factory=list)


class WorkoutSession(BaseModel):
    """Single workout day routine."""

    day_title: str
    focus: str
    warmup: str
    exercises: List[Exercise]
    cooldown: str


class WorkoutPlan(BaseModel):
    """Complete multi-day structured workout program."""

    title: str
    goal: str
    experience_level: str
    frequency_days: int
    sessions: List[WorkoutSession]
    progression_advice: str
    recovery_advice: str
    safety_reminder: str


class SafetyCheckResult(BaseModel):
    """Result of safety guardrail analysis."""

    is_safe: bool
    warning_flag: Optional[str] = None
    warning_message: Optional[str] = None
    recommended_action: Optional[str] = None
