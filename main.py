import requests
import time
import os
import base64

print("===== MONSTER EBAY SNIPER ACTIVE =====")

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

CHECK_INTERVAL = 90
MAX_PRICE = 400
MIN_PROFIT = 35
FEE_RATE = 0.15

SEEN = set()

########################################

KEYWORDS = [
    "dyson v15",
    "dyson airwrap",
    "airpods pro",
    "sony wh-1000xm5",
    "steam deck",
    "nintendo switch oled",
    "apple watch ultra",
    "dji mini 3 pro",
    "gopro hero 12",
    "lego technic"
]

MISSPELLINGS = [
    "dyzon",
    "airpod pro",
    "soni headphones",
    "apl watch",
    "nintndo switch",
    "lego technik"
]

BAD_WORDS = [
    "parts","repair","broken","faulty",
    "spares","untested","for parts",
    "empty box","box only","manual only",
    "strap","case only","damaged",
    "missing","cracked","shell","housing",
    "job lot","bundle","cover"
]

########################################

def get_token():

    creds = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    encoded = base64.b64encode(creds.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type":"application/x-www-form-urlencoded"
    }

    data = {
        "grant_type":"client_credentials",
        "scope":"https://api.ebay.com/oauth/api_scope"
    }

    r = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers=headers,
        data=data
    )

    return r.json()["access_token"]

########################################

def send_discord(title, price, avg, profit, link):

    tier = "⚡ STRONG FLIP"

    if profit > 70:
        tier = "🔥 ELITE FLIP"

    msg = {
        "content":f"""
{tier}

🛒 {title}

Buy: £{price}
Avg Sold: £{avg}
Net Profit: £{profit}

{link}
"""
    }

    requests.post(DISCORD_WEBHOOK, json=msg)

########################################

def bad(title):
    t = title.lower()
    return any(w in t for w in BAD_WORDS)

########################################

def avg_sold(token, keyword):

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID":"EBAY_GB"
    }

    params = {
        "q":keyword,
        "filter":"soldItemsOnly:true",
        "limit":20
    }

    r = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params=params
    )

    data = r.json().get("itemSummaries", [])

    if len(data) < 8:
        return None  # low demand filter

    prices = []

    for i in data:
        try:
            prices.append(float(i["price"]["value"]))
        except:
            pass

    return sum(prices)/len(prices)

########################################

def scan(token, keyword):

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID":"EBAY_GB"
    }

    params = {
        "q":keyword,
        "limit":30,
        "sort":"newlyListed"
    }

    r = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params=params
    )

    avg = avg_sold(token, keyword)

    if not avg:
        return

    for item in r.json().get("itemSummaries", []):

        id = item.get("itemId")

        if id in SEEN:
            continue

        title = item.get("title","")
        price = float(item["price"]["value"])
        link = item.get("itemWebUrl")

        if price > MAX_PRICE:
            continue

        if bad(title):
            continue

        fee = avg * FEE_RATE
        profit = round(avg - price - fee,2)

        if profit >= MIN_PROFIT:

            print("DEAL:",title)

            send_discord(
                title,
                round(price,2),
                round(avg,2),
                profit,
                link
            )

            SEEN.add(id)

########################################

token = get_token()

while True:

    try:

        if not token:
            token = get_token()

        for k in KEYWORDS + MISSPELLINGS:
            scan(token, k)

        print("Sleeping...")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:

        print("Error:",e)
        time.sleep(60)
