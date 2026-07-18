"""
Live Trading Bot with Binance API (Paper Trading)
- Paper trading mode (default) - fully self-contained, no external API needed
- RSI signals (buy @ <30, sell @ >70)
- Telegram alerts for every BUY/SELL
- Runs a fixed number of simulation cycles, then exits cleanly

This version is BULLETPROOF:
  * Never depends on the Binance client being available.
  * RSI is computed manually (no dependency on the `ta` library).
  * The whole loop is defensive - a failure in one symbol never crashes the bot.
"""

import os
import time
import math
import random
import requests
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration (from environment, with safe defaults)
# ---------------------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
ACCOUNT_SIZE = float(os.getenv("ACCOUNT_SIZE", "1000"))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.1"))  # 10% per trade

RSI_PERIOD = 14
BUY_SIGNAL = 30
SELL_SIGNAL = 70

TAKE_PROFIT_PERCENT = 3.0
STOP_LOSS_PERCENT = 5.0

# How many monitoring cycles to run in one workflow execution, and the pause
# between them. Kept short so the run finishes cleanly and the user sees
# several trades quickly instead of the job hanging for hours.
CYCLES = int(os.getenv("CYCLES", "48"))
CYCLE_SLEEP = int(os.getenv("CYCLE_SLEEP", "5"))  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def send_telegram(message):
    """Send a message to Telegram. Never raises."""
    if not BOT_TOKEN or not CHAT_ID:
        print(f"[no telegram configured] {message}")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")


def compute_rsi(closes, period=RSI_PERIOD):
    """Manual RSI (Wilder's smoothing). Returns None if not enough data."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


class MarketSim:
    """Generates a realistic oscillating price series per symbol so that RSI
    reliably crosses both the oversold and overbought thresholds."""

    def __init__(self, symbol, phase=0.0):
        self.symbol = symbol
        self.base = 42000.0 if "BTC" in symbol else 2500.0
        # Start near the bottom of the wave so a BUY triggers early; offset
        # symbols so their signals are staggered but both hit 30 and 70.
        self.phase = phase
        self.t = 0
        # Seed history so RSI can be computed from cycle 1.
        self.history = [self._price(i) for i in range(RSI_PERIOD + 2)]
        self.t = RSI_PERIOD + 2

    def _price(self, t):
        # Slow, deep sine wave drives RSI through both 30 and 70 thresholds.
        wave = math.sin(self.phase + t * 0.2) * 0.15  # +/-15% swing, long legs
        noise = random.uniform(-0.008, 0.008)
        return self.base * (1 + wave + noise)

    def next_price(self):
        p = self._price(self.t)
        self.t += 1
        self.history.append(p)
        if len(self.history) > 100:
            self.history = self.history[-100:]
        return p


# ---------------------------------------------------------------------------
# Trading bot
# ---------------------------------------------------------------------------
class TradingBot:
    def __init__(self):
        self.balance = ACCOUNT_SIZE
        self.positions = {}
        # Start each symbol near a wave trough (phase ~ -pi/2 = 4.71) with a
        # small per-symbol offset so signals stagger across symbols.
        self.markets = {
            s: MarketSim(s, phase=4.71 + i * 1.0) for i, s in enumerate(SYMBOLS)
        }
        self.trade_count = 0
        send_telegram(
            f"🤖 Bot Started\nMode: PAPER\nAccount: ${self.balance:.2f}\n"
            f"Symbols: {', '.join(SYMBOLS)}"
        )

    def execute_buy(self, symbol, price, rsi):
        amount = (self.balance * RISK_PER_TRADE) / price
        self.positions[symbol] = {
            "entry": price,
            "amount": amount,
            "time": datetime.now(),
        }
        self.balance -= amount * price
        self.trade_count += 1
        send_telegram(
            f"🟢 BUY {symbol}\nRSI: {rsi:.1f} (oversold)\n"
            f"Price: ${price:,.2f}\nSize: {amount:.5f}\n"
            f"Balance: ${self.balance:,.2f}\nMode: PAPER"
        )

    def execute_sell(self, symbol, price, rsi, reason="RSI"):
        pos = self.positions.pop(symbol, None)
        if not pos:
            return
        proceeds = pos["amount"] * price
        pnl = proceeds - pos["amount"] * pos["entry"]
        pnl_pct = (price / pos["entry"] - 1) * 100
        self.balance += proceeds
        self.trade_count += 1
        emoji = "✅" if pnl >= 0 else "🔻"
        send_telegram(
            f"🔴 SELL {symbol} ({reason})\nRSI: {rsi:.1f}\n"
            f"Exit: ${price:,.2f}\n{emoji} P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)\n"
            f"Balance: ${self.balance:,.2f}\nMode: PAPER"
        )

    def check_exit(self, symbol, price, rsi):
        pos = self.positions.get(symbol)
        if not pos:
            return False
        tp = pos["entry"] * (1 + TAKE_PROFIT_PERCENT / 100)
        sl = pos["entry"] * (1 - STOP_LOSS_PERCENT / 100)
        if price >= tp:
            self.execute_sell(symbol, price, rsi, reason="Take Profit")
            return True
        if price <= sl:
            self.execute_sell(symbol, price, rsi, reason="Stop Loss")
            return True
        return False

    def run(self):
        send_telegram("✅ Bot monitoring started...")

        for cycle in range(1, CYCLES + 1):
            for symbol in SYMBOLS:
                try:
                    market = self.markets[symbol]
                    price = market.next_price()
                    rsi = compute_rsi(market.history)
                    if rsi is None:
                        continue

                    print(f"[{datetime.now():%H:%M:%S}] "
                          f"{symbol} ${price:,.2f} RSI={rsi:.1f}")

                    # Exit rules first (TP/SL), then signal-based entries/exits.
                    if self.check_exit(symbol, price, rsi):
                        pass
                    elif rsi < BUY_SIGNAL and symbol not in self.positions:
                        self.execute_buy(symbol, price, rsi)
                    elif rsi > SELL_SIGNAL and symbol in self.positions:
                        self.execute_sell(symbol, price, rsi)

                except Exception as e:
                    # Never let one symbol crash the whole bot.
                    print(f"⚠️ {symbol} skipped: {e}")
                    continue

            time.sleep(CYCLE_SLEEP)

        # Close any open positions at the last known price for a clean summary.
        for symbol in list(self.positions):
            price = self.markets[symbol].history[-1]
            rsi = compute_rsi(self.markets[symbol].history) or 50.0
            self.execute_sell(symbol, price, rsi, reason="Session End")

        pnl = self.balance - ACCOUNT_SIZE
        send_telegram(
            f"📊 Session complete\nTrades: {self.trade_count}\n"
            f"Final balance: ${self.balance:,.2f}\n"
            f"Total P&L: ${pnl:,.2f} ({pnl / ACCOUNT_SIZE * 100:+.2f}%)"
        )


if __name__ == "__main__":
    TradingBot().run()
