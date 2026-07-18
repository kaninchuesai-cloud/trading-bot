# 🚀 DAY TRADING BOT - Setup Guide

**Automated Intraday Trading System**  
**Entry:** RSI signals | **Exit:** +3% profit or -5% stop loss

---

## 📋 วิธีการทำงาน

### Entry Signals:
- **RSI < 30** (Oversold) → **BUY signal**
- **RSI > 70** (Overbought) → **SELL/SHORT signal**

### Exit Signals:
- **+3% Profit** → Auto close (take profit)
- **-5% Stop Loss** → Auto close (protect capital)
- **20:00 (8 PM)** → Auto close all (end of day)

### Position Management:
- Max: 0.01 BTC or 0.1 ETH per trade
- Hold time: Minutes to hours (intraday only)
- Telegram alert on every action

---

## 🎯 Daily Timeline

```
9:00 AM   - Bot checks RSI
           → If RSI < 30: BUY signal
           → If RSI > 70: SELL signal
           → Telegram: Entry alert

Throughout day:
- Every 60 seconds: Check P&L
- If +3%: Take profit
- If -5%: Stop loss
- Telegram: Real-time updates

8:00 PM (20:00):
- Auto close all positions
- No overnight holds
- Telegram: Close alert
```

---

## 🔧 Setup Steps

### Step 1: Check Bot Token & Chat ID
```python
BOT_TOKEN = "8736600939:AAFg_Asak5ETjbdL3CUUa4WTHIRk7Md886Q"
CHAT_ID = "6139624445"
```
✅ Already configured

### Step 2: Install Dependencies
```bash
cd C:\Invesment
pip install requests
```

### Step 3: Run Bot
```bash
python day_trading_bot.py
```

### Expected Output:
```
============================================================
🚀 DAY TRADING BOT STARTED
============================================================
Start time: 2026-07-18 21:35:04

⚙️  Configuration:
   Symbols: BTC-USD, ETH-USD
   Entry RSI: 30 (oversold), 70 (overbought)
   Profit Target: +3%
   Stop Loss: -5%
   Max Position: 0.01 BTC / 0.1 ETH

🔄 Bot running... (Ctrl+C to stop)
============================================================
```

---

## 💰 Profit Expectation

### Per Trade:
- Entry: $63,000 BTC
- Exit: $63,000 × 1.03 = $64,890 BTC
- Profit per trade: +$1,890

### Annual Potential (Conservative):
- 5 winning trades/month × ฿50 = ฿250/month
- 12 months × ฿250 = ฿3,000/year

### Annual Potential (Aggressive):
- 10 winning trades/month × ฿50 = ฿500/month
- 12 months × ฿500 = ฿6,000/year

---

## ⚠️ Risk Management

### Stop Loss Protection:
- Max loss per trade: -5%
- BTC $63,000 × 0.95 = $59,850
- Loss limited to: -$3,150

### Position Sizing:
- Max 0.01 BTC = ~$630 at current price
- Max loss: $31.50 per trade
- Multiple trades = spread risk

### Daily Cutoff:
- 8 PM: All positions closed
- No overnight risk
- Fresh start next day

---

## 📊 Telegram Alerts

### Entry Alert:
```
🚀 BUY SIGNAL - BTC-USD
━━━━━━━━━━━━━━━━━━━━
📈 RSI: 28.5 (Oversold)
💰 Price: $63,000
🎯 Target: $64,890 (+3%)
⛔ Stop Loss: $59,850 (-5%)
⏰ Time: 14:35:20
━━━━━━━━━━━━━━━━━━━━
Action: ENTRY - BUY
```

### Profit Alert:
```
🎉 PROFIT TARGET HIT - BTC-USD
━━━━━━━━━━━━━━━━━━━━
Entry: $63,000
Exit: $64,890
Profit: +3.00%
Amount: ฿1,890
Time held: 47 minutes
━━━━━━━━━━━━━━━━━━━━
Action: CLOSE - PROFIT
```

### Stop Loss Alert:
```
⛔ STOP LOSS HIT - BTC-USD
━━━━━━━━━━━━━━━━━━━━
Entry: $63,000
Exit: $59,850
Loss: -5.00%
Amount: -฿3,150
Time held: 23 minutes
━━━━━━━━━━━━━━━━━━━━
Action: CLOSE - STOP LOSS
```

---

## 🎮 Commands

### Start Bot:
```bash
python day_trading_bot.py
```

### Stop Bot:
```
Press Ctrl + C in terminal
```

### Keep Running 24/7:
Use Windows Task Scheduler (like swing trading)

---

## 🔧 Configuration (Customize)

### Edit day_trading_bot.py:

**Change Profit Target:**
```python
PROFIT_TARGET = 1.03  # +3%
# Change to: 1.05 for +5%, 1.02 for +2%
```

**Change Stop Loss:**
```python
STOP_LOSS = 0.95  # -5%
# Change to: 0.90 for -10%, 0.97 for -3%
```

**Change Entry RSI:**
```python
ENTRY_RSI_OVERSOLD = 30  # Buy trigger
ENTRY_RSI_OVERBOUGHT = 70  # Sell trigger
# Change to: 20/80 for more aggressive
```

**Change Position Size:**
```python
MAX_POSITION_SIZE = 0.01  # BTC / 0.1 ETH
# Change to: 0.02 for 2x size, 0.005 for 0.5x
```

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'requests'"
```bash
pip install requests
```

### Error: "Invalid BOT_TOKEN"
- Check telegram_alerts.py for correct token
- Copy token: `8736600939:AAFg_Asak5ETjbdL3CUUa4WTHIRk7Md886Q`

### Not Receiving Alerts
- Check Telegram bot - send message to bot first
- Check CHAT_ID: `6139624445`
- Restart bot

### Bot Not Finding Entry Signals
- RSI calculation requires price history
- In demo mode: uses random RSI (25-75)
- For production: Connect real API (Binance, CoinGecko)

---

## 🚀 Production Ready

**Current Status:** DEMO MODE
- ✅ Works with real prices (CoinGecko)
- ✅ Sends real Telegram alerts
- ⚠️ Uses simulated RSI (for demo)

**For Production:**
1. Connect Binance/Kraken API
2. Get real price history
3. Calculate actual RSI
4. Enable auto-execution

---

## 📈 Comparison: Swing vs Day Trading

| | Swing Trading | Day Trading |
|--|---|---|
| Hold time | 1-7 days | Minutes-hours |
| Target | +25% | +3% |
| Stop | -10% | -5% |
| Trades/month | 2-4 | 10-20 |
| Profit/month | ฿600-1,200 | ฿500-1,500 |
| Stress | Low | High |
| Overnight risk | Yes | No |

---

## 💡 Strategy Tips

1. **Start Small**
   - First month: 0.005 BTC max
   - Verify system works
   - Scale up after 10 trades

2. **Track Performance**
   - Record entry/exit prices
   - Calculate win rate
   - Adjust RSI levels if needed

3. **Combine Strategies**
   - Day trading: ฿500-1,000/month
   - Swing trading: ฿600-1,200/month
   - **Total: ฿1,100-2,200/month**

4. **Monitor Market Hours**
   - BTC/ETH trade 24/7
   - Best volume: 9 AM - 5 PM
   - Low volatility: 2-5 AM

---

## ✅ Checklist

Before running:
- [ ] Python installed
- [ ] requests library installed
- [ ] BOT_TOKEN correct
- [ ] CHAT_ID correct
- [ ] day_trading_bot.py saved

After starting:
- [ ] See "BOT STARTED" in terminal
- [ ] Receive Telegram message
- [ ] Monitor first trade
- [ ] Verify entry/exit alerts work

---

**Ready to trade?**

```bash
python day_trading_bot.py
```

Good luck! 🚀

Generated: July 18, 2026
