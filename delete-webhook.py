import os
import requests
from dotenv import load_dotenv

# Carica le variabili d'ambiente da un file .env (se sei in locale)
load_dotenv()

# Leggi il token del bot da variabili d'ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ Errore: variabile d'ambiente BOT_TOKEN non trovata.")
    exit(1)

# URL per eliminare il webhook
url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"

# Richiesta HTTP
response = requests.get(url)

# Output del risultato
print("✅ Risposta Telegram:", response.text)
