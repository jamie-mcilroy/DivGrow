import os

url = os.getenv("GOOGLE_SHEETS_INVESTMENT_SCREEN_URL")

if url is None:
    print("ERROR: Environment variable GOOGLE_SHEETS_INVESTMENT_SCREEN_URL is not set!")
else:
    print(f"GOOGLE_SHEETS_INVESTMENT_SCREEN_URL: {url}")
