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
        print("SENT")
    except:
        pass

print("\n" + "="*50)
print("BOT TRADING")
print("="*50 + "\n")

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
            close_data = df['Close'].iloc[:, 0].values
        else:
            close_data = df['Close'].values
        
        price = float(close_data[-1])
        
        up = 0.0
        dn = 0.0
        for i in range(len(close_data)-14, len(close_data)):
            if i > 0:
                d = close_data[i] - close_data[i-1]
                if d > 0:
                    up += d
                else:
                    dn += abs(d)
        
        ru = up / 14.0
        rd = dn / 14.0
        rsi = 100.0 - (100.0 / (1.0 + ru/rd)) if rd > 0 else 50.0
        
        sig = ""
        if rsi < 30:
            sig = "BUY"
            ok = True
        elif rsi > 70:
            sig = "SELL"
            ok = True
        
        print(str(round(price, 2)) + " RSI:" + str(round(rsi, 1)) + " " + sig)
        
        if sig:
            res += sig + " " + name + " $" + str(round(price, 2)) + "\n"
    
    except Exception as e:
        print("ERR")
    
    time.sleep(1)

print("\n" + "="*50)
if ok:
    msg = "SIGNALS " + datetime.now().strftime('%H:%M:%S') + "\n\n" + res
    alert(msg)
    print("SIGNALS FOUND & SENT")
else:
    print("NO SIGNALS")
print("="*50 + "\n")
