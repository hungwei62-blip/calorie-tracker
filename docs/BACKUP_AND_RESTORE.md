# Google Drive 備份與還原

## 每週備份安裝

1. 由正式試算表擁有者建立私人 Drive 資料夾。
2. 在正式試算表開啟「擴充功能 → Apps Script」。
3. 貼上 `ops/apps_script/weekly_backup.gs`。
4. Script Properties 設定：
   - `SOURCE_SPREADSHEET_ID`：正式試算表 ID。
   - `BACKUP_FOLDER_ID`：私人備份資料夾 ID。
5. 將專案時區設為 `Asia/Taipei`。
6. 執行 `installWeeklyTrigger()` 並完成擁有者授權。
7. 執行一次 `backupNow()`，確認副本存在且只有擁有者可讀取。

腳本每週日 03:00 建立完整副本，保留最近 12 份。大量匯入、遷移或 schema 修改前，先從試算表的「PROJECT PRIME → 立即備份」建立額外快照。

## 還原演練

1. 複製最新備份為測試試算表，不要覆蓋正式檔案。
2. 將本機 `SPREADSHEET_ID` 暫時指向測試副本。
3. 執行 `python tools/init_sheets.py`，確認六張工作表皆為 `ok`。
4. 執行 smoke test，核對 Users、Records、Weight、Training、Notes、AuditLog 筆數。
5. 恢復正式 `SPREADSHEET_ID` 並刪除測試 secrets。

每季至少演練一次，將日期、執行者、來源備份與驗證結果記錄在維運紀錄中。

