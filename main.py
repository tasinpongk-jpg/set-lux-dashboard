"""
SET Lux Algo Daily Scanner — Main Entry Point

Usage:
  python main.py              # Run scan now
  python main.py --schedule   # Run daily at 18:30 Bangkok time (after SET close)
  python main.py --ticker ADVANC  # Analyze a single ticker
  python main.py --sector FOOD    # Scan a specific sector only
  python main.py --top 10         # Show only top 10 picks
  python main.py --no-ai          # Skip Claude analysis (faster)
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime

import schedule

from scanner import run_scan, get_top_picks
from claude_analyzer import analyze_picks, quick_ticker_analysis
from reporter import save_report, print_console_report
from set_tickers import ALL_TICKERS, get_tickers_by_sector, get_all_tickers
from indicators import compute_lux_score
import yfinance as yf

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s"
)


def run_daily_scan(top_n: int = 20, use_ai: bool = True,
                   tickers: list = None, min_score: int = 50):
    """Full pipeline: scan → AI analysis → report."""
    print(f"\n{'═'*60}")
    print(f"  SET LUX ALGO SCANNER  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═'*60}")

    # 1. Run scan
    results = run_scan(tickers=tickers, max_workers=8, min_score=0)

    if not results:
        print("❌ No results returned. Check your internet connection.")
        return

    # 2. Get top picks
    picks = get_top_picks(results, n=top_n, min_score=min_score)

    # 3. Console output
    print_console_report(results, picks)

    # 4. Claude AI analysis
    ai_analysis = ""
    if use_ai and picks:
        print(f"\n🤖 Generating Claude AI analysis...")
        ai_analysis = analyze_picks(picks, results)
        print("\n" + "─" * 60)
        print("CLAUDE AI MARKET BRIEF")
        print("─" * 60)
        print(ai_analysis)

    # 5. Save report
    if picks:
        save_report(results, picks, ai_analysis)

    return results, picks


def analyze_single_ticker(ticker: str):
    """Deep dive on one ticker."""
    if not ticker.endswith(".BK"):
        ticker = ticker + ".BK"

    print(f"\nDownloading data for {ticker}...")
    try:
        import pandas as pd
        df = yf.download(ticker, period="6mo", interval="1d",
                         progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df is None or len(df) < 30:
            print(f"❌ Insufficient data for {ticker}")
            return

        result = compute_lux_score(df)
        if not result:
            print(f"❌ Could not compute signals for {ticker}")
            return

        result["ticker"] = ticker
        result["base_ticker"] = ticker.replace(".BK", "")
        from set_tickers import ticker_to_sector
        result["sector"] = ticker_to_sector(ticker)

        # Console output
        print(f"\n{'─'*50}")
        print(f"  {result['base_ticker']} — {result['sector']}")
        print(f"{'─'*50}")
        print(f"  Score:      {result['score']}/100  ({result['trend']})")
        print(f"  Price:      {result['close']} THB  ({result['pct_change_1d']:+.2f}%)")
        print(f"  RSI:        {result['rsi']}")
        print(f"  SuperTrend: {result['supertrend_dir']}")
        print(f"  AI Cluster: {result['ai_cluster']}")
        print(f"  EMA Ribbon: {result['ema_ribbon']}")
        print(f"  MACD:       {'BULL' if result['macd_bull'] else 'BEAR'}")
        print(f"  Vol Surge:  {'YES' if result['vol_surge'] else 'NO'}")
        print(f"  Support:    {result['support']} THB")
        print(f"  Resistance: {result['resistance']} THB")
        print(f"  Signals:    {', '.join(result['signals']) if result['signals'] else 'none'}")
        print(f"\nScore Breakdown:")
        for k, v in result["score_breakdown"].items():
            bar = "█" * v
            print(f"  {k:<15} {v:>2}  {bar}")

        # Claude analysis
        print(f"\n🤖 Asking Claude for deep analysis...")
        analysis = quick_ticker_analysis(result)
        print("\n" + "─" * 50)
        print(analysis)

    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        raise


def schedule_daily(run_time: str = "18:30"):
    """Schedule daily scan after SET market closes (16:30 Bangkok)."""
    print(f"\n⏰ Scheduler active — daily scan at {run_time} Bangkok time")
    print("   Press Ctrl+C to stop\n")

    def job():
        print(f"\n🔔 Scheduled scan starting at {datetime.now().strftime('%H:%M')}")
        run_daily_scan()

    schedule.every().day.at(run_time).do(job)

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="SET Lux Algo Daily Scanner")
    parser.add_argument("--schedule", action="store_true",
                        help="Run daily at 18:30 (after SET close)")
    parser.add_argument("--time", default="18:30",
                        help="Schedule time HH:MM (default: 18:30)")
    parser.add_argument("--ticker", type=str,
                        help="Analyze a single ticker (e.g. ADVANC)")
    parser.add_argument("--sector", type=str,
                        help="Scan one sector only (e.g. FOOD, PROPERTY)")
    parser.add_argument("--top", type=int, default=20,
                        help="Number of top picks to show (default: 20)")
    parser.add_argument("--min-score", type=int, default=50,
                        help="Minimum score threshold (default: 50)")
    parser.add_argument("--no-ai", action="store_true",
                        help="Skip Claude AI analysis")
    args = parser.parse_args()

    # Single ticker deep dive
    if args.ticker:
        analyze_single_ticker(args.ticker)
        return

    # Sector-only scan
    tickers = None
    if args.sector:
        tickers = get_tickers_by_sector(args.sector.upper())
        if not tickers:
            print(f"❌ Unknown sector: {args.sector}")
            print(f"   Available: ENERGY, BANKING, FINANCE, INDUSTRIAL, PROPERTY,")
            print(f"              PFREIT, FOOD_BEVERAGE, RETAIL, HEALTHCARE,")
            print(f"              TELECOM_TECH, TRANSPORT, MEDIA, MATERIALS, AGRI")
            sys.exit(1)
        print(f"Sector filter: {args.sector.upper()} ({len(tickers)} tickers)")

    # Scheduled mode
    if args.schedule:
        schedule_daily(run_time=args.time)
        return

    # Default: run now
    run_daily_scan(
        top_n=args.top,
        use_ai=not args.no_ai,
        tickers=tickers,
        min_score=args.min_score,
    )


if __name__ == "__main__":
    main()
