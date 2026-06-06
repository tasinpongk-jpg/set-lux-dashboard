"""
Daily scanner: downloads SET ticker data from Yahoo Finance
and runs all Lux Algo-equivalent indicators.
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from indicators import compute_lux_score
from set_tickers import ALL_TICKERS, ticker_to_sector

logger = logging.getLogger(__name__)


def fetch_ticker_data(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame | None:
    """Download OHLCV data for a single ticker from Yahoo Finance."""
    try:
        data = yf.download(ticker, period=period, interval=interval,
                           progress=False, auto_adjust=True, timeout=15)
        if data is None or len(data) < 30:
            return None
        # Flatten multi-level columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        logger.debug(f"Failed to fetch {ticker}: {e}")
        return None


def scan_single(ticker: str) -> dict | None:
    """Scan one ticker and return signal result."""
    df = fetch_ticker_data(ticker)
    if df is None:
        return None

    result = compute_lux_score(df)
    if result is None:
        return None

    result["ticker"] = ticker
    result["base_ticker"] = ticker.replace(".BK", "")
    result["sector"] = ticker_to_sector(ticker)
    result["scan_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return result


def run_scan(tickers: list[str] = None, max_workers: int = 8,
             min_score: int = 0) -> list[dict]:
    """
    Parallel scan of all tickers.
    Returns sorted list of results (highest score first).
    """
    if tickers is None:
        tickers = ALL_TICKERS

    results = []
    failed = []
    total = len(tickers)

    print(f"\n🔍 Scanning {total} SET tickers...")
    print("─" * 50)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_single, t): t for t in tickers}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            ticker = futures[future]
            try:
                result = future.result(timeout=30)
                if result and result["score"] >= min_score:
                    results.append(result)
                    if result["score"] >= 55:
                        print(f"  ✅ {ticker:<15} Score: {result['score']:>5.1f}  {result['trend']}")
            except Exception as e:
                failed.append(ticker)
                logger.debug(f"Scan error {ticker}: {e}")

            if completed % 20 == 0:
                elapsed = time.time() - start_time
                print(f"  Progress: {completed}/{total} | {elapsed:.0f}s elapsed")

    elapsed = time.time() - start_time
    print(f"\n✅ Scan complete: {len(results)} results in {elapsed:.1f}s")
    if failed:
        print(f"⚠️  Failed: {len(failed)} tickers (no data or error)")

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def get_top_picks(results: list[dict], n: int = 20, min_score: int = 55) -> list[dict]:
    """Filter to top N buy candidates."""
    buys = [r for r in results if r["score"] >= min_score and r["trend"] in ("BUY", "STRONG BUY")]
    return buys[:n]


def results_to_dataframe(results: list[dict]) -> pd.DataFrame:
    """Convert scan results to a clean DataFrame."""
    if not results:
        return pd.DataFrame()

    rows = []
    for r in results:
        rows.append({
            "Ticker": r["base_ticker"],
            "Sector": r["sector"],
            "Score": r["score"],
            "Signal": r["trend"],
            "Close": r["close"],
            "1D%": r["pct_change_1d"],
            "RSI": r["rsi"],
            "SuperTrend": r["supertrend_dir"],
            "AI Cluster": r["ai_cluster"],
            "EMA Ribbon": r["ema_ribbon"],
            "MACD": "BULL" if r["macd_bull"] else "BEAR",
            "Vol Surge": "YES" if r["vol_surge"] else "-",
            "Support": r["support"],
            "Resistance": r["resistance"],
            "Active Signals": ", ".join(r["signals"]) if r["signals"] else "-",
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    results = run_scan(max_workers=8)
    picks = get_top_picks(results, n=20)
    df = results_to_dataframe(picks)
    if not df.empty:
        print("\nTop Picks:")
        print(df.to_string(index=False))
