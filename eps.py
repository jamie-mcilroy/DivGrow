import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_average_annual_eps(symbols, num_years):
    results = []

    for symbol in symbols:
        ogSymbol = str(symbol)
        symbol = cleanSymbol(symbol)
        try:
            url = f'https://www.alphaquery.com/stock/T.{symbol}/earnings-history'
            response = requests.get(url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find the EPS table directly
                table = soup.find('table', {'class': 'table table-bordered table-striped table-basic'})

                # Proceed only if the table is found
                if table:
                    data = []
                    headers = ["Announcement Date", "Fiscal Quarter End", "Estimated EPS", "Actual EPS"]

                    for row in table.find_all('tr'):
                        cols = row.find_all('td')
                        if len(cols) == len(headers):
                            data.append({headers[i]: cols[i].text.strip() for i in range(len(headers))})

                    df = pd.DataFrame(data)
                    df['Announcement Date'] = pd.to_datetime(df['Announcement Date'], errors='coerce')
                    df['Fiscal Quarter End'] = pd.to_datetime(df['Fiscal Quarter End'], errors='coerce')

                    # Filter data for the specified number of years
                    current_year = pd.Timestamp.now().year
                    start_year = current_year - num_years
                    filtered_df = df[(df['Announcement Date'].dt.year >= start_year) & 
                                     (df['Announcement Date'].dt.year < current_year)]

                    # Convert 'Actual EPS' to numeric, handling any non-numeric values
                    filtered_df.loc[:, 'Actual EPS'] = pd.to_numeric(filtered_df['Actual EPS'].str.replace('[^\d.]', '', regex=True),errors='coerce')

                    # Calculate the mean of annual EPS, summing quarters for each year
                    annual_eps = filtered_df.groupby(filtered_df['Announcement Date'].dt.year)['Actual EPS'].sum()
                    annual_eps_mean = annual_eps.mean() if not annual_eps.empty else float('nan')

                    results.append({"Symbol": ogSymbol, "EPS": round(annual_eps_mean, 2) if not pd.isna(annual_eps_mean) else "unavailable"})
                else:
                    print(f"No EPS data table found for symbol {symbol}.")
                    results.append({"Symbol": ogSymbol, "EPS": "unavailable"})
            else:
                print(f"Failed to retrieve data for symbol {symbol}. Status code:", response.status_code)
                results.append({"Symbol": ogSymbol, "EPS": "unavailable"})

        except Exception as e:
            print(f"An error occurred for symbol {symbol}: {str(e)}")
            results.append({"Symbol": ogSymbol, "EPS": "unavailable"})

    # Return the results as a DataFrame
    return pd.DataFrame(results)

def cleanSymbol(input_string):
    # Remove any suffixes after a period (e.g., "ACO.X" becomes "ACO")
    if "." in input_string:
        parts = input_string.split(".", 1)
        return parts[0]
    else:
        return input_string

if __name__ == "__main__":
    symbols = ["ENB", "ACO.X","BIP"]  # Example symbols
    num_years = 10
    result_df = scrape_average_annual_eps(symbols, num_years)

    print(result_df)
