"""Service Account JSON \u8f49 TOML \u8f49\u63db\u5de5\u5177\u3002

\u4f7f\u7528\u65b9\u6cd5\uff1a
    python tools\\json_to_toml.py <path-to-service-account.json>

\u6703\u5728\u63a7\u5236\u6aaf\u5370\u51fa\u53ef\u76f4\u63a5\u8cbc\u5165 Streamlit Cloud Secrets \u7684 [gcp] \u5340\u584a\u3002
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python json_to_toml.py <service-account.json>", file=sys.stderr)
        return 1
    src = Path(sys.argv[1])
    if not src.is_file():
        print(f"\u627e\u4e0d\u5230\u6a94\u6848: {src}", file=sys.stderr)
        return 1
    # utf-8-sig \u53ef\u5b89\u5168\u8655\u7406\u542b BOM \u7684 JSON (\u90e8\u5206\u700f\u89bd\u5668\u4e0b\u8f09\u6703\u52a0 BOM)
    try:
        data = json.loads(src.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"JSON \u89e3\u6790\u5931\u6557: {exc}", file=sys.stderr)
        return 1

    required = [
        "type",
        "project_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
        "auth_provider_x509_cert_url",
        "client_x509_cert_url",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        print(f"\u6a94\u6848\u7f3a\u5c11\u5fc5\u8981\u6b04\u4f4d: {missing}", file=sys.stderr)
        return 1

    out = []
    out.append("[gcp]")
    out.append(f'type = "{data["type"]}"')
    out.append(f'project_id = "{data["project_id"]}"')
    pk = data["private_key"]
    out.append('private_key = """' + pk + '"""')
    out.append(f'client_email = "{data["client_email"]}"')
    out.append(f'client_id = "{data["client_id"]}"')
    out.append(f'auth_uri = "{data["auth_uri"]}"')
    out.append(f'token_uri = "{data["token_uri"]}"')
    out.append(f'auth_provider_x509_cert_url = "{data["auth_provider_x509_cert_url"]}"')
    out.append(f'client_x509_cert_url = "{data["client_x509_cert_url"]}"')

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())