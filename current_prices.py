import csv
import json
import os
import time

import yfinance as yf
from yfinance.exceptions import YFRateLimitError
from dividend_forecasts.paths import CURRENT_PRICES_CSV


SYMBOLS_PATH = "configs/symbols.json"
OUTPUT_PATH = CURRENT_PRICES_CSV
RETRY_DELAYS = [2, 5, 10]


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


def get_current_price_with_retry(symbol):
    yahoo_symbol = normalize_symbol(symbol)
    ticker = yf.Ticker(yahoo_symbol)
    last_rate_limit_error = None

    for delay in [0] + RETRY_DELAYS:
        if delay:
            time.sleep(delay)

        try:
            fast_info = ticker.fast_info
            if fast_info:
                price = None
                if hasattr(fast_info, "get"):
                    price = (
                        fast_info.get("lastPrice")
                        or fast_info.get("regularMarketPrice")
                        or fast_info.get("previousClose")
                    )
                if price:
                    return {
                        "Symbol": symbol,
                        "Yahoo Symbol": yahoo_symbol,
                        "Current Price": round(float(price), 2),
                    }
        except YFRateLimitError as exc:
            last_rate_limit_error = exc
            continue
        except Exception:
            pass

        try:
            history = ticker.history(period="5d", interval="1d", auto_adjust=False)
            if history is not None and not history.empty:
                close_price = history["Close"].dropna().iloc[-1]
                return {
                    "Symbol": symbol,
                    "Yahoo Symbol": yahoo_symbol,
                    "Current Price": round(float(close_price), 2),
                }
        except YFRateLimitError as exc:
            last_rate_limit_error = exc
            continue
        except Exception:
            pass

    if last_rate_limit_error is not None:
        raise ValueError(f"Yahoo rate limited the price request for {yahoo_symbol}") from last_rate_limit_error

    raise ValueError(f"No current price returned for {yahoo_symbol}")


def write_csv(rows, output_path=OUTPUT_PATH):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["Symbol", "Yahoo Symbol", "Current Price"])
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda item: item["Symbol"]))


def main():
    symbols = load_symbols()
    results = []

    for symbol in symbols:
        try:
            results.append(get_current_price_with_retry(symbol))
        except Exception as exc:
            print(f"Failed for {symbol}: {exc}")

    if not results:
        raise SystemExit(1)

    write_csv(results)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
