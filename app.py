"""Fitness & Nutrition Coach — Streamlit Application.

An end-to-end AI coaching platform providing personalized, evidence-based
fitness, nutrition, workout plans, and health safety guardrails.
"""

import streamlit as st
from pydantic import ValidationError
import config
from fitness.ai_coach import AICoachService
from fitness.models import (
    ActivityLevel,
    BiologicalSex,
    DietaryPreference,
    FitnessGoal,
    UserProfile,
    WorkoutExperience,
)
from fitness.nutrition import (
    calculate_macronutrients,
    estimate_food_nutrition,
    generate_sample_meal_plan,
    get_food_substitutions,
)
from fitness.safety import (
    MEDICAL_DISCLAIMER,
    evaluate_user_safety,
)
from fitness.workouts import (
    generate_workout_plan,
    get_exercise_alternatives,
    get_warmup_cooldown_routine,
)

# Page configuration
st.set_page_config(
    page_title="Fitness & Nutrition Coach | AI Powered",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern Custom CSS styling
st.markdown(
    """
    <style>
    /* Global layout & typography */
    .main {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header gradient banner */
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #064e3b 100%);
        border: 1px solid #10b98133;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .app-title {
        color: #f8fafc;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    .app-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 0;
    }

    /* Metric cards */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .metric-card:hover {
        border-color: #10b981;
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #10b981;
        margin: 4px 0;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.5px;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 4px;
    }

    /* Disclaimers & callouts */
    .safety-banner {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #f59e0b;
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        margin-bottom: 20px;
        font-size: 0.9rem;
        color: #fcd34d;
    }
    .disclaimer-badge {
        display: inline-block;
        background: #334155;
        color: #cbd5e1;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 8px;
    }

    /* Card containers */
    .content-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize persistent Streamlit session keys."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "👋 Welcome! I am your **Fitness & Nutrition AI Coach**.\n\n"
                    "I can help you build structured workout programs, calculate your daily energy targets, "
                    "tailor allergy-safe meal plans, and guide your healthy habits. "
                    "To personalize your experience, please update your profile in the sidebar, or ask any fitness or nutrition question below!"
                ),
            }
        ]

    if "user_profile" not in st.session_state:
        # Initial sensible default profile to enable instant exploration
        st.session_state.user_profile = UserProfile(
            age=28,
            biological_sex=BiologicalSex.MALE,
            height_cm=178.0,
            weight_kg=78.0,
            fitness_goal=FitnessGoal.GENERAL_FITNESS,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            dietary_preference=DietaryPreference.NON_VEGETARIAN,
            allergies=[],
            workout_experience=WorkoutExperience.BEGINNER,
            available_equipment=["dumbbells", "bodyweight"],
            medical_notes=None,
        )

    if "api_key_override" not in st.session_state:
        st.session_state.api_key_override = ""

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = config.get_openai_model()


initialize_session_state()

# -------------------------------------------------------------
# SIDEBAR: Configuration & Profile Management
# -------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=400&auto=format&fit=crop&q=60",
        caption="Science-Backed Fitness & Nutrition",
        use_container_width=True,
    )

    st.subheader("⚙️ API Configuration")
    env_key = config.get_openai_api_key()
    is_env_configured = bool(env_key and env_key not in {"your_openai_api_key_here", "your_new_api_key_here"})

    if is_env_configured:
        st.success("✅ OpenAI API key loaded from environment", icon="🔒")
        active_key = env_key
    else:
        st.warning("⚠️ No valid `OPENAI_API_KEY` detected in `.env`.")
        key_input = st.text_input(
            "Enter OpenAI API Key (Session Only):",
            type="password",
            value=st.session_state.api_key_override,
            help="Your API key stays securely in this browser session and is NEVER saved to disk or tracked.",
        )
        if key_input:
            st.session_state.api_key_override = key_input
            active_key = key_input
        else:
            active_key = None

    # Model selector
    configured_model = config.get_openai_model()
    model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    if configured_model not in model_options:
        model_options.insert(0, configured_model)

    chosen_model = st.selectbox(
        "OpenAI Model (`OPENAI_MODEL`):",
        options=model_options,
        index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
        help="Configured via OPENAI_MODEL environment variable.",
    )
    st.session_state.selected_model = chosen_model

    st.divider()

    st.subheader("👤 User Profile Settings")
    st.caption("Update your demographic data to re-calculate BMR, TDEE, and custom workout plans.")

    curr_profile = st.session_state.user_profile

    with st.form("profile_form"):
        col_age, col_sex = st.columns(2)
        with col_age:
            age = st.number_input("Age (years)", min_value=13, max_value=100, value=curr_profile.age)
        with col_sex:
            sex_options = [BiologicalSex.MALE, BiologicalSex.FEMALE, BiologicalSex.OTHER]
            sex_idx = sex_options.index(curr_profile.biological_sex)
            bio_sex = st.selectbox("Biological Sex", options=sex_options, index=sex_idx, format_func=lambda s: s.value.title())

        col_h, col_w = st.columns(2)
        with col_h:
            height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=curr_profile.height_cm, step=0.5)
        with col_w:
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=curr_profile.weight_kg, step=0.5)

        goal_options = [
            FitnessGoal.GENERAL_FITNESS,
            FitnessGoal.WEIGHT_LOSS,
            FitnessGoal.MUSCLE_GAIN,
            FitnessGoal.MAINTENANCE,
        ]
        fitness_goal = st.selectbox(
            "Fitness Goal",
            options=goal_options,
            index=goal_options.index(curr_profile.fitness_goal),
            format_func=lambda g: g.value.replace("_", " ").title(),
        )

        activity_options = [
            ActivityLevel.SEDENTARY,
            ActivityLevel.LIGHTLY_ACTIVE,
            ActivityLevel.MODERATELY_ACTIVE,
            ActivityLevel.VERY_ACTIVE,
            ActivityLevel.EXTRA_ACTIVE,
        ]
        activity_level = st.selectbox(
            "Activity Level",
            options=activity_options,
            index=activity_options.index(curr_profile.activity_level),
            format_func=lambda a: a.value.replace("_", " ").title(),
        )

        diet_options = [
            DietaryPreference.NON_VEGETARIAN,
            DietaryPreference.VEGETARIAN,
            DietaryPreference.VEGAN,
            DietaryPreference.PESCATARIAN,
            DietaryPreference.KETO,
        ]
        dietary_pref = st.selectbox(
            "Dietary Preference",
            options=diet_options,
            index=diet_options.index(curr_profile.dietary_preference),
            format_func=lambda d: d.value.replace("_", " ").title(),
        )

        allergies_str = st.text_input(
            "Allergies & Restrictions (comma-separated):",
            value=", ".join(curr_profile.allergies),
            placeholder="e.g. peanuts, dairy, gluten",
        )

        exp_options = [
            WorkoutExperience.BEGINNER,
            WorkoutExperience.INTERMEDIATE,
            WorkoutExperience.ADVANCED,
        ]
        workout_exp = st.selectbox(
            "Workout Experience",
            options=exp_options,
            index=exp_options.index(curr_profile.workout_experience),
            format_func=lambda e: e.value.title(),
        )

        equipment_str = st.text_input(
            "Available Equipment (comma-separated):",
            value=", ".join(curr_profile.available_equipment),
            placeholder="e.g. dumbbells, barbell, bodyweight, full gym",
        )

        medical_notes = st.text_area(
            "Health & Injury Context (optional):",
            value=curr_profile.medical_notes or "",
            placeholder="e.g. mild lower-back sensitivity, asthma",
            height=60,
        )

        submit_profile = st.form_submit_button("💾 Save Profile Changes", use_container_width=True)

        if submit_profile:
            try:
                new_profile = UserProfile(
                    age=age,
                    biological_sex=bio_sex,
                    height_cm=height,
                    weight_kg=weight,
                    fitness_goal=fitness_goal,
                    activity_level=activity_level,
                    dietary_preference=dietary_pref,
                    allergies=allergies_str,
                    workout_experience=workout_exp,
                    available_equipment=equipment_str,
                    medical_notes=medical_notes.strip() if medical_notes.strip() else None,
                )
                st.session_state.user_profile = new_profile
                st.success("✅ Profile successfully updated!")
                st.rerun()
            except ValidationError as err:
                st.error(f"Validation Error: {err.errors()[0]['msg']}")

    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Conversation cleared! What would you like to work on today?",
            }
        ]
        st.rerun()


# -------------------------------------------------------------
# MAIN APP HEADER
# -------------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <div class="app-title">🏋️ Fitness & Nutrition Coach</div>
        <div class="app-subtitle">Personalized training routines, evidence-based nutrition estimates, and safety-guided AI advice.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Prominent Safety Notice Banner
st.markdown(
    f"""
    <div class="safety-banner">
        <strong>⚠️ Medical & Educational Disclaimer:</strong> All energy requirements and nutritional values are mathematical estimates, 
        not clinical diagnoses. This chatbot provides general educational guidance. Stop exercising if you experience acute pain or dizziness, 
        and consult a physician or registered dietitian for specialized care.
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# TAB NAVIGATION
# -------------------------------------------------------------
tab_chat, tab_dashboard, tab_nutrition, tab_workout, tab_safety = st.tabs(
    [
        "💬 AI Coach Chat",
        "📊 Profile & Estimates",
        "🥗 Nutrition & Meal Plan",
        "🏋️ Workout Generator",
        "🛡️ Safety & Guidelines",
    ]
)

# -------------------------------------------------------------
# TAB 1: AI COACH CHAT
# -------------------------------------------------------------
with tab_chat:
    st.subheader("💬 Chat with your Personal Coach")
    st.caption("Ask questions about exercises, calorie targets, healthy recipes, recovery, or form tips.")

    # Quick prompt shortcuts
    st.markdown("**Quick Prompts:**")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
    quick_prompt = None
    if quick_col1.button("🥩 How to hit my protein target?"):
        quick_prompt = "How can I easily hit my recommended daily protein target with whole foods?"
    if quick_col2.button("⏱️ Quick 30-min workout routine"):
        quick_prompt = "Can you design a high-intensity 30-minute full body workout using only my available equipment?"
    if quick_col3.button("🥗 Plant-based protein alternatives"):
        quick_prompt = "What are the most bioavailable plant-based protein sources for muscle recovery?"
    if quick_col4.button("📈 How progressive overload works"):
        quick_prompt = "Explain progressive overload in simple terms and give examples of how to apply it weekly."

    # Render previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask a question about your workouts, food, or healthy habits...")
    prompt_to_process = quick_prompt or user_input

    if prompt_to_process:
        # Append user message
        st.session_state.messages.append({"role": "user", "content": prompt_to_process})
        with st.chat_message("user"):
            st.markdown(prompt_to_process)

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("AI Coach is analyzing your metrics and formulating guidance..."):
                active_api_key = config.get_openai_api_key(st.session_state.api_key_override)
                coach_service = AICoachService(
                    api_key=active_api_key,
                    model=st.session_state.selected_model,
                )

                # Check if API key is present
                is_valid, validation_msg = config.validate_api_key_configuration(active_api_key)
                if not is_valid:
                    error_box = (
                        f"⚠️ **OpenAI Configuration Notice**\n\n"
                        f"{validation_msg}\n\n"
                        "To chat with the AI Coach, please either:\n"
                        "1. Add your valid key to `.env` as `OPENAI_API_KEY=sk-...`\n"
                        "2. Paste your API key in the sidebar under **API Configuration**.\n\n"
                        "*Note: You can still view your calculated BMR, TDEE, custom meal plans, and workout routines in the other tabs without an active API key!*"
                    )
                    st.markdown(error_box)
                    st.session_state.messages.append({"role": "assistant", "content": error_box})
                else:
                    # Execute chat completion
                    assistant_response, error_msg = coach_service.generate_chat_response(
                        messages=st.session_state.messages,
                        profile=st.session_state.user_profile,
                        stream=False,
                    )

                    if error_msg:
                        st.error(error_msg)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": f"❌ Error: {error_msg}"}
                        )
                    else:
                        st.markdown(assistant_response)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": assistant_response}
                        )


# -------------------------------------------------------------
# TAB 2: PROFILE & ESTIMATES DASHBOARD
# -------------------------------------------------------------
with tab_dashboard:
    profile = st.session_state.user_profile
    macros = calculate_macronutrients(profile)

    st.subheader("📊 Metabolic Estimates & Target Metrics")
    st.markdown(
        """
        <span class="disclaimer-badge">MATHEMATICAL ESTIMATES — NOT LAB MEASUREMENTS</span>
        """,
        unsafe_allow_html=True,
    )

    # Metric summary row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Body Mass Index (BMI)</div>
                <div class="metric-value">{profile.bmi}</div>
                <div class="metric-sub">{profile.bmi_category}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Basal Metabolic Rate</div>
                <div class="metric-value">{macros.bmr} <span style="font-size:1rem;color:#94a3b8">kcal</span></div>
                <div class="metric-sub">Mifflin-St Jeor (Resting)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Daily Expenditure (TDEE)</div>
                <div class="metric-value">{macros.tdee} <span style="font-size:1rem;color:#94a3b8">kcal</span></div>
                <div class="metric-sub">Activity Multiplier Applied</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Target Daily Intake</div>
                <div class="metric-value" style="color:#38bdf8">{macros.target_calories} <span style="font-size:1rem;color:#94a3b8">kcal</span></div>
                <div class="metric-sub">Goal: {profile.fitness_goal.value.replace('_', ' ').title()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not macros.is_safe_threshold and macros.safety_notes:
        st.warning(f"⚠️ {macros.safety_notes}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Macronutrient target columns
    st.subheader("🍗 Suggested Daily Macronutrient Distribution")
    st.caption("Calculated based on evidence-based sports nutrition recommendations (ISSN guidelines).")

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(
            f"""
            <div class="metric-card" style="border-top: 4px solid #ef4444;">
                <div class="metric-label">Protein Target</div>
                <div class="metric-value" style="color:#f87171">{macros.protein_grams}g</div>
                <div class="metric-sub">{macros.protein_pct}% of total daily calories</div>
                <div style="font-size:0.75rem;color:#94a3b8;margin-top:6px;">Supports muscle synthesis & retention</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m_col2:
        st.markdown(
            f"""
            <div class="metric-card" style="border-top: 4px solid #3b82f6;">
                <div class="metric-label">Carbohydrate Target</div>
                <div class="metric-value" style="color:#60a5fa">{macros.carbs_grams}g</div>
                <div class="metric-sub">{macros.carbs_pct}% of total daily calories</div>
                <div style="font-size:0.75rem;color:#94a3b8;margin-top:6px;">Fuels high-intensity training & glycogen</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m_col3:
        st.markdown(
            f"""
            <div class="metric-card" style="border-top: 4px solid #eab308;">
                <div class="metric-label">Dietary Fat Target</div>
                <div class="metric-value" style="color:#facc15">{macros.fat_grams}g</div>
                <div class="metric-sub">{macros.fat_pct}% of total daily calories</div>
                <div style="font-size:0.75rem;color:#94a3b8;margin-top:6px;">Vital for hormone production & micronutrients</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Scientific assumptions explanation
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📖 Scientific Assumptions & Calculation Methodology", expanded=True):
        st.markdown(f"**Methodology Description:**\n\n{macros.explanation}")
        st.markdown(
            """
            - **Formula**: Mifflin MD, St Jeor ST, et al. *A new predictive equation for resting energy expenditure in healthy individuals.* Am J Clin Nutr. 1990.
            - **Protein Guidance**: Morton RW, et al. *A systematic review, meta-analysis and meta-regression of the effect of protein supplementation on resistance training.* Br J Sports Med. 2018.
            - **Note on Accuracy**: All predictive formulas have an inherent statistical error margin of ±10-15%. Real-world adjustments should be guided by your 3-4 week weight trend.
            """
        )


# -------------------------------------------------------------
# TAB 3: NUTRITION & MEAL PLANNER
# -------------------------------------------------------------
with tab_nutrition:
    st.subheader("🥗 Sample Daily Meal Plan")
    profile = st.session_state.user_profile
    macros = calculate_macronutrients(profile)
    meal_plan = generate_sample_meal_plan(profile, target_calories=macros.target_calories)

    st.markdown(
        f"**Plan Diet Style:** `{meal_plan.dietary_preference.replace('_', ' ').title()}` | "
        f"**Target Energy:** `{meal_plan.target_calories} kcal` | "
        f"**Estimated Total:** `{meal_plan.total_calories_est} kcal` (P: {meal_plan.total_protein_est}g, C: {meal_plan.total_carbs_est}g, F: {meal_plan.total_fat_est}g)"
    )

    if profile.allergies:
        st.info(f"🛡️ **Allergy Filter Active:** Verified exclusion of user allergens: `{', '.join(profile.allergies)}`")

    # Display meals
    meal_categories = [
        ("🌅 Breakfast", meal_plan.breakfast),
        ("☀️ Lunch", meal_plan.lunch),
        ("🌙 Dinner", meal_plan.dinner),
        ("🍎 Snack", meal_plan.snacks),
    ]

    for title, items in meal_categories:
        with st.expander(title, expanded=True):
            for item in items:
                col_name, col_macros, col_subs = st.columns([2, 1, 1.5])
                with col_name:
                    st.markdown(f"**{item.name}**")
                    st.caption(f"Portion: {item.portion}")
                with col_macros:
                    st.markdown(f"**~{item.calories_est} kcal**")
                    st.caption(f"P: {item.protein_est}g | C: {item.carbs_est}g | F: {item.fat_est}g")
                with col_subs:
                    if item.substitutes:
                        st.caption(f"Swaps: {', '.join(item.substitutes[:2])}")

    st.caption(f"ℹ️ *{meal_plan.disclaimer}*")

    st.divider()

    # Interactive Food Estimator
    st.subheader("🔍 Quick Food Nutrition Estimator")
    st.caption("Look up educational macronutrient estimates for common health foods.")
    
    col_search, col_result = st.columns([1, 1])
    with col_search:
        sample_foods = ["chicken breast", "firm tofu", "rolled oats", "salmon fillet", "greek yogurt (0% fat)", "sweet potato", "almonds"]
        selected_food = st.selectbox("Select or type a food item:", options=sample_foods)
        custom_food = st.text_input("Or enter custom food item name:")
        query_food = custom_food if custom_food.strip() else selected_food

    with col_result:
        food_data = estimate_food_nutrition(query_food)
        if food_data:
            st.markdown(
                f"""
                <div class="content-box">
                    <h4 style="margin-top:0;color:#10b981">{query_food.title()}</h4>
                    <p style="color:#94a3b8;margin-bottom:6px">Serving Size: <strong>{food_data.get('serving', 'Standard Portion')}</strong></p>
                    <ul style="margin-bottom:8px">
                        <li><strong>Calories:</strong> ~{food_data['calories']} kcal</li>
                        <li><strong>Protein:</strong> ~{food_data['protein']}g</li>
                        <li><strong>Carbohydrates:</strong> ~{food_data['carbs']}g</li>
                        <li><strong>Dietary Fat:</strong> ~{food_data['fat']}g</li>
                    </ul>
                    <span style="font-size:0.75rem;color:#64748b">{food_data.get('disclaimer')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info(f"No built-in reference for '{query_food}'. Ask the AI Coach in the Chat tab for an estimation!")

    st.subheader("🔄 Practical Food Substitutions")
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        swap_input = st.selectbox(
            "Find alternatives for:",
            options=["chicken breast", "salmon", "egg", "whey protein powder", "cow milk", "peanut butter", "brown rice", "wheat pasta"],
        )
    with sub_col2:
        alternatives = get_food_substitutions(swap_input)
        st.markdown(f"**Recommended swaps for {swap_input}:**")
        for alt in alternatives:
            st.markdown(f"- {alt}")


# -------------------------------------------------------------
# TAB 4: WORKOUT GENERATOR
# -------------------------------------------------------------
with tab_workout:
    profile = st.session_state.user_profile
    workout_plan = generate_workout_plan(profile)

    st.subheader(f"🏋️ {workout_plan.title}")
    st.markdown(
        f"**Goal:** `{workout_plan.goal}` | "
        f"**Experience:** `{workout_plan.experience_level}` | "
        f"**Frequency:** `{workout_plan.frequency_days} Days / Week` | "
        f"**Equipment Available:** `{', '.join(profile.available_equipment)}`"
    )

    st.info(f"💡 **Progression Principle:** {workout_plan.progression_advice}")

    # Display sessions
    for idx, session in enumerate(workout_plan.sessions, 1):
        with st.expander(f"📅 {session.day_title} — Focus: {session.focus}", expanded=(idx == 1)):
            st.markdown(f"**🔥 Dynamic Warm-Up:** {session.warmup}")
            st.markdown("---")
            
            # Exercise table
            for ex in session.exercises:
                e_col1, e_col2, e_col3 = st.columns([2, 1, 1.5])
                with e_col1:
                    st.markdown(f"**{ex.name}**")
                    st.caption(f"Target Muscle: *{ex.target_muscle}*")
                with e_col2:
                    st.markdown(f"**{ex.sets} Sets × {ex.reps}**")
                    st.caption(f"Rest: {ex.rest_seconds}s")
                with e_col3:
                    st.markdown(f"<span style='font-size:0.85rem;color:#cbd5e1'>{ex.guidance}</span>", unsafe_allow_html=True)
                    if ex.alternatives:
                        st.caption(f"Alternatives: {', '.join(ex.alternatives[:2])}")
                st.divider()

            st.markdown(f"**🧊 Post-Workout Recovery & Cool-Down:** {session.cooldown}")

    st.markdown(
        f"""
        <div class="safety-banner" style="margin-top:20px">
            <strong>🛑 Safety Protocol:</strong> {workout_plan.safety_reminder}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("🛌 Active Recovery & Rest Day Guidelines"):
        st.markdown(workout_plan.recovery_advice)


# -------------------------------------------------------------
# TAB 5: SAFETY & GUIDELINES
# -------------------------------------------------------------
with tab_safety:
    st.subheader("🛡️ Safety, Guardrails & Clinical Boundaries")

    st.markdown(
        """
        <div class="content-box">
            <h3 style="color:#10b981;margin-top:0;">Educational Purpose</h3>
            <p>
                This chatbot is designed to provide general fitness, movement, and nutritional education.
                It utilizes established exercise science principles (such as progressive overload and the Mifflin-St Jeor equation)
                to offer general guidelines for healthy adults.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### Full Medical Disclaimer\n\n{MEDICAL_DISCLAIMER}")

    st.divider()

    st.subheader("🚨 When to Consult Qualified Professionals")
    c_prof1, c_prof2 = st.columns(2)
    with c_prof1:
        st.markdown(
            """
            **Consult a Licensed Physician or Cardiologist if:**
            - You experience chest pressure, shortness of breath, or palpitations during exercise.
            - You have a personal or family history of cardiovascular disease.
            - You are pregnant or recovering postpartum.
            - You have joint arthritis, spinal herniation, or acute orthopedic pain.
            - You are taking prescription medications for blood pressure, blood glucose, or thyroid function.
            """
        )
    with c_prof2:
        st.markdown(
            """
            **Consult a Registered Dietitian (RD/RDN) if:**
            - You manage metabolic conditions such as Type 1 or Type 2 Diabetes.
            - You have severe gastrointestinal disorders (Celiac disease, Crohn's, IBS).
            - You have a history of eating disorders or persistent anxiety around food.
            - You require individualized clinical meal planning for renal disease or liver conditions.
            """
        )

    st.divider()

    st.subheader("📞 Emergency & Mental Health Resources")
    st.markdown(
        """
        - **Emergency Services**: Call **911** (US) or **112** (Europe / International) immediately if you experience acute medical emergencies.
        - **National Eating Disorders Association (NEDA)**:
          - Call or Text: **1-800-931-2237**
          - Crisis Text Line: Text **'NEDA' to 741741**
        - **SAMHSA National Helpline** (Substance Abuse & Mental Health): **1-800-662-4357**
        """
    )
