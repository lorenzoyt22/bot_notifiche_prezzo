import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN mancante nelle variabili d’ambiente")
    exit(1)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
r = requests.get(url)
print("✅ Risposta Telegram:", r.text)
