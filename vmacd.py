import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    data['EMA12'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    return data

def analyze_macd(symbol):
    # Fetch historical data
    data = yf.download(symbol, period='6mo', interval='1d')
    if data.empty:
        print(f"No data found for {symbol}.")
        return

    # Calculate MACD
    data = calculate_macd(data)

    # Determine trend
    latest_macd = data['MACD'].iloc[-1]
    latest_signal = data['Signal'].iloc[-1]
    status = "Closer to Buy" if latest_macd > latest_signal else "Further from Buy"

    # Plot MACD chart styled like TradingView dark mode
    plt.style.use('dark_background')
    plt.figure(figsize=(14,7), facecolor='#1e1e1e')
    plt.plot(data.index, data['MACD'], label='MACD', color='#26a69a', linewidth=2)
    plt.plot(data.index, data['Signal'], label='Signal Line', color='#ef5350', linewidth=2, linestyle='--')
    plt.title(f"MACD Analysis for {symbol} ({status})", fontsize=18, color='white', weight='bold')
    plt.xlabel('Date', fontsize=14, color='#a9a9a9')
    plt.ylabel('MACD', fontsize=14, color='#a9a9a9')
    plt.legend(frameon=False, loc='upper left')
    plt.grid(color='#333333', linestyle='--', linewidth=0.5, alpha=0.7)
    plt.gca().set_facecolor('#1e1e1e')
    plt.gca().spines['bottom'].set_color('#4d4d4d')
    plt.gca().spines['top'].set_color('#4d4d4d')
    plt.gca().spines['right'].set_color('#4d4d4d')
    plt.gca().spines['left'].set_color('#4d4d4d')
    plt.gca().tick_params(axis='x', colors='#a9a9a9')
    plt.gca().tick_params(axis='y', colors='#a9a9a9')
    plt.tight_layout()
    plt.show()

def main():
    analyze_macd('tou.TO')

if __name__ == "__main__":
    main()