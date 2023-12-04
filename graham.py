import pandas as pd
from eps import scrape_average_annual_eps
from bvps import get_book_value
from divhist import avg_div_grwth
import math

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
    combined_df["Graham Number"] = combined_df.apply(
        lambda row: round(math.sqrt(22.5 * row["EPS"] * row["BVPS"]), 2), axis=1
    )
     # Calculate the BG_Perc column
    combined_df["gr%"] = combined_df.apply(
        lambda row: round(((row["closing_price"]-row["Graham Number"]) / row["closing_price"]) * 100, 2),
        axis=1
    )



    # Select and reorder columns for the final dataframe
    combined_df = combined_df[["Symbol", "Graham Number", "closing_price", "gr%","BVPS", "EPS","yield","avg_div_grwth","exDivDate","daysToExDiv"]]
    combined_df.sort_values(by="gr%", inplace=True)
    return combined_df

if __name__ == "__main__":
    symbols = ["TD", "TOU", "CNQ", "ACO.X", "NA", "ENB", "TRP", "RY", "CM", "BNS","CJ"]
    years = 5
    output_format = "csv"
    result = get_combined_metrics(symbols, years)
    print(result)