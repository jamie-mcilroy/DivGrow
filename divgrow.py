def calculate_dividend_income_and_shares(initial_year, years, initial_dividend, dividend_growth_rate, num_shares):
    dividend_income_and_shares = []
    current_dividend = initial_dividend

    for year in range(initial_year, initial_year + years):
        # Calculate the future dividend for the next year
        future_dividend = current_dividend * (1 + dividend_growth_rate)
        
        # Calculate the dividend income for the current year based on the number of shares
        year_income = num_shares * current_dividend

        # Append the year, number of shares, dividend per share, total income to the list
        dividend_income_and_shares.append((year, num_shares, current_dividend, year_income))

        # Calculate the future stock price based on the future dividend and historic yield
        future_stock_price = future_dividend / (historic_yield / 100)
        
        # Calculate the number of additional shares that can be purchased with the income
        additional_shares = year_income / future_stock_price
        
        # Update the total number of shares for the next year
        num_shares += additional_shares

        # Update current_dividend for the next iteration
        current_dividend = future_dividend

    return dividend_income_and_shares

def calculate_forecasted_prices(initial_year, years, initial_dividend, historic_yield, dividend_growth_rate):
    forecasted_prices = []
    current_dividend = initial_dividend

    for year in range(initial_year, initial_year + years):
        # Calculate the future dividend for the next year
        future_dividend = current_dividend * (1 + dividend_growth_rate)
        
        # Calculate the future stock price based on the future dividend and historic yield
        future_stock_price = future_dividend / (historic_yield / 100)
        
        # Append the year, future stock price, and future dividend to the list
        forecasted_prices.append((year, future_stock_price))
        
        # Update current_dividend for the next iteration
        current_dividend = future_dividend

    return forecasted_prices

# Example usage:
initial_year = 2023
years = 15
initial_dividend = 4.06  # The first future year's dividend
historic_yield = 5.8    # Static historic yield
dividend_growth_rate = 0.05  # Replace with your dividend growth rate (5% as 0.05)
num_shares = 6255  # Number of shares you own initially

dividend_income_and_shares = calculate_dividend_income_and_shares(initial_year, years, initial_dividend, dividend_growth_rate, num_shares)
forecasted_prices = calculate_forecasted_prices(initial_year, years, initial_dividend, historic_yield, dividend_growth_rate)

# Print the combined information for each year
for i in range(len(dividend_income_and_shares)):
    year, shares, dividend_per_share, total_income = dividend_income_and_shares[i]
    _, future_price = forecasted_prices[i]
    print(f"Year {year}: Number of Shares: {shares:.2f}, Dividend per Share: ${dividend_per_share:.2f}, Total Income: ${total_income:.2f}, Future Price: ${future_price:.2f}")
