import os
import json
import uuid
import threading
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from telebot import TeleBot
import yt_dlp
from pytubefix import YouTube

# Токен бота
BOT_TOKEN = "8846880400:AAHGhCWXJagGcmoTaPg4tkJCZ-QNk436lW8"
DOWNLOAD_DIR = "downloads"
TASKS_FILE = "telegram_tasks.json"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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
app = FastAPI(title="TikTok57 Remote Bot")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

@app.get("/")
def index(): return "Server OK"

@app.get("/tasks")
def get_tasks(): return load_tasks()

@app.get("/files/{filename}")
def get_file(filename: str):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(path): return FileResponse(path, media_type="video/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="Not found")

# --- ГИБРИДНОЕ СКАЧИВАНИЕ ---
def download_video(url: str, output_path: str):
    # 1. Если это ЮТУБ - используем бронебойный pytubefix
    if "youtu" in url:
        # Притворяемся смартфоном на Android
        yt = YouTube(url, client='ANDROID')
        # Берем поток, где видео и звук уже склеены
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            stream = yt.streams.get_highest_resolution()
        
        stream.download(
            output_path=os.path.dirname(output_path),
            filename=os.path.basename(output_path)
        )
        return output_path
        
    # 2. Если это TikTok, Reels и т.д. - используем yt-dlp
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        base, _ = os.path.splitext(output_path)
        for ext in ['.mkv', '.webm', '.mp4']:
            if os.path.exists(base + ext):
                os.rename(base + ext, output_path)
                break
        return output_path

# --- ТЕЛЕГРАМ БОТ ---
bot = TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(m):
    bot.reply_to(m, "👋 Привет! Кидай ссылку (YouTube или TikTok).")

@bot.message_handler(func=lambda m: True)
def handle_message(m):
    url = m.text.strip()
    if not url.startswith("http"):
        return bot.reply_to(m, "⚠️ Это не похоже на ссылку.")

    status = bot.reply_to(m, "⏳ Подключаюсь к серверам, качаю...")
    filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
    path = os.path.join(DOWNLOAD_DIR, filename)

    try:
        download_video(url, path)
        tasks = load_tasks()
        tasks.insert(0, {
            "user_id": m.from_user.id,
            "username": m.from_user.username or "User",
            "url": url,
            "filename": filename
        })
        save_tasks(tasks)
        bot.edit_message_text("✅ Готово! Открывай TikTok Ai 57, видео уже там.", chat_id=status.chat.id, message_id=status.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка скачивания: {e}", chat_id=status.chat.id, message_id=status.message_id)

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))