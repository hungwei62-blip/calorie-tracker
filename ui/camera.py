"""Inline Streamlit component for reliable multi-camera food capture."""

from __future__ import annotations

import base64
import binascii
from typing import Any

import streamlit as st


_CAMERA_HTML = """
<div class="food-camera" aria-label="食物拍照">
  <div class="food-camera__toolbar">
    <button class="food-camera__switch" type="button" disabled
            title="正在偵測可用鏡頭">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M20 5h-3.2l-1.2-1.3A2 2 0 0 0 14.1 3H9.9a2 2 0 0 0-1.5.7L7.2 5H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2Z"/>
        <path d="m16.5 10 2 2-2 2M7.5 14l-2-2 2-2M6 12h12"/>
      </svg>
      <span>切換前後鏡頭</span>
    </button>
  </div>
  <div class="food-camera__viewport">
    <video autoplay muted playsinline></video>
    <img alt="已拍攝的食物照片" hidden />
  </div>
  <p class="food-camera__status" role="status">正在啟動相機…</p>
  <div class="food-camera__actions">
    <button class="food-camera__capture" type="button" disabled>拍攝照片</button>
    <button class="food-camera__retake" type="button" hidden>重新拍攝</button>
  </div>
  <canvas hidden></canvas>
</div>
"""


_CAMERA_CSS = """
:host {
  display: block;
  width: 100%;
  color: var(--st-text-color, #2f3e46);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.food-camera {
  box-sizing: border-box;
  width: 100%;
}

.food-camera__toolbar {
  display: flex;
  justify-content: flex-end;
  min-height: 42px;
  margin-bottom: 8px;
}

button {
  min-height: 40px;
  border: 1px solid #d8b8aa;
  border-radius: 12px;
  background: #f6e8de;
  color: #b88470;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: background 120ms ease, border-color 120ms ease, transform 80ms ease;
}

button:hover:not(:disabled) {
  border-color: #c99a86;
  background: #f0d9ca;
}

button:active:not(:disabled) {
  background: #ead0c0;
  transform: translateY(1px);
}

button:focus-visible {
  outline: 3px solid rgba(184, 132, 112, 0.30);
  outline-offset: 2px;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.food-camera__switch {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 8px 12px;
}

.food-camera__switch svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.food-camera__viewport {
  position: relative;
  overflow: hidden;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #eeeae6;
  border: 1px solid rgba(120, 120, 115, 0.14);
  border-radius: 16px;
}

.food-camera__viewport video,
.food-camera__viewport img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.food-camera__status {
  min-height: 20px;
  margin: 7px 2px;
  color: #777773;
  font-size: 13px;
  line-height: 1.4;
}

.food-camera__status.is-error {
  color: #b85c5c;
}

.food-camera__actions button {
  width: 100%;
  padding: 9px 14px;
}
"""


_CAMERA_JS = """
const instances = new WeakMap()

function stopStream(state) {
  if (state.stream) {
    state.stream.getTracks().forEach(track => track.stop())
    state.stream = null
  }
  state.video.srcObject = null
}

function setStatus(state, message, isError = false) {
  state.status.textContent = message
  state.status.classList.toggle("is-error", isError)
}

function showCaptured(state, dataUrl) {
  state.captured = dataUrl
  state.preview.src = dataUrl
  state.preview.hidden = false
  state.video.hidden = true
  state.captureButton.hidden = true
  state.retakeButton.hidden = false
  state.switchButton.disabled = true
  state.switchButton.title = "重新拍攝後即可切換鏡頭"
  setStatus(state, "照片已拍攝，可進行分析。")
  stopStream(state)
}

async function openStream(state, constraints) {
  stopStream(state)
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: false,
    video: constraints,
  })
  state.stream = stream
  state.video.srcObject = stream
  await state.video.play()
}

async function startCamera(state, requestedDeviceId = null) {
  if (!navigator.mediaDevices?.getUserMedia) {
    setStatus(state, "此瀏覽器不支援相機，請改用相簿上傳。", true)
    state.captureButton.disabled = true
    state.switchButton.disabled = true
    return
  }

  state.captureButton.disabled = true
  state.switchButton.disabled = true
  setStatus(state, "正在啟動相機…")

  const preferredFacing = state.facingMode === "user" ? "user" : "environment"
  const constraints = requestedDeviceId
    ? { deviceId: { exact: requestedDeviceId } }
    : { facingMode: { ideal: preferredFacing } }

  try {
    await openStream(state, constraints)
  } catch (error) {
    if (requestedDeviceId) {
      state.facingMode = preferredFacing === "environment" ? "user" : "environment"
      try {
        await openStream(state, { facingMode: { ideal: state.facingMode } })
      } catch (fallbackError) {
        setStatus(state, "無法開啟相機，請確認瀏覽器權限或改用相簿上傳。", true)
        return
      }
    } else {
      setStatus(state, "無法開啟相機，請確認瀏覽器權限或改用相簿上傳。", true)
      return
    }
  }

  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    state.devices = devices.filter(device => device.kind === "videoinput")
  } catch (error) {
    state.devices = []
  }

  const activeDeviceId = state.stream?.getVideoTracks()[0]?.getSettings().deviceId
  const activeIndex = state.devices.findIndex(device => device.deviceId === activeDeviceId)
  state.deviceIndex = activeIndex >= 0 ? activeIndex : 0
  state.captureButton.disabled = false
  state.switchButton.disabled = state.devices.length < 2
  state.switchButton.title = state.devices.length < 2
    ? "僅偵測到一個鏡頭"
    : "切換前後鏡頭"
  setStatus(
    state,
    state.devices.length < 2 ? "目前僅偵測到一個鏡頭。" : "相機已就緒。",
  )
}

export default function(component) {
  const { parentElement, data, setStateValue } = component
  let state = instances.get(parentElement)

  if (!state) {
    const root = parentElement.querySelector(".food-camera")
    state = {
      root,
      video: root.querySelector("video"),
      preview: root.querySelector("img"),
      canvas: root.querySelector("canvas"),
      status: root.querySelector(".food-camera__status"),
      switchButton: root.querySelector(".food-camera__switch"),
      captureButton: root.querySelector(".food-camera__capture"),
      retakeButton: root.querySelector(".food-camera__retake"),
      stream: null,
      devices: [],
      deviceIndex: 0,
      facingMode: "environment",
      captured: "",
      initialized: false,
      setStateValue,
    }
    instances.set(parentElement, state)

    state.switchButton.onclick = async () => {
      if (state.devices.length < 2) return
      state.deviceIndex = (state.deviceIndex + 1) % state.devices.length
      const nextDevice = state.devices[state.deviceIndex]
      await startCamera(state, nextDevice.deviceId)
    }

    state.captureButton.onclick = () => {
      const sourceWidth = state.video.videoWidth
      const sourceHeight = state.video.videoHeight
      if (!sourceWidth || !sourceHeight) return
      const scale = Math.min(1, 1600 / Math.max(sourceWidth, sourceHeight))
      state.canvas.width = Math.max(1, Math.round(sourceWidth * scale))
      state.canvas.height = Math.max(1, Math.round(sourceHeight * scale))
      const context = state.canvas.getContext("2d")
      context.drawImage(state.video, 0, 0, state.canvas.width, state.canvas.height)
      const dataUrl = state.canvas.toDataURL("image/jpeg", 0.9)
      showCaptured(state, dataUrl)
      state.setStateValue("image_data_url", dataUrl)
    }

    state.retakeButton.onclick = async () => {
      state.setStateValue("image_data_url", "")
      state.captured = ""
      state.preview.removeAttribute("src")
      state.preview.hidden = true
      state.video.hidden = false
      state.captureButton.hidden = false
      state.retakeButton.hidden = true
      await startCamera(state)
    }
  }

  state.setStateValue = setStateValue
  const nextCaptured = data?.image_data_url || ""
  if (nextCaptured && nextCaptured !== state.captured) {
    showCaptured(state, nextCaptured)
  } else if (!nextCaptured && !state.initialized) {
    state.initialized = true
    startCamera(state)
  }

  return () => {
    stopStream(state)
    instances.delete(parentElement)
  }
}
"""


_FOOD_CAMERA = st.components.v2.component(
    "food_camera_capture",
    html=_CAMERA_HTML,
    css=_CAMERA_CSS,
    js=_CAMERA_JS,
)


def _component_state_value(state: Any, key: str, default: str = "") -> str:
    if isinstance(state, dict):
        value = state.get(key, default)
    else:
        value = getattr(state, key, default)
    return value if isinstance(value, str) else default


def decode_camera_data_url(data_url: object) -> bytes | None:
    """Decode a JPEG data URL emitted by the camera component."""
    if not isinstance(data_url, str):
        return None
    prefix = "data:image/jpeg;base64,"
    if not data_url.startswith(prefix):
        return None
    try:
        image_bytes = base64.b64decode(data_url[len(prefix):], validate=True)
    except (binascii.Error, ValueError):
        return None
    return image_bytes or None


def camera_capture(*, key: str) -> bytes | None:
    """Render the camera and return the current captured JPEG, if present."""
    component_state = st.session_state.get(key, {})
    image_data_url = _component_state_value(component_state, "image_data_url")
    result = _FOOD_CAMERA(
        key=key,
        data={"image_data_url": image_data_url},
        default={"image_data_url": ""},
        on_image_data_url_change=lambda: None,
        width="stretch",
        height="content",
    )
    return decode_camera_data_url(
        _component_state_value(result, "image_data_url", image_data_url)
    )
