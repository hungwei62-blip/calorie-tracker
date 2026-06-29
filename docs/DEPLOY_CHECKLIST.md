# 部署檢查清單

> 照 `docs/SETUP_GCP_FIREBASE.md` 走完所有關卡後，貼到 share.streamlit.io Secrets 區的最終內容。

## 完成後您會有 4 段 Secrets

### 1. `GEMINI_API_KEY`
- 來源：https://aistudio.google.com/app/apikey
- 值：例如 `AIza...` 或新版 Gemini 格式（`AQ...` 開頭也可）
- 警告：**舊 key 已外洩，請用新 key**

### 2. `[gcp]` 區塊
- 來源：GCP Service Account JSON 檔（從 3.4 下載）
- 取得方式：跑 `python tools\json_to_toml.py <json>\u8def\u5f91` \u8b80\u5230
- 包含 9 \u500b\u6b04\u4f4d\uff1a`type / project_id / private_key / client_email / client_id / auth_uri / token_uri / auth_provider_x509_cert_url / client_x509_cert_url`
- **注意**：`private_key` 一定要用三引號 `"""..."""` 包好

### 3. `SPREADSHEET_ID`
- 來源：Google Sheet `CalorieTracker` 網址 `/d/` 與 `/edit` 之間的字串
- 例：`1aBcDeFgHiJkLmNoPqRsTuVwXyZ`

### 4. `[firebase]` 區塊（兩行）
- `STORAGE_BUCKET`：例如 `calories-a1a96.firebasestorage.app`（新版）或 `<project-id>.appspot.com`（舊版）
- `PUBLIC_URL_PREFIX`：`https://storage.googleapis.com/<bucket>/`

---

## 完整 Secrets 範本（貼入 Streamlit Cloud）

把以下 4 段組合成**一整段 TOML** 貼進 share.streamlit.io 的 Secrets 編輯區：

```toml
GEMINI_API_KEY = "<貼上你的 key>"

[gcp]
type = "service_account"
project_id = "<貼上 project_id>"
private_key = """<貼上完整 PEM，含 \u958b\u59cb\u8207\u7d50\u675f\uff0c\n \u4fdd\u7559\u539f\u8c8c>"""
client_email = "<貼上 client_email>"
client_id = "<貼上 client_id>"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "<貼上 client_x509_cert_url>"

SPREADSHEET_ID = "<貼上你的 Sheet ID>"

[firebase]
STORAGE_BUCKET = "<貼上 bucket 名稱>"
PUBLIC_URL_PREFIX = "https://storage.googleapis.com/<bucket>/"
```

---

## 部署前最後檢查

- [ ] `GEMINI_API_KEY` 是**新申請的**（舊 key 不要再用）
- [ ] `private_key` 用三引號包好
- [ ] `SPREADSHEET_ID` 沒夾帶 `/d/` 或 `/edit`
- [ ] `STORAGE_BUCKET` 不含 `gs://` 前綴
- [ ] `PUBLIC_URL_PREFIX` 結尾有 `/`
- [ ] 整段 TOML 中**沒有**真正的 `REPLACE_ME` 字樣殘留

---

## 部署步驟（share.streamlit.io）

1. https://share.streamlit.io/ → 右上 Sign in → Continue with GitHub → 授權
2. 工作台 → New app
3. 填欄位：
   - **Repository**：`hungwei62-blip/calorie-tracker`
   - **Branch**：`main`
   - **Main file path**：`app.py`
   - **App URL**：`worldgymzoe-caloriesoe`（您選的）
4. Advanced settings → Secrets 貼上整段 TOML
5. 點 **Deploy**
6. 等 2–5 分鐘
7. 取得 `https://worldgymzoe-caloriesoe.streamlit.app`

---

## 部署後第一個測試

1. 開啟 `https://worldgymzoe-caloriesoe.streamlit.app`
2. 應該看到登入 / 註冊頁（不應出現 `KeyError`、`gcp not found` 之類）
3. 點註冊 tab → 輸入帳號密碼 → 自動登入
4. 進「記一餐」→ 選「午餐」→ 拍照或上傳照片 → 送出分析
5. 看到 Gemini 回傳 5 欄 JSON → 改份數 → 確認送出
6. 進「今日」→ 看到累積數字與進度條
7. 進「歷史」→ 看到本週統計（達成/未達/超標標籤）
8. 開 Firebase Storage → Files 看到剛剛上傳的照片
9. 開 Google Sheet → Records 工作表看到新 row

---

## 卡住了？

- **首頁 500 / ImportError** → 看 Streamlit Cloud log，把錯誤訊息貼給我
- **登入失敗** → 確認 Sheet 已被 SA 邀請為 Editor
- **拍照上傳 403** → 確認 Storage Rules 已 Publish、bucket 名稱正確
- **Gemini 503** → 過幾秒重試（API 偶爾過載）