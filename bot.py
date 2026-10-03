import os
import json
import uuid
import asyncio
import threading
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import yt_dlp
from telebot import TeleBot, types

# Твой токен уже на месте
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

@app.get("/tasks")
def get_tasks():
    return load_tasks()

@app.get("/files/{filename}")
def get_file(filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="Файл не найден")

# --- СКАЧИВАНИЕ БЕЗ КУКОВ (МАГИЯ ANDROID) ---
def download_video(video_url: str, output_path: str) -> str:
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        # ВЕСЬ СЕКРЕТ ЗДЕСЬ: Притворяемся смартфоном. Никакого 'web'.
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    if os.path.exists(output_path):
        return output_path

    base, _ = os.path.splitext(output_path)
    for ext in ['.mkv', '.webm', '.mp4']:
        candidate = base + ext
        if os.path.exists(candidate):
            os.rename(candidate, output_path)
            return output_path

    raise Exception("Файл не был сохранен.")

# --- ТЕЛЕГРАМ-БОТ ---
bot = TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Привет! Кидай ссылку (YouTube / TikTok), качаю без куков.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "⚠️ Это не похоже на ссылку.")
        return

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"id_{user_id}"

    status_msg = bot.reply_to(message, "⏳ Обхожу защиту Ютуба и начинаю загрузку...")

    filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
    local_path = os.path.join(DOWNLOAD_DIR, filename)

    try:
        download_video(url, local_path)

        # Сохраняем в самое начало списка, чтобы новое видео было первым
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
            f"❌ Ошибка: {e}",
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