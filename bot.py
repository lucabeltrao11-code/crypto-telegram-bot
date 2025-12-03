import requests
import pandas as pd
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
import os

# Token vem da variável de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

BINANCE_URL = "https://api.binance.com/api/v3/klines"

def get_price(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    data = requests.get(url).json()
    return float(data["price"])

def get_ma(symbol="BTCUSDT"):
    params = {
        "symbol": symbol,
        "interval": "1d",
        "limit": 30
    }
    data = requests.get(BINANCE_URL, params=params).json()
    closes = [float(c[4]) for c in data]

    df = pd.DataFrame({"close": closes})
    df["MA7"] = df["close"].rolling(window=7).mean()
    df["MA21"] = df["close"].rolling(window=21).mean()

    return df.iloc[-1]["MA7"], df.iloc[-1]["MA21"]

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Bot de monitoramento ligado!\n\n"
        "Comandos disponíveis:\n"
        "📈 /precos — preços BTC/ETH\n"
        "📊 /tendencias — MA7 x MA21\n"
        "🚨 /alerta BTC 90000 — criar alerta\n"
    )

def precos(update: Update, context: CallbackContext):
    btc = get_price("BTCUSDT")
    eth = get_price("ETHUSDT")

    update.message.reply_text(
        f"💰 *Preços atuais:*\n\n"
        f"₿ Bitcoin: *${btc:,.2f}*\n"
        f"♦ Ethereum: *${eth:,.2f}*",
        parse_mode="Markdown"
    )

def tendencias(update: Update, context: CallbackContext):
    btc_ma7, btc_ma21 = get_ma("BTCUSDT")
    eth_ma7, eth_ma21 = get_ma("ETHUSDT")

    def trend(ma7, ma21):
        return "📈 Alta" if ma7 > ma21 else "📉 Baixa"

    update.message.reply_text(
        f"📊 *Tendências:*\n\n"
        f"₿ Bitcoin: {trend(btc_ma7, btc_ma21)}\n"
        f"MA7: {btc_ma7:,.2f} — MA21: {btc_ma21:,.2f}\n\n"
        f"♦ Ethereum: {trend(eth_ma7, eth_ma21)}\n"
        f"MA7: {eth_ma7:,.2f} — MA21: {eth_ma21:,.2f}",
        parse_mode="Markdown"
    )

alerts = {}

def alerta(update: Update, context: CallbackContext):
    try:
        symbol = context.args[0].upper()
        price = float(context.args[1])
        chat_id = update.message.chat_id

        alerts[chat_id] = {"symbol": symbol, "price": price}

        update.message.reply_text(
            f"🚨 Alerta ativado!\n"
            f"{symbol} será avisado quando chegar em ${price}."
        )
    except:
        update.message.reply_text("Use: /alerta BTC 90000")

def check_alerts(context: CallbackContext):
    for chat_id, a in list(alerts.items()):
        symbol = a["symbol"] + "USDT"
        target = a["price"]

        price = get_price(symbol)

        if price <= target:
            context.bot.send_message(
                chat_id,
                f"⚠️ ALERTA!\n{symbol[:-4]} chegou em ${price:,.2f} (alvo: ${target})!"
            )
            del alerts[chat_id]

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("precos", precos))
    dp.add_handler(CommandHandler("tendencias", tendencias))
    dp.add_handler(CommandHandler("alerta", alerta))

    job = updater.job_queue
    job.run_repeating(check_alerts, interval=60, first=5)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
