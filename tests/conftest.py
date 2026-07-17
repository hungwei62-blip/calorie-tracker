from __future__ import annotations

from dataclasses import dataclass

import pytest


@dataclass
class FakeCell:
    row: int
    col: int
    value: object = ""


class FakeWorksheet:
    def __init__(self, values=None):
        self.values = values or []
        self.updated_cells = []
        self.appended_rows = []
        self.deleted_rows = []

    def get_all_values(self):
        return [list(row) for row in self.values]

    def row_values(self, row):
        return list(self.values[row - 1]) if len(self.values) >= row else []

    def update_cell(self, row, col, value):
        self.updated_cells.append((row, col, value))

    def update_cells(self, cells, **_kwargs):
        self.updated_cells.extend((cell.row, cell.col, cell.value) for cell in cells)

    def append_row(self, row, **_kwargs):
        self.appended_rows.append(list(row))

    def delete_rows(self, row):
        self.deleted_rows.append(row)


@pytest.fixture
def student_row():
    return {
        "user_id": "u_20260717123045_deadbeef",
        "username": "student",
        "name": "測試學員",
        "password_hash": "hash",
        "created_at": "2026-07-17T12:30:45+08:00",
        "bmr": "1500",
        "daily_calorie_goal": "2000",
        "daily_protein_goal": "120",
        "daily_carb_goal": "220",
        "daily_fat_goal": "60",
        "daily_water_goal": "2400",
        "role": "student",
        "weekly_training_goal": "4",
        "record_mode": "full",
        "coach_id": "coach_1",
    }
