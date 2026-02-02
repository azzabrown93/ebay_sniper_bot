import requests
import time
import os
import base64

print("===== EBAY SNIPER BOT STARTED =====")

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

CHECK_INTERVAL = 180  # 3 minutes
MAX_PRICE = 200
MIN_PROFIT = 25

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

SEEN_ITEMS = set()


########################################
# GET EBAY ACCESS TOKEN
########################################

def get_ebay_token():
    print("Getting eBay token...")

    credentials = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers=headers,
        data=data
    )

    if response.status_code != 200:
        print("Failed to get token:", response.text)
        return None

    return response.json()["access_token"]


########################################
# SEND TO DISCORD
########################################

def send_to_discord(title, price, avg_price, profit, url):
    message = {
        "content": f"""
🚨 **UNDERPRICED EBAY ITEM**

🛒 **{title}**
💷 Price: £{price}
📈 Avg Sold: £{avg_price}
🔥 Profit: £{profit}

{url}
"""
    }

    requests.post(DISCORD_WEBHOOK, json=message)


########################################
# CHECK FOR BAD WORDS
########################################

def contains_bad_words(text):
    text = text.lower()
    return any(word in text for word in BAD_WORDS)


########################################
# GET AVERAGE SOLD PRICE
########################################

def get_avg_sold_price(token, keyword):

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }

    params = {
        "q": keyword,
        "filter": "soldItemsOnly:true",
        "limit": 10
    }

    response = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        return None

    items = response.json().get("itemSummaries", [])

    prices = []

    for item in items:
        try:
            prices.append(float(item["price"]["value"]))
        except:
            pass

    if not prices:
        return None

    return sum(prices) / len(prices)


########################################
# SEARCH EBAY
########################################

def search_ebay(token, keyword):

    print(f"Searching for: {keyword}")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }

    params = {
        "q": keyword,
        "sort": "newlyListed",
        "limit": 20
    }

    response = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        print("Search failed.")
        return

    items = response.json().get("itemSummaries", [])

    avg_price = get_avg_sold_price(token, keyword)

    if not avg_price:
        return

    for item in items:

        item_id = item.get("itemId")

        if item_id in SEEN_ITEMS:
            continue

        title = item.get("title", "")
        price = float(item["price"]["value"])
        url = item.get("itemWebUrl")

        # Skip expensive items
        if price > MAX_PRICE:
            continue

        # Skip junk listings
        if contains_bad_words(title):
            continue

        profit = round(avg_price - price, 2)

        if profit >= MIN_PROFIT:

            print(f"FOUND DEAL: {title}")

            send_to_discord(
                title,
                price,
                round(avg_price, 2),
                profit,
                url
            )

            SEEN_ITEMS.add(item_id)


########################################
# MAIN LOOP
########################################

if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET or not DISCORD_WEBHOOK:
    print("ERROR: Missing environment variables!")
    exit()

token = get_ebay_token()

while True:

    try:

        if not token:
            token = get_ebay_token()

        for keyword in KEYWORDS:
            search_ebay(token, keyword)

        print("Sleeping...")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:

        print("BOT ERROR:", str(e))
        time.sleep(60)
