import logging
import os
import time
import urllib.request
import urllib.error
import ssl
import itertools
import string
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8847925540:AAFO-af6iMFKtwmOT_8sxXStYxCxYcvexYk"
logging.basicConfig(level=logging.INFO)

MAX_THREADS = 300
TIMEOUT = 0.5
PROGRESS_INTERVAL = 500
RETRY_DELAY = 0.1

CHARS = string.ascii_lowercase + string.digits
URL = "https://profiles.np.playstation.net/profiles/"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def scan_names_sync(length, progress_callback):
    total = len(CHARS) ** length
    found = []
    checked = 0
    start_time = time.time()

    def check(name):
        for attempt in range(3):
            try:
                req = urllib.request.Request(URL + name, method="HEAD")
                with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
                    if r.getcode() == 404:
                        return name
                    return None
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return name
                if e.code in (429, 500, 502, 503):
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                return None
            except:
                time.sleep(RETRY_DELAY)
                continue
        return None

    names = (''.join(p) for p in itertools.product(CHARS, repeat=length))
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        for result in ex.map(check, names):
            checked += 1
            if result:
                found.append(result)
            if checked % PROGRESS_INTERVAL == 0:
                elapsed = time.time() - start_time
                rate = checked / elapsed if elapsed > 0 else 0
                remaining = (total - checked) / rate if rate > 0 else 0
                progress_callback(checked, total, len(found), elapsed, remaining)

    elapsed = time.time() - start_time
    progress_callback(checked, total, len(found), elapsed, 0, final=True)
    return found

async def scan_names(update: Update, context: ContextTypes.DEFAULT_TYPE, length: int):
    chat_id = update.effective_chat.id
    msg = await context.bot.send_message(chat_id, f"⚡ بدء الفحص الأسطوري {length}... (0/{len(CHARS)**length})")
    message_id = msg.message_id
    loop = asyncio.get_running_loop()

    def progress_callback(checked, total, found_count, elapsed, remaining, final=False):
        if final:
            text = f"🏆 اكتمل! فحص {checked:,} اسماً، متاح: {found_count}، الزمن: {elapsed:.0f}s"
        else:
            text = (f"⚡ فحص: {checked:,}/{total:,} | متاح: {found_count} | "
                    f"مضى: {elapsed:.0f}s | متبقي: {remaining:.0f}s")
        coro = context.bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
        asyncio.run_coroutine_threadsafe(coro, loop)

    found = await loop.run_in_executor(None, scan_names_sync, length, progress_callback)

    if found:
        await context.bot.send_message(chat_id, "🔥 الأسماء المتاحة:\n" + "\n".join(found[:20]))
    else:
        await context.bot.send_message(chat_id, "💀 لم يتم العثور على أي اسم.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 البوت الأسطوري جاهز! /scan3 أو /scan4")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ /scan3 - فحص ثلاثي\n/scan4 - فحص رباعي")

async def scan3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await scan_names(update, context, 3)

async def scan4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await scan_names(update, context, 4)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("scan3", scan3))
    app.add_handler(CommandHandler("scan4", scan4))
    print("⚡ البوت الأسطوري يعمل...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    task = loop.create_task(main())
    print("✅ البوت يعمل في الخلفية. افتح تيليجرام وجرب الأوامر.")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("🛑 تم إيقاف البوت.")
        task.cancel()
        loop.stop()
        loop.close()
