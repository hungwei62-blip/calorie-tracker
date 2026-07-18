# PROJECT PRIME｜教練與學員飲食管理系統

PROJECT PRIME 是以 Streamlit 建置的教練／學員健康紀錄系統，使用 Google Sheets 作為主要資料庫，並以 Gemini 2.5 Flash 分析餐點照片。系統目前支援 `admin`、`coach`、`student` 三種角色，核心目標是讓教練掌握學員的日常飲食、飲水、體重與訓練狀態。

本 README 同時是專案的 handoff 文件。接手開發前，請先閱讀「重要商業規則」、「資料結構」、「安全與資料操作」及「已知限制」。

## 目前狀態

- 主要分支：`main`
- 執行環境：Python 3.11、Streamlit 1.48 以上
- 資料庫：Google Sheets
- AI 模型：Gemini 2.5 Flash
- 自動測試：182 項 pytest 測試
- 照片儲存：不保存；只在當次請求中送交 Gemini
- Firebase：正式流程不使用

## 角色與功能

### 學員端

- 註冊、登入與 TDEE 問卷。
- 個人首頁顯示體重、卡路里、水量、蛋白質與今日記錄完成度。
- 「日常紀錄」整合四個分頁：
  - 食物：手動輸入熱量／蛋白質，或拍照／上傳圖片交由 Gemini 辨識。
  - 飲水：預設 200 ml，每次調整 100 ml，可在同一天累加多筆。
  - 訓練：可複選重量訓練、有氧訓練、其他，並分別填寫內容；同日再次儲存會完整覆蓋。
  - 體重：每次調整 0.5 kg，可同日記錄多筆。
- 歷史頁依序顯示：
  - 體重 7／30 天趨勢；沒有新量測時只在記憶體中沿用最近有效體重，不建立假資料。
  - 熱量與蛋白質 7／30 天趨勢。
  - 飲水量 7／30 天趨勢。
  - 訓練週／月日曆。
- 固定底部導覽為「個人、飲食、歷史」三個純圖示按鈕；TDEE 與問卷仍保留於路由，但不在底部導覽。

### 教練端

- 只可查閱 `coach_id` 等於自己 `user_id` 的學員。
- 本日學員狀態顯示卡路里、水、蛋白質進度及訓練狀態。
- 可查看單一學員的飲食、體重、訓練及歷史趨勢。
- 可修改 BMR 與營養目標、管理教練備註。
- 可匯入 Excel 飲食紀錄，並選擇略過或覆蓋重複資料。
- 可匯出歷史 CSV 與 PDF。
- 固定底部導覽為「學員、歷史」兩個純圖示按鈕。

### 管理員

- 使用與教練端相同的介面與導覽。
- `admin` 可取得所有學員；`coach` 只能取得歸屬自己的學員。
- 管理員身份由 `Users.role` 決定，不應在程式中依帳號名稱判斷。

## 重要商業規則

1. 所有透過註冊頁建立的新學員固定歸屬主教練 `u_20260629165506_4b525f9c`。
2. 上述帳號必須存在於 `Users` 且保持 `role=coach`，否則系統會拒絕新註冊。
3. 註冊流程目前不讀取 `PRIMARY_COACH_ID`；若要更換主教練，需修改 `services/sheets.py` 的 `FIXED_PRIMARY_COACH_ID`、更新測試並重新部署。
4. 新學員註冊成功後，初始體重會同時寫入 `Weight`；若體重寫入失敗，帳號仍保留，學員可稍後補填。
5. `Records.meal_type` 只使用「食物」與「飲水」。舊值「喝水」只為歷史讀取相容；系統不再使用早餐、午餐、晚餐或宵夜。
6. 食物照片不寫入 Google Sheets 或任何永久儲存；`Records.image_url` 是相容欄位，應保持空白。
7. Gemini 只回傳並保存食物摘要、熱量與蛋白質；目前新食物紀錄的碳水、脂肪與水量為 0。
8. 教練端所有學員查詢與修改都必須通過歸屬驗證；學員只能使用 session 中自己的 `user_id`。
9. 體重卡片以完整 timestamp 排序，顯示最新有效體重，趨勢為「最新一筆－前一次有效紀錄」。
10. Google Sheets 讀取快取為 60 秒；所有寫入應走 `services/sheets.py` 並呼叫統一的快取失效流程。

## 技術架構

```text
app.py                    Streamlit 設定、session 初始化、角色路由與入口
pages/common.py           共用 session、快取、日期與登出邏輯
pages/student/            登入、註冊、學員首頁、日常紀錄、歷史、TDEE
pages/coach/              教練總覽、學員詳細頁、歷史、匯入與匯出
domain/                   不依賴外部服務的營養、完成度與歷史純函式
services/auth.py          bcrypt 密碼雜湊、帳號查詢、user_id 與時間產生
services/sheets.py        Google Sheets schema、CRUD、權限篩選與快取失效
services/gemini.py        Gemini 圖片分析、JSON schema 與嚴格回傳驗證
services/metrics.py       日期篩選、營養加總及進度分類
services/*_migration.py   Users／Records 遷移判斷邏輯
ui/navigation.py          依角色產生固定底部導覽
ui/styles.py              全域及頁面範圍限定的 Streamlit CSS
tools/                    稽核、備份、資料遷移與 secrets 轉換工具
tests/                    mock Sheets／Gemini 的 pytest 測試
static/                   登入品牌圖與共用頭像
assets/fonts/             本機字型資產
docs/                     GCP 設定與部署檢查清單
archive/                  不參與部署的舊腳本與實驗檔（被 gitignore）
backups/                  本機遷移備份（被 gitignore）
```

資料流：

```text
Streamlit 頁面
  ├─ domain/*：純計算，可直接單元測試
  ├─ services/sheets.py：Google Sheets 讀寫與權限
  └─ services/gemini.py：僅在食物照片分析時呼叫 Gemini
```

`app.py` 只負責啟動與路由。新增商業規則時優先放入 `domain/` 或 `services/`，避免把新邏輯繼續堆入頁面函式。

## Google Sheets 資料結構

程式會檢查並建立下列工作表。營養目標直接存放在 `Users`，沒有 `Goals` 工作表。

### Users

```text
user_id, username, name, password_hash, created_at, bmr,
daily_calorie_goal, daily_protein_goal, daily_carb_goal,
daily_fat_goal, daily_water_goal, role, weekly_training_goal,
record_mode, coach_id
```

- `role`：`admin`、`coach` 或 `student`。
- `password_hash`：bcrypt 雜湊，不儲存明碼。
- `record_mode`：保留 `simple`／`full` 相容欄位；學員首頁目前使用統一版面。
- `coach_id`：學員所屬教練；教練帳號本身保持空白。

### Records

```text
timestamp, user_id, meal_type, food_summary, calories, protein,
carb, fat, water_ml, image_url, portion
```

- 新紀錄種類只應為「食物」或「飲水」。
- `image_url` 固定留空。
- 同日多筆飲水與食物由查詢端加總。

### Weight

```text
timestamp, user_id, weight_kg
```

- 新資料使用完整 ISO timestamp。
- 舊 date-only 資料仍可讀取。
- 同一時間戳若重複，工作表較後列視為較新。

### Training

```text
timestamp, user_id, training_types, strength_detail,
cardio_detail, other_detail
```

- `training_types` 可包含重量訓練、有氧訓練、其他。
- 每一種類型使用獨立內容欄位，不共用文字。

### Notes

```text
timestamp, user_id, coach_id, note
```

## 本機啟動

### 1. 建立環境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 設定 secrets

將範例複製到本機設定檔：

```powershell
Copy-Item config\secrets.example.toml .streamlit\secrets.toml
```

必要設定：

- 頂層 `SPREADSHEET_ID`。
- `[gcp]` 內完整的 Google Service Account JSON 欄位。
- Gemini：Streamlit secret 與環境變數皆使用 `GEMINI_API_KEY`。

請將 Google Sheet 分享給 Service Account 的 `client_email` 並授予 Editor。完整步驟見 [docs/SETUP_GCP.md](docs/SETUP_GCP.md)。

> `.streamlit/secrets.toml` 含真實金鑰且已被 `.gitignore` 排除，禁止加入版本控制、截圖或貼到 issue。

### 3. 啟動

```powershell
streamlit run app.py
```

預設本機網址通常為 `http://localhost:8501`。若樣式未更新，停止程序後重新啟動，再以 `Ctrl + F5` 強制重新整理瀏覽器。

## 測試與品質檢查

完整測試不會讀取真實 secrets，Google Sheets 與 Gemini 皆以 mock 隔離。

```powershell
python -m pytest -q
python -m compileall -q app.py domain pages services tests ui
python -c "import app; print('APP_IMPORT_OK')"
git diff --check
```

目前完整測試基準為 `182 passed`。新增功能時至少要補足純函式、服務層與主要頁面路由測試。

## 資料備份與遷移

所有工具預設只預覽，只有明確傳入 `--apply` 才可修改線上 Sheet。執行前請確認使用的是正確試算表與 Service Account。

### Users 稽核與欄位修復

```powershell
python tools/audit_and_migrate.py
python tools/audit_and_migrate.py --apply
```

預覽會在 `backups/<時間>/` 匯出 `Users`、`Records`、`Weight`、`Training`、`Notes` 及稽核報告。套用後需比對前後筆數與 `Users.after.csv`。

### 移除舊用餐時段紀錄

```powershell
python tools/remove_legacy_meal_records.py
python tools/remove_legacy_meal_records.py --apply
```

此工具會鎖定 `meal_type` 精確為早餐、午餐、晚餐、宵夜的紀錄；套用前必須檢查備份報告。

### Training schema 重設

```powershell
python tools/migrate_training_schema.py
python tools/migrate_training_schema.py --apply
```

`--apply` 會先備份，再刪除全部舊 Training 資料並建立新版表頭；它不會轉換舊的背、胸、腿、核心或有氧欄位。這是破壞性操作，未確認備份前禁止執行。

## 部署與 Git 流程

部署平台需設定與本機相同的 Streamlit secrets。部署前依 [docs/DEPLOY_CHECKLIST.md](docs/DEPLOY_CHECKLIST.md) 完成權限、資料與 Gemini 驗證。

建議提交流程：

```powershell
git status --short
python -m pytest -q
git diff --check
git add <本次相關檔案>
git diff --cached --check
git commit -m "<type>: <summary>"
git push origin main
```

禁止提交：

- `.streamlit/secrets.toml`
- `backups/`、`_backup/`
- Streamlit log、pytest cache、coverage 輸出
- 真實 API key、Service Account private key、學員個資或匯出的線上資料

## 常見問題

### 新學員顯示主教練設定錯誤

確認 `Users` 中存在 `u_20260629165506_4b525f9c`，且該列 `role` 精確為 `coach`。

### Google Sheets 無法讀寫

確認 Sheet 已分享給 Service Account、`SPREADSHEET_ID` 只有 ID、private key 換行格式正確，且 GCP 已啟用 Sheets API 與 Drive API。

### Gemini 找不到 API key

確認 Streamlit secret 或環境變數使用大寫 `GEMINI_API_KEY`，並重新啟動應用程式。

### 手機樣式沒有更新

重新啟動 Streamlit、關閉手機瀏覽器或主畫面 App 後重開，必要時清除網站資料。底部導覽使用 viewport fixed 定位，不依賴 user-agent 判斷手機。

### 寫入後畫面仍是舊資料

讀取快取 TTL 為 60 秒。先確認寫入是否經過 `services/sheets.py` 的統一快取失效；不要直接在頁面層呼叫 gspread 寫入。

## 已知限制與後續建議

1. `pages/student/__init__.py` 與 `pages/coach/__init__.py` 仍偏大，後續可按頁面或元件繼續拆分。
2. 主教練 ID 目前硬編碼；若需要可營運切換，應改成受驗證的部署設定或管理員介面。
3. Google Sheets 適合目前規模，但不具交易、關聯約束與高併發能力；學員量或寫入頻率明顯成長時應評估 SQL。
4. 部署網址未寫入版本庫；交接時需由部署平台管理者補充正式 URL、擁有者與回滾方式。
5. 線上資料不隨 Git 版本回滾。程式回退前必須確認 schema 與線上資料仍相容。

## Handoff 檢查清單

- [ ] 可存取 GitHub repository 與部署平台。
- [ ] 可管理 Google Sheet 與 GCP Service Account。
- [ ] 知道正式環境 secrets 的管理位置，但沒有把值寫入文件或 Git。
- [ ] 已確認固定主教練帳號仍存在且角色正確。
- [ ] 本機 `python -m pytest -q` 全數通過。
- [ ] 已閱讀資料遷移工具的預覽／套用差異。
- [ ] 已完成學員註冊、登入、照片分析、飲水、體重與訓練的 smoke test。
- [ ] 已完成教練權限、目標修改、備註、匯入與匯出的 smoke test。
- [ ] 已記錄正式部署 URL、目前維運者與最近一次成功部署時間。

更詳細的環境與部署說明：

- [Google Cloud、Sheets 與 Gemini 設定](docs/SETUP_GCP.md)
- [部署檢查清單](docs/DEPLOY_CHECKLIST.md)
