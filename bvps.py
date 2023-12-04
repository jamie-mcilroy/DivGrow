import yfinance as yf
import json
from xml.etree import ElementTree as ET
import pandas as pd

def get_book_value(symbols, output_format="json"):
    results = []

    for symbol in symbols:
        try:
            # Create a Ticker object for the stock
            ticker = yf.Ticker(symbol)

            # Get the info data for the stock
            info = ticker.info

            # Extract the total equity from the info data
            total_book_value = info.get('bookValue', 'unavailable')

            results.append({"Symbol": symbol, "Total BVPS": total_book_value})
        
        except Exception as e:
            print(f"An error occurred for symbol {symbol}: {str(e)}")
            results.append({"Symbol": symbol, "Total BookValue": "unavailable"})

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
            ET.SubElement(entry, "TotalBookValue").text = str(result["Total Book Value"])
        return ET.tostring(root, encoding="utf-8", method="xml").decode()
    else:
        return "Invalid output format"

# Example usage:
symbols = ["TD.TO", "MSFT", "GOOGL", "TOU.TO"]  # Example list of symbols
output_format = "json"
result = get_book_value(symbols, output_format)
print(result)
