"""Gemini 1.5 Flash 營養結構化識別示範腳本。

依據《專案開發需求書》第 5 章的 System Prompt，
使用 google-genai SDK 的 response_schema 強制以 JSON 格式回傳以下架構：
    food_summary, calories, protein, water_ml
"""

from __future__ import annotations

import os
import sys
from typing import Any

from google import genai
from google.genai import errors, types
from PIL import Image


MODEL_NAME = "gemini-2.5-flash"
ENV_VAR = "GEMINI_API_KEY"

SYSTEM_PROMPT = """你是一位專業的營養師。請嚴格分析使用者提供的「食物照片」或「文字描述」，估算其中包含的食物品項、總熱量（大卡）、蛋白質（克）以及飲水量（毫升）。

請嚴格遵守以下 JSON 格式回傳，不要包含任何 markdown 標籤（如 ```json）、不要包含額外的解釋文字或空格：
{
  "food_summary": "清晰的食物摘要（例如：大麥克漢堡與中杯可樂）",
  "calories": 0,
  "protein": 0,
  "water_ml": 0
}"""

# 以 Schema 強制回傳架構，搭配 response_mime_type="application/json" 讓 SDK 直接回 JSON
RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "food_summary": types.Schema(type=types.Type.STRING),
        "calories": types.Schema(type=types.Type.NUMBER),
        "protein": types.Schema(type=types.Type.NUMBER),
        "water_ml": types.Schema(type=types.Type.NUMBER),
    },
    required=["food_summary", "calories", "protein", "water_ml"],
)

CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    response_mime_type="application/json",
    response_schema=RESPONSE_SCHEMA,
    temperature=0.2,
)


def _get_client() -> genai.Client:
    api_key = os.environ.get(ENV_VAR)
    if not api_key:
        raise EnvironmentError(
            "未找到環境變數 GEMINI_API_KEY。請先在 shell 中設定，例如："
            " $env:GEMINI_API_KEY = \"你的 API Key\""
        )
    return genai.Client(api_key=api_key)


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


def _parse_response(response: Any) -> dict[str, Any]:
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini 回傳空內容")
    import json
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini 回傳不是有效 JSON: {text!r}") from exc
    expected = {"food_summary", "calories", "protein", "water_ml"}
    missing = expected - set(data.keys())
    if missing:
        raise RuntimeError(f"Gemini 回傳缺少欄位: {sorted(missing)}")
    return data


def analyze_image(image_path: str) -> dict[str, Any]:
    """將本地圖片送給 Gemini 並返回結構化營養資訊。"""
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"找不到圖片檔: {image_path}")
    img = Image.open(image_path)
    parts: list[Any] = [img, "請分析這張食物照片。"]
    return _generate(parts)


def analyze_text(description: str) -> dict[str, Any]:
    """將純文字描述送給 Gemini 並返回結構化營養資訊。"""
    if not description or not description.strip():
        raise ValueError("描述不可以是空字串")
    parts: list[Any] = [description.strip()]
    return _generate(parts)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Gemini 營養結構識別示範")
    parser.add_argument("--image", help="本地圖片路徑（設定並且有檔案時便會走圖片結構）")
    parser.add_argument("--text", help="文字描述（預設為「吃了一盤肉絲炒飯跟一顆滷蛋」）")
    args = parser.parse_args()

    if args.image:
        result = analyze_image(args.image)
    else:
        result = analyze_text(args.text or "吃了一盤肉絲炒飯跟一顆滷蛋")

    print(json.dumps(result, ensure_ascii=False, indent=2))
