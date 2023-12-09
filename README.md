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

## Contributing
Contributions to this project are welcome! Feel free to fork the repository and submit pull requests.


