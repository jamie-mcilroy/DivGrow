import csv
import json
import os
import time

import yfinance as yf
from yfinance.exceptions import YFRateLimitError
from dividend_forecasts.paths import DATA_DIR


SYMBOLS_PATH = "configs/symbols.json"
OUTPUT_DIR = DATA_DIR
RETRY_DELAYS = [2, 5, 10]
EQUITY_LABELS = [
    "Total Stockholder Equity",
    "Stockholders Equity",
    "Common Stock Equity",
    "Total Equity Gross Minority Interest",
]


def load_symbols(path=SYMBOLS_PATH):
    with open(path, "r", encoding="utf-8") as file:
        symbols = json.load(file)
    if not isinstance(symbols, list):
        raise ValueError(f"{path} must contain a JSON array of symbols")
    return [str(symbol).strip() for symbol in symbols if str(symbol).strip()]


def normalize_symbol(symbol):
    cleaned = symbol.strip().upper()
    if "." in cleaned:
        cleaned = cleaned.replace(".", "-")
    if not cleaned.endswith(".TO"):
        cleaned = f"{cleaned}.TO"
    return cleaned


def get_balance_sheet_with_retry(ticker, symbol):
    last_rate_limit_error = None

    for delay in [0] + RETRY_DELAYS:
        if delay:
            time.sleep(delay)

        for getter in (
            lambda: ticker.balance_sheet,
            lambda: ticker.get_balance_sheet(),
            lambda: ticker.quarterly_balance_sheet,
        ):
            try:
                balance_sheet = getter()
                if balance_sheet is not None and not balance_sheet.empty:
                    return balance_sheet
            except YFRateLimitError as exc:
                last_rate_limit_error = exc
                break
            except Exception:
                continue

    if last_rate_limit_error is not None:
        raise ValueError(f"Yahoo rate limited the request for {symbol}") from last_rate_limit_error

    raise ValueError(f"No balance sheet data returned for {symbol}")


def get_shares_outstanding_with_retry(ticker, symbol):
    last_rate_limit_error = None

    for delay in [0] + RETRY_DELAYS:
        if delay:
            time.sleep(delay)

        try:
            info = ticker.info
            shares = info.get("sharesOutstanding")
            if shares:
                return shares
        except YFRateLimitError as exc:
            last_rate_limit_error = exc
            continue
        except Exception:
            pass

        try:
            info = ticker.get_info()
            shares = info.get("sharesOutstanding")
            if shares:
                return shares
        except YFRateLimitError as exc:
            last_rate_limit_error = exc
            continue
        except Exception:
            pass

        try:
            shares_series = ticker.get_shares_full()
            if shares_series is not None and not shares_series.empty:
                return float(shares_series.dropna().iloc[-1])
        except YFRateLimitError as exc:
            last_rate_limit_error = exc
            continue
        except Exception:
            pass

        try:
            fast_info = ticker.fast_info
            shares = fast_info.get("shares") if hasattr(fast_info, "get") else None
            if shares:
                return shares
        except Exception:
            pass

    if last_rate_limit_error is not None:
        raise ValueError(f"Yahoo rate limited the share count request for {symbol}") from last_rate_limit_error

    raise ValueError(f"No sharesOutstanding value returned for {symbol}")


def calculate_bvps(symbol):
    yahoo_symbol = normalize_symbol(symbol)
    ticker = yf.Ticker(yahoo_symbol)

    balance_sheet = get_balance_sheet_with_retry(ticker, yahoo_symbol)
    shares_outstanding = get_shares_outstanding_with_retry(ticker, yahoo_symbol)

    equity = None
    for label in EQUITY_LABELS:
        if label in balance_sheet.index:
            equity = balance_sheet.loc[label].iloc[0]
            break

    if equity is None:
        raise ValueError(f"No supported equity row found in balance sheet for {yahoo_symbol}")

    balance_sheet_year = balance_sheet.columns[0].year
    bvps = equity / shares_outstanding
    return {
        "Symbol": symbol,
        "Yahoo Symbol": yahoo_symbol,
        "Balance Sheet Year": balance_sheet_year,
        "Shares Outstanding": int(shares_outstanding),
        "BVPS": round(float(bvps), 2),
    }


def write_grouped_csvs(results, output_dir=OUTPUT_DIR):
    os.makedirs(output_dir, exist_ok=True)
    written_files = []

    results_by_year = {}
    for row in results:
        year = row["Balance Sheet Year"]
        results_by_year.setdefault(year, []).append(row)

    for year, rows in sorted(results_by_year.items()):
        output_path = os.path.join(output_dir, f"bvps_{year}.csv")
        with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["Symbol", "Yahoo Symbol", "Balance Sheet Year", "Shares Outstanding", "BVPS"],
            )
            writer.writeheader()
            writer.writerows(sorted(rows, key=lambda item: item["Symbol"]))
        written_files.append(output_path)

    return written_files


def main():
    symbols = load_symbols()
    results = []

    for symbol in symbols:
        try:
            results.append(calculate_bvps(symbol))
        except Exception as exc:
            print(f"Failed for {symbol}: {exc}")

    if not results:
        raise SystemExit(1)

    for output_path in write_grouped_csvs(results):
        print(output_path)


if __name__ == "__main__":
    main()
