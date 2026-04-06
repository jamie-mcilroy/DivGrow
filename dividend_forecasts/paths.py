import os
from datetime import date


CONFIGS_DIR = "configs"
RUNS_DIR = "runs"
RUN_DATE = os.getenv("DIVGROW_RUN_DATE", date.today().isoformat())
RUN_DIR = f"{RUNS_DIR}/{RUN_DATE}"
DATA_DIR = f"{RUN_DIR}/data"
OUTPUT_DIR = f"{RUN_DIR}/output"

SYMBOLS_JSON = f"{CONFIGS_DIR}/symbols.json"
HOLDINGS_CSV = f"{CONFIGS_DIR}/Holdings.csv"

EPS_10Y_PIVOT_CSV = f"{DATA_DIR}/eps_10y_pivot.csv"
CURRENT_PRICES_CSV = f"{DATA_DIR}/current_prices.csv"
BEN_GRAHAM_PRICES_CSV = f"{DATA_DIR}/ben_graham_prices.csv"
DIVIDENDS_BY_YEAR_CSV = f"{DATA_DIR}/dividends_by_year.csv"
DIVIDENDS_10Y_PIVOT_CSV = f"{DATA_DIR}/dividends_10y_pivot.csv"
DIVIDEND_EVENTS_CSV = f"{DATA_DIR}/dividend_events.csv"
DIVIDEND_EVENTS_WITH_PRICES_CSV = f"{DATA_DIR}/dividend_events_with_prices.csv"
DIVIDEND_YIELD_SUMMARY_CSV = f"{DATA_DIR}/dividend_yield_summary.csv"
FUNDAMENTALS_SUMMARY_CSV = f"{DATA_DIR}/fundamentals_summary.csv"

ACCOUNT_INCOME_DIR = f"{OUTPUT_DIR}/account_income_projections"
ACCOUNT_SHARE_DIR = f"{OUTPUT_DIR}/account_share_projections"
ACCOUNT_DRIP_INCOME_DIR = f"{OUTPUT_DIR}/account_drip_income_projections"
ACCOUNT_BALANCE_DIR = f"{OUTPUT_DIR}/account_balance_projections"
ACCOUNT_REPORTS_DIR = f"{OUTPUT_DIR}/account_reports"
FUNDAMENTALS_SUMMARY_HTML = f"{OUTPUT_DIR}/fundamentals_summary.html"
WEEKLY_PORTFOLIO_REPORT_HTML = f"{OUTPUT_DIR}/weekly_portfolio_report.html"
OUTPUT_INDEX_HTML = f"{OUTPUT_DIR}/index.html"
