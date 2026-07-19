import subprocess, sys, importlib
try:
    import nest_asyncio
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "nest-asyncio"])
    import nest_asyncio
nest_asyncio.apply()

import asyncio, logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8847925540:AAFO-af6iMFKtwmOT_8sxXStYxCxYcvexYk"
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 البوت الأسطوري جاهز! /scan3 أو /scan4")

async def scan3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ تم استقبال أمر scan3 (الفحص الفعلي قيد التطوير)")

async def scan4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ تم استقبال أمر scan4 (الفحص الفعلي قيد التطوير)")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan3", scan3))
    app.add_handler(CommandHandler("scan4", scan4))
    print("⚡ البوت يعمل داخل المفسر...")
    await app.run_polling()

asyncio.run(main())