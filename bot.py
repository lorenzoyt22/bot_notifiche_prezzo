import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import nest_asyncio
import asyncio

# === PATCH LOOP ===
nest_asyncio.apply()

# === VARIABILI D'AMBIENTE ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))  # deve essere int
CHECK_INTERVAL = 60  # secondi

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === ALERTS ===
alerts = [
    {"chat_id": CHAT_ID, "symbol": "MINA", "price": -0.188},
    {"chat_id": CHAT_ID, "symbol": "GST", "price": -0.006265}
]

# === API COINBASE ===
def get_coinbase_price(symbol: str):
    url = f"https://api.exchange.coinbase.com/products/{symbol.upper()}-USD/ticker"
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError("Simbolo non valido o problema API Coinbase.")
    return float(r.json()['price'])

def get_daily_open(symbol: str):
    url = f"https://api.exchange.coinbase.com/products/{symbol.upper()}-USD/candles?granularity=86400"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    candles = r.json()
    if not candles:
        return None
    return float(candles[0][3])

# === /START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Ciao! Questo bot ti avviserà quando una cripto raggiunge un prezzo o una variazione impostata.")

# === /ALERT <COIN> <PREZZO o %> ===
async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper()
        target_str = context.args[1]

        current_price = get_coinbase_price(symbol)
        if target_str.endswith("%"):
            # Alert percentuale
            perc = float(target_str.replace("%", ""))
            target_price = current_price * (1 + perc / 100)
            direction = "⬆️ sopra" if perc > 0 else "⬇️ sotto"
            msg = f"✅ Alert percentuale impostato: {symbol} {direction} {abs(perc)}% → target {target_price:.6f}$"
        else:
            # Alert a valore fisso
            target_price = float(target_str)
            direction = "⬆️ sopra" if target_price > current_price else "⬇️ sotto"
            msg = f"✅ Alert impostato per {symbol} {direction} {target_price}$ (ora {current_price}$)"

        alerts.append({
            "chat_id": update.effective_chat.id,
            "symbol": symbol,
            "price": target_price
        })

        await update.message.reply_text(msg)
    except Exception as e:
        print("Errore /alert:", e)
        await update.message.reply_text("❌ Usa: /alert BTC 60000 oppure /alert BTC 1% o /alert BTC -0.5%")

# === /REMOVEALERT <COIN> <PREZZO> ===
async def remove_single_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper()
        target_price = float(context.args[1])
        chat_id = update.effective_chat.id

        before = len(alerts)
        alerts[:] = [a for a in alerts if not (a["chat_id"] == chat_id and a["symbol"] == symbol and a["price"] == target_price)]
        after = len(alerts)

        if before != after:
            await update.message.reply_text(f"🗑️ Alert rimosso per {symbol} a {target_price}$")
        else:
            await update.message.reply_text("⚠️ Nessun alert trovato con quei parametri.")
    except:
        await update.message.reply_text("❌ Usa il comando così: /removealert BTC 60000")

# === /REMOVEALERTS <COIN> ===
async def remove_alerts_for_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper()
        chat_id = update.effective_chat.id

        before = len(alerts)
        alerts[:] = [a for a in alerts if not (a["chat_id"] == chat_id and a["symbol"] == symbol)]
        removed_count = before - len(alerts)

        if removed_count > 0:
            await update.message.reply_text(f"🧹 Rimossi {removed_count} alert per {symbol}.")
        else:
            await update.message.reply_text(f"⚠️ Nessun alert trovato per {symbol}.")
    except:
        await update.message.reply_text("❌ Usa il comando così: /removealerts BTC")

# === /LISTALERTS ===
async def list_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_alerts = [a for a in alerts if a["chat_id"] == chat_id]

    if not user_alerts:
        await update.message.reply_text("📭 Non hai alert attivi.")
        return

    msg_lines = ["📋 *I tuoi alert attivi:*"]
    for a in user_alerts:
        msg_lines.append(f"• {a['symbol']} → {a['price']}$")

    await update.message.reply_text("\n".join(msg_lines), parse_mode="Markdown")

# === CONTROLLO PERIODICO ===
async def check_prices_job(context: ContextTypes.DEFAULT_TYPE):
    to_remove = []
    for alert in alerts:
        try:
            current_price = get_coinbase_price(alert["symbol"])
            target_price = alert["price"]
            chat_id = alert["chat_id"]

            if current_price >= target_price or current_price <= target_price:
                open_price = get_daily_open(alert["symbol"])
                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
                direction = "📈SALE" if current_price >= target_price else "📉SCENDE"
                msg = (
                    f"{direction} *ALERT PREZZO RAGGIUNTO*\n"
                    f"💰 Cripto: *{alert['symbol']}*\n"
                    f"📅 Data: *{now}*\n"
                    f"📍 Prezzo attuale: *{current_price:.6f}$*\n"
                    f"🎯 Target: *{target_price:.6f}$*\n"
                    f"🕯️ Apertura giornaliera: *{open_price:.6f}$*"
                )
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                to_remove.append(alert)
        except Exception as e:
            print("Errore nel controllo alert:", e)

    for a in to_remove:
        alerts.remove(a)

# === MAIN ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("listalerts", list_alerts))
    app.add_handler(CommandHandler("removealert", remove_single_alert))
    app.add_handler(CommandHandler("removealerts", remove_alerts_for_coin))

    app.job_queue.run_repeating(check_prices_job, interval=CHECK_INTERVAL, first=5)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run_polling())

if __name__ == "__main__":
    main()
