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

# --- НАСТРОЙКИ И ДИРЕКТОРИИ ---
BOT_TOKEN = "8846880400:AAHGhCWXJagGcmoTaPg4tkJCZ-QNk436lW8"
DOWNLOAD_DIR = "downloads"
TASKS_FILE = "telegram_tasks.json"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Инициализация хранилища задач
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

# --- FASTAPI СЕРВЕР ДЛЯ СВЯЗИ С APP_2.PY ---
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

# --- СКАЧИВАНИЕ ВИДЕО (YT-DLP С КУКИ-ФАЙЛОМ) ---
def download_video(video_url: str, output_path: str) -> str:
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'cookiefile': 'cookies.txt',  # Обход проверки "Sign in to confirm you’re not a bot"
        'socket_timeout': 30,
        'quiet': False,
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'web']
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    if os.path.exists(output_path):
        return output_path

    # Проверка возможных альтернативных расширений после слияния
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
    bot.reply_to(
        message,
        "👋 Привет! Отправь мне ссылку на видео (YouTube / Shorts), и я подготовлю его для нарезки в TikTok Ai 57."
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "⚠️ Пожалуйста, отправь корректную ссылку на видео.")
        return

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or f"id_{user_id}"

    status_msg = bot.reply_to(message, "⏳ Начинаю скачивание видео с обходом защиты...")

    filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
    local_path = os.path.join(DOWNLOAD_DIR, filename)

    try:
        download_video(url, local_path)

        # Сохранение задачи в базу для приложения
        tasks = load_tasks()
        new_task = {
            "user_id": user_id,
            "username": username,
            "url": url,
            "filename": filename,
            "local_path": local_path
        }
        tasks.append(new_task)
        save_tasks(tasks)

        bot.edit_message_text(
            f"✅ Видео успешно скачано!\nОно уже появилось в веб-интерфейсе TikTok Ai 57 в списке очереди.",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id
        )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка скачивания: {e}\nУбедись, что файл cookies.txt актуален.",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id
        )

# --- ЗАПУСК БОТА И API ---
def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # Запуск Telegram-бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Запуск веб-сервера FastAPI на порту 8000 (или из переменной PORT для Render)
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)