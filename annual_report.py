import csv
import html
import os
import subprocess
import sys
import tempfile
from datetime import date


REPORT_DIR = "reports"
HOLDINGS_CSV = "configs/Holdings.csv"
SUMMARY_CSV = "data/dividends_10y_pivot.csv"
INCOME_DIR = "output/account_drip_income_projections"
BALANCE_DIR = "output/account_balance_projections"
PERSONAL_ACCOUNTS = ["MichelleCash", "MichelleTFSA", "MichelleRSP"]
RETIREMENT_ACCOUNT = "MasterRetirement"
CHROMIUM_PATH = "/opt/homebrew/bin/chromium"


def load_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def parse_money(value):
    return float(value.replace(",", "").replace("$", "").strip())


def parse_percent(value):
    cleaned = value.replace("%", "").strip()
    return float(cleaned) / 100 if cleaned else 0.0


def format_currency(value):
    return f"${value:,.0f}"


def format_decimal_percent(value):
    return f"{value * 100:.1f}%"


def get_year_columns(fieldnames):
    return sorted(int(name) for name in fieldnames if name.isdigit())


def read_account_projection(path):
    rows = load_csv_rows(path)
    if not rows:
        raise ValueError(f"No rows found in {path}")

    year_columns = get_year_columns(rows[0].keys())
    symbol_rows = [row for row in rows if row.get("Symbol") != "TOTAL"]
    total_row = next((row for row in rows if row.get("Symbol") == "TOTAL"), None)
    return {"rows": symbol_rows, "total": total_row, "years": year_columns}


def build_holdings_lookup():
    lookup = {}
    for row in load_csv_rows(HOLDINGS_CSV):
        account = row["Account"].strip()
        symbol = row["Symbol"].strip()
        lookup[(account, symbol)] = row
    return lookup


def build_summary_lookup():
    return {row["Ticker"]: row for row in load_csv_rows(SUMMARY_CSV)}


def account_paths(account_name):
    safe = account_name
    return {
        "income": os.path.join(INCOME_DIR, f"{safe}_drip_income_20y.csv"),
        "balance": os.path.join(BALANCE_DIR, f"{safe}_balance_20y.csv"),
    }


def aggregate_personal_totals(account_names):
    income_total = 0.0
    balance_total = 0.0
    future_income = {}
    future_balance = {}

    for account in account_names:
        income_projection = read_account_projection(account_paths(account)["income"])
        balance_projection = read_account_projection(account_paths(account)["balance"])

        income_total += sum(parse_money(row["Price"]) * 0 for row in [])  # no-op for clarity
        if income_projection["total"] is not None:
            for year in income_projection["years"]:
                future_income[year] = future_income.get(year, 0.0) + parse_money(income_projection["total"][str(year)])

        if balance_projection["total"] is not None:
            balance_total += parse_money(balance_projection["total"]["Current Balance"])
            for year in balance_projection["years"]:
                future_balance[year] = future_balance.get(year, 0.0) + parse_money(balance_projection["total"][str(year)])

    return {
        "current_balance": balance_total,
        "future_income": future_income,
        "future_balance": future_balance,
    }


def build_top_holdings(holdings_lookup, summary_lookup):
    top_rows = []
    for account in PERSONAL_ACCOUNTS:
        for (row_account, symbol), holding in holdings_lookup.items():
            if row_account != account:
                continue
            quantity = float(holding["Quantity"])
            price = float(holding["Price"]) if holding["Price"] else 0.0
            balance = quantity * price
            summary = summary_lookup.get(symbol, {})
            top_rows.append(
                {
                    "account": account,
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                    "balance": balance,
                    "yield": float(holding["Yield"]) if holding["Yield"] else 0.0,
                    "last_growth": float(summary.get("Last Growth") or 0.0),
                    "dividend_2026": float(summary.get("2026") or 0.0),
                }
            )

    top_rows.sort(key=lambda row: row["balance"], reverse=True)
    return top_rows[:10]


def line_chart_svg(series, width=880, height=240, color="#1d6f5f"):
    items = [(int(year), float(value)) for year, value in series.items()]
    if not items:
        return ""

    left_pad = 56
    right_pad = 20
    top_pad = 18
    bottom_pad = 28
    chart_width = width - left_pad - right_pad
    chart_height = height - top_pad - bottom_pad

    values = [value for _, value in items]
    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        min_value = 0

    def x_pos(index):
        if len(items) == 1:
            return left_pad + chart_width / 2
        return left_pad + (chart_width * index / (len(items) - 1))

    def y_pos(value):
        if max_value == min_value:
            return top_pad + chart_height / 2
        ratio = (value - min_value) / (max_value - min_value)
        return top_pad + chart_height - (ratio * chart_height)

    points = " ".join(f"{x_pos(idx):.1f},{y_pos(value):.1f}" for idx, (_, value) in enumerate(items))
    grid_lines = []
    for step in range(5):
        y = top_pad + chart_height * step / 4
        label_value = max_value - ((max_value - min_value) * step / 4)
        grid_lines.append(
            f'<line x1="{left_pad}" y1="{y:.1f}" x2="{width - right_pad}" y2="{y:.1f}" class="grid" />'
            f'<text x="{left_pad - 8}" y="{y + 4:.1f}" class="axis-label">{format_currency(label_value)}</text>'
        )

    x_labels = []
    for idx, (year, _) in enumerate(items):
        x = x_pos(idx)
        x_labels.append(f'<text x="{x:.1f}" y="{height - 6}" class="axis-label year-label">{year}</text>')

    return f"""
    <svg viewBox="0 0 {width} {height}" class="chart-svg" role="img" aria-label="Projection chart">
      <style>
        .grid {{ stroke: #d9e2dd; stroke-width: 1; }}
        .axis-label {{ fill: #5a675f; font-size: 11px; font-family: Georgia, serif; }}
        .year-label {{ text-anchor: middle; }}
        .line {{ fill: none; stroke: {color}; stroke-width: 3; }}
      </style>
      {''.join(grid_lines)}
      <polyline points="{points}" class="line" />
      {''.join(x_labels)}
    </svg>
    """


def metric_card(label, value, subtext=""):
    subtext_html = f'<div class="metric-sub">{html.escape(subtext)}</div>' if subtext else ""
    return f"""
    <div class="metric-card">
      <div class="metric-label">{html.escape(label)}</div>
      <div class="metric-value">{html.escape(value)}</div>
      {subtext_html}
    </div>
    """


def render_top_holdings_table(rows):
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(row['account'])}</td>"
            f"<td>{html.escape(row['symbol'])}</td>"
            f"<td>{row['quantity']:.0f}</td>"
            f"<td>{format_currency(row['price'])}</td>"
            f"<td>{format_currency(row['balance'])}</td>"
            f"<td>{format_decimal_percent(row['yield'])}</td>"
            f"<td>{format_decimal_percent(row['last_growth'])}</td>"
            f"<td>{row['dividend_2026']:.2f}</td>"
            "</tr>"
        )
    return (
        "<table class=\"data-table\">"
        "<thead><tr><th>Account</th><th>Symbol</th><th>Shares</th><th>Price</th><th>Balance</th><th>Yield</th><th>Last Growth</th><th>Dividend/Share</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def render_account_table(account_name, income_projection, balance_projection):
    year_targets = [income_projection["years"][0], income_projection["years"][4], income_projection["years"][9], income_projection["years"][-1]]
    headers = "".join(f"<th>{year}</th>" for year in year_targets)
    rows_html = []

    balance_rows = {row["Symbol"]: row for row in balance_projection["rows"]}

    for income_row in sorted(income_projection["rows"], key=lambda item: item["Symbol"]):
        symbol = income_row["Symbol"]
        balance_row = balance_rows.get(symbol, {})
        cells = []
        for year in year_targets:
            income_value = parse_money(income_row[str(year)])
            balance_value = parse_money(balance_row[str(year)]) if str(year) in balance_row else 0.0
            cells.append(f"<td>{format_currency(income_value)}<span class=\"cell-sub\">{format_currency(balance_value)}</span></td>")

        rows_html.append(
            "<tr>"
            f"<td>{html.escape(symbol)}</td>"
            f"<td>{income_row['Starting Quantity']}</td>"
            f"<td>{income_row['Yield']}</td>"
            f"<td>{income_row['Growth Rate Used']}</td>"
            + "".join(cells)
            + "</tr>"
        )

    total_income = income_projection["total"]
    total_balance = balance_projection["total"]
    total_cells = []
    for year in year_targets:
        income_value = parse_money(total_income[str(year)])
        balance_value = parse_money(total_balance[str(year)])
        total_cells.append(f"<td>{format_currency(income_value)}<span class=\"cell-sub\">{format_currency(balance_value)}</span></td>")

    rows_html.append(
        "<tr class=\"total-row\">"
        f"<td>{html.escape(account_name)} Total</td><td></td><td></td><td></td>"
        + "".join(total_cells)
        + "</tr>"
    )

    return (
        "<table class=\"data-table compact\">"
        "<thead><tr><th>Symbol</th><th>Shares</th><th>Yield</th><th>Growth</th>"
        f"{headers}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody></table>"
    )


def build_report_html():
    holdings_lookup = build_holdings_lookup()
    summary_lookup = build_summary_lookup()
    personal_totals = aggregate_personal_totals(PERSONAL_ACCOUNTS)
    retirement_income = read_account_projection(account_paths(RETIREMENT_ACCOUNT)["income"])
    retirement_balance = read_account_projection(account_paths(RETIREMENT_ACCOUNT)["balance"])

    report_date = date.today().strftime("%B %d, %Y")
    next_year = retirement_income["years"][0]
    year_10 = retirement_income["years"][9]
    year_20 = retirement_income["years"][-1]

    executive_cards = "".join(
        [
            metric_card("Michelle Personal Balance", format_currency(personal_totals["current_balance"])),
            metric_card("Master Retirement Balance", format_currency(parse_money(retirement_balance["total"]["Current Balance"]))),
            metric_card("Master Retirement Income", format_currency(parse_money(retirement_income["total"][str(next_year)])), f"Projected in {next_year}"),
            metric_card("10-Year Retirement Income", format_currency(parse_money(retirement_income["total"][str(year_10)])), f"Projected in {year_10}"),
            metric_card("20-Year Retirement Balance", format_currency(parse_money(retirement_balance["total"][str(year_20)])), f"Projected in {year_20}"),
            metric_card("Price Growth Assumption", "2.0%", "Conservative annual price growth"),
        ]
    )

    personal_balance_chart = line_chart_svg(personal_totals["future_balance"], color="#8b5e3c")
    retirement_income_chart = line_chart_svg({year: parse_money(retirement_income["total"][str(year)]) for year in retirement_income["years"]}, color="#1d6f5f")
    retirement_balance_chart = line_chart_svg({year: parse_money(retirement_balance["total"][str(year)]) for year in retirement_balance["years"]}, color="#0e4b7a")

    top_holdings_table = render_top_holdings_table(build_top_holdings(holdings_lookup, summary_lookup))
    account_sections = []
    for account in PERSONAL_ACCOUNTS + [RETIREMENT_ACCOUNT]:
        income_projection = read_account_projection(account_paths(account)["income"])
        balance_projection = read_account_projection(account_paths(account)["balance"])
        account_sections.append(
            f"""
            <section class="panel break-avoid">
              <div class="section-kicker">Account outlook</div>
              <h2>{html.escape(account)}</h2>
              <p class="section-note">Primary cells show projected dividend income. Smaller figures underneath show projected account balance for the same year.</p>
              {render_account_table(account, income_projection, balance_projection)}
            </section>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Michelle Annual Dividend Report</title>
  <style>
    :root {{
      --ink: #1a1f1c;
      --muted: #5a675f;
      --paper: #f6f1e8;
      --panel: #fffdfa;
      --line: #d9d2c4;
      --navy: #0e4b7a;
      --green: #1d6f5f;
      --gold: #a57a3f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(165,122,63,0.12), transparent 28%),
        linear-gradient(180deg, #f8f4ec 0%, #f1ebdf 100%);
    }}
    .report {{
      width: 980px;
      margin: 0 auto;
      padding: 42px 42px 56px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(14,75,122,0.96), rgba(29,111,95,0.92));
      color: white;
      border-radius: 24px;
      padding: 42px;
      box-shadow: 0 20px 40px rgba(30,40,36,0.12);
    }}
    .eyebrow {{
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      opacity: 0.82;
      margin-bottom: 14px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 42px;
      line-height: 1.05;
      font-weight: 600;
    }}
    .hero p {{
      margin: 0;
      max-width: 720px;
      font-size: 18px;
      line-height: 1.55;
      color: rgba(255,255,255,0.88);
    }}
    .meta {{
      margin-top: 18px;
      font-size: 14px;
      color: rgba(255,255,255,0.75);
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 18px;
      margin: 28px 0 26px;
    }}
    .metric-card {{
      background: var(--panel);
      border: 1px solid rgba(14,75,122,0.08);
      border-radius: 18px;
      padding: 18px 20px;
      box-shadow: 0 14px 30px rgba(33,36,31,0.06);
    }}
    .metric-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
      margin-bottom: 10px;
    }}
    .metric-value {{
      font-size: 30px;
      color: var(--navy);
      line-height: 1.1;
    }}
    .metric-sub {{
      margin-top: 8px;
      font-size: 13px;
      color: var(--muted);
    }}
    .panel {{
      background: var(--panel);
      border-radius: 22px;
      margin-top: 24px;
      padding: 28px;
      box-shadow: 0 14px 28px rgba(33,36,31,0.05);
      border: 1px solid rgba(14,75,122,0.08);
    }}
    .section-kicker {{
      color: var(--gold);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
      margin-bottom: 8px;
    }}
    h2 {{
      margin: 0 0 10px;
      font-size: 28px;
      color: var(--navy);
    }}
    .section-note {{
      color: var(--muted);
      margin: 0 0 18px;
      line-height: 1.5;
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 18px;
    }}
    .chart-card {{
      background: #fcfaf5;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
    }}
    .chart-card h3 {{
      margin: 0 0 6px;
      font-size: 18px;
      color: var(--ink);
    }}
    .chart-card p {{
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 14px;
    }}
    .chart-svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    .data-table th {{
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .data-table td {{
      padding: 12px 10px;
      border-bottom: 1px solid #eee5d7;
      vertical-align: top;
    }}
    .compact td, .compact th {{
      padding: 10px 8px;
      font-size: 13px;
    }}
    .cell-sub {{
      display: block;
      margin-top: 4px;
      font-size: 11px;
      color: var(--muted);
    }}
    .total-row td {{
      font-weight: 700;
      background: #f4efe5;
    }}
    .assumptions {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px 24px;
      margin-top: 6px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }}
    .break-avoid {{
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    @media print {{
      body {{ background: white; }}
      .report {{ width: auto; margin: 0; padding: 0; }}
      .panel, .hero, .metric-card {{ box-shadow: none; }}
    }}
  </style>
</head>
<body>
  <div class="report">
    <section class="hero break-avoid">
      <div class="eyebrow">Annual Dividend Outlook</div>
      <h1>Michelle Annual Dividend Report</h1>
      <p>This report summarizes current balances, projected dividend income, and long-range balance growth using the portfolio’s current holdings, dividend growth history, DRIP assumptions, and a conservative annual price-growth assumption.</p>
      <div class="meta">Prepared {report_date}</div>
    </section>

    <section class="metrics break-avoid">
      {executive_cards}
    </section>

    <section class="panel break-avoid">
      <div class="section-kicker">Executive summary</div>
      <h2>What The Next 20 Years Look Like</h2>
      <p class="section-note">The personal-account snapshot focuses on Michelle’s own accounts. The retirement snapshot shows the combined retirement pool represented by MasterRetirement.</p>
      <div class="chart-grid">
        <div class="chart-card">
          <h3>Michelle Personal Account Balance</h3>
          <p>Projected future balance across MichelleCash, MichelleTFSA, and MichelleRSP.</p>
          {personal_balance_chart}
        </div>
        <div class="chart-card">
          <h3>Master Retirement Dividend Income</h3>
          <p>Projected annual dividend income with reinvestment.</p>
          {retirement_income_chart}
        </div>
        <div class="chart-card">
          <h3>Master Retirement Balance</h3>
          <p>Projected future account value using DRIP share growth and a 2.0% annual price-growth assumption.</p>
          {retirement_balance_chart}
        </div>
      </div>
    </section>

    <section class="panel break-avoid">
      <div class="section-kicker">Largest positions</div>
      <h2>Top Michelle Holdings By Current Balance</h2>
      <p class="section-note">Largest holdings across Michelle’s personal accounts. Dividend-per-share values come from the latest year in the dividend summary file.</p>
      {top_holdings_table}
    </section>

    {''.join(account_sections)}

    <section class="panel break-avoid">
      <div class="section-kicker">Methodology</div>
      <h2>Assumptions</h2>
      <div class="assumptions">
        <div>Dividend growth uses the <strong>Last Growth</strong> field from the 10-year dividend pivot.</div>
        <div>Negative dividend growth is floored at <strong>0.0%</strong> in the forecast models.</div>
        <div>Current-year dividends may be forecasted for monthly and quarterly payers in the source annual dividend file.</div>
        <div>DRIP assumes full reinvestment using the holding’s current yield to derive a reinvestment price proxy.</div>
        <div>Balance projections assume a conservative <strong>2.0%</strong> annual price-growth rate.</div>
        <div>No taxes, contributions, withdrawals, trading changes, or currency effects are included.</div>
      </div>
    </section>
  </div>
</body>
</html>
"""


def write_report_files():
    os.makedirs(REPORT_DIR, exist_ok=True)
    html_path = os.path.join(REPORT_DIR, "Michelle_Annual_Dividend_Report.html")
    pdf_path = os.path.join(REPORT_DIR, "Michelle_Annual_Dividend_Report.pdf")

    report_html = build_report_html()
    with open(html_path, "w", encoding="utf-8") as output_file:
        output_file.write(report_html)

    return html_path, pdf_path


def render_pdf(html_path, pdf_path):
    if not os.path.exists(CHROMIUM_PATH):
        print(f"Chromium not found at {CHROMIUM_PATH}. HTML report created only.", file=sys.stderr)
        return False

    with tempfile.TemporaryDirectory(dir=".") as user_data_dir:
        subprocess.run(
            [
                CHROMIUM_PATH,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--user-data-dir={os.path.abspath(user_data_dir)}",
                f"--print-to-pdf={os.path.abspath(pdf_path)}",
                os.path.abspath(html_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True


def main():
    try:
        html_path, pdf_path = write_report_files()
        pdf_created = render_pdf(html_path, pdf_path)
    except Exception as exc:
        print(f"Failed to generate annual report: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(html_path)
    if pdf_created:
        print(pdf_path)


if __name__ == "__main__":
    main()
