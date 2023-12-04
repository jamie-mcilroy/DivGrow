import pandas as pd
from eps import scrape_average_annual_eps
from bvps import get_book_value
import math

def get_combined_metrics(symbols, years, output_format="json"):
    # Get EPS dataframe
    eps_df = scrape_average_annual_eps(symbols, years)
    # Get BVPS dataframe
    bvps_df = get_book_value(symbols)
    # Merge dataframes on the "Symbol" column
    combined_df = pd.merge(eps_df, bvps_df, on="Symbol")

    # Convert "EPS" and "BVPS" columns to numeric, handling non-numeric values as NaN
    combined_df["EPS"] = pd.to_numeric(combined_df["EPS"], errors="coerce")
    combined_df["BVPS"] = pd.to_numeric(combined_df["BVPS"], errors="coerce")

    # Calculate the Graham number and add it as a new column, rounded to 2 decimal places
    combined_df["Graham Number"] = combined_df.apply(
        lambda row: round(math.sqrt(22.5 * row["EPS"] * row["BVPS"]), 2), axis=1
    )

    # Select and reorder columns for the final dataframe
    combined_df = combined_df[["Symbol", "Graham Number", "BVPS", "EPS"]]

    # Return the combined data in the specified output format
    if output_format == "json":
        return combined_df.to_json(orient="records", indent=4)
    elif output_format == "csv":
        return combined_df.to_csv(index=False)
    elif output_format == "xml":
        # Convert to XML format (you may need to implement this)
        combined_xml_data = convert_to_xml(combined_df)
        return combined_xml_data
    else:
        return "Invalid output format"

# Example usage:
symbols = ["TD", "TOU", "CNQ", "ACO.X", "NA"]
years = 5
output_format = "csv"
result = get_combined_metrics(symbols, years, output_format)
print(result)
