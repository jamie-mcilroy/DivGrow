from jinja2 import Environment, FileSystemLoader
import pandas as pd
from eps import scrape_average_annual_eps
from bvps import get_book_value
from divhist import avg_div_grwth
import math
import json
import requests

def get_combined_metrics(symbols, years):
    eps_df = scrape_average_annual_eps(symbols, years)
    bvps_df = get_book_value(symbols)
    avgYield_df = avg_div_grwth(symbols, years)
    # Merge dataframes on the "Symbol" column
    combined_df = pd.merge(eps_df, bvps_df, on="Symbol")
    combined_df = pd.merge(combined_df, avgYield_df, on="Symbol")

    # Convert "EPS" and "BVPS" columns to numeric, handling non-numeric values as NaN
    combined_df["EPS"] = pd.to_numeric(combined_df["EPS"], errors="coerce")
    combined_df["BVPS"] = pd.to_numeric(combined_df["BVPS"], errors="coerce")
    # Convert the "closing_price" column to a numeric data type (float)
    combined_df["closing_price"] = pd.to_numeric(combined_df["closing_price"], errors="coerce")

    # Calculate the Graham number and add it as a new column, rounded to 2 decimal places
    combined_df["BG"] = combined_df.apply(
        lambda row: round(math.sqrt(22.5 * row["EPS"] * row["BVPS"]), 2), axis=1
    )
     # Calculate the BG_Perc column
    combined_df["gr"] = combined_df.apply(
        lambda row: round(((row["closing_price"]-row["BG"]) / row["closing_price"]) * 100, 2),
        axis=1
    )
    combined_df["chowder"] = combined_df.apply(
        lambda row: round(row["div_yield"] + row["avg_div_grwth"], 2),
        axis=1
    )
    combined_df = combined_df[["Symbol", "BG", "closing_price", "gr","BVPS", "EPS","div_yield","avg_yield","avg_div_grwth","chowder","exDivDate","daysToExDiv"]]
    combined_df.sort_values(by="gr", inplace=True)
    return combined_df



if __name__ == "__main__":
    with open('symbols.json', 'r') as file:
        symbols = json.load(file)

    # Load the configuration from the JSON file
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    # Retrieve the Google Sheets URL
    google_sheets_url = config.get('google_sheets_url')

    years = 5
    result = get_combined_metrics(symbols, years)

    json_data = result.to_json(orient='split')
    parsed_data = json.loads(json_data)
    url = google_sheets_url
    response = requests.post(url, json=parsed_data)

    # Print the response from the Google Apps Script
    print(response.text)