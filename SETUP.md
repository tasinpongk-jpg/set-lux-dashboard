# SET Lux Algo Scanner — Setup Guide

## Quick Start (5 minutes)

### 1. Add your Anthropic API key (for Claude AI analysis)
```bash
cd /Users/champtk/VSCoder/SET-Lux-Scanner
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...
```
Get your key from: https://console.anthropic.com/

### 2. Run a scan now
```bash
cd /Users/champtk/VSCoder/SET-Lux-Scanner
python3 main.py
```

### 3. Quick options
```bash
# Scan all 173 SET tickers + Claude AI brief
python3 main.py

# Skip Claude analysis (faster, no API key needed)
python3 main.py --no-ai

# Deep dive on one stock
python3 main.py --ticker ADVANC
python3 main.py --ticker GULF

# Scan your coverage sectors only
python3 main.py --sector FOOD_BEVERAGE
python3 main.py --sector PROPERTY
python3 main.py --sector PFREIT

# Top 10 only, score >= 70
python3 main.py --top 10 --min-score 70

# Run daily at 18:30 automatically (keeps running in background)
python3 main.py --schedule
```

---

## Schedule Daily Scan (cron — runs even when VS Code is closed)

```bash
# Open crontab
crontab -e

# Add this line (runs Mon-Fri at 18:30 Bangkok = after SET 16:30 close)
30 18 * * 1-5 /Users/champtk/VSCoder/SET-Lux-Scanner/run_daily.sh >> /tmp/set_scanner.log 2>&1
```

---

## Output

Reports are saved to: `SET-Lux-Scanner/reports/`
- `report_YYYY-MM-DD.md` — full markdown report with AI analysis
- `scan_YYYY-MM-DD.json` — raw signal data

---

## Indicators Used (Lux Algo Equivalents)

| Lux Algo | This Scanner | Weight |
|----------|-------------|--------|
| Signals & Overlays | SuperTrend (ATR-based) | 35 pts |
| Smart Trail | ATR Trailing Stop | 20 pts |
| AI Cluster | K-Means Classification | 15 pts |
| Oscillator Matrix | RSI+Stoch+CCI+MFI | 15 pts |
| Trend Forecaster | EMA Ribbon (9/21/50/100/200) | 10 pts |
| — | MACD | 5 pts |
| — | Volume Surge + OBV | 5+ pts |

Score 0–100: **75+ = STRONG BUY**, 55–74 = BUY, 40–54 = NEUTRAL

---

## Add More Tickers

Edit `set_tickers.py` → add tickers to the relevant sector dict.
Yahoo Finance uses `.BK` suffix for all SET stocks.

## Sectors Available
- ENERGY, BANKING, FINANCE, INDUSTRIAL
- PROPERTY, PFREIT, FOOD_BEVERAGE, RETAIL
- HEALTHCARE, TELECOM_TECH, TRANSPORT, MEDIA
- MATERIALS, AGRI
