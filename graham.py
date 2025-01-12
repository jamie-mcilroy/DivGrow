from jinja2 import Environment, FileSystemLoader
import pandas as pd
from eps import scrape_average_annual_eps
from bvps import get_book_value
from divhist2 import avg_div_grwth
import math
import json
import requests
import os

def get_combined_metrics(symbols, years):
    try:
        # Try to get EPS data
        try:
            eps_df = scrape_average_annual_eps(symbols, years)
        except Exception as e:
            print(f"An error occurred while retrieving EPS data: {e}")
            eps_df = pd.DataFrame()  # Default to an empty DataFrame if EPS retrieval fails

        # Try to get BVPS data
        try:
            bvps_df = get_book_value(symbols)
        except Exception as e:
            print(f"An error occurred while retrieving Book Value data: {e}")
            bvps_df = pd.DataFrame()  # Default to an empty DataFrame if BVPS retrieval fails

        # Try to get average dividend growth data
        try:
            avgYield_df = avg_div_grwth(symbols, years)
        except Exception as e:
            print(f"An error occurred while retrieving Dividend Growth data: {e}")
            avgYield_df = pd.DataFrame()  # Default to an empty DataFrame if avg_div_grwth retrieval fails

        # Merge dataframes on the "Symbol" column if data is available
        if not eps_df.empty and not bvps_df.empty and not avgYield_df.empty:
            combined_df = pd.merge(eps_df, bvps_df, on="Symbol", how="inner")
            combined_df = pd.merge(combined_df, avgYield_df, on="Symbol", how="inner")

            # Convert columns to numeric, handling non-numeric values as NaN
            combined_df["EPS"] = pd.to_numeric(combined_df["EPS"], errors="coerce")
            combined_df["BVPS"] = pd.to_numeric(combined_df["BVPS"], errors="coerce")
            combined_df["closing_price"] = pd.to_numeric(combined_df["closing_price"], errors="coerce")

            # Calculate the Graham number
            combined_df["BG"] = combined_df.apply(
                lambda row: round(math.sqrt(22.5 * row["EPS"] * row["BVPS"]), 2), axis=1
            )

            # Calculate BG_Perc
            combined_df["gr"] = combined_df.apply(
                lambda row: round(((row["closing_price"] - row["BG"]) / row["closing_price"]) * 100, 2),
                axis=1
            )

            # Calculate Chowder number
            combined_df["chowder"] = combined_df.apply(
                lambda row: round(row["div_yield"] + row["weighted_avg_div_grwth"], 2),
                axis=1
            )

            # Select and order relevant columns
            combined_df = combined_df[
                ["Symbol", "BG", "closing_price", "gr", "BVPS", "EPS", "div_yield", "avg_yield", 
                 "weighted_avg_div_grwth", "chowder", "exDivDate", "daysToExDiv"]
            ]
            combined_df.sort_values(by="gr", inplace=True)
        else:
            print("One or more data retrievals failed, resulting in an empty DataFrame.")
            combined_df = pd.DataFrame()  # Empty DataFrame if any retrieval fails completely

        return combined_df

    except Exception as e:
        print(f"An unexpected error occurred in get_combined_metrics: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on unexpected failure



if __name__ == "__main__":
    with open('symbols.json', 'r') as file:
        symbols = json.load(file)


    years = 10
    result = get_combined_metrics(symbols, years)

    json_data = result.to_json(orient='split')
    parsed_data = json.loads(json_data)
    parsed_data['payload_type'] = 'div-grow'
    url = os.getenv("GOOGLE_SHEETS_INVESTMENT_SCREEN_URL")
    response = requests.post(url, json=parsed_data)
    print(response.text)