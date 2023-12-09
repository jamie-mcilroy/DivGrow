# Graham Number Analysis Script

## Overview
This Python script is designed to calculate key financial metrics, including the Graham Number, for a list of stocks. The Graham Number is a figure that measures a stock's fundamental value by taking into account the earnings per share (EPS) and book value per share (BVPS). This script not only calculates the Graham Number but also provides additional insights such as dividend yield growth and closing price percentages.

## Features
- **Graham Number Calculation**: Computes the Graham Number for each stock symbol provided.
- **Dividend Growth and Yield Analysis**: Analyzes average dividend growth and yield.
- **Closing Price Analysis**: Compares the Graham Number with the closing price to calculate the percentage difference.
- **Data Export**: Sends the processed data to a specified Google Sheets document for easy viewing and analysis.

## Prerequisites
- Python 3.8 or higher
- Pandas library
- Requests library

## Environment Variable
**GOOGLE_SHEETS_URL** - This environment variable is crucial for the script's functionality. It should contain the URL of the Google Sheets Web App where the data will be sent. Ensure that this URL is correctly set in your environment before running the script.

## Installation
1. Clone the repository to your local machine.
2. Install the required dependencies using `pip install -r requirements.txt`.

## Usage
1. Make sure to have a `symbols.json` file in your directory with the stock symbols you want to analyze.
2. Set the `GOOGLE_SHEETS_URL` environment variable.
3. Run the script using `python script_name.py` (replace `script_name.py` with the actual name of your script).

## Google Apps Script Integration
This Python script sends data to a Google Sheets document via a Google Apps Script. Below is an overview of the Apps Script function that handles the incoming POST request from the Python script.

### `doPost` Function
- **Functionality**: The `doPost` function in the Google Apps Script is triggered when it receives a POST request from the Python script.
- **Process**:
  - Retrieves the active sheet in a Google Spreadsheet.
  - Parses the JSON payload from the POST request.
  - Clears existing content in the sheet, maintaining the existing format.
  - Sets headers based on the 'columns' field in the payload.
  - Processes each row in the data, converting 'exDivDate' from a long integer to a date format.
  - Appends each row to the sheet.
- **Response**: After updating the sheet, the script sends back a confirmation message.

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

