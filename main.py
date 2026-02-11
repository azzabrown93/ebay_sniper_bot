import requests
from bs4 import BeautifulSoup
import random
import time
import os
import base64

print("🚨 VALUE SNIPER BOT — LIVE")

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

MIN_PROFIT = 12        # LOWER = MORE ALERTS
MIN_ROI = 0.28        # 28% is the sweet spot
FEE_RATE = 0.15

SEEN = set()

#############################################

def human_sleep():
    sleep_time = random.randint(180, 420)  # 3–7 minutes
    print(f"😴 Sleeping {sleep_time}s")
    time.sleep(sleep_time)

#############################################
# THIS is where the magic is.
# These are CHAOTIC markets.
#############################################

KEYWORDS = [

# Collectibles / Toys (AMAZING margins)

"pokemon bundle",
"pokemon box",
"elite trainer box",
"booster box",
"yu gi oh box",
"lorcana",
"one piece cards",
"funko bundle",
"funko lot",

# Lego flips destroy Amazon regularly

"lego bundle",
"lego clearance",
"lego retired",
"lego sale",

# Board games spike constantly

"board game bundle",
"warhammer",
"dungeons dragons",
"mtg bundle",

# Baby gear (massively mispriced often)

"baby monitor",
"breast pump",
"nanit",
"owlet",

# Random high ROI chaos

"nerf bundle",
"hot wheels lot",
"rc car",
"drone with camera",
"3d printer",

# Seasonal panic

"christmas lights",
"heater electric",
"air conditioner portable"
]

#############################################

BAD_WORDS = [
    "case","cover","replacement","strap",
    "cable","adapter","refill","ink",
    "parts","repair","sticker",
    "damaged","box only"
]

#############################################

def get_ebay_token():

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

#############################################

def get_ebay_avg(token, query):

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID":"EBAY_GB"
    }

    params = {
        "q":query,
        "filter":"soldItemsOnly:true",
        "limit":25
    }

    r = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params=params
    )

    items = r.json().get("itemSummaries", [])

    prices = []

    for i in items:
        try:
            prices.append(float(i["price"]["value"]))
        except:
            pass

    if len(prices) < 6:
        return None

    return sum(prices)/len(prices)

#############################################

def send_discord(title, amazon_price, avg_price, profit, roi, link):

    msg = {
        "content":f"""
🔥 **FLIP FOUND**

{title}

🛒 Amazon: £{amazon_price}
📦 eBay Avg: £{avg_price}

💰 Profit: £{profit}
📈 ROI: {int(roi*100)}%

{link}
"""
    }

    requests.post(DISCORD_WEBHOOK, json=msg)

#############################################

def scan_amazon(keyword):

    headers = {"User-Agent":"Mozilla/5.0"}

    url = f"https://www.amazon.co.uk/s?k={keyword.replace(' ','+')}"

    r = requests.get(url, headers=headers)

    soup = BeautifulSoup(r.text, "lxml")

    titles = soup.select("h2 span")
    prices = soup.select(".a-price-whole")
    links = soup.select("h2 a")

    results = []

    for t, p, l in zip(titles, prices, links):

        title = t.text.lower()

        if any(bad in title for bad in BAD_WORDS):
            continue

        try:
            price = float(p.text.replace(",", ""))
        except:
            continue

        link = "https://amazon.co.uk" + l["href"]

        results.append((title, price, link))

    print(f"Found {len(results)} products for {keyword}")

    return results

#############################################

token = get_ebay_token()
last_token_refresh = time.time()

while True:

    try:

        if time.time() - last_token_refresh > 7000:
            token = get_ebay_token()
            last_token_refresh = time.time()
            print("✅ Token refreshed")

        for keyword in KEYWORDS:

            print("🔎 Scanning:", keyword)

            products = scan_amazon(keyword)

            for title, amazon_price, link in products:

                if title in SEEN:
                    continue

                avg_price = get_ebay_avg(token, title)

                if not avg_price:
                    continue

                fee = avg_price * FEE_RATE
                profit = round(avg_price - amazon_price - fee,2)

                roi = profit / amazon_price

                if profit >= MIN_PROFIT and roi >= MIN_ROI:

                    print("🚨 FLIP:", title)

                    send_discord(
                        title,
                        amazon_price,
                        round(avg_price,2),
                        profit,
                        roi,
                        link
                    )

                    SEEN.add(title)

        human_sleep()

    except Exception as e:

        print("ERROR:", e)
        token = get_ebay_token()
        time.sleep(120)
