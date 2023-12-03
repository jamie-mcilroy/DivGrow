import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from xml.etree import ElementTree as ET

def scrape_average_annual_eps(symbols, num_years, output_format="json"):
    results = []

    for symbol in symbols:
        url = f'https://www.alphaquery.com/stock/t.{symbol}/earnings-history'
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

            # Calculate the average Annual EPS and round it to 2 decimal places
            average_annual_eps = filtered_df['Actual EPS'].astype(float).mean()
            average_annual_eps = round(average_annual_eps, 2)  # Round to 2 decimal places

            results.append({"Symbol": symbol, "Average Annual EPS": average_annual_eps})

        else:
            print(f"Failed to retrieve data for symbol {symbol}. Status code:", response.status_code)

    # Return the results in the specified format
    if output_format == "json":
        return json.dumps(results, indent=4)
    elif output_format == "csv":
        df = pd.DataFrame(results)
        return df.to_csv(index=False)
    elif output_format == "xml":
        root = ET.Element("Results")
        for result in results:
            entry = ET.SubElement(root, "Entry")
            ET.SubElement(entry, "Symbol").text = result["Symbol"]
            ET.SubElement(entry, "AverageAnnualEPS").text = str(result["Average Annual EPS"])
        return ET.tostring(root, encoding="utf-8", method="xml").decode()

# Example usage:
symbols = ["TD","BCE","ACO", "TOU", "ENB"]  # Example symbol for TD Bank on the Toronto Stock Exchange
num_years = 5
output_format = "json"
result = scrape_average_annual_eps(symbols, num_years, output_format)
print(result)
