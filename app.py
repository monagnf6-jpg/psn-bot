import subprocess, sys, importlib
try:
    import nest_asyncio
except ImportError:
    print("📦 تثبيت nest-asyncio...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "nest-asyncio"])
    import nest_asyncio
nest_asyncio.apply()

import asyncio, logging, time, urllib.request, urllib.error, ssl, itertools, string
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
                    return name if r.getcode() == 404 else None
            except urllib.error.HTTPError as e:
                if e.code == 404: return name
                if e.code in (429, 500, 502, 503):
                    time.sleep(RETRY_DELAY * (attempt + 1)); continue
                return None
            except: time.sleep(RETRY_DELAY); continue
        return None
    names = (''.join(p) for p in itertools.product(CHARS, repeat=length))
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        for result in ex.map(check, names):
            checked += 1
            if result: found.append(result)
            if checked % PROGRESS_INTERVAL == 0:
                elapsed = time.time() - start_time
                rate = checked / elapsed if elapsed else 0
                remaining = (total - checked) / rate if rate else 0
                progress_callback(checked, total, len(found), elapsed, remaining)
    elapsed = time.time() - start_time
    progress_callback(checked, total, len(found), elapsed, 0, final=True)
    return found

async def scan_names(update, context, length):
    chat_id = update.effective_chat.id
    msg = await context.bot.send_message(chat_id, f"⚡ بدء الفحص الأسطوري {length}... (0/{len(CHARS)**length})")
    loop = asyncio.get_running_loop()
    def progress_callback(checked, total, found_count, elapsed, remaining, final=False):
        text = f"🏆 اكتمل! فحص {checked:,} اسماً، متاح: {found_count}، الزمن: {elapsed:.0f}s" if final else f"⚡ فحص: {checked:,}/{total:,} | متاح: {found_count} | مضى: {elapsed:.0f}s | متبقي: {remaining:.0f}s"
        asyncio.run_coroutine_threadsafe(context.bot.edit_message_text(text, chat_id=chat_id, message_id=msg.message_id), loop)
    found = await loop.run_in_executor(None, scan_names_sync, length, progress_callback)
    await context.bot.send_message(chat_id, ("🔥 الأسماء المتاحة:\n" + "\n".join(found[:20])) if found else "💀 لم يتم العثور على أي اسم.")

async def start(update, context): await update.message.reply_text("🔥 البوت الأسطوري جاهز! /scan3 أو /scan4")
async def help_command(update, context): await update.message.reply_text("⚡ /scan3 - فحص ثلاثي\n/scan4 - فحص رباعي")
async def scan3(update, context): await scan_names(update, context, 3)
async def scan4(update, context): await scan_names(update, context, 4)

async def main():
    app = Application.builder().token(TOKEN).build()
    for cmd, handler in [("start", start), ("help", help_command), ("scan3", scan3), ("scan4", scan4)]:
        app.add_handler(CommandHandler(cmd, handler))
    print("⚡ البوت الأسطوري يعمل داخل المفسر...")
    await app.run_polling()

print("🚀 جارٍ تشغيل البوت...")
asyncio.run(main())