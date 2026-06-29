"""Firebase Storage \u4e0a\u50b3\u670d\u52d9\u3002\n\n\u4f7f\u7528\u6a5f\u5236\uff1a\n- \u8b58\u5225\u670d\u52d9\u4ee5 Admin SDK \u4f86\u8a2d\u5b9a\u3001\u4e0a\u50b3\u3001\u751f\u6210\u4e0b\u8f09\u4ee4\u724c\n- \u8a72\u4e0b\u8f09\u4ee4\u724c\u6703\u88dc\u52a0\u5728 PUBLIC_URL_PREFIX \u4e4b\u5f8c\u4f5c\u70ba\u516c\u958b\u8a2a\u554f\u4e4b URL\u3002\n- \u82e5 Secrets \u4e2d\u4e0d\u5305\u542b Firebase \u8a2d\u5b9a\uff0c\u6703\u8fd4\u56de\u4e0a\u50b3\u5931\u6557\u932f\u8aa4\u4e26\u8b9a\u4f7f\u7528\u8005\u91cd\u65b0\u4e0a\u50b3\u3002\n"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import streamlit as st


def _is_configured() -> bool:
    return "firebase" in st.secrets and all(
        k in st.secrets["firebase"] for k in ("STORAGE_BUCKET", "PUBLIC_URL_PREFIX")
    )


def upload_image(image_bytes: bytes, content_type: str, user_id: str) -> str:
    """\u4e0a\u50b3\u4e00\u500b\u4e8c\u9032\u4f5c\u696d\u5f0f\u6a94\u6848\u5230 Firebase Storage\uff0c\u4e26\u8fd4\u56de\u53ef\u8b80\u53d6\u7684\u516c\u958b URL\u3002"""
    if not _is_configured():
        raise RuntimeError(
            "Firebase \u8a2d\u5b9a\u4e0d\u5b8c\u6574\uff0c\u8acb\u5728 .streamlit/secrets.toml \u4e2d\u8a2d\u5b9a [firebase]\u3002"
        )
    try:
        import firebase_admin
        from firebase_admin import credentials, storage
    except ImportError as exc:
        raise RuntimeError("firebase-admin \u5c1a\u672a\u5b89\u88dd\uff0c\u8acb pip install firebase-admin") from exc

    bucket_name = st.secrets["firebase"]["STORAGE_BUCKET"]
    prefix = st.secrets["firebase"]["PUBLIC_URL_PREFIX"].rstrip("/")

    if not firebase_admin._apps:
        if "gcp" not in st.secrets:
            raise RuntimeError("\u9700\u8981 [gcp] Service Account \u4ee5\u4f86\u8a8d\u8b49 Firebase")
        sa_info = {k: v for k, v in st.secrets["gcp"].items() if k != "SPREADSHEET_ID"}
        cred = credentials.Certificate(sa_info)
        firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})

    bucket = storage.bucket()
    suffix = uuid.uuid4().hex
    ts = datetime.utcnow().strftime("%Y%m%d")
    ext = (content_type.split("/")[-1] if content_type else "jpg").lower()
    object_name = f"food/{user_id}/{ts}_{suffix}.{ext}"
    blob = bucket.blob(object_name)
    blob.upload_from_string(image_bytes, content_type=content_type)
    blob.make_public()
    return f"{prefix}/{object_name}"
