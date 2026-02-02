import requests
import time
import re

#############################
# ADD YOUR KEYS HERE
#############################

DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1467518544676917344/fQeZ15CBOM_81BBsRnKNwH_Rpuh5djbjr9T-9A64vrxQWPF1b2PgoN-7B-cnXu-9ntXK"
EBAY_APP_ID = "aaronbro-dealfind-PRD-1e7fa1504-3b2c59e2"

#############################

CHECK_INTERVAL = 300   # 5 minutes (aggressive but safe)
MIN_DISCOUNT = 40
MIN_PROFIT = 15       # Only alert if £15+ profit
ALERT_COOLDOWN = 1800

last_alert = 0

KEYWORDS = [
    # Tech
    "sony", "logitech", "razer", "steelseries", "corsair",
    "hyperx", "gaming headset", "mechanical keyboard",
    "gaming mouse", "airpods", "beats headphones",

    # Beauty / Hair
    "dyson airwrap", "dyson supersonic",
    "ghd platinum", "cloud nine straighteners",
    "shark flexstyle", "babyliss pro",

    # Toys
    "lego", "pokemon", "hot wheels",
    "barbie", "nerf", "jurassic world",
    "marvel toy"
]

SITES = [
    "https://www.amazon.co.uk/gp/goldbox",
    "https://www.amazon.co.uk/deals",
    "https://www.amazon.co.uk/outlet"
]


###################################
# DISCORD ALERT
###################################

def send_discord(message):
    global last_alert

    if time.time() - last_alert > ALERT_COOLDOWN:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
        last_alert = time.time()


###################################
# EBAY SOLD PRICE CHECK
###################################

def get_ebay_sold_price(query):

    url = "https://svcs.ebay.com/services/search/FindingService/v1"

    params = {
        "OPERATION-NAME": "findCompletedItems",
        "SERVICE-VERSION": "1.13.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": query,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "paginationInput.entriesPerPage": "10"
    }

    try:
        res = requests.get(url, params=params, timeout=20)
        data = res.json()

        items = data["findCompletedItemsResponse"][0]["searchResult"][0].get("item", [])

        prices = []

        for item in items:
            price = float(item["sellingStatus"][0]["currentPrice"][0]["__value__"])
            prices.append(price)

        if not prices:
            return None

        return sum(prices) / len(prices)

    except:
        return None


###################################
# AMAZON SCANNER
###################################

def check_deals():

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-GB,en;q=0.9"
    }

    for site in SITES:

        print(f"Scanning {site}")

        try:
            response = requests.get(site, headers=headers, timeout=30)

            html = response.text.lower()

            discounts = re.findall(r"-(\d{2})%", html)

            big_discounts = [int(d) for d in discounts if int(d) >= MIN_DISCOUNT]

            if not big_discounts:
                print("No big discounts.")
                continue


            for word in KEYWORDS:

                if word in html:

                    print(f"Deal keyword found: {word}")

                    avg_price = get_ebay_sold_price(word)

                    if not avg_price:
                        print("No eBay data.")
                        continue

                    # VERY rough estimate — assume amazon price ~60% of ebay if 40% off
                    estimated_amazon_price = avg_price * 0.6
                    profit = avg_price - estimated_amazon_price

                    if profit >= MIN_PROFIT:

                        send_discord(
f"""
💰 **PROFIT DEAL FOUND**

Item: {word}

Avg eBay Sold: £{round(avg_price,2)}
Est Buy: £{round(estimated_amazon_price,2)}
Est Profit: £{round(profit,2)}

{site}
"""
                        )

        except Exception as e:
            print("Error scanning site:", e)


###################################
# RUN BOT
###################################

print("===== MONEY BOT STARTED =====")

while True:

    try:
        check_deals()
        print("Sleeping...\n")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print("BOT ERROR:", e)
        time.sleep(60)

