import json
import sys

import requests


API_KEY = "VzusVsTSqfGJNssVdkcnPit9WnBEUvlR"
BASE_URL = "https://financialmodelingprep.com/api/v3"


def normalize_symbol(symbol: str) -> str:
    if symbol.endswith(".TO"):
        return symbol.replace(".TO", ":TSX")
    return symbol.upper()


def print_endpoint_message(symbols):
    for original_symbol in symbols:
        symbol = normalize_symbol(original_symbol)
        url = f"{BASE_URL}/profile/{symbol}?apikey={API_KEY}"

        try:
            response = requests.get(url, timeout=30)
            print(f"Symbol: {original_symbol}")
            print(f"URL: {url}")
            print(f"Status: {response.status_code}")

            try:
                payload = response.json()
                print(json.dumps(payload, indent=2))
            except ValueError:
                print(response.text)

            print("-" * 60)
        except Exception as exc:
            print(f"Symbol: {original_symbol}")
            print(f"URL: {url}")
            print(f"Request failed: {exc}")
            print("-" * 60)


def main():
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ["TD.TO", "AAPL"]
    print_endpoint_message(symbols)


if __name__ == "__main__":
    main()
