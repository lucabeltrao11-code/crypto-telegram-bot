import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from fastapi import FastAPI
from telegram.ext import ApplicationBuilder

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") + "/" + TOKEN

app = FastAPI()

# Telegram bot application
tg_app = ApplicationBuilder().token(TOKEN).build()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot online! Envie /precos para ver BTC e ETH")

# Comando /precos
async def precos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btc = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
    eth = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT").json()
    
    msg = f"💰 *Preços atuais:*\n\nBTC: ${btc['price']}\nETH: ${eth['price']}"
    await update.message.reply_text(msg, parse_mode="Markdown")

# Handlers
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("precos", precos))

# Rota Webhook Telegram
@app.post(f"/{TOKEN}")
async def telegram_webhook(update: dict):
    await tg_app.update_queue.put(Update.de_json(update, tg_app.bot))
    return {"status": "ok"}

# Rota padrão
@app.get("/")
def home():
    return {"status": "bot ativo"}

# Setar webhook automaticamente
@app.on_event("startup")
async def setup_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
    requests.get(url)
