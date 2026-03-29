import re
from datetime import datetime
from html import unescape
from urllib.request import Request, urlopen

from .io_utils import load_json, write_csv_rows


CURRENT_YEAR = datetime.now().year
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def load_symbols(path):
    symbols = load_json(path)
    if not isinstance(symbols, list):
        raise ValueError(f"{path} must contain a JSON array of ticker symbols")
    return [symbol.strip() for symbol in symbols if isinstance(symbol, str) and symbol.strip()]


def fetch_html(symbol):
    url = f"https://dividendhistory.org/payout/tsx/{symbol}/"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_dividends(html):
    text = re.sub(r"<[^>]+>", "\n", html)
    text = unescape(text)
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})\s*\$(\d+(?:\.\d+)?)")
    rows = pattern.findall(text)
    return [(ex_date, pay_date, float(amount)) for ex_date, pay_date, amount in rows]


def parse_date(date_text):
    return datetime.strptime(date_text, "%Y-%m-%d").date()


def infer_payments_per_year(rows):
    dated_rows = sorted(rows, key=lambda row: parse_date(row[0]))
    month_gaps = []

    for index in range(1, len(dated_rows)):
        previous_date = parse_date(dated_rows[index - 1][0])
        current_date = parse_date(dated_rows[index][0])
        month_gap = (current_date.year - previous_date.year) * 12 + (current_date.month - previous_date.month)
        if month_gap > 0:
            month_gaps.append(month_gap)

    if not month_gaps:
        return None

    recent_gap = min(month_gaps[-3:])
    if recent_gap <= 1:
        return 12
    if recent_gap <= 3:
        return 4
    return None


def add_current_year_forecast(rows, yearly_totals):
    current_year_rows = [row for row in rows if parse_date(row[0]).year == CURRENT_YEAR]
    if not current_year_rows:
        return yearly_totals

    payments_per_year = infer_payments_per_year(current_year_rows)
    if payments_per_year is None:
        payments_per_year = infer_payments_per_year(rows)

    if payments_per_year not in (4, 12):
        return yearly_totals

    current_year_rows = sorted(current_year_rows, key=lambda row: parse_date(row[0]))
    paid_amount = sum(row[2] for row in current_year_rows)
    payments_made = len(current_year_rows)
    remaining_payments = max(payments_per_year - payments_made, 0)
    latest_amount = current_year_rows[-1][2]
    yearly_totals[str(CURRENT_YEAR)] = paid_amount + remaining_payments * latest_amount
    return yearly_totals


def summarize_by_year(rows):
    totals = {}
    for ex_date, _pay_date, amount in rows:
        year = ex_date.split("-")[0]
        if int(year) == CURRENT_YEAR:
            continue
        totals[year] = totals.get(year, 0.0) + amount
    return add_current_year_forecast(rows, totals)


def calculate_latest_growth(year_values):
    growth_rates = []
    for index in range(1, len(year_values)):
        previous_value = year_values[index - 1]
        current_value = year_values[index]
        if previous_value in ("", None):
            continue
        previous_total = float(previous_value)
        current_total = float(current_value) if current_value not in ("", None) else 0.0
        if previous_total == 0:
            continue
        growth_rates.append((current_total - previous_total) / previous_total)
    return f"{growth_rates[-1]:.4f}" if growth_rates else ""


def calculate_average_growth(year_values, window_size):
    growth_rates = []
    for index in range(1, len(year_values)):
        previous_value = year_values[index - 1]
        current_value = year_values[index]
        if previous_value in ("", None):
            continue
        previous_total = float(previous_value)
        current_total = float(current_value) if current_value not in ("", None) else 0.0
        if previous_total == 0:
            continue
        growth_rates.append(((current_total - previous_total) / previous_total) * 100)

    trailing_rates = growth_rates[-window_size:]
    if not trailing_rates:
        return ""
    average_percent = sum(trailing_rates) / len(trailing_rates)
    return f"{average_percent / 100:.4f}"


def build_yearly_rows(symbol, yearly_totals):
    rows = []
    previous_total = None
    for year in sorted(yearly_totals):
        current_total = yearly_totals[year]
        growth = ""
        if previous_total not in (None, 0):
            growth = f"{((current_total - previous_total) / previous_total) * 100:.2f}"
        rows.append([symbol, year, f"{current_total:.3f}", growth])
        previous_total = current_total
    return rows


def write_dividends_by_year(path, rows):
    write_csv_rows(path, ["Ticker", "Year", "Annual Dividend", "Dividend Growth YoY %"], rows)


def determine_years(rows, years_back):
    years = sorted({int(row["Year"]) for row in rows})
    return years[-years_back:]


def build_pivot(rows, selected_years):
    pivot = {}
    for row in rows:
        symbol = row["Ticker"]
        year = int(row["Year"])
        if year not in selected_years:
            continue
        if symbol not in pivot:
            pivot[symbol] = {selected_year: "" for selected_year in selected_years}
        pivot[symbol][year] = row["Annual Dividend"]
    return pivot


def build_pivot_rows(pivot, selected_years):
    rows = []
    for symbol in sorted(pivot):
        year_values = [pivot[symbol][year] for year in selected_years]
        rows.append(
            [symbol]
            + year_values
            + [
                calculate_latest_growth(year_values),
                calculate_average_growth(year_values, 3),
                calculate_average_growth(year_values, 5),
            ]
        )
    return rows


def write_pivot(path, selected_years, rows):
    header = ["Ticker"] + [str(year) for year in selected_years] + ["Last Growth", "Avg Growth 3Y %", "Avg Growth 5Y %"]
    write_csv_rows(path, header, rows)

