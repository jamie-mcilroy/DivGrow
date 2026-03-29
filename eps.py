import json
import os
import re
import sys

import pandas as pd
import requests
from bs4 import BeautifulSoup


SYMBOLS_PATH = "configs/symbols.json"
OUTPUT_CSV = "data/eps_10y_pivot.csv"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
TABLE_CLASS = "table table-bordered table-striped table-basic"


def clean_symbol(symbol):
    return symbol.split(".", 1)[0] if "." in symbol else symbol


def load_symbols(path=SYMBOLS_PATH):
    with open(path, "r", encoding="utf-8") as file:
        symbols = json.load(file)
    if not isinstance(symbols, list):
        raise ValueError(f"{path} must contain a JSON array of symbols")
    return [str(symbol).strip() for symbol in symbols if str(symbol).strip()]


def fetch_earnings_history_page(symbol):
    cleaned_symbol = clean_symbol(symbol)
    url = f"https://www.alphaquery.com/stock/T.{cleaned_symbol}/earnings-history"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response.text


def parse_eps_table(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.find("table", {"class": TABLE_CLASS})
    if table is None:
        return pd.DataFrame()

    rows = []
    headers = ["Announcement Date", "Fiscal Quarter End", "Estimated EPS", "Actual EPS"]

    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) != len(headers):
            continue
        rows.append({headers[index]: cols[index].get_text(strip=True) for index in range(len(headers))})

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["Announcement Date"] = pd.to_datetime(df["Announcement Date"], errors="coerce")
    df["Fiscal Quarter End"] = pd.to_datetime(df["Fiscal Quarter End"], errors="coerce")
    df["Actual EPS"] = pd.to_numeric(
        df["Actual EPS"].str.replace(r"[^\d.-]", "", regex=True),
        errors="coerce",
    )
    return df


def build_yearly_eps_series(symbol, num_years):
    try:
        html_text = fetch_earnings_history_page(symbol)
        df = parse_eps_table(html_text)
    except Exception as exc:
        print(f"Failed to fetch EPS history for {symbol}: {exc}", file=sys.stderr)
        return {"Symbol": symbol, "Years": {}, "AverageEPS": "unavailable"}

    if df.empty:
        print(f"No EPS data table found for symbol {symbol}.", file=sys.stderr)
        return {"Symbol": symbol, "Years": {}, "AverageEPS": "unavailable"}

    df = df.dropna(subset=["Fiscal Quarter End", "Actual EPS"]).copy()
    if df.empty:
        return {"Symbol": symbol, "Years": {}, "AverageEPS": "unavailable"}

    current_year = pd.Timestamp.now().year
    start_year = current_year - num_years
    filtered_df = df[
        (df["Fiscal Quarter End"].dt.year >= start_year)
        & (df["Fiscal Quarter End"].dt.year < current_year)
    ].copy()

    if filtered_df.empty:
        return {"Symbol": symbol, "Years": {}, "AverageEPS": "unavailable"}

    annual_eps = (
        filtered_df.groupby(filtered_df["Fiscal Quarter End"].dt.year)["Actual EPS"]
        .sum()
        .sort_index()
    )

    years = {int(year): round(value, 2) for year, value in annual_eps.items()}
    average_eps = round(annual_eps.mean(), 2) if not annual_eps.empty else "unavailable"

    return {"Symbol": symbol, "Years": years, "AverageEPS": average_eps}


def build_eps_pivot(symbols, num_years):
    end_year = pd.Timestamp.now().year - 1
    selected_years = list(range(end_year - num_years + 1, end_year + 1))
    rows = []
    average_rows = []

    for symbol in symbols:
        result = build_yearly_eps_series(symbol, num_years)
        year_values = [result["Years"].get(year, "") for year in selected_years]
        numeric_values = [value for value in year_values if value != ""]
        avg_3y = round(sum(numeric_values[-3:]) / len(numeric_values[-3:]), 2) if numeric_values[-3:] else ""
        avg_5y = round(sum(numeric_values[-5:]) / len(numeric_values[-5:]), 2) if numeric_values[-5:] else ""
        avg_10y = round(sum(numeric_values[-10:]) / len(numeric_values[-10:]), 2) if numeric_values[-10:] else ""

        rows.append([result["Symbol"]] + year_values + [avg_3y, avg_5y, avg_10y])
        average_rows.append(
            {
                "Symbol": result["Symbol"],
                "EPS": result["AverageEPS"],
            }
        )

    pivot_df = pd.DataFrame(
        rows,
        columns=["Symbol"] + [str(year) for year in selected_years] + ["Avg EPS 3Y", "Avg EPS 5Y", "Avg EPS 10Y"],
    )
    average_df = pd.DataFrame(average_rows)
    return pivot_df, average_df


def write_eps_pivot(df, output_path=OUTPUT_CSV):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def scrape_average_annual_eps(symbols, num_years):
    _, average_df = build_eps_pivot(symbols, num_years)
    return average_df


def main():
    symbols = load_symbols()
    pivot_df, _average_df = build_eps_pivot(symbols, 10)
    output_path = write_eps_pivot(pivot_df)
    print(output_path)


if __name__ == "__main__":
    main()
