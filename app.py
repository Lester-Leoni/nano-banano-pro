import streamlit as st
import streamlit.components.v1 as components
import re
import datetime
import os
from prompt_manager import PromptManager
from st_copy_to_clipboard import st_copy_to_clipboard
from deep_translator import GoogleTranslator

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Nano Banano Pro",
    page_icon="🍌",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. JS CLEANER (remove annoying titles from select tooltips) ---
components.html(
    """
    <script>
    function removeTitles() {
        const elems = window.parent.document.querySelectorAll('div[data-baseweb="select"] *');
        elems.forEach(el => {
            if (el.hasAttribute('title')) el.removeAttribute('title');
        });
    }
    const observer = new MutationObserver(() => removeTitles());
    observer.observe(window.parent.document.body, { childList: true, subtree: true });
    setTimeout(removeTitles, 800);
    </script>
    """,
    height=0,
)

# --- 3. NEGATIVE PROMPT LIBRARY ---
# NOTE:
# - NanoBanano Pro usually uses single-line input, so we append NEG with "--no".
# - For advanced users we still show Positive and Negative separately (WebUI-style).
NEG_GROUPS = {
    1: {  # Photorealism & People
        "Mini": {
            "en": "waxy/plastic skin, beauty retouch, identity drift, extra fingers, watermark, text",
            "ru": "восковая/пластиковая кожа, бьюти-ретушь, потеря сходства, лишние пальцы, водяной знак, текст",
        },
        "Plus": {
            "en": "waxy/plastic skin, over-smoothing, beauty retouch, face reshaping, identity drift, extra teeth, deformed hands, extra fingers, watermark, text",
            "ru": "восковая/пластиковая кожа, пересглаживание, бьюти-ретушь, изменение лица, потеря сходства, лишние зубы, деформированные руки, лишние пальцы, водяной знак, текст",
        },
        "Full": {
            "en": "waxy/plastic skin, over-smoothing, beauty retouch, face reshaping, identity drift, uncanny face, extra teeth, deformed hands, extra limbs/fingers, AI glow, oversharpen halos, banding, watermark, logo, text",
            "ru": "восковая/пластиковая кожа, пересглаживание, бьюти-ретушь, изменение лица, потеря сходства, жуткое лицо, лишние зубы, деформированные руки, лишние конечности/пальцы, AI-свечение, ореолы перешарпа, бэндинг, водяной знак, логотип, текст",
        },
    },
    2: {  # Scene Editing
        "Mini": {
            "en": "seams, halos, ghosting, wrong shadow, wrong scale, watermark, text",
            "ru": "швы, ореолы, двоение, неверные тени, неверный масштаб, водяной знак, текст",
        },
        "Plus": {
            "en": "seams, halos, cutout edges, ghosting, smear, warped lines, floating object, wrong shadow, wrong scale, mismatch grain, watermark, text",
            "ru": "швы, ореолы, обрезанные края, двоение, размазывание, кривые линии, левитация, неверные тени, неверный масштаб, разное зерно, водяной знак, текст",
        },
        "Full": {
            "en": "seams, halos, cutout edges, ghosting, smearing, warped perspective/lines, floating objects, wrong scale, wrong shadows, inconsistent lighting, mismatch grain/noise, color mismatch, missing reflections, watermark, logo, text",
            "ru": "швы, ореолы, обрезанные края, двоение, размазывание, искаженная перспектива/линии, левитирующие объекты, неверный масштаб, неверные тени, несогласованный свет, разное зерно/шум, несовпадение цвета, ошибки отражений, водяной знак, логотип, текст",
        },
    },
    3: {  # Commercial Design
        "Mini": {
            "en": "misspelling, broken glyphs, lorem ipsum, tiny text, random logo, watermark",
            "ru": "опечатки, битые символы, lorem ipsum, мелкий текст, случайный логотип, водяной знак",
        },
        "Plus": {
            "en": "misspelling, broken glyphs, lorem ipsum, tiny unreadable text, clutter, misaligned layout, low-contrast text, pixelation, random logo, watermark",
            "ru": "опечатки, битые символы, lorem ipsum, нечитаемый текст, мусор, кривая верстка, низкий контраст, пикселизация, случайный логотип, водяной знак",
        },
        "Full": {
            "en": "misspelling, broken glyphs, lorem ipsum, tiny unreadable text, clutter, misaligned layout, low contrast, pixelation, jagged edges, wrong aspect ratio, random brand/logo, extra QR codes, illegible icons, watermark",
            "ru": "опечатки, битые символы, lorem ipsum, мелкий нечитаемый текст, мусор, кривая верстка, низкий контраст, пикселизация, рваные края, неверные пропорции, случайный бренд/логотип, лишние QR-коды, неразборчивые иконки, водяной знак",
        },
    },
    4: {  # Art & Illustration
        "Mini": {
            "en": "extra objects, anatomy warp, style drift, seams, vignette, watermark, text",
            "ru": "лишние объекты, искажение анатомии, плавающий стиль, швы, виньетка, водяной знак, текст",
        },
        "Plus": {
            "en": "extra objects, anatomy warp, proportion change, perspective distortion, messy linework, style drift, pattern seams, vignette, unreadable text, watermark",
            "ru": "лишние объекты, искажение анатомии, нарушение пропорций, искажение перспективы, неряшливые линии, плавающий стиль, швы, виньетка, нечитаемый текст, водяной знак",
        },
        "Full": {
            "en": "extra objects, anatomy warp, proportion changes, perspective distortion, messy linework, inconsistent style, seams in pattern, vignette, unwanted shading, unreadable text/gibberish, watermark, logo",
            "ru": "лишние объекты, искажение анатомии, нарушение пропорций, искажение перспективы, неряшливые линии, непоследовательный стиль, швы в паттерне, виньетка, лишние тени, нечитаемый текст/бессмыслица, водяной знак, логотип",
        },
    },
    5: {  # Architecture
        "Mini": {
            "en": "keystone distortion, warped verticals, messy geometry, unrealistic scale, watermark, text",
            "ru": "трапеция (keystone), кривые вертикали, грязная геометрия, нереальный масштаб, водяной знак, текст",
        },
        "Plus": {
            "en": "keystone distortion, warped verticals, bent walls, unrealistic scale, messy geometry, low-res textures, blown highlights, muddy shadows, clutter, watermark",
            "ru": "keystone, кривые вертикали/стены, нереальный масштаб, грязная геометрия, низкое разрешение текстур, пересветы, грязные тени, мусор, водяной знак",
        },
        "Full": {
            "en": "keystone distortion, bent walls, warped verticals, unrealistic scale, messy geometry, low-res textures, oversharpen halos, blown highlights, muddy shadows, clutter, people (if not requested), watermark, logo, text",
            "ru": "keystone, кривые стены/вертикали, нереальный масштаб, грязная геометрия, низкое разрешение текстур, ореолы перешарпа, пересветы, грязные тени, мусор, лишние люди (если не просили), водяной знак, логотип, текст",
        },
    },
    6: {  # VFX / Cinema (base)
        "Mini": {
            "en": "overdone flares, heavy aberration, excessive bloom, noisy artifacts, watermark, text",
            "ru": "перебор бликов, сильная аберрация, избыточный bloom, шумные артефакты, водяной знак, текст",
        },
        "Plus": {
            "en": "excessive bloom, heavy chromatic aberration, overdone flares, crushed blacks, blown highlights, noisy artifacts, oversharpen halos, watermark, text",
            "ru": "избыточный bloom, сильная аберрация, перебор бликов, проваленные черные, пересветы, шумные артефакты, ореолы перешарпа, водяной знак, текст",
        },
        "Full": {
            "en": "overdone bloom, heavy aberration, excessive flares, crushed blacks, blown highlights, noisy artifacts, oversharpen halos, unreadable text, tiny clutter text, watermark, logo",
            "ru": "перебор bloom, сильная аберрация, избыточные блики, проваленные черные, пересветы, шумные артефакты, ореолы перешарпа, нечитаемый текст, мелкий мусорный текст, водяной знак, логотип",
        },
    },
}

# Per-prompt NEG add-ons (to fix mixed groups like Group 6 and special tasks like Logo)
NEG_ADDONS = {
    "logo_creative": {
        "en": "photorealistic, 3d render, mockup, gradients, textures, shadows, realistic lighting",
        "ru": "фотореализм, 3d-рендер, мокап, градиенты, текстуры, тени, реалистичный свет",
    },
    "technical_blueprint": {
        "en": "shading, gradients, perspective view, sketchy lines, hand-drawn look",
        "ru": "шейдинг, градиенты, перспектива, скетчевые линии, рисунок от руки",
    },
    "macro_extreme": {
        "en": "cartoon, illustration, painterly style, fake CG look",
        "ru": "мультяшность, иллюстрация, живописная стилизация, фейковый CG-вид",
    },
}

ID_TO_GROUP = {
    "upscale_restore": 1, "studio_portrait": 1, "background_change": 1, "face_swap": 1, "expression_change": 1, "cloth_swap": 1,
    "object_removal": 2, "object_addition": 2, "scene_relighting": 2, "scene_composite": 2,
    "product_card": 3, "mockup_generation": 3, "knolling_photography": 3, "logo_creative": 3, "logo_stylization": 3, "ui_design": 3, "text_design": 3,
    "image_restyling": 4, "sketch_to_photo": 4, "character_sheet": 4, "sticker_pack": 4, "comic_page": 4, "seamless_pattern": 4,
    "interior_design": 5, "architecture_exterior": 5, "isometric_room": 5,
    "youtube_thumbnail": 6, "cinematic_atmosphere": 6, "technical_blueprint": 6, "macro_extreme": 6
}

# --- 4. HISTORY ---
if "history" not in st.session_state:
    st.session_state["history"] = []

def save_to_history(task, prompt_en, prompt_ru):
    timestamp = datetime.datetime.now().strftime("%H:%M")
    st.session_state["history"].insert(0, {
        "task": task,
        "en": prompt_en,
        "ru": prompt_ru,
        "time": timestamp,
        "id": len(st.session_state["history"]) + 1
    })
    if len(st.session_state["history"]) > 50:
        st.session_state["history"].pop()

# --- 5. CSS (VISUAL FIXES) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

header[data-testid="stHeader"] { background: transparent !important; border-bottom: none !important; box-shadow: none !important; }
[data-testid="stDecoration"] { display: none !important; }
button[data-testid="stSidebarCollapsedControl"] { color: #FFD700 !important; border: none !important; background: transparent !important; }
button[data-testid="stSidebarCollapsedControl"]:hover { color: #FFC300 !important; background: transparent !important; }
div[data-testid="stToolbar"] { right: 2rem; top: 0.5rem; }
footer { display: none !important; }
.main .block-container { padding-top: 3rem !important; }

[data-testid="stAppViewContainer"] {
    background-color: #0e0e0e;
    background-image:
        radial-gradient(circle at 100% 0%, #332a00 0%, transparent 30%),
        radial-gradient(circle at 0% 100%, #1a1a1a 0%, transparent 40%);
    background-attachment: fixed;
}
[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #333 !important;
    background-image: linear-gradient(180deg, #1a1a1a 0%, #111111 100%) !important;
    padding-top: 1rem !important;
}
h1, h2, h3, p, label, .stMarkdown, .stCaption, [data-testid="stSidebar"] label, [data-testid="stExpander"] p {
    color: #e0e0e0 !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-baseweb="base-input"], div[data-baseweb="textarea"] { background-color: #1a1a1a !important; border: 1px solid #444 !important; }
div[data-baseweb="base-input"] input, div[data-baseweb="textarea"] textarea {
    color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; caret-color: #FFD700 !important; font-weight: 500 !important;
}
input::placeholder, textarea::placeholder {
    color: #888888 !important; -webkit-text-fill-color: #888888 !important; opacity: 1 !important; font-weight: 400 !important;
}
div[data-baseweb="base-input"]:focus-within, div[data-baseweb="select"] > div:focus-within, div[data-baseweb="textarea"]:focus-within {
    border-color: #FFD700 !important; box-shadow: 0 0 0 1px #FFD700 !important;
}

button[data-baseweb="tab"] { border-radius: 8px !important; margin-right: 6px !important; border: 1px solid transparent !important; transition: all 0.2s ease !important; padding: 0.5rem 1rem !important; }
button[data-baseweb="tab"] div p { color: #e0e0e0 !important; font-family: 'Inter', sans-serif !important; font-weight: 600; }
button[data-baseweb="tab"][aria-selected="true"] { background-color: #FFD700 !important; border: none !important; box-shadow: 0 2px 5px rgba(255, 215, 0, 0.2) !important; }
button[data-baseweb="tab"][aria-selected="true"] div p { color: #000000 !important; font-weight: 800 !important; }
div[data-baseweb="tab-highlight"] { display: none !important; }

div.stButton > button, div.stFormSubmitButton > button {
    background-color: #FFD700 !important; border: none !important; padding: 0.7rem 1rem !important;
    transition: all 0.3s ease !important; width: 100% !important; border-radius: 8px !important; color: #000000 !important;
}
div.stButton > button p, div.stFormSubmitButton > button p {
    color: #000000 !important; font-family: 'Inter', sans-serif !important; font-weight: 700 !important;
    text-transform: none !important; letter-spacing: normal !important; font-size: 18px !important;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    background-color: #FFC300 !important; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important; transform: translateY(-1px);
}

.main-banner {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-left: 6px solid #FFD700;
    padding: 25px;
    border-radius: 12px;
    margin-bottom: 25px;
    box-shadow: 0 0 25px rgba(255, 215, 0, 0.25);
}
.main-banner h1 { color: #FFD700 !important; }

[data-testid="stSidebar"] .stButton:first-child > button {
    width: 100%; background-color: #FFD700 !important; color: #000000 !important;
    font-weight: 800 !important; font-size: 1.2rem !important; border-radius: 12px !important; padding: 15px !important;
    border: none !important; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

# --- 6. BANNER & INSTRUCTIONS ---
st.markdown("""
<div class="main-banner">
    <h1>🍌 Nano Banano Pro</h1>
    <p>Твой карманный AI-креативщик</p>
</div>
""", unsafe_allow_html=True)

with st.expander(":material/info: Как пользоваться и что значат кнопки?"):
    st.markdown("""
### :material/bolt: Быстрый старт
1. **Выберите задачу** в меню слева.
2. **Заполните поля**.
3. **Выберите режим негатива**.
4. Нажмите **"🍌 Сгенерировать Промпт"**.

### :material/tune: Режимы негатива
- **Mini:** минимум запретов (если модель «теряется»).
- **Default (Mini+):** рекомендованный баланс.
- **Aggressive (Full):** если лезут артефакты/пластик/швы.

### :material/content_copy: Копирование
- **Всё в одном (для NanoBanano / ботов):** Positive + `--no` + Negative
- **Раздельно (для WebUI):** Positive и Negative отдельными кнопками
""")
st.write("---")

# --- 7. UI LABELS / EXAMPLES ---
VAR_MAP = {
    "image_1": "Исходное изображение / Ссылка",
    "image_2": "Второе изображение / Референс",
    "aspect_ratio": "Формат (Пропорции)",
    "background": "Фон / Окружение",
    "lighting": "Освещение",
    "style": "Стиль",
    "colors": "Цветовая гамма",

    "person": "Персонаж (Кто?)",
    "emotion": "Эмоция",
    "intensity": "Интенсивность эмоции",
    "fabric_material": "Материал ткани/одежды",

    "object": "Объект",
    "placement_details": "Где разместить объект?",
    "lighting_condition": "Условия освещения",
    "element_1": "Элемент 1 (Основа)",
    "element_2": "Элемент 2 (Вставка)",
    "scene_description": "Описание сцены",
    "lens_match_mode": "Сведение линз (feel/strict)",

    "product": "Название продукта",
    "text": "Текст (Точная цитата)",
    "features_list": "Список фич (через запятую)",
    "object_type": "Тип объекта (для мокапа)",
    "background_type": "Тип фона (поверхность)",
    "print_finish": "Покрытие (Matte/Glossy/Foil)",
    "brand": "Бренд",
    "imagery": "Образ / Символ",
    "materials": "Материалы",
    "screen_type": "Тип экрана",
    "industry": "Индустрия / Ниша",
    "platform": "Платформа (iOS/Android/Web)",
    "font_style": "Стиль шрифта",

    "level": "Сила стилизации",
    "medium": "Медиум",
    "description": "Описание персонажа",
    "labels_visibility": "Подписи ракурсов",
    "character": "Персонаж для стикеров",
    "count": "Количество стикеров",
    "list": "Список эмоций/поз",
    "scene": "Сцена комикса",
    "language": "Язык текста (en/ru)",
    "theme": "Тема паттерна",
    "show_preview": "Показать превью 2×2?",
    "room_type": "Тип комнаты",
    "room": "Комната (для среза)",
    "building_type": "Тип здания",
    "environment": "Окружение здания",
    "time": "Время суток / Погода",
    "lens": "Объектив (24mm/35mm...)",
    "background_color": "Цвет фона (изометрия)",
    "type": "Тип (Photo/Illustration)",
    "expression": "Выражение лица (превью)",
    "subject": "Главный объект",
    "focus_stacking": "Focus stacking (on/off)",
}

EXAMPLES_DB = {
    "image_1": {"ph": "Ссылка на изображение или имя файла...", "help": "Главное изображение для обработки."},
    "image_2": {"ph": "Ссылка на референс / донор...", "help": "Лицо/одежда/дизайн/референс."},
    "aspect_ratio": {"ph": "16:9, 9:16, 1:1, 4:5...", "help": "Пропорции итоговой картинки."},
    "background": {"ph": "Современный офис, улица Токио ночью...", "help": "Новое окружение."},
    "lighting": {"ph": "soft studio, window light, neon...", "help": "Свет в кадре."},
    "style": {"ph": "photoreal, cyberpunk, watercolor...", "help": "Общий стиль."},
    "colors": {"ph": "black & gold, pastel, neon...", "help": "Цветовая палитра."},
    "lens_match_mode": {"ph": "feel / strict", "help": "feel = визуально сводим, strict = строго фокусное."},
}

# Enumerated widgets (reduce user mistakes)
ENUM_OPTIONS = {
    "intensity": ["low", "medium", "high"],
    "level": ["light", "medium", "strong"],
    "labels_visibility": ["on", "off"],
    "show_preview": ["yes", "no"],
    "focus_stacking": ["on", "off"],
    "lens_match_mode": ["feel", "strict"],
    "language": ["en", "ru"],
    "platform": ["iOS", "Android", "Web"],
    "type": ["Photo", "Illustration"],
}

# --- 8. ENGINE ---
@st.cache_resource
def load_engine():
    if not os.path.exists("prompts.json"):
        return None
    return PromptManager("prompts.json")

manager = load_engine()
if not manager:
    st.error("❌ Файл `prompts.json` не найден. Положите его рядом с app.py")
    st.stop()

# --- 9. SIDEBAR ---
with st.sidebar:
    st.button("🍌 PRO MENU", key="promenu_btn", use_container_width=True)
    tab_menu, tab_history = st.tabs(["Меню", "История"])

all_prompts = manager.prompts
options = {data["title"]: pid for pid, data in all_prompts.items()}

with tab_menu:
    st.write(" ")
    selected_title = st.selectbox("Выберите задачу:", list(options.keys()))
    selected_id = options[selected_title]
    current_prompt_data = all_prompts[selected_id]
    with st.container(border=True):
        st.info(current_prompt_data["description"])

# --- 10. MAIN FORM ---
st.subheader(f"{selected_title}")

template_en = current_prompt_data["prompt_en"]
template_ru = current_prompt_data["prompt_ru"]

VAR_PATTERN = r"\[([a-zA-Z0-9_]+)\]"
required_vars = sorted(set(re.findall(VAR_PATTERN, template_en) + re.findall(VAR_PATTERN, template_ru)))

user_inputs = {}

def has_cyrillic(s: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", s))

def safe_translate_to_en(text: str) -> str:
    # translate only if looks non-EN (mostly Cyrillic)
    if not text or not text.strip():
        return text
    if text.strip().startswith(("http://", "https://", "www.")):
        return text
    if not has_cyrillic(text):
        return text
    try:
        translator = GoogleTranslator(source="auto", target="en")
        return translator.translate(text)
    except Exception:
        return text  # fail-safe

def normalize_special_vars(d: dict) -> dict:
    # Expand "control" vars into model-friendly instructions
    out = dict(d)

    if "lens_match_mode" in out:
        mode = out["lens_match_mode"].strip().lower()
        out["lens_match_mode"] = (
            "match lens look (focal-length feel) so it reads as one photo"
            if mode.startswith("f")
            else "match focal length strictly (same equivalent focal length)"
        )

    if "show_preview" in out:
        val = out["show_preview"].strip().lower()
        out["show_preview"] = (
            "show a 2×2 tiled preview in one frame"
            if val.startswith("y")
            else "single tile only"
        )

    if "labels_visibility" in out:
        val = out["labels_visibility"].strip().lower()
        out["labels_visibility"] = (
            "add small view labels (Front/Side/Back)"
            if val == "on"
            else "no labels"
        )

    if "focus_stacking" in out:
        val = out["focus_stacking"].strip().lower()
        out["focus_stacking"] = (
            "on (more of the subject in focus)"
            if val == "on"
            else "off (razor-thin DOF)"
        )

    if "intensity" in out:
        out["intensity"] = out["intensity"].strip().lower()

    if "level" in out:
        out["level"] = out["level"].strip().lower()

    return out

if not required_vars:
    st.success("✅ Для этого промпта параметры не требуются. Просто нажмите кнопку.")
    with st.form("prompt_form_empty"):
        neg_mode = st.radio(
            "Режим негатива (Negative Prompt):",
            ["Mini (Легкий)", "Default (Mini+)", "Aggressive (Full)"],
            index=1,
            horizontal=True
        )
        submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)
else:
    with st.form("prompt_form"):
        cols = st.columns(2)
        for i, var in enumerate(required_vars):
            col = cols[i % 2]
            label = VAR_MAP.get(var, f"Введите {var}")
            example = EXAMPLES_DB.get(var, {})
            ph = example.get("ph", "Пример...")
            help_text = example.get("help", "")

            widget_key = f"{selected_id}__{var}"

            if var in ENUM_OPTIONS:
                user_inputs[var] = col.selectbox(
                    label,
                    options=ENUM_OPTIONS[var],
                    key=widget_key,
                    help=help_text
                )
            else:
                user_inputs[var] = col.text_input(
                    label,
                    key=widget_key,
                    placeholder=ph,
                    help=help_text
                )

        st.write("---")
        neg_mode = st.radio(
            "Режим негатива (Negative Prompt):",
            ["Mini (Легкий)", "Default (Mini+)", "Aggressive (Full)"],
            index=1,
            horizontal=True
        )
        st.write(" ")
        submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)

# --- 11. GENERATION ---
if "submitted" in locals() and submitted:
    missing = [VAR_MAP.get(k, k) for k, v in user_inputs.items() if not str(v).strip()]
    if missing:
        st.error("⚠️ **Вы забыли заполнить поля:**\n\n" + "\n".join([f"- {m}" for m in missing]))
    else:
        try:
            with st.spinner("⏳ Собираем промпт..."):

                # RU: use raw inputs (as user typed)
                inputs_ru = normalize_special_vars(user_inputs)

                # EN: translate only if needed (Cyrillic -> EN), keep URLs
                inputs_en = {}
                for k, v in user_inputs.items():
                    v = str(v)
                    inputs_en[k] = safe_translate_to_en(v)
                inputs_en = normalize_special_vars(inputs_en)

                # Generate
                res_en = manager.generate(selected_id, "en", **inputs_en).strip()
                res_ru = manager.generate(selected_id, "ru", **inputs_ru).strip()

                # NEG mode
                group_id = ID_TO_GROUP.get(selected_id, 1)
                mode_key = "Plus"
                if "Mini" in neg_mode:
                    mode_key = "Mini"
                elif "Aggressive" in neg_mode:
                    mode_key = "Full"

                neg_text_en = NEG_GROUPS[group_id][mode_key]["en"]
                neg_text_ru = NEG_GROUPS[group_id][mode_key]["ru"]

                # Add per-prompt NEG add-ons if needed
                addon = NEG_ADDONS.get(selected_id)
                if addon:
                    neg_text_en = f"{neg_text_en}, {addon['en']}"
                    neg_text_ru = f"{neg_text_ru}, {addon['ru']}"

                # For NanoBanano/bots: "--no"
                full_bot_text = f"{res_en} --no {neg_text_en}"

                save_to_history(
                    selected_title,
                    full_bot_text,
                    f"{res_ru} | NEG: {neg_text_ru}"
                )

            st.success(":material/check_circle: **Готово!**")

            tab1, tab2 = st.tabs(["🇺🇸 **English (PRO)**", "🇷🇺 Русский (Info)"])

            with tab1:
                st.markdown("### :material/rocket_launch: Всё в одном (для NanoBanano / ботов)")
                st.caption(f"NEG preset: **{mode_key}** (добавлено через `--no`).")
                st.code(full_bot_text, language="text")
                st_copy_to_clipboard(full_bot_text, "📋 Скопировать всё", key=f"all_{hash(full_bot_text)}")

                st.divider()

                st.markdown("### :material/build: Раздельно (для WebUI)")
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(":material/add_circle: **Positive Prompt**")
                    st.code(res_en, language="text")
                    st_copy_to_clipboard(res_en, "Positive", key=f"pos_{hash(res_en)}")
                with col2:
                    st.caption(":material/do_not_disturb_on: **Negative Prompt**")
                    st.code(neg_text_en, language="text")
                    st_copy_to_clipboard(neg_text_en, "Negative", key=f"neg_{hash(neg_text_en)}")

            with tab2:
                st.markdown("##### 🇷🇺 Что мы попросили нейросеть:")
                st.info(f"**Positive:**\n\n{res_ru}")
                st.warning(f"**NEG ({mode_key}):**\n\n{neg_text_ru}")

        except Exception as e:
            st.error(f"❌ Ошибка: {e}")

# --- 12. HISTORY OUTPUT ---
with tab_history:
    st.write(" ")
    if st.button("Очистить историю"):
        st.session_state["history"] = []
        st.rerun()

    history_list = st.session_state["history"]
    if not history_list:
        st.caption("История пуста.")
    else:
        for item in history_list:
            label = f"{item['time']} | {item['task']}"
            with st.expander(label):
                st.caption("English (NanoBanano / bot):")
                st.code(item["en"], language="text")
                st_copy_to_clipboard(item["en"], "Копировать EN", key=f"hist_en_{item['id']}")

                st.markdown("---")

                st.caption("Russian (Info):")
                st.code(item["ru"], language="text")

with st.sidebar:
    st.markdown("---")
