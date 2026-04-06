import csv
import datetime
import os
import sys
import time

import pandas as pd
import yfinance as yf
from yfinance.exceptions import YFRateLimitError

from dividend_forecasts.paths import DIVIDEND_EVENTS_CSV, DIVIDEND_EVENTS_WITH_PRICES_CSV, DIVIDEND_YIELD_SUMMARY_CSV


ENRICHED_EVENTS_CSV = DIVIDEND_EVENTS_WITH_PRICES_CSV
RETRY_DELAYS = [2, 5, 10]
WINDOWS = [3, 5, 10]


def load_dividend_events(path=DIVIDEND_EVENTS_CSV):
    with open(path, "r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def normalize_symbol_for_yahoo(symbol):
    cleaned = symbol.strip().upper()
    if "." in cleaned:
        cleaned = cleaned.replace(".", "-")
    if not cleaned.endswith(".TO"):
        cleaned = f"{cleaned}.TO"
    return cleaned


def fetch_price_history(symbol, ex_dates):
    yahoo_symbol = normalize_symbol_for_yahoo(symbol)
    parsed_dates = sorted(datetime.datetime.strptime(ex_date, "%Y-%m-%d").date() for ex_date in ex_dates)
    start_date = parsed_dates[0] - datetime.timedelta(days=7)
    end_date = parsed_dates[-1] + datetime.timedelta(days=7)

    ticker = yf.Ticker(yahoo_symbol)
    last_rate_limit_error = None

    for delay in [0] + RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            history = ticker.history(start=start_date.isoformat(), end=(end_date + datetime.timedelta(days=1)).isoformat(), auto_adjust=False)
            if history is not None and not history.empty:
                return yahoo_symbol, history
        except YFRateLimitError as exc:
            last_rate_limit_error = exc
            continue
        except Exception as exc:
            raise ValueError(f"Failed to fetch price history for {yahoo_symbol}: {exc}") from exc

    if last_rate_limit_error is not None:
        raise ValueError(f"Yahoo rate limited the request for {yahoo_symbol}") from last_rate_limit_error

    raise ValueError(f"No price history returned for {yahoo_symbol}")


def find_price_on_or_before(history, ex_date):
    history_index = history.index
    if getattr(history_index, "tz", None) is not None:
        comparison_index = history_index.tz_localize(None)
    else:
        comparison_index = history_index

    target = pd.Timestamp(ex_date)
    eligible = history.loc[comparison_index <= target]
    if eligible.empty:
        return "", ""
    last_row = eligible.iloc[-1]
    price_date = eligible.index[-1].date().isoformat()
    close_price = last_row.get("Close")
    if pd.isna(close_price):
        return "", ""
    return price_date, round(float(close_price), 4)


def infer_payments_per_year(ex_dates):
    parsed_dates = sorted(datetime.datetime.strptime(ex_date, "%Y-%m-%d").date() for ex_date in ex_dates)
    month_gaps = []

    for index in range(1, len(parsed_dates)):
        previous_date = parsed_dates[index - 1]
        current_date = parsed_dates[index]
        month_gap = (current_date.year - previous_date.year) * 12 + (current_date.month - previous_date.month)
        if month_gap > 0:
            month_gaps.append(month_gap)

    if not month_gaps:
        return None

    recent_gap = min(month_gaps[-3:])
    if recent_gap <= 1:
        return 12
    if recent_gap <= 3:
        return 4

    return None


def enrich_events_with_prices(events):
    events_by_symbol = {}
    for event in events:
        events_by_symbol.setdefault(event["Ticker"], []).append(event)

    enriched_rows = []
    failures = []

    for symbol, symbol_events in sorted(events_by_symbol.items()):
        ex_dates = [event["ExDate"] for event in symbol_events]
        payments_per_year = infer_payments_per_year(ex_dates)
        try:
            yahoo_symbol, history = fetch_price_history(symbol, ex_dates)
        except Exception as exc:
            failures.append(f"{symbol}: {exc}")
            continue

        for event in sorted(symbol_events, key=lambda row: row["ExDate"]):
            price_date, close_price = find_price_on_or_before(history, event["ExDate"])
            dividend = float(event["Dividend"])
            event_yield = round(dividend / close_price, 6) if close_price not in ("", 0) else ""
            annualized_yield = (
                round(event_yield * payments_per_year, 6)
                if event_yield != "" and payments_per_year in (4, 12)
                else ""
            )

            enriched_rows.append(
                {
                    "Ticker": symbol,
                    "Yahoo Symbol": yahoo_symbol,
                    "ExDate": event["ExDate"],
                    "PayDate": event["PayDate"],
                    "Dividend": f"{dividend:.6f}",
                    "PaymentsPerYear": payments_per_year if payments_per_year is not None else "",
                    "PriceDateUsed": price_date,
                    "ClosePrice": close_price if close_price != "" else "",
                    "EventYield": event_yield if event_yield != "" else "",
                    "AnnualizedYield": annualized_yield if annualized_yield != "" else "",
                }
            )

    return enriched_rows, failures


def calculate_average_yields(enriched_rows):
    current_year = datetime.date.today().year
    summary_rows = []
    rows_by_symbol = {}

    for row in enriched_rows:
        rows_by_symbol.setdefault(row["Ticker"], []).append(row)

    for symbol, symbol_rows in sorted(rows_by_symbol.items()):
        output_row = {"Ticker": symbol}

        for window in WINDOWS:
            start_year = current_year - window
            window_rows = []
            for row in symbol_rows:
                event_year = datetime.datetime.strptime(row["ExDate"], "%Y-%m-%d").year
                if start_year <= event_year < current_year and row["AnnualizedYield"] not in ("", None):
                    window_rows.append(float(row["AnnualizedYield"]))

            if window_rows:
                output_row[f"Avg Yield {window}Y"] = f"{sum(window_rows) / len(window_rows):.6f}"
            else:
                output_row[f"Avg Yield {window}Y"] = ""

        summary_rows.append(output_row)

    return summary_rows


def write_enriched_events(rows, path=ENRICHED_EVENTS_CSV):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "Ticker",
                "Yahoo Symbol",
                "ExDate",
                "PayDate",
                "Dividend",
                "PaymentsPerYear",
                "PriceDateUsed",
                "ClosePrice",
                "EventYield",
                "AnnualizedYield",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_yield_summary(rows, path=DIVIDEND_YIELD_SUMMARY_CSV):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["Ticker", "Avg Yield 3Y", "Avg Yield 5Y", "Avg Yield 10Y"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def main():
    if not os.path.exists(DIVIDEND_EVENTS_CSV):
        print(f"Missing dividend events file: {DIVIDEND_EVENTS_CSV}", file=sys.stderr)
        raise SystemExit(1)

    events = load_dividend_events()
    if not events:
        print(f"No rows found in {DIVIDEND_EVENTS_CSV}", file=sys.stderr)
        raise SystemExit(1)

    enriched_rows, failures = enrich_events_with_prices(events)
    for failure in failures:
        print(failure, file=sys.stderr)

    if not enriched_rows:
        print("No enriched dividend yield rows generated.", file=sys.stderr)
        raise SystemExit(1)

    enriched_path = write_enriched_events(enriched_rows)
    summary_path = write_yield_summary(calculate_average_yields(enriched_rows))
    print(enriched_path)
    print(summary_path)


if __name__ == "__main__":
    main()
