// ============================================================
// FA Careers — Google Apps Script
// ============================================================
// SETUP INSTRUCTIONS:
//
// 1. Go to sheets.google.com → create a new sheet, name it
//    something like "FA Applications 2026"
//
// 2. In the sheet: Extensions → Apps Script
//
// 3. Delete any existing code and paste everything below
//    the dashed line into the editor. Save (Cmd+S).
//
// 4. Click Deploy → New Deployment
//    - Type: Web app
//    - Execute as: Me
//    - Who has access: Anyone
//    Click Deploy, approve permissions when prompted.
//
// 5. Copy the Web App URL that appears.
//
// 6. In careers.html, replace YOUR_APPS_SCRIPT_URL with that URL.
//
// ============================================================

function doGet(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const p     = e.parameter;

  // Write headers on the first submission
  if (sheet.getLastRow() === 0) {
    sheet.appendRow([
      'Timestamp (Sydney)', 'Position', 'Name', 'Email',
      'Phone', 'City', 'Showreel', 'Message'
    ]);
    sheet.getRange(1, 1, 1, 8).setFontWeight('bold');
  }

  const sydneyTime = Utilities.formatDate(
    new Date(),
    'Australia/Sydney',
    'dd/MM/yyyy HH:mm:ss'
  );

  sheet.appendRow([
    sydneyTime,
    p.position,
    p.name,
    p.email,
    p.phone,
    p.city,
    p.showreel,
    p.message
  ]);

  return ContentService
    .createTextOutput(JSON.stringify({ result: 'success' }))
    .setMimeType(ContentService.MimeType.JSON);
}
