import requests
import os
from datetime import datetime

# --- Configs ---
API_KEY = os.environ.get("CMC_API_KEY")
TELEGRAM_TOKEN = os.environ.get("bot_token")
TELEGRAM_CHAT_ID = os.environ.get("chat_id")
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"

# --- Filtering Criteria ---
MAX_PRICE = 10.0
MIN_PRICE = 0.1
MIN_VOLUME = 500_000
MIN_PERCENT_CHANGE = 10
EXCHANGE_FILTER = "KuCoin"

# --- Headers ---
HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": API_KEY,
}

# --- Get Crypto List ---
def get_top_coins():
    url = f"{CMC_BASE_URL}/cryptocurrency/listings/latest"
    params = {
        "start": "1",
        "limit": "200",
        "convert": "USD"
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        print("Error fetching coins")
        return []
    return response.json().get("data", [])

# --- Filter for KuCoin ---
def is_on_kucoin(symbol):
    url = f"{CMC_BASE_URL}/cryptocurrency/market-pairs/latest"
    params = {
        "symbol": symbol,
        "limit": 50
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        return False
    pairs = response.json().get("data", {}).get("market_pairs", [])
    for pair in pairs:
        if pair.get("exchange", {}).get("name") == EXCHANGE_FILTER:
            return True
    return False

# --- Send to Telegram ---
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except:
        pass

# --- Scan Logic ---
def scan():
    coins = get_top_coins()
    matching_coins = []

    for coin in coins:
        quote = coin["quote"]["USD"]
        price = quote["price"]
        volume = quote["volume_24h"]
        change = quote.get("percent_change_1h") or 0
        symbol = coin["symbol"]
        name = coin["name"]

        if not (MIN_PRICE <= price <= MAX_PRICE):
            continue
        if volume < MIN_VOLUME:
            continue
        if change < MIN_PERCENT_CHANGE:
            continue
        if not is_on_kucoin(symbol):
            continue

        matching_coins.append((symbol, name, price, volume, change))

    if not matching_coins:
        send_telegram_message("No KuCoin coins found matching the criteria.")
        return

    matching_coins.sort(key=lambda x: x[-1], reverse=True)
    top_5 = matching_coins[:5]

    msg = "\U0001F680 *Top 5 KuCoin Cryptos (1H)*:\n"
    for coin in top_5:
        msg += f"- {coin[1]} (${coin[0]}): {coin[4]:.2f}% | Price: ${coin[2]:.4f} | Volume: ${coin[3]:,.2f}\n"

    send_telegram_message(msg)

# --- Run Now ---
if __name__ == '__main__':
    scan()
