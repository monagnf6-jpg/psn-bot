from flask import Flask, render_template, jsonify, request
import threading, time, urllib.request, urllib.error, ssl, itertools, string, socket
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
status_lock = threading.Lock()
status = {
    "running": False,
    "phase": "idle",
    "checked": 0,
    "total": 0,
    "found": [],
    "log": [],
    "start_time": None,
    "elapsed": 0,
    "done": False
}
CHARS = string.ascii_lowercase + string.digits
URL = "https://profiles.np.playstation.net/profiles/"
THREADS = 15
TIMEOUT = 0.5
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def double_check(name):
    try:
        req = urllib.request.Request(URL + name, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            return r.getcode() == 404
    except urllib.error.HTTPError as e:
        return e.code == 404
    except:
        return False

def check_name(name, length):
    try:
        req = urllib.request.Request(URL + name, method="HEAD")
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            if r.getcode() == 404 and double_check(name):
                with status_lock:
                    status["found"].append((name, length))
                    status["log"].append(f"[+] {name} ({length} حروف)")
                return True
    except urllib.error.HTTPError as e:
        if e.code == 404 and double_check(name):
            with status_lock:
                status["found"].append((name, length))
                status["log"].append(f"[+] {name} ({length} حروف)")
            return True
    except:
        pass
    return False

def scan_phase(length):
    global status
    total = len(CHARS) ** length
    with status_lock:
        status["total"] = total
        status["checked"] = 0
        status["phase"] = f"{length} أحرف"
    names = (''.join(p) for p in itertools.product(CHARS, repeat=length))
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futures = {ex.submit(check_name, name, length): name for name in names}
        for future in as_completed(futures):
            with status_lock:
                status["checked"] += 1
                status["elapsed"] = time.time() - status["start_time"]
            try:
                future.result(timeout=0.2)
            except:
                pass

def run_bot():
    global status
    with status_lock:
        status["running"] = True
        status["done"] = False
        status["found"] = []
        status["log"] = []
        status["start_time"] = time.time()
        status["elapsed"] = 0
    scan_phase(3)
    scan_phase(4)
    with status_lock:
        status["running"] = False
        status["done"] = True
        status["elapsed"] = time.time() - status["start_time"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    if status["running"]:
        return jsonify({"error": "يعمل حالياً"}), 400
    threading.Thread(target=run_bot, daemon=True).start()
    return jsonify({"message": "تم بدء الفحص"})

@app.route('/status')
def get_status():
    with status_lock:
        elapsed = status["elapsed"]
        checked = status["checked"]
        total = status["total"]
        remaining = 0
        if checked > 0 and elapsed > 0:
            rate = checked / elapsed
            remaining = (total - checked) / rate if rate > 0 else 0
        return jsonify({
            "running": status["running"],
            "done": status["done"],
            "phase": status["phase"],
            "checked": checked,
            "total": total,
            "found": len(status["found"]),
            "log": status["log"][-15:],
            "elapsed": int(elapsed),
            "remaining": int(remaining)
        })

@app.route('/results')
def results():
    with status_lock:
        return jsonify({"found": status["found"], "log": status["log"]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
