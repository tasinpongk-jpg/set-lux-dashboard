"""
Claude API integration for AI analysis of Lux Algo scan results.
Provides contextual market analysis and ranked stock picks for SET.
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from anthropic import Anthropic

def _get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Create a .env file in SET-Lux-Scanner/ with:\n"
            "  ANTHROPIC_API_KEY=sk-ant-..."
        )
    return Anthropic(api_key=api_key)


def analyze_picks(top_picks: list[dict], all_results: list[dict]) -> str:
    """
    Send top picks to Claude for contextual analysis.
    Returns a formatted analysis report.
    """
    if not top_picks:
        return "No buy signals detected in today's scan."

    today = datetime.now().strftime("%Y-%m-%d")
    scan_count = len(all_results)

    # Build signal summary for Claude
    picks_text = ""
    for i, p in enumerate(top_picks[:20], 1):
        signals_str = ", ".join(p["signals"]) if p["signals"] else "none"
        picks_text += (
            f"{i}. {p['base_ticker']} ({p['sector']})\n"
            f"   Score: {p['score']}/100 | Signal: {p['trend']}\n"
            f"   Price: {p['close']} THB | 1D Change: {p['pct_change_1d']}%\n"
            f"   RSI: {p['rsi']} | SuperTrend: {p['supertrend_dir']} | "
            f"AI Cluster: {p['ai_cluster']}\n"
            f"   EMA Ribbon: {p['ema_ribbon']} | MACD: {'BULL' if p['macd_bull'] else 'BEAR'} | "
            f"Vol Surge: {'YES' if p['vol_surge'] else 'NO'}\n"
            f"   Active Signals: {signals_str}\n"
            f"   Support: {p['support']} | Resistance: {p['resistance']}\n\n"
        )

    prompt = f"""You are an expert Thai stock market analyst specializing in SET (Stock Exchange of Thailand) equities.

Today's date: {today}
Stocks scanned: {scan_count} SET-listed tickers
Lux Algo equivalent indicators used: SuperTrend, Smart Trail, AI Cluster, Oscillator Matrix, EMA Ribbon, MACD, Volume Analysis

TOP BUY CANDIDATES FROM TODAY'S SCAN:
{picks_text}

Please provide a professional daily market brief with:

1. **EXECUTIVE SUMMARY** (2-3 sentences on overall market tone from these signals)

2. **TOP 5 STOCK PICKS FOR TODAY**
   For each pick: ticker, why it's compelling (which signals are strongest), key risk level, short-term target (use resistance as guide)

3. **SECTOR INSIGHTS**
   Which sectors are showing the most bullish signals and why this matters

4. **WATCHLIST** (picks #6-10 to monitor)

5. **KEY RISKS TO WATCH**
   What could invalidate these signals

Format in clear markdown. Be specific about prices and levels. Keep it actionable for a Relationship Manager covering SET stocks."""

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def quick_ticker_analysis(ticker_result: dict) -> str:
    """Deep dive analysis on a single ticker."""
    p = ticker_result
    signals_str = ", ".join(p["signals"]) if p["signals"] else "none"

    prompt = f"""Analyze this SET stock based on Lux Algo-equivalent technical signals:

Stock: {p['base_ticker']} ({p['sector']})
Score: {p['score']}/100 | Signal: {p['trend']}
Price: {p['close']} THB | 1D Change: {p['pct_change_1d']}%
RSI: {p['rsi']}
SuperTrend: {p['supertrend_dir']}
AI Cluster: {p['ai_cluster']}
EMA Ribbon: {p['ema_ribbon']} (4 = all EMAs bullish aligned)
MACD: {'BULLISH crossover' if p['macd_bull'] else 'BEARISH'}
Volume Surge: {'YES' if p['vol_surge'] else 'NO'}
Active Signals: {signals_str}
Support: {p['support']} THB | Resistance: {p['resistance']} THB

Score Breakdown:
{chr(10).join(f"  {k}: {v}" for k, v in p['score_breakdown'].items())}

Provide:
1. Trade setup (entry, stop loss, target)
2. Signal confluence analysis
3. Risk/reward assessment
4. What to watch for (confirmation/invalidation)

Keep it concise and actionable."""

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text
