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
        dividend_data = stock.dividends
        total_dividends = dividend_data.resample('Y').sum()
        dividend_growth_rate = total_dividends.pct_change() * 100
        last_years_data = dividend_growth_rate.loc[(dividend_growth_rate.index.year >= current_year - num_years) & (dividend_growth_rate.index.year < current_year)]
        average_growth_rate = round(last_years_data.mean(), 2)
        results.append({"Symbol": ogSymbol, "avg_div_grwth": average_growth_rate, "yrs": num_years})

    # Create a DataFrame from the results
    df = pd.DataFrame(results)

    # Sort the DataFrame in descending order by "Average Growth Rate"
    df = df.sort_values(by="avg_div_grwth", ascending=False).reset_index(drop=True)

    return df

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
    symbols = ["cj"]
    num_years = 5
    result_df = avg_div_grwth(symbols, num_years)
    print(result_df)
