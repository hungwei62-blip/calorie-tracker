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

CALORIE_DEFICIT_OPTIONS = {
    "溫和（-200 大卡）": 200,
    "標準（-300 大卡）": 300,
    "積極（-400 大卡）": 400,
}
DEFAULT_CALORIE_DEFICIT_LABEL = "標準（-300 大卡）"


def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    if gender == "男":
        return 66 + (13.7 * weight) + (5.0 * height) - (6.8 * age)
    return 655 + (9.6 * weight) + (1.8 * height) - (4.7 * age)


def calculate_tdee(bmr: float, exercise_level: str) -> float:
    return bmr * TDEE_MULTIPLIERS.get(exercise_level, 1.2)


def calculate_goals(
    weight: float,
    tdee: float,
    bmr: float,
    calorie_deficit: int,
) -> dict[str, float]:
    if calorie_deficit not in set(CALORIE_DEFICIT_OPTIONS.values()):
        raise ValueError("熱量赤字只能選擇 200、300 或 400 大卡")
    protein = weight * 2
    calorie = max(0, bmr, tdee - calorie_deficit)
    return {
        "bmr": bmr,
        "calorie": calorie,
        "protein": protein,
        "carb": 0,
        "fat": 0,
        "water": weight * 40,
    }
