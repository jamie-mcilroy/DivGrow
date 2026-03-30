import csv
import os
import sys


DIVIDEND_PIVOT_CSV = "data/dividends_10y_pivot.csv"
BEN_GRAHAM_CSV = "data/ben_graham_prices.csv"
YIELD_SUMMARY_CSV = "data/dividend_yield_summary.csv"
OUTPUT_CSV = "data/fundamentals_summary.csv"


def load_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def merge_rows():
    dividend_rows = load_csv_rows(DIVIDEND_PIVOT_CSV)
    ben_graham_rows = load_csv_rows(BEN_GRAHAM_CSV)
    yield_rows = load_csv_rows(YIELD_SUMMARY_CSV)

    ben_graham_by_symbol = {row["Symbol"]: row for row in ben_graham_rows}
    yield_by_symbol = {row["Ticker"]: row for row in yield_rows}

    merged_rows = []

    for dividend_row in dividend_rows:
        symbol = dividend_row["Ticker"]
        ben_graham_row = ben_graham_by_symbol.get(symbol, {})
        yield_row = yield_by_symbol.get(symbol, {})

        merged_row = dict(dividend_row)
        merged_row.update(
            {
                "BVPS Year": ben_graham_row.get("BVPS Year", ""),
                "BVPS": ben_graham_row.get("BVPS", ""),
                "Avg EPS 3Y": ben_graham_row.get("Avg EPS 3Y", ""),
                "Avg EPS 5Y": ben_graham_row.get("Avg EPS 5Y", ""),
                "Avg EPS 10Y": ben_graham_row.get("Avg EPS 10Y", ""),
                "Ben Graham 3Y": ben_graham_row.get("Ben Graham 3Y", ""),
                "Ben Graham 5Y": ben_graham_row.get("Ben Graham 5Y", ""),
                "Ben Graham 10Y": ben_graham_row.get("Ben Graham 10Y", ""),
                "Avg Yield 3Y": yield_row.get("Avg Yield 3Y", ""),
                "Avg Yield 5Y": yield_row.get("Avg Yield 5Y", ""),
                "Avg Yield 10Y": yield_row.get("Avg Yield 10Y", ""),
            }
        )
        merged_rows.append(merged_row)

    return merged_rows


def write_csv(rows, output_path=OUTPUT_CSV):
    if not rows:
        raise ValueError("No rows to write.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    priority_fieldnames = [
        "Ticker",
        "Ben Graham 3Y",
        "Ben Graham 5Y",
        "Ben Graham 10Y",
        "Avg Yield 5Y",
        "Avg Growth 5Y %",
    ]
    remaining_fieldnames = [field for field in rows[0].keys() if field not in priority_fieldnames]
    fieldnames = priority_fieldnames + remaining_fieldnames

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    for path in (DIVIDEND_PIVOT_CSV, BEN_GRAHAM_CSV, YIELD_SUMMARY_CSV):
        if not os.path.exists(path):
            print(f"Missing input file: {path}", file=sys.stderr)
            raise SystemExit(1)

    rows = merge_rows()
    if not rows:
        print("No fundamentals rows generated.", file=sys.stderr)
        raise SystemExit(1)

    write_csv(rows)
    print(OUTPUT_CSV)


if __name__ == "__main__":
    main()
