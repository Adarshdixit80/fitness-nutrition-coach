"""Safety, guardrails, and medical disclaimer module.

Enforces evidence-based health boundaries, flags dangerous queries,
prevents promotion of unsafe weight-loss practices or banned compounds,
and guides users toward licensed medical professionals when necessary.
"""

import re
from typing import Optional
from fitness.models import SafetyCheckResult, UserProfile

MEDICAL_DISCLAIMER = (
    "**Important Health & Medical Disclaimer:**\n\n"
    "This application and its AI-generated recommendations provide general educational fitness and "
    "nutritional information only. It is **not** a substitute for professional medical advice, clinical diagnosis, "
    "or individualized medical treatment. Always consult a physician, registered dietitian (RD), or qualified "
    "healthcare provider prior to starting any new diet, workout routine, or supplement regimen, particularly if you "
    "are pregnant, nursing, a minor, have pre-existing cardiovascular, metabolic, or musculoskeletal conditions, or are taking medications.\n\n"
    "**Stop immediately** and seek emergency medical care if you experience chest pain, severe shortness of breath, "
    "dizziness, fainting, or acute joint pain during physical activity."
)

# High-risk keywords & patterns
DANGEROUS_SUBSTANCES = [
    r"\b(steroids?|anavar|trenbolone|tren|dianabol|deca|winstrol|clenbuterol|clen|sarms?|rad140|mk2866|lgd4033|dnp|2,4-dinitrophenol|ozempic|wegovy|tirzepatide|phentermine|t3|cytomel)\b"
]

EATING_DISORDER_KEYWORDS = [
    r"\b(anorexi[ac]|bulimi[ac]|purge|purging|throw up after eating|starve myself|starvation diet|laxatives? to lose weight|eat 500 calories|eat 600 calories|eat 700 calories|water fast for 30 days)\b"
]

ACUTE_MEDICAL_SYMPTOMS = [
    r"\b(chest pain|tightness in chest|left arm numbness|fainted while lifting|blacked out|heart palpitations|vomiting blood|sharp spinal pain|dislocated)\b"
]

HIGH_RISK_POPULATIONS = [
    r"\b(pregnant|pregnancy|trimester|breastfeeding|postpartum|under 14|kidney failure|dialysis|type 1 diabetes)\b"
]


def evaluate_user_safety(query: str, profile: Optional[UserProfile] = None) -> SafetyCheckResult:
    """Analyze user prompt or metrics for dangerous behaviors, acute symptoms, or unsafe practices.

    Returns:
        SafetyCheckResult with safety status and actionable guidance.
    """
    text = query.strip().lower()

    # 1. Check for acute medical emergencies / red flags
    for pattern in ACUTE_MEDICAL_SYMPTOMS:
        if re.search(pattern, text, re.IGNORECASE):
            return SafetyCheckResult(
                is_safe=False,
                warning_flag="ACUTE_MEDICAL_EMERGENCY",
                warning_message=(
                    "ALERT: The symptoms you described (such as chest pain, fainting, or acute spinal pain) "
                    "may indicate a serious medical emergency. Please stop all physical activity immediately."
                ),
                recommended_action=(
                    "Seek immediate professional medical care or call local emergency services (e.g. 911 / 112). "
                    "Do not attempt to exercise through these symptoms."
                ),
            )

    # 2. Check for eating disorder triggers or extreme starvation
    for pattern in EATING_DISORDER_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return SafetyCheckResult(
                is_safe=False,
                warning_flag="EATING_DISORDER_RISK",
                warning_message=(
                    "Notice: Severe calorie restriction, extreme starvation, or purging behaviors carry severe "
                    "cardiovascular, metabolic, and psychological risks. This coach strictly promotes sustainable, "
                    "health-first, nourishing habits and will not assist with dangerous calorie deprivation."
                ),
                recommended_action=(
                    "If you or someone you know is struggling with disordered eating or body image distress, compassionate, "
                    "confidential support is available through the National Eating Disorders Association (NEDA) helpline "
                    "at 1-800-931-2237 or by texting 'NEDA' to 741741, or by consulting a specialized registered dietitian."
                ),
            )

    # 3. Check for banned/dangerous pharmacological agents
    for pattern in DANGEROUS_SUBSTANCES:
        if re.search(pattern, text, re.IGNORECASE):
            return SafetyCheckResult(
                is_safe=False,
                warning_flag="UNSAFE_SUBSTANCES",
                warning_message=(
                    "Notice: Anabolic androgenic steroids, SARMs, unprescribed peptide agonists, and dangerous metabolic stimulants "
                    "carry documented health risks including hepatic toxicity, cardiovascular hypertrophy, and endocrine shutdown. "
                    "This coach exclusively provides natural, evidence-based nutrition and training guidance."
                ),
                recommended_action=(
                    "Focus on optimized sleep, natural macronutrient intake, and structured progressive overload. Consult a licensed "
                    "sports medicine physician or endocrinologist for questions regarding prescription medications or hormone panels."
                ),
            )

    # 4. Check for high-risk demographics / conditions
    for pattern in HIGH_RISK_POPULATIONS:
        if re.search(pattern, text, re.IGNORECASE):
            return SafetyCheckResult(
                is_safe=True,  # Informational caution rather than strict block
                warning_flag="SPECIAL_POPULATION_CAUTION",
                warning_message=(
                    "Caution: Pregnancy, nursing, pediatric growth phases, or chronic conditions (e.g. renal failure, diabetes) "
                    "have specialized metabolic and clinical requirements that generalized algorithms cannot address."
                ),
                recommended_action=(
                    "Please share these guidelines with your obstetrician, pediatrician, or managing physician to tailor them "
                    "to your specific clinical parameters."
                ),
            )

    # 5. Check user profile for extreme age or calorie minimums
    if profile:
        if profile.age < 16:
            return SafetyCheckResult(
                is_safe=True,
                warning_flag="ADOLESCENT_CAUTION",
                warning_message=(
                    f"User profile indicates age {profile.age}. Adolescents have unique nutritional and bone development "
                    "needs. Calorie restriction is generally discouraged during active growth periods."
                ),
                recommended_action="Consult a pediatric nutritionist or certified youth strength coach.",
            )

    return SafetyCheckResult(is_safe=True)


def get_safety_system_prompt_addendum() -> str:
    """Return explicit safety rules to inject into OpenAI system instructions."""
    return (
        "CORE SAFETY & ETHICAL RULES:\n"
        "1. You are an educational fitness and nutrition coach, NOT a medical doctor or clinical dietitian.\n"
        "2. NEVER diagnose medical conditions or prescribe medical treatments.\n"
        "3. NEVER recommend extreme calorie deficits (under 1200 kcal for women, under 1500 kcal for men).\n"
        "4. NEVER recommend anabolic steroids, SARMs, prescription weight-loss drugs without a doctor, or dangerous fat burners (e.g., DNP).\n"
        "5. NEVER guarantee rapid or unrealistic results (e.g., 'lose 10 lbs in a week'). Emphasize sustainable progress (0.25 - 0.75 kg/week).\n"
        "6. Explicitly state that all food calorie and macro values are educational approximations, not clinical guarantees.\n"
        "7. If the user mentions pain, acute symptoms, injury, pregnancy, or eating disorders, urge them to consult a qualified healthcare professional.\n"
        "8. Respect all specified food allergies and dietary restrictions strictly in every suggestion."
    )
