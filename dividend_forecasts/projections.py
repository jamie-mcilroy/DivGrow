def effective_growth_rate(growth_rate):
    return growth_rate if growth_rate >= 0 else 0.0


def project_holding_income(quantity, latest_dividend, growth_rate, latest_year, years_to_project):
    yearly_income = {}
    projected_dividend = latest_dividend
    growth = effective_growth_rate(growth_rate)

    for year in range(latest_year + 1, latest_year + years_to_project + 1):
        projected_dividend *= (1 + growth)
        yearly_income[year] = projected_dividend * quantity
    return yearly_income


def project_share_counts(quantity, current_price, yield_rate, latest_dividend, growth_rate, latest_year, years_to_project):
    yearly_shares = {}
    projected_shares = quantity
    projected_dividend = latest_dividend
    growth = effective_growth_rate(growth_rate)

    for year in range(latest_year + 1, latest_year + years_to_project + 1):
        projected_dividend *= (1 + growth)
        projected_price = projected_dividend / yield_rate if yield_rate > 0 else current_price
        annual_dividend_income = projected_shares * projected_dividend
        new_shares = annual_dividend_income / projected_price if projected_price > 0 else 0.0
        projected_shares += new_shares
        yearly_shares[year] = projected_shares
    return yearly_shares


def project_drip_income(quantity, current_price, yield_rate, latest_dividend, growth_rate, latest_year, years_to_project):
    yearly_income = {}
    yearly_shares = {}
    projected_shares = quantity
    projected_dividend = latest_dividend
    growth = effective_growth_rate(growth_rate)

    for year in range(latest_year + 1, latest_year + years_to_project + 1):
        projected_dividend *= (1 + growth)
        annual_income = projected_shares * projected_dividend
        projected_price = projected_dividend / yield_rate if yield_rate > 0 else current_price
        new_shares = annual_income / projected_price if projected_price > 0 else 0.0
        projected_shares += new_shares
        yearly_income[year] = annual_income
        yearly_shares[year] = projected_shares

    return yearly_income, yearly_shares


def project_balance(quantity, current_price, yield_rate, latest_dividend, growth_rate, latest_year, years_to_project, price_growth_rate):
    yearly_balance = {}
    projected_shares = quantity
    projected_dividend = latest_dividend
    growth = effective_growth_rate(growth_rate)

    for offset, year in enumerate(range(latest_year + 1, latest_year + years_to_project + 1), start=1):
        projected_dividend *= (1 + growth)
        drip_price = projected_dividend / yield_rate if yield_rate > 0 else current_price
        annual_income = projected_shares * projected_dividend
        new_shares = annual_income / drip_price if drip_price > 0 else 0.0
        projected_shares += new_shares
        projected_market_price = current_price * ((1 + price_growth_rate) ** offset)
        yearly_balance[year] = projected_shares * projected_market_price

    return yearly_balance
