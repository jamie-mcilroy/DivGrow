# DivGrow Project

The DivGrow project is a Python script that retrieves financial data, processes it, and publishes it to a Google Sheets document using a Google Apps Script web app. It can be scheduled to run periodically to keep the data up to date.

## Prerequisites

Before running the script, make sure you have the following prerequisites installed:

- Python 3.x
- Required Python packages (install them using `pip install -r requirements.txt`)
- A Google Sheets document for publishing the data

## Configuration

Create a `config.json` file in the project directory with the following content:


{
  "google_sheets_url": "your endpoint here"
}

## Configuration

1. Create a Google Sheets document where you want to publish the financial data.

2. Open the Google Sheets document and click on "Extensions" > "Apps Script" to open the Google Apps Script editor.

3. Replace the default `Code.gs` content with the following Google Apps Script code:

```javascript
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var data = JSON.parse(e.postData.contents);

  // Clear only the values in the sheet, keeping formatting intact
  var range = sheet.getDataRange();
  range.clearContent();

  // Set headers using the 'columns' field in the payload
  sheet.appendRow(data.columns);

  // Find the index of 'exDividendDate' in the 'columns' array
  var exDividendDateIndex = data.columns.indexOf('exDivDate');

  // Convert 'exDividendDate' from long to date and write data without headers
  data.data.forEach(function(row) {
    if (exDividendDateIndex !== -1) {
      var exDividendDate = new Date(row[exDividendDateIndex]);
      row[exDividendDateIndex] = exDividendDate; // Replace the long with the date object
    }
    sheet.appendRow(row);
  });

  return ContentService.createTextOutput('Data received and sheet updated successfully.  Secure');
}


