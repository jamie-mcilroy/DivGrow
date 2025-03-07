import pandas as pd
import requests
from bs4 import BeautifulSoup

def avg_div_grwth(tickers, years_back):
    def fetch_dividend_data(ticker):
        url = f"https://dividendhistory.org/payout/tsx/{ticker}/"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve data for symbol {ticker}. Status code: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', id='dividend_table')
        if not table:
            print(f"No dividend table found for {ticker}")
            return []

        dividend_data = []
        rows = table.find_all('tr')
        for row in rows[1:]:
            cols = row.find_all('td')
            date = cols[0].text.strip()
            dividend_text = cols[2].text.strip()

            # Remove non-numeric characters
            cleaned_dividend = dividend_text.replace("$", "").replace("USD", "").strip()

            try:
                dividend = float(cleaned_dividend)
            except ValueError:
                print(f"Skipping invalid dividend value '{dividend_text}' for {ticker}")
                continue  # Skip invalid values

            dividend_data.append({'Date': date, 'Dividend': dividend})
        return dividend_data

    results = []

    for ticker in tickers:
        dividend_data = fetch_dividend_data(ticker)
        if not dividend_data:
            continue  # Skip processing if no data available

        dividends_per_year = {}
        for item in dividend_data:
            date = item['Date']
            year = date.split('-')[0]
            dividend = item['Dividend']
            dividends_per_year[year] = dividends_per_year.get(year, 0) + dividend

        percentage_changes = []
        sorted_years = sorted(dividends_per_year.keys(), reverse=True)
        relevant_years = sorted_years[1:][:years_back]
        weights = []

        for i in range(len(relevant_years) - 1):
            current_year = relevant_years[i]
            previous_year = relevant_years[i + 1]
            current_dividend = dividends_per_year.get(current_year, 0)
            previous_dividend = dividends_per_year.get(previous_year, 0)
            if previous_dividend != 0:
                percentage_change = ((current_dividend - previous_dividend) / previous_dividend) * 100
                percentage_changes.append(percentage_change)
                weights.append(len(relevant_years) - i)  # Assign higher weight to recent years

        weighted_avg_change = (
            sum(p * w for p, w in zip(percentage_changes, weights)) / sum(weights)
            if weights else 0
        )

        results.append({'Symbol': ticker, 'weighted_avg_div_grwth': weighted_avg_change, 'Years': relevant_years})

    results_df = pd.DataFrame(results)
    return results_df

def main():
    tickers = ['BMO', 'TD', 'ENB', 'LB', 'CWB', 'CCA', 'XTC', 'ACO.X', 'BNS', 'POW', 'CM', 'MFC', 'EMP.A', 'GWO', 
               'CU', 'EMA', 'SU', 'CPX', 'TRP', 'NA', 'RY', 'FTS', 'TOU', 'BCE', 'PPL', 'T', 'FTT', 'IMO', 'MRU', 
               'KEY', 'IFC', 'CNQ', 'SJ', 'L', 'CNR','BIPC']
    years_back = 10
    results_df = avg_div_grwth(tickers, years_back)
    
    if results_df.empty:
        print("No valid dividend data found.")
    else:
        results_df = results_df.sort_values(by='weighted_avg_div_grwth', ascending=False)
        print(results_df)

if __name__ == "__main__":
    main()
