"""Authorized application operations above the raw Sheets repository."""

from __future__ import annotations

from typing import Any

from services import auth, sheets
from services.security import AuthContext, log_event, new_request_id


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


def request_password_reset(username: str) -> None:
    """Create a reset request when eligible without revealing account existence."""
    rows = sheets.get_users_rows()
    # Always touch the same request source before account lookup so valid and
    # unknown usernames follow the same external read path.
    sheets.get_password_reset_requests("pending")
    user = auth.find_user(rows, username)
    if user is None or str(user.get("role") or "student").strip().lower() != "student":
        log_event("password_reset.request", result="accepted")
        return
    user_id = str(user.get("user_id") or "").strip()
    created = sheets.create_password_reset_request(
        new_request_id(), user_id, auth.now_iso()
    )
    log_event(
        "password_reset.request",
        result="created" if created else "duplicate",
        target_type="student",
        target_id=user_id,
    )


def get_password_reset_requests(context: AuthContext) -> list[dict[str, Any]]:
    """Return pending requests only for students visible to this manager."""
    if not context.is_manager:
        raise PermissionDenied("只有教練或管理員可以查看密碼重設申請")
    students = sheets.get_students_for_manager(context.user_id)
    students_by_id = {
        str(student.get("user_id") or "").strip(): student for student in students
    }
    visible = []
    for request in sheets.get_password_reset_requests("pending"):
        student = students_by_id.get(str(request.get("user_id") or "").strip())
        if student is not None:
            visible.append({**request, "student": student})
    return visible


def _managed_password_reset(
    context: AuthContext, request_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not context.is_manager:
        raise PermissionDenied("只有教練或管理員可以處理密碼重設申請")
    request = next(
        (
            row
            for row in sheets.get_password_reset_requests("pending")
            if str(row.get("request_id") or "").strip() == str(request_id or "").strip()
        ),
        None,
    )
    if request is None:
        raise LookupError("找不到待處理的密碼重設申請")
    student = require_managed_student(context, str(request.get("user_id") or ""))
    return request, student


def approve_password_reset(context: AuthContext, request_id: str) -> str:
    request, student = _managed_password_reset(context, request_id)
    user_id = str(student.get("user_id") or "").strip()
    temporary_password = auth.make_temporary_password()
    if not sheets.approve_password_reset_request(
        str(request.get("request_id") or ""),
        user_id,
        auth.hash_password(temporary_password),
        resolved_at=auth.now_iso(),
        resolved_by=context.user_id,
    ):
        raise RuntimeError("密碼重設申請狀態已變更")
    log_event(
        "password_reset.approve",
        result="success",
        actor_id=context.user_id,
        actor_role=context.role,
        target_type="student",
        target_id=user_id,
    )
    return temporary_password


def reject_password_reset(context: AuthContext, request_id: str) -> bool:
    request, student = _managed_password_reset(context, request_id)
    resolved = sheets.resolve_password_reset_request(
        str(request.get("request_id") or ""),
        status="rejected",
        resolved_at=auth.now_iso(),
        resolved_by=context.user_id,
    )
    log_event(
        "password_reset.reject",
        result="success" if resolved else "not_found",
        actor_id=context.user_id,
        actor_role=context.role,
        target_type="student",
        target_id=str(student.get("user_id") or ""),
    )
    return resolved


def change_own_password(
    context: AuthContext, new_password: str
) -> bool:
    if len(new_password or "") < 8:
        raise ValueError("新密碼至少需要 8 個字元")
    updated = sheets.update_user_password(
        context.user_id,
        auth.hash_password(new_password),
        must_change_password=False,
    )
    log_event(
        "password.change",
        result="success" if updated else "not_found",
        actor_id=context.user_id,
        actor_role=context.role,
        target_type="user",
        target_id=context.user_id,
    )
    return updated


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
