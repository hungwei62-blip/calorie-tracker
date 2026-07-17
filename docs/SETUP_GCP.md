# Google Cloud、Sheets 與 Gemini 設定

## 1. 建立 Google Sheet

建立試算表並記下網址 `/d/` 與 `/edit` 間的 `SPREADSHEET_ID`。程式會建立或補齊 `Users`、`Records`、`Weight`、`Training`、`Notes` 工作表。

## 2. 建立 Service Account

1. 在 GCP 啟用 Google Sheets API 與 Google Drive API。
2. 建立 Service Account 並下載 JSON 金鑰。
3. 將試算表分享給 JSON 內的 `client_email`，權限設為 Editor。
4. 執行 `python tools/json_to_toml.py <JSON 路徑>` 產生 `[gcp]` 設定。

## 3. 建立主教練

在 `Users` 加入一個 `role` 為 `coach` 的帳號，將其 `user_id` 設為 `PRIMARY_COACH_ID`。所有新註冊及首次遷移的既有學員都會歸屬該教練。

## 4. Secrets 範例

```toml
GEMINI_API_KEY = "<Gemini API key>"
PRIMARY_COACH_ID = "<Users 中的教練 user_id>"
SPREADSHEET_ID = "<Google Sheet ID>"

[gcp]
type = "service_account"
project_id = "..."
private_key = """-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
"""
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

餐點照片不永久保存，因此不需要 Firebase Storage 或 Storage Rules。
