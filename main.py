import requests
from bs4 import BeautifulSoup
import time
import os
import base64

print("===== AMAZON → EBAY ARBITRAGE BOT LIVE =====")

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

MIN_PROFIT = 25
FEE_RATE = 0.15
CHECK_INTERVAL = 600  # every 10 mins

SEEN = set()

########################################

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

########################################

def send_discord(title, amazon_price, avg_price, profit, link):

    msg = {
        "content":f"""
🔥 **AMAZON → EBAY FLIP**

🛒 {title}

Amazon: £{amazon_price}
Avg Sold: £{avg_price}
Net Profit: £{profit}

{link}
"""
    }

    requests.post(DISCORD_WEBHOOK, json=msg)

########################################

def get_ebay_avg(token, query):

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID":"EBAY_GB"
    }

    params = {
        "q":query,
        "filter":"soldItemsOnly:true",
        "limit":12
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

    if len(prices) < 5:
        return None

    return sum(prices)/len(prices)

########################################

def scan_amazon():

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    url = "https://www.amazon.co.uk/gp/goldbox"

    r = requests.get(url, headers=headers)

    soup = BeautifulSoup(r.text, "lxml")

    products = soup.select(".DealContent-module__truncate_sWbxETx42ZPStTc9jwySW")

    prices = soup.select(".a-price-whole")

    return list(zip(products, prices))

########################################

token = get_ebay_token()

while True:

    try:

        deals = scan_amazon()

        for product, price_tag in deals:

            title = product.text.strip()

            try:
                amazon_price = float(price_tag.text.replace(",", ""))
            except:
                continue

            if title in SEEN:
                continue

            avg_price = get_ebay_avg(token, title)

            if not avg_price:
                continue

            fee = avg_price * FEE_RATE
            profit = round(avg_price - amazon_price - fee,2)

            if profit >= MIN_PROFIT:

                print("FLIP FOUND:", title)

                send_discord(
                    title,
                    amazon_price,
                    round(avg_price,2),
                    profit,
                    "https://www.amazon.co.uk/gp/goldbox"
                )

                SEEN.add(title)

        print("Sleeping...")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:

        print("Error:",e)
        token = get_ebay_token()
        time.sleep(60)
