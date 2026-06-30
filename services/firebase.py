"""Firebase Storage 上傳服務。

使用機制：
- 識別服務以 Admin SDK 來設定、上傳、生成下載令牌
- 該下載令牌會補加在 PUBLIC_URL_PREFIX 之後作為公開訪問之 URL
- 若 Secrets 中不包含 Firebase 設定，會返回上傳失敗錯誤並請使用者重新上傳
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import streamlit as st


def _is_configured() -> bool:
    return "firebase" in st.secrets and all(
        k in st.secrets["firebase"] for k in ("STORAGE_BUCKET", "PUBLIC_URL_PREFIX")
    )


def upload_image(image_bytes: bytes, content_type: str, user_id: str) -> str:
    """上傳一個二進作業式檔案到 Firebase Storage，並返回可讀取的公開 URL。"""
    if not _is_configured():
        raise RuntimeError(
            "Firebase 設定不完整，請在 .streamlit/secrets.toml 中設定 [firebase]。"
        )
    try:
        import firebase_admin
        from firebase_admin import credentials, storage
    except ImportError as exc:
        raise RuntimeError("firebase-admin 尚未安裝，請 pip install firebase-admin") from exc

    bucket_name = st.secrets["firebase"]["STORAGE_BUCKET"]
    prefix = st.secrets["firebase"]["PUBLIC_URL_PREFIX"].rstrip("/")

    if not firebase_admin._apps:
        if "gcp" not in st.secrets:
            raise RuntimeError("需要 [gcp] Service Account 以來認證 Firebase")
        sa_info = {k: v for k, v in st.secrets["gcp"].items() if k != "SPREADSHEET_ID"}
        cred = credentials.Certificate(sa_info)
        firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})

    bucket = storage.bucket()
    suffix = uuid.uuid4().hex
    # 使用 timezone-aware 的 now() 取代已棄用的 utcnow()（Python 3.12+）
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    ext = (content_type.split("/")[-1] if content_type else "jpg").lower()
    object_name = f"food/{user_id}/{ts}_{suffix}.{ext}"
    blob = bucket.blob(object_name)
    blob.upload_from_string(image_bytes, content_type=content_type)
    blob.make_public()
    return f"{prefix}/{object_name}"
