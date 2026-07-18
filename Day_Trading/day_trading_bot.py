#!/usr/bin/env python3
"""
Day Trading Bot - Intraday Trading System
Trades BTC/ETH with technical indicators
Entry: RSI oversold/overbought
Exit: +3% profit or -5% stop loss
"""

import requests
import json
from datetime import datetime, timedelta
import time

# Configuration
BOT_TOKEN = "8736600939:AAFg_Asak5ETjbdL3CUUa4WTHIRk7Md886Q"
CHAT_ID = "6139624445"

# Trading Config
SYMBOLS = ["BTC-USD", "ETH-USD"]
TIMEFRAME = "1h"  # 1 hour candles
RSI_PERIOD = 14
ENTRY_RSI_OVERSOLD = 30  # Buy signal
ENTRY_RSI_OVERBOUGHT = 70  # Sell signal (short)
PROFIT_TARGET = 1.03  # +3%
STOP_LOSS = 0.95  # -5%
MAX_POSITION_SIZE = 0.01  # BTC / 0.1 ETH

# Portfolio tracking
ACTIVE_TRADES = {
    "BTC-USD": {"entry_price": None, "quantity": 0, "entry_time": None},
    "ETH-USD": {"entry_price": None, "quantity": 0, "entry_time": None}
}

def send_telegram(message):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    if len(prices) < period + 1:
        return None
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    seed = deltas[:period]
    up = sum([x for x in seed if x > 0]) / period
    down = -sum([x for x in seed if x < 0]) / period
    
    if down == 0:
        return 100 if up > 0 else 0
    
    rs = up / down
    rsi = 100 - (100 / (1 + rs))
    
    for delta in deltas[period:]:
        up = (up * (period - 1) + (delta if delta > 0 else 0)) / period
        down = (down * (period - 1) + (-delta if delta < 0 else 0)) / period
        rs = up / down
        rsi = 100 - (100 / (1 + rs))
    
    return rsi

def get_current_price(symbol):
    """Get current price from CoinGecko (free API)"""
    try:
        if "BTC" in symbol:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            data = response.json()
            return data['bitcoin']['usd']
        elif "ETH" in symbol:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            data = response.json()
            return data['ethereum']['usd']
    except Exception as e:
        print(f"❌ Price fetch error: {e}")
        return None

def check_entry_signals():
    """Check for day trading entry signals"""
    print(f"\n⏰ Checking entry signals - {datetime.now().strftime('%H:%M:%S')}")
    
    for symbol in SYMBOLS:
        price = get_current_price(symbol)
        if not price:
            continue
        
        # Simulate RSI (in production, use real price history)
        # For demo: random RSI between 25-75
        import random
        rsi = random.uniform(25, 75)
        
        print(f"\n📊 {symbol}")
        print(f"   Price: ${price:,.0f}")
        print(f"   RSI: {rsi:.1f}")
        
        # Entry Signal - Oversold (Buy)
        if rsi < ENTRY_RSI_OVERSOLD and ACTIVE_TRADES[symbol]["quantity"] == 0:
            send_telegram(f"""
<b>🚀 BUY SIGNAL - {symbol}</b>
━━━━━━━━━━━━━━━━━━━━
📈 RSI: {rsi:.1f} (Oversold)
💰 Price: ${price:,.0f}
🎯 Target: ${price * PROFIT_TARGET:,.0f} (+3%)
⛔ Stop Loss: ${price * STOP_LOSS:,.0f} (-5%)
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
Action: <b>ENTRY - BUY</b>
""")
            print(f"   ✅ BUY signal generated!")
            ACTIVE_TRADES[symbol]["entry_price"] = price
            ACTIVE_TRADES[symbol]["entry_time"] = datetime.now()
        
        # Entry Signal - Overbought (Sell/Short)
        elif rsi > ENTRY_RSI_OVERBOUGHT and ACTIVE_TRADES[symbol]["quantity"] == 0:
            send_telegram(f"""
<b>📉 SELL SIGNAL - {symbol}</b>
━━━━━━━━━━━━━━━━━━━━
📉 RSI: {rsi:.1f} (Overbought)
💰 Price: ${price:,.0f}
🎯 Target: ${price * (1 - 0.03):,.0f} (-3%)
⛔ Stop Loss: ${price * (1 + 0.05):,.0f} (+5%)
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
Action: <b>ENTRY - SHORT</b>
""")
            print(f"   ⚠️ SELL signal generated!")

def check_exit_signals():
    """Check for day trading exit signals"""
    for symbol in SYMBOLS:
        if ACTIVE_TRADES[symbol]["quantity"] == 0:
            continue
        
        price = get_current_price(symbol)
        if not price:
            continue
        
        entry = ACTIVE_TRADES[symbol]["entry_price"]
        profit_pct = (price - entry) / entry * 100
        
        # Check profit target (+3%)
        if price >= entry * PROFIT_TARGET:
            profit = (price - entry) * ACTIVE_TRADES[symbol]["quantity"]
            send_telegram(f"""
<b>🎉 PROFIT TARGET HIT - {symbol}</b>
━━━━━━━━━━━━━━━━━━━━
Entry: ${entry:,.0f}
Exit: ${price:,.0f}
Profit: +{profit_pct:.2f}%
Amount: ฿{profit:.2f}
Time held: {(datetime.now() - ACTIVE_TRADES[symbol]["entry_time"]).total_seconds() / 60:.0f} minutes
━━━━━━━━━━━━━━━━━━━━
Action: <b>CLOSE - PROFIT</b>
""")
            ACTIVE_TRADES[symbol]["quantity"] = 0
            ACTIVE_TRADES[symbol]["entry_price"] = None
        
        # Check stop loss (-5%)
        elif price <= entry * STOP_LOSS:
            loss = (price - entry) * ACTIVE_TRADES[symbol]["quantity"]
            send_telegram(f"""
<b>⛔ STOP LOSS HIT - {symbol}</b>
━━━━━━━━━━━━━━━━━━━━
Entry: ${entry:,.0f}
Exit: ${price:,.0f}
Loss: {profit_pct:.2f}%
Amount: ฿{loss:.2f}
Time held: {(datetime.now() - ACTIVE_TRADES[symbol]["entry_time"]).total_seconds() / 60:.0f} minutes
━━━━━━━━━━━━━━━━━━━━
Action: <b>CLOSE - STOP LOSS</b>
""")
            ACTIVE_TRADES[symbol]["quantity"] = 0
            ACTIVE_TRADES[symbol]["entry_price"] = None
        
        # Daily timeout (close all positions before market close)
        if datetime.now().hour >= 20:  # 8 PM - close all day trades
            if ACTIVE_TRADES[symbol]["quantity"] > 0:
                send_telegram(f"""
<b>⏰ MARKET CLOSE - {symbol}</b>
━━━━━━━━━━━━━━━━━━━━
Closing all day positions before market close
Current Price: ${price:,.0f}
Profit/Loss: {profit_pct:.2f}%
━━━━━━━━━━━━━━━━━━━━
Action: <b>CLOSE - END OF DAY</b>
""")
                ACTIVE_TRADES[symbol]["quantity"] = 0
                ACTIVE_TRADES[symbol]["entry_price"] = None

def print_status():
    """Print current trading status"""
    print("\n" + "="*60)
    print("🤖 DAY TRADING BOT STATUS")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scan interval: Every 60 seconds")
    print()
    
    for symbol in SYMBOLS:
        price = get_current_price(symbol)
        if price:
            print(f"📊 {symbol}")
            print(f"   Current Price: ${price:,.0f}")
            if ACTIVE_TRADES[symbol]["quantity"] > 0:
                entry = ACTIVE_TRADES[symbol]["entry_price"]
                profit = (price - entry) / entry * 100
                print(f"   Status: 🔴 OPEN")
                print(f"   Entry: ${entry:,.0f}")
                print(f"   P&L: {profit:+.2f}%")
            else:
                print(f"   Status: ⚪ IDLE (waiting for signal)")
        print()

def run_bot():
    """Main bot loop"""
    print("="*60)
    print("🚀 DAY TRADING BOT STARTED")
    print("="*60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("⚙️  Configuration:")
    print(f"   Symbols: {', '.join(SYMBOLS)}")
    print(f"   Entry RSI: {ENTRY_RSI_OVERSOLD} (oversold), {ENTRY_RSI_OVERBOUGHT} (overbought)")
    print(f"   Profit Target: +3%")
    print(f"   Stop Loss: -5%")
    print(f"   Max Position: {MAX_POSITION_SIZE} BTC / 0.1 ETH")
    print()
    print("🔄 Bot running... (Ctrl+C to stop)")
    print("="*60)
    
    send_telegram("🚀 <b>DAY TRADING BOT STARTED</b>\n\nMonitoring: BTC-USD, ETH-USD\nEntry signals: RSI < 30 (buy), RSI > 70 (sell)")
    
    try:
        while True:
            print_status()
            check_entry_signals()
            check_exit_signals()
            
            # Check every 60 seconds
            for i in range(60):
                time.sleep(1)
                if i % 30 == 0:
                    print(f"⏳ Next check in {60-i} seconds...")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  BOT STOPPED")
        print(f"Stop time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        send_telegram("⏹️ <b>DAY TRADING BOT STOPPED</b>")

if __name__ == "__main__":
    run_bot()
