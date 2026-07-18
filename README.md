# 健身教練飲食管理系統

以 Streamlit 製作的管理員／教練／學員飲食管理系統。管理員可查看所有學員，教練只能管理歸屬自己的學員；學員可記錄食物、飲水、體重與訓練，並使用 Gemini 分析餐點照片。

## 主要功能

- 教練學員總覽、歷史趨勢、營養目標、備註與 CSV/PDF 匯出
- 學員飲食、體重、訓練、TDEE 與營養達成率
- Gemini 2.5 Flash 食物分析
- Google Sheets 資料儲存與 Excel 飲食紀錄匯入

餐點照片只在當次請求中交給 Gemini 分析，不會保存到 Firebase、Google Sheets 或其他永久儲存空間；`Records.image_url` 僅為舊版相容欄位，固定留空。

`Records.meal_type` 僅用於區分「食物」與「飲水」，系統不使用早餐、午餐、晚餐或宵夜等用餐時段分類。

## 執行

```bash
pip install -r requirements.txt
streamlit run app.py
```

設定方式請參考 [docs/SETUP_GCP.md](docs/SETUP_GCP.md)，部署前請依 [docs/DEPLOY_CHECKLIST.md](docs/DEPLOY_CHECKLIST.md) 驗證。

## 專案結構

```text
app.py                 Streamlit 設定、角色路由與啟動入口
pages/coach/            教練端頁面
pages/student/          學員端、登入與註冊頁面
pages/common.py         Session、快取與頁面共用設定
domain/                 TDEE、營養與歷史彙總規則
services/               認證、Google Sheets、Gemini 服務
ui/                     共用 Streamlit 樣式
tools/                  設定轉換、資料備份與遷移工具
tests/                  pytest 自動化測試
archive/                不參與部署的舊版腳本與實驗檔
```

## Google Sheets 工作表

- `Users`：帳號、bcrypt 密碼雜湊、`admin/coach/student` 角色、營養目標、`coach_id`
- `Records`：飲食及飲水紀錄
- `Weight`：體重紀錄
- `Training`：分類訓練紀錄，包含訓練類型及重量／有氧／其他的獨立內容
- `Notes`：教練備註

營養目標直接存放在 `Users`，沒有獨立的 `Goals` 工作表。

## 新學員歸屬

目前所有透過註冊頁建立的新學員，固定歸屬主教練
`u_20260629165506_4b525f9c`。此帳號必須存在於 `Users`，且 `role` 必須維持為
`coach`；註冊流程不讀取部署環境的 `PRIMARY_COACH_ID`。

## 資料遷移

先執行唯讀稽核與完整 CSV 備份：

```bash
python tools/audit_and_migrate.py
```

確認 `backups/<時間>/audit_report.json` 後才套用：

```bash
python tools/audit_and_migrate.py --apply
```

### Training 結構遷移

新版 `Training` 使用以下欄位：

```text
timestamp, user_id, training_types, strength_detail, cardio_detail, other_detail
```

先預覽並備份現有 Training：

```bash
python tools/migrate_training_schema.py
```

確認 `backups/migrate_training_<時間>/report.json` 後才清除舊訓練資料並套用新表頭：

```bash
python tools/migrate_training_schema.py --apply
```

這項遷移不轉換舊的背、胸、腿、核心與有氧欄位；`--apply` 會在完整備份後刪除全部舊 Training 資料。
