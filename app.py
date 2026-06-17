from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GITHUB_REPO = "RMBLOGG/aniku-app"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

def get_latest_release():
    res = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
    return res.json() if res.status_code == 200 else None

def get_all_releases():
    res = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases")
    return res.json() if res.status_code == 200 else []

def main_menu(chat_id):
    text = "🎌 *Aniku Bot*\n\nSelamat datang! Pilih menu di bawah:"
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📦 Versi Terbaru", "callback_data": "latest"},
                {"text": "📋 Semua Versi", "callback_data": "versions"}
            ],
            [
                {"text": "📲 Download", "callback_data": "download"}
            ]
        ]
    }
    send_message(chat_id, text, reply_markup)

def answer_callback(callback_query_id):
    requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": callback_query_id})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # Handle callback query (button tap)
    if "callback_query" in data:
        cq = data["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        action = cq["data"]
        answer_callback(cq["id"])

        if action == "latest":
            release = get_latest_release()
            if release:
                tag = release.get("tag_name", "-")
                name = release.get("name", "-")
                body = release.get("body", "Tidak ada changelog.").strip()
                # Hapus baris Full Changelog
                lines = [l for l in body.splitlines() if "Full Changelog" not in l and "github.com" not in l]
                # Convert markdown ### ke bold Telegram
                converted = []
                for l in lines:
                    if l.startswith("### "):
                        converted.append(f"*{l[4:]}*")
                    else:
                        converted.append(l)
                body = "\n".join(converted).strip()
                text = f"📦 *{name}* (`{tag}`)\n\n{body}\n\n📲 Download: https://aniku-downloads.vercel.app/"
            else:
                text = "❌ Gagal ambil data release."
            reply_markup = {
                "inline_keyboard": [[{"text": "⬅️ Kembali", "callback_data": "menu"}]]
            }
            send_message(chat_id, text, reply_markup)

        elif action == "versions":
            releases = get_all_releases()
            if releases:
                lines = []
                for r in releases[:10]:
                    tag = r.get("tag_name", "-")
                    name = r.get("name", tag)
                    lines.append(f"• *{name}* (`{tag}`)")
                text = "📋 *Semua Versi Aniku:*\n\n" + "\n".join(lines)
            else:
                text = "❌ Gagal ambil data versi."
            reply_markup = {
                "inline_keyboard": [[{"text": "⬅️ Kembali", "callback_data": "menu"}]]
            }
            send_message(chat_id, text, reply_markup)

        elif action == "download":
            text = "📲 *Download Aniku*\n\nKlik link di bawah untuk download APK terbaru:\nhttps://aniku-downloads.vercel.app/"
            reply_markup = {
                "inline_keyboard": [[{"text": "⬅️ Kembali", "callback_data": "menu"}]]
            }
            send_message(chat_id, text, reply_markup)

        elif action == "menu":
            main_menu(chat_id)

    # Handle regular message
    elif "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if text in ["/start", "/menu"]:
            main_menu(chat_id)

    return jsonify({"ok": True})

@app.route("/")
def index():
    return "Aniku Bot is running!"

if __name__ == "__main__":
    app.run(debug=True)
