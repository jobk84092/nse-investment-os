#!/bin/zsh
# Run the full pipeline, then email outputs (see docs/EMAIL_DIGEST.md).
# Scheduled every 14 days via launchd StartInterval.
set -euo pipefail
ROOT="/Users/jobkimani/Library/CloudStorage/OneDrive-Personal/JOB/personal stuff/personal finance/stocks/20260402 stocks automation/nse_investment_os"
if [[ -f "$ROOT/.email_env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/.email_env"
  set +a
fi
if [[ -f "$ROOT/.telegram_env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/.telegram_env"
  set +a
fi
cd "$ROOT"
"$ROOT/.venv/bin/python" scripts/run_all.py
"$ROOT/.venv/bin/python" scripts/send_memo_email.py
