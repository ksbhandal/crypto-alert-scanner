import os
import requests
from flask import Flask
import threading
import time

API_KEY = os.environ.get("API_KEY")
BOT_TOKEN = os.environ.get("bot_token")
CHAT_ID = os.environ.get("chat_id")

app = Flask(__name__)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except:
        pass

def get_top_5_cryptos():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": API_KEY
    }
    params = {
        "start": "1",
        "limit": "5000",
        "convert": "USD"
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    filtered = []
    for coin in data.get("data", []):
        quote = coin.get("quote", {}).get("USD", {})
        price = quote.get("price")
        market_cap = quote.get("market_cap")
        volume_24h = quote.get("volume_24h")
        percent_change_15m = quote.get("percent_change_15m")
        percent_change_1h = quote.get("percent_change_1h")

        timeframe = None
        if percent_change_15m is not None and percent_change_15m > 10:
            percent_change = percent_change_15m
            timeframe = "15m"
        elif percent_change_1h is not None and percent_change_1h > 10:
            percent_change = percent_change_1h
            timeframe = "1h"
        else:
            continue

        if None in [price, market_cap, volume_24h, percent_change]:
            continue

        if (
            0.1 <= price <= 10 and
            market_cap < 300_000_000 and
            volume_24h > 500_000
        ):
            filtered.append({
                "symbol": coin.get("symbol"),
                "name": coin.get("name"),
                "price": price,
                "market_cap": market_cap,
                "volume": volume_24h,
                "change": percent_change,
                "timeframe": timeframe
            })

    top_5 = sorted(filtered, key=lambda x: x["change"], reverse=True)[:5]

    if top_5:
        message = "\U0001F680 Top 5 Exploding Cryptos:\n"
        for coin in top_5:
            message += (f"- {coin['name']} (${coin['symbol']}): {coin['change']:.2f}% ({coin['timeframe']})\n"
                        f"Price: ${coin['price']:.4f}\nVol: ${coin['volume']:,}\n\n")
        send_telegram_message(message.strip())
    else:
        send_telegram_message("No coins found meeting the criteria.")

@app.route("/")
def home():
    return "Crypto scanner running..."

@app.route("/scan")
def scan():
    get_top_5_cryptos()
    return "Scan done."

if __name__ == "__main__":
    def ping_self():
        while True:
            try:
                requests.get("https://your-render-url.onrender.com/scan")
            except:
                pass
            time.sleep(600)  # every 10 minutes

    threading.Thread(target=ping_self).start()
    app.run(host="0.0.0.0", port=10000)
