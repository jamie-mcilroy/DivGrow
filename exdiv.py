import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def load_tickers(config_file="configs/config.json"):
    with open(config_file, "r") as file:
        config = json.load(file)
    return config.get("tickers", [])

def get_next_dividend_info(ticker):
    url = f"https://dividendhistory.org/payout/tsx/{ticker}/"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        table_rows = soup.select("table.table.table-bordered tbody tr")
        
        for row in reversed(table_rows):  # Reverse order to get the future payout first
            cols = row.find_all("td")
            if len(cols) >= 3:  # Ensure required columns exist
                ex_div_date = cols[0].text.strip()  # Ex-dividend date
                payout_date = cols[1].text.strip()  # Payment date
                try:
                    ex_div_date_obj = datetime.strptime(ex_div_date, "%Y-%m-%d")
                    payout_date_obj = datetime.strptime(payout_date, "%Y-%m-%d")
                    
                    if ex_div_date_obj > datetime.today():
                        return ex_div_date, payout_date
                except ValueError:
                    continue
    return "No upcoming ex-div date found", "No upcoming payout date found"

if __name__ == "__main__":
    tickers = load_tickers()
    
    for ticker in tickers:
        next_ex_div, next_payout = get_next_dividend_info(ticker)
        print(f"{ticker}: Next Ex-Dividend Date: {next_ex_div}, Next Payout Date: {next_payout}")
