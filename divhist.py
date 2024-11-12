import yfinance as yf
import datetime
import pandas as pd
#This uses yfinance.  I found there are instances in the historical data where it doesn't reflect reality (missing one for TD in 2023)
def avg_div_grwth(symbols, num_years):
    current_year = datetime.date.today().year
    results = []

    for symbol in symbols:
        ogSymbol=str(symbol)
        symbol=cleanSymbol(symbol)
        stock = yf.Ticker(f"{symbol}.to")
        dividend_data = stock.dividends
        total_dividends = dividend_data.resample('Y').sum()
        #print (total_dividends)
        dividend_growth_rate = total_dividends.pct_change() * 100
        last_years_data = dividend_growth_rate.loc[(dividend_growth_rate.index.year >= current_year - num_years) & (dividend_growth_rate.index.year < current_year)]
        average_growth_rate = round(last_years_data.mean(), 2)
        results.append({"Symbol": ogSymbol, "avg_div_grwth": average_growth_rate, "yrs": num_years})
    df = pd.DataFrame(results)
    df = df.sort_values(by="avg_div_grwth", ascending=False).reset_index(drop=True)

    return df

def cleanSymbol(input_string):
    if "." in input_string:
        result = input_string.replace(".", "-")
        return result
    else:
        return input_string

if __name__ == "__main__":
    symbols = ["BMO","TD"]
    num_years = 5
    result_df = avg_div_grwth(symbols, num_years)
    print(result_df)
