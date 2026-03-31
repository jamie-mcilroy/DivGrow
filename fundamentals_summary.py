import csv
import os
import sys


DIVIDEND_PIVOT_CSV = "data/dividends_10y_pivot.csv"
BEN_GRAHAM_CSV = "data/ben_graham_prices.csv"
YIELD_SUMMARY_CSV = "data/dividend_yield_summary.csv"
CURRENT_PRICES_CSV = "data/current_prices.csv"
OUTPUT_CSV = "data/fundamentals_summary.csv"


def load_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def format_percent(value):
    if value in ("", None):
        return ""
    try:
        return f"{float(value) * 100:.2f}"
    except ValueError:
        return value


def get_year_columns(row):
    return sorted(int(key) for key in row.keys() if key.isdigit())


def merge_rows():
    dividend_rows = load_csv_rows(DIVIDEND_PIVOT_CSV)
    ben_graham_rows = load_csv_rows(BEN_GRAHAM_CSV)
    yield_rows = load_csv_rows(YIELD_SUMMARY_CSV)
    current_price_rows = load_csv_rows(CURRENT_PRICES_CSV)

    ben_graham_by_symbol = {row["Symbol"]: row for row in ben_graham_rows}
    yield_by_symbol = {row["Ticker"]: row for row in yield_rows}
    current_price_by_symbol = {row["Symbol"]: row for row in current_price_rows}

    merged_rows = []

    for dividend_row in dividend_rows:
        symbol = dividend_row["Ticker"]
        ben_graham_row = ben_graham_by_symbol.get(symbol, {})
        yield_row = yield_by_symbol.get(symbol, {})
        current_price_row = current_price_by_symbol.get(symbol, {})
        current_price = current_price_row.get("Current Price", "")
        ben_graham_5y = ben_graham_row.get("Ben Graham 5Y", "")
        year_columns = get_year_columns(dividend_row)
        latest_full_year = year_columns[-2] if len(year_columns) >= 2 else None
        current_year = year_columns[-1] if year_columns else None

        yield_full = ""
        yield_current = ""
        if current_price not in ("", None):
            try:
                current_price_value = float(current_price)
                if current_price_value != 0:
                    if latest_full_year is not None and dividend_row.get(str(latest_full_year), "") not in ("", None):
                        yield_full = round((float(dividend_row[str(latest_full_year)]) / current_price_value) * 100, 2)
                    if current_year is not None and dividend_row.get(str(current_year), "") not in ("", None):
                        yield_current = round((float(dividend_row[str(current_year)]) / current_price_value) * 100, 2)
            except ValueError:
                yield_full = ""
                yield_current = ""

        delta_bg5 = ""
        if current_price not in ("", None) and ben_graham_5y not in ("", None):
            try:
                ben_graham_5y_value = float(ben_graham_5y)
                if ben_graham_5y_value != 0:
                    delta_bg5 = round(((float(current_price) - ben_graham_5y_value) / ben_graham_5y_value) * 100, 2)
            except ValueError:
                delta_bg5 = ""

        merged_row = dict(dividend_row)
        merged_row.update(
            {
                "Current Price": current_price,
                "YieldFull": yield_full,
                "YieldCurrent": yield_current,
                "Δ BG5": delta_bg5,
                "Growth5": format_percent(dividend_row.get("Avg Growth 5Y %", "")),
                "BVPS Year": ben_graham_row.get("BVPS Year", ""),
                "BVPS": ben_graham_row.get("BVPS", ""),
                "Avg EPS 3Y": ben_graham_row.get("Avg EPS 3Y", ""),
                "Avg EPS 5Y": ben_graham_row.get("Avg EPS 5Y", ""),
                "Avg EPS 10Y": ben_graham_row.get("Avg EPS 10Y", ""),
                "BG3": ben_graham_row.get("Ben Graham 3Y", ""),
                "BG5": ben_graham_row.get("Ben Graham 5Y", ""),
                "BG10": ben_graham_row.get("Ben Graham 10Y", ""),
                "Avg Yield 3Y": format_percent(yield_row.get("Avg Yield 3Y", "")),
                "Yield5": format_percent(yield_row.get("Avg Yield 5Y", "")),
                "Avg Yield 10Y": format_percent(yield_row.get("Avg Yield 10Y", "")),
                "Last Growth": format_percent(dividend_row.get("Last Growth", "")),
                "Avg Growth 3Y %": format_percent(dividend_row.get("Avg Growth 3Y %", "")),
                "Avg Growth 5Y %": format_percent(dividend_row.get("Avg Growth 5Y %", "")),
            }
        )
        merged_rows.append(merged_row)

    merged_rows.sort(
        key=lambda row: (
            row["Δ BG5"] == "",
            float(row["Δ BG5"]) if row["Δ BG5"] != "" else 0.0,
        )
    )

    return merged_rows


def write_csv(rows, output_path=OUTPUT_CSV):
    if not rows:
        raise ValueError("No rows to write.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    year_columns = get_year_columns(rows[0])
    latest_full_year_label = f"Y{year_columns[-2]}" if len(year_columns) >= 2 else "YieldFull"
    current_year_label = f"Y{year_columns[-1]}" if year_columns else "YieldCurrent"
    priority_fieldnames = [
        "Ticker",
        "Current Price",
        "BG5",
        "Δ BG5",
        "BG3",
        "BG10",
        latest_full_year_label,
        current_year_label,
        "Yield5",
        "Growth5",
    ]
    renamed_rows = []
    for row in rows:
        renamed_row = dict(row)
        renamed_row[latest_full_year_label] = renamed_row.pop("YieldFull", "")
        renamed_row[current_year_label] = renamed_row.pop("YieldCurrent", "")
        renamed_rows.append(renamed_row)

    remaining_fieldnames = [field for field in renamed_rows[0].keys() if field not in priority_fieldnames]
    fieldnames = priority_fieldnames + remaining_fieldnames

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(renamed_rows)


def main():
    for path in (DIVIDEND_PIVOT_CSV, BEN_GRAHAM_CSV, YIELD_SUMMARY_CSV, CURRENT_PRICES_CSV):
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
