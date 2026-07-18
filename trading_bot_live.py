"""
Live Trading Bot with Binance API
- Real/Paper trading mode
- Risk management (10% per trade)
- RSI signals (buy @ <30, sell @ >70)
- Telegram alerts
- Stop loss & Take profit automation
"""

import os
import sys
import time
import requests
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import ta

# Load environment variables
load_dotenv()

# API Keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Trading parameters
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.1"))  # 10%
ACCOUNT_SIZE = float(os.getenv("ACCOUNT_SIZE", "1000"))
PAPER_TRADING = os.getenv("PAPER_TRADING", "True").lower() == "true"

# RSI parameters
RSI_PERIOD = 14
BUY_SIGNAL = 30
SELL_SIGNAL = 70

# Take profit & Stop loss
TAKE_PROFIT_PERCENT = 3.0
STOP_LOSS_PERCENT = 5.0

# Initialize Binance client
client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY, testnet=True)

class TradingBot:
    def __init__(self):
        self.paper_trading = PAPER_TRADING
        self.positions = {}
        self.account_balance = ACCOUNT_SIZE
        self.send_telegram(f"🤖 Bot Started\nMode: {'PAPER' if self.paper_trading else 'LIVE'}\nAccount: ${self.account_balance:.2f}")

    def send_telegram(self, message):
        """Send message to Telegram"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Telegram error: {e}")

    def get_balance(self):
        """Get account balance"""
        if self.paper_trading:
            return self.account_balance
        try:
            account = client.get_account()
            balance = float(account['totalAssetOfBtc'])
            return balance
        except Exception as e:
            self.send_telegram(f"❌ Balance error: {e}")
            return 0

    def get_price_data(self, symbol, interval="1h"):
        """Get price data for RSI calculation"""
        try:
            klines = client.get_klines(symbol=symbol, interval=interval, limit=50)
            closes = [float(kline[4]) for kline in klines]
            return closes
        except Exception as e:
            self.send_telegram(f"❌ Data error ({symbol}): {e}")
            return None

    def calculate_rsi(self, closes):
        """Calculate RSI indicator"""
        if len(closes) < RSI_PERIOD:
            return None

        import pandas as pd
        df = pd.DataFrame({'close': closes})
        rsi = ta.momentum.rsi(df['close'], length=RSI_PERIOD)
        return rsi.iloc[-1]

    def execute_buy(self, symbol, price):
        """Execute buy order"""
        trade_amount = (self.account_balance * RISK_PER_TRADE) / price

        if self.paper_trading:
            self.positions[symbol] = {
                'entry_price': price,
                'amount': trade_amount,
                'entry_time': datetime.now(),
                'status': 'OPEN'
            }
            self.account_balance -= (trade_amount * price)
            msg = f"🟢 BUY Signal: {symbol}\nPrice: ${price:.2f}\nAmount: {trade_amount:.4f}\nMode: PAPER"
        else:
            try:
                order = client.order_market_buy(symbol=symbol, quantity=trade_amount)
                msg = f"🟢 BUY Executed: {symbol}\nPrice: ${price:.2f}\nAmount: {trade_amount:.4f}\nOrder ID: {order['orderId']}"
            except BinanceAPIException as e:
                msg = f"❌ BUY Failed: {e}"
                return

        self.send_telegram(msg)

    def execute_sell(self, symbol, price):
        """Execute sell order"""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        if position['status'] != 'OPEN':
            return

        pnl = (price - position['entry_price']) * position['amount']
        pnl_percent = (pnl / (position['entry_price'] * position['amount'])) * 100

        if self.paper_trading:
            self.account_balance += (position['amount'] * price)
            self.positions[symbol]['status'] = 'CLOSED'
            msg = f"🔴 SELL Signal: {symbol}\nExit Price: ${price:.2f}\nP&L: ${pnl:.2f} ({pnl_percent:.2f}%)\nMode: PAPER"
        else:
            try:
                order = client.order_market_sell(symbol=symbol, quantity=position['amount'])
                msg = f"🔴 SELL Executed: {symbol}\nExit Price: ${price:.2f}\nP&L: ${pnl:.2f} ({pnl_percent:.2f}%)\nOrder ID: {order['orderId']}"
            except BinanceAPIException as e:
                msg = f"❌ SELL Failed: {e}"
                return

        self.send_telegram(msg)

    def check_stop_loss_take_profit(self, symbol, current_price):
        """Check stop loss & take profit"""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        if position['status'] != 'OPEN':
            return

        entry_price = position['entry_price']

        # Take profit
        tp_price = entry_price * (1 + TAKE_PROFIT_PERCENT / 100)
        if current_price >= tp_price:
            self.send_telegram(f"📈 Take Profit Hit: {symbol}\nExit: ${current_price:.2f}")
            self.execute_sell(symbol, current_price)
            return

        # Stop loss
        sl_price = entry_price * (1 - STOP_LOSS_PERCENT / 100)
        if current_price <= sl_price:
            self.send_telegram(f"📉 Stop Loss Hit: {symbol}\nExit: ${current_price:.2f}")
            self.execute_sell(symbol, current_price)
            return

    def run(self):
        """Main bot loop"""
        self.send_telegram("✅ Bot monitoring started...")

        while True:
            try:
                for symbol in SYMBOLS:
                    # Get current price
                    ticker = client.get_symbol_info(symbol)
                    if not ticker:
                        continue

                    current_price = float(client.get_symbol_ticker(symbol=symbol)['price'])

                    # Get price data
                    closes = self.get_price_data(symbol)
                    if not closes:
                        continue

                    # Calculate RSI
                    rsi = self.calculate_rsi(closes)
                    if rsi is None:
                        continue

                    # Check signals
                    if rsi < BUY_SIGNAL and symbol not in self.positions:
                        self.send_telegram(f"📊 {symbol} RSI: {rsi:.2f} (BUY Signal!)")
                        self.execute_buy(symbol, current_price)

                    elif rsi > SELL_SIGNAL and symbol in self.positions:
                        self.send_telegram(f"📊 {symbol} RSI: {rsi:.2f} (SELL Signal!)")
                        self.execute_sell(symbol, current_price)

                    # Check stop loss / take profit
                    self.check_stop_loss_take_profit(symbol, current_price)

                    # Log status
                    print(f"[{datetime.now()}] {symbol}: Price=${current_price:.2f}, RSI={rsi:.2f}")

                # Print account status
                balance = self.get_balance()
                print(f"Account Balance: ${balance:.2f}")

                # Wait before next check (4 hours)
                time.sleep(14400)

            except Exception as e:
                print(f"Error: {e}")
                self.send_telegram(f"❌ Bot Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
