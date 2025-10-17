import os
import requests
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio

nest_asyncio.apply()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHECK_INTERVAL = 180  # 3 minuti
logging.basicConfig(level=logging.WARNING)

session = requests.Session()

alerts = []

def get_price(symbol: str):
    symbol = symbol.upper()
    if symbol == "USDT.D":
        try:
            data = session.get("https://api.coinlore.net/api/global/", timeout=5).json()
            return float(data[0].get("usdt_d", 0.0))
        except:
            return None
    try:
        url = f"https://api.exchange.coinbase.com/products/{symbol}-USD/ticker"
        r = session.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return float(r.json()["price"])
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot attivo. Usa /alert <COIN> <VALORE o %>")

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usa: /alert BTC 60000 oppure /alert BTC -2%")
        return
    symbol = context.args[0].upper()
    target = context.args[1]
    price = get_price(symbol)
    if price is None:
        await update.message.reply_text("⚠️ Simbolo non valido o non disponibile.")
        return

    if target.endswith("%"):
        perc = float(target[:-1])
        target_price = price * (1 + perc / 100)
    else:
        target_price = float(target)

    alerts.append({
        "chat_id": update.effective_chat.id,
        "symbol": symbol,
        "price": target_price
    })
    await update.message.reply_text(f"✅ Alert impostato {symbol} → {target_price:.4f} (ora {price:.4f})")

async def list_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_alerts = [a for a in alerts if a["chat_id"] == update.effective_chat.id]
    if not user_alerts:
        await update.message.reply_text("📭 Nessun alert attivo.")
        return
    text = "\n".join(f"• {a['symbol']} {a['price']:.4f}" for a in user_alerts)
    await update.message.reply_text(f"📋 Alert attivi:\n{text}")

async def remove_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("❌ Usa: /removealert BTC")
        return
    sym = context.args[0].upper()
    before = len(alerts)
    alerts[:] = [a for a in alerts if a["symbol"] != sym or a["chat_id"] != update.effective_chat.id]
    after = len(alerts)
    await update.message.reply_text("🧹 Rimossi" if after < before else "⚠️ Nessun alert trovato.")

async def check_prices(context: ContextTypes.DEFAULT_TYPE):
    to_remove = []
    for a in alerts:
        price = get_price(a["symbol"])
        if price is None:
            continue
        if (price >= a["price"] and a["price"] > 0) or (price <= a["price"] and a["price"] < 0):
            msg = (
                f"🎯 *{a['symbol']}* ha raggiunto {a['price']:.4f}\n"
                f"📍 Prezzo attuale: {price:.4f}\n"
                f"⏰ {datetime.utcnow().strftime('%H:%M:%S UTC')}"
            )
            await context.bot.send_message(a["chat_id"], msg, parse_mode="Markdown")
            to_remove.append(a)
    for x in to_remove:
        alerts.remove(x)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("listalerts", list_alerts))
    app.add_handler(CommandHandler("removealert", remove_alert))
    app.job_queue.run_repeating(check_prices, interval=CHECK_INTERVAL, first=10)
    asyncio.get_event_loop().run_until_complete(app.run_polling())

if __name__ == "__main__":
    main()
