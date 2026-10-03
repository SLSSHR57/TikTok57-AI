import os
import json
import threading
import asyncio
from flask import Flask, send_from_directory, jsonify
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import yt_dlp

# Твой токен
BOT_TOKEN = "8846880400:AAHGhCWXJagGcmoTaPg4tkJCZ-QNk436lW8"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Flask сервер для отдачи файлов приложению
app = Flask(__name__)
TASKS_FILE = "tasks.json"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def save_task(user_id, username, video_url, filename):
    tasks = []
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            try: tasks = json.load(f)
            except: pass
    
    tasks.insert(0, {
        "username": username or "User",
        "url": video_url,
        "filename": filename # Сохраняем только имя файла для API
    })
    
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=4, ensure_ascii=False)

# --- API РОУТЫ ---
@app.route('/')
def index():
    return "Bot is alive!" # Сюда будет стучаться UptimeRobot

@app.route('/tasks')
def get_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/files/<filename>')
def get_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- ЛОГИКА ТЕЛЕГРАМ БОТА ---
def download_video(url, output_path):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Салют! Бот на сервере. Кидай ссылку, и я подготовлю её для приложения.")

@dp.message()
async def handle_link(message: Message):
    url = message.text.strip()
    if not url.startswith("http"):
        return await message.answer("Бро, это не ссылка.")

    status_msg = await message.answer("🔄 Загружаю на сервер Render...")
    
    filename = f"tg_{message.message_id}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    try:
        await asyncio.to_thread(download_video, url, filepath)
        save_task(message.from_user.id, message.from_user.username, url, filename)
        await status_msg.edit_text("✅ Готово! Открывай TikTok Ai 57 на маке, видео уже в базе.")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка скачивания: {e}")

async def main():
    # Запускаем Flask в отдельном потоке, чтобы он не блокировал бота
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот и API запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())