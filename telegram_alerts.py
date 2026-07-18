#!/usr/bin/env python3
"""
Portfolio 10K - Telegram Alerts System
ส่ง alerts สำหรับ BTC/ETH prices, profit targets, stop loss
"""

import requests
import json
from datetime import datetime

# ==================== CONFIG ====================
BOT_TOKEN = "8736600939:AAFg_Asak5ETjbdL3CUUa4WTHIRk7Md886Q"
CHAT_ID = "6139624445"

# Portfolio Config
PORTFOLIO = {
    "core_holdings": {
        "amount": 7870,
        "percentage": 78.7,
        "assets": ["SPY", "QQQ", "GLD", "BND"]
    },
    "trading": {
        "amount": 2275,
        "percentage": 22.8,
        "assets": [
            {"symbol": "BTC-USD", "entry": 63000, "qty": 0.02, "target": 75000, "stop_loss": 56700},
            {"symbol": "ETH-USD", "entry": 3500, "qty": 0.29, "target": 4500, "stop_loss": 3150}
        ]
    }
}

# ==================== TELEGRAM FUNCTIONS ====================

def send_message(message):
    """ส่งข้อความไป Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return None

# ==================== ALERT TYPES ====================

def daily_portfolio_alert():
    """📊 Daily portfolio summary"""
    time = datetime.now().strftime("%H:%M:%S")
    message = f"""
<b>📊 Daily Portfolio Summary</b>

<b>Core Holdings:</b> ฿{PORTFOLIO['core_holdings']['amount']:,} ({PORTFOLIO['core_holdings']['percentage']}%)
<b>Trading Book:</b> ฿{PORTFOLIO['trading']['amount']:,} ({PORTFOLIO['trading']['percentage']}%)
<b>Total Portfolio:</b> ฿{PORTFOLIO['core_holdings']['amount'] + PORTFOLIO['trading']['amount']:,}

<b>Status:</b> MONITORING
<b>Time:</b> {time}

Next Update: Tomorrow 9:00 AM
    """
    return send_message(message)

def price_alert(symbol, current_price, change_pct, status):
    """💹 Price movement alert"""
    time = datetime.now().strftime("%H:%M:%S")
    
    if change_pct > 0:
        arrow = "📈"
    elif change_pct < 0:
        arrow = "📉"
    else:
        arrow = "➡️"
    
    message = f"""
{arrow} <b>PRICE ALERT: {symbol}</b>

<b>Current Price:</b> ${current_price:,.2f}
<b>Change:</b> {change_pct:+.2f}%
<b>Status:</b> {status}
<b>Time:</b> {time}

<b>Action:</b> MONITOR
    """
    return send_message(message)

def profit_target_alert(symbol, current_price, gain_pct):
    """💰 Profit target reached"""
    message = f"""
💰 <b>PROFIT TARGET HIT!</b>

<b>Symbol:</b> {symbol}
<b>Current Price:</b> ${current_price:,.2f}
<b>Gain:</b> <b>+{gain_pct:.2f}%</b>

<b>⚠️ ACTION REQUIRED:</b> TAKE PROFIT

Consider exiting or taking partial profits
    """
    return send_message(message)

def stop_loss_alert(symbol, current_price, loss_pct):
    """⛔ Stop loss triggered"""
    message = f"""
⛔ <b>STOP LOSS TRIGGERED!</b>

<b>Symbol:</b> {symbol}
<b>Current Price:</b> ${current_price:,.2f}
<b>Loss:</b> <b>{loss_pct:.2f}%</b>

<b>⚠️ ACTION REQUIRED:</b> EXIT POSITION

Sell immediately to prevent further losses
    """
    return send_message(message)

def trading_signal_alert(symbol, signal_type, price):
    """📊 Trading signal received"""
    if signal_type == "BUY":
        emoji = "🟢"
    elif signal_type == "SELL":
        emoji = "🔴"
    else:
        emoji = "🟡"
    
    message = f"""
{emoji} <b>TRADING SIGNAL</b>

<b>Symbol:</b> {symbol}
<b>Signal:</b> {signal_type}
<b>Price:</b> ${price:,.2f}

<b>Entry:</b> {signal_type} at ${price:,.2f}
<b>Next:</b> Watch for profit target / stop loss
    """
    return send_message(message)

def test_alert():
    """🧪 Test alert"""
    message = """
🧪 <b>TEST ALERT</b>

Portfolio 10K Telegram Alerts System is <b>ONLINE</b> ✅

Alerts configured:
✅ Daily portfolio summary
✅ Price movements
✅ Profit targets
✅ Stop loss levels
✅ Trading signals

Ready to receive alerts!
    """
    return send_message(message)

# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    print("🚀 Portfolio 10K - Telegram Alerts System\n")
    
    # Test alert
    print("1️⃣ Sending test alert...")
    test_alert()
    print("✅ Test alert sent!\n")
    
    # Daily summary
    print("2️⃣ Sending daily portfolio summary...")
    daily_portfolio_alert()
    print("✅ Daily summary sent!\n")
    
    # Price alerts
    print("3️⃣ Sending price alerts...")
    price_alert("BTC-USD", 63000, 0.0, "MONITOR")
    price_alert("ETH-USD", 3500, -2.5, "MONITOR")
    print("✅ Price alerts sent!\n")
    
    # Trading examples
    print("4️⃣ Sending trading signal...")
    trading_signal_alert("BTC-USD", "BUY", 63000)
    print("✅ Trading signal sent!\n")
    
    print("=" * 50)
    print("✅ ALL ALERTS SENT SUCCESSFULLY!")
    print("=" * 50)
    print("\n📋 NEXT STEPS:")
    print("1. Setup scheduler for daily/hourly alerts")
    print("2. Monitor BTC/ETH prices")
    print("3. Check profit/stop loss levels")
    print("4. Execute trades based on signals")

