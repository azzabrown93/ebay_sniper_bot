import requests
import time
import os

print("===== EBAY SNIPER BOT STARTED =====")

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

CHECK_INTERVAL = 180  # 3 minutes
MAX_PRICE = 200  # your budget
MIN_PROFIT = 25  # minimum profit target (£)

KEYWORDS = [
    "sony headphones",
    "airpods",
    "dyson",
    "nintendo switch",
    "lego",
    "apple watch",
    "bosch tools"
]

BAD_WORDS = [
    "replacement",
    "part",
    "spares",
    "repair",
    "faulty",
    "broken",
    "read description",
    "strap",
    "box only",
    "manual only", 
    "earpiece",
    "1x",
    "single"
]

#########################################
# GET EBAY ACCESS TOKEN
#########################################

def get_ebay_token():
    print("Getting eBay token...")

    url = "https://api.ebay.com/identity/v1/oauth2/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(
        url,
        headers=headers,
        data=data,
        auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)
    )

    token = response.json()["access_token"]

    print("Token acquired.")
    return token


#########################################
# DISCORD ALERT
#########################################

def send_discord(message):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
    except:
        print("Discord failed.")


#########################################
# GET AVERAGE SOLD PRICE
#########################################

def get_sold_average(keyword, token):

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "q": keyword,
        "filter": "soldItemsOnly:true",
        "limit": 20
    }

    response = requests.get(url, headers=headers, params=params)

    data = response.json()

    prices = []

    if "itemSummaries" not in data:
        return None

    for item in data["itemSummaries"]:
        try:
            prices.append(float(item["price"]["value"]))
        except:
            pass

    if len(prices) < 5:
        return None

    avg_price = sum(prices) / len(prices)

    return avg_price


#########################################
# FIND LIVE UNDERPRICED LISTINGS
#########################################

def find_deals(keyword, token, avg_price):

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "q": keyword,
        "sort": "price",
        "limit": 10
    }

    response = requests.get(url, headers=headers, params=params)

    data = response.json()

    if "itemSummaries" not in data:
        return

    for item in data["itemSummaries"]:

        try:
            price = float(item["price"]["value"])
            title = item["title"]
            link = item["itemWebUrl"]

        except:
            continue

        if price > MAX_PRICE:
            continue

        profit = avg_price - price

        ###################################
        # DEAL DETECTED
        ###################################

        if profit > MIN_PROFIT:

            message = f"""
🚨 **UNDERPRICED EBAY ITEM**

🛒 {title}

💰 Price: £{price}
📈 Avg Sold: £{round(avg_price,2)}
🔥 Profit: £{round(profit,2)}

{link}
"""

            print("DEAL FOUND!")
            send_discord(message)


#########################################
# MAIN LOOP
#########################################

token = get_ebay_token()

while True:

    try:

        print("Scanning market...")

        for keyword in KEYWORDS:

            avg_price = get_sold_average(keyword, token)

            if avg_price:
                print(f"{keyword} avg: £{round(avg_price,2)}")
                find_deals(keyword, token, avg_price)

        print(f"Sleeping {CHECK_INTERVAL} seconds...\n")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:

        print("ERROR:", str(e))

        # refresh token if needed
        token = get_ebay_token()
        time.sleep(60)

