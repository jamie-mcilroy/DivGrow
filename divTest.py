import yfinance as yf
import datetime
import pandas as pd

def avg_div_grwth(symbols, num_years):
    # Get the current year
    current_year = datetime.date.today().year

    # Create a list to store the results
    results = []

    for symbol in symbols:
        ogSymbol=str(symbol)
        symbol=cleanSymbol(symbol)
        stock = yf.Ticker(f"{symbol}.to")
        dividend_data = stock.info["exDividendDate"]
        print (datetime.datetime.utcfromtimestamp(dividend_data ))

def cleanSymbol(input_string):
    # Check if the string contains a period
    if "." in input_string:
        # Replace the period with a hyphen
        result = input_string.replace(".", "-")
        return result
    else:
        # If no period is found, return the original string
        return input_string

if __name__ == "__main__":
    # Example usage:
    symbols = ["bce"]
    num_years = 5
    result_df = avg_div_grwth(symbols, num_years)

