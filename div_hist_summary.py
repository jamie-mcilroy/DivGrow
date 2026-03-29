import sys
from dividend_forecasts.dividends import build_pivot, build_pivot_rows, determine_years, write_pivot
from dividend_forecasts.io_utils import load_csv_rows
from dividend_forecasts.paths import DIVIDENDS_10Y_PIVOT_CSV, DIVIDENDS_BY_YEAR_CSV


YEARS_BACK = 10


def main():
    try:
        rows = load_csv_rows(DIVIDENDS_BY_YEAR_CSV, encoding="utf-8")
    except FileNotFoundError:
        print(f"Input file not found: {DIVIDENDS_BY_YEAR_CSV}", file=sys.stderr)
        raise SystemExit(1)

    if not rows:
        print(f"No rows found in {DIVIDENDS_BY_YEAR_CSV}", file=sys.stderr)
        raise SystemExit(1)

    selected_years = determine_years(rows, YEARS_BACK)
    if not selected_years:
        print("No years available to summarize.", file=sys.stderr)
        raise SystemExit(1)

    pivot = build_pivot(rows, selected_years)
    write_pivot(DIVIDENDS_10Y_PIVOT_CSV, selected_years, build_pivot_rows(pivot, selected_years))
    print(DIVIDENDS_10Y_PIVOT_CSV)


if __name__ == "__main__":
    main()
