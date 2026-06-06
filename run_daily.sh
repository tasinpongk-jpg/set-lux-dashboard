#!/bin/bash
# Daily SET Lux Algo Scanner
# Run manually: bash run_daily.sh
# Schedule via cron: add to crontab with: crontab -e
#   30 18 * * 1-5 /Users/champtk/VSCoder/SET-Lux-Scanner/run_daily.sh >> /tmp/set_scanner.log 2>&1

cd "$(dirname "$0")"
/Users/champtk/.pyenv/versions/3.13.4/bin/python3 -W ignore main.py --top 20 --min-score 55
