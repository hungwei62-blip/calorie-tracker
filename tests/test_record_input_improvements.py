from __future__ import annotations

import inspect

from pages import student as student_pages


def test_manual_nutrition_inputs_are_blank_integer_widgets():
    source = inspect.getsource(student_pages._render_manual_food_input)

    assert 'min_value=0, value=None, step=10' in source
    assert 'min_value=0, value=None, step=1' in source
    assert "calories or 0" in source
    assert "protein or 0" in source
    assert "manual_food_form_version" in source


def test_training_inputs_keep_fields_without_example_placeholders():
    module_source = inspect.getsource(student_pages)

    assert "st.text_input(" in module_source
    training_source = module_source.split(
        "def _render_training_records()", maxsplit=1
    )[1].split("def _render_weight_records()", maxsplit=1)[0]
    assert "placeholder=" not in training_source
    assert "例如：深蹲" not in module_source
    assert "跑步機 20 分鐘" not in module_source


def test_record_success_uses_one_time_cross_rerun_flash():
    module_source = inspect.getsource(student_pages)

    assert '"message": "紀錄完成"' in module_source
    assert 'st.session_state.pop("daily_record_flash", None)' in module_source
    assert '_set_record_success("食物")' in module_source
    assert '_set_record_success("飲水")' in module_source
    assert '_set_record_success("訓練")' in module_source
