import yfinance as yf
import datetime
import pandas as pd
import json
import csv
from xml.etree import ElementTree as ET

def calculate_average_growth_rates(symbols, num_years, output_format="json"):
    # Get the current year
    current_year = datetime.date.today().year

    # Create a list to store the results
    results = []

    for symbol in symbols:
        # Create a Yahoo Finance ticker object
        stock = yf.Ticker(symbol)

        # Get historical dividend data
        dividend_data = stock.dividends

        # Calculate the total annual dividends paid
        total_dividends = dividend_data.resample('Y').sum()

        # Calculate the dividend growth rate
        dividend_growth_rate = total_dividends.pct_change() * 100

        # Calculate the average growth rate for the last 'num_years' years, excluding the current year
        last_years_data = dividend_growth_rate.loc[(dividend_growth_rate.index.year >= current_year - num_years) & (dividend_growth_rate.index.year < current_year)]
        average_growth_rate = round(last_years_data.mean(), 2)

        # Append the result to the list
        results.append({"Symbol": symbol, "Average Growth Rate": average_growth_rate})

    # Sort the results in descending order by dividend growth rate
    results.sort(key=lambda x: x["Average Growth Rate"], reverse=True)

    # Return the results in the specified format
    if output_format == "json":
        return json.dumps(results, indent=4)
    elif output_format == "csv":
        df = pd.DataFrame(results)
        return df.to_csv(index=False)
    elif output_format == "xml":
        root = ET.Element("Results")
        for result in results:
            entry = ET.SubElement(root, "Entry")
            ET.SubElement(entry, "Symbol").text = result["Symbol"]
            ET.SubElement(entry, "AverageGrowthRate").text = str(result["Average Growth Rate"])
        return ET.tostring(root, encoding="utf-8", method="xml").decode()

# Example usage:
symbols = ["bce.to", "cnq.to", "td.to", "na.to", "aco-x.to", "tou.to", "enb.to"]
num_years = 10
output_format = "csv"
result = calculate_average_growth_rates(symbols, num_years, output_format)
print(result)
