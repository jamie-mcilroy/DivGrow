import yfinance as yf
import pandas as pd

def get_book_value(symbols):
    results = []

    for symbol in symbols:
        try:
            # Create a Ticker object for the stock
            ticker = yf.Ticker(f"{symbol}.to")

            info = ticker.info

            # Extract the total equity from the info data
            total_book_value = info.get('bookValue', 'unavailable')

            results.append({"Symbol": symbol, "BVPS": total_book_value})
        
        except Exception as e:
            print(f"An error occurred for symbol {symbol}: {str(e)}")
            results.append({"Symbol": symbol, "BVPS": "unavailable"})

    # Return the results as a DataFrame
    return pd.DataFrame(results)

if __name__ == "__main__":
    symbols = ["TD", "TOU", "ACO-X"]  # Example list of symbols
    result_df = get_book_value(symbols)
    print(result_df)
