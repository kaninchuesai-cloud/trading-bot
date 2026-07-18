import yfinance as yf
import requests
from datetime import datetime
import time

TOKEN = "8736600939:AAFg_Asak5ETjbdL3CUUa4WTHIRk7Md886Q"
CHAT_ID = "6139624445"

WATCH = {'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'GC=F': 'Gold', 'CL=F': 'Oil'}

def alert(msg):
    try:
        requests.post("https://api.telegram.org/bot" + TOKEN + "/sendMessage", 
                     data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

def calc_macd(closes, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = sum(closes[-fast:]) / fast
    ema_slow = sum(closes[-slow:]) / slow
    macd_line = ema_fast - ema_slow
    return macd_line

def calc_ema(closes, period):
    """Calculate EMA"""
    return sum(closes[-period:]) / period

print("\n" + "="*60)
print("BOT TRADING - MULTIPLE SIGNALS")
print("="*60 + "\n")

res = ""
ok = False

for sym, name in WATCH.items():
    try:
        print(name + "...", end=" ")
        df = yf.download(sym, period='3mo', progress=False)
        
        if df is None or len(df) < 50:
            print("SKIP")
            continue
        
        if isinstance(df.columns, type(df.columns)):
            closes = df['Close'].iloc[:, 0].values
            volumes = df.iloc[:, -1].iloc[:, 0].values if 'Volume' in str(df.columns) else None
        else:
            closes = df['Close'].values
            volumes = df['Volume'].values if 'Volume' in df.columns else None
        
        price = float(closes[-1])
        
        # 1. RSI
        up = dn = 0.0
        for i in range(len(closes)-14, len(closes)):
            if i > 0:
                d = closes[i] - closes[i-1]
                if d > 0:
                    up += d
                else:
                    dn += abs(d)
        
        ru = up / 14.0
        rd = dn / 14.0
        rsi = 100.0 - (100.0 / (1.0 + ru/rd)) if rd > 0 else 50.0
        
        # 2. EMA
        ema20 = calc_ema(closes, 20)
        ema50 = calc_ema(closes, 50)
        
        # 3. MACD
        macd = calc_macd(closes, 12, 26, 9)
        
        # 4. Volume trend
        vol_up = volumes[-1] > volumes[-5] if volumes is not None else False
        
        # Signals
        rsi_sig = (rsi < 30) or (rsi > 70)
        ema_sig = ema20 > ema50
        macd_sig = macd > 0
        
        # Need 2+ confirmations
        confirmations = sum([rsi_sig, ema_sig, macd_sig])
        
        sig = ""
        if confirmations >= 2:
            if (rsi < 30 or (rsi < 50 and macd_sig and ema_sig)):
                sig = "BUY"
                ok = True
            elif (rsi > 70 or (rsi > 50 and not macd_sig and not ema_sig)):
                sig = "SELL"
                ok = True
        
        detail = "RSI:" + str(round(rsi, 1)) + " EMA:" + ("UP" if ema_sig else "DN") + " MACD:" + ("+" if macd_sig else "-")
        print("$" + str(round(price, 2)) + " " + detail + " " + sig)
        
        if sig:
            res += sig + " " + name + " $" + str(round(price, 2)) + "\n"
            res += "  RSI:" + str(round(rsi, 1)) + " | EMA20>50:" + str(ema_sig) + " | MACD:" + str(round(macd, 4)) + "\n"
    
    except:
        print("ERR")
    
    time.sleep(1)

print("\n" + "="*60)
if ok:
    msg = "SIGNALS (Multiple Confirmation)\n" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n" + res
    alert(msg)
    print("SIGNALS SENT")
else:
    print("NO SIGNALS")
print("="*60 + "\n")
