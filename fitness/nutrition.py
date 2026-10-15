"""Nutrition calculations, calorie estimation, meal planning, and food substitution helpers.

Formulas implemented:
- Basal Metabolic Rate (BMR): Mifflin-St Jeor Equation (Mifflin et al., 1990)
- Total Daily Energy Expenditure (TDEE): BMR * Activity Factor
- Goal Adjustments: Deficit for weight loss, surplus for muscle hypertrophy, maintenance.
- Macronutrient distributions: Evidence-based guidelines (ISSN / ACSM).

NOTE: All nutritional values and calorie requirements are estimates designed for
educational and general fitness planning. They are not clinical dietary prescriptions.
"""

from typing import Dict, List, Optional, Tuple
from fitness.models import (
    ActivityLevel,
    BiologicalSex,
    DailyMealPlan,
    DietaryPreference,
    FitnessGoal,
    MacronutrientTargets,
    MealItem,
    UserProfile,
)

# Activity multipliers for TDEE calculation
ACTIVITY_MULTIPLIERS: Dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTRA_ACTIVE: 1.9,
}

# Calorie adjustments relative to TDEE
GOAL_CALORIE_ADJUSTMENTS: Dict[FitnessGoal, int] = {
    FitnessGoal.WEIGHT_LOSS: -450,       # Moderate, sustainable ~450 kcal/day deficit
    FitnessGoal.MUSCLE_GAIN: 350,        # Lean hypertrophy ~350 kcal/day surplus
    FitnessGoal.MAINTENANCE: 0,
    FitnessGoal.GENERAL_FITNESS: 0,
}

# Recommended protein intake (grams per kg of body weight)
PROTEIN_PER_KG: Dict[FitnessGoal, float] = {
    FitnessGoal.WEIGHT_LOSS: 2.0,       # Higher protein to preserve lean muscle during a deficit
    FitnessGoal.MUSCLE_GAIN: 2.0,       # Optimal hypertrophy stimulus (ISSN recommendation: 1.6-2.2g/kg)
    FitnessGoal.MAINTENANCE: 1.6,       # General health and muscle maintenance
    FitnessGoal.GENERAL_FITNESS: 1.6,
}

# Minimum safe daily intake floors to prevent metabolic distress
MINIMUM_SAFE_CALORIES = {
    BiologicalSex.MALE: 1500,
    BiologicalSex.FEMALE: 1200,
    BiologicalSex.OTHER: 1350,
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: BiologicalSex) -> float:
    """Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.

    Formula:
    - Men: 10 * weight(kg) + 6.25 * height(cm) - 5 * age(y) + 5
    - Women: 10 * weight(kg) + 6.25 * height(cm) - 5 * age(y) - 161
    - Other: Midpoint average of male and female formulas (+5 and -161 midpoint is -78)
    """
    base = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age)
    if sex == BiologicalSex.MALE:
        return base + 5.0
    elif sex == BiologicalSex.FEMALE:
        return base - 161.0
    else:
        # Documented assumption for non-binary/unspecified biological sex
        return base - 78.0


def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
    """Calculate Total Daily Energy Expenditure (TDEE = BMR * Activity Factor)."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
    return bmr * multiplier


def calculate_target_calories(
    tdee: float, goal: FitnessGoal, sex: BiologicalSex = BiologicalSex.MALE
) -> Tuple[int, bool, Optional[str]]:
    """Determine target daily calories based on goal and check against safety floors.

    Returns:
        (target_calories, is_safe_threshold, safety_warning)
    """
    adjustment = GOAL_CALORIE_ADJUSTMENTS.get(goal, 0)
    raw_target = int(round(tdee + adjustment))
    min_safe = MINIMUM_SAFE_CALORIES.get(sex, 1350)

    if raw_target < min_safe:
        return (
            min_safe,
            False,
            f"Calculated target ({raw_target} kcal) was below the recommended minimum safe intake "
            f"threshold of {min_safe} kcal/day for your demographic. Target has been adjusted to {min_safe} kcal "
            "to prevent nutrient deficiencies and metabolic slowdown.",
        )
    return (raw_target, True, None)


def calculate_macronutrients(profile: UserProfile) -> MacronutrientTargets:
    """Calculate comprehensive energy and macronutrient distribution with full explanations."""
    bmr_val = calculate_bmr(
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        age=profile.age,
        sex=profile.biological_sex,
    )
    tdee_val = calculate_tdee(bmr_val, profile.activity_level)
    target_cal, is_safe, safety_note = calculate_target_calories(
        tdee_val, profile.fitness_goal, profile.biological_sex
    )

    # 1. Protein calculation: based on body weight target
    protein_rate = PROTEIN_PER_KG.get(profile.fitness_goal, 1.8)
    # Special adjustment for keto: moderate protein, high fat
    if profile.dietary_preference == DietaryPreference.KETO:
        protein_grams = int(round(profile.weight_kg * 1.6))
    else:
        protein_grams = int(round(profile.weight_kg * protein_rate))

    # Cap protein if it exceeds 35% of total daily calories
    protein_calories = protein_grams * 4
    if protein_calories > target_cal * 0.35:
        protein_calories = int(target_cal * 0.30)
        protein_grams = int(protein_calories / 4)

    # 2. Fat calculation
    if profile.dietary_preference == DietaryPreference.KETO:
        # Keto: 70% calories from fat, 5% from carbs, 25% from protein
        fat_calories = int(target_cal * 0.70)
        fat_grams = int(round(fat_calories / 9.0))
        carbs_calories = max(0, target_cal - protein_calories - fat_calories)
        carbs_grams = int(round(carbs_calories / 4.0))
    else:
        # Standard balanced distribution: 25% of calories from healthy fats
        fat_calories = int(target_cal * 0.25)
        fat_grams = int(round(fat_calories / 9.0))
        carbs_calories = max(0, target_cal - protein_calories - fat_calories)
        carbs_grams = int(round(carbs_calories / 4.0))

    # Calculate percentages
    total_calculated_cals = (protein_grams * 4) + (carbs_grams * 4) + (fat_grams * 9)
    p_pct = int(round((protein_grams * 4 / total_calculated_cals) * 100)) if total_calculated_cals else 0
    c_pct = int(round((carbs_grams * 4 / total_calculated_cals) * 100)) if total_calculated_cals else 0
    f_pct = max(0, 100 - p_pct - c_pct)

    explanation = (
        f"Daily calorie needs estimated via the clinically validated Mifflin-St Jeor formula (BMR = {int(bmr_val)} kcal), "
        f"scaled by your physical activity factor ({ACTIVITY_MULTIPLIERS.get(profile.activity_level)}x) for a TDEE of {int(tdee_val)} kcal. "
        f"Goal adjustment for {profile.fitness_goal.value.replace('_', ' ')}: {GOAL_CALORIE_ADJUSTMENTS.get(profile.fitness_goal, 0):+d} kcal. "
        f"Protein is targeted at {protein_rate}g/kg of body weight ({protein_grams}g) to support muscle retention and synthesis; "
        f"healthy dietary fats are budgeted at ~{f_pct}% ({fat_grams}g) for hormonal support; and complex carbohydrates make up the remainder "
        f"({carbs_grams}g) for training energy and glycogen replenishment. All values are baseline educational estimates."
    )

    return MacronutrientTargets(
        bmr=int(round(bmr_val)),
        tdee=int(round(tdee_val)),
        target_calories=target_cal,
        protein_grams=protein_grams,
        carbs_grams=carbs_grams,
        fat_grams=fat_grams,
        protein_pct=p_pct,
        carbs_pct=c_pct,
        fat_pct=f_pct,
        explanation=explanation,
        is_safe_threshold=is_safe,
        safety_notes=safety_note,
    )


# Reference database of nutritional estimates per typical portion
FOOD_ESTIMATES_DATABASE: Dict[str, Dict[str, float]] = {
    "rolled oats": {"calories": 150, "protein": 5.0, "carbs": 27.0, "fat": 2.5, "serving": "40g dry"},
    "egg": {"calories": 72, "protein": 6.3, "carbs": 0.4, "fat": 4.8, "serving": "1 large boiled/poached"},
    "egg whites": {"calories": 51, "protein": 10.9, "carbs": 0.7, "fat": 0.2, "serving": "100g"},
    "chicken breast": {"calories": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6, "serving": "100g cooked skinless"},
    "salmon fillet": {"calories": 208, "protein": 20.4, "carbs": 0.0, "fat": 13.4, "serving": "100g cooked"},
    "firm tofu": {"calories": 144, "protein": 17.3, "carbs": 2.8, "fat": 8.7, "serving": "150g raw/pan-seared"},
    "tempeh": {"calories": 195, "protein": 20.0, "carbs": 7.6, "fat": 11.0, "serving": "100g cooked"},
    "cooked lentils": {"calories": 230, "protein": 17.9, "carbs": 39.9, "fat": 0.8, "serving": "1 cup (198g)"},
    "cooked brown rice": {"calories": 216, "protein": 5.0, "carbs": 44.8, "fat": 1.8, "serving": "1 cup (195g)"},
    "cooked quinoa": {"calories": 222, "protein": 8.1, "carbs": 39.4, "fat": 3.6, "serving": "1 cup (185g)"},
    "sweet potato": {"calories": 103, "protein": 2.3, "carbs": 23.6, "fat": 0.2, "serving": "1 medium baked (114g)"},
    "greek yogurt (0% fat)": {"calories": 100, "protein": 17.0, "carbs": 6.0, "fat": 0.7, "serving": "170g single container"},
    "soy milk (unsweetened)": {"calories": 80, "protein": 7.0, "carbs": 4.0, "fat": 4.0, "serving": "1 cup (240ml)"},
    "whey protein powder": {"calories": 120, "protein": 24.0, "carbs": 3.0, "fat": 1.5, "serving": "1 scoop (30g)"},
    "pea protein powder": {"calories": 115, "protein": 24.0, "carbs": 2.0, "fat": 1.5, "serving": "1 scoop (30g)"},
    "almonds": {"calories": 164, "protein": 6.0, "carbs": 6.1, "fat": 14.2, "serving": "28g (approx 23 nuts)"},
    "peanut butter": {"calories": 188, "protein": 8.0, "carbs": 6.0, "fat": 16.0, "serving": "2 tablespoons (32g)"},
    "sunflower seed butter": {"calories": 198, "protein": 5.5, "carbs": 7.0, "fat": 17.5, "serving": "2 tablespoons (32g)"},
    "steamed broccoli": {"calories": 55, "protein": 3.7, "carbs": 11.2, "fat": 0.6, "serving": "1 cup chopped (156g)"},
    "olive oil": {"calories": 119, "protein": 0.0, "carbs": 0.0, "fat": 13.5, "serving": "1 tablespoon (14g)"},
    "avocado": {"calories": 160, "protein": 2.0, "carbs": 8.5, "fat": 14.7, "serving": "Half medium avocado (100g)"},
    "banana": {"calories": 105, "protein": 1.3, "carbs": 27.0, "fat": 0.3, "serving": "1 medium (118g)"},
    "apple": {"calories": 95, "protein": 0.5, "carbs": 25.0, "fat": 0.3, "serving": "1 medium (182g)"},
    "berries (mixed)": {"calories": 70, "protein": 1.0, "carbs": 16.0, "fat": 0.5, "serving": "1 cup (150g)"},
    "cottage cheese (low fat)": {"calories": 163, "protein": 28.0, "carbs": 6.1, "fat": 2.3, "serving": "1 cup (226g)"},
    "canned tuna in water": {"calories": 130, "protein": 29.0, "carbs": 0.0, "fat": 1.0, "serving": "1 can drained (114g)"},
}

# Food substitutions mapping
FOOD_SUBSTITUTIONS_MAP: Dict[str, List[str]] = {
    "chicken breast": [
        "Extra-firm tofu (pan-seared)",
        "Tempeh slices",
        "Turkey breast",
        "White fish (cod, haddock)",
        "Cooked lentils or chickpeas",
    ],
    "salmon": [
        "Trout or mackerel",
        "Canned sardines in olive oil",
        "Hemp seeds + chia seeds + walnuts (for plant-based Omega-3s)",
        "Pan-seared firm tofu with algae oil",
    ],
    "egg": [
        "Tofu scramble with nutritional yeast",
        "Chickpea flour omelet",
        "Chia or flaxseed gel (in baking)",
        "Egg whites (for low fat)",
    ],
    "whey protein powder": [
        "Pea protein isolate powder",
        "Soy protein isolate",
        "Brown rice & pea protein blend",
        "Egg white protein powder",
    ],
    "greek yogurt": [
        "Silk or Forager unsweetened soy/almond Greek-style yogurt",
        "Low-fat cottage cheese (if dairy tolerated)",
        "Silken tofu blended with lemon juice and vanilla",
    ],
    "cow milk": [
        "Unsweetened soy milk (high protein)",
        "Unsweetened almond milk (low calorie)",
        "Oat milk (creamy texture)",
        "Lactose-free cow's milk",
    ],
    "peanut butter": [
        "Sunflower seed butter (nut-free)",
        "Tahini (sesame seed paste)",
        "Almond butter",
        "Pumpkin seed butter",
    ],
    "brown rice": [
        "Quinoa (complete plant protein)",
        "Riced cauliflower (very low carbohydrate)",
        "Sweet potato or yams",
        "Barley or buckwheat",
    ],
    "wheat pasta": [
        "Chickpea or lentil pasta (high protein & gluten-free)",
        "Zucchini noodles (zoodles)",
        "Brown rice pasta",
        "Spaghetti squash",
    ],
}


def estimate_food_nutrition(food_name: str) -> Optional[Dict[str, float]]:
    """Look up estimated macronutrient information for a common fitness food item.

    Values are clearly documented educational estimates.
    """
    key = food_name.strip().lower()
    for name, data in FOOD_ESTIMATES_DATABASE.items():
        if key in name or name in key:
            result = dict(data)
            result["disclaimer"] = "Estimated standard nutritional average; not an individualized laboratory measurement."
            return result
    return None


def get_food_substitutions(food_item: str) -> List[str]:
    """Retrieve suitable food swaps for allergies, dietary restrictions, or variety."""
    key = food_item.strip().lower()
    for item, subs in FOOD_SUBSTITUTIONS_MAP.items():
        if key in item or item in key:
            return subs
    # General fallback suggestions
    return [
        "Tofu, tempeh, or edamame for plant-based protein",
        "Beans, lentils, or chickpeas for high-fiber complex carbohydrates",
        "Sunflower seed butter or tahini for peanut/tree-nut allergies",
        "Unsweetened soy milk or almond milk for dairy-free alternatives",
        "Quinoa or sweet potatoes for gluten-free carbohydrate sources",
    ]


def _filter_meal_items_for_allergies(items: List[MealItem], allergies: List[str]) -> List[MealItem]:
    """Ensure meal items do not contain user-specified allergens."""
    cleaned_allergies = [a.lower().strip() for a in allergies if a.strip()]
    if not cleaned_allergies:
        return items

    safe_items = []
    for item in items:
        name_lower = item.name.lower()
        has_allergen = False
        for allergen in cleaned_allergies:
            if allergen in name_lower:
                has_allergen = True
                break
            if allergen in ("dairy", "lactose", "milk") and any(
                d in name_lower for d in ("whey", "yogurt", "milk", "cottage cheese", "cheese")
            ):
                has_allergen = True
                break
            if allergen in ("peanut", "peanuts", "nuts", "tree nuts") and any(
                n in name_lower for n in ("peanut", "almond", "walnut", "cashew", "nut")
            ):
                has_allergen = True
                break
            if allergen in ("gluten", "wheat") and any(
                g in name_lower for g in ("oats", "bread", "pasta", "wheat")
            ):
                has_allergen = True
                break
            if allergen in ("soy", "soya") and any(s in name_lower for s in ("tofu", "tempeh", "soy", "edamame")):
                has_allergen = True
                break
            if allergen in ("egg", "eggs") and "egg" in name_lower:
                has_allergen = True
                break

        if not has_allergen:
            safe_items.append(item)
        else:
            # Provide an allergy-safe substitution
            safe_items.append(
                MealItem(
                    name=f"Allergy-Safe Alternative ({item.name.split('(')[0].strip()})",
                    portion=item.portion,
                    calories_est=item.calories_est,
                    protein_est=item.protein_est,
                    carbs_est=item.carbs_est,
                    fat_est=item.fat_est,
                    substitutes=item.substitutes or ["See safe ingredient substitutions in nutrition guide."],
                )
            )
    return safe_items


def generate_sample_meal_plan(profile: UserProfile, target_calories: int) -> DailyMealPlan:
    """Generate a structured, evidence-based daily meal plan tailored to dietary preferences and allergies.

    All nutrition values are clearly labeled educational approximations.
    """
    pref = profile.dietary_preference
    allergies = profile.allergies

    # Construct plan templates by preference
    if pref == DietaryPreference.VEGAN:
        breakfast = [
            MealItem(
                name="Warm Oatmeal with Pea Protein & Mixed Berries",
                portion="50g oats, 25g pea protein powder, 100g mixed berries",
                calories_est=350,
                protein_est=28.0,
                carbs_est=45.0,
                fat_est=5.0,
                substitutes=["Chia pudding with hemp seeds", "Tofu scramble with nutritional yeast"],
            ),
            MealItem(
                name="Unsweetened Soy Milk",
                portion="200ml",
                calories_est=70,
                protein_est=6.0,
                carbs_est=3.5,
                fat_est=3.5,
                substitutes=["Unsweetened almond milk", "Oat milk"],
            ),
        ]
        lunch = [
            MealItem(
                name="Quinoa & Lentil Power Bowl with Avocado",
                portion="150g cooked quinoa, 150g brown lentils, 50g avocado, spinach",
                calories_est=520,
                protein_est=24.0,
                carbs_est=72.0,
                fat_est=14.0,
                substitutes=["Brown rice & black bean bowl", "Chickpea and tahini salad"],
            ),
        ]
        dinner = [
            MealItem(
                name="Pan-Seared Firm Tofu with Stir-Fried Greens & Brown Rice",
                portion="180g firm tofu, 150g brown rice, 150g broccoli & snap peas, 1 tsp sesame oil",
                calories_est=540,
                protein_est=30.0,
                carbs_est=62.0,
                fat_est=16.0,
                substitutes=["Tempeh stir-fry", "Edamame & buckwheat soba bowl"],
            ),
        ]
        snacks = [
            MealItem(
                name="Roasted Edamame & Apple Slices",
                portion="50g dry roasted edamame, 1 medium apple",
                calories_est=280,
                protein_est=17.0,
                carbs_est=35.0,
                fat_est=7.0,
                substitutes=["Pumpkin seeds with pear", "Rice cakes with sunflower seed butter"],
            ),
        ]

    elif pref == DietaryPreference.VEGETARIAN:
        breakfast = [
            MealItem(
                name="High-Protein Greek Yogurt Parfait with Oats & Berries",
                portion="200g Greek yogurt (0%), 40g oats, 100g fresh berries, 1 tbsp honey",
                calories_est=380,
                protein_est=27.0,
                carbs_est=54.0,
                fat_est=3.5,
                substitutes=["Cottage cheese bowl", "Tofu breakfast scramble with whole wheat toast"],
            ),
            MealItem(
                name="Hard-Boiled Eggs",
                portion="2 large eggs",
                calories_est=145,
                protein_est=13.0,
                carbs_est=0.8,
                fat_est=9.6,
                substitutes=["Egg white omelet", "Tofu slices"],
            ),
        ]
        lunch = [
            MealItem(
                name="Spiced Chickpea & Paneer/Tofu Mediterranean Bowl",
                portion="150g cooked chickpeas, 75g low-fat paneer or tofu, mixed salad greens, olive oil dressing",
                calories_est=510,
                protein_est=28.0,
                carbs_est=52.0,
                fat_est=18.0,
                substitutes=["Lentil soup with whole grain pita", "Black bean burrito bowl with cheese"],
            ),
        ]
        dinner = [
            MealItem(
                name="Lentil Dahl with Steamed Basmati Brown Rice & Roasted Broccoli",
                portion="200g yellow or red lentil dahl, 150g brown rice, 150g broccoli",
                calories_est=530,
                protein_est=26.0,
                carbs_est=80.0,
                fat_est=9.0,
                substitutes=["Tofu vegetable curry", "Cottage cheese stuffed bell peppers"],
            ),
        ]
        snacks = [
            MealItem(
                name="Whey or Plant Protein Shake with Handful of Almonds",
                portion="1 scoop protein (30g) in water/almond milk, 20g almonds",
                calories_est=240,
                protein_est=28.0,
                carbs_est=6.0,
                fat_est=11.0,
                substitutes=["String cheese + apple", "Hummus with cucumber sticks"],
            ),
        ]

    elif pref == DietaryPreference.KETO:
        breakfast = [
            MealItem(
                name="Avocado & Spinach 3-Egg Omelet with Cheddar",
                portion="3 whole eggs, 30g cheddar, 50g avocado, cooked in 1 tsp butter",
                calories_est=460,
                protein_est=27.0,
                carbs_est=4.5,
                fat_est=37.0,
                substitutes=["Scrambled eggs with smoked salmon", "Tofu omelet with vegan cheese & avocado"],
            ),
        ]
        lunch = [
            MealItem(
                name="Grilled Chicken Thigh & Bacon Salad with Olive Oil & Seeds",
                portion="150g chicken thigh, 1 slice bacon, leafy greens, 1.5 tbsp extra virgin olive oil",
                calories_est=550,
                protein_est=36.0,
                carbs_est=5.0,
                fat_est=42.0,
                substitutes=["Canned tuna in olive oil with celery", "Baked salmon over baby spinach"],
            ),
        ]
        dinner = [
            MealItem(
                name="Herb-Butter Baked Salmon with Garlic Asparagus & Cauliflower Mash",
                portion="180g Atlantic salmon, 150g steamed asparagus, 150g mashed cauliflower with butter",
                calories_est=560,
                protein_est=38.0,
                carbs_est=7.0,
                fat_est=41.0,
                substitutes=["Grass-fed beef patty with zucchini", "Pork tenderloin with broccoli & cheese"],
            ),
        ]
        snacks = [
            MealItem(
                name="Macadamia Nuts & String Cheese",
                portion="25g macadamia nuts, 1 mozzarella stick",
                calories_est=260,
                protein_est=9.0,
                carbs_est=3.5,
                fat_est=24.0,
                substitutes=["Boiled egg with mayo", "Celery with cream cheese"],
            ),
        ]

    elif pref == DietaryPreference.PESCATARIAN:
        breakfast = [
            MealItem(
                name="Poached Eggs on Sprouted Toast with Sliced Avocado",
                portion="2 eggs, 1 slice whole sprouted bread, 50g avocado",
                calories_est=360,
                protein_est=18.0,
                carbs_est=22.0,
                fat_est=20.0,
                substitutes=["Greek yogurt with walnuts and berries", "Smoked salmon breakfast wrap"],
            ),
        ]
        lunch = [
            MealItem(
                name="Mediterranean Tuna & White Bean Salad",
                portion="1 can tuna (120g drained), 100g cannellini beans, diced cucumber, tomatoes, olive oil",
                calories_est=470,
                protein_est=38.0,
                carbs_est=32.0,
                fat_est=14.0,
                substitutes=["Grilled shrimp quinoa bowl", "Salmon salad in whole wheat pita"],
            ),
        ]
        dinner = [
            MealItem(
                name="Baked Salmon with Roasted Sweet Potato & Steamed Green Beans",
                portion="160g salmon fillet, 150g sweet potato, 150g green beans",
                calories_est=540,
                protein_est=35.0,
                carbs_est=40.0,
                fat_est=22.0,
                substitutes=["Pan-seared cod with wild rice", "Shrimp & broccoli stir-fry"],
            ),
        ]
        snacks = [
            MealItem(
                name="Greek Yogurt with Chia Seeds & Blueberries",
                portion="170g 0% Greek yogurt, 10g chia seeds, 75g blueberries",
                calories_est=210,
                protein_est=20.0,
                carbs_est=20.0,
                fat_est=4.0,
                substitutes=["Roasted edamame", "Cottage cheese with pineapple"],
            ),
        ]

    else:  # NON_VEGETARIAN (Default)
        breakfast = [
            MealItem(
                name="Scrambled Eggs & Egg Whites with Oatmeal and Berries",
                portion="2 whole eggs + 2 egg whites, 40g dry rolled oats, 80g berries",
                calories_est=410,
                protein_est=29.0,
                carbs_est=38.0,
                fat_est=13.0,
                substitutes=["Greek yogurt protein smoothie", "Whole grain turkey bacon breakfast sandwich"],
            ),
        ]
        lunch = [
            MealItem(
                name="Grilled Chicken Breast with Brown Rice & Steamed Vegetables",
                portion="150g cooked chicken breast, 150g brown rice, 150g broccoli, 1 tsp olive oil",
                calories_est=520,
                protein_est=42.0,
                carbs_est=50.0,
                fat_est=11.0,
                substitutes=["Lean ground turkey with sweet potato", "Canned tuna grain bowl"],
            ),
        ]
        dinner = [
            MealItem(
                name="Lean Ground Beef (or Salmon) with Baked Sweet Potato & Green Salad",
                portion="150g 90% lean beef, 180g baked sweet potato, large leafy greens with vinaigrette",
                calories_est=560,
                protein_est=40.0,
                carbs_est=45.0,
                fat_est=17.0,
                substitutes=["Grilled flank steak with quinoa", "Baked chicken thighs with roasted squash"],
            ),
        ]
        snacks = [
            MealItem(
                name="Protein Shake with an Apple & Almonds",
                portion="1 scoop whey/plant protein (30g), 1 medium apple, 15g almonds",
                calories_est=310,
                protein_est=28.0,
                carbs_est=32.0,
                fat_est=8.0,
                substitutes=["0% Greek yogurt with walnuts", "Jerky with rice cakes"],
            ),
        ]

    # Filter out allergens
    breakfast = _filter_meal_items_for_allergies(breakfast, allergies)
    lunch = _filter_meal_items_for_allergies(lunch, allergies)
    dinner = _filter_meal_items_for_allergies(dinner, allergies)
    snacks = _filter_meal_items_for_allergies(snacks, allergies)

    total_cals = sum(item.calories_est for meal in (breakfast, lunch, dinner, snacks) for item in meal)
    total_p = sum(item.protein_est for meal in (breakfast, lunch, dinner, snacks) for item in meal)
    total_c = sum(item.carbs_est for meal in (breakfast, lunch, dinner, snacks) for item in meal)
    total_f = sum(item.fat_est for meal in (breakfast, lunch, dinner, snacks) for item in meal)

    return DailyMealPlan(
        title=f"Sample Daily Meal Plan ({pref.value.replace('_', ' ').title()})",
        dietary_preference=pref.value,
        target_calories=target_calories,
        total_calories_est=total_cals,
        total_protein_est=round(total_p, 1),
        total_carbs_est=round(total_c, 1),
        total_fat_est=round(total_f, 1),
        breakfast=breakfast,
        lunch=lunch,
        dinner=dinner,
        snacks=snacks,
        disclaimer=(
            "Nutrition values are educational estimations calculated from standard references. "
            "Individual food labels, preparation methods, cooking oils, and brands will vary. "
            "Never verified against clinical or personal medical databases without explicit lab testing."
        ),
    )
