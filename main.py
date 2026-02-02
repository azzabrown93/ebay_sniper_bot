import requests
import time

DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1467469794298298378/LO-ogavZ2FS9j5x6WG_M-9lOKDDNO9dGyJykVBT_Zf_STEIKMZQunmOmR8ngnVUTQeFr"

CHECK_INTERVAL = 900  # 15 minutes

KEYWORDS = [
    "logitech",
    "sony",
    "steelseries",
    "razer",
    "corsair",
    "hyperx",
    "gaming headset",
    "mechanical keyboard",
    "gaming mouse"
]

def send_discord(message):
    requests.post(DISCORD_WEBHOOK, json={"content": message})


def check_deals():
    url = "https://www.amazon.co.uk/gp/goldbox"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        html = response.text.lower()

        for word in KEYWORDS:
            if word in html:
                send_discord(f"🚨 Possible deal spotted on Amazon!\nKeyword detected: {word}\nCheck here: {url}")
                break


while True:
    try:
        check_deals()
        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        send_discord(f"Bot error: {e}")
        time.sleep(300)