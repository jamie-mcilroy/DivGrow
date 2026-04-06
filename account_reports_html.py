import csv
import html
import os
from collections import defaultdict
from datetime import datetime
from dividend_forecasts.paths import ACCOUNT_REPORTS_DIR, OUTPUT_DIR as OUTPUT_ROOT


REPORT_DIR = ACCOUNT_REPORTS_DIR
CSV_GROUPS = {
    "income": "account_income_projections",
    "shares": "account_share_projections",
    "drip_income": "account_drip_income_projections",
    "balance": "account_balance_projections",
}
SECTION_TITLES = {
    "income": "Projected Dividend Income",
    "shares": "Projected Share Counts",
    "drip_income": "Projected DRIP Income",
    "balance": "Projected Account Balance",
}
SECTION_DESCRIPTIONS = {
    "income": "Forward annual dividend income by symbol using the dividend growth model.",
    "shares": "Projected share counts under DRIP assumptions.",
    "drip_income": "Forward annual dividend income after reinvestment increases the share base.",
    "balance": "Projected account value using DRIP share growth and conservative price appreciation.",
}
RETIREMENT_YEAR = "2033"
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


def load_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def to_float(value):
    if value in ("", None):
        return None
    try:
        return float(str(value).replace("%", "").replace(",", ""))
    except ValueError:
        return None


def get_year_columns(fieldnames):
    return sorted(column for column in fieldnames if column.isdigit())


def format_number(value, decimals=2):
    number = to_float(value)
    if number is None:
        return html.escape(str(value or ""))
    return f"{number:,.{decimals}f}"


def format_currency(value, decimals=0):
    number = to_float(value)
    if number is None:
        return html.escape(str(value or ""))
    return f"${number:,.{decimals}f}"


def slugify(account):
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in account).strip("-")


def sort_accounts(account_names):
    order_lookup = {name: index for index, name in enumerate(ACCOUNT_ORDER)}
    return sorted(account_names, key=lambda name: (order_lookup.get(name, len(ACCOUNT_ORDER)), name))


def collect_account_files():
    accounts = defaultdict(dict)
    for key, folder in CSV_GROUPS.items():
        folder_path = os.path.join(OUTPUT_ROOT, folder)
        if not os.path.isdir(folder_path):
            continue
        for filename in sorted(os.listdir(folder_path)):
            if not filename.endswith(".csv"):
                continue
            account = filename.split("_")[0]
            accounts[account][key] = os.path.join(folder_path, filename)
    return dict(accounts)


def extract_totals(rows):
    if not rows:
        return {}
    for row in rows:
        if row.get("Symbol") == "TOTAL":
            return row
    return rows[-1]


def build_account_summary(account, file_map):
    summary = {
        "account": account,
        "holdings": 0,
        "current_balance": "",
        "retirement_balance": "",
        "end_balance": "",
        "current_income": "",
        "retirement_income": "",
        "income_5y": "",
        "end_income": "",
        "end_drip_income": "",
    }

    balance_rows = load_csv_rows(file_map["balance"]) if "balance" in file_map else []
    if balance_rows:
        total_row = extract_totals(balance_rows)
        year_columns = get_year_columns(balance_rows[0].keys())
        summary["holdings"] = max(len(balance_rows) - 1, 0)
        summary["current_balance"] = total_row.get("Current Balance", "")
        if RETIREMENT_YEAR in total_row:
            summary["retirement_balance"] = total_row.get(RETIREMENT_YEAR, "")
        if year_columns:
            summary["end_balance"] = total_row.get(year_columns[-1], "")

    income_rows = load_csv_rows(file_map["income"]) if "income" in file_map else []
    if income_rows:
        total_row = extract_totals(income_rows)
        year_columns = get_year_columns(income_rows[0].keys())
        current_income = 0.0
        for row in income_rows:
            if row.get("Symbol") == "TOTAL":
                continue
            growth_text = str(row.get("Growth Rate 5Y", "")).replace("%", "")
            first_year = year_columns[0] if year_columns else None
            first_year_income = to_float(row.get(first_year)) if first_year else None
            growth_rate = to_float(growth_text)
            if first_year_income is None:
                continue
            if growth_rate is None:
                current_income += first_year_income
            else:
                current_income += first_year_income / (1 + (growth_rate / 100))
        if current_income:
            summary["current_income"] = f"{current_income:.2f}"
        if RETIREMENT_YEAR in total_row:
            summary["retirement_income"] = total_row.get(RETIREMENT_YEAR, "")
        if len(year_columns) >= 5:
            summary["income_5y"] = total_row.get(year_columns[4], "")
        if year_columns:
            summary["end_income"] = total_row.get(year_columns[-1], "")

    drip_rows = load_csv_rows(file_map["drip_income"]) if "drip_income" in file_map else []
    if drip_rows:
        total_row = extract_totals(drip_rows)
        year_columns = get_year_columns(drip_rows[0].keys())
        if RETIREMENT_YEAR in total_row:
            summary["retirement_income"] = total_row.get(RETIREMENT_YEAR, "")
        if year_columns:
            summary["end_drip_income"] = total_row.get(year_columns[-1], "")

    return summary


def metric_card(label, value):
    return f"""
    <div class="metric-card">
      <div class="metric-label">{html.escape(label)}</div>
      <div class="metric-value">{html.escape(value)}</div>
    </div>
    """


def render_table(rows):
    if not rows:
        return "<p class='empty-state'>No data available.</p>"

    headers = list(rows[0].keys())
    year_columns = set(get_year_columns(headers))
    header_html = "".join(f"<th title='{html.escape(header_tooltip(header))}'>{html.escape(header)}</th>" for header in headers)

    body_rows = []
    for row in rows:
        cells = []
        for header in headers:
            value = row.get(header, "")
            css_class = []
            if header == "Symbol":
                css_class.append("ticker")
            if value == "TOTAL":
                css_class.append("total")
            if "%" in str(value):
                css_class.append("percent")
            class_attr = f" class=\"{' '.join(css_class)}\"" if css_class else ""

            if header in year_columns:
                display = format_number(value)
            elif header in {"Current Balance", "Current Price", "Price"}:
                display = format_number(value)
            elif header in {"Starting Quantity", "Quantity"}:
                display = format_number(value, 0)
            else:
                display = html.escape(str(value))

            cells.append(f"<td{class_attr}>{display}</td>")
        row_class = " class='total-row'" if row.get("Symbol") == "TOTAL" else ""
        body_rows.append(f"<tr{row_class}>{''.join(cells)}</tr>")

    return f"""
    <div class="table-wrap">
      <table>
        <thead><tr>{header_html}</tr></thead>
        <tbody>
          {''.join(body_rows)}
        </tbody>
      </table>
    </div>
    """


def header_tooltip(header):
    tooltips = {
        "Account": "Account name from Holdings.csv.",
        "Symbol": "Holding ticker or TOTAL row.",
        "Quantity": "Starting share count.",
        "Starting Quantity": "Starting share count before future projections.",
        "Current Price": "Current price used in the projection.",
        "Price": "Current price used in the projection.",
        "Yield": "Current yield assumption for the holding.",
        "Growth Rate Used": "Dividend growth rate used in the projection.",
        "Growth Rate 5Y": "Dividend growth rate shown in the income projection file.",
        "Current Balance": "Current market value before future projections.",
        "Price Growth Assumption": "Annual price appreciation assumption used in balance projections.",
    }
    if header.isdigit():
        return f"Projected value for {header}."
    return tooltips.get(header, header)


def render_account_page(account, file_map, summary):
    sections = []
    for key in ("income", "shares", "drip_income", "balance"):
        path = file_map.get(key)
        if not path:
            continue
        rows = load_csv_rows(path)
        sections.append(
            f"""
            <section class="section">
              <h2>{html.escape(SECTION_TITLES[key])}</h2>
              <div class="section-copy">{html.escape(SECTION_DESCRIPTIONS[key])}</div>
              {render_table(rows)}
            </section>
            """
        )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(account)} Account Report</title>
  <style>
    :root {{
      --paper: #f6f1e7;
      --ink: #12161d;
      --muted: #5a6472;
      --navy: #16263a;
      --gold: #b8945b;
      --line: rgba(18, 22, 29, 0.12);
      --panel: rgba(255, 255, 255, 0.68);
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
    .eyebrow {{ font-size: 12px; letter-spacing: 0.22em; text-transform: uppercase; color: rgba(247,242,232,0.68); margin-bottom: 14px; }}
    h1 {{ margin: 0; font-family: "Iowan Old Style", Georgia, serif; font-size: clamp(34px, 4vw, 54px); font-weight: 700; line-height: 0.95; letter-spacing: -0.03em; }}
    .subhead {{ margin-top: 16px; color: rgba(247,242,232,0.8); font-size: 16px; line-height: 1.6; }}
    .timestamp {{ margin-top: 18px; color: rgba(247,242,232,0.6); font-size: 13px; }}
    .back-link {{ display: inline-block; margin-top: 18px; color: #f4dcc0; text-decoration: none; border-bottom: 1px solid rgba(244,220,192,0.4); }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 24px; }}
    .metric-card {{ min-height: 118px; padding: 18px; border-radius: 18px; background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); }}
    .metric-label {{ color: rgba(247,242,232,0.64); text-transform: uppercase; letter-spacing: 0.12em; font-size: 11px; }}
    .metric-value {{ margin-top: 10px; font-size: 28px; line-height: 1; font-weight: 700; letter-spacing: -0.03em; }}
    .section {{ margin-top: 24px; padding: 24px; border-radius: 24px; background: var(--panel); border: 1px solid var(--line); box-shadow: 0 10px 40px rgba(26,32,44,0.08); }}
    .section h2 {{ margin: 0 0 8px; font-family: "Iowan Old Style", Georgia, serif; font-size: 28px; color: var(--navy); }}
    .section-copy {{ margin-bottom: 16px; color: var(--muted); font-size: 14px; }}
    .table-wrap {{ overflow: auto; max-height: 72vh; border-radius: 18px; border: 1px solid var(--line); background: rgba(255,255,255,0.55); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    thead th {{ position: sticky; top: 0; background: #f4ecdf; color: var(--navy); text-transform: uppercase; letter-spacing: 0.08em; font-size: 10px; z-index: 1; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: right; white-space: nowrap; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{ text-align: left; position: sticky; background: inherit; }}
    th:first-child, td:first-child {{ left: 0; }}
    th:nth-child(2), td:nth-child(2) {{ left: 108px; }}
    tbody tr:nth-child(odd) {{ background: rgba(255,255,255,0.34); }}
    tbody tr:hover {{ background: rgba(184,148,91,0.08); }}
    .ticker {{ font-weight: 700; color: var(--navy); }}
    .total-row {{ background: rgba(22,38,58,0.08) !important; font-weight: 700; }}
    .empty-state {{ color: var(--muted); }}
    @media (max-width: 900px) {{
      .page {{ width: calc(100vw - 24px); margin: 12px auto 24px; }}
      .hero, .section {{ padding: 18px; border-radius: 18px; }}
      h1 {{ font-size: 36px; }}
      th:nth-child(2), td:nth-child(2) {{ left: 88px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="eyebrow">DivGrow Account Report</div>
      <h1>{html.escape(account)}</h1>
      <div class="subhead">Account-level projection set covering income, shares, DRIP income, and balance outlook over the next 20 years.</div>
      <div class="timestamp">Generated {html.escape(generated_at)}</div>
      <a class="back-link" href="index.html">Back to account summary</a>
      <div class="metrics">
        {metric_card("Holdings", str(summary["holdings"]))}
        {metric_card("Current Balance", format_number(summary["current_balance"]))}
        {metric_card("Current Income", format_number(summary["current_income"]))}
        {metric_card("2033 Balance", format_number(summary["retirement_balance"]))}
        {metric_card("2033 Income", format_number(summary["retirement_income"]))}
        {metric_card("5Y Income", format_number(summary["income_5y"]))}
        {metric_card("20Y Balance", format_number(summary["end_balance"]))}
        {metric_card("20Y Income", format_number(summary["end_income"]))}
        {metric_card("20Y DRIP Income", format_number(summary["end_drip_income"]))}
      </div>
    </section>
    {''.join(sections)}
  </main>
</body>
</html>"""
    return page


def render_index(account_summaries):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    cards = []
    for summary in account_summaries:
        slug = slugify(summary["account"])
        cards.append(
            f"""
            <a class="account-card" href="{slug}.html">
              <div class="card-top">
                <div class="card-eyebrow">Account</div>
                <div class="card-title">{html.escape(summary["account"])}</div>
              </div>
              <div class="card-grid">
                <div><span>Holdings</span><strong>{summary["holdings"]}</strong></div>
                <div><span>Current Balance</span><strong>{format_currency(summary["current_balance"])}</strong></div>
                <div><span>Current Income</span><strong>{format_currency(summary["current_income"])}</strong></div>
                <div><span>2033 Balance</span><strong>{format_currency(summary["retirement_balance"])}</strong></div>
                <div><span>2033 Income</span><strong>{format_currency(summary["retirement_income"])}</strong></div>
                <div><span>5Y Income</span><strong>{format_currency(summary["income_5y"])}</strong></div>
                <div><span>20Y Balance</span><strong>{format_currency(summary["end_balance"])}</strong></div>
                <div><span>20Y DRIP Income</span><strong>{format_currency(summary["end_drip_income"])}</strong></div>
              </div>
            </a>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Account Projection Reports</title>
  <style>
    :root {{
      --paper: #f6f1e7;
      --ink: #12161d;
      --muted: #5a6472;
      --navy: #16263a;
      --gold: #b8945b;
      --line: rgba(18, 22, 29, 0.12);
      --panel: rgba(255, 255, 255, 0.68);
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
    .hero {{ padding: 36px 40px 30px; border: 1px solid var(--line); background: linear-gradient(135deg, rgba(22, 38, 58, 0.96), rgba(18, 22, 29, 0.96)); color: #f7f2e8; border-radius: 24px; box-shadow: 0 24px 70px rgba(14,18,24,0.18); }}
    .eyebrow {{ font-size: 12px; letter-spacing: 0.22em; text-transform: uppercase; color: rgba(247,242,232,0.68); margin-bottom: 14px; }}
    h1 {{ margin: 0; font-family: "Iowan Old Style", Georgia, serif; font-size: clamp(36px, 5vw, 58px); line-height: 0.95; letter-spacing: -0.03em; }}
    .subhead {{ margin-top: 16px; max-width: 820px; color: rgba(247,242,232,0.8); font-size: 16px; line-height: 1.6; }}
    .timestamp {{ margin-top: 18px; color: rgba(247,242,232,0.6); font-size: 13px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; margin-top: 24px; }}
    .account-card {{ display: block; padding: 22px; border-radius: 24px; background: var(--panel); border: 1px solid var(--line); box-shadow: 0 10px 40px rgba(26,32,44,0.08); text-decoration: none; color: inherit; transition: transform 120ms ease, box-shadow 120ms ease; }}
    .account-card:hover {{ transform: translateY(-2px); box-shadow: 0 16px 50px rgba(26,32,44,0.12); }}
    .card-top {{ margin-bottom: 18px; }}
    .card-eyebrow {{ text-transform: uppercase; letter-spacing: 0.12em; font-size: 11px; color: var(--muted); }}
    .card-title {{ margin-top: 8px; font-family: "Iowan Old Style", Georgia, serif; font-size: 30px; color: var(--navy); }}
    .card-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px 18px; }}
    .card-grid span {{ display: block; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }}
    .card-grid strong {{ display: block; margin-top: 5px; font-size: 22px; letter-spacing: -0.03em; color: var(--ink); }}
    @media (max-width: 900px) {{
      .page {{ width: calc(100vw - 24px); margin: 12px auto 24px; }}
      .hero {{ padding: 18px; border-radius: 18px; }}
      h1 {{ font-size: 38px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="eyebrow">DivGrow Account Reports</div>
      <h1>Projection Book</h1>
      <div class="subhead">Master summary of the generated account projection files. Each card links into a dedicated account page with income, share, DRIP income, and balance tables.</div>
      <div class="timestamp">Generated {html.escape(generated_at)}</div>
    </section>
    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>"""


def main():
    account_files = collect_account_files()
    if not account_files:
        raise SystemExit("No account projection CSV files found under output/.")

    os.makedirs(REPORT_DIR, exist_ok=True)
    summaries = []
    for account in sort_accounts(account_files.keys()):
        file_map = account_files[account]
        summary = build_account_summary(account, file_map)
        summaries.append(summary)
        output_path = os.path.join(REPORT_DIR, f"{slugify(account)}.html")
        with open(output_path, "w", encoding="utf-8") as html_file:
            html_file.write(render_account_page(account, file_map, summary))

    with open(os.path.join(REPORT_DIR, "index.html"), "w", encoding="utf-8") as html_file:
        html_file.write(render_index(summaries))

    print(os.path.join(REPORT_DIR, "index.html"))


if __name__ == "__main__":
    main()
