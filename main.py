import requests
import time
import os
import base64

print("========== ELITE EBAY SNIPER STARTED ==========")

############################################
# ENV VARIABLES
############################################

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET or not DISCORD_WEBHOOK:
    raise Exception("Missing environment variables!")

############################################
# BOT SETTINGS (EDIT THESE)
############################################

CHECK_INTERVAL = 180        # seconds
MAX_PRICE = 200            # don't alert above this
MIN_PROFIT = 30            # realistic minimum after fees

# HIGH VALUE SEARCH TERMS
KEYWORDS = [
    "airpods pro",
    "sony wh-1000xm5",
    "sony wh-1000xm4",
    "dyson v10",
    "dyson v11",
    "dyson v15",
    "nintendo switch oled",
    "apple watch series 7",
    "apple watch series 8",
    "bosch professional",
]

# JUNK FILTER
BAD_WORDS = [
    "parts",
    "spares",
    "repair",
    "faulty",
    "broken",
    "replacement",
    "read description",
    "doesn't work",
    "doesnt work",
    "strap",
    "box only",
    "manual only",
    "empty box",
    "earpiece",
    "single",
    "1x",
    "for parts",
]

SEEN = set()

############################################
# GET EBAY TOKEN
############################################

def get_token():

    creds = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    encoded = base64.b64encode(creds.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    r = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers=headers,
        data=data,
    )

    if r.status_code != 200:
        print("TOKEN ERROR:", r.text)
        return None

    print("New token acquired")
    return r.json()["access_token"]

############################################
# DISCORD ALERT
############################################

def alert(title, price, avg, profit, url):

    message = {
        "content":
f"""
🚨 **UNDERPRICED EBAY ITEM**

🛒 {title}

💷 Price: £{price}
📊 Avg Sold: £{avg}
🔥 Estimated Profit: £{profit}

{url}
"""
    }

    requests.post(DISCORD_WEBHOOK, json=message)

############################################
# FILTER
############################################

def junk(title):
    title = title.lower()
    return any(word in title for word in BAD_WORDS)

############################################
# GET SOLD AVG
############################################

def sold_average(token, keyword):

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB",
    }

    params = {
        "q": keyword,
        "filter": "soldItemsOnly:true",
        "limit": 15
    }

    r = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params=params
    )

    if r.status_code != 200:
        return None

    items = r.json().get("itemSummaries", [])

    prices = []

    for i in items:
        try:
            prices.append(float(i["price"]["value"]))
        except:
            pass

    if len(prices) < 5:
        return None

    return round(sum(prices) / len(prices), 2)

############################################
# SEARCH
############################################

def search(token, keyword):

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB",
    }

    params = {
        "q": keyword,
        "sort": "newlyListed",
        "limit": 25,
    }

    r = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params=params,
    )

    if r.status_code == 401:
        return "TOKEN_EXPIRED"

    if r.status_code != 200:
        return

    items = r.json().get("itemSummaries", [])

    avg_price = sold_average(token, keyword)

    if not avg_price:
        return

    for item in items:

        item_id = item.get("itemId")

        if item_id in SEEN:
            continue

        title = item.get("title", "")
        price = float(item["price"]["value"])
        url = item.get("itemWebUrl")

        if price > MAX_PRICE:
            continue

        if junk(title):
            continue

        # subtract approx ebay fees (13%)
        resale = avg_price * 0.87
        profit = round(resale - price, 2)

        if profit >= MIN_PROFIT:

            print("DEAL FOUND:", title)

            alert(title, price, avg_price, profit, url)

            SEEN.add(item_id)

############################################
# MAIN LOOP
############################################

token = get_token()

while True:

    try:

        if not token:
            token = get_token()

        for keyword in KEYWORDS:

            result = search(token, keyword)

            if result == "TOKEN_EXPIRED":
                token = get_token()

        print("Sleeping...\n")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:

        print("BOT ERROR:", e)

        # prevents crash loop
        time.sleep(60)
