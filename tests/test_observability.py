from __future__ import annotations

import json
import logging

from services.observability import JsonFormatter


def test_json_formatter_promotes_structured_event_fields():
    record = logging.LogRecord(
        "project_prime",
        logging.INFO,
        __file__,
        1,
        "security_event",
        (),
        None,
    )
    record.event = {
        "request_id": "req-1",
        "action": "test.action",
        "actor_id": "actor-1",
        "target_id": "target-1",
        "duration_ms": 12.5,
        "result": "success",
    }

    payload = json.loads(JsonFormatter().format(record))

    assert payload["request_id"] == "req-1"
    assert payload["action"] == "test.action"
    assert payload["duration_ms"] == 12.5
    assert payload["result"] == "success"
