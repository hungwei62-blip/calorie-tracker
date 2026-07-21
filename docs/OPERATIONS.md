# PROJECT PRIME 維運手冊

## 每次部署前

1. 安裝 `requirements.lock`，執行完整 pytest、compileall 與入口匯入。
2. 涉及 schema、遷移或大量匯入時，先從試算表選單執行「PROJECT PRIME → 立即備份」。
3. 以管理員帳號確認「系統健康狀態」全部正常；警告項目需留下處理紀錄。
4. schema 只能透過 `python tools/init_sheets.py` 預覽，再以 `--apply` 明確套用；一般頁面不會自動改表。

## Log 與稽核

部署 log 使用 JSON 格式。應至少以 `timestamp`、`level`、`request_id`、`action`、`actor_id`、`target_id`、`duration` 與 `result` 查找事件。log 與 AuditLog 不得包含密碼、API key、照片、備註全文或健康紀錄內容。

敏感操作寫入 `AuditLog`。登入失敗、權限拒絕、備份、批次匯入及資料遷移應以 `request_id` 串接部署 log。

## 告警基準

- Google Sheets 或 Gemini 連續失敗 3 次：立即檢查部署 log、配額及憑證。
- Sheets 或 Gemini 操作 p95 超過 3 秒且持續 15 分鐘：檢查服務狀態及讀取範圍。
- 15 分鐘內登入失敗異常增加：檢查來源與帳號鎖定事件。
- 每週備份未在 AuditLog 出現 `backup.complete`：手動備份並檢查 Apps Script trigger。

## 備份與還原

- 每週 Drive 備份保留 12 份，本機 CSV 作為第二層備份。
- 每季在隔離副本執行一次還原演練，比對 Users、Records、Weight、Training、Notes、AuditLog 與 PasswordResetRequests 的表頭及筆數。
- 還原演練不可覆蓋正式試算表；結果需記錄日期、操作者、備份檔及比對結果。

## 事故處理

1. 記錄時間範圍與 request ID，暫停會擴大資料差異的批次操作。
2. 確認正式試算表與最近備份，不先刪除或覆蓋資料。
3. 依 AuditLog 與部署 log 判定受影響帳號及操作。
4. 修正後先在備份副本驗證，再恢復正式服務。
