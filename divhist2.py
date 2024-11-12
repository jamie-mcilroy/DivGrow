import pandas as pd
import requests
from bs4 import BeautifulSoup

def avg_div_grwth(tickers, years_back):
    def fetch_dividend_data(ticker):
        url = f"https://dividendhistory.org/payout/tsx/{ticker}/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        dividend_data = []
        table = soup.find('table', id='dividend_table')
        rows = table.find_all('tr')
        for row in rows[1:]:  # Skip header row
            cols = row.find_all('td')
            date = cols[0].text.strip()
            dividend = cols[2].text.strip()
            dividend_data.append({'Date': date, 'Dividend': dividend})
        return dividend_data

    results = []

    for ticker in tickers:
        dividend_data = fetch_dividend_data(ticker)
        dividends_per_year = {}
        for item in dividend_data:
            date = item['Date']
            year = date.split('-')[0]
            dividend = float(item['Dividend'].replace('$', ''))
            if year in dividends_per_year:
                dividends_per_year[year] += dividend
            else:
                dividends_per_year[year] = dividend

        percentage_changes = []
        sorted_years = sorted(dividends_per_year.keys(), reverse=True)
        relevant_years = sorted_years[1:][:years_back]
        for i in range(len(relevant_years) - 1):
            current_year = relevant_years[i]
            previous_year = relevant_years[i + 1]
            current_dividend = dividends_per_year.get(current_year, 0)
            previous_dividend = dividends_per_year.get(previous_year, 0)
            if previous_dividend != 0:
                percentage_change = ((current_dividend - previous_dividend) / previous_dividend) * 100
                percentage_changes.append(percentage_change)

        average_percentage_change = sum(percentage_changes) / len(percentage_changes) if percentage_changes else 0
        results.append({'Symbol': ticker, 'avg_div_grwth': average_percentage_change, 'Years': relevant_years})

    results_df = pd.DataFrame(results)
    return results_df

def main():
    tickers = ['BMO', 'TD', 'ENB', 'LB', 'CWB', 'CCA', 'XTC', 'ACO.X', 'BNS', 'POW', 'CM', 'MFC', 'EMP.A', 'GWO', 
               'CU', 'EMA', 'SU', 'CPX', 'TRP', 'NA', 'RY', 'FTS', 'TOU', 'BCE', 'PPL', 'T', 'FTT', 'IMO', 'MRU', 
               'KEY', 'IFC', 'CNQ', 'SJ', 'L', 'CNR']
    years_back = 10  # Set the number of years to look back
    results_df = avg_div_grwth(tickers, years_back)
    
    # Sort the DataFrame in descending order based on 'avg_div_grwth'
    results_df = results_df.sort_values(by='avg_div_grwth', ascending=False)
    
    print(results_df)

if __name__ == "__main__":
    main()
