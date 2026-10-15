"""Workout generation module.

Generates structured, evidence-based resistance training and conditioning plans
customized by fitness goal, experience level, and available equipment.
Includes progression models, warm-ups, recovery, and equipment substitution logic.
"""

from typing import Dict, List
from fitness.models import (
    Exercise,
    FitnessGoal,
    UserProfile,
    WorkoutExperience,
    WorkoutPlan,
    WorkoutSession,
)

# Standard exercise substitution index
EXERCISE_ALTERNATIVES: Dict[str, Dict[str, List[str]]] = {
    "Barbell Back Squat": {
        "dumbbells": ["Dumbbell Goblet Squat", "Dumbbell Bulgarian Split Squat", "Dumbbell Front Squat"],
        "bodyweight": ["Bodyweight Squat", "Bulgarian Split Squat", "Pistol Squat (Assisted)"],
        "resistance bands": ["Banded Squat", "Banded Spanish Squat"],
    },
    "Barbell Bench Press": {
        "dumbbells": ["Flat Dumbbell Chest Press", "Incline Dumbbell Press", "Dumbbell Floor Press"],
        "bodyweight": ["Push-Ups (Standard or Elevated)", "Deficit Push-Ups", "Decline Push-Ups"],
        "resistance bands": ["Banded Push-Up", "Standing Band Chest Press"],
    },
    "Conventional Barbell Deadlift": {
        "dumbbells": ["Dumbbell Romanian Deadlift (RDL)", "Dumbbell Single-Leg RDL", "Dumbbell Sumo Deadlift"],
        "bodyweight": ["Single-Leg Romanian Deadlift", "Glute Bridges", "Nordic Hamstring Curls (assisted)"],
        "resistance bands": ["Banded Good Mornings", "Banded Romanian Deadlift"],
    },
    "Overhead Barbell Press": {
        "dumbbells": ["Seated or Standing Dumbbell Overhead Press", "Arnold Press"],
        "bodyweight": ["Pike Push-Ups", "Elevated Feet Pike Push-Ups", "Handstand Hold"],
        "resistance bands": ["Standing Banded Shoulder Press", "Band Lateral Raises"],
    },
    "Pull-Ups / Lat Pulldown": {
        "dumbbells": ["Dumbbell Bent-Over Row", "Single-Arm Dumbbell Row", "Dumbbell Chest-Supported Row"],
        "bodyweight": ["Inverted Rows (under a table/bed)", "Doorway Rows", "Scapular Pulls"],
        "resistance bands": ["Banded Lat Pulldown", "Banded Kneeling Face Pulls"],
    },
    "Dumbbell Bicep Curls": {
        "bodyweight": ["Chin-Ups (underhand grip)", "Towel Isometric Curls"],
        "resistance bands": ["Banded Bicep Curls", "Banded Hammer Curls"],
    },
    "Tricep Rope Pushdowns": {
        "dumbbells": ["Dumbbell Overhead Tricep Extension", "Dumbbell Skull Crushers"],
        "bodyweight": ["Bench/Chair Dips", "Diamond Push-Ups"],
        "resistance bands": ["Banded Tricep Pushdown", "Overhead Band Extension"],
    },
}


def get_exercise_alternatives(exercise_name: str, equipment: List[str]) -> List[str]:
    """Retrieve suitable alternatives for an exercise based on available equipment."""
    alternatives = []
    exercise_clean = exercise_name.strip()
    
    # Check exact or partial match in alternative map
    for base_exercise, eq_map in EXERCISE_ALTERNATIVES.items():
        if base_exercise.lower() in exercise_clean.lower() or exercise_clean.lower() in base_exercise.lower():
            for eq_type, sub_list in eq_map.items():
                if any(eq in " ".join(equipment).lower() for eq in [eq_type, "full gym"]):
                    alternatives.extend(sub_list)

    if not alternatives:
        # Generic alternatives
        alternatives = [
            "Bodyweight tempo variations (3-second eccentric phase)",
            "Unilateral / single-leg / single-arm variation for progressive overload without extra weight",
            "Resistance band equivalent with paused isometric contractions",
        ]
    return list(dict.fromkeys(alternatives))[:3]


def get_warmup_cooldown_routine() -> Dict[str, str]:
    """Provide standard dynamic warm-up and post-workout cool-down guidance."""
    return {
        "warmup": (
            "5-8 minutes dynamic mobility: Arm circles, Cat-Cow (10 reps), World's Greatest Stretch (5 per side), "
            "Bodyweight air squats (15 reps), Glute bridges (15 reps), and 2-3 light warm-up sets building up to working weight."
        ),
        "cooldown": (
            "5-10 minutes restorative cool-down: Low-intensity nasal walking, static stretching for hamstrings, hip flexors, "
            "chest, and lats (hold 30-45s per side), deep diaphragmatic box breathing (4s in, 4s hold, 4s out, 4s hold)."
        ),
    }


def generate_workout_plan(profile: UserProfile) -> WorkoutPlan:
    """Generate a structured, evidence-based workout routine customized for the user.

    Balances training frequency, volume, and exercise selection based on equipment
    and experience level.
    """
    exp = profile.workout_experience
    goal = profile.fitness_goal
    equipment = profile.available_equipment
    has_weights = any(e in " ".join(equipment).lower() for e in ["dumbbells", "barbell", "full gym", "kettlebells", "weights"])
    has_gym = any(e in " ".join(equipment).lower() for e in ["full gym", "gym", "barbell"])

    routines = get_warmup_cooldown_routine()

    # Determine progression advice based on goal and experience
    if goal == FitnessGoal.MUSCLE_GAIN:
        progression = (
            "Progressive Overload Principle: When you can complete the upper rep target (e.g. 12 reps) with clean form "
            "across all sets, increase resistance by 2-5% or add 1 additional repetition next session. Keep 1-2 reps in reserve (RIR 1-2)."
        )
    elif goal == FitnessGoal.WEIGHT_LOSS:
        progression = (
            "Maintain Strength Focus: Maintain lifting loads as much as possible to preserve lean muscle tissue during a calorie deficit. "
            "Keep rest intervals controlled (60-90s) and conclude sessions with 10-15 minutes of zone-2 low-impact aerobic activity (brisk incline walk)."
        )
    else:
        progression = (
            "Consistency & Form Mastery: Focus on smooth movement execution and controlled tempo (2 seconds down, 1 second up). "
            "Gradually increase training volume by 1 set per exercise every 3-4 weeks."
        )

    recovery = (
        "Active Recovery & Rest: Target 7,000-10,000 daily steps on off days. Prioritize 7-9 hours of restful sleep for tissue repair "
        "and drink at least 2.5-3.5 liters of water daily. Ensure at least 48 hours of recovery before retraining the same primary muscle group."
    )

    safety = (
        "STOP IF YOU FEEL PAIN: Exercise-induced muscular fatigue or a burning sensation is normal, but sharp, pinching, "
        "or asymmetric joint pain is an immediate signal to stop. Never push through joint or spinal pain. Consult a licensed "
        "physical therapist or physician if pain persists."
    )

    # 1. Beginner Plan (Full Body 3 Days per Week)
    if exp == WorkoutExperience.BEGINNER:
        title = "3-Day Beginner Full-Body Foundation"
        days_per_week = 3
        
        if has_gym:
            day1_exercises = [
                Exercise(
                    name="Barbell Back Squat (or Goblet Squat)",
                    target_muscle="Quadriceps, Glutes, Core",
                    sets=3,
                    reps="8-10 reps",
                    rest_seconds=90,
                    guidance="Keep chest tall, push knees outward in line with toes, achieve parallel depth.",
                    alternatives=get_exercise_alternatives("Barbell Back Squat", equipment),
                ),
                Exercise(
                    name="Barbell Bench Press (or Dumbbell Press)",
                    target_muscle="Pectorals, Anterior Deltoids, Triceps",
                    sets=3,
                    reps="8-10 reps",
                    rest_seconds=90,
                    guidance="Retract shoulder blades, plant feet firmly, lower bar controlled to mid-chest.",
                    alternatives=get_exercise_alternatives("Barbell Bench Press", equipment),
                ),
                Exercise(
                    name="Lat Pulldown (or Inverted Rows)",
                    target_muscle="Latissimus Dorsi, Biceps, Upper Back",
                    sets=3,
                    reps="10-12 reps",
                    rest_seconds=60,
                    guidance="Drive elbows straight down towards hips, pause briefly at collarbone.",
                    alternatives=get_exercise_alternatives("Pull-Ups / Lat Pulldown", equipment),
                ),
                Exercise(
                    name="Romanian Deadlift (Dumbbell or Barbell)",
                    target_muscle="Hamstrings, Glutes, Lower Back",
                    sets=3,
                    reps="10-12 reps",
                    rest_seconds=75,
                    guidance="Hinge at hips with soft knees, keep spine neutral, feel hamstring stretch.",
                    alternatives=get_exercise_alternatives("Conventional Barbell Deadlift", equipment),
                ),
                Exercise(
                    name="Plank Hold",
                    target_muscle="Core & Transverse Abdominis",
                    sets=3,
                    reps="30-45 seconds",
                    rest_seconds=60,
                    guidance="Brace abs as if expecting a punch, keep straight line from heels to shoulders.",
                    alternatives=["Deadbug (12 reps/side)", "Bird-Dog (10 reps/side)"],
                ),
            ]
        elif has_weights:
            day1_exercises = [
                Exercise(
                    name="Dumbbell Goblet Squat",
                    target_muscle="Quadriceps & Glutes",
                    sets=3,
                    reps="10-12 reps",
                    rest_seconds=75,
                    guidance="Hold dumbbell vertically against chest, elbows tracking inside knees.",
                    alternatives=["Bodyweight Tempo Squats", "Step-Ups onto Chair/Box"],
                ),
                Exercise(
                    name="Dumbbell Flat Bench / Floor Press",
                    target_muscle="Chest & Triceps",
                    sets=3,
                    reps="10-12 reps",
                    rest_seconds=75,
                    guidance="Keep wrists over elbows, press dumbbells in smooth natural arc.",
                    alternatives=["Push-Ups (elevated if needed)", "Banded Chest Press"],
                ),
                Exercise(
                    name="Single-Arm Dumbbell Row",
                    target_muscle="Lats & Mid-Back",
                    sets=3,
                    reps="10-12 reps per side",
                    rest_seconds=60,
                    guidance="Support on bench or knee, pull elbow back towards hip without rotating torso.",
                    alternatives=["Banded Seated Row", "Doorframe Towel Row"],
                ),
                Exercise(
                    name="Dumbbell Romanian Deadlift",
                    target_muscle="Hamstrings & Posterior Chain",
                    sets=3,
                    reps="10-12 reps",
                    rest_seconds=75,
                    guidance="Push hips backward, keep dumbbells skimming shins, neutral neck.",
                    alternatives=["Single-Leg Glute Bridge", "Good Mornings with Band"],
                ),
                Exercise(
                    name="Dumbbell Overhead Shoulder Press",
                    target_muscle="Shoulders & Triceps",
                    sets=3,
                    reps="10-12 reps",
                    rest_seconds=60,
                    guidance="Press straight overhead without arching lower back. Squeeze glutes for stability.",
                    alternatives=["Pike Push-Up", "Banded Overhead Press"],
                ),
            ]
        else:  # Bodyweight only
            day1_exercises = [
                Exercise(
                    name="Bodyweight Squats (Tempo 3-1-1)",
                    target_muscle="Quadriceps & Glutes",
                    sets=3,
                    reps="12-15 reps",
                    rest_seconds=60,
                    guidance="Take 3 seconds lowering, pause 1 second at bottom, stand up explosively.",
                    alternatives=["Wall Sit (45s)", "Step-Ups"],
                ),
                Exercise(
                    name="Push-Ups (Incline / Standard / Knee)",
                    target_muscle="Chest, Shoulders & Triceps",
                    sets=3,
                    reps="8-12 reps",
                    rest_seconds=60,
                    guidance="Rigid plank position. Lower chest within 2 inches of the floor.",
                    alternatives=["Deficit Push-Up", "Isometric Push-Up Hold"],
                ),
                Exercise(
                    name="Inverted Rows (under sturdy table) or Doorway Rows",
                    target_muscle="Upper Back & Biceps",
                    sets=3,
                    reps="10-12 reps",
                    rest_seconds=60,
                    guidance="Pull chest towards surface, pinch shoulder blades together at peak.",
                    alternatives=["Towel Doorframe Rows", "Prone Cobra Holds (30s)"],
                ),
                Exercise(
                    name="Glute Bridges (Bilateral or Single-Leg)",
                    target_muscle="Glutes & Hamstrings",
                    sets=3,
                    reps="15 reps",
                    rest_seconds=45,
                    guidance="Drive through heels, pause and squeeze glutes hard at the top.",
                    alternatives=["Single-Leg Romanian Deadlift (unweighted)", "Frog Pumps"],
                ),
                Exercise(
                    name="Plank to Downward Dog",
                    target_muscle="Core & Shoulder Stability",
                    sets=3,
                    reps="10-12 reps",
                    rest_seconds=45,
                    guidance="Alternate between solid plank and pushing hips skyward.",
                    alternatives=["Deadbugs (12 per side)", "Bird-Dogs"],
                ),
            ]

        sessions = [
            WorkoutSession(
                day_title="Day 1: Full Body A (Foundational Strength)",
                focus="Full Body Strength & Core Stability",
                warmup=routines["warmup"],
                exercises=day1_exercises,
                cooldown=routines["cooldown"],
            ),
            WorkoutSession(
                day_title="Day 2: Full Body B (Muscular Endurance & Posterior Chain)",
                focus="Hip-Hinge, Vertical Pull, and Overhead Movement",
                warmup=routines["warmup"],
                exercises=day1_exercises,  # Alternate variation
                cooldown=routines["cooldown"],
            ),
            WorkoutSession(
                day_title="Day 3: Full Body C (Compound Balance & Conditioning)",
                focus="Lunge/Split Stance, Horizontal Press, and Functional Core",
                warmup=routines["warmup"],
                exercises=day1_exercises,
                cooldown=routines["cooldown"],
            ),
        ]

    # 2. Intermediate Plan (4-Day Upper / Lower Split)
    elif exp == WorkoutExperience.INTERMEDIATE:
        title = "4-Day Intermediate Upper / Lower Hypertrophy Split"
        days_per_week = 4
        
        upper_exercises = [
            Exercise(
                name="Barbell or Dumbbell Bench Press",
                target_muscle="Chest & Triceps",
                sets=4,
                reps="6-8 reps",
                rest_seconds=90,
                guidance="Focus on heavy controlled presses with steady tempo.",
                alternatives=get_exercise_alternatives("Barbell Bench Press", equipment),
            ),
            Exercise(
                name="Bent-Over Barbell or Dumbbell Row",
                target_muscle="Lats & Mid-Back",
                sets=4,
                reps="8-10 reps",
                rest_seconds=90,
                guidance="Hinge 45 degrees, pull through elbows into lower ribs.",
                alternatives=get_exercise_alternatives("Pull-Ups / Lat Pulldown", equipment),
            ),
            Exercise(
                name="Seated Dumbbell Overhead Shoulder Press",
                target_muscle="Shoulders",
                sets=3,
                reps="8-12 reps",
                rest_seconds=75,
                guidance="Keep elbows slightly forward of body in scapular plane.",
                alternatives=get_exercise_alternatives("Overhead Barbell Press", equipment),
            ),
            Exercise(
                name="Incline Dumbbell Bicep Curls",
                target_muscle="Biceps",
                sets=3,
                reps="10-12 reps",
                rest_seconds=60,
                guidance="Full extension at the bottom for maximum stretch on the long head.",
                alternatives=get_exercise_alternatives("Dumbbell Bicep Curls", equipment),
            ),
            Exercise(
                name="Overhead Tricep Extension (Dumbbell or Cable)",
                target_muscle="Triceps Long Head",
                sets=3,
                reps="10-12 reps",
                rest_seconds=60,
                guidance="Keep upper arms stationary near ears, bend only at elbows.",
                alternatives=get_exercise_alternatives("Tricep Rope Pushdowns", equipment),
            ),
        ]

        lower_exercises = [
            Exercise(
                name="Squat (Barbell, Goblet, or Bulgarian Split Squat)",
                target_muscle="Quadriceps & Glutes",
                sets=4,
                reps="6-8 reps",
                rest_seconds=120,
                guidance="Maintain upright posture, deep hip crease, drive evenly through feet.",
                alternatives=get_exercise_alternatives("Barbell Back Squat", equipment),
            ),
            Exercise(
                name="Romanian Deadlift (RDL)",
                target_muscle="Hamstrings & Posterior Chain",
                sets=4,
                reps="8-10 reps",
                rest_seconds=90,
                guidance="Drive hips back, keep weights close to body, neutral spine throughout.",
                alternatives=get_exercise_alternatives("Conventional Barbell Deadlift", equipment),
            ),
            Exercise(
                name="Walking Lunges (with or without weights)",
                target_muscle="Glutes & Quads",
                sets=3,
                reps="10 reps per leg",
                rest_seconds=60,
                guidance="Step forward smoothly, back knee gently kissing floor, upright torso.",
                alternatives=["Step-Ups", "Reverse Lunges"],
            ),
            Exercise(
                name="Standing or Seated Calf Raises",
                target_muscle="Calves (Gastrocnemius & Soleus)",
                sets=4,
                reps="12-15 reps",
                rest_seconds=45,
                guidance="2-second stretch at bottom, 1-second peak contraction.",
                alternatives=["Single-Leg Bodyweight Calf Raises"],
            ),
            Exercise(
                name="Hanging Leg Raises / Lying Leg Raises",
                target_muscle="Lower Rectus Abdominis",
                sets=3,
                reps="12-15 reps",
                rest_seconds=60,
                guidance="Roll pelvis upward towards chest; avoid swinging.",
                alternatives=["Ab Wheel Rollouts", "Bicycle Crunches"],
            ),
        ]

        sessions = [
            WorkoutSession(
                day_title="Day 1: Upper Body Power & Hypertrophy",
                focus="Horizontal Press & Pull, Shoulders",
                warmup=routines["warmup"],
                exercises=upper_exercises,
                cooldown=routines["cooldown"],
            ),
            WorkoutSession(
                day_title="Day 2: Lower Body Power & Quad Dominance",
                focus="Squat Pattern, Hamstring Hinges, Calves",
                warmup=routines["warmup"],
                exercises=lower_exercises,
                cooldown=routines["cooldown"],
            ),
            WorkoutSession(
                day_title="Day 3: Upper Body Volume & Accessories",
                focus="Incline Press, Vertical Pull, Arms & Delts",
                warmup=routines["warmup"],
                exercises=upper_exercises,
                cooldown=routines["cooldown"],
            ),
            WorkoutSession(
                day_title="Day 4: Lower Body Posterior Chain & Conditioning",
                focus="Deadlift / Hinge Pattern, Unilateral Legs, Core",
                warmup=routines["warmup"],
                exercises=lower_exercises,
                cooldown=routines["cooldown"],
            ),
        ]

    # 3. Advanced Plan (5-Day Push / Pull / Legs / Upper / Lower Split)
    else:
        title = "5-Day Advanced Periodized Split (Push / Pull / Legs / Upper / Lower)"
        days_per_week = 5
        
        push_exercises = [
            Exercise(
                name="Barbell Incline Bench Press",
                target_muscle="Upper Chest & Front Deltoids",
                sets=4,
                reps="6-8 reps",
                rest_seconds=90,
                guidance="Angle bench to 30 degrees, controlled lower to upper chest.",
                alternatives=get_exercise_alternatives("Barbell Bench Press", equipment),
            ),
            Exercise(
                name="Standing Dumbbell Shoulder Press",
                target_muscle="Anterior & Lateral Deltoids",
                sets=4,
                reps="8-10 reps",
                rest_seconds=75,
                guidance="Full range of motion, lockout overhead with core engaged.",
                alternatives=get_exercise_alternatives("Overhead Barbell Press", equipment),
            ),
            Exercise(
                name="Dumbbell Lateral Raises (Strict)",
                target_muscle="Lateral Deltoid",
                sets=4,
                reps="12-15 reps",
                rest_seconds=45,
                guidance="Lead with elbows, pause at parallel, avoid shrugging traps.",
                alternatives=["Banded Lateral Raises", "Cable Lateral Raises"],
            ),
            Exercise(
                name="Tricep Dips (Weighted or Bodyweight)",
                target_muscle="Triceps & Lower Chest",
                sets=3,
                reps="8-12 reps",
                rest_seconds=60,
                guidance="Keep torso upright to prioritize triceps, lower to 90 degrees elbow bend.",
                alternatives=get_exercise_alternatives("Tricep Rope Pushdowns", equipment),
            ),
        ]

        pull_exercises = [
            Exercise(
                name="Deadlift / Heavy Rack Pulls",
                target_muscle="Full Posterior Chain & Traps",
                sets=4,
                reps="5-6 reps",
                rest_seconds=120,
                guidance="Reset each rep, engage lats, push floor away through midfoot.",
                alternatives=get_exercise_alternatives("Conventional Barbell Deadlift", equipment),
            ),
            Exercise(
                name="Weighted or Bodyweight Pull-Ups",
                target_muscle="Latissimus Dorsi",
                sets=4,
                reps="6-10 reps",
                rest_seconds=90,
                guidance="Dead hang at bottom, clear chin over bar without kipping.",
                alternatives=get_exercise_alternatives("Pull-Ups / Lat Pulldown", equipment),
            ),
            Exercise(
                name="Chest-Supported Dumbbell Rows",
                target_muscle="Rhomboids & Mid-Traps",
                sets=3,
                reps="10-12 reps",
                rest_seconds=60,
                guidance="Eliminates lower-back fatigue, strict retraction at top.",
                alternatives=["Single-Arm Dumbbell Row", "Inverted Row"],
            ),
            Exercise(
                name="Barbell or Dumbbell Bicep Curls",
                target_muscle="Biceps Brachii",
                sets=3,
                reps="10-12 reps",
                rest_seconds=60,
                guidance="Supinate wrists, squeeze hard at peak without swinging elbows.",
                alternatives=get_exercise_alternatives("Dumbbell Bicep Curls", equipment),
            ),
        ]

        legs_exercises = [
            Exercise(
                name="Barbell Back Squat",
                target_muscle="Quadriceps & Glutes",
                sets=4,
                reps="6-8 reps",
                rest_seconds=120,
                guidance="Depth below parallel with tight brace. Build strength foundation.",
                alternatives=get_exercise_alternatives("Barbell Back Squat", equipment),
            ),
            Exercise(
                name="Romanian Deadlift",
                target_muscle="Hamstrings & Glutes",
                sets=4,
                reps="8-10 reps",
                rest_seconds=90,
                guidance="Strict hip hinge, maximize hamstring stretch under tension.",
                alternatives=get_exercise_alternatives("Conventional Barbell Deadlift", equipment),
            ),
            Exercise(
                name="Bulgarian Split Squats (Dumbbells)",
                target_muscle="Quads, Glutes & Adductors",
                sets=3,
                reps="10-12 reps per leg",
                rest_seconds=60,
                guidance="Elevate rear foot, sink deep into front hip.",
                alternatives=["Walking Lunges", "Step-Ups"],
            ),
            Exercise(
                name="Calf & Core Superset",
                target_muscle="Calves & Abdominals",
                sets=4,
                reps="15 reps each",
                rest_seconds=45,
                guidance="Calf raises immediately followed by hanging leg raises.",
                alternatives=["Plank + Single-Leg Calf Raise"],
            ),
        ]

        sessions = [
            WorkoutSession(
                day_title="Day 1: Push (Chest, Shoulders, Triceps)",
                focus="Horizontal & Vertical Pushing Hypertrophy",
                warmup=routines["warmup"],
                exercises=push_exercises,
                cooldown=routines["cooldown"],
            ),
            WorkoutSession(
                day_title="Day 2: Pull (Back, Rear Delts, Biceps)",
                focus="Deadlift, Vertical Pull, Horizontal Rows",
                warmup=routines["warmup"],
                exercises=pull_exercises,
                cooldown=routines["cooldown"],
            ),
            WorkoutSession(
                day_title="Day 3: Legs & Core (Squats, Hinge, Unilateral)",
                focus="Quad Dominance, Posterior Chain, Calves",
                warmup=routines["warmup"],
                exercises=legs_exercises,
                cooldown=routines["cooldown"],
            ),
            WorkoutSession(
                day_title="Day 4: Upper Body Density & Hypertrophy",
                focus="Antagonistic Upper Body Pairs (Chest/Back, Arms)",
                warmup=routines["warmup"],
                exercises=push_exercises,
                cooldown=routines["cooldown"],
            ),
            WorkoutSession(
                day_title="Day 5: Lower Body Posterior & Conditioning",
                focus="Hamstring Isolation, Hip Thrusts, Core & Mobility",
                warmup=routines["warmup"],
                exercises=legs_exercises,
                cooldown=routines["cooldown"],
            ),
        ]

    return WorkoutPlan(
        title=title,
        goal=goal.value.replace("_", " ").title(),
        experience_level=exp.value.title(),
        frequency_days=days_per_week,
        sessions=sessions,
        progression_advice=progression,
        recovery_advice=recovery,
        safety_reminder=safety,
    )
