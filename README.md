# 🏋️ Fitness & Nutrition Coach — End-to-End AI Coaching Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-SDK%20v1%2B-412991.svg)](https://platform.openai.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![pytest](https://img.shields.io/badge/pytest-Passing-brightgreen.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end, evidence-based **Fitness & Nutrition AI Coach** chatbot built with **Streamlit**, **OpenAI API**, and **Pydantic**. The application combines physiological metabolic formulas (Mifflin-St Jeor), sports science training principles (progressive overload, periodization), allergy-aware meal generation, and clinical safety guardrails.

---

## 📑 Table of Contents
- [Key Features](#-key-features)
- [System Architecture & Project Structure](#-system-architecture--project-structure)
- [Nutrition & Workout Methodology](#-nutrition--workout-methodology)
- [Safety, Ethics & Guardrails](#-safety-ethics--guardrails)
- [Local Setup & Installation](#-local-setup--installation)
- [Environment Configuration](#-environment-configuration)
- [Running the Application](#-running-the-application)
- [Running Automated Tests](#-running-automated-tests)
- [Deployment on Streamlit Community Cloud](#-deployment-on-streamlit-community-cloud)
- [Security Considerations & Limitations](#-security-considerations--limitations)
- [License](#-license)

---

## 🌟 Key Features

### 1. 💬 AI Fitness & Nutrition Chatbot
- Natural language dialogue answering questions about workouts, biomechanics, food nutrition, calorie deficits/surpluses, and healthy habits.
- Injects active user demographics (age, weight, height, BMI, equipment, dietary preferences, and allergies) directly into the dynamic OpenAI system prompt.
- Maintains conversation history across the active Streamlit session with a one-click chat reset button.
- Handles missing API keys, rate limits, network interruptions, and authentication failures gracefully without exposing credentials.

### 2. 👤 Dynamic User Profile
- User-provided parameters: Age, Biological Sex, Height (cm), Weight (kg), Fitness Goal, Activity Level, Dietary Preference, Allergies/Restrictions, Workout Experience, and Available Equipment.
- Validated via **Pydantic v2** with type enforcement, boundary checking, and custom sanitizers.

### 3. 📊 Metabolic & Nutrition Estimates Dashboard
- **Mifflin-St Jeor Equation**: Accurately calculates Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE).
- **Target Daily Calories**: Evidence-based goal calibration (moderate ~450 kcal deficit for fat loss, ~350 kcal surplus for muscle gain, neutral for maintenance).
- **Safe Calorie Floors**: Enforces minimum safe intakes (≥1200 kcal for women, ≥1500 kcal for men) to prevent metabolic distress.
- **Macronutrient Breakdown**: Targets protein (1.6–2.0g/kg body weight), dietary fats (25% total calories), and fills remainder with complex carbohydrates.
- **BMI Metric**: Calculates BMI with WHO category classification.

### 4. 🥗 Allergy-Aware Meal Planner & Food Estimator
- Tailored meal plan generation for **Vegan**, **Vegetarian**, **Non-Vegetarian**, **Pescatarian**, and **Keto** lifestyles.
- Strict allergy filtering: Eliminates specified allergens (e.g., dairy, peanuts, tree nuts, gluten, soy, eggs, shellfish) and suggests safe swaps.
- Interactive Food Nutrition Estimator: Quick lookup for macros and calories, clearly labeled as educational estimates.
- Practical substitution engine for plant-based alternatives and allergen-safe swaps.

### 5. 🏋️ Personalized Workout Generator
- Multi-day structured training splits:
  - **Beginner**: 3-Day Full Body Foundation
  - **Intermediate**: 4-Day Upper / Lower Hypertrophy Split
  - **Advanced**: 5-Day Periodized Push / Pull / Legs / Upper / Lower Split
- Tailored to available equipment: Bodyweight-only, Dumbbells, Resistance Bands, Barbell, or Full Commercial Gym.
- Includes target muscle groups, sets, repetitions, rest periods, exercise guidance, and equipment alternatives.
- Structured dynamic warm-ups and post-workout recovery routines.

---

## 🏗️ System Architecture & Project Structure

```
fitness-nutrition-coach/
├── app.py                      # Main Streamlit application and UI tabs
├── config.py                   # Secure environment loader and API key validator
├── requirements.txt            # Project dependencies
├── .env.example                # Template configuration file (placeholder only)
├── .gitignore                  # Excludes .env, virtualenvs, __pycache__, caches
├── README.md                   # Comprehensive technical documentation
│
├── fitness/                    # Modular domain business logic
│   ├── __init__.py             # Domain package interface
│   ├── models.py               # Pydantic validation models for profiles, meals, workouts
│   ├── nutrition.py            # Mifflin-St Jeor BMR, TDEE, macros, meal generator
│   ├── workouts.py             # Workout generation, exercise alternatives, warmups
│   ├── safety.py               # Clinical safety guardrails, keyword checks, disclaimers
│   └── ai_coach.py             # OpenAI API integration with streaming & prompt injection
│
├── tests/                      # Automated pytest test suite (39 passing tests)
│   ├── __init__.py
│   ├── test_config.py          # Config loading and security masking tests
│   ├── test_nutrition.py       # BMR/TDEE formula tests, macro splits, allergy filters
│   ├── test_workouts.py        # Workout split and equipment alternative tests
│   ├── test_safety.py          # Guardrail red flag and emergency symptom tests
│   ├── test_ai_coach.py        # Mocked OpenAI responses (zero billing) & error handling
│   └── test_app.py             # Streamlit AppTest end-to-end rendering test
│
└── .streamlit/
    └── config.toml             # Custom theme (dark mode, emerald accents) and server rules
```

---

## 🔬 Nutrition & Workout Methodology

### Basal Metabolic Rate (BMR)
Calculated using the **Mifflin-St Jeor Equation** (1990):
- **Men:** $BMR = (10 \times \text{weight in kg}) + (6.25 \times \text{height in cm}) - (5 \times \text{age in years}) + 5$
- **Women:** $BMR = (10 \times \text{weight in kg}) + (6.25 \times \text{height in cm}) - (5 \times \text{age in years}) - 161$
- **Other / Unspecified:** Midpoint average of male and female formula: $\text{Base} - 78$

### Total Daily Energy Expenditure (TDEE)
$$\text{TDEE} = \text{BMR} \times \text{Activity Multiplier}$$
- **Sedentary:** 1.2
- **Lightly Active:** 1.375
- **Moderately Active:** 1.55
- **Very Active:** 1.725
- **Extra Active:** 1.9

### Macronutrient Guidelines (ISSN Standards)
1. **Protein**: 1.6 to 2.0g per kg of total body mass to optimize muscle protein synthesis and spare muscle mass during deficits.
2. **Fat**: 25% of total energy budgeted for hormonal function, essential fatty acids, and fat-soluble vitamin uptake.
3. **Carbohydrates**: Remaining energy allocated to carbohydrates (4 kcal/g) for glycogen replenishment and training performance.

---

## 🛡️ Safety, Ethics & Guardrails

The application enforces strict health boundaries in code (`fitness/safety.py`) and via OpenAI system prompts:

1. **Medical Boundaries**: Never provides medical diagnoses or prescriptions. Emphasizes that advice is purely educational.
2. **Acute Emergency Detection**: Queries mentioning acute cardiovascular symptoms (e.g. chest pain, left-arm numbness, fainting) immediately trigger emergency medical guidance (911 / 112) and advise stopping all exercise.
3. **Disordered Eating & Starvation Interception**: Intercepts requests for extreme calorie restriction (<1000 kcal diets, starvation, purging) and directs users to the **National Eating Disorders Association (NEDA) Helpline** (1-800-931-2237).
4. **Banned Substance Prevention**: Flags and declines inquiries promoting anabolic-androgenic steroids, SARMs, or unapproved fat-loss chemicals (e.g. DNP).
5. **Special Population Warnings**: Provides caution flags for pregnancy, minors, and chronic medical illnesses.
6. **No Fake Verifications**: Explicitly identifies food estimates as standard nutritional averages and never claims unverified laboratory or clinical validation.

---

## 💻 Local Setup & Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Adarshdixit80/fitness-nutrition-coach.git
cd fitness-nutrition-coach
```

### 2. Create and Activate a Virtual Environment
```bash
# macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# Windows (Command Prompt / PowerShell):
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Configuration

Create a `.env` file in the root directory by copying `.env.example`:

```bash
cp .env.example .env
```

Open `.env` and configure your settings:

```ini
# OpenAI API Key (Never commit this file to version control!)
OPENAI_API_KEY=sk-proj-yourActualKeyHere...

# OpenAI Model Selection (defaults to gpt-4o-mini if left unset)
OPENAI_MODEL=gpt-4o-mini
```

> **Security Note:** `.env` is listed in `.gitignore` and will never be tracked by Git. If an API key is not provided in `.env`, the user can temporarily enter their key inside the app sidebar for the active browser session.

---

## 🚀 Running the Application

Launch the Streamlit web application:

```bash
streamlit run app.py
```

The application will start and open in your default browser at:
```
http://localhost:8501
```

---

## 🧪 Running Automated Tests

The project includes an automated test suite with **39 tests** covering configuration, nutrition formulas, workout plans, safety guardrails, mocked AI responses, and Streamlit component rendering:

```bash
# Run the full test suite with verbose output
pytest -v

# Run with test coverage report
pytest --cov=fitness --cov=config
```

### Test Coverage Highlights
- `tests/test_config.py`: Verifies secure key loading, placeholder rejection, and model defaults.
- `tests/test_nutrition.py`: Verifies Mifflin-St Jeor calculations against manual mathematical baselines, TDEE scaling, safe calorie floors, and allergy filters.
- `tests/test_workouts.py`: Tests 3-day, 4-day, and 5-day routine generation across beginner/intermediate/advanced levels and equipment types.
- `tests/test_safety.py`: Verifies acute emergency detection, eating disorder protection, and medical disclaimers.
- `tests/test_ai_coach.py`: Mocks OpenAI completions to test prompt building, API errors (AuthenticationError, RateLimitError), and zero billing during tests.
- `tests/test_app.py`: Simulates end-to-end Streamlit app execution and verifies tab rendering.

---

## ☁️ Deployment on Streamlit Community Cloud

Deploying to **Streamlit Community Cloud** is straightforward:

1. Push your repository to GitHub: `https://github.com/<your-username>/fitness-nutrition-coach`.
2. Visit [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **"New app"**.
4. Select your repository (`fitness-nutrition-coach`), branch (`main`), and main file path (`app.py`).
5. Open **"Advanced settings"** -> **"Secrets"** and enter your production credentials:
   ```toml
   OPENAI_API_KEY = "sk-proj-your-production-key-here"
   OPENAI_MODEL = "gpt-4o-mini"
   ```
6. Click **"Deploy!"**. Streamlit will install dependencies from `requirements.txt` and launch your live application.

---

## 🔒 Security Considerations & Limitations

- **Credential Isolation**: OpenAI API keys are never stored in client-side code, never committed to Git, and never exposed in error responses.
- **Mocked Automated Tests**: Automated tests use `unittest.mock` to intercept external API calls, guaranteeing zero API billing during continuous integration.
- **Educational Approximation**: All caloric and macronutrient targets are mathematical approximations. Individual metabolism varies based on gut microbiota, thyroid function, lean mass percentage, and genetics.
- **Pain & Medical Boundaries**: Users experiencing physical pain or medical symptoms are guided to certified healthcare professionals.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
#   f i t n e s s - n u t r i t i o n - c o a c h  
 