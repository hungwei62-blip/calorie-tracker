# 部署檢查清單

## Secrets

- [ ] `GEMINI_API_KEY` 是有效的新金鑰
- [ ] `[gcp]` Service Account 欄位完整，`private_key` 使用三引號
- [ ] `SPREADSHEET_ID` 不包含 `/d/` 或 `/edit`
- [ ] `PRIMARY_COACH_ID` 指向 `Users.role=coach` 的帳號
- [ ] Google Sheet 已分享給 Service Account

## 部署前

```bash
python -m py_compile app.py pages/common.py pages/coach/__init__.py pages/student/__init__.py
python -m pytest -q
python tools/audit_and_migrate.py
```

- [ ] 檢查 `audit_report.json`，確認主教練及預計修復資料
- [ ] 先保存產生的五份 CSV，再視需要執行 `--apply`
- [ ] 遷移後確認 Users 筆數不變，並保留 `Users.after.csv`

## 部署後驗收

- [ ] 學員可註冊、登入及完成 TDEE 問卷
- [ ] TDEE 不會改動 `created_at`，五項目標寫入正確欄位
- [ ] 教練只能看到 `coach_id` 等於自己的學員
- [ ] 文字與照片皆可取得 Gemini 分析結果
- [ ] 儲存飲食後 `Records.image_url` 保持空白
- [ ] 體重、訓練、歷史與 CSV/PDF 匯出正常

餐點圖片只用於當次 Gemini 分析，不需要檢查 Firebase。
