import yfinance as yf
import pandas as pd
import json
from datetime import datetime, timedelta

# Function to fetch data from Yahoo Finance
def fetch_data(ticker, days_back):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    return data

# Function to calculate Exponential Moving Average
def calculate_ema(prices, days):
    return prices.ewm(span=days, adjust=False).mean()

# Function to calculate MACD and Signal line
def calculate_macd(df):
    df['EMA_12'] = calculate_ema(df['Close'], 12)
    df['EMA_26'] = calculate_ema(df['Close'], 26)
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = calculate_ema(df['MACD'], 9)
    return df

# Function to find the most recent MACD and Signal Line crossover
def find_most_recent_crossover(df):
    most_recent_crossover = None

    for i in range(1, len(df)):
        if df['MACD'].iloc[i] > df['Signal_Line'].iloc[i] and df['MACD'].iloc[i-1] <= df['Signal_Line'].iloc[i-1]:
            most_recent_crossover = (df.index[i], 'Bullish')
        elif df['MACD'].iloc[i] < df['Signal_Line'].iloc[i] and df['MACD'].iloc[i-1] >= df['Signal_Line'].iloc[i-1]:
            most_recent_crossover = (df.index[i], 'Bearish')

    return most_recent_crossover

# Function to read symbols from a JSON file, replace dots with dashes, and append ".TO"
def read_symbols(file_path):
    with open(file_path, 'r') as file:
        symbols = json.load(file)
    return [symbol.replace('.', '-') + ".TO" for symbol in symbols]

# File containing the symbols
symbols_file = "symbols.json"
symbols = read_symbols(symbols_file)
days_back = 180

# Creating an empty DataFrame to hold the most recent crossovers
crossovers_df = pd.DataFrame(columns=['Symbol', 'Crossover Type', 'Date'])

# Iterating through each symbol and finding the most recent crossover
for ticker in symbols:
    df = fetch_data(ticker, days_back)
    df_macd = calculate_macd(df)
    most_recent_crossover = find_most_recent_crossover(df_macd)

    # Adding the most recent crossover to the DataFrame using pd.concat
    if most_recent_crossover:
        crossover_date, crossover_type = most_recent_crossover
        new_row = pd.DataFrame({
            'Symbol': [ticker],
            'Crossover Type': [crossover_type],
            'Date': [crossover_date.date()]
        })
        crossovers_df = pd.concat([crossovers_df, new_row], ignore_index=True)

# Print the DataFrame
print(crossovers_df)
