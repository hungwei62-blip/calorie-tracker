"""BMR、TDEE 與營養目標計算。"""

from __future__ import annotations


TDEE_MULTIPLIERS = {
    "幾乎不動": 1.2,
    "每週運動 1-3 天": 1.375,
    "每週運動 3-5 天": 1.55,
    "每週運動 6-7 天": 1.72,
    "每天激烈運動": 1.9,
}
EXERCISE_LEVELS = list(TDEE_MULTIPLIERS)


def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    if gender == "男":
        return 66 + (13.7 * weight) + (5.0 * height) - (6.8 * age)
    return 655 + (9.6 * weight) + (1.8 * height) - (4.7 * age)


def calculate_tdee(bmr: float, exercise_level: str) -> float:
    return bmr * TDEE_MULTIPLIERS.get(exercise_level, 1.2)


def calculate_goals(weight: float, tdee: float, goal_type: str = "維持") -> dict[str, float]:
    protein = weight * 2
    fat = weight * 0.8
    carb = ((tdee - 100) - (protein * 4) - (fat * 9)) / 4
    calorie = tdee - 300 if goal_type == "減脂" else tdee + 300 if goal_type == "增肌" else tdee
    return {
        "bmr": 0,
        "calorie": max(0, calorie),
        "protein": protein,
        "carb": max(0, carb),
        "fat": fat,
        "water": weight * 40,
    }
