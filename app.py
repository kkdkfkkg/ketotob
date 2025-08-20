import requests
import time
import threading
from flask import Flask, request

# ---------------- 네이버 API ----------------
CLIENT_ID = "UQ2dEN7Cv8zVjV1bvORy"
CLIENT_SECRET = "HztMkAp71y"
NAVER_HEADERS = {
    "X-Naver-Client-Id": CLIENT_ID,
    "X-Naver-Client-Secret": CLIENT_SECRET
}

# ---------------- 텔레그램 ----------------
TELEGRAM_TOKEN = "8261709160:AAFpweKkpOddsbcg3CsFjx1FJNE7ZcbQdMo"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Flask 앱
app = Flask(__name__)

# 모니터링 상태 저장 (chat_id 별로 관리)
monitoring_keywords = {}  # {chat_id: {"keyword": str, "seen": set(), "interval": int}}

# ---------------- 네이버 검색 ----------------
def naver_search(query, target="news", display=5):
    url = f"https://openapi.naver.com/v1/search/{target}.json"
    params = {"query": query, "display": display, "sort": "date"}
    res = requests.get(url, headers=NAVER_HEADERS, params=params)
    return res.json() if res.status_code == 200 else {}

# ---------------- 텔레그램 메시지 ----------------
def send_telegram(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": text})

# ---------------- 모니터링 쓰레드 ----------------
def monitor_task(chat_id):
    """백그라운드 모니터링"""
    while chat_id in monitoring_keywords:
        keyword = monitoring_keywords[chat_id]["keyword"]
        seen_links = monitoring_keywords[chat_id]["seen"]
        interval = monitoring_keywords[chat_id]["interval"]
        sources = ["news", "blog", "cafearticle", "webkr"]

        for src in sources:
            items = naver_search(keyword, target=src, display=5).get("items", [])
            for item in items:
                link = item["link"]
                if link not in seen_links:
                    title = item["title"].replace("<b>", "").replace("</b>", "")
                    msg = f"🔔 [{src.upper()}] 새 글 발견!\n\n{title}\n👉 {link}"
                    send_telegram(chat_id, msg)
                    seen_links.add(link)

        time.sleep(interval)

# ---------------- 텔레그램 명령어 처리 ----------------
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.startswith("/monitor "):
            try:
                _, keyword, interval_str = text.split(" ", 2)
                interval = int(interval_str)
            except ValueError:
                send_telegram(chat_id, "⚠️ 사용법: /monitor <키워드> <주기(초)>")
                return "OK"

            monitoring_keywords[chat_id] = {"keyword": keyword, "seen": set(), "interval": interval}
            send_telegram(chat_id, f"✅ '{keyword}' 모니터링을 시작합니다. (주기: {interval}초)")
            threading.Thread(target=monitor_task, args=(chat_id,), daemon=True).start()

        elif text.startswith("/stop"):
            if chat_id in monitoring_keywords:
                keyword = monitoring_keywords[chat_id]["keyword"]
                del monitoring_keywords[chat_id]
                send_telegram(chat_id, f"🛑 '{keyword}' 모니터링을 중지했습니다.")
            else:
                send_telegram(chat_id, "⚠️ 현재 모니터링 중인 키워드가 없습니다.")

        elif text.startswith("/list"):
            if chat_id in monitoring_keywords:
                kw = monitoring_keywords[chat_id]["keyword"]
                iv = monitoring_keywords[chat_id]["interval"]
                send_telegram(chat_id, f"👀 현재 모니터링 중:\n- 키워드: {kw}\n- 주기: {iv}초")
            else:
                send_telegram(chat_id, "⚠️ 현재 모니터링 중인 키워드가 없습니다.")

    return "OK"

@app.route("/")
def index():
    return "Telegram Bot Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
