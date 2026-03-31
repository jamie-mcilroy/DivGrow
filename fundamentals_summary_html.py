import csv
import html
import os
from datetime import datetime


INPUT_CSV = "data/fundamentals_summary.csv"
OUTPUT_HTML = "output/fundamentals_summary.html"
HEADER_TOOLTIPS = {
    "Ticker": "Stock symbol from configs/symbols.json.",
    "Current Price": "Latest market price pulled from Yahoo Finance.",
    "BG3": "Ben Graham value using the 3-year average EPS.",
    "BG5": "Ben Graham value using the 5-year average EPS.",
    "BG10": "Ben Graham value using the 10-year average EPS.",
    "Δ BG5": "Percent difference between Current Price and BG5: ((Current Price - BG5) / BG5) * 100.",
    "Yield5": "Historic 5-year average annualized dividend yield based on ex-dividend-date pricing.",
    "Growth5": "Average annual dividend growth rate over the last 5 years.",
    "Last Growth": "Most recent year-over-year dividend growth rate.",
    "Avg Growth 3Y %": "Average annual dividend growth rate over the last 3 years.",
    "Avg Growth 5Y %": "Average annual dividend growth rate over the last 5 years.",
    "Avg Yield 3Y": "Historic 3-year average annualized dividend yield based on ex-dividend-date pricing.",
    "Avg Yield 10Y": "Historic 10-year average annualized dividend yield based on ex-dividend-date pricing.",
    "BVPS Year": "Year of the balance sheet used for the BVPS calculation.",
    "BVPS": "Book value per share from Yahoo Finance balance sheet data.",
    "Avg EPS 3Y": "Average annual EPS over the last 3 years.",
    "Avg EPS 5Y": "Average annual EPS over the last 5 years.",
    "Avg EPS 10Y": "Average annual EPS over the last 10 years.",
}


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


def metric_card(label, value, tone="neutral"):
    return f"""
    <div class="metric-card {tone}">
      <div class="metric-label">{html.escape(label)}</div>
      <div class="metric-value">{html.escape(value)}</div>
    </div>
    """


def build_summary(rows):
    deltas = [to_float(row.get("Δ BG5")) for row in rows]
    deltas = [value for value in deltas if value is not None]
    yield5_values = [to_float(row.get("Yield5")) for row in rows]
    yield5_values = [value for value in yield5_values if value is not None]
    growth5_values = [to_float(row.get("Growth5")) for row in rows]
    growth5_values = [value for value in growth5_values if value is not None]

    cheapest = rows[0] if rows else None
    richest = rows[-1] if rows else None

    cards = [
        metric_card("Coverage", f"{len(rows)} symbols"),
        metric_card("Average Δ BG5", f"{sum(deltas) / len(deltas):.2f}" if deltas else "", "negative" if deltas and (sum(deltas) / len(deltas)) < 0 else "positive"),
        metric_card("Average Yield5", f"{sum(yield5_values) / len(yield5_values):.2f}" if yield5_values else ""),
        metric_card("Average Growth5", f"{sum(growth5_values) / len(growth5_values):.2f}" if growth5_values else ""),
        metric_card("Most Discounted", cheapest["Ticker"] if cheapest else ""),
        metric_card("Most Premium", richest["Ticker"] if richest else ""),
    ]
    return "\n".join(cards)


def build_highlights(rows):
    top_rows = rows[:12]
    items = []
    for row in top_rows:
        current_yield = ""
        year_yield_columns = [column for column in row.keys() if column.startswith("Y") and column[1:].isdigit()]
        if year_yield_columns:
            current_yield = row.get(sorted(year_yield_columns)[-1], "")
        items.append(
            f"""
            <tr>
              <td>{html.escape(row.get("Ticker", ""))}</td>
              <td>{html.escape(format_number(row.get("Current Price")))}</td>
              <td>{html.escape(format_number(row.get("BG5")))}</td>
              <td class="{delta_class(row.get('Δ BG5'))}">{html.escape(format_number(row.get("Δ BG5")))}</td>
              <td>{html.escape(format_number(current_yield))}</td>
              <td>{html.escape(format_number(row.get("Yield5")))}</td>
              <td>{html.escape(format_number(row.get("Growth5")))}</td>
            </tr>
            """
        )
    return "\n".join(items)


def delta_class(value):
    number = to_float(value)
    if number is None:
        return ""
    if number < 0:
        return "negative"
    if number > 0:
        return "positive"
    return "neutral"


def render_cell(column, value):
    if column == "Ticker":
        return f'<td class="ticker">{html.escape(value)}</td>'

    if column in {"Current Price", "BG3", "BG5", "BG10", "BVPS", "Avg EPS 3Y", "Avg EPS 5Y", "Avg EPS 10Y"}:
        return f"<td>{html.escape(format_number(value))}</td>"

    if column in {"Δ BG5", "Yield5", "Growth5", "Last Growth", "Avg Growth 3Y %", "Avg Growth 5Y %", "Avg Yield 3Y", "Avg Yield 10Y"} or (column.startswith("Y") and column[1:].isdigit()):
        return f'<td class="{delta_class(value) if column == "Δ BG5" else ""}">{html.escape(format_number(value))}</td>'

    if column.isdigit():
        return f"<td>{html.escape(format_number(value, 3))}</td>"

    return f"<td>{html.escape(value)}</td>"


def build_table(rows):
    headers = rows[0].keys()
    header_html = "".join(
        f'<th title="{html.escape(HEADER_TOOLTIPS.get(column, year_tooltip(column)))}">{html.escape(column)}</th>'
        for column in headers
    )
    body_rows = []
    for row in rows:
        cells = "".join(render_cell(column, row.get(column, "")) for column in headers)
        body_rows.append(f"<tr>{cells}</tr>")
    return header_html, "\n".join(body_rows)


def year_tooltip(column):
    if column.isdigit():
        return f"Annual dividend total for {column}."
    if column.startswith("Y") and column[1:].isdigit():
        return f"Dividend yield using the {column[1:]} annual dividend and the current price."
    return column


def render_html(rows):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    header_html, body_html = build_table(rows)
    summary_html = build_summary(rows)
    highlights_html = build_highlights(rows)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fundamentals Summary</title>
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
    .page {{
      width: min(1440px, calc(100vw - 48px));
      margin: 32px auto 48px;
    }}
    .hero {{
      padding: 36px 40px 30px;
      border: 1px solid var(--line);
      background: linear-gradient(135deg, rgba(22, 38, 58, 0.96), rgba(18, 22, 29, 0.96));
      color: #f7f2e8;
      border-radius: 24px;
      box-shadow: 0 24px 70px rgba(14, 18, 24, 0.18);
    }}
    .eyebrow {{
      font-size: 12px;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: rgba(247, 242, 232, 0.68);
      margin-bottom: 14px;
    }}
    h1 {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
      font-size: clamp(36px, 5vw, 58px);
      font-weight: 700;
      line-height: 0.95;
      letter-spacing: -0.03em;
    }}
    .subhead {{
      margin-top: 16px;
      max-width: 820px;
      color: rgba(247, 242, 232, 0.8);
      font-size: 16px;
      line-height: 1.6;
    }}
    .timestamp {{
      margin-top: 18px;
      color: rgba(247, 242, 232, 0.6);
      font-size: 13px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-top: 24px;
    }}
    .metric-card {{
      min-height: 120px;
      padding: 18px 18px 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.12);
      backdrop-filter: blur(12px);
    }}
    .metric-card.positive {{ box-shadow: inset 0 0 0 1px rgba(20, 108, 67, 0.18); }}
    .metric-card.negative {{ box-shadow: inset 0 0 0 1px rgba(159, 45, 45, 0.18); }}
    .metric-label {{
      color: rgba(247, 242, 232, 0.64);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 11px;
    }}
    .metric-value {{
      margin-top: 10px;
      font-size: 30px;
      line-height: 1;
      font-weight: 700;
      letter-spacing: -0.03em;
    }}
    .section {{
      margin-top: 24px;
      padding: 24px;
      border-radius: 24px;
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: 0 10px 40px rgba(26, 32, 44, 0.08);
    }}
    .section h2 {{
      margin: 0 0 16px;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
      font-size: 28px;
      letter-spacing: -0.02em;
      color: var(--navy);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    thead th {{
      position: sticky;
      top: 0;
      background: #f4ecdf;
      color: var(--navy);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 10px;
      z-index: 1;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: right;
      white-space: nowrap;
    }}
    th:first-child, td:first-child {{
      text-align: left;
      position: sticky;
      left: 0;
      background: inherit;
    }}
    tbody tr:nth-child(odd) {{
      background: rgba(255, 255, 255, 0.34);
    }}
    tbody tr:hover {{
      background: rgba(184, 148, 91, 0.08);
    }}
    .table-wrap {{
      overflow: auto;
      max-height: 72vh;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.55);
    }}
    .ticker {{
      font-weight: 700;
      color: var(--navy);
      letter-spacing: 0.03em;
    }}
    .negative {{ color: var(--red); }}
    .positive {{ color: var(--green); }}
    .footer-note {{
      margin-top: 14px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }}
    @media (max-width: 900px) {{
      .page {{ width: calc(100vw - 24px); margin: 12px auto 24px; }}
      .hero, .section {{ padding: 18px; border-radius: 18px; }}
      h1 {{ font-size: 36px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="eyebrow">DivGrow Fundamental Screen</div>
      <h1>Street Sheet</h1>
      <div class="subhead">
        Consolidated view of Graham valuation, current pricing, historic dividend yield, and dividend growth for the active symbol universe.
      </div>
      <div class="timestamp">Generated {html.escape(generated_at)}</div>
      <div class="metrics">
        {summary_html}
      </div>
    </section>

    <section class="section">
      <h2>Deep Discount Watchlist</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th title="{html.escape(HEADER_TOOLTIPS['Ticker'])}">Ticker</th>
              <th title="{html.escape(HEADER_TOOLTIPS['Current Price'])}">Current Price</th>
              <th title="{html.escape(HEADER_TOOLTIPS['BG5'])}">BG5</th>
              <th title="{html.escape(HEADER_TOOLTIPS['Δ BG5'])}">Δ BG5</th>
              <th title="Dividend yield using the current-year annual dividend and the current price.">Current Yield</th>
              <th title="{html.escape(HEADER_TOOLTIPS['Yield5'])}">Yield5</th>
              <th title="{html.escape(HEADER_TOOLTIPS['Growth5'])}">Growth5</th>
            </tr>
          </thead>
          <tbody>
            {highlights_html}
          </tbody>
        </table>
      </div>
      <div class="footer-note">
        Rows are ordered by Δ BG5 ascending, so the most discounted names versus BG5 rise to the top.
      </div>
    </section>

    <section class="section">
      <h2>Full Fundamentals Table</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>{header_html}</tr>
          </thead>
          <tbody>
            {body_html}
          </tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>
"""


def main():
    rows = load_rows()
    if not rows:
        raise SystemExit("No rows found in data/fundamentals_summary.csv")

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as html_file:
        html_file.write(render_html(rows))

    print(OUTPUT_HTML)


if __name__ == "__main__":
    main()
