import yfinance as yf
from datetime import datetime, timedelta

def calculate_stock_performance(ticker):
    # Define the time range
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=365 * 10)

    # Fetch historical data using download method with auto_adjust
    historical_data = yf.download(ticker, start=start_date, end=end_date, actions=False, auto_adjust=False)

    # Ensure there is data to process
    if historical_data.empty:
        print("No data found for the given ticker.")
        return None

    # Get first and last closing prices
    start_price = historical_data['Close'].iloc[0].item()
    end_price = historical_data['Close'].iloc[-1].item()

    # Calculate average annual percentage change
    total_years = 10
    average_annual_change = ((end_price / start_price) ** (1 / total_years) - 1) * 100

    print(f"Stock: {ticker}")
    print(f"Start Date: {start_date}, Start Price: {start_price:.2f}")
    print(f"End Date: {end_date}, End Price: {end_price:.2f}")
    print(f"Average Annual Percentage Change Over 10 Years: {average_annual_change:.2f}%")

    return average_annual_change

# Example usage
ticker = "ENB.TO"  # Replace with any Canadian stock symbol
calculate_stock_performance(ticker)
