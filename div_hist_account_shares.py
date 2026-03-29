import os
import sys
from dividend_forecasts.accounts import prepare_accounts
from dividend_forecasts.io_utils import get_year_columns, load_csv_rows
from dividend_forecasts.paths import ACCOUNT_SHARE_DIR, DIVIDENDS_10Y_PIVOT_CSV, HOLDINGS_CSV
from dividend_forecasts.projections import effective_growth_rate, project_share_counts


OUTPUT_DIR = ACCOUNT_SHARE_DIR
YEARS_TO_PROJECT = 20


def build_summary_lookup(summary_rows):
    lookup = {}
    for row in summary_rows:
        lookup[row["Ticker"]] = row
    return lookup


def build_account_projection(holdings, summary_lookup, latest_year):
    symbol_rows = []
    missing_symbols = []

    for holding in holdings:
        symbol = holding["Symbol"]
        quantity = holding["Quantity"]
        current_price = holding["Price"]
        yield_rate = holding["Yield"]
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
        yearly_shares = project_share_counts(
            quantity=quantity,
            current_price=current_price,
            yield_rate=yield_rate,
            latest_dividend=latest_dividend,
            growth_rate=growth_rate,
            latest_year=latest_year,
            years_to_project=YEARS_TO_PROJECT,
        )

        symbol_rows.append(
            {
                "Account": holding.get("Account", ""),
                "Symbol": symbol,
                "Quantity": quantity,
                "Price": current_price,
                "Yield": yield_rate,
                "GrowthRateUsed": effective_growth_rate(growth_rate),
                "YearlyShares": yearly_shares,
            }
        )

    return symbol_rows, sorted(set(missing_symbols))


def write_account_projection(account, symbol_rows, output_dir):
    import csv

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{account}_shares_20y.csv")

    years = sorted(symbol_rows[0]["YearlyShares"]) if symbol_rows else []
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
                    f"{row['Quantity']:.4f}",
                    f"{row['Price']:.2f}",
                    f"{row['Yield'] * 100:.1f}%",
                    f"{row['GrowthRateUsed'] * 100:.1f}%",
                ]
                + [f"{row['YearlyShares'][year]:.4f}" for year in years]
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
        symbol_rows, missing_symbols = build_account_projection(holdings, summary_lookup, latest_year)
        if not symbol_rows:
            continue

        output_path = write_account_projection(account, symbol_rows, OUTPUT_DIR)
        written_files.append(output_path)

        if missing_symbols:
            print(
                f"{account}: missing share projection data for {', '.join(missing_symbols)}",
                file=sys.stderr,
            )

    for output_path in written_files:
        print(output_path)


if __name__ == "__main__":
    main()
