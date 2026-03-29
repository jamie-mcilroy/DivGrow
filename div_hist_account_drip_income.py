import os
import sys
from dividend_forecasts.accounts import prepare_accounts
from dividend_forecasts.io_utils import get_year_columns, load_csv_rows
from dividend_forecasts.paths import ACCOUNT_DRIP_INCOME_DIR, DIVIDENDS_10Y_PIVOT_CSV, HOLDINGS_CSV
from dividend_forecasts.projections import effective_growth_rate, project_drip_income


OUTPUT_DIR = ACCOUNT_DRIP_INCOME_DIR
YEARS_TO_PROJECT = 20


def build_summary_lookup(summary_rows):
    return {row["Ticker"]: row for row in summary_rows}


def build_account_projection(holdings, summary_lookup, latest_year):
    years = list(range(latest_year + 1, latest_year + YEARS_TO_PROJECT + 1))
    symbol_rows = []
    totals = {year: 0.0 for year in years}
    missing_symbols = []

    for holding in holdings:
        symbol = holding["Symbol"]
        summary_row = summary_lookup.get(symbol)
        if summary_row is None:
            missing_symbols.append(symbol)
            continue

        latest_dividend_value = summary_row.get(str(latest_year), "")
        growth_rate_value = summary_row.get("Last Growth", "")
        if latest_dividend_value in ("", None) or growth_rate_value in ("", None):
            missing_symbols.append(symbol)
            continue

        latest_dividend = float(latest_dividend_value)
        growth_rate = float(growth_rate_value)
        yearly_income, yearly_shares = project_drip_income(
            quantity=holding["Quantity"],
            current_price=holding["Price"],
            yield_rate=holding["Yield"],
            latest_dividend=latest_dividend,
            growth_rate=growth_rate,
            latest_year=latest_year,
            years_to_project=YEARS_TO_PROJECT,
        )

        symbol_rows.append(
            {
                "Symbol": symbol,
                "Starting Quantity": holding["Quantity"],
                "Price": holding["Price"],
                "Yield": holding["Yield"],
                "Growth Rate Used": effective_growth_rate(growth_rate),
                "Yearly Income": yearly_income,
                "Year-End Shares": yearly_shares,
            }
        )

        for year, amount in yearly_income.items():
            totals[year] += amount

    return symbol_rows, totals, sorted(set(missing_symbols))


def write_account_projection(account, symbol_rows, yearly_totals, output_dir):
    import csv

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{account}_drip_income_20y.csv")
    years = sorted(yearly_totals)

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            ["Account", "Symbol", "Starting Quantity", "Price", "Yield", "Growth Rate Used"]
            + [str(year) for year in years]
        )

        for row in sorted(symbol_rows, key=lambda item: item["Symbol"]):
            writer.writerow(
                [
                    account,
                    row["Symbol"],
                    f"{row['Starting Quantity']:.0f}",
                    f"{row['Price']:.2f}",
                    f"{row['Yield'] * 100:.1f}%",
                    f"{row['Growth Rate Used'] * 100:.1f}%",
                ]
                + [f"{row['Yearly Income'][year]:.2f}" for year in years]
            )

        writer.writerow([account, "TOTAL", "", "", "", ""] + [f"{yearly_totals[year]:.2f}" for year in years])

    return output_path


def main():
    try:
        holdings_rows = load_csv_rows(HOLDINGS_CSV)
        summary_rows = load_csv_rows(DIVIDENDS_10Y_PIVOT_CSV)
    except FileNotFoundError as exc:
        print(f"Input file not found: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not holdings_rows:
        print(f"No rows found in {HOLDINGS_CSV}", file=sys.stderr)
        raise SystemExit(1)
    if not summary_rows:
        print(f"No rows found in {DIVIDENDS_10Y_PIVOT_CSV}", file=sys.stderr)
        raise SystemExit(1)

    year_columns = get_year_columns(summary_rows[0].keys())
    if not year_columns:
        print(f"No year columns found in {DIVIDENDS_10Y_PIVOT_CSV}", file=sys.stderr)
        raise SystemExit(1)

    latest_year = year_columns[-1]
    summary_lookup = build_summary_lookup(summary_rows)
    accounts = prepare_accounts(holdings_rows)

    written_files = []

    for account, holdings in sorted(accounts.items()):
        symbol_rows, yearly_totals, missing_symbols = build_account_projection(holdings, summary_lookup, latest_year)
        if not symbol_rows:
            continue

        output_path = write_account_projection(account, symbol_rows, yearly_totals, OUTPUT_DIR)
        written_files.append(output_path)

        if missing_symbols:
            print(
                f"{account}: missing DRIP income data for {', '.join(missing_symbols)}",
                file=sys.stderr,
            )

    for output_path in written_files:
        print(output_path)


if __name__ == "__main__":
    main()
