"""Gemini 2.5 Flash 營養辨識服務。

辨識結果包含五個欄位：food_summary / calories / protein / carb / fat
"""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import errors, types
from PIL import Image


MODEL_NAME = "gemini-2.5-flash"
ENV_VAR = "gemini_api_key"  # Streamlit secrets key (對應降低字尾允許, .lower())

SYSTEM_PROMPT = """你是一位專業的營養師。請嚴格分析使用者提供的「食物照片」或「文字描述」，估計這一餐 / 造食物的「整體」營養總和，不要先估單味再計算。

請嚴格遵守以下 JSON 格式回傳，不要包含任何 markdown 標記（如 ```json）、不要包含額外的解釋文字或空格：
{"food_summary": "清晰的食物摘要（例如：一個便當含炒麵、雞肉、三式青菜）", "calories": 650, "protein": 30, "carb": 60, "fat": 20}"""

RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "food_summary": types.Schema(type=types.Type.STRING),
        "calories": types.Schema(type=types.Type.NUMBER),
        "protein": types.Schema(type=types.Type.NUMBER),
        "carb": types.Schema(type=types.Type.NUMBER),
        "fat": types.Schema(type=types.Type.NUMBER),
    },
    required=["food_summary", "calories", "protein", "carb", "fat"],
)

CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    response_mime_type="application/json",
    response_schema=RESPONSE_SCHEMA,
    temperature=0.2,
)


def _get_api_key() -> str:
    # 1) Streamlit secrets (部署上線時)
    try:
        import streamlit as st

        if hasattr(st, "secrets") and ENV_VAR in st.secrets:
            return str(st.secrets[ENV_VAR])
    except Exception:
        pass
    # 2) 環境變數 (本機開發 / CLI 走 gemini_nutrition.py)
    import os

    val = os.environ.get("GEMINI_API_KEY")
    if val:
        return val
    raise EnvironmentError(
        "找不到 Gemini API Key。請在 .streamlit/secrets.toml 設定 "
        "GEMINI_API_KEY 或者設定環境變數 GEMINI_API_KEY。"
    )


def _get_client() -> genai.Client:
    return genai.Client(api_key=_get_api_key())


def _parse_response(response: Any) -> dict[str, Any]:
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini 回傳空內容")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini 回傳不是有效 JSON: {text!r}") from exc
    expected = {"food_summary", "calories", "protein", "carb", "fat"}
    missing = expected - set(data.keys())
    if missing:
        raise RuntimeError(f"Gemini 回傳缺少欄位: {sorted(missing)}")
    # 變型安全：數值變為 float，任何無法譯讀的值以 0 替代
    for k in ("calories", "protein", "carb", "fat"):
        try:
            data[k] = float(data[k])
        except (TypeError, ValueError):
            data[k] = 0.0
    # Atwater 公式: 蛋白 4 + 碳水 4 + 脂肪 9 (kcal/g)
    # 始終計算 Atwater 熱量，確保準確性
    atwater_calories = data["protein"] * 4 + data["carb"] * 4 + data["fat"] * 9
    
    # 如果原始熱量為 0 但巨量營養素有值，使用 Atwater 公式計算的熱量
    if data["calories"] <= 0 and atwater_calories > 0:
        data["calories"] = round(atwater_calories, 2)
    
    return data


def _generate(parts: list[Any]) -> dict[str, Any]:
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=parts,
            config=CONFIG,
        )
    except errors.APIError as exc:
        raise RuntimeError(f"Gemini API 呼叫失敗: {exc}") from exc
    return _parse_response(response)


def analyze_image(image: Image.Image) -> dict[str, Any]:
    """接受 Pillow Image 並返回結構化營養資訊。"""
    parts: list[Any] = [image, "請分析這張食物照片。"]
    return _generate(parts)


def analyze_text(description: str) -> dict[str, Any]:
    """接受純文字並返回結構化營養資訊。"""
    if not description or not description.strip():
        raise ValueError("描述不可以是空字串")
    parts: list[Any] = [description.strip()]
    return _generate(parts)
