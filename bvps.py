import yfinance as yf
import pandas as pd
import datetime

def get_book_value(symbols):
    results = []

    for symbol in symbols:
        try:
            ogSymbol=str(symbol)
            symbol=cleanSymbol(symbol)
            ticker = yf.Ticker(f"{symbol}.to")

            info = ticker.info
            close_price = ticker.history(period="1d")["Close"].iloc[0]
            formatted_price = f"{close_price:.2f}"
            total_book_value = info.get('bookValue', 'unavailable')
            div_yield = round(ticker.info["dividendYield"]*100,2)
            avg_yield = ticker.info["fiveYearAvgDividendYield"]
            exDivDate = datetime.datetime.utcfromtimestamp(ticker.info["exDividendDate"] )
            today = datetime.date.today()
            days_difference = (exDivDate.date() - today).days
            results.append({"Symbol": ogSymbol, "BVPS": total_book_value, "closing_price": formatted_price,"div_yield": div_yield,"avg_yield": avg_yield, "exDivDate":exDivDate,"daysToExDiv": days_difference})
        except Exception as e:
            print(f"An error occurred for symbol {symbol}: {str(e)}")
            results.append({"Symbol": ogSymbol, "BVPS": "unavailable","closing_price": "unavailable"})

    # Return the results as a DataFrame
    return pd.DataFrame(results)

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
    symbols = ["TD", "TOU", "ACO-X"]  # Example list of symbols
    result_df = get_book_value(symbols)
    print(result_df)
