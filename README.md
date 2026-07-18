# 🚀 DAY TRADING SYSTEM

**Automated Intraday Trading Bot**  
**BTC/ETH - RSI Signals**

---

## 📂 Structure

```
C:\Invesment\
├── Day_Trading/                    (This folder)
│   ├── day_trading_bot.py         (Main bot)
│   ├── DAY_TRADING_SETUP.md       (Setup guide)
│   └── README.md                  (This file)
│
└── [Swing Trading Files]          (In parent folder)
    ├── telegram_alerts.py
    ├── scheduler_runner.py
    ├── Portfolio_10K_Complete.xlsx
    └── etc...
```

---

## 🎯 Quick Start

### 1. Install Dependencies
```bash
cd C:\Invesment\Day_Trading
pip install requests
```

### 2. Run Bot
```bash
python day_trading_bot.py
```

### 3. Expected Output
```
🚀 DAY TRADING BOT STARTED
Entry RSI: 30 (oversold), 70 (overbought)
Profit Target: +3%
Stop Loss: -5%
```

---

## 📖 Documentation

**Complete guide:** See `DAY_TRADING_SETUP.md`

Topics:
- Setup instructions
- Configuration options
- Telegram alerts
- Risk management
- Troubleshooting

---

## 💰 Income Model

| Metric | Value |
|--------|-------|
| Per trade profit | +3% |
| Per trade loss | -5% |
| Trades/day | 1-3 |
| Hold time | Minutes-hours |
| Max position | 0.01 BTC |
| Annual profit | ฿3,000-6,000 |

---

## ⚠️ Risk Management

- ✅ Auto stop loss: -5%
- ✅ Auto profit target: +3%
- ✅ No overnight positions
- ✅ Position size: 0.01 BTC max
- ✅ Daily cutoff: 8 PM

---

## 🤖 Strategy

**Entry:** RSI Indicators
- RSI < 30 = BUY (oversold)
- RSI > 70 = SELL (overbought)

**Exit:** Automatic
- +3% = Take profit
- -5% = Stop loss
- 8 PM = End of day

---

## 📱 Alerts

Every trade sends Telegram:
- Entry signal with price
- Real-time P&L tracking
- Profit/loss on exit
- Daily summary

---

## 🔧 Customization

Edit `day_trading_bot.py`:

```python
PROFIT_TARGET = 1.03      # +3%
STOP_LOSS = 0.95          # -5%
ENTRY_RSI_OVERSOLD = 30   # Buy trigger
ENTRY_RSI_OVERBOUGHT = 70 # Sell trigger
MAX_POSITION_SIZE = 0.01  # 0.01 BTC
```

---

## ✅ System Status

- ✅ Price data: Live (CoinGecko)
- ✅ Telegram alerts: Active
- ✅ RSI calculation: Included
- ⚠️ Auto-execution: Demo mode (manual trades)

---

## 📊 Comparison

vs Swing Trading:

| | Day Trading | Swing Trading |
|--|---|---|
| Hold | Hours | 1-7 days |
| Target | +3% | +25% |
| Stop | -5% | -10% |
| Frequency | Daily | 2-4/month |
| Profit/month | ฿250-500 | ฿600-1,200 |
| Stress | High | Low |

---

## 🚀 Run Commands

```bash
# Start bot
python day_trading_bot.py

# Stop bot
Ctrl + C

# Keep running 24/7
# Use Windows Task Scheduler (see DAY_TRADING_SETUP.md)
```

---

**Ready to trade?**

```bash
python day_trading_bot.py
```

Good luck! 📈

---

Generated: July 18, 2026
# Trigger workflow
