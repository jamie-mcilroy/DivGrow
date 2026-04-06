import csv
import glob
import math
import os
import sys

from dividend_forecasts.paths import DATA_DIR, EPS_10Y_PIVOT_CSV
from dividend_forecasts.paths import BEN_GRAHAM_PRICES_CSV


EPS_CSV = EPS_10Y_PIVOT_CSV
BVPS_GLOB = os.path.join(DATA_DIR, "bvps_*.csv")
OUTPUT_CSV = BEN_GRAHAM_PRICES_CSV


def load_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def load_latest_bvps_by_symbol():
    latest = {}

    for path in sorted(glob.glob(BVPS_GLOB)):
        for row in load_csv_rows(path):
            symbol = row["Symbol"]
            year = int(row["Balance Sheet Year"])
            bvps = row["BVPS"]

            if bvps in ("", None):
                continue

            current = latest.get(symbol)
            if current is None or year > current["Balance Sheet Year"]:
                latest[symbol] = {
                    "Balance Sheet Year": year,
                    "BVPS": float(bvps),
                }

    return latest


def calculate_graham_price(eps_value, bvps_value):
    if eps_value in ("", None) or bvps_value in ("", None):
        return ""

    eps = float(eps_value)
    bvps = float(bvps_value)
    if eps <= 0 or bvps <= 0:
        return ""

    return round(math.sqrt(22.5 * eps * bvps), 2)


def build_rows():
    eps_rows = load_csv_rows(EPS_CSV)
    latest_bvps = load_latest_bvps_by_symbol()
    output_rows = []

    for row in eps_rows:
        symbol = row["Symbol"]
        bvps_info = latest_bvps.get(symbol)
        if bvps_info is None:
            continue

        bvps = bvps_info["BVPS"]
        output_rows.append(
            {
                "Symbol": symbol,
                "BVPS Year": bvps_info["Balance Sheet Year"],
                "BVPS": f"{bvps:.2f}",
                "Avg EPS 3Y": row.get("Avg EPS 3Y", ""),
                "Avg EPS 5Y": row.get("Avg EPS 5Y", ""),
                "Avg EPS 10Y": row.get("Avg EPS 10Y", ""),
                "Ben Graham 3Y": calculate_graham_price(row.get("Avg EPS 3Y", ""), bvps),
                "Ben Graham 5Y": calculate_graham_price(row.get("Avg EPS 5Y", ""), bvps),
                "Ben Graham 10Y": calculate_graham_price(row.get("Avg EPS 10Y", ""), bvps),
            }
        )

    return output_rows


def write_csv(rows, output_path=OUTPUT_CSV):
    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "Symbol",
                "BVPS Year",
                "BVPS",
                "Avg EPS 3Y",
                "Avg EPS 5Y",
                "Avg EPS 10Y",
                "Ben Graham 3Y",
                "Ben Graham 5Y",
                "Ben Graham 10Y",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    if not os.path.exists(EPS_CSV):
        print(f"Missing EPS file: {EPS_CSV}", file=sys.stderr)
        raise SystemExit(1)

    rows = build_rows()
    if not rows:
        print("No Graham rows generated.", file=sys.stderr)
        raise SystemExit(1)

    write_csv(rows)
    print(OUTPUT_CSV)


if __name__ == "__main__":
    main()
