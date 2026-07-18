"""Preview or explicitly initialize PROJECT PRIME worksheet schemas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services import sheets  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="檢查 PROJECT PRIME 工作表；只有 --apply 才會建立或補齊欄位"
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = sheets.initialize_worksheets(apply=args.apply)
    output = json.dumps(
        {"applied": args.apply, "worksheets": report},
        ensure_ascii=False,
        indent=2,
    )
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    return 1 if any(item["status"] == "mismatch" for item in report) else 0


if __name__ == "__main__":
    raise SystemExit(main())

