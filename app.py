import streamlit as st
import os
import subprocess
import json
import shutil
import time
from moviepy.editor import VideoFileClip
import moviepy.video.fx.all as vfx
from openai import OpenAI

# --- 1. БАЗОВАЯ НАСТРОЙКА И КАСТОМНЫЙ CSS ---
st.set_page_config(page_title="TikTok Ai 57", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;800;900&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] * {
    font-family: 'Montserrat', sans-serif !important;
}

#MainMenu, header, footer, .stDeployButton { visibility: hidden; display: none !important; }

/* ЭКРАН ЗАГРУЗКИ: Монолитный черный фон поверх всего */
.splash-screen {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background: #0f0f11; z-index: 9999999; 
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    animation: splashOut 1s cubic-bezier(0.7, 0, 0.3, 1) forwards;
    animation-delay: 3s;
    pointer-events: none;
}
@keyframes splashOut {
    0% { opacity: 1; transform: scale(1); filter: blur(0); }
    100% { opacity: 0; transform: scale(1.15); filter: blur(15px); visibility: hidden; display: none; }
}

.splash-logo {
    font-size: 4.5rem; font-weight: 900; color: #ffffff; letter-spacing: -2px;
    animation: logoPop 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
    text-shadow: 0 0 30px rgba(255,0,80,0.3);
}
.splash-sub {
    color: #8E8E93; font-size: 1rem; font-weight: 600; margin-top: 12px; 
    letter-spacing: 0.25em; text-transform: uppercase;
    opacity: 0; animation: fadeIn 0.8s ease forwards; animation-delay: 0.4s;
}

/* Кинематографичный градиентный лоадер */
.splash-loader {
    width: 250px; height: 4px; background: #222228; margin-top: 45px; 
    border-radius: 4px; overflow: hidden; position: relative;
    opacity: 0; animation: fadeIn 0.8s ease forwards; animation-delay: 0.6s;
    box-shadow: 0 0 10px rgba(0,0,0,0.5);
}
.splash-loader::after {
    content: ''; position: absolute; left: 0; top: 0; height: 100%; width: 0%;
    background: linear-gradient(90deg, #ff0050, #00f2fe);
    border-radius: 4px;
    animation: loadBar 2.5s cubic-bezier(0.8, 0, 0.2, 1) forwards;
    animation-delay: 0.8s;
}

@keyframes loadBar { 0% { width: 0%; } 100% { width: 100%; } }
@keyframes logoPop { 0% { transform: scale(0.8); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
@keyframes fadeIn { 0% { opacity: 0; transform: translateY(15px); } 100% { opacity: 1; transform: translateY(0); } }

/* ОБНОВЛЕННЫЙ ПУЛЬСИРУЮЩИЙ ЗАГОЛОВОК */
.main-title {
    font-size: 3.6rem !important; 
    font-weight: 900 !important;
    text-align: center; 
    margin-bottom: 2rem;
    color: #ff0050 !important;
    letter-spacing: -2px;
    text-shadow: 0 0 20px rgba(255, 0, 80, 0.6), 0 0 40px rgba(255, 0, 80, 0.2) !important;
    animation: titlePulse 3s ease-in-out infinite;
}

@keyframes titlePulse {
    0%, 100% { text-shadow: 0 0 20px rgba(255, 0, 80, 0.5), 0 0 40px rgba(255, 0, 80, 0.2); }
    50% { text-shadow: 0 0 25px rgba(255, 0, 80, 0.8), 0 0 55px rgba(255, 0, 80, 0.4); }
}

/* ЖИВЫЕ КНОПКИ */
div.stButton > button {
    background: #ff0050 !important; color: white !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 12px !important; font-weight: 800 !important; font-size: 1.1rem !important;
    padding: 0.8rem 2rem !important; width: 100% !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    box-shadow: 0 4px 15px rgba(255, 0, 80, 0.2) !important;
}
div.stButton > button:hover {
    background: #ff1a60 !important;
    transform: translateY(-4px) scale(1.02) !important;
    box-shadow: 0 12px 30px rgba(255, 0, 80, 0.45) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
}
div.stButton > button:active {
    transform: translateY(2px) scale(0.97) !important;
    box-shadow: 0 2px 8px rgba(255, 0, 80, 0.3) !important;
}

/* ДЫШАЩИЕ ПОЛЯ ВВОДА И СЕЛЕКТОРЫ */
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
    border-radius: 10px !important; background-color: #1a1a1f !important;
    border: 1px solid #2d2d33 !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
}
div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
    border-color: #ff0050 !important;
    background-color: #1f1f25 !important;
    box-shadow: 0 0 0 3px rgba(255, 0, 80, 0.15) !important;
    transform: translateY(-2px);
}

/* ВКЛАДКИ (TABS) */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px; background-color: #121216; padding: 8px;
    border-radius: 16px; border: 1px solid #222228; justify-content: center;
}
.stTabs [data-baseweb="tab"] {
    height: 46px; border-radius: 12px; padding: 0 22px;
    color: #8E8E93; font-weight: 600; font-size: 0.95rem; border: none !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #ffffff; background: rgba(255, 255, 255, 0.05) !important;
}
.stTabs [aria-selected="true"] {
    background: #2a2a32 !important; color: #ffffff !important;
    transform: scale(1.05); box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
</style>

<!-- Splash Screen с лоадером -->
<div class="splash-screen">
    <div class="splash-logo">TikTok Ai 57</div>
    <div class="splash-sub">Video Processing Engine</div>
    <div class="splash-loader"></div>
</div>
""", unsafe_allow_html=True)

# Главный HTML-заголовок
st.markdown('<h1 class="main-title">TikTok Ai 57</h1>', unsafe_allow_html=True)

DIRECTORIES = ["temp", "assets/banners", "assets/music", "assets/fonts", "output"]
for folder in DIRECTORIES:
    os.makedirs(folder, exist_ok=True)

# --- 2. УТИЛИТЫ И НЕЙРОСЕТЬ ---
@st.cache_resource
def load_whisper_model():
    from faster_whisper import WhisperModel
    return WhisperModel("small", device="cpu", compute_type="int8")

def format_time_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100: cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def hex_to_ass_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"&H00{b}{g}{r}"

def get_video_info(video_path):
    w, d = 1080, 5.0
    try:
        cmd_w = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width", "-of", "default=nw=1:nk=1", video_path]
        w = int(subprocess.run(cmd_w, capture_output=True, text=True).stdout.strip())
    except: pass
    try:
        cmd_d = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", video_path]
        d = float(subprocess.run(cmd_d, capture_output=True, text=True).stdout.strip())
    except: pass
    return w, d

def has_audio_stream(video_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "default=nw=1:nk=1", video_path]
        res = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
        return len(res) > 0
    except:
        return False

class SubWord:
    def __init__(self, word, start, end):
        self.word = word
        self.start = start
        self.end = end

STYLE_PRESETS = {
    "🔥 TikTok (Динамичный POP)": {"pri": "#FFFFFF", "act": "#FFD500", "out": "#000000", "pop": 115, "border": 8, "shadow": 0, "blur": 0, "fade": 0},
    "✨ Неоновое Свечение (Glow)": {"pri": "#FFFFFF", "act": "#00FFFF", "out": "#FF00FF", "pop": 105, "border": 5, "shadow": 0, "blur": 8, "fade": 0},
    "☁️ Плавный Chill (Фейд)": {"pri": "#F0F0F0", "act": "#FFFFFF", "out": "#000000", "pop": 100, "border": 3, "shadow": 3, "blur": 1, "fade": 300},
    "🎙 57 Mobb (Стиль подкаста)": {"pri": "#FFFFFF", "act": "#FF0033", "out": "#111111", "pop": 105, "border": 4, "shadow": 4, "blur": 0, "fade": 100},
    "☀️ SUMMER TIME (Летний вайб)": {"pri": "#FFFFFF", "act": "#00FFAA", "out": "#FF007F", "pop": 120, "border": 6, "shadow": 0, "blur": 4, "fade": 150},
    "🛠 Свой стиль (Ручной)": None
}

# Функция обрезки в вертикальный формат 9:16 (MoviePy Crop)
def apply_vertical_crop(file_path):
    try:
        clip = VideoFileClip(file_path)
        target_width = int(clip.h * 9 / 16)
        if target_width < clip.w:
            cropped = clip.fx(vfx.crop, x_center=clip.w / 2, y_center=clip.h / 2, width=target_width, height=clip.h)
            out_cropped = file_path.replace(".mp4", "_cropped.mp4")
            cropped.write_videofile(out_cropped, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            clip.close()
            cropped.close()
            os.replace(out_cropped, file_path)
        else:
            clip.close()
    except Exception as e:
        st.warning(f"Не удалось применить авто-кроп 9:16: {e}")

# --- AI-ФУНКЦИЯ ДЛЯ АНАЛИЗА ТРАНСКРИПТА (ZVENOAI С ВЫБОРОМ МОДЕЛИ) ---
def analyze_transcript_with_gemini(transcript_text, num_clips, min_duration, max_duration, theme="", model="openai/gpt-4o-mini"):
    client = OpenAI(
        api_key="sk-90W-jDtT3mk6J0BwXRImf_JulZmymomOmtq-AsLsO64",
        base_url="https://api.zveno.ai/v1"
    )
    
    all_clips = []
    lines = transcript_text.split('\n')
    chunks = []
    current_chunk = ""
    for line in lines:
        if len(current_chunk) + len(line) > 5000:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk)
        
    clips_per_chunk = max(1, num_clips // max(1, len(chunks))) + 1
    theme_instruction = f"Тематика для поиска: {theme.strip()}. Найди моменты, которые максимально подходят под эту тему.\n" if theme.strip() else ""
    
    for i, chunk in enumerate(chunks):
        prompt = (
            f"{theme_instruction}"
            f"Найди {clips_per_chunk} лучших вирусных моментов для короткого видео.\n"
            f"ВАЖНО: Разница между end и start (end - start) должна быть СТРОГО от {min_duration} до {max_duration} секунд! "
            f"Моменты короче {min_duration} сек или длиннее {max_duration} сек будут отклонены.\n"
            f"Верни ТОЛЬКО JSON объект с ключом 'clips', внутри которого массив словарей:\n"
            f"{{\"clips\": [{{\"start\": 10.5, \"end\": 55.0, \"title\": \"Название\"}}]}}\n"
            f"Используй точные таймкоды из скобок в тексте. Текст:\n{chunk}"
        )
        
        try:
            with st.spinner(f"Анализ части {i+1} из {len(chunks)} через модель '{model}'..."):
                create_params = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a professional video editor and data extractor. Output strictly valid JSON."},
                        {"role": "user", "content": prompt}
                    ]
                }
                try:
                    create_params["response_format"] = {"type": "json_object"}
                    response = client.chat.completions.create(**create_params)
                except Exception:
                    create_params.pop("response_format", None)
                    response = client.chat.completions.create(**create_params)
                
                text_response = response.choices[0].message.content
                st.info(f"📡 Ответ: {text_response[:150]}...")
                
                clean_json = text_response.replace('```json', '').replace('```', '').strip()
                parsed = json.loads(clean_json)
                
                if isinstance(parsed, dict) and "clips" in parsed:
                    all_clips.extend(parsed["clips"])
                elif isinstance(parsed, list):
                    all_clips.extend(parsed)
                    
        except Exception as e:
            st.error(f"❌ Ошибка API на части {i+1}: {e}")
            continue
            
    if not all_clips:
        st.error("❌ Внимание: Не удалось извлечь ни одного клипа. Проверьте баланс, модель и API-ключ.")
        
    return all_clips[:num_clips]

# --- 3. ПОИСК ФАЙЛОВ ---
banners = [f for f in os.listdir("assets/banners") if f.endswith(('.png', '.jpg', '.mp4', '.mov', '.gif', '.webm'))]
musics = [f for f in os.listdir("assets/music") if f.endswith(('.mp3', '.wav'))]
fonts = [f for f in os.listdir("assets/fonts") if f.endswith(('.ttf', '.otf'))]

# --- 4. СИММЕТРИЧНЫЕ ВКЛАДКИ С НАСТРОЙКАМИ ---
tab_source, tab_subs, tab_banner, tab_audio, tab_ai = st.tabs([
    "🎥 Исходник", 
    "💬 Субтитры", 
    "🖼️ Баннер", 
    "🎵 Звук", 
    "✂️ AI Нарезка"
])

with tab_source:
    st.markdown("#### Параметры холста и формата")
    c_fmt1, c_fmt2 = st.columns([1, 1], gap="medium")
    with c_fmt1:
        video_format = st.selectbox(
            "Формат видео:",
            ["Вертикальный TikTok (9:16)", "Горизонтальный (16:9)"],
            index=0
        )
    with c_fmt2:
        st.info("ℹ️ При выборе 9:16 горизонтальное видео кадрируется по центру (Smart Center Crop).")
    
    st.markdown("---")
    st.markdown("##### Ручные таймкоды (при выключенной AI-нарезке)")
    c_s1, c_s2 = st.columns(2, gap="medium")
    with c_s1:
        start_time = st.number_input("Начало (сек):", min_value=0.0, value=0.0, step=0.5)
    with c_s2:
        end_time = st.number_input("Конец (сек, 0 = до конца)", min_value=0.0, value=0.0, step=0.5)

with tab_subs:
    st.markdown("#### Настройка нейро-субтитров")
    enable_subs = st.checkbox("Включить генерацию субтитров", value=True)
    if enable_subs:
        cs1, cs2, cs3 = st.columns(3, gap="medium")
        with cs1:
            max_words = st.slider("Слов на экране (рубим текст):", 1, 8, 3)
            progressive_reveal = st.checkbox("Караоке (скрывать будущие слова)", value=True)
        with cs2:
            sub_font = st.selectbox("Шрифт текста:", fonts) if fonts else None
            font_size = st.slider("Размер шрифта:", 40, 150, 95)
        with cs3:
            sub_y_margin = st.slider("Отступ от низа (px):", 100, 1000, 450, step=10)
            selected_preset = st.selectbox("🎨 Пресет стиля:", list(STYLE_PRESETS.keys()))

        if STYLE_PRESETS[selected_preset] is None:
            st.markdown("##### Пользовательский стиль")
            col1, col2, col3 = st.columns(3, gap="medium")
            with col1:
                pop_scale = st.slider("Увеличение слова (%):", 100, 150, 115)
                sub_color = st.color_picker("Основной цвет:", "#FFFFFF")
            with col2:
                active_color = st.color_picker("Активное слово:", "#FFD500")
                outline_color = st.color_picker("Цвет обводки:", "#000000")
                border_size = st.slider("Толщина обводки:", 0, 15, 8)
            with col3:
                shadow_size = st.slider("Размер тени:", 0, 15, 0)
                blur_amt = st.slider("Свечение (Blur):", 0, 20, 0)
                fade_ms = st.slider("Плавность (Fade, ms):", 0, 1000, 0)
        else:
            p = STYLE_PRESETS[selected_preset]
            pop_scale = p["pop"]
            sub_color = p["pri"]
            active_color = p["act"]
            outline_color = p["out"]
            border_size = p["border"]
            shadow_size = p["shadow"]
            blur_amt = p["blur"]
            fade_ms = p["fade"]
    else:
        max_words, progressive_reveal, sub_font, font_size, sub_y_margin = 3, True, None, 95, 450
        pop_scale, sub_color, active_color, outline_color = 115, "#FFFFFF", "#FFD500", "#000000"
        border_size, shadow_size, blur_amt, fade_ms = 8, 0, 0, 0

with tab_banner:
    st.markdown("#### Рекламная врезка и баннер")
    selected_banner = st.selectbox("Выбери файл баннера:", ["Без баннера"] + banners) if banners else None
    if selected_banner == "Без баннера": 
        selected_banner = None

    if selected_banner:
        cb1, cb2 = st.columns(2, gap="medium")
        with cb1:
            banner_behavior = st.radio("Поведение врезки:", ["Врезка (Пауза видео)", "Просто поверх видео"], horizontal=True)
            banner_size_mode = st.radio("Размер на экране:", ["25% (Оптимально)", "50%", "Вручную"], horizontal=True)
            if banner_size_mode == "Вручную":
                scale_percent = st.slider("Ширина (% от экрана):", 10, 100, 40)
            else:
                scale_percent = int(banner_size_mode.split("%")[0])
            banner_start = st.number_input("Секунда появления:", min_value=0.0, value=2.0, step=0.5)
        with cb2:
            chroma_key = st.radio("Хромакей подложки:", ("Прозрачный", "Зеленый", "Синий"), horizontal=True)
            pos_x_select = st.selectbox("Позиция X:", ["По центру", "Слева", "Справа"])
            pos_y = st.slider("Отступ сверху Y (px):", 0, 1920, 200, step=10)
    else:
        banner_behavior = "Врезка (Пауза видео)"
        scale_percent = 40
        banner_start = 2.0
        chroma_key = "Прозрачный"
        pos_x_select = "По центру"
        pos_y = 200

with tab_audio:
    st.markdown("#### Фоновое аудио")
    ca1, ca2 = st.columns(2, gap="medium")
    with ca1:
        music_options = ["Без музыки"] + musics if musics else []
        selected_music = st.selectbox("Выберите трек из каталога:", music_options) if music_options else None
        if selected_music == "Без музыки": 
            selected_music = None
    with ca2:
        if selected_music:
            music_vol = st.slider("Громкость фоновой музыки:", 0.0, 1.0, 0.10, step=0.01)
        else:
            music_vol = 0.10

with tab_ai:
    st.markdown("#### ✂️ Автоматический AI-конвейер клипов")
    ai_mode_enabled = st.checkbox("Включить режим AI-Нарезки (ZvenoAI Engine)", value=False)

    col_m1, col_m2 = st.columns([1, 1], gap="medium")
    with col_m1:
        model_options = [
            "openai/gpt-4o-mini",
            "stealth/space-bunny-alpha",
            "qwen/qwen-3.8-27b-free",
            "nvidia/nemotron-3.5-lightning-free",
            "liquidai/lfm-2.5-2.6b-free",
            "cohere/north-mini-code-free"
        ]
        chosen_preset_model = st.selectbox(
            "Выбор нейросети:",
            model_options,
            index=0,
            disabled=not ai_mode_enabled
        )
    with col_m2:
        custom_model_enabled = st.checkbox("Свой вариант модели", value=False, disabled=not ai_mode_enabled)
        if custom_model_enabled:
            custom_model_input = st.text_input(
                "Идентификатор модели:",
                placeholder="например: meta-llama/llama-3-8b-instruct:free",
                disabled=not ai_mode_enabled
            )
        else:
            custom_model_input = ""

    if custom_model_enabled and custom_model_input.strip():
        selected_model = custom_model_input.strip()
    else:
        selected_model = chosen_preset_model

    theme_keywords = st.text_input(
        "Тематика или ключевые слова (необязательно):",
        placeholder="например: смешные моменты, инсайты, скандалы, бизнес-секреты"
    )

    c_ai1, c_ai2 = st.columns(2, gap="medium")
    with c_ai1:
        num_clips = st.slider("Количество клипов:", min_value=1, max_value=10, value=3, disabled=not ai_mode_enabled)
    with c_ai2:
        min_clip_duration, max_clip_duration = st.slider(
            "Диапазон длительности клипа (сек):",
            min_value=15,
            max_value=120,
            value=(40, 60),
            disabled=not ai_mode_enabled
        )

# --- 5. ЛОГИКА РЕНДЕРА (FFMPEG) ---
def process_video(input_path, start_sec, end_sec, is_preview=False):
    ass_path = "temp/subs.ass"
    if os.path.exists(ass_path):
        os.remove(ass_path)

    trimmed_path = os.path.join("temp", "trimmed.mp4")
    trim_cmd = ["ffmpeg", "-y", "-i", input_path, "-ss", str(start_sec)]
    if is_preview:
        trim_cmd.extend(["-t", "5"])
    elif end_sec > start_sec:
        trim_cmd.extend(["-to", str(end_sec)])
    
    preset = "ultrafast" if is_preview else "fast"
    trim_cmd.extend(["-c:v", "libx264", "-preset", preset, "-c:a", "aac", trimmed_path])
    subprocess.run(trim_cmd, capture_output=True)

    main_w, main_dur = get_video_info(trimmed_path)
    
    D = 3.0 
    banner_has_audio = False
    if selected_banner:
        b_path = os.path.join("assets/banners", selected_banner)
        _, D = get_video_info(b_path)
        banner_has_audio = has_audio_stream(b_path)
        is_static_img = b_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
        if is_static_img: D = 3.0 

    T = min(float(banner_start), max(main_dur - 0.5, 0.0)) if selected_banner else 0.0
    is_insert_mode = selected_banner and banner_behavior == "Врезка (Пауза видео)"

    has_subs = False
    if enable_subs:
        st.info("🤖 Нейросеть слушает аудио...")
        model = load_whisper_model()
        all_words = []
        try:
            segments, info = model.transcribe(trimmed_path, language="ru", word_timestamps=True, vad_filter=True)
            for segment in segments:
                for w in segment.words:
                    if w.word.strip():
                        all_words.append(SubWord(w.word.strip(), w.start, w.end))
        except Exception:
            segments, info = model.transcribe(trimmed_path, language="ru", word_timestamps=True)
            for segment in segments:
                for w in segment.words:
                    if w.word.strip():
                        all_words.append(SubWord(w.word.strip(), w.start, w.end))
        
        if is_insert_mode:
            for w in all_words:
                if w.start >= T:
                    w.start += D
                    w.end += D
                elif w.start < T and w.end > T:
                    w.end += D

        font_name = os.path.splitext(sub_font)[0] if sub_font else "Arial"
        primary_c = hex_to_ass_color(sub_color)
        active_c = hex_to_ass_color(active_color)
        outline_c = hex_to_ass_color(outline_color)
        
        ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_c},&H000000FF,{outline_c},&H00000000,1,0,0,0,100,100,0,0,1,{border_size},{shadow_size},2,20,20,{sub_y_margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"""

        for i in range(len(all_words) - 1):
            if all_words[i].end > all_words[i+1].start:
                all_words[i].end = all_words[i+1].start
                if all_words[i].start >= all_words[i].end:
                    all_words[i].start = all_words[i].end - 0.05

        chunks = [all_words[i:i + max_words] for i in range(0, len(all_words), max_words)]
        y_pos = 1920 - sub_y_margin
        
        for c_idx, chunk in enumerate(chunks):
            for i, active_word in enumerate(chunk):
                start_t = active_word.start
                if i < len(chunk) - 1:
                    end_t = chunk[i+1].start
                else:
                    end_t = active_word.end
                    if c_idx < len(chunks) - 1:
                        next_chunk_start = chunks[c_idx+1][0].start
                        if end_t > next_chunk_start:
                            end_t = next_chunk_start
                if start_t >= end_t: end_t = start_t + 0.05
                    
                start_str = format_time_ass(start_t)
                end_str = format_time_ass(end_t)
                
                t_fade_in = fade_ms if i == 0 else 0
                t_fade_out = fade_ms if i == len(chunk) - 1 else 0
                
                line_prefix = f"{{\\pos(540,{y_pos})\\an5"
                if t_fade_in > 0 or t_fade_out > 0: line_prefix += f"\\fad({t_fade_in},{t_fade_out})"
                if blur_amt > 0: line_prefix += f"\\blur{blur_amt}"
                line_prefix += "}"
                
                text_parts = []
                for j, w in enumerate(chunk):
                    if j < i:
                        text_parts.append(f"{{\\c{primary_c}}}{w.word}")
                    elif j == i:
                        if pop_scale > 100:
                            text_parts.append(f"{{\\c{active_c}\\fscx100\\fscy100\\t(0,100,\\fscx{pop_scale}\\fscy{pop_scale})}}{w.word}{{\\c{primary_c}\\fscx100\\fscy100}}")
                        else:
                            text_parts.append(f"{{\\c{active_c}}}{w.word}{{\\c{primary_c}}}")
                    else:
                        if progressive_reveal: text_parts.append(f"{{\\alpha&HFF&}}{w.word}{{\\alpha&H00&}}")
                        else: text_parts.append(f"{{\\c{primary_c}}}{w.word}")
                
                final_line = " ".join(text_parts)
                ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_prefix}{final_line}\n"
            
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        has_subs = True

    target_path = os.path.join("temp", "preview_final.mp4") if is_preview else os.path.join("output", "final_video.mp4")
    cmd = ["ffmpeg", "-y", "-i", trimmed_path]
    current_input_idx = 1
    
    banner_idx, music_idx = None, None
    if selected_banner:
        cmd.extend(["-i", b_path])
        banner_idx = current_input_idx
        current_input_idx += 1
        
    if selected_music:
        music_path = os.path.join("assets/music", selected_music)
        cmd.extend(["-i", music_path])
        music_idx = current_input_idx
        current_input_idx += 1

    vf = []
    
    if selected_music:
        vf.append(f"[{music_idx}:a]volume={music_vol},aresample=48000[bgm]")
        vf.append(f"[0:a]aresample=48000[main_a_resampled]")
        vf.append(f"[main_a_resampled][bgm]amix=inputs=2:duration=first:normalize=0[mixed_audio]")
    else:
        vf.append(f"[0:a]aresample=48000[mixed_audio]")

    if selected_banner:
        target_w = int(main_w * (scale_percent / 100))
        f_scale = f"[{banner_idx}:v]scale={target_w}:-1[scaled]"
        if chroma_key == "Зеленый": f_chroma = "[scaled]colorkey=0x00FF00:0.3:0.2[b_c]"
        elif chroma_key == "Синий": f_chroma = "[scaled]colorkey=0x0000FF:0.3:0.2[b_c]"
        else: f_chroma = "[scaled]format=rgba[b_c]"
        
        if pos_x_select == "По центру": pos_x = "(W-w)/2"
        elif pos_x_select == "Слева": pos_x = "30"
        else: pos_x = "(W-w-30)"

        if is_insert_mode:
            vf.append(f"[0:v]trim=start=0:end={T},setpts=PTS-STARTPTS,format=yuv420p[v1]")
            vf.append(f"[0:v]trim=start={T}:end={T+0.05},setpts=PTS-STARTPTS,loop=loop=-1:size=1,trim=duration={D},setpts=PTS-STARTPTS[v_freeze]")
            vf.append(f"[0:v]trim=start={T},setpts=PTS-STARTPTS,format=yuv420p[v3]")
            
            vf.append(f"[mixed_audio]asplit=2[ma1][ma2]")
            vf.append(f"[ma1]atrim=start=0:end={T},asetpts=PTS-STARTPTS[a1]")
            vf.append(f"[ma2]atrim=start={T},asetpts=PTS-STARTPTS[a3]")
            
            vf.append(f"{f_scale};{f_chroma}")
            vf.append(f"[v_freeze][b_c]overlay=x={pos_x}:y={pos_y}:shortest=1,format=yuv420p[v2]")
            
            if banner_has_audio and not is_static_img:
                vf.append(f"[{banner_idx}:a]aresample=48000[a2]")
            else:
                vf.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={D}[a2]")
                
            vf.append("[v1][a1][v2][a2][v3][a3]concat=n=3:v=1:a=1[vout_base][aout_base]")
        else:
            vf.append(f"{f_scale};{f_chroma}")
            enable_expr = f"between(t,{T},{T+D})"
            vf.append(f"[0:v][b_c]overlay=x={pos_x}:y={pos_y}:enable='{enable_expr}':eof_action=pass[vout_base]")
            
            if banner_has_audio and not is_static_img:
                vf.append(f"[{banner_idx}:a]aresample=48000,adelay={int(T*1000)}|{int(T*1000)}[b_a_delayed]")
                vf.append(f"[mixed_audio][b_a_delayed]amix=inputs=2:duration=first:normalize=0[aout_base]")
            else:
                vf.append(f"[mixed_audio]anull[aout_base]")
    else:
        vf.append("[0:v]null[vout_base]")
        vf.append("[mixed_audio]anull[aout_base]")

    if has_subs:
        ass_escaped = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:").replace(" ", "\\ ")
        vf.append(f"[vout_base]subtitles=filename={ass_escaped}[vout_final]")
    else:
        vf.append("[vout_base]null[vout_final]")

    filter_complex = ";".join(vf)
    cmd.extend(["-filter_complex", filter_complex])
    cmd.extend(["-map", "[vout_final]", "-map", "[aout_base]"])
    cmd.extend(["-c:v", "libx264", "-preset", preset, "-c:a", "aac", target_path])
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        st.error(f"⚠️ Ошибка FFmpeg:\n\n{res.stderr}")
        return None
    return target_path

# --- 6. СИММЕТРИЧНАЯ ЗОНА ЗАГРУЗКИ ---
st.markdown("---")
st.markdown("### 📥 Источник видеоматериала")

c_src1, c_src2 = st.columns([1, 2], gap="large")

with c_src1:
    source_type = st.radio(
        "Способ импорта:",
        ["✈️ Из Telegram бота", "Локальный файл"],
        horizontal=False
    )

input_path = None

with c_src2:
    if source_type == "Локальный файл":
        uploaded_video = st.file_uploader("Перетащите файл MP4 / MOV сюда:", type=["mp4", "mov"])
        if uploaded_video:
            local_target = os.path.join("temp", "input_video.mp4")
            with open(local_target, "wb") as f:
                f.write(uploaded_video.read())
            input_path = local_target
    else:
        # Логика для "✈️ Из Telegram бота"
        tasks_file = "telegram_tasks.json"
        
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, "r", encoding="utf-8") as f:
                    telegram_tasks = json.load(f)
            except Exception:
                telegram_tasks = []

            if isinstance(telegram_tasks, list) and len(telegram_tasks) > 0:
                # Формируем список строк в формате "@username - url"
                options = [
                    f"@{task.get('username', 'user')} - {task.get('url', 'Без ссылки')}"
                    for task in telegram_tasks
                ]
                
                selected_idx = st.selectbox(
                    "Выберите загруженное видео из очереди бота:",
                    range(len(options)),
                    format_func=lambda i: options[i]
                )
                
                chosen_task = telegram_tasks[selected_idx]
                target_local_path = chosen_task.get("local_path", "")
                
                if target_local_path and os.path.exists(target_local_path):
                    input_path = target_local_path
                    st.success(f"✅ Файл из Telegram готов: {os.path.basename(target_local_path)}")
                else:
                    st.warning("⚠️ Файл видео не найден по указанному пути на диске.")

                # Кнопка очистки истории
                if st.button("🗑 Очистить историю Telegram", use_container_width=True):
                    try:
                        os.remove(tasks_file)
                    except Exception:
                        pass
                    st.rerun()
            else:
                st.info("База пуста. Отправь ссылку Telegram-боту, чтобы видео появилось здесь.")
        else:
            st.info("База пуста. Отправь ссылку Telegram-боту, чтобы видео появилось здесь.")

# --- 7. ПЛЕЕР И ПАНЕЛЬ УПРАВЛЕНИЯ ---
if input_path and os.path.exists(input_path):
    st.markdown("---")
    col_player, col_actions = st.columns([1.1, 0.9], gap="large")
    with col_player:
        st.markdown("#### 📺 Монитор предпросмотра")
        st.video(input_path)

    with col_actions:
        st.markdown("#### ⚡ Сборка и экспорт")
        st.write("Запустите быстрый 5-секундный тест или соберите итоговый пакет:")
        
        c_btn1, c_btn2 = st.columns(2, gap="medium")
        with c_btn1:
            btn_prev = st.button("👁 5-сек Превью", use_container_width=True)
        with c_btn2:
            btn_render = st.button("🚀 ФИНАЛЬНЫЙ РЕНДЕР", use_container_width=True)

        if btn_prev:
            with st.spinner("Сборка превью..."):
                res_path = process_video(input_path, start_time, end_time, is_preview=True)
                if res_path and os.path.exists(res_path):
                    if video_format == "Вертикальный TikTok (9:16)":
                        apply_vertical_crop(res_path)
                    st.success("Превью готово!")
                    st.video(res_path)

        if btn_render:
            # СЦЕНАРИЙ 1: AI-НАРЕЗКА ВКЛЮЧЕНА (ZVENOAI + ВЫБРАННАЯ МОДЕЛЬ + WHISPER)
            if ai_mode_enabled:
                with st.spinner("🤖 Whisper анализирует всё видео целиком..."):
                    model = load_whisper_model()
                    try:
                        segments, _ = model.transcribe(input_path, language="ru", word_timestamps=True, vad_filter=True)
                    except Exception:
                        segments, _ = model.transcribe(input_path, language="ru", word_timestamps=True)
                    
                    transcript_text = "\n".join([f"[{segment.start:.1f} - {segment.end:.1f}] {segment.text}" for segment in segments])

                with st.spinner(f"🧠 ИИ ({selected_model}) ищет вирусные моменты с учетом темы и диапазона секунд..."):
                    clips = analyze_transcript_with_gemini(
                        transcript_text=transcript_text,
                        num_clips=num_clips,
                        min_duration=min_clip_duration,
                        max_duration=max_clip_duration,
                        theme=theme_keywords,
                        model=selected_model
                    )

                if clips:
                    st.success(f"🎯 Найдено {len(clips)} фрагментов! Запускаем конвейер рендеринга...")
                    progress_bar = st.progress(0)
                    
                    for i, clip in enumerate(clips):
                        st.info(f"🔍 Дебаг ответа (клип {i+1}): {clip}")
                        
                        start_raw = clip.get("start", clip.get("Start", clip.get("start_time", clip.get("начало", 0.0))))
                        end_raw = clip.get("end", clip.get("End", clip.get("end_time", clip.get("конец", 0.0))))
                        
                        try:
                            start_clean = ''.join(c for c in str(start_raw) if c.isdigit() or c == '.')
                            end_clean = ''.join(c for c in str(end_raw) if c.isdigit() or c == '.')
                            
                            start_time = float(start_clean) if start_clean else 0.0
                            end_time = float(end_clean) if end_clean else 0.0
                        except:
                            start_time = 0.0
                            end_time = 0.0
                            
                        # Предохранитель от битых фрагментов
                        if start_time >= end_time or end_time == 0.0:
                            st.warning(f"Пропущен битый фрагмент. Ищу следующий...")
                            continue

                        c_title = clip.get("title", clip.get("Title", clip.get("название", f"Клип {i+1}")))
                        st.markdown(f"**🎬 Рендерим Клип {i+1}:** {c_title} ({start_time:.1f}с — {end_time:.1f}с)")
                        
                        with st.spinner(f"Обработка клипа #{i+1}..."):
                            res_path = process_video(input_path, start_sec=start_time, end_sec=end_time, is_preview=False)
                            
                            if res_path and os.path.exists(res_path):
                                if video_format == "Вертикальный TikTok (9:16)":
                                    apply_vertical_crop(res_path)
                                    
                                clip_filename = f"tiktok_ready_clip_{i+1}.mp4"
                                clip_save_path = os.path.join("output", clip_filename)
                                shutil.copy(res_path, clip_save_path)
                                
                                st.video(clip_save_path)
                                with open(clip_save_path, "rb") as file:
                                    st.download_button(
                                        f"📥 Скачать {clip_filename} ({c_title})",
                                        data=file,
                                        file_name=clip_filename,
                                        mime="video/mp4",
                                        key=f"dl_btn_{i+1}",
                                        use_container_width=True
                                    )
                        progress_bar.progress((i + 1) / len(clips))
                    st.balloons()
                else:
                    st.warning("Нейросеть не смогла выделить фрагменты. Попробуйте сменить модель или скорректировать запрос.")
            
            # СЦЕНАРИЙ 2: КЛАССИЧЕСКИЙ РЕЖИМ (ПО РУЧНЫМ ТАЙМКОДАМ)
            else:
                with st.spinner("Рендер видео..."):
                    res_path = process_video(input_path, start_time, end_time, is_preview=False)
                    if res_path and os.path.exists(res_path):
                        if video_format == "Вертикальный TikTok (9:16)":
                            apply_vertical_crop(res_path)
                            
                        st.success("✅ Готово!")
                        st.video(res_path)
                        with open(res_path, "rb") as file:
                            st.download_button(
                                "📥 Скачать результат",
                                data=file,
                                file_name="tiktok_ready_pro.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )

# --- 8. ПОДПИСЬ АВТОРА ---
st.markdown(
    """<div style="text-align: center; margin-top: 4.5rem; margin-bottom: 1.5rem; font-size: 0.78rem; color: #8E8E93; letter-spacing: 0.22em; text-transform: uppercase;">made by SLSSHR ❤️</div>""",
    unsafe_allow_html=True
)