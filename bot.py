import os
import json
import uuid
import threading
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from telebot import TeleBot

# Токен на месте
BOT_TOKEN = "8846880400:AAHGhCWXJagGcmoTaPg4tkJCZ-QNk436lW8"
DOWNLOAD_DIR = "downloads"
TASKS_FILE = "telegram_tasks.json"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

if not os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

def load_tasks() -> list:
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_tasks(tasks: list):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# --- FASTAPI СЕРВЕР ---
app = FastAPI(title="TikTok57 Remote Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return "Server is running!"

@app.get("/tasks")
def get_tasks():
    return load_tasks()

@app.get("/files/{filename}")
def get_file(filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="Файл не найден")

# --- СКАЧИВАНИЕ ЧЕРЕЗ СЕКРЕТНЫЙ API (БЕЗ БАНОВ) ---
def download_video(video_url: str, output_path: str) -> str:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://cobalt.tools",
        "Referer": "https://cobalt.tools/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    data = {
        "url": video_url,
        "vQuality": "1080",
        "filenamePattern": "basic"
    }

    try:
        # 1. Просим сервера Cobalt обработать ссылку
        res = requests.post("https://api.cobalt.tools/api/json", json=data, headers=headers, timeout=15)
        res.raise_for_status()
        
        resp_json = res.json()
        if resp_json.get("status") == "error":
            raise Exception(resp_json.get("text", "Неизвестная ошибка API Cobalt"))
            
        download_url = resp_json.get("url")
        if not download_url:
            raise Exception("Cobalt не отдал ссылку на файл.")
            
        # 2. Скачиваем чистый mp4 файл
        video_res = requests.get(download_url, stream=True, timeout=60)
        video_res.raise_for_status()
        
        with open(output_path, "wb") as f:
            for chunk in video_res.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    
        return output_path
        
    except Exception as e:
        raise Exception(f"{e}")

# --- ТЕЛЕГРАМ-БОТ ---
bot = TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Привет! Кидай ссылку. Качаю через внешний API в обход любых блокировок Ютуба.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("youtu")):
        bot.reply_to(message, "⚠️ Это не похоже на ссылку.")
        return

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"id_{user_id}"

    status_msg = bot.reply_to(message, "⏳ Обхожу блокировку Ютуба и вытягиваю видео...")

    filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
    local_path = os.path.join(DOWNLOAD_DIR, filename)

    try:
        download_video(url, local_path)

        tasks = load_tasks()
        tasks.insert(0, {
            "user_id": user_id,
            "username": username,
            "url": url,
            "filename": filename
        })
        save_tasks(tasks)

        bot.edit_message_text(
            f"✅ Готово! Открывай TikTok Ai 57, видео уже там.",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id
        )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка скачивания: {e}",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id
        )

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)