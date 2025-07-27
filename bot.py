import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import nest_asyncio
import asyncio

# === APPLICO PATCH PER EVENT LOOP GIÀ ATTIVO ===
nest_asyncio.apply()

# === LEGGO LE VARIABILI D'AMBIENTE ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))  # Deve essere un intero

CHECK_INTERVAL = 60  # Intervallo di controllo in secondi

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === ALERT PRE-INSERITI ===
alerts = [
    {
        "chat_id": CHAT_ID,
        "symbol": "MINA",
        "price": -0.188  # Notifica se il prezzo scende sotto o uguale
    },
    {
        "chat_id": CHAT_ID,
        "symbol": "GST",
        "price": -0.006265  # Notifica se il prezzo scende sotto o uguale
    }
]

# === FUNZIONE PER OTTENERE IL PREZZO ATTUALE ===
def get_coinbase_price(symbol: str):
    url = f"https://api.exchange.coinbase.com/products/{symbol.upper()}-USD/ticker"
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError("Simbolo non valido o problema API Coinbase.")
    return float(r.json()['price'])

# === FUNZIONE PER OTTENERE L'APERTURA GIORNALIERA ===
def get_daily_open(symbol: str):
    url = f"https://api.exchange.coinbase.com/products/{symbol.upper()}-USD/candles?granularity=86400"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    candles = r.json()
    if not candles:
        return None
    return float(candles[0][3])  # prezzo di apertura della candela

# === COMANDO /START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Ciao! Questo bot ti avviserà quando una cripto raggiunge un prezzo impostato.")

    # Mostra le criptovalute attualmente monitorate
    symbols = list(set([a['symbol'] for a in alerts if a['chat_id'] == update.effective_chat.id]))
    if symbols:
        coin_list = "\n".join([f"• {s}" for s in symbols])
        await update.message.reply_text(f"📡 Cripto attualmente monitorate:\n{coin_list}")
    else:
        await update.message.reply_text("❌ Nessuna cripto monitorata al momento.")

# === COMANDO /ALERT ===
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

# === CONTROLLO PERIODICO DEI PREZZI ===
async def check_prices_job(context: ContextTypes.DEFAULT_TYPE):
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
                    f"📍 Prezzo attuale: *{current_price:.6f}$*\n"
                    f"🕯️ Apertura giornaliera: *{open_price:.6f}$*"
                )
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                to_remove.append(alert)
        except Exception as e:
            print("Errore nel controllo alert:", e)

    for a in to_remove:
        alerts.remove(a)

# === FUNZIONE PRINCIPALE ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alert", alert))
    app.job_queue.run_repeating(check_prices_job, interval=CHECK_INTERVAL, first=5)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run_polling())

if __name__ == "__main__":
    main()
