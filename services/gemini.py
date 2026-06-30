"""Gemini 2.5 Flash \u71df\u990a\u8b58\u5225\u670d\u52d9\u3002

\u8b58\u5225\u7d50\u679c\u5305\u542b\u4e94\u500b\u6b04\u4f4d\uff1afood_summary / calories / protein / carb / fat
"""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import errors, types
from PIL import Image


MODEL_NAME = "gemini-2.5-flash"
ENV_VAR = "gemini_api_key"  # Streamlit secrets key (\u5c0d\u61c9\u4f4e\u9ad8\u5b57\u5141\u8a31, .lower())

SYSTEM_PROMPT = """\u4f60\u662f\u4e00\u4f4d\u5c08\u696d\u7684\u71df\u990a\u5e2b\u3002\u8acb\u56b4\u683c\u5206\u6790\u4f7f\u7528\u8005\u63d0\u4f9b\u7684\u300c\u98df\u7269\u7167\u7247\u300d\u6216\u300c\u6587\u5b57\u63cf\u8ff0\u300d\uff0c\u4f30\u7b97\u9019\u4e00\u6b63\u4efd / \u9020\u98df\u7269\u7684\u300c\u6574\u9ad4\u300d\u71df\u990a\u7e3d\u548c\uff0c\u4e0d\u8981\u5148\u4f30\u55ae\u4f4d\u518d\u8a08\u7b97\u3002

\u4f30\u7b97\u5169\u9805\u4ee5\u5916\u6642\uff0c\u8acb\u4ee5 0 \u586b\u4f4d\uff1a
1. \u300c\u91cd\u91cf\u300d\uff1a\u82e5\u7121\u6cd5\u4f30\u7b97\uff0c\u4f7f\u7528\u4e2d\u5e38\u898b\u4f86\u5dee\u4e0d\u591a\u7684\u53c3\u8003\u91cd\u91cf\uff1b\u82e5\u9805\u76ee\u662f\u300c\u98f2\u6c34\u300d\u985e\u578b\uff0c\u8acb\u4f30\u7b97\u300c\u98f2\u7528\u91cf\u300d\u672c\u4efb\u52d9\u4e0d\u9700\u8981\u4f30\u7b97\u98f2\u6c34\u91cf\uff0c\u98f2\u6c34\u91cf\u7531\u4f7f\u7528\u8005\u53e6\u884c\u586b\u5165
2. \u300c\u98f2\u6c34\u91cf\u300d\uff1a\u82e5\u7167\u7247\u4e2d\u7121\u660e\u78ba\u98f2\u6599\u8b49\u64da\uff0c\u8acb\u56de\u50b3 0\uff1b\u53ea\u6709\u80fd\u78ba\u5b9a\u8b58\u5225\u51fa\u300c\u6c34\u3001\u8336\u3001\u53ef\u6a02\u3001\u5496\u5561\u300d\u7b49\u98f2\u6599\u624d\u586b\u5165\u8a72\u985e\u4f30\u7b97\u503c\u3002

\u8acb\u56b4\u683c\u9075\u5b88\u4ee5\u4e0b JSON \u683c\u5f0f\u56de\u50b3\uff0c\u4e0d\u8981\u5305\u542b\u4efb\u4f55 markdown \u6a19\u7c64\uff08\u5982 ```json\uff09\u3001\u4e0d\u8981\u5305\u542b\u984d\u5916\u7684\u89e3\u91cb\u6587\u5b57\u6216\u7a7a\u683c\uff1a
{
  \"food_summary\": \"\u6e05\u6670\u7684\u98df\u7269\u6458\u8981\uff08\u4f8b\u5982\uff1a\u4e00\u500b\u4fbf\u7576\u542b\u6eff\u9eb5\u9eb5\u3001\u9d3b\u8089\u3001\u4e09\u5f0f\u9752\u83dc\uff09\",
  \"calories\": 0,
  \"protein\": 0,
  \"carb\": 0,
  \"fat\": 0,
}"""

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
    # 1) Streamlit secrets (\u90e8\u7f72\u4e0a\u7dda\u6642)
    try:
        import streamlit as st

        if hasattr(st, "secrets") and ENV_VAR in st.secrets:
            return str(st.secrets[ENV_VAR])
    except Exception:
        pass
    # 2) \u74b0\u5883\u8b8a\u6578 (\u672c\u6a5f\u958b\u767c / CLI \u8d70 gemini_nutrition.py)
    import os

    val = os.environ.get("GEMINI_API_KEY")
    if val:
        return val
    raise EnvironmentError(
        "\u627e\u4e0d\u5230 Gemini API Key\u3002\u8acb\u5728 .streamlit/secrets.toml \u8a2d\u5b9a "
        "GEMINI_API_KEY \u6216\u8005\u8a2d\u5b9a\u74b0\u5883\u8b8a\u6578 GEMINI_API_KEY\u3002"
    )


def _get_client() -> genai.Client:
    return genai.Client(api_key=_get_api_key())


def _parse_response(response: Any) -> dict[str, Any]:
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini \u56de\u50b3\u7a7a\u5167\u5bb9")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini \u56de\u50b3\u4e0d\u662f\u6709\u6548 JSON: {text!r}") from exc
    expected = {"food_summary", "calories", "protein", "carb", "fat"}
    missing = expected - set(data.keys())
    if missing:
        raise RuntimeError(f"Gemini \u56de\u50b3\u7f3a\u5c11\u6b04\u4f4d: {sorted(missing)}")
    # \u8b8a\u578b\u5b89\u5168\uff1a\u6578\u503c\u8b8a\u70ba float\uff0c\u4efb\u4f55\u7121\u6cd5\u8b6f\u8b80\u7684\u503c\u4ee5 0 \u4ee3\u66ff
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
        raise RuntimeError(f"Gemini API \u547c\u53eb\u5931\u6557: {exc}") from exc
    return _parse_response(response)


def analyze_image(image: Image.Image) -> dict[str, Any]:
    """\u63a5\u53d7 Pillow Image \u4e26\u8fd4\u56de\u7d50\u69cb\u5316\u71df\u990a\u8cc7\u8a0a\u3002"""
    parts: list[Any] = [image, "\u8acb\u5206\u6790\u9019\u5f35\u98df\u7269\u7167\u7247\u3002"]
    return _generate(parts)


def analyze_text(description: str) -> dict[str, Any]:
    """\u63a5\u53d7\u7d14\u6587\u5b57\u4e26\u8fd4\u56de\u7d50\u69cb\u5316\u71df\u990a\u8cc7\u8a0a\u3002"""
    if not description or not description.strip():
        raise ValueError("\u63cf\u8ff0\u4e0d\u53ef\u4ee5\u662f\u7a7a\u5b57\u4e32")
    parts: list[Any] = [description.strip()]
    return _generate(parts)
