def calculate_dividend_and_shares(initial_year, years, initial_dividend, historic_yield, dividend_growth_rate, num_shares, reinvest_dividends=True):
    data = []
    current_dividend = initial_dividend

    for year in range(initial_year, initial_year + years):
        # Calculate the future dividend for the next year
        future_dividend = round(current_dividend * (1 + dividend_growth_rate), 2)

        # Calculate the dividend income for the current year based on the number of shares
        year_income = round(num_shares * current_dividend, 2)

        # Calculate the future stock price based on the future dividend and historic yield
        future_stock_price = round(future_dividend / (historic_yield / 100), 2)

        if reinvest_dividends:
            # Calculate the number of additional shares that can be purchased with the income
            additional_shares = round(year_income / future_stock_price, 2)

            # Update the total number of shares for the next year
            num_shares = round(num_shares + additional_shares, 2)

        # Create a dictionary with the data for this year
        year_data = {
            'Year': year,
            'Number of Shares': num_shares,
            'Dividend per Share': current_dividend,
            'Total Income': year_income,
            'Future Price': future_stock_price
        }

        data.append(year_data)

        # Update current_dividend for the next iteration
        current_dividend = future_dividend

    return data

# Example usage:
initial_year = 2023
years = 15
initial_dividend = 4.06  # The first future year's dividend
historic_yield = 5.8    # Static historic yield
dividend_growth_rate = 0.05  # Replace with your dividend growth rate (5% as 0.05)
num_shares = 6255  # Number of shares you own initially
reinvest_dividends = True  # Set to False if you don't want to reinvest dividends

data = calculate_dividend_and_shares(initial_year, years, initial_dividend, historic_yield, dividend_growth_rate, num_shares, reinvest_dividends)

# Print the structured data with rounded values
for year_data in data:
    print(year_data)

# If you want to convert the data to a CSV file using Pandas:
import pandas as pd

df = pd.DataFrame(data)
df.to_csv('dividend_data.csv', index=False)
