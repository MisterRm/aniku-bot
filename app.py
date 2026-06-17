from flask import Flask, request, jsonify, send_file
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GITHUB_REPO = "RMBLOGG/aniku-app"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return requests.post(f"{BASE_URL}/sendMessage", json=payload)

def get_latest_release():
    res = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
    return res.json() if res.status_code == 200 else None

def get_all_releases():
    res = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases")
    return res.json() if res.status_code == 200 else []

def clean_body(body):
    skip_sections = ["instalasi", "minimum android"]
    lines = body.splitlines()
    result = []
    skip = False
    for l in lines:
        lower = l.strip().lower()
        if any(s in lower for s in skip_sections):
            skip = True
        if lower.startswith("### ") and not any(s in lower for s in skip_sections):
            skip = False
        if skip:
            continue
        if "github.com" in l or "Full Changelog" in l:
            continue
        if l.startswith("### "):
            result.append(f"*{l[4:].strip()}*")
        elif l.strip() == "---":
            continue
        elif l.strip().startswith("> "):
            continue
        else:
            result.append(l)
    while result and not result[-1].strip():
        result.pop()
    return "\n".join(result)

def answer_callback(callback_query_id):
    requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": callback_query_id})

def main_menu(chat_id):
    text = "🎌 *Aniku — Bot Resmi*\n\nInfo rilis, versi, & download ada di sini."
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📦 Versi Terbaru", "callback_data": "latest"},
                {"text": "📋 Semua Versi", "callback_data": "versions"}
            ],
            [{"text": "📲 Download", "callback_data": "download"}]
        ]
    }
    send_telegram(chat_id, text, reply_markup)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

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
                body = clean_body(release.get("body", "").strip())
                assets = release.get("assets", [])
                dl_count = assets[0].get("download_count", 0) if assets else 0
                text = f"📦 *{name}* (`{tag}`)\n\n{body}\n\n📥 Download: {dl_count}x\n📲 https://aniku-downloads.vercel.app/"
            else:
                text = "Gagal ambil data release."
            send_telegram(chat_id, text, {"inline_keyboard": [[{"text": "⬅️ Kembali", "callback_data": "menu"}]]})

        elif action == "versions":
            releases = get_all_releases()
            if releases:
                lines = []
                for r in releases[:10]:
                    tag = r.get("tag_name", "-")
                    name = r.get("name", tag)
                    assets = r.get("assets", [])
                    dl = assets[0].get("download_count", 0) if assets else 0
                    lines.append(f"• *{name}* — {dl}x download")
                text = "📋 *Semua Versi Aniku:*\n\n" + "\n".join(lines)
            else:
                text = "Gagal ambil data versi."
            send_telegram(chat_id, text, {"inline_keyboard": [[{"text": "⬅️ Kembali", "callback_data": "menu"}]]})

        elif action == "download":
            text = "📲 *Download Aniku*\n\nhttps://aniku-downloads.vercel.app/"
            send_telegram(chat_id, text, {"inline_keyboard": [[{"text": "⬅️ Kembali", "callback_data": "menu"}]]})

        elif action == "menu":
            main_menu(chat_id)

    elif "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        if text in ["/start", "/menu"]:
            main_menu(chat_id)

    return jsonify({"ok": True})

@app.route("/send", methods=["POST"])
def send_to_channel():
    data = request.json
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"ok": False, "error": "Empty message"})
    if not CHAT_ID:
        return jsonify({"ok": False, "error": "TELEGRAM_CHAT_ID not set"})
    res = send_telegram(CHAT_ID, msg)
    result = res.json()
    return jsonify({"ok": result.get("ok", False)})

@app.route("/admin")
def admin():
    return send_file("admin.html")

@app.route("/")
def index():
    return "Aniku Bot is running!"

if __name__ == "__main__":
    app.run(debug=True)
