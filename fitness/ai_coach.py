"""OpenAI AI Coach integration module.

Interacts with the official OpenAI Python SDK to deliver personalized,
profile-informed, and safety-bounded fitness and nutrition coaching.
Gracefully handles API exceptions, rate limits, and configuration errors
without exposing secrets.
"""

from typing import Dict, Generator, List, Optional, Tuple, Union
import openai
from config import get_openai_api_key, get_openai_model, validate_api_key_configuration
from fitness.models import MacronutrientTargets, UserProfile
from fitness.nutrition import calculate_macronutrients
from fitness.safety import evaluate_user_safety, get_safety_system_prompt_addendum


def build_system_prompt(profile: Optional[UserProfile] = None) -> str:
    """Construct an evidence-based system prompt contextualized with the user's profile and metrics."""
    base_prompt = (
        "You are an empathetic, highly knowledgeable, and certified AI Fitness & Nutrition Coach. "
        "Your mission is to provide science-based, practical, encouraging, and safe guidance on exercise, "
        "nutrition, meal planning, recovery, and sustainable habits.\n\n"
    )

    if profile:
        macros: MacronutrientTargets = calculate_macronutrients(profile)
        allergies_str = ", ".join(profile.allergies) if profile.allergies else "None specified"
        equipment_str = ", ".join(profile.available_equipment) if profile.available_equipment else "Bodyweight only"

        context = (
            "ACTIVE CLIENT PROFILE & PHYSIOLOGICAL METRICS:\n"
            f"- Demographic: {profile.age} years old, Biological Sex: {profile.biological_sex.value.title()}\n"
            f"- Height: {profile.height_cm} cm | Weight: {profile.weight_kg} kg | BMI: {profile.bmi} ({profile.bmi_category})\n"
            f"- Primary Goal: {profile.fitness_goal.value.replace('_', ' ').title()}\n"
            f"- Activity Factor: {profile.activity_level.value.replace('_', ' ').title()}\n"
            f"- Dietary Lifestyle: {profile.dietary_preference.value.replace('_', ' ').title()}\n"
            f"- Documented Allergies / Intolerances: {allergies_str}\n"
            f"- Training Experience: {profile.workout_experience.value.title()}\n"
            f"- Equipment Access: {equipment_str}\n"
            f"- Optional Medical/Injury Notes: {profile.medical_notes or 'None'}\n\n"
            "CALCULATED NUTRITION ESTIMATES (Mifflin-St Jeor Reference):\n"
            f"- Estimated BMR: {macros.bmr} kcal/day\n"
            f"- Estimated TDEE: {macros.tdee} kcal/day\n"
            f"- Target Daily Energy: {macros.target_calories} kcal/day\n"
            f"- Target Macronutrients: Protein ~{macros.protein_grams}g ({macros.protein_pct}%), "
            f"Carbs ~{macros.carbs_grams}g ({macros.carbs_pct}%), Fat ~{macros.fat_grams}g ({macros.fat_pct}%)\n\n"
        )
    else:
        context = (
            "CLIENT PROFILE:\n"
            "The client has not saved a complete demographic profile yet. Encourage them gently to specify "
            "their metrics in the sidebar for customized calorie and training breakdowns, while answering their "
            "general fitness and nutrition inquiries warmly.\n\n"
        )

    safety = get_safety_system_prompt_addendum()

    communication_style = (
        "\n\nCOMMUNICATION GUIDELINES:\n"
        "- Format answers cleanly using markdown headings, bullet points, and tables where suitable.\n"
        "- If the client asks for food ideas, respect their dietary lifestyle and strictly omit their allergies.\n"
        "- Clearly clarify that all food calorie and macro counts are standard educational estimates.\n"
        "- When recommending exercises, emphasize proper mechanics and remind the user to stop if they experience pain.\n"
        "- Be encouraging, realistic, and non-judgmental."
    )

    return f"{base_prompt}{context}{safety}{communication_style}"


class AICoachService:
    """Service wrapper for OpenAI Chat Completion calls."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = get_openai_api_key(api_key)
        self.model = get_openai_model(model)

    def _get_client(self) -> openai.OpenAI:
        """Instantiate official OpenAI client."""
        if not self.api_key:
            raise openai.AuthenticationError(
                "OpenAI API key is missing. Please set OPENAI_API_KEY in your .env or sidebar."
            )
        return openai.OpenAI(api_key=self.api_key)

    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        profile: Optional[UserProfile] = None,
        stream: bool = False,
    ) -> Union[Tuple[str, Optional[str]], Generator[str, None, None]]:
        """Generate response from OpenAI API.

        Returns:
            Tuple of (assistant_text, error_message) if stream=False,
            or a Generator yielding string tokens if stream=True.
        """
        # 1. First run safety evaluation on latest user message
        latest_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                latest_user_msg = m.get("content", "")
                break

        if latest_user_msg:
            safety_eval = evaluate_user_safety(latest_user_msg, profile)
            if not safety_eval.is_safe:
                blocked_response = (
                    f"⚠️ **Safety Notice**\n\n{safety_eval.warning_message}\n\n"
                    f"**Recommended Action:** {safety_eval.recommended_action}"
                )
                if stream:
                    def _generator():
                        yield blocked_response
                    return _generator()
                return blocked_response, None

        # 2. Validate configuration
        is_valid, msg = validate_api_key_configuration(self.api_key)
        if not is_valid:
            if stream:
                def _err_gen():
                    yield f"⚠️ **Configuration Issue**: {msg}"
                return _err_gen()
            return "", msg

        # 3. Build message history with dynamic system prompt
        system_content = build_system_prompt(profile)
        full_messages = [{"role": "system", "content": system_content}]
        # Filter out existing system messages and append recent chat history
        for m in messages:
            if m.get("role") in ("user", "assistant"):
                full_messages.append({"role": m["role"], "content": m["content"]})

        try:
            client = self._get_client()

            if stream:
                response_stream = client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=0.7,
                    stream=True,
                )

                def token_generator():
                    try:
                        for chunk in response_stream:
                            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                                yield chunk.choices[0].delta.content
                    except Exception as ex:
                        yield f"\n\n*[Streaming interrupted: {str(ex)}]*"

                return token_generator()
            else:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=0.7,
                    stream=False,
                )
                assistant_text = response.choices[0].message.content or ""
                return assistant_text, None

        except openai.AuthenticationError:
            err = (
                "Authentication failed: The provided OpenAI API key is invalid, revoked, or expired. "
                "Please verify your key in `.env` or the sidebar."
            )
            if stream:
                def _auth_err():
                    yield f"❌ {err}"
                return _auth_err()
            return "", err

        except openai.RateLimitError:
            err = (
                "Rate limit exceeded or quota exhausted: You have exceeded your OpenAI rate limit "
                "or your account has run out of credits. Please check your usage on platform.openai.com."
            )
            if stream:
                def _rate_err():
                    yield f"⏳ {err}"
                return _rate_err()
            return "", err

        except openai.APIConnectionError:
            err = (
                "Network connection error: Unable to reach OpenAI API servers. "
                "Please check your internet connection and try again."
            )
            if stream:
                def _conn_err():
                    yield f"🌐 {err}"
                return _conn_err()
            return "", err

        except openai.BadRequestError as e:
            err = f"API Bad Request: {str(e.message) if hasattr(e, 'message') else str(e)}"
            if stream:
                def _bad_err():
                    yield f"⚠️ {err}"
                return _bad_err()
            return "", err

        except openai.OpenAIError as e:
            err = f"OpenAI API Error: {str(e)}"
            if stream:
                def _gen_err():
                    yield f"❌ {err}"
                return _gen_err()
            return "", err

        except Exception as e:
            err = f"Unexpected system error: {str(e)}"
            if stream:
                def _sys_err():
                    yield f"❌ {err}"
                return _sys_err()
            return "", err
