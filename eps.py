import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_average_annual_eps(symbols, num_years):
    results = []

    for symbol in symbols:
        try:
            url = f'https://www.alphaquery.com/stock/T.{symbol}/earnings-history'
            print(url)
            response = requests.get(url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                div = soup.find('div', {'class': 'col-xl margin-top'})
                table = div.find('table', {'class': 'table table-bordered table-striped table-basic'})

                data = []
                headers = ["Announcement Date", "Fiscal Quarter End", "Estimated EPS", "Actual EPS"]

                for row in table.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) == len(headers):
                        data.append({headers[i]: cols[i].text.strip() for i in range(len(headers))})

                df = pd.DataFrame(data)
                df['Announcement Date'] = pd.to_datetime(df['Announcement Date'])
                df['Fiscal Quarter End'] = pd.to_datetime(df['Fiscal Quarter End'])

                # Filter data for the specified number of years
                current_year = pd.Timestamp.now().year
                start_year = current_year - num_years
                filtered_df = df[(df['Announcement Date'].dt.year >= start_year) & (df['Announcement Date'].dt.year < current_year)]

                # Clean and convert the 'Actual EPS' values to numeric using .loc
                filtered_df.loc[:, 'Actual EPS'] = filtered_df['Actual EPS'].str.replace('[^\d.]', '', regex=True).astype(float)

                # Calculate the annual EPS by summing the quarters for each year
                annual_eps = filtered_df.groupby(filtered_df['Announcement Date'].dt.year)['Actual EPS'].sum()
                annual_eps = annual_eps.mean()  # Calculate the mean of annual EPS

                results.append({"Symbol": symbol, "EPS": round(annual_eps, 2)})  # Round to 2 decimal places

            else:
                print(f"Failed to retrieve data for symbol {symbol}. Status code:", response.status_code)
                results.append({"Symbol": symbol, "Average Annual EPS": "unavailable"})

        except Exception as e:
            print(f"An error occurred for symbol {symbol}: {str(e)}")
            results.append({"Symbol": symbol, "Average Annual EPS": "unavailable"})

    # Return the results as a DataFrame
    return pd.DataFrame(results)

if __name__ == "__main__":
    symbols = ["BCE"]  # Example symbols including an invalid one
    num_years = 3
    result_df = scrape_average_annual_eps(symbols, num_years)
    print(result_df)

