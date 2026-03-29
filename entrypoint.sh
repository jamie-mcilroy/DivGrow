#!/bin/bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

run_step() {
  local script_name="$1"
  echo "Running ${script_name}..."
  "${PYTHON_BIN}" "${script_name}"
}

run_step "eps.py"
run_step "bvps_yf.py"
run_step "ben_graham.py"
run_step "div_hist_all.py"
run_step "div_hist_summary.py"
run_step "div_hist_account_income.py"
run_step "div_hist_account_shares.py"
run_step "div_hist_account_drip_income.py"
run_step "div_hist_account_balance.py"

echo "Investment pipeline completed."
