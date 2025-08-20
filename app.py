import os
from flask import Flask, request
import requests

TOKEN = os.environ.get("BOT_TOKEN")  # Render 환경변수에 BOT_TOKEN 등록
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# 루트 확인용
@app.route("/", methods=["GET"])
def index():
    return "Telegram bot is running via webhook!", 200


# Webhook 엔드포인트
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if not data or "message" not in data:
        return "no message", 200

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    # 간단한 명령 처리
    if text.startswith("/start"):
        send_message(chat_id, "안녕하세요! 봇이 시작되었습니다 😊")
    elif text.startswith("/monitor"):
        send_message(chat_id, f"모니터 명령 감지됨: {text}")
    else:
        send_message(chat_id, f"메시지 수신: {text}")

    return "ok", 200


def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("send_message error:", e)


if __name__ == "__main__":
    # Render에서 gunicorn 실행, 로컬 테스트용으로만 실행됨
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
