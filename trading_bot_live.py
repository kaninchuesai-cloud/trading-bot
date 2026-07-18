"""
Paper-Trading Bot on REAL market data (forward test).

Strategy: RSI + Moving Averages + Support/Resistance
  * Data: real hourly BTC/ETH prices (CoinGecko -> Kraken -> Coinbase fallback)
  * One evaluation per run (designed to be run hourly by GitHub Actions cron)
  * Persistent state in state.json so P&L accumulates across runs
  * Telegram report every run; prominent alerts on BUY/SELL

This is PAPER trading: no real orders are placed. It simulates trades against
real prices so we can see whether the rules would have made or lost money.
"""

import os
import json
import time
import urllib.request
from datetime import datetime, timezone

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# CoinGecko ids -> our display symbols
ASSETS = {"BTCUSDT": "bitcoin", "ETHUSDT": "ethereum"}

START_BALANCE = float(os.getenv("ACCOUNT_SIZE", "1000"))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.1"))    # 10% of cash per trade

# Strategy thresholds
RSI_PERIOD = 14
RSI_BUY = float(os.getenv("RSI_BUY", "38"))      # oversold entry
RSI_SELL = float(os.getenv("RSI_SELL", "68"))    # overbought exit
NEAR_SUPPORT = float(os.getenv("NEAR_SUPPORT", "0.02"))   # within 2% of MA20/support
NEAR_RESIST = float(os.getenv("NEAR_RESIST", "0.01"))     # within 1% of resistance
TAKE_PROFIT = float(os.getenv("TAKE_PROFIT", "4.0"))      # +4%
STOP_LOSS = float(os.getenv("STOP_LOSS", "3.0"))         # -3%
SR_LOOKBACK = int(os.getenv("SR_LOOKBACK", "48"))        # candles for support/resistance

STATE_FILE = os.getenv("STATE_FILE", "state.json")
# After this UTC time the bot closes everything and stops trading.
STOP_DATE = os.getenv("STOP_DATE", "2026-07-21T00:00:00")


# --------------------------------------------------------------------------- #
# Telegram
# --------------------------------------------------------------------------- #
def send_telegram(message):
    print(message)
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        data = json.dumps({"chat_id": CHAT_ID, "text": message}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"Telegram error: {e}")


# --------------------------------------------------------------------------- #
# Real market data (fallback chain). Returns list of hourly closes, oldest -> newest.
# --------------------------------------------------------------------------- #
def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "paper-bot/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=25))


def fetch_hourly_closes(display_symbol, gecko_id):
    """Try several free, no-key sources so at least one works on the runner."""
    # 1) CoinGecko (price series, ~5min/hourly depending on range)
    try:
        d = _get(f"https://api.coingecko.com/api/v3/coins/{gecko_id}"
                 f"/market_chart?vs_currency=usd&days=5")
        closes = [p[1] for p in d["prices"]]
        # thin to ~hourly if finer granularity was returned
        if len(closes) > 200:
            closes = closes[::max(1, len(closes) // 150)]
        if len(closes) >= RSI_PERIOD + 2:
            return closes, "CoinGecko"
    except Exception as e:
        print(f"CoinGecko failed ({display_symbol}): {e}")

    # 2) Kraken OHLC (hourly). XBT for BTC.
    try:
        pair = "XBTUSD" if "BTC" in display_symbol else "ETHUSD"
        d = _get(f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=60")
        result = d["result"]
        key = [k for k in result if k != "last"][0]
        closes = [float(c[4]) for c in result[key]]
        if len(closes) >= RSI_PERIOD + 2:
            return closes, "Kraken"
    except Exception as e:
        print(f"Kraken failed ({display_symbol}): {e}")

    # 3) Coinbase candles (hourly, newest first -> reverse)
    try:
        prod = "BTC-USD" if "BTC" in display_symbol else "ETH-USD"
        d = _get(f"https://api.exchange.coinbase.com/products/{prod}"
                 f"/candles?granularity=3600")
        closes = [row[4] for row in d][::-1]  # row = [t,low,high,open,close,vol]
        if len(closes) >= RSI_PERIOD + 2:
            return closes, "Coinbase"
    except Exception as e:
        print(f"Coinbase failed ({display_symbol}): {e}")

    return None, None


# --------------------------------------------------------------------------- #
# Indicators
# --------------------------------------------------------------------------- #
def rsi(closes, period=RSI_PERIOD):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
    if al == 0:
        return 100.0
    rs = ag / al
    return 100.0 - 100.0 / (1.0 + rs)


def sma(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def support_resistance(closes, lookback=SR_LOOKBACK):
    window = closes[-lookback:] if len(closes) >= lookback else closes
    return min(window), max(window)


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "start_balance": START_BALANCE,
        "balance": START_BALANCE,
        "positions": {},
        "trades": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "runs": 0,
        "final_done": False,
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# --------------------------------------------------------------------------- #
# Strategy
# --------------------------------------------------------------------------- #
def evaluate(display_symbol, closes, state):
    """Return a human-readable status line; mutates state on trades."""
    price = closes[-1]
    r = rsi(closes)
    ma20 = sma(closes, 20)
    ma50 = sma(closes, 50) or sma(closes, len(closes) - 1)
    support, resistance = support_resistance(closes)

    if r is None or ma20 is None or ma50 is None:
        return f"{display_symbol}: not enough data"

    trend = "UP" if ma20 > ma50 else "DOWN"
    pos = state["positions"].get(display_symbol)

    # ---- Exit logic (if holding) ----
    if pos:
        entry = pos["entry"]
        pnl_pct = (price / entry - 1) * 100
        reason = None
        if r > RSI_SELL:
            reason = f"RSI {r:.0f} overbought"
        elif price >= resistance * (1 - NEAR_RESIST):
            reason = "hit resistance"
        elif pnl_pct >= TAKE_PROFIT:
            reason = f"take profit +{pnl_pct:.1f}%"
        elif pnl_pct <= -STOP_LOSS:
            reason = f"stop loss {pnl_pct:.1f}%"
        if reason:
            proceeds = pos["amount"] * price
            pnl = proceeds - pos["amount"] * entry
            state["balance"] += proceeds
            state["trades"].append({
                "symbol": display_symbol, "side": "SELL", "price": price,
                "amount": pos["amount"], "pnl": pnl, "pnl_pct": pnl_pct,
                "reason": reason, "time": datetime.now(timezone.utc).isoformat(),
            })
            del state["positions"][display_symbol]
            emoji = "✅" if pnl >= 0 else "🔻"
            send_telegram(
                f"🔴 SELL {display_symbol} ({reason})\n"
                f"Exit: ${price:,.2f}\n{emoji} P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)\n"
                f"Cash: ${state['balance']:,.2f}"
            )
            return (f"{display_symbol} ${price:,.2f} | RSI {r:.0f} | "
                    f"MA20 {ma20:,.0f}/{ma50:,.0f} {trend} | SOLD")
        return (f"{display_symbol} ${price:,.2f} | RSI {r:.0f} | "
                f"MA20 {ma20:,.0f}/{ma50:,.0f} {trend} | HOLD ({pnl_pct:+.1f}%)")

    # ---- Entry logic (if flat) ----
    cond_rsi = r < RSI_BUY
    cond_trend = ma20 > ma50                 # uptrend STRUCTURE (buy dips in uptrend)
    # Pullback to dynamic support (price at/near MA20), or price near the
    # static support level - either counts as a good entry zone.
    cond_support = (price <= ma20 * (1 + NEAR_SUPPORT)
                    or price <= support * (1 + NEAR_SUPPORT))
    if cond_rsi and cond_trend and cond_support:
        amount = (state["balance"] * RISK_PER_TRADE) / price
        cost = amount * price
        state["balance"] -= cost
        state["positions"][display_symbol] = {
            "entry": price, "amount": amount,
            "opened": datetime.now(timezone.utc).isoformat(),
        }
        state["trades"].append({
            "symbol": display_symbol, "side": "BUY", "price": price,
            "amount": amount, "pnl": 0.0, "pnl_pct": 0.0,
            "reason": f"RSI {r:.0f} + uptrend + near support",
            "time": datetime.now(timezone.utc).isoformat(),
        })
        send_telegram(
            f"🟢 BUY {display_symbol}\n"
            f"Reason: RSI {r:.0f} oversold + {trend}trend + near support\n"
            f"Price: ${price:,.2f}\nSize: {amount:.5f}\n"
            f"Support ${support:,.0f} / Resistance ${resistance:,.0f}\n"
            f"Cash: ${state['balance']:,.2f}"
        )
        return (f"{display_symbol} ${price:,.2f} | RSI {r:.0f} | "
                f"MA20 {ma20:,.0f}/{ma50:,.0f} {trend} | BOUGHT")

    # No action - explain why (which condition blocked entry)
    miss = []
    if not cond_rsi:
        miss.append(f"RSI {r:.0f}≥{RSI_BUY:.0f}")
    if not cond_trend:
        miss.append("downtrend (MA20<MA50)")
    if not cond_support:
        miss.append("above MA20 (no pullback)")
    return (f"{display_symbol} ${price:,.2f} | RSI {r:.0f} | "
            f"MA20 {ma20:,.0f}/{ma50:,.0f} {trend} | wait ({', '.join(miss)})")


# --------------------------------------------------------------------------- #
# Main (one evaluation per run)
# --------------------------------------------------------------------------- #
def main():
    state = load_state()
    state["runs"] = state.get("runs", 0) + 1
    now = datetime.now(timezone.utc)

    # Fetch prices + last known prices for equity calc
    last_prices = {}
    status_lines = []
    stop = now >= datetime.fromisoformat(STOP_DATE).replace(tzinfo=timezone.utc)

    for sym, gid in ASSETS.items():
        closes, source = fetch_hourly_closes(sym, gid)
        if not closes:
            status_lines.append(f"{sym}: price fetch failed (all sources)")
            continue
        last_prices[sym] = closes[-1]
        if stop:
            continue  # don't open/close via rules; we wind down below
        status_lines.append(evaluate(sym, closes, state))
        time.sleep(1)  # be gentle with the API

    # Wind-down after the test period: close everything at last price.
    if stop and not state.get("final_done"):
        for sym in list(state["positions"]):
            price = last_prices.get(sym)
            if not price:
                continue
            pos = state["positions"][sym]
            proceeds = pos["amount"] * price
            pnl = proceeds - pos["amount"] * pos["entry"]
            state["balance"] += proceeds
            state["trades"].append({
                "symbol": sym, "side": "SELL", "price": price,
                "amount": pos["amount"], "pnl": pnl,
                "pnl_pct": (price / pos["entry"] - 1) * 100,
                "reason": "test period ended", "time": now.isoformat(),
            })
            del state["positions"][sym]
        state["final_done"] = True

    # Equity = cash + open positions marked to market
    equity = state["balance"]
    for sym, pos in state["positions"].items():
        if sym in last_prices:
            equity += pos["amount"] * last_prices[sym]
    total_pnl = equity - state["start_balance"]
    total_pct = total_pnl / state["start_balance"] * 100
    n_trades = len([t for t in state["trades"] if t["side"] == "SELL"])
    wins = len([t for t in state["trades"] if t["side"] == "SELL" and t["pnl"] > 0])

    header = "🏁 TEST ENDED\n" if stop else f"📟 Hourly check #{state['runs']}\n"
    summary = (
        header +
        f"{now:%Y-%m-%d %H:%M} UTC\n\n" +
        "\n".join(status_lines) +
        f"\n\n💼 Equity: ${equity:,.2f}\n"
        f"📈 Total P&L: ${total_pnl:,.2f} ({total_pct:+.2f}%)\n"
        f"🔁 Closed trades: {n_trades} (wins: {wins})\n"
        f"📊 Open: {', '.join(state['positions']) or 'none'}"
    )
    send_telegram(summary)
    save_state(state)


if __name__ == "__main__":
    main()
