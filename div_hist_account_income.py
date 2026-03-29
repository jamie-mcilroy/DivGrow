import os
import sys
from dividend_forecasts.accounts import prepare_accounts
from dividend_forecasts.io_utils import get_year_columns, load_csv_rows
from dividend_forecasts.paths import ACCOUNT_INCOME_DIR, DIVIDENDS_10Y_PIVOT_CSV, HOLDINGS_CSV
from dividend_forecasts.projections import effective_growth_rate, project_holding_income

YEARS_TO_PROJECT = 20
OUTPUT_DIR = ACCOUNT_INCOME_DIR


def build_summary_lookup(summary_rows):
    lookup = {}
    for row in summary_rows:
        lookup[row["Ticker"]] = row
    return lookup


def build_account_projection(holdings, summary_lookup, latest_year):
    years = list(range(latest_year + 1, latest_year + YEARS_TO_PROJECT + 1))
    symbol_rows = []
    totals = {year: 0.0 for year in years}
    missing_symbols = []

    for holding in holdings:
        symbol = holding["Symbol"]
        quantity = holding["Quantity"]
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
        projected_income = project_holding_income(
            quantity=quantity,
            latest_dividend=latest_dividend,
            growth_rate=growth_rate,
            latest_year=latest_year,
            years_to_project=YEARS_TO_PROJECT,
        )

        symbol_row = {
            "Account": holding.get("Account", ""),
            "Symbol": symbol,
            "Quantity": quantity,
            "GrowthRate5Y": effective_growth_rate(growth_rate),
            "YearlyIncome": projected_income,
        }
        symbol_rows.append(symbol_row)

        for year, income in projected_income.items():
            totals[year] += income

    return symbol_rows, totals, sorted(set(missing_symbols))


def write_account_projection(account, symbol_rows, yearly_totals, output_dir):
    import csv

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{account}_income_20y.csv")
    years = sorted(yearly_totals)

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Account", "Symbol", "Quantity", "Growth Rate 5Y"] + [str(year) for year in years])

        for row in sorted(symbol_rows, key=lambda item: item["Symbol"]):
            writer.writerow(
                [account, row["Symbol"], f"{row['Quantity']:.4f}", f"{row['GrowthRate5Y'] * 100:.1f}%"]
                + [f"{row['YearlyIncome'][year]:.2f}" for year in years]
            )

        writer.writerow(
            [account, "TOTAL", "", ""]
            + [f"{yearly_totals[year]:.2f}" for year in years]
        )

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
        output_path = write_account_projection(account, symbol_rows, yearly_totals, OUTPUT_DIR)
        written_files.append(output_path)

        if missing_symbols:
            print(
                f"{account}: missing dividend summary data for {', '.join(missing_symbols)}",
                file=sys.stderr,
            )

    for output_path in written_files:
        print(output_path)


if __name__ == "__main__":
    main()
