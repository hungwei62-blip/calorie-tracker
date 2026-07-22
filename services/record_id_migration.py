"""Pure audit helpers for adding stable IDs to editable record worksheets."""

from __future__ import annotations

from collections import Counter
from typing import Any


def audit_record_ids(
    values: list[list[Any]],
    *,
    legacy_headers: list[str],
    target_headers: list[str],
) -> dict[str, Any]:
    headers = [str(value) for value in (values[0] if values else [])]
    if headers not in (legacy_headers, target_headers):
        raise ValueError("工作表欄位不是可辨識的舊版或新版 schema")

    migrated = headers == target_headers
    id_index = target_headers.index("record_id")
    record_ids = [
        str(row[id_index]).strip() if migrated and len(row) > id_index else ""
        for row in values[1:]
    ]
    counts = Counter(value for value in record_ids if value)
    duplicates = sorted(value for value, count in counts.items() if count > 1)
    return {
        "rows": max(len(values) - 1, 0),
        "schema": "current" if migrated else "legacy",
        "missing_ids": sum(not value for value in record_ids),
        "duplicate_ids": duplicates,
    }
