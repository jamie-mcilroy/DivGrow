# DivGrow

Canadian dividend and valuation pipeline for a curated symbol list. The repo pulls EPS, BVPS, current price, dividend history, historic dividend yield, and account-level DRIP projections, then writes CSV outputs for screening and planning.

## Inputs

- [`configs/symbols.json`](/Users/jmcilroy/scripts/divgrow/DivGrow/configs/symbols.json)
  List of TSX symbols to analyze.
- [`configs/Holdings.csv`](/Users/jmcilroy/scripts/divgrow/DivGrow/configs/Holdings.csv)
  Account holdings used for the income, share, DRIP income, and balance projections.

## Main Pipeline

Run the full pipeline from the repo root:

```bash
PYTHON_BIN=./venv/bin/python ./entrypoint.sh
```

`entrypoint.sh` runs these scripts in order:

1. [`eps.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/eps.py)
2. [`bvps_yf.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/bvps_yf.py)
3. [`ben_graham.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/ben_graham.py)
4. [`current_prices.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/current_prices.py)
5. [`div_hist_all.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_all.py)
6. [`div_hist_yield.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_yield.py)
7. [`div_hist_summary.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_summary.py)
8. [`fundamentals_summary.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/fundamentals_summary.py)
9. [`div_hist_account_income.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_account_income.py)
10. [`div_hist_account_shares.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_account_shares.py)
11. [`div_hist_account_drip_income.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_account_drip_income.py)
12. [`div_hist_account_balance.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_account_balance.py)

## Core Outputs

Written to [`data/`](/Users/jmcilroy/scripts/divgrow/DivGrow/data):

- `eps_10y_pivot.csv`
  Past 10 years of annual EPS plus 3Y, 5Y, and 10Y EPS averages.
- `bvps_<year>.csv`
  BVPS snapshot grouped by the balance sheet year returned by Yahoo Finance.
- `ben_graham_prices.csv`
  Graham values using 3Y, 5Y, and 10Y average EPS.
- `current_prices.csv`
  Current Yahoo Finance price for each symbol.
- `dividend_events.csv`
  Raw dividend events scraped from `dividendhistory.org`.
- `dividend_events_with_prices.csv`
  Dividend events enriched with ex-dividend-date prices from Yahoo Finance.
- `dividend_yield_summary.csv`
  Historic average annualized dividend yield over 3, 5, and 10 years.
- `dividends_by_year.csv`
  Annual dividend totals by symbol.
- `dividends_10y_pivot.csv`
  Past 10 years of annual dividends with growth metrics.
- `fundamentals_summary.csv`
  Combined screening file with current price, BG3/BG5/BG10, yield, dividend growth, and the 10-year dividend pivot.

Written to [`output/`](/Users/jmcilroy/scripts/divgrow/DivGrow/output):

- `account_income_projections/`
- `account_share_projections/`
- `account_drip_income_projections/`
- `account_balance_projections/`

These contain per-account 20-year forward projections and also generate `MasterRetirement` by combining `JamieRSP` and `MichelleRSP`.

## Script Notes

- [`eps.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/eps.py)
  Scrapes AlphaQuery earnings history and builds the EPS pivot.
- [`bvps_yf.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/bvps_yf.py)
  Uses `yfinance` balance sheet and share count data to calculate BVPS.
- [`ben_graham.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/ben_graham.py)
  Calculates Graham values with `sqrt(22.5 * EPS * BVPS)`.
- [`current_prices.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/current_prices.py)
  Pulls current prices from Yahoo Finance.
- [`div_hist_all.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_all.py)
  Scrapes raw dividend history and derives annual totals.
- [`div_hist_yield.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_yield.py)
  Enriches dividend events with ex-date prices and computes average annualized yield.
- [`div_hist_summary.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/div_hist_summary.py)
  Builds the 10-year dividend pivot and growth columns.
- [`fundamentals_summary.py`](/Users/jmcilroy/scripts/divgrow/DivGrow/fundamentals_summary.py)
  Merges dividends, Graham values, yields, and current price into a single sortable screening CSV.

## Current Fundamentals Summary Layout

[`data/fundamentals_summary.csv`](/Users/jmcilroy/scripts/divgrow/DivGrow/data/fundamentals_summary.csv) currently starts with:

- `Ticker`
- `Current Price`
- `Δ BG5`
- `BG3`
- `BG5`
- `BG10`
- `Yield5`
- `Growth5`

`Δ BG5` is stored as a percentage:

```text
((Current Price - BG5) / BG5) * 100
```

Growth and yield columns in the summary file are written as percent values rounded to 2 decimals.

## Running Individual Steps

Examples:

```bash
./venv/bin/python current_prices.py
./venv/bin/python div_hist_all.py
./venv/bin/python div_hist_yield.py
./venv/bin/python fundamentals_summary.py
```

To refresh only historic dividend yields:

```bash
./venv/bin/python div_hist_all.py
./venv/bin/python div_hist_yield.py
```

## Notes

- TSX symbols are normalized for Yahoo Finance by appending `.TO` and converting `.` to `-`.
- The dividend pipeline stores raw events before building yearly summaries so yield history can be calculated from ex-dividend dates.
- Some Yahoo Finance calls can rate-limit. The Yahoo-based scripts include simple retry/backoff logic.
