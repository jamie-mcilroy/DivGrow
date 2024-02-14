from divhist2 import get_dividend_growth

ticker = "TD"  # Example ticker
years_back = 5  # Example number of years back

# Get the average dividend growth
ticker, avg_growth, years_used = get_dividend_growth(ticker, years_back)
print(f"Ticker: {ticker}, Average Growth: {avg_growth}%, Years: {years_used}")
