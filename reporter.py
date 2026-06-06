"""
Report generation — saves daily results to disk and formats output.
"""

import os
import json
from datetime import datetime
from tabulate import tabulate


REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def save_report(results: list[dict], top_picks: list[dict], ai_analysis: str):
    """Save scan results and AI analysis to dated files."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Save raw JSON
    json_path = os.path.join(REPORTS_DIR, f"scan_{today}.json")
    with open(json_path, "w") as f:
        json.dump({
            "date": today,
            "total_scanned": len(results),
            "buy_signals": len(top_picks),
            "top_picks": top_picks,
            "all_results": results[:50],  # save top 50
        }, f, indent=2, default=str)

    # Save markdown report
    md_path = os.path.join(REPORTS_DIR, f"report_{today}.md")
    with open(md_path, "w") as f:
        f.write(f"# SET Daily Lux Algo Scan — {today}\n\n")
        f.write(f"**Tickers scanned:** {len(results)}  \n")
        f.write(f"**Buy signals detected:** {len(top_picks)}  \n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(ai_analysis)
        f.write("\n\n---\n\n## Raw Signal Table\n\n")
        f.write(format_table(top_picks))

    print(f"\n📄 Report saved: {md_path}")
    print(f"📊 Data saved:   {json_path}")
    return md_path


def format_table(picks: list[dict]) -> str:
    """Format picks as a markdown table."""
    if not picks:
        return "_No picks to display._"

    headers = ["#", "Ticker", "Sector", "Score", "Signal", "Close", "1D%", "RSI", "Signals"]
    rows = []
    for i, p in enumerate(picks, 1):
        rows.append([
            i,
            p["base_ticker"],
            p["sector"],
            f"{p['score']}/100",
            p["trend"],
            f"{p['close']} ฿",
            f"{p['pct_change_1d']:+.1f}%",
            f"{p['rsi']}" if p["rsi"] else "-",
            ", ".join(p["signals"][:3]) if p["signals"] else "-",
        ])

    return tabulate(rows, headers=headers, tablefmt="github")


def print_console_report(results: list[dict], top_picks: list[dict]):
    """Pretty print to console."""
    today = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "═" * 60)
    print(f"  SET DAILY LUX ALGO SCAN  |  {today}")
    print("═" * 60)
    print(f"  Scanned: {len(results)} tickers  |  Buy signals: {len(top_picks)}")
    print("─" * 60)

    if not top_picks:
        print("  No buy signals today. Market may be in distribution phase.")
        return

    print(f"\n{'#':<4} {'TICKER':<10} {'SECTOR':<18} {'SCORE':>6} {'SIGNAL':<14} {'PRICE':>8} {'1D%':>7} {'RSI':>6}")
    print("─" * 80)

    for i, p in enumerate(top_picks, 1):
        score_bar = "█" * int(p["score"] / 10)
        print(
            f"{i:<4} {p['base_ticker']:<10} {p['sector']:<18} "
            f"{p['score']:>5.1f}  {p['trend']:<14} "
            f"{p['close']:>8.2f} {p['pct_change_1d']:>+6.1f}% {p['rsi']:>6}"
            if p["rsi"] else
            f"{i:<4} {p['base_ticker']:<10} {p['sector']:<18} "
            f"{p['score']:>5.1f}  {p['trend']:<14} "
            f"{p['close']:>8.2f} {p['pct_change_1d']:>+6.1f}%     -"
        )

    print("─" * 80)
    print(f"\nTop signal: {top_picks[0]['base_ticker']} at {top_picks[0]['score']}/100")
    if top_picks[0]["signals"]:
        print(f"Active triggers: {', '.join(top_picks[0]['signals'])}")
