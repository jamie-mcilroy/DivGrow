import pandas as pd
from eps import scrape_average_annual_eps
from divgrow import calculate_dividend_and_shares
from bvps import get_book_value

def transform_symbols_for_yahoo(symbols):
    return [f"{symbol}.TO" for symbol in symbols]

def transform_symbols_for_earnings(symbols):
    return [f"T.{symbol}" for symbol in symbols]

def get_combined_metrics(symbols, years, output_format="json"):
    # Convert symbols for Yahoo Finance
    yahoo_symbols = transform_symbols_for_yahoo(symbols)

    # Convert symbols for earnings function
    earnings_symbols = transform_symbols_for_earnings(symbols)

    # Retrieve EPS, dividend yield, and BVPS for each symbol
    eps_data = scrape_average_annual_eps(earnings_symbols, years, output_format="csv")
    bvps_data = get_book_value(yahoo_symbols, output_format="csv")

    # Combine the data into a single structure (e.g., a dictionary)
    combined_data = {
        "Earnings Per Share": eps_data,
        "Book Value Per Share": bvps_data
    }

    # Convert scalar values to lists
    for key, value in combined_data.items():
        if not isinstance(value, list):
            combined_data[key] = [value]

    # Return the combined data in the specified output format
    if output_format == "json":
        return combined_data
    elif output_format == "csv":
        # Convert to CSV format using pandas DataFrame
        combined_csv_data = pd.DataFrame(combined_data)
        return combined_csv_data.to_csv(index=False)
    elif output_format == "xml":
        # Convert to XML format (you may need to implement this)
        combined_xml_data = convert_to_xml(combined_data)
        return combined_xml_data
    else:
        return "Invalid output format"

# Example usage:
symbols = ["TD", "TOU", "CNQ"]
years = 5
output_format = "csv"
result = get_combined_metrics(symbols, years, output_format)
print(result)
