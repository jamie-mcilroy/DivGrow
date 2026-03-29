import sys
from dividend_forecasts.dividends import (
    build_event_rows,
    build_yearly_rows,
    extract_dividends,
    fetch_html,
    load_symbols,
    summarize_by_year,
    write_dividend_events,
    write_dividends_by_year,
)
from dividend_forecasts.paths import DIVIDEND_EVENTS_CSV, DIVIDENDS_BY_YEAR_CSV, SYMBOLS_JSON


def main():
    try:
        symbols = load_symbols(SYMBOLS_JSON)
    except Exception as exc:
        print(f"Failed to load symbols: {exc}", file=sys.stderr)
        raise SystemExit(1)

    all_event_rows = []
    all_yearly_rows = []

    for symbol in symbols:
        try:
            html = fetch_html(symbol)
            raw_rows = extract_dividends(html)
            if not raw_rows:
                print(f"No dividend rows found for {symbol}", file=sys.stderr)
                continue

            all_event_rows.extend(build_event_rows(symbol, raw_rows))
            yearly_totals = summarize_by_year(raw_rows)
            all_yearly_rows.extend(build_yearly_rows(symbol, yearly_totals))
        except Exception as exc:
            print(f"Failed for {symbol}: {exc}", file=sys.stderr)

    if not all_event_rows or not all_yearly_rows:
        print("No dividend data collected.", file=sys.stderr)
        raise SystemExit(1)

    write_dividend_events(DIVIDEND_EVENTS_CSV, all_event_rows)
    write_dividends_by_year(DIVIDENDS_BY_YEAR_CSV, all_yearly_rows)
    print(DIVIDEND_EVENTS_CSV)
    print(DIVIDENDS_BY_YEAR_CSV)


if __name__ == "__main__":
    main()
