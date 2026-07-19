"""
Weekly Trading Report Generator

Analyzes trading performance from state.json and sends a Telegram summary
showing P&L breakdown, win rate, and trade analysis by reason.
"""

import os
import json
import urllib.request
from datetime import datetime, timezone
from collections import defaultdict

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STATE_FILE = os.getenv("STATE_FILE", "state.json")


def send_telegram(message):
    """Send message to Telegram"""
    print(message)
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        data = json.dumps({"chat_id": CHAT_ID, "text": message}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"Telegram error: {e}")


def analyze_trades(state):
    """
    Analyze all closed trades and return summary stats.
    Returns: dict with analysis
    """
    trades = state.get("trades", [])
    closed_trades = [t for t in trades if t["side"] == "SELL"]

    if not closed_trades:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_pnl_per_trade": 0.0,
            "by_reason": {},
            "by_symbol": {},
        }

    # Overall stats
    wins = [t for t in closed_trades if t["pnl"] > 0]
    losses = [t for t in closed_trades if t["pnl"] < 0]
    break_even = [t for t in closed_trades if t["pnl"] == 0]

    total_pnl = sum(t["pnl"] for t in closed_trades)

    # Group by exit reason
    by_reason = defaultdict(lambda: {"trades": 0, "wins": 0, "total_pnl": 0.0, "avg_pnl": 0.0})
    for t in closed_trades:
        reason = t.get("reason", "unknown")
        by_reason[reason]["trades"] += 1
        if t["pnl"] > 0:
            by_reason[reason]["wins"] += 1
        by_reason[reason]["total_pnl"] += t["pnl"]

    # Calculate avg per reason
    for reason in by_reason:
        by_reason[reason]["avg_pnl"] = by_reason[reason]["total_pnl"] / by_reason[reason]["trades"]

    # Group by symbol
    by_symbol = defaultdict(lambda: {"trades": 0, "wins": 0, "total_pnl": 0.0})
    for t in closed_trades:
        sym = t.get("symbol", "unknown")
        by_symbol[sym]["trades"] += 1
        if t["pnl"] > 0:
            by_symbol[sym]["wins"] += 1
        by_symbol[sym]["total_pnl"] += t["pnl"]

    return {
        "total_trades": len(closed_trades),
        "wins": len(wins),
        "losses": len(losses),
        "break_even": len(break_even),
        "win_rate": (len(wins) / len(closed_trades) * 100) if closed_trades else 0,
        "total_pnl": total_pnl,
        "avg_pnl_per_trade": total_pnl / len(closed_trades) if closed_trades else 0,
        "by_reason": dict(by_reason),
        "by_symbol": dict(by_symbol),
        "start_balance": state.get("start_balance", 0),
        "current_equity": state.get("balance", 0),
    }


def generate_report(state, analysis):
    """Generate formatted Telegram report"""

    start_balance = analysis["start_balance"]
    current_equity = state.get("balance", 0)
    open_positions_value = sum(
        pos.get("amount", 0) * pos.get("entry", 0)
        for pos in state.get("positions", {}).values()
    )
    total_equity = current_equity + open_positions_value

    pnl_total = total_equity - start_balance
    pnl_pct = (pnl_total / start_balance * 100) if start_balance > 0 else 0

    # Build report
    lines = []
    lines.append("📊 **WEEKLY TRADING REPORT**")
    lines.append(f"Period: {state.get('started_at', 'N/A')} → {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    # Summary
    lines.append("**📈 Summary**")
    lines.append(f"Starting Balance: ${start_balance:,.2f}")
    lines.append(f"Current Equity: ${total_equity:,.2f}")
    lines.append(f"Total P&L: ${pnl_total:,.2f} ({pnl_pct:+.2f}%)")
    lines.append(f"Open Cash: ${current_equity:,.2f}")
    lines.append("")

    # Trade stats
    lines.append("**🎯 Trade Performance**")
    lines.append(f"Closed Trades: {analysis['total_trades']}")
    lines.append(f"Wins: {analysis['wins']} | Losses: {analysis['losses']} | Break-even: {analysis['break_even']}")
    lines.append(f"Win Rate: {analysis['win_rate']:.1f}%")
    lines.append(f"Avg P&L per Trade: ${analysis['avg_pnl_per_trade']:,.2f}")
    lines.append("")

    # By symbol
    if analysis["by_symbol"]:
        lines.append("**🪙 Performance by Symbol**")
        for sym, stats in sorted(analysis["by_symbol"].items()):
            wr = (stats["wins"] / stats["trades"] * 100) if stats["trades"] > 0 else 0
            lines.append(
                f"{sym}: {stats['trades']} trades | {stats['wins']} wins ({wr:.0f}%) | "
                f"P&L ${stats['total_pnl']:+,.2f}"
            )
        lines.append("")

    # By reason (exit reason)
    if analysis["by_reason"]:
        lines.append("**📋 Exit Reasons & P&L**")
        for reason, stats in sorted(analysis["by_reason"].items(), key=lambda x: -x[1]["total_pnl"]):
            wr = (stats["wins"] / stats["trades"] * 100) if stats["trades"] > 0 else 0
            lines.append(
                f"{reason}: {stats['trades']} | {stats['wins']} wins ({wr:.0f}%) | "
                f"Avg ${stats['avg_pnl']:+,.2f}"
            )
        lines.append("")

    # Open positions
    if state.get("positions"):
        lines.append("**📂 Open Positions**")
        for sym, pos in state.get("positions", {}).items():
            unrealized_pnl_pct = (pos.get("amount", 0) / pos.get("entry", 0) - 1) * 100 if pos.get("entry") else 0
            lines.append(f"{sym}: {pos.get('amount', 0):.5f} units @ ${pos.get('entry', 0):,.2f} ({unrealized_pnl_pct:+.2f}%)")
        lines.append("")

    # Conclusion
    if analysis["total_trades"] > 0:
        if pnl_total > 0:
            lines.append(f"✅ **Week Result: PROFITABLE** (+${pnl_total:,.2f})")
        elif pnl_total < 0:
            lines.append(f"❌ **Week Result: LOSS** (${pnl_total:,.2f})")
        else:
            lines.append("⚖️ **Week Result: BREAK-EVEN**")
    else:
        lines.append("⏳ No trades closed yet this week")

    return "\n".join(lines)


def main():
    """Load state, analyze, and send report"""

    if not os.path.exists(STATE_FILE):
        send_telegram("📊 Weekly Report: No state file found (trading not yet started)")
        return

    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except Exception as e:
        send_telegram(f"❌ Error loading state: {e}")
        return

    # Analyze
    analysis = analyze_trades(state)

    # Generate report
    report = generate_report(state, analysis)

    # Send via Telegram
    send_telegram(report)


if __name__ == "__main__":
    main()
