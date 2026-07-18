/**
 * PROJECT PRIME weekly Google Drive backup.
 * Script Properties required: SOURCE_SPREADSHEET_ID, BACKUP_FOLDER_ID.
 */
const RETENTION_WEEKS = 12;
const BACKUP_PREFIX = 'PROJECT_PRIME_BACKUP_';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('PROJECT PRIME')
    .addItem('立即備份', 'backupNow')
    .addToUi();
}

function backupNow() {
  const properties = PropertiesService.getScriptProperties();
  const sourceId = properties.getProperty('SOURCE_SPREADSHEET_ID');
  const folderId = properties.getProperty('BACKUP_FOLDER_ID');
  if (!sourceId || !folderId) {
    throw new Error('缺少 SOURCE_SPREADSHEET_ID 或 BACKUP_FOLDER_ID Script Property');
  }

  const timezone = Session.getScriptTimeZone() || 'Asia/Taipei';
  const stamp = Utilities.formatDate(new Date(), timezone, 'yyyyMMdd_HHmmss');
  const folder = DriveApp.getFolderById(folderId);
  DriveApp.getFileById(sourceId).makeCopy(`${BACKUP_PREFIX}${stamp}`, folder);
  recordBackupAudit_(sourceId, stamp);
  pruneOldBackups_(folder);
}

function recordBackupAudit_(sourceId, stamp) {
  const audit = SpreadsheetApp.openById(sourceId).getSheetByName('AuditLog');
  if (!audit) return;
  audit.appendRow([
    new Date().toISOString(), `backup-${stamp}`, '', 'system',
    'backup.complete', 'spreadsheet', '', 'success', '{}'
  ]);
}

function pruneOldBackups_(folder) {
  const files = folder.getFiles();
  const backups = [];
  while (files.hasNext()) {
    const file = files.next();
    if (file.getName().startsWith(BACKUP_PREFIX)) {
      backups.push(file);
    }
  }
  backups.sort((a, b) => b.getDateCreated().getTime() - a.getDateCreated().getTime());
  backups.slice(RETENTION_WEEKS).forEach(file => file.setTrashed(true));
}

function installWeeklyTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(trigger => trigger.getHandlerFunction() === 'backupNow')
    .forEach(trigger => ScriptApp.deleteTrigger(trigger));
  ScriptApp.newTrigger('backupNow')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.SUNDAY)
    .atHour(3)
    .create();
}
