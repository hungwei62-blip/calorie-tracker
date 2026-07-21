from __future__ import annotations

import base64

from ui.camera import (
    _CAMERA_CSS,
    _CAMERA_HTML,
    _CAMERA_JS,
    decode_camera_data_url,
)


def test_camera_decodes_only_valid_jpeg_data_urls():
    payload = b"jpeg-bytes"
    encoded = base64.b64encode(payload).decode("ascii")

    assert decode_camera_data_url(f"data:image/jpeg;base64,{encoded}") == payload
    assert decode_camera_data_url("data:image/png;base64," + encoded) is None
    assert decode_camera_data_url("data:image/jpeg;base64,invalid!") is None
    assert decode_camera_data_url(None) is None


def test_camera_uses_ccv2_state_and_browser_media_devices():
    assert "setStateValue(\"image_data_url\"" in _CAMERA_JS
    assert "navigator.mediaDevices.getUserMedia" in _CAMERA_JS
    assert "navigator.mediaDevices.enumerateDevices()" in _CAMERA_JS
    assert "deviceId: { exact: requestedDeviceId }" in _CAMERA_JS
    assert "facingMode: { ideal: preferredFacing }" in _CAMERA_JS
    assert "getTracks().forEach(track => track.stop())" in _CAMERA_JS
    assert "Streamlit.setComponentValue" not in _CAMERA_JS
    assert "window.Streamlit" not in _CAMERA_JS


def test_camera_controls_are_visible_and_isolated_from_preview():
    assert "切換前後鏡頭" in _CAMERA_HTML
    assert "拍攝照片" in _CAMERA_HTML
    assert "重新拍攝" in _CAMERA_HTML
    assert ".food-camera__toolbar" in _CAMERA_CSS
    assert "margin-bottom: 8px" in _CAMERA_CSS
    assert "background: #f6e8de" in _CAMERA_CSS.lower()
    assert "僅偵測到一個鏡頭" in _CAMERA_JS
    assert "請確認瀏覽器權限" in _CAMERA_JS
