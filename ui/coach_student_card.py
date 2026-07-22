"""Clickable coach overview card implemented with Streamlit Components v2."""

from __future__ import annotations

from collections.abc import Mapping
import math
from typing import Any

import streamlit as st


_CARD_HTML = """
<button class="coach-student-card" type="button" aria-expanded="false">
  <span class="coach-student-card__top">
    <span class="coach-student-card__avatar" aria-hidden="true"></span>
    <span class="coach-student-card__name"></span>
    <span class="coach-student-card__training"></span>
    <span class="coach-student-card__chevron" aria-hidden="true">⌄</span>
  </span>
  <span class="coach-student-card__nutrients"></span>
</button>
"""


_CARD_CSS = """
:host {
  display: block;
  width: 100%;
  font-family: system-ui, -apple-system, "Noto Sans TC", sans-serif;
}

.coach-student-card {
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  width: 100%;
  gap: 16px;
  padding: 16px;
  color: #1f2937;
  text-align: left;
  background: #ffffff;
  border: 1px solid rgba(229, 231, 235, 0.86);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: border-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
}

.coach-student-card:hover {
  border-color: rgba(132, 204, 214, 0.72);
  box-shadow: 0 7px 22px rgba(74, 119, 126, 0.13);
}

.coach-student-card:active {
  transform: scale(0.995);
}

.coach-student-card:focus-visible {
  outline: 3px solid rgba(111, 189, 201, 0.34);
  outline-offset: 2px;
}

.coach-student-card[aria-expanded="true"] {
  border-color: rgba(132, 204, 214, 0.82);
  border-bottom-right-radius: 10px;
  border-bottom-left-radius: 10px;
  box-shadow: 0 8px 24px rgba(74, 119, 126, 0.14);
}

.coach-student-card__top {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 12px;
}

.coach-student-card__avatar {
  display: grid;
  flex: 0 0 56px;
  width: 56px;
  height: 56px;
  place-items: center;
  margin-right: 8px;
  color: #315f67;
  background: #bbe8ee;
  border-radius: 50%;
  font-size: 22px;
  font-weight: 600;
}

.coach-student-card__name {
  min-width: 0;
  overflow: hidden;
  font-size: 18px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coach-student-card__training {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  margin-left: auto;
  padding: 4px 10px;
  color: #16a34a;
  background: #dcfce7;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.coach-student-card__training.not-done {
  color: #9ca3af;
  background: #f3f4f6;
}

.coach-student-card__chevron {
  flex: 0 0 auto;
  color: #809097;
  font-size: 22px;
  line-height: 1;
  transform: translateY(-2px);
  transition: transform 140ms ease;
}

.coach-student-card[aria-expanded="true"] .coach-student-card__chevron {
  transform: rotate(180deg) translateY(1px);
}

.coach-student-card__nutrients {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  width: 100%;
  gap: 18px;
  padding: 4px 0 2px;
}

.coach-nutrient {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 7px;
}

.coach-nutrient__label {
  overflow: hidden;
  color: #4b5563;
  font-size: 14px;
  font-weight: 550;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coach-nutrient__track {
  width: 100%;
  height: 5px;
  overflow: hidden;
  background: #e9ecef;
  border-radius: 999px;
}

.coach-nutrient__track > span {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.coach-nutrient__value {
  display: block;
  width: 100%;
  overflow: hidden;
  color: #7d8795;
  font-size: 17px;
  font-variant-numeric: tabular-nums;
  font-weight: 550;
  letter-spacing: -0.01em;
  line-height: 1.2;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 480px) {
  .coach-student-card {
    gap: 12px;
    padding: 14px 12px;
  }

  .coach-student-card__avatar {
    flex-basis: 48px;
    width: 48px;
    height: 48px;
    margin-right: 0;
    font-size: 19px;
  }

  .coach-student-card__name {
    font-size: 16px;
  }

  .coach-student-card__training {
    padding: 4px 7px;
    font-size: 10px;
  }

  .coach-student-card__chevron {
    font-size: 19px;
  }

  .coach-student-card__nutrients {
    gap: 6px;
  }

  .coach-nutrient {
    gap: 6px;
  }

  .coach-nutrient__label {
    font-size: 13px;
  }

  .coach-nutrient__value {
    font-size: 15px;
  }
}
"""


_CARD_JS = """
export default function(component) {
  const { parentElement, data, setTriggerValue } = component
  const card = parentElement.querySelector(".coach-student-card")
  if (!card) return

  const avatar = card.querySelector(".coach-student-card__avatar")
  const name = card.querySelector(".coach-student-card__name")
  const training = card.querySelector(".coach-student-card__training")
  const nutrients = card.querySelector(".coach-student-card__nutrients")
  if (!avatar || !name || !training || !nutrients) return

  const expanded = Boolean(data?.expanded)
  card.setAttribute("aria-expanded", String(expanded))
  card.setAttribute("aria-label", `${data?.name ?? "學員"}，${expanded ? "收合" : "展開"}目標編輯`)
  avatar.textContent = data?.initial ?? "?"
  name.textContent = data?.name ?? "學員"
  training.textContent = data?.has_training ? "已訓練" : "未訓練"
  training.classList.toggle("not-done", !data?.has_training)

  nutrients.replaceChildren()
  for (const nutrient of data?.nutrients ?? []) {
    const wrapper = document.createElement("span")
    wrapper.className = "coach-nutrient"

    const label = document.createElement("span")
    label.className = "coach-nutrient__label"
    label.textContent = nutrient.label

    const track = document.createElement("span")
    track.className = "coach-nutrient__track"
    track.setAttribute("role", "progressbar")
    track.setAttribute("aria-label", nutrient.label)
    track.setAttribute("aria-valuemin", "0")
    track.setAttribute("aria-valuemax", "100")
    track.setAttribute("aria-valuenow", String(Math.round(nutrient.percentage)))
    const fill = document.createElement("span")
    fill.style.width = `${nutrient.percentage}%`
    fill.style.background = nutrient.color
    track.appendChild(fill)

    const value = document.createElement("span")
    value.className = "coach-nutrient__value"
    value.textContent = nutrient.value_text
    wrapper.append(label, track, value)
    nutrients.appendChild(wrapper)
  }

  card.onclick = () => setTriggerValue("toggle", data?.student_id ?? "")
}
"""


_COACH_STUDENT_CARD = st.components.v2.component(
    "coach_student_status_card",
    html=_CARD_HTML,
    css=_CARD_CSS,
    js=_CARD_JS,
)


def _positive_number(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) and number > 0 else 0.0


def _format_number(value: float) -> str:
    return f"{int(round(value)):,}"


def coach_student_card(
    *,
    student_id: str,
    name: str,
    has_training: bool,
    totals: Mapping[str, Any],
    goals: Mapping[str, Any],
    expanded: bool,
    key: str,
) -> bool:
    """Render one accessible status card and report a one-shot toggle event."""
    specs = (
        ("卡路里", "calories", "calorie", "kcal", "#ff6068"),
        ("水", "water", "water", "ml", "#90cbfb"),
        ("蛋白質", "protein", "protein", "g", "#bbf250"),
    )
    nutrients = []
    for label, actual_key, goal_key, unit, color in specs:
        actual = _positive_number(totals.get(actual_key))
        goal = _positive_number(goals.get(goal_key))
        percentage = min(actual / goal * 100, 100) if goal else 0.0
        goal_text = _format_number(goal) if goal else "—"
        nutrients.append(
            {
                "label": label,
                "percentage": percentage,
                "color": color,
                "value_text": f"{_format_number(actual)} / {goal_text} {unit}",
            }
        )

    result = _COACH_STUDENT_CARD(
        key=key,
        data={
            "student_id": student_id,
            "name": str(name or "學員"),
            "initial": str(name or "?")[:1],
            "has_training": bool(has_training),
            "nutrients": nutrients,
            "expanded": bool(expanded),
        },
        on_toggle_change=lambda: None,
        width="stretch",
        height="content",
    )
    toggle = result.get("toggle") if isinstance(result, Mapping) else getattr(result, "toggle", None)
    return str(toggle or "") == str(student_id)


__all__ = ["coach_student_card"]
