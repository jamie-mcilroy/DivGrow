import requests
import pandas as pd

API_KEY = "VzusVsTSqfGJNssVdkcnPit9WnBEUvlR"
BASE_URL = "https://financialmodelingprep.com/stable"

def test_fmp_income_statement(symbol="TD:TSX"):
    """Simple connectivity + data test for FMP income statement endpoint."""
    url = f"{BASE_URL}/income-statement?symbol={symbol}&apikey={API_KEY}"

    print(f"Requesting: {url}\n")
    response = requests.get(url)
    print(f"HTTP Status: {response.status_code}")

    if response.status_code != 200:
        print("❌ Request failed.")
        return

    data = response.json()
    if not data:
        print("⚠️ No data returned.")
        return

    # Convert to DataFrame for a clean view
    df = pd.DataFrame(data)

    print("\n✅ Connection succeeded! Sample record:\n")
    print(df.head(1).T)  # print the most recent record vertically

    print("\nAvailable columns:")
    print(df.columns.tolist())

if __name__ == "__main__":
    test_fmp_income_statement()