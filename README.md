# 📈 Telegram Crypto Alert Bot

Questo bot Telegram permette di ricevere **notifiche automatiche** quando il prezzo di una criptovaluta supera o scende sotto una soglia impostata.

---

## ⚙️ Funzionalità

- `/start`: mostra messaggio di benvenuto e cripto monitorate
- `/alert <COIN> <PREZZO>`: imposta un alert  
  - Es: `/alert BTC -30000` → notifica se BTC scende sotto 30.000$
  - Prezzi negativi = alert al ribasso ⬇️
  - Prezzi positivi = alert al rialzo ⬆️
- `/listalerts`: mostra tutti gli alert attivi dell’utente
- `/removealert <COIN> <PREZZO>`: rimuove un singolo alert
- `/removealerts <COIN>`: rimuove **tutti** gli alert relativi a quella coin

---

## 🔧 Dipendenze

- `python-telegram-bot`
- `requests`
- `nest_asyncio`

BOT_TOKEN=...   # Token del bot Telegram
CHAT_ID=...     # Chat ID predefinito 

Installa con:

```bash
pip install python-telegram-bot requests nest_asyncio
