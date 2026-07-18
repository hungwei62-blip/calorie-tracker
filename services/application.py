"""Authorized application operations above the raw Sheets repository."""

from __future__ import annotations

from typing import Any

from services import sheets
from services.security import AuthContext, log_event


class PermissionDenied(PermissionError):
    pass


def require_self(context: AuthContext, user_id: str) -> None:
    if context.role != "student" or context.user_id != str(user_id or "").strip():
        raise PermissionDenied("沒有權限操作此學員資料")


def require_managed_student(context: AuthContext, user_id: str) -> dict[str, Any]:
    if not context.is_manager:
        raise PermissionDenied("只有教練或管理員可以操作學員資料")
    student = sheets.get_student_for_manager(user_id, context.user_id)
    if student is None:
        log_event(
            "authorization.denied",
            result="denied",
            actor_id=context.user_id,
            actor_role=context.role,
            target_type="student",
            target_id=user_id,
        )
        raise PermissionDenied("沒有權限操作此學員資料")
    return student


def get_students(context: AuthContext) -> list[dict[str, Any]]:
    if not context.is_manager:
        raise PermissionDenied("只有教練或管理員可以查看學員")
    return sheets.get_students_for_manager(context.user_id)


def get_student(context: AuthContext, user_id: str) -> dict[str, Any] | None:
    try:
        return require_managed_student(context, user_id)
    except PermissionDenied:
        return None


def update_student_goals(
    context: AuthContext, user_id: str, goals: dict[str, float]
) -> bool:
    if context.role == "student":
        require_self(context, user_id)
    else:
        require_managed_student(context, user_id)
    updated = sheets.update_user_goals(user_id, goals)
    log_event(
        "student.goals.update",
        result="success" if updated else "not_found",
        actor_id=context.user_id,
        actor_role=context.role,
        target_type="student",
        target_id=user_id,
        metadata={"fields": sorted(goals)},
    )
    return updated


def update_student_bmr(context: AuthContext, user_id: str, bmr: float) -> bool:
    require_self(context, user_id)
    return sheets.update_user_bmr(user_id, bmr)


def append_student_record(context: AuthContext, user_id: str, **payload: Any) -> None:
    require_self(context, user_id)
    sheets.append_record(user_id=user_id, **payload)


def append_student_weight(
    context: AuthContext, user_id: str, timestamp: str, weight_kg: float
) -> None:
    require_self(context, user_id)
    sheets.append_weight(timestamp, user_id, weight_kg)


def update_student_training(context: AuthContext, user_id: str, **payload: Any) -> bool:
    require_self(context, user_id)
    return sheets.update_training(user_id=user_id, **payload)


def import_student_records(
    context: AuthContext, user_id: str, **payload: Any
) -> dict[str, Any]:
    require_managed_student(context, user_id)
    result = sheets.import_records_from_excel(user_id=user_id, **payload)
    log_event(
        "student.records.import",
        result="success" if not result.get("errors") else "partial",
        actor_id=context.user_id,
        actor_role=context.role,
        target_type="student",
        target_id=user_id,
        metadata={
            "overwrite": bool(payload.get("overwrite_duplicates")),
            "imported": result.get("imported", 0),
            "overwritten": result.get("overwritten", 0),
            "skipped": result.get("skipped", 0),
        },
    )
    return result
