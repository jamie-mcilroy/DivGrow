#!/bin/bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
DIVGROW_RUN_DATE="${DIVGROW_RUN_DATE:-$(date +%F)}"
export DIVGROW_RUN_DATE

echo "Run date: ${DIVGROW_RUN_DATE}"
echo "Run root: runs/${DIVGROW_RUN_DATE}"

run_step() {
  local script_name="$1"
  echo "Running ${script_name}..."
  "${PYTHON_BIN}" "${script_name}"
}

run_step "eps.py"
run_step "bvps_yf.py"
run_step "ben_graham.py"
run_step "current_prices.py"
run_step "div_hist_all.py"
run_step "div_hist_yield.py"
run_step "div_hist_summary.py"
run_step "fundamentals_summary.py"
run_step "fundamentals_summary_html.py"
run_step "weekly_portfolio_report.py"
run_step "div_hist_account_income.py"
run_step "div_hist_account_shares.py"
run_step "div_hist_account_drip_income.py"
run_step "div_hist_account_balance.py"
run_step "account_reports_html.py"
run_step "output_index_html.py"

echo "Investment pipeline completed."
