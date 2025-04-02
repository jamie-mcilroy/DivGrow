import pandas as pd

def drip_projection(stock_price, num_shares, current_yield, avg_div_growth, years, price_growth=0.0):
    """
    Projects DRIP (Dividend Reinvestment Plan) over a given number of years.

    Parameters:
        stock_price (float): Initial stock price.
        num_shares (float): Number of shares currently held.
        current_yield (float): Current dividend yield (e.g. 0.03 for 3%).
        avg_div_growth (float): Average annual dividend growth rate (e.g. 0.05 for 5%).
        years (int): Number of years to project.
        price_growth (float): Expected annual stock price growth rate (e.g. 0.06 for 6%).

    Returns:
        pd.DataFrame: Table of projection with columns: Year, Share Price, Shares Owned, Annual Income, Portfolio Value
    """
    data = []
    dividend_per_share = stock_price * current_yield

    for year in range(1, years + 1):
        annual_income = num_shares * dividend_per_share
        new_shares = annual_income / stock_price
        num_shares += new_shares
        portfolio_value = num_shares * stock_price

        data.append({
            "Year": year,
            "Share Price": round(stock_price, 2),
            "Shares Owned": round(num_shares, 4),
            "Annual Income": round(annual_income, 2),
            "Portfolio Value": round(portfolio_value, 2)
        })

        # Grow dividend and stock price for next year
        dividend_per_share *= (1 + avg_div_growth)
        stock_price *= (1 + price_growth)

    return pd.DataFrame(data)

def main():
    # Example test parameters
    stock_price = 44.58
    num_shares = 6178
    current_yield = .0648
    avg_div_growth = .2642
    price_growth = 0.02  # Stock price grows 6% annually
    years = 10

    projection = drip_projection(
        stock_price=stock_price,
        num_shares=num_shares,
        current_yield=current_yield,
        avg_div_growth=avg_div_growth,
        years=years,
        price_growth=price_growth
    )

    print(projection)

if __name__ == "__main__":
    main()
