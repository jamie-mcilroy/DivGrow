import sys
from dividend_forecasts.io_utils import get_year_columns, load_csv_rows
from dividend_forecasts.paths import DIVIDENDS_10Y_PIVOT_CSV
from dividend_forecasts.projections import project_holding_income


YEARS_TO_PROJECT = 20


def find_symbol_row(rows, symbol):
    for row in rows:
        if row["Ticker"] == symbol:
            return row
    return None

def build_projection_rows(symbol, shares, latest_year, latest_dividend, growth_rate, years_to_project):
    rows = []
    yearly_income = project_holding_income(shares, latest_dividend, growth_rate, latest_year, years_to_project)
    projected_dividend = latest_dividend

    for year in range(latest_year + 1, latest_year + years_to_project + 1):
        projected_dividend *= (1 + (growth_rate if growth_rate >= 0 else 0.0))
        rows.append(
            {
                "Ticker": symbol,
                "Shares": f"{shares:.4f}",
                "Base Year": str(latest_year),
                "Growth Rate Used": f"{growth_rate:.4f}",
                "Year": str(year),
                "Projected Dividend Per Share": f"{projected_dividend:.4f}",
                "Projected Annual Dividend Income": f"{yearly_income[year]:.2f}",
            }
        )

    return rows


def write_projection_csv(path, rows):
    import csv

    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "Ticker",
                "Shares",
                "Base Year",
                "Growth Rate Used",
                "Year",
                "Projected Dividend Per Share",
                "Projected Annual Dividend Income",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 div_hist_project.py <SYMBOL> <SHARES>", file=sys.stderr)
        raise SystemExit(1)

    symbol = sys.argv[1].strip()

    try:
        shares = float(sys.argv[2])
    except ValueError:
        print("Shares must be a number.", file=sys.stderr)
        raise SystemExit(1)

    rows = load_csv_rows(DIVIDENDS_10Y_PIVOT_CSV, encoding="utf-8")
    if not rows:
        print(f"No rows found in {DIVIDENDS_10Y_PIVOT_CSV}", file=sys.stderr)
        raise SystemExit(1)

    year_columns = get_year_columns(rows[0].keys())
    if not year_columns:
        print(f"No year columns found in {DIVIDENDS_10Y_PIVOT_CSV}", file=sys.stderr)
        raise SystemExit(1)

    latest_year = year_columns[-1]
    symbol_row = find_symbol_row(rows, symbol)
    if symbol_row is None:
        print(f"Symbol not found in {DIVIDENDS_10Y_PIVOT_CSV}: {symbol}", file=sys.stderr)
        raise SystemExit(1)

    latest_dividend_value = symbol_row.get(str(latest_year), "")
    growth_rate_value = symbol_row.get("Last Growth", "")
    if latest_dividend_value in ("", None):
        print(f"No dividend value for {symbol} in {latest_year}", file=sys.stderr)
        raise SystemExit(1)
    if growth_rate_value in ("", None):
        print(f"No last-year growth rate available for {symbol}", file=sys.stderr)
        raise SystemExit(1)

    latest_dividend = float(latest_dividend_value)
    growth_rate = float(growth_rate_value)

    projection_rows = build_projection_rows(
        symbol=symbol,
        shares=shares,
        latest_year=latest_year,
        latest_dividend=latest_dividend,
        growth_rate=growth_rate,
        years_to_project=YEARS_TO_PROJECT,
    )

    safe_symbol = symbol.replace(".", "_")
    output_path = f"{safe_symbol}_dividend_projection_20y.csv"
    write_projection_csv(output_path, projection_rows)
    print(output_path)


if __name__ == "__main__":
    main()
