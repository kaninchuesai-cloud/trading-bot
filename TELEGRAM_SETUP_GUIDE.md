# 🔔 TELEGRAM ALERTS SETUP GUIDE

## Phase 3: Alert System

---

## STEP 1: สร้าง Telegram Bot

### 1.1 เปิด Telegram
- ค้นหา **@BotFather**
- Click "Start"

### 1.2 สร้าง Bot ใหม่
พิมพ์: `/newbot`

**ตอบคำถาม:**
- **ชื่อ Bot:** `Pooh Trading Bot` (หรือชื่ออื่น)
- **Username:** `pooh_trading_bot_xxxxx` (ต้องไม่ซ้ำ)

### 1.3 ได้ Token
BotFather จะให้:
```
🎉 Done! Congratulations on your new bot. 
You will find it at t.me/pooh_trading_bot_xxxxx. 
You can now add a description, about section and more using these commands. 
Keep your token secure and store it safely!

Your bot token is:
123456789:ABCdefGHIjklmnoPQRstuvWXYZabcdefghi
```

**💾 Copy token นี้ไว้!**

---

## STEP 2: ได้ Chat ID

### 2.1 เปิด Bot ที่สร้าง
- ไป `t.me/pooh_trading_bot_xxxxx`
- Click "Start"

### 2.2 ได้ Chat ID
ไปที่: `https://api.telegram.org/bot{YOUR_TOKEN}/getUpdates`

แทน `{YOUR_TOKEN}` ด้วย token จาก step 1.3

จะได้ JSON แบบนี้:
```json
{
  "ok": true,
  "result": [
    {
      "update_id": 123456789,
      "message": {
        "message_id": 1,
        "chat": {
          "id": 987654321,
          "type": "private"
        }
      }
    }
  ]
}
```

**💾 Copy Chat ID:** `987654321`

---

## STEP 3: ตั้งค่า Python Script

### 3.1 Alert Template

ใช้ Python script เพื่อส่ง alerts:

```python
import requests
import json

# Config
BOT_TOKEN = "YOUR_TOKEN_HERE"
CHAT_ID = "YOUR_CHAT_ID_HERE"

def send_alert(message):
    """ส่งข้อความ Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    return response.json()

# Example: Price Alert
def price_alert(symbol, price, action):
    message = f"""
🚨 <b>PRICE ALERT</b>

Symbol: <b>{symbol}</b>
Price: <b>{price:,.2f}</b>
Action: <b>{action}</b>
Time: {datetime.now().strftime('%H:%M:%S')}
    """
    send_alert(message)

# Example: Profit Alert
def profit_alert(symbol, gain_pct, amount):
    message = f"""
💰 <b>PROFIT TARGET HIT!</b>

Symbol: <b>{symbol}</b>
Gain: <b>{gain_pct}%</b>
Amount: <b>฿{amount:,.2f}</b>
Action: <b>TAKE PROFIT</b>
    """
    send_alert(message)

# Example: Stop Loss Alert
def stop_loss_alert(symbol, loss_pct, amount):
    message = f"""
⛔ <b>STOP LOSS TRIGGERED!</b>

Symbol: <b>{symbol}</b>
Loss: <b>{loss_pct}%</b>
Amount: <b>฿{amount:,.2f}</b>
Action: <b>EXIT POSITION</b>
    """
    send_alert(message)
```

---

## STEP 4: Alert Rules (จากไฟล์ Trading_System_Rules.md)

### Core Holdings
- ✅ HOLD 5+ years
- ℹ️ Monthly review
- 🔄 Rebalance if >10% off

### Trading Positions
- 📈 **Take Profit:** +25%
- 📉 **Stop Loss:** -10%
- 📊 Entry: Bot signal
- ⏰ Review: Whenever price hits target

### Alert Schedule
- **Price Alerts:** Every 4 hours (BTC, ETH)
- **Portfolio Update:** Daily 9:00 AM
- **Weekly Report:** Every Monday
- **Critical Alerts:** Instant (target/stop loss)

---

## STEP 5: Messages Template

### 📍 Daily Status
```
📊 Daily Portfolio Update

Core Holdings: ฿7,870 (78.7%)
Trading Book: ฿2,275 (22.8%)
Total: ฿10,145

Top Performer: SPY ↑ 0%
Today's Action: HOLD

Next Check: Tomorrow 9:00 AM
```

### 📈 Price Movement
```
💹 BTC-USD Price Update

Current: $63,000
Change: ±0%
Status: MONITOR
Target: $75,000
Stop Loss: $56,700

Action: HOLD POSITION
```

### ✅ Trade Executed
```
✅ TRADE EXECUTED

Symbol: BTC-USD
Type: BUY
Price: $63,000
Qty: 0.02
Entry: Portfolio Alert

Next: Watch for +25% profit target
```

---

## STEP 6: Testing

### Test 1: ส่ง test message
```python
send_alert("🧪 Test Alert - Portfolio Setup Complete!")
```

### Test 2: ตรวจสอบ Telegram
ควรได้ข้อความใน Telegram

### Test 3: Try Different Alert Types
```python
price_alert("BTC-USD", 63000, "MONITOR")
profit_alert("SPY", 5.2, 155)
stop_loss_alert("ETH-USD", -10, -101.50)
```

---

## SUMMARY

| Step | Done | Notes |
|------|------|-------|
| 1. Create Bot | ☐ | Get BOT_TOKEN from @BotFather |
| 2. Get Chat ID | ☐ | From getUpdates API |
| 3. Save Credentials | ☐ | Keep TOKEN & CHAT_ID safe |
| 4. Test Message | ☐ | Send test via Telegram API |
| 5. Set Alerts | ☐ | Configure alert rules |
| 6. Monitor | ☐ | Check alerts daily |

---

## ⚠️ SECURITY NOTES

🔐 **Never share your:**
- BOT_TOKEN (anyone can use your bot)
- CHAT_ID (if you want privacy)

✅ **Best Practice:**
- Store in `.env` file
- Don't commit to GitHub
- Use environment variables

---

## NEXT: Phase 3 Implementation

Once setup:
1. Run alerts script daily
2. Monitor BTC/ETH prices
3. Check profit/stop loss levels
4. Adjust as needed

👉 **Ready to implement?** Let me know when you have BOT_TOKEN & CHAT_ID!

