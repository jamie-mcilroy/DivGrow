import yfinance as yf
import pandas as pd

# Create a Ticker object for a stock symbol
symbol = "AAPL"  # Replace with your desired stock symbol
ticker = yf.Ticker(symbol)

# Get historical dividend data as a DataFrame
dividends_df = ticker.dividends.reset_index()

# Get historical stock split data as a DataFrame
splits_df = ticker.splits.reset_index()

# Merge dividend and stock split data on the 'Date' column
merged_df = pd.merge(dividends_df, splits_df, on="Date", how="outer")

# Calculate adjusted dividends
merged_df['Adjusted Dividend'] = merged_df['Dividends'] / merged_df['Stock Splits'].cumprod()

# Print the adjusted dividend data
print(merged_df[['Date', 'Dividends', 'Stock Splits', 'Adjusted Dividend']])
