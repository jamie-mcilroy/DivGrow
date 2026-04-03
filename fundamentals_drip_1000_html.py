import csv
import html
import os
from datetime import datetime


INPUT_CSV = "data/fundamentals_summary.csv"
OUTPUT_HTML = "output/fundamentals_drip_1000.html"
INITIAL_INVESTMENT = 1000.0
YEARS = 20


def load_rows(path=INPUT_CSV):
    with open(path, "r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value, decimals=2):
    number = to_float(value)
    if number is None:
        return ""
    return f"{number:,.{decimals}f}"


def format_currency(value, decimals=0):
    number = to_float(value)
    if number is None:
        return ""
    return f"${number:,.{decimals}f}"


def get_current_yield_column(fieldnames):
    year_columns = sorted(column for column in fieldnames if column.startswith("Y") and column[1:].isdigit())
    if not year_columns:
        raise ValueError("No current yield columns found in fundamentals_summary.csv")
    return year_columns[-1]


def project_row(row, current_yield_column):
    price = to_float(row.get("Current Price"))
    current_yield = to_float(row.get(current_yield_column))
    growth = to_float(row.get("Growth5"))

    if price is None or price <= 0 or current_yield is None or growth is None:
        return None

    yield_rate = current_yield / 100.0
    growth_rate = growth / 100.0
    shares = INITIAL_INVESTMENT / price
    annual_dividend_per_share = price * yield_rate
    current_price = price

    yearly_values = []
    for year_index in range(1, YEARS + 1):
        annual_dividend_per_share *= 1 + growth_rate
        current_price *= 1 + growth_rate
        dividend_cash = shares * annual_dividend_per_share
        new_shares = dividend_cash / current_price if current_price else 0.0
        shares += new_shares
        portfolio_value = shares * current_price
        yearly_values.append(
            {
                "Year Offset": year_index,
                "Price": current_price,
                "Dividend/Share": annual_dividend_per_share,
                "Shares": shares,
                "Dividend Cash": dividend_cash,
                "Value": portfolio_value,
            }
        )

    final_year = yearly_values[-1]
    return {
        "Ticker": row.get("Ticker", ""),
        "Current Price": price,
        "Current Yield": current_yield,
        "Growth5": growth,
        "BG5": to_float(row.get("BG5")),
        "Δ BG5": to_float(row.get("Δ BG5")),
        "Final Value": final_year["Value"],
        "Final Shares": final_year["Shares"],
        "Final Dividend Cash": final_year["Dividend Cash"],
        "CAGR": ((final_year["Value"] / INITIAL_INVESTMENT) ** (1 / YEARS) - 1) * 100 if final_year["Value"] > 0 else None,
        "Trajectory": yearly_values,
    }


def project_rows(rows):
    current_yield_column = get_current_yield_column(rows[0].keys())
    projections = []
    for row in rows:
        projection = project_row(row, current_yield_column)
        if projection is not None:
            projections.append(projection)
    projections.sort(key=lambda item: item["Final Value"], reverse=True)
    return projections, current_yield_column


def metric_card(label, value):
    return f"""
    <div class="metric-card">
      <div class="metric-label">{html.escape(label)}</div>
      <div class="metric-value">{html.escape(value)}</div>
    </div>
    """


def build_summary(projections):
    if not projections:
        return ""
    avg_final_value = sum(item["Final Value"] for item in projections) / len(projections)
    avg_cagr = sum(item["CAGR"] for item in projections if item["CAGR"] is not None) / len(projections)
    cards = [
        metric_card("Coverage", f"{len(projections)} symbols"),
        metric_card("Starting Capital", format_currency(INITIAL_INVESTMENT)),
        metric_card("Average 20Y Value", format_currency(avg_final_value)),
        metric_card("Average CAGR", f"{avg_cagr:.2f}%"),
        metric_card("Top Outcome", projections[0]["Ticker"]),
        metric_card("Top 20Y Value", format_currency(projections[0]["Final Value"])),
    ]
    return "\n".join(cards)


def build_watchlist(projections):
    rows = []
    for item in projections[:15]:
        rows.append(
            f"""
            <tr>
              <td>{html.escape(item['Ticker'])}</td>
              <td>{html.escape(format_number(item['Current Yield']))}%</td>
              <td>{html.escape(format_number(item['Growth5']))}%</td>
              <td>{html.escape(format_currency(item['Final Value']))}</td>
              <td>{html.escape(format_number(item['Final Shares'], 2))}</td>
              <td>{html.escape(format_currency(item['Final Dividend Cash']))}</td>
              <td>{html.escape(format_number(item['CAGR']))}%</td>
            </tr>
            """
        )
    return "\n".join(rows)


def build_table(projections):
    headers = ["Ticker", "Current Price", "Current Yield", "Growth5", "BG5", "Δ BG5", "20Y Value", "20Y Shares", "20Y Income", "CAGR"]
    header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    rows = []
    for item in projections:
        rows.append(
            f"""
            <tr>
              <td class="ticker">{html.escape(item['Ticker'])}</td>
              <td>{html.escape(format_currency(item['Current Price'], 2))}</td>
              <td>{html.escape(format_number(item['Current Yield']))}%</td>
              <td>{html.escape(format_number(item['Growth5']))}%</td>
              <td>{html.escape(format_currency(item['BG5'], 2))}</td>
              <td class="{'negative' if (item['Δ BG5'] or 0) < 0 else 'positive'}">{html.escape(format_number(item['Δ BG5']))}%</td>
              <td>{html.escape(format_currency(item['Final Value']))}</td>
              <td>{html.escape(format_number(item['Final Shares'], 2))}</td>
              <td>{html.escape(format_currency(item['Final Dividend Cash']))}</td>
              <td>{html.escape(format_number(item['CAGR']))}%</td>
            </tr>
            """
        )
    return header_html, "\n".join(rows)


def render_html(projections, current_yield_column):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_html = build_summary(projections)
    watchlist_html = build_watchlist(projections)
    header_html, body_html = build_table(projections)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>$1,000 DRIP Projection</title>
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
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 24px; }}
    .metric-card {{ min-height: 120px; padding: 18px 18px 16px; border-radius: 18px; background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); }}
    .metric-label {{ color: rgba(247,242,232,0.64); text-transform: uppercase; letter-spacing: 0.12em; font-size: 11px; }}
    .metric-value {{ margin-top: 10px; font-size: 30px; line-height: 1; font-weight: 700; letter-spacing: -0.03em; }}
    .section {{ margin-top: 24px; padding: 24px; border-radius: 24px; background: var(--panel); border: 1px solid var(--line); box-shadow: 0 10px 40px rgba(26,32,44,0.08); }}
    .section h2 {{ margin: 0 0 16px; font-family: "Iowan Old Style", Georgia, serif; font-size: 28px; color: var(--navy); }}
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
    .footer-note {{ margin-top: 14px; color: var(--muted); font-size: 12px; line-height: 1.6; }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="eyebrow">DivGrow Fundamental Scenario</div>
      <h1>$1,000 DRIP Outlook</h1>
      <div class="subhead">Scenario analysis for investing ${INITIAL_INVESTMENT:,.0f} today in each symbol, reinvesting all dividends for {YEARS} years. This model uses the latest current yield column ({html.escape(current_yield_column)}), the 5-year average dividend growth rate, and a constant-yield assumption so share price rises with dividend/share growth.</div>
      <div class="timestamp">Generated {html.escape(generated_at)}</div>
      <div class="metrics">{summary_html}</div>
    </section>
    <section class="section">
      <h2>Top 20-Year Outcomes</h2>
      <div class="section-copy">Highest ending portfolio values from a ${INITIAL_INVESTMENT:,.0f} starting investment with DRIP enabled.</div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Current Yield</th>
              <th>Growth5</th>
              <th>20Y Value</th>
              <th>20Y Shares</th>
              <th>20Y Income</th>
              <th>CAGR</th>
            </tr>
          </thead>
          <tbody>{watchlist_html}</tbody>
        </table>
      </div>
      <div class="footer-note">Assumption: price grows with dividend/share so the current yield stays constant through time.</div>
    </section>
    <section class="section">
      <h2>Full Projection Table</h2>
      <div class="table-wrap">
        <table>
          <thead><tr>{header_html}</tr></thead>
          <tbody>{body_html}</tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>"""


def main():
    rows = load_rows()
    if not rows:
        raise SystemExit("No rows found in data/fundamentals_summary.csv")
    projections, current_yield_column = project_rows(rows)
    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as html_file:
        html_file.write(render_html(projections, current_yield_column))
    print(OUTPUT_HTML)


if __name__ == "__main__":
    main()
