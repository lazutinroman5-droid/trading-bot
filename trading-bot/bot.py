import os
import ccxt
import pandas as pd
import time
import requests

# ===== ENV =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["BTC/USDT", "ETH/USDT", "ETH/USDT"]
TIMEFRAME = "15m"

exchange = ccxt.binance({
    'enableRateLimit': True
})

last_signals = {}

# ===== TELEGRAM =====
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except:
        pass

# ===== DATA =====
def get_data(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        return df
    except:
        return None

# ===== ЛОГИКА (СТРАТЕГИЯ) =====
def analyze():
    for symbol in SYMBOLS:
        df = get_data(symbol)

        if df is None or len(df) < 50:
            continue

        df["high_20"] = df["high"].rolling(20).max()
        df["low_20"] = df["low"].rolling(20).min()

        df["high_10"] = df["high"].rolling(10).max()
        df["low_10"] = df["low"].rolling(10).min()

        last = df.iloc[-1]

        price = last["close"]
        high_20 = last["high_20"]
        low_20 = last["low_20"]
        high_10 = last["high_10"]
        low_10 = last["low_10"]

        last_signal = last_signals.get(symbol)

        # BUY
        if price > high_20 and last_signal != "BUY":
            send_message(f"🚀 BUY {symbol}\nЦена: {price}")
            last_signals[symbol] = "BUY"

        # SELL
        elif price < low_20 and last_signal != "SELL":
            send_message(f"🔻 SELL {symbol}\nЦена: {price}")
            last_signals[symbol] = "SELL"

        # EXIT BUY
        elif last_signal == "BUY" and price < low_10:
            send_message(f"❌ EXIT BUY {symbol}")
            last_signals[symbol] = None

        # EXIT SELL
        elif last_signal == "SELL" and price > high_10:
            send_message(f"❌ EXIT SELL {symbol}")
            last_signals[symbol] = None

# ===== START =====
print("Бот запущен")
send_message("✅ Бот запущен и ищет сигналы")

while True:
    try:
        analyze()
        time.sleep(120)
    except:
        time.sleep(10)
