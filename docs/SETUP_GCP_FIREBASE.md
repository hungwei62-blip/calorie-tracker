# GCP / Firebase / Google Sheet 設定指南

> 本指南協助您取得 share.streamlit.io 部署所需的 4 段 Secrets 設定值。
> 預估時間：15–20 分鐘。

## 事前準備
- [ ] Google 帳號
- [ ] 已申請新的 Gemini API key（**舊 key 已外洩，請重新申請**）
- [ ] 記事本或暫存區（記錄您拿到的 ID、bucket 名稱等）

---

## 關卡 1：建立 Google Sheet（3 分鐘）

### 1.1 建立新試算表
1. 開新分頁，網址列輸入：`sheets.new` → 按 Enter
2. 自動建立一個空白試算表
3. 點左上角「**未命名試算表**」 → 改名為 `CalorieTracker`

### 1.2 取得 Sheet ID
看網址列，長這樣：
```
https://docs.google.com/spreadsheets/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit#gid=0
                                              ^^^^^^^^^^^^^^^^^^^^^^
                                              這段就是 ID
```
複製 `1aBcDeFgHiJkLmNoPqRsTuVwXyZ`（從 `/d/` 到 `/edit` 之間），貼到記事本：
```
SPREADSHEET_ID = "1aBcDeFgHiJkLmNoPqRsTuVwXyZ"
```

### 1.3 不用手動建工作表
App 第一次連線時會自動建立 `Users` 與 `Records` 兩個工作表，**此處不用動**。

✅ **驗證**：開 Sheet URL 看得到新建立的試算表

---

## 關卡 2：Firebase Storage（5 分鐘）

### 2.1 建立 Firebase project
1. 開新分頁 → `https://console.firebase.google.com/`
2. 點「**Add project / 建立專案**」或「**Create a project**」
3. Project name：填 `calorie-tracker`
4. 點 **Continue**
5. 問要不要啟用 Google Analytics：**關掉**（不需勾）
6. 點 **Create project**，等 30 秒

### 2.2 啟用 Storage
1. 進到專案後，左邊選單點「**Build / 建構**」→「**Storage**」
2. 點「**Get started / 開始使用**」
3. Security rules 選「**Start in production mode / 在正式模式啟動**」
4. 選 Storage 地區：**`asia-east1` (Taiwan)** ← 對台灣延遲最低
5. 點 **Done / 完成**

### 2.3 設定 Storage Rules

1. 切到「Rules / 規則」頁籤
2. 把內容整個取代成（**限定 /food/ 路徑下公開讀寫，其餘關閉**）：
```text
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /food/{userId}/{filename} {
      allow read, write: if true;
    }
    match /{allPaths=**} {
      allow read, write: if false;
    }
  }
}
```
3. 點「**Publish / 發布**」

驗證：上方「規則測試區」可選 `/food/test/abc.jpg` + `get`/`write`，執出 Allowed。

---
### 2.4 取得 bucket 名稱
1. 切到「Files / 檔案」頁籤
2. 看上方路徑：
   - 新版：`gs://calorie-tracker-xxxxx.firebasestorage.app`
   - 舊版：`gs://calorie-tracker-xxxxx.appspot.com`
3. 複製 `calorie-tracker-xxxxx.firebasestorage.app`（不包含 `gs://`），貼到記事本：
```
STORAGE_BUCKET = "calorie-tracker-xxxxx.firebasestorage.app"
PUBLIC_URL_PREFIX = "https://storage.googleapis.com/calorie-tracker-xxxxx.firebasestorage.app/"
```

✅ **驗證**：Storage Files 頁面空白但路徑顯示 bucket 名稱

---

### 2.5 跨帳號 IAM 設定（選用，僅當 Firebase 與 GCP 屬不同帳號）

如果您的 Firebase project 與 GCP Service Account 在**不同的 Google 帳號**下，
需要在 Firebase 這邊授予 Service Account 存取 bucket 的權限。

1. 仍登入 **Firebase 帳號 A**，到 https://console.cloud.google.com/
2. 右上角專業下拉 → 切到 Firebase 對應的 GCP project
3. 搜尋 「Cloud Storage」 → 「Buckets」 → 點入 `calories-xxxxx.firebasestorage.app`
4. 上方「Permissions」頁籤 → 「Grant access」
5. **New principals** 貼上帳號 B 的 SA email：
   ```
   calorie-tracker-sa@<account-B-project-id>.iam.gserviceaccount.com
   ```
6. **Role** 選 **`Storage Object Admin`**（含讀、寫、刪除）
7. 點 **Save**

✅ **驗證**：GCP Cloud Storage 頁面看到 SA email 為 `Storage Object Admin`

---


---

## 關卡 3：GCP Service Account + 權限（10 分鐘）

### 3.1 連結 GCP 專案
1. 開新分頁 → `https://console.cloud.google.com/`
2. 右上角專案下拉 → 找 Firebase 用的那個 project（**GCP 與 Firebase 預設綁同一個**）

### 3.2 啟用 API
1. 頂部搜尋 `Google Sheets API` → 點進去 → 「**Enable / 啟用**」
2. 同樣步驟搜 `Firebase Storage API`（或 `Cloud Storage for Firebase API`）→ 啟用

### 3.3 建立 Service Account
1. 頂部搜尋 `IAM` → 點「**IAM & Admin / IAM 與管理**」
2. 左邊選「**Service Accounts / 服務帳戶**」
3. 點「**+ CREATE SERVICE ACCOUNT**」
4. Step 1：Service account name 填 `calorie-tracker-sa` → 「**Create and Continue**」
5. Step 2：選 **`Editor` / 編輯者** 角色 → 「**Continue**」
6. Step 3：略過 → 「**Done**」

### 3.4 下載 JSON 金鑰
1. 點該 SA 右邊 `⋮` → 「**Manage keys**」 → 「**Add Key**」 → 「**Create new key**」
2. 選 **JSON** → **Create**
3. 瀏覽器下載 `xxxxx-xxxxx.json` 檔，**不要推上 GitHub**

### 3.5 把 JSON 轉成 TOML
跑我們準備好的腳本：
```powershell
python tools\json_to_toml.py "C:\Users\<you>\Downloads\xxxxx-xxxxx.json"
```
它會印出可直接貼入 Secrets 的 `[gcp]` 區塊。

### 3.6 授權 Service Account 讀寫 Google Sheet
1. 開 Google Sheet `CalorieTracker`
2. 右上角「**Share / 分享**」
3. 把 JSON 內的 `client_email` 整段貼到「Add people」：
   ```
   calorie-tracker-sa@calorie-tracker-xxxxx.iam.gserviceaccount.com
   ```
4. 權限：**Editor / 編輯者**
5. **取消勾選**「Notify people」
6. 點「**Share / 分享**」

✅ **驗證**：Service Account `client_email` 出現在 Sheet 共用名單內

---

## 最終：組裝 Secrets TOML

把記事本內的值依下列格式組裝（**`private_key` 一定要用三引號**）：
```toml
GEMINI_API_KEY = "您的_Gemini_key"

[gcp]
type = "service_account"
project_id = "calorie-tracker-xxxxx"
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQ...
-----END PRIVATE KEY-----
"""
client_email = "calorie-tracker-sa@calorie-tracker-xxxxx.iam.gserviceaccount.com"
client_id = "123456789012345678901"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/calorie-tracker-sa%40calorie-tracker-xxxxx.iam.gserviceaccount.com"

SPREADSHEET_ID = "1aBcDeFgHiJkLmNoPqRsTuVwXyZ"

[firebase]
STORAGE_BUCKET = "calorie-tracker-xxxxx.appspot.com"
PUBLIC_URL_PREFIX = "https://storage.googleapis.com/calorie-tracker-xxxxx.appspot.com/"
```

---

## 卡住了嗎？

- **API 找不到 / 介面改名** → 嘗試 `console.cloud.google.com` 頂部搜尋框直接打 API 名稱
- **GCP 要信用卡** → 沒辦法跳過，但**不會被收費**（除非主動升級）
- **JSON 太大無法貼 TOML** → 正常，`private_key` 會很長；用 `tools/json_to_toml.py` 自動產生
- **Service Account 沒出現在 Sheet 共用名單** → 重新邀請一次並檢查 email 拼字

把每一關卡完成後的訊息或錯誤截圖丟給我，我幫您繼續。

- **跨帳號上傳出現 403 Forbidden** → 可能是 Firebase 帳號未授予 SA `Storage Object Admin`，回關卡 2.5 加成員