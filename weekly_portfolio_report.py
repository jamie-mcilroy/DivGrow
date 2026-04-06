import csv
import html
import json
import os
import time
from datetime import datetime, timedelta

import yfinance as yf
from yfinance.exceptions import YFRateLimitError

from dividend_forecasts.accounts import prepare_accounts
from dividend_forecasts.paths import HOLDINGS_CSV, OUTPUT_DIR, OUTPUT_INDEX_HTML, WEEKLY_PORTFOLIO_REPORT_HTML
SYMBOLS_JSON = "configs/symbols.json"
OUTPUT_HTML = WEEKLY_PORTFOLIO_REPORT_HTML
RETRY_DELAYS = [2, 5, 10]
ACCOUNT_ORDER = [
    "All Investments",
    "MasterRetirement",
    "JamieRSP",
    "MichelleRSP",
    "JamieTFSA",
    "MichelleTFSA",
    "RESP",
    "JamieCash",
    "MichelleCash",
]
AGGREGATE_ACCOUNT_NAME = "All Investments"
TSX_EXTRA_SYMBOLS = {"CASH"}


def load_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def load_tsx_symbols():
    with open(SYMBOLS_JSON, "r", encoding="utf-8") as json_file:
        symbols = json.load(json_file)
    return {str(symbol).strip().upper() for symbol in symbols} | TSX_EXTRA_SYMBOLS


def normalize_symbol(symbol, tsx_symbols):
    cleaned = symbol.strip().upper()
    if "." in cleaned:
        cleaned = cleaned.replace(".", "-")
    if cleaned in tsx_symbols and not cleaned.endswith(".TO"):
        return f"{cleaned}.TO"
    return cleaned


def to_float(value):
    if value in ("", None):
        return None
    try:
        return float(str(value).replace("%", "").replace(",", ""))
    except ValueError:
        return None


def format_currency(value, decimals=0):
    number = to_float(value)
    if number is None:
        return ""
    return f"${number:,.{decimals}f}"


def format_number(value, decimals=2):
    number = to_float(value)
    if number is None:
        return ""
    return f"{number:,.{decimals}f}"


def format_percent(value, decimals=2):
    number = to_float(value)
    if number is None:
        return ""
    return f"{number:.{decimals}f}%"


def sort_accounts(account_names):
    order_lookup = {name: index for index, name in enumerate(ACCOUNT_ORDER)}
    return sorted(account_names, key=lambda name: (order_lookup.get(name, len(ACCOUNT_ORDER)), name))


def fetch_weekly_prices(symbol, tsx_symbols):
    yahoo_symbol = normalize_symbol(symbol, tsx_symbols)
    ticker = yf.Ticker(yahoo_symbol)
    last_rate_limit_error = None

    for delay in [0] + RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            history = ticker.history(period="14d", interval="1d", auto_adjust=False)
            if history is None or history.empty:
                continue
            closes = history["Close"].dropna()
            if closes.empty or len(closes) < 2:
                continue

            end_timestamp = closes.index[-1].tz_localize(None) if hasattr(closes.index[-1], "tz_localize") else closes.index[-1]
            target_start = end_timestamp - timedelta(days=7)
            start_candidates = closes[closes.index.tz_localize(None) <= target_start] if getattr(closes.index, "tz", None) else closes[closes.index <= target_start]
            if start_candidates.empty:
                start_close = float(closes.iloc[0])
                start_timestamp = closes.index[0]
            else:
                start_close = float(start_candidates.iloc[-1])
                start_timestamp = start_candidates.index[-1]

            end_close = float(closes.iloc[-1])
            return {
                "Symbol": symbol,
                "Yahoo Symbol": yahoo_symbol,
                "Start Date": start_timestamp.strftime("%Y-%m-%d"),
                "End Date": end_timestamp.strftime("%Y-%m-%d"),
                "Start Close": start_close,
                "End Close": end_close,
                "Weekly Return %": ((end_close - start_close) / start_close) * 100 if start_close else 0.0,
            }
        except YFRateLimitError as exc:
            last_rate_limit_error = exc
            continue
        except Exception:
            continue

    if last_rate_limit_error is not None:
        raise ValueError(f"Yahoo rate limited the weekly price request for {yahoo_symbol}") from last_rate_limit_error
    raise ValueError(f"No weekly price history returned for {yahoo_symbol}")


def collect_price_data(symbols, tsx_symbols):
    data = {}
    for symbol in sorted(symbols):
        try:
            data[symbol] = fetch_weekly_prices(symbol, tsx_symbols)
        except Exception as exc:
            print(f"Failed for {symbol}: {exc}")
    return data


def build_account_reports(accounts, price_lookup):
    reports = []
    for account in sort_accounts(accounts.keys()):
        holdings = accounts[account]
        rows = []
        start_value = 0.0
        end_value = 0.0
        total_change = 0.0

        for holding in holdings:
            symbol = holding["Symbol"]
            price_row = price_lookup.get(symbol)
            if not price_row:
                continue
            quantity = float(holding["Quantity"])
            start_position = quantity * price_row["Start Close"]
            end_position = quantity * price_row["End Close"]
            change = end_position - start_position
            return_pct = ((change / start_position) * 100) if start_position else 0.0

            rows.append(
                {
                    "Symbol": symbol,
                    "Quantity": quantity,
                    "Start Close": price_row["Start Close"],
                    "End Close": price_row["End Close"],
                    "Start Value": start_position,
                    "End Value": end_position,
                    "Change": change,
                    "Return %": return_pct,
                }
            )
            start_value += start_position
            end_value += end_position
            total_change += change

        rows.sort(key=lambda row: row["Change"], reverse=True)
        weekly_return = ((end_value - start_value) / start_value) * 100 if start_value else 0.0
        reports.append(
            {
                "Account": account,
                "Rows": rows,
                "Start Value": start_value,
                "End Value": end_value,
                "Change": total_change,
                "Return %": weekly_return,
                "Winner": rows[0]["Symbol"] if rows else "",
                "Loser": rows[-1]["Symbol"] if rows else "",
            }
        )
    return reports


def metric_card(label, value, tone="neutral"):
    return f"""
    <div class="metric-card {tone}">
      <div class="metric-label">{html.escape(label)}</div>
      <div class="metric-value">{html.escape(value)}</div>
    </div>
    """


def build_summary_cards(reports, start_date, end_date):
    aggregate_report = next((report for report in reports if report["Account"] == AGGREGATE_ACCOUNT_NAME), None)
    if aggregate_report is None:
        overall_start = sum(report["Start Value"] for report in reports)
        overall_end = sum(report["End Value"] for report in reports)
        overall_change = overall_end - overall_start
        overall_return = ((overall_change / overall_start) * 100) if overall_start else 0.0
    else:
        overall_start = aggregate_report["Start Value"]
        overall_end = aggregate_report["End Value"]
        overall_change = aggregate_report["Change"]
        overall_return = aggregate_report["Return %"]
    best_account = max(reports, key=lambda report: report["Return %"]) if reports else None
    worst_account = min(reports, key=lambda report: report["Return %"]) if reports else None

    cards = [
        metric_card("Week", f"{start_date} to {end_date}"),
        metric_card("Coverage", f"{len(reports)} accounts"),
        metric_card("Aggregate Start", format_currency(overall_start)),
        metric_card("Aggregate End", format_currency(overall_end)),
        metric_card("Aggregate Change", format_currency(overall_change), "positive" if overall_change >= 0 else "negative"),
        metric_card("Aggregate Return", format_percent(overall_return), "positive" if overall_return >= 0 else "negative"),
        metric_card("Best Account", best_account["Account"] if best_account else ""),
        metric_card("Worst Account", worst_account["Account"] if worst_account else ""),
    ]
    return "\n".join(cards)


def build_account_overview(reports):
    rows = []
    for report in reports:
        rows.append(
            f"""
            <tr>
              <td class="ticker">{html.escape(report['Account'])}</td>
              <td>{html.escape(format_currency(report['Start Value']))}</td>
              <td>{html.escape(format_currency(report['End Value']))}</td>
              <td class="{'positive' if report['Change'] >= 0 else 'negative'}">{html.escape(format_currency(report['Change']))}</td>
              <td class="{'positive' if report['Return %'] >= 0 else 'negative'}">{html.escape(format_percent(report['Return %']))}</td>
              <td>{html.escape(report['Winner'])}</td>
              <td>{html.escape(report['Loser'])}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def build_account_sections(reports):
    sections = []
    for report in reports:
        rows_html = []
        for row in report["Rows"]:
            rows_html.append(
                f"""
                <tr>
                  <td class="ticker">{html.escape(row['Symbol'])}</td>
                  <td>{html.escape(format_number(row['Quantity'], 0))}</td>
                  <td>{html.escape(format_currency(row['Start Close'], 2))}</td>
                  <td>{html.escape(format_currency(row['End Close'], 2))}</td>
                  <td>{html.escape(format_currency(row['Start Value']))}</td>
                  <td>{html.escape(format_currency(row['End Value']))}</td>
                  <td class="{'positive' if row['Change'] >= 0 else 'negative'}">{html.escape(format_currency(row['Change']))}</td>
                  <td class="{'positive' if row['Return %'] >= 0 else 'negative'}">{html.escape(format_percent(row['Return %']))}</td>
                </tr>
                """
            )

        sections.append(
            f"""
            <section class="section">
              <h2>{html.escape(report['Account'])}</h2>
              <div class="section-copy">Weekly mark-to-market change based on holding quantities and Yahoo Finance closing prices.</div>
              <div class="mini-metrics">
                {metric_card("Start", format_currency(report["Start Value"]))}
                {metric_card("End", format_currency(report["End Value"]))}
                {metric_card("Weekly P/L", format_currency(report["Change"]), "positive" if report["Change"] >= 0 else "negative")}
                {metric_card("Return", format_percent(report["Return %"]), "positive" if report["Return %"] >= 0 else "negative")}
              </div>
              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Qty</th>
                      <th>Start Close</th>
                      <th>End Close</th>
                      <th>Start Value</th>
                      <th>End Value</th>
                      <th>Change</th>
                      <th>Return</th>
                    </tr>
                  </thead>
                  <tbody>
                    {''.join(rows_html)}
                  </tbody>
                </table>
              </div>
            </section>
            """
        )
    return "\n".join(sections)


def render_html(reports, start_date, end_date):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_cards = build_summary_cards(reports, start_date, end_date)
    account_overview = build_account_overview(reports)
    account_sections = build_account_sections(reports)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Weekly Portfolio Report</title>
  <style>
    :root {{
      --paper: #f6f1e7;
      --ink: #12161d;
      --muted: #5a6472;
      --navy: #16263a;
      --gold: #b8945b;
      --line: rgba(18, 22, 29, 0.12);
      --panel: rgba(255, 255, 255, 0.68);
      --green: #146c43;
      --red: #9f2d2d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(184, 148, 91, 0.2), transparent 28%),
        linear-gradient(180deg, #efe4d0 0%, var(--paper) 35%, #f8f5ee 100%);
      font-family: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif;
    }}
    .page {{ width: min(1440px, calc(100vw - 48px)); margin: 32px auto 48px; }}
    .hero {{
      padding: 36px 40px 30px;
      border: 1px solid var(--line);
      background: linear-gradient(135deg, rgba(22, 38, 58, 0.96), rgba(18, 22, 29, 0.96));
      color: #f7f2e8;
      border-radius: 24px;
      box-shadow: 0 24px 70px rgba(14, 18, 24, 0.18);
    }}
    .eyebrow {{ font-size: 12px; letter-spacing: 0.22em; text-transform: uppercase; color: rgba(247, 242, 232, 0.68); margin-bottom: 14px; }}
    h1 {{ margin: 0; font-family: "Iowan Old Style", Georgia, serif; font-size: clamp(36px, 5vw, 58px); font-weight: 700; line-height: 0.95; letter-spacing: -0.03em; }}
    .subhead {{ margin-top: 16px; max-width: 860px; color: rgba(247, 242, 232, 0.8); font-size: 16px; line-height: 1.6; }}
    .timestamp {{ margin-top: 18px; color: rgba(247, 242, 232, 0.6); font-size: 13px; }}
    .metrics, .mini-metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 24px; }}
    .metric-card {{ min-height: 110px; padding: 18px; border-radius: 18px; background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); }}
    .metric-card.positive {{ box-shadow: inset 0 0 0 1px rgba(20,108,67,0.18); }}
    .metric-card.negative {{ box-shadow: inset 0 0 0 1px rgba(159,45,45,0.18); }}
    .metric-label {{ color: rgba(247,242,232,0.64); text-transform: uppercase; letter-spacing: 0.12em; font-size: 11px; }}
    .metric-value {{ margin-top: 10px; font-size: 28px; line-height: 1; font-weight: 700; letter-spacing: -0.03em; }}
    .section {{ margin-top: 24px; padding: 24px; border-radius: 24px; background: var(--panel); border: 1px solid var(--line); box-shadow: 0 10px 40px rgba(26,32,44,0.08); }}
    .section h2 {{ margin: 0 0 12px; font-family: "Iowan Old Style", Georgia, serif; font-size: 28px; color: var(--navy); }}
    .section-copy {{ margin-bottom: 16px; color: var(--muted); font-size: 14px; line-height: 1.6; }}
    .table-wrap {{ overflow: auto; max-height: 72vh; border-radius: 18px; border: 1px solid var(--line); background: rgba(255,255,255,0.55); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    thead th {{ position: sticky; top: 0; background: #f4ecdf; color: var(--navy); text-transform: uppercase; letter-spacing: 0.08em; font-size: 10px; z-index: 1; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: right; white-space: nowrap; }}
    th:first-child, td:first-child {{ text-align: left; position: sticky; left: 0; background: inherit; }}
    tbody tr:nth-child(odd) {{ background: rgba(255,255,255,0.34); }}
    tbody tr:hover {{ background: rgba(184,148,91,0.08); }}
    .ticker {{ font-weight: 700; color: var(--navy); }}
    .negative {{ color: var(--red); }}
    .positive {{ color: var(--green); }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="eyebrow">DivGrow Weekly Close</div>
      <h1>Weekly Portfolio Report</h1>
      <div class="subhead">End-of-week account performance from the prior weekly close to the latest available close, based on current holdings and Yahoo Finance market prices.</div>
      <div class="timestamp">Generated {html.escape(generated_at)}</div>
      <div class="metrics">{summary_cards}</div>
    </section>
    <section class="section">
      <h2>Account Overview</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Account</th>
              <th>Start Value</th>
              <th>End Value</th>
              <th>Change</th>
              <th>Return</th>
              <th>Top Winner</th>
              <th>Top Loser</th>
            </tr>
          </thead>
          <tbody>{account_overview}</tbody>
        </table>
      </div>
    </section>
    {account_sections}
  </main>
</body>
</html>"""


def main():
    holdings_rows = load_csv_rows(HOLDINGS_CSV)
    accounts = prepare_accounts(holdings_rows)
    tsx_symbols = load_tsx_symbols()
    symbols = {holding["Symbol"] for holdings in accounts.values() for holding in holdings}
    price_lookup = collect_price_data(symbols, tsx_symbols)
    if not price_lookup:
        raise SystemExit("No weekly price data collected.")

    reports = build_account_reports(accounts, price_lookup)
    first_symbol = next(iter(price_lookup.values()))
    start_date = first_symbol["Start Date"]
    end_date = first_symbol["End Date"]

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as html_file:
        html_file.write(render_html(reports, start_date, end_date))

    print(OUTPUT_HTML)


if __name__ == "__main__":
    main()
