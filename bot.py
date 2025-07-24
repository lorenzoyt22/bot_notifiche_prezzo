import logging
import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import asyncio

# === CONFIGURAZIONE ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # ← Railway: setta questa variabile
CHECK_INTERVAL = 60  # in secondi

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === ALERT PREIMPOSTATO (MINA/USD ≤ 0.188) ===
alerts = [
    {
        "chat_id": int(os.getenv("CHAT_ID")),  # ← Railway: setta questa variabile
        "symbol": "MINA",
        "price": -0.188
    }
]

# === OTTIENI PREZZO ATTUALE ===
def get_coinbase_price(symbol: str):
    url = f"https://api.exchange.coinbase.com/products/{symbol.upper()}-USD/ticker"
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError("Simbolo non valido o API Coinbase non disponibile.")
    return float(r.json()['price'])

# === OTTIENI APERTURA GIORNALIERA ===
def get_daily_open(symbol: str):
    url = f"https://api.exchange.coinbase.com/products/{symbol.upper()}-USD/candles?granularity=86400"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    candles = r.json()
    if not candles:
        return None
    return float(candles[0][3])

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Ciao! Questo bot ti avviserà quando una cripto raggiunge un prezzo impostato.")

# === /alert ===
async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper()
        target_price = float(context.args[1])
        alerts.append({
            "chat_id": update.effective_chat.id,
            "symbol": symbol,
            "price": target_price
        })
        await update.message.reply_text(f"✅ Alert impostato per {symbol} a {target_price}$")
    except:
        await update.message.reply_text("❌ Usa il comando così: /alert MINA 0.188")

# === CONTROLLO PERIODICO ===
async def check_prices(app):
    while True:
        to_remove = []
        for alert in alerts:
            try:
                current_price = get_coinbase_price(alert["symbol"])
                target_price = alert["price"]
                chat_id = alert["chat_id"]
                is_lower_check = target_price < 0
                abs_target = abs(target_price)

                if (is_lower_check and current_price <= abs_target) or (not is_lower_check and current_price >= abs_target):
                    open_price = get_daily_open(alert["symbol"])
                    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
                    emoji = "📉" if is_lower_check else "📈"
                    msg = (
                        f"{emoji} *ALERT PREZZO RAGGIUNTO*\n"
                        f"💰 Cripto: *{alert['symbol']}*\n"
                        f"📅 Data: *{now}*\n"
                        f"📍 Prezzo attuale: *{current_price:.4f}$*\n"
                        f"🕯️ Apertura giornaliera: *{open_price:.4f}$*"
                    )
                    await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                    to_remove.append(alert)
            except Exception as e:
                print("Errore nel controllo alert:", e)

        for a in to_remove:
            alerts.remove(a)

        await asyncio.sleep(CHECK_INTERVAL)

# === AVVIO BOT ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alert", alert))
    asyncio.create_task(check_prices(app))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
