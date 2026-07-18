"""Gemini 2.5 Flash 食物照片辨識服務。"""

from __future__ import annotations

import json
import math
from typing import Any

from google import genai
from google.genai import errors, types
from PIL import Image


MODEL_NAME = "gemini-2.5-flash"
SECRET_NAME = "GEMINI_API_KEY"

SYSTEM_PROMPT = """你是專業的營養分析助手，只分析使用者提供的食物照片。
請辨識照片中所有可食用內容，估計整張照片所呈現餐點的總熱量與總蛋白質；不要重複計算同一食物，無法判斷份量時採保守估計。
如果照片不是食物、內容過度模糊、遮擋嚴重或無法可靠辨識，is_food 必須為 false，且 calories 與 protein 回傳 0。
所有數值必須是非負有限數字。只回傳符合 schema 的 JSON，不要加入 Markdown 或額外說明。"""

RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "is_food": types.Schema(type=types.Type.BOOLEAN),
        "food_summary": types.Schema(type=types.Type.STRING),
        "calories": types.Schema(type=types.Type.NUMBER),
        "protein": types.Schema(type=types.Type.NUMBER),
    },
    required=["is_food", "food_summary", "calories", "protein"],
)

CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    response_mime_type="application/json",
    response_schema=RESPONSE_SCHEMA,
    temperature=0.2,
)


def _get_api_key() -> str:
    try:
        import streamlit as st

        if hasattr(st, "secrets") and SECRET_NAME in st.secrets:
            return str(st.secrets[SECRET_NAME])
    except Exception:
        pass

    import os

    value = os.environ.get(SECRET_NAME)
    if value:
        return value
    raise EnvironmentError(
        "找不到 Gemini API Key。請在 .streamlit/secrets.toml 或環境變數設定 GEMINI_API_KEY。"
    )


def is_configured() -> bool:
    """Return configuration presence without exposing the secret value."""
    try:
        return bool(_get_api_key())
    except EnvironmentError:
        return False


def _get_client() -> genai.Client:
    return genai.Client(api_key=_get_api_key())


def _parse_response(response: Any) -> dict[str, Any]:
    text = (getattr(response, "text", "") or "").strip()
    if not text:
        raise RuntimeError("Gemini 回傳空白內容")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini 回傳不是有效 JSON") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Gemini 回傳格式必須是 JSON 物件")

    expected = {"is_food", "food_summary", "calories", "protein"}
    missing = expected - set(data)
    if missing:
        raise RuntimeError(f"Gemini 回傳缺少欄位: {sorted(missing)}")
    if not isinstance(data["is_food"], bool):
        raise RuntimeError("Gemini 回傳的 is_food 必須是布林值")
    if not isinstance(data["food_summary"], str) or not data["food_summary"].strip():
        raise RuntimeError("Gemini 回傳的食物摘要不可為空")

    data["food_summary"] = data["food_summary"].strip()
    for key in ("calories", "protein"):
        value = data[key]
        if isinstance(value, bool):
            raise RuntimeError(f"Gemini 回傳的 {key} 不是有效數字")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Gemini 回傳的 {key} 不是有效數字") from exc
        if not math.isfinite(number) or number < 0:
            raise RuntimeError(f"Gemini 回傳的 {key} 必須是非負有限數字")
        data[key] = number

    if data["is_food"] and data["calories"] == 0 and data["protein"] == 0:
        raise RuntimeError("Gemini 未提供可用的營養數值")
    return {key: data[key] for key in ("is_food", "food_summary", "calories", "protein")}


def _generate(parts: list[Any]) -> dict[str, Any]:
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=parts,
            config=CONFIG,
        )
    except errors.APIError as exc:
        raise RuntimeError("Gemini 服務目前無法使用，請稍後再試") from exc
    except Exception as exc:
        raise RuntimeError("Gemini 服務連線失敗，請稍後再試") from exc
    return _parse_response(response)


def analyze_image(image: Image.Image) -> dict[str, Any]:
    """分析 Pillow Image 並回傳嚴格驗證的食物營養資料。"""
    if image.mode != "RGB":
        image = image.convert("RGB")
    return _generate([image, "請分析這張照片，並依照指定 JSON schema 回傳結果。"])
