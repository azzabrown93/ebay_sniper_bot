import requests
from bs4 import BeautifulSoup
import time
import os
import base64

print("===== SNIPER AMAZON → EBAY BOT LIVE =====")

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

MIN_PROFIT = 15
MIN_ROI = 0.35
FEE_RATE = 0.15
CHECK_INTERVAL = 900  # 15 mins

SEEN = set()

#############################################

KEYWORDS = [
    
##############
# SMART HOME
##############

"ring doorbell",
"ring floodlight",
"blink outdoor",
"arlo pro",
"arlo essential",
"eufy security",
"eufy doorbell",
"tapo camera",
"google nest cam",
"nest doorbell",

##############
# VACUUM GOLDMINE
##############

"dyson v7",
"dyson v8",
"dyson v10",
"dyson v11",
"dyson cyclone",
"shark cordless",
"shark stratos",
"shark anti hair wrap",

##############
# KITCHEN MONEY PRINTERS
##############

"ninja air fryer",
"ninja dual air fryer",
"ninja foodi",
"instant pot duo",
"cosori air fryer",
"nutribullet",
"vitamix",
"kitchenaid mixer",

##############
# AUDIO (HIGH LIQUIDITY)
##############

"sony xm4",
"sony xm5",
"bose qc45",
"bose 700",
"airpods pro",
"airpods max",
"jbl flip",
"jbl charge",
"ultimate ears",

##############
# GAMING ACCESSORIES (NOT CONSOLES)
##############

"logitech g pro",
"steelseries arctis",
"razer headset",
"razer mouse",
"elgato capture",
"elgato wave",
"gaming keyboard",
"gaming mouse wireless",

##############
# STORAGE / SSD
##############

"samsung 980",
"samsung 990",
"wd black sn850",
"crucial p3",
"portable ssd",
"nvme ssd",
"external ssd",

##############
# BABY TECH (INSANELY UNDERRATED)
##############

"owlet monitor",
"nanit pro",
"vtech baby monitor",
"motorola baby monitor",
"angelcare monitor",

##############
# LEGO ECOSYSTEM
##############

"lego technic",
"lego creator",
"lego star wars",
"lego ideas",
"retired lego",
"lego architecture",

##############
# POWER TOOLS (HIGH ROI)
##############

"dewalt xr",
"milwaukee m18",
"makita drill",
"bosch professional",
"dewalt combi",

##############
# CONTENT CREATOR ECONOMY
##############

"gopro hero",
"dji osmo",
"dji mic",
"rode microphone",
"ring light",
"streaming microphone"
]

BAD_WORDS = [

    "case",
    "cover",
    "replacement",
    "strap",
    "cable",
    "adapter",
    "refill",
    "ink",
    "parts",
    "repair",
    "sticker",
    "toy figure",
    "single card",
    "proxy",
    "damaged",
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
        "limit":20
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

    if len(prices) < 7:
        return None

    return sum(prices)/len(prices)

#############################################

def send_discord(title, amazon_price, avg_price, profit, roi, link):

    msg = {
        "content":f"""
🚨 **SNIPER FLIP FOUND**

🛒 {title}

Amazon: £{amazon_price}
Avg Sold: £{avg_price}

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

    return results

#############################################

token = get_ebay_token()
last_token_refresh = time.time()

while True:

    try:

        if time.time() - last_token_refresh > 7000:
            token = get_ebay_token()
            last_token_refresh = time.time()
            print("Refreshed eBay token")

        for keyword in KEYWORDS:

            print("Scanning:", keyword)

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

                    print("SNIPER HIT:", title)

                    send_discord(
                        title,
                        amazon_price,
                        round(avg_price,2),
                        profit,
                        roi,
                        link
                    )

                    SEEN.add(title)

        print("Sleeping...")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:

        print("ERROR:", e)
        token = get_ebay_token()
        time.sleep(120)
