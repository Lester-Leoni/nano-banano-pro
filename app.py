import os
import atexit
import time
import unicodedata
import re
import threading
import datetime
from pathlib import Path
import json
import hashlib
import sys
import traceback

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, wait as futures_wait, FIRST_COMPLETED
from typing import List, Tuple

import streamlit as st
import streamlit.components.v1 as components

from prompt_manager import PromptManager

# =========================================================
# FUTURE_SAAS FOUNDATION (no auth/billing implemented)
# =========================================================
# These hooks are part of the repository and must load reliably.
# Security principle: fail closed (do not silently disable limits / logging).
try:
    from future_saas.bootstrap import get_future_config, get_request_context, get_usage_recorder
    from future_saas.errors import public_error_message
    from future_saas.limits import enforce_usage_limits
    from future_saas.usage import UsageAction, make_event
except ImportError as e:  # pragma: no cover
    raise RuntimeError(
        "future_saas is required but could not be imported. "
        "Ensure the repository contains the future_saas/ package."
    ) from e

# Копирование в буфер: используем пакет, если установлен; иначе — JS fallback.
try:
    from st_copy_to_clipboard import st_copy_to_clipboard  # type: ignore
except Exception:
    import base64
    import html

    def st_copy_to_clipboard(text: str, label: str = "Копировать", key: str | None = None):
        """Fallback: кнопка копирования через встроенный JS.

        Security: НЕ вставляем пользовательский текст напрямую в <script>, чтобы
        исключить XSS через последовательности вида </script>.
        """
        btn_id_raw = (key or f"copy_{abs(hash(text))}")[:60]
        btn_id = re.sub(r"[^a-zA-Z0-9_-]", "_", btn_id_raw)
        label_safe = html.escape(label or "Копировать")
        b64 = base64.b64encode((text or "").encode("utf-8")).decode("ascii")

        components.html(
            f"""
            <div style='display:flex; gap:8px; align-items:center;'>
              <button id='{btn_id}' style='
                background:#FFD700; border:none; padding:10px 14px; border-radius:8px;
                cursor:pointer; font-weight:800; color:#000; width:100%;'>
                {label_safe}
              </button>
            </div>
            <script>
              const btn = document.getElementById('{btn_id}');
              const b64 = '{b64}';
              const decodeB64Utf8 = (s) => {{
                try {{
                  const bytes = Uint8Array.from(atob(s), c => c.charCodeAt(0));
                  return new TextDecoder('utf-8').decode(bytes);
                }} catch (e) {{
                  return '';
                }}
              }};
              if (btn) {{
                btn.onclick = async () => {{
                  try {{
                    await navigator.clipboard.writeText(decodeB64Utf8(b64));
                    btn.innerText = '✅ Скопировано';
                    setTimeout(()=>btn.innerText='{label_safe}', 900);
                  }} catch (e) {{
                    btn.innerText = '⚠️ Не удалось';
                    setTimeout(()=>btn.innerText='{label_safe}', 1200);
                  }}
                }}
              }}
            </script>
            """,
            height=55,
        )

# Перевод (защита от падения)
try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None


# PIL is used only for lightweight image structure verification.
try:
    from PIL import Image  # type: ignore
except Exception:
    Image = None


# =========================================================
# PATHS
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_PATH = BASE_DIR / "prompts.json"
ASSETS_DIR = BASE_DIR / "assets"


@st.cache_data(show_spinner=False)
def resolve_preview_image(prompt_id: str) -> str | None:
    """Resolve preview asset path for a prompt id (cached to avoid per-rerun FS checks)."""
    if not prompt_id:
        return None
    try:
        if not ASSETS_DIR.exists():
            return None
    except Exception:
        return None
    for ext in (".jpg", ".png"):
        p = ASSETS_DIR / f"{prompt_id}{ext}"
        try:
            if p.exists():
                return str(p)
        except Exception:
            continue
    return None



def _env_int(name: str, default: int) -> int:
    """Безопасно парсит int из переменных окружения."""
    try:
        raw = (os.getenv(name) or "").strip()
        return int(raw) if raw else int(default)
    except Exception:
        return int(default)


def _env_float(name: str, default: float) -> float:
    """Безопасно парсит float из переменных окружения."""
    try:
        raw = (os.getenv(name) or "").strip()
        return float(raw) if raw else float(default)
    except Exception:
        return float(default)


def _env_bool(name: str, default: bool) -> bool:
    """Безопасно парсит bool из переменных окружения."""
    raw = (os.getenv(name) or "").strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


# Лимит загрузки файлов в UI (DoS-guard). По умолчанию 8MB.
UI_MAX_FILE_BYTES = _env_int("NANOBANANO_UI_MAX_FILE_BYTES", 8 * 1024 * 1024)

# Дополнительные лимиты загрузки.
UI_MAX_UPLOAD_FILES = _env_int("NANOBANANO_UI_MAX_UPLOAD_FILES", 12)
UI_MAX_TOTAL_UPLOAD_BYTES = _env_int("NANOBANANO_UI_MAX_TOTAL_UPLOAD_BYTES", 32 * 1024 * 1024)

# Перевод (можно отключить полностью).
TRANSLATION_ENABLED_DEFAULT = _env_bool("NANOBANANO_TRANSLATION_ENABLED", True)

# Таймауты/лимиты для переводчика (hardening).
# Важно: перевод вызывается из UI-треда, поэтому дефолт держим коротким.
TRANSLATE_TIMEOUT_SEC = _env_float("NANOBANANO_TRANSLATE_TIMEOUT_SEC", 2.0)
TRANSLATE_MAX_CHARS = _env_int("NANOBANANO_TRANSLATE_MAX_CHARS", 4000)
TRANSLATE_MAX_CONCURRENCY = _env_int("NANOBANANO_TRANSLATE_MAX_CONCURRENCY", 1)
TRANSLATE_ACQUIRE_TIMEOUT_SEC = _env_float("NANOBANANO_TRANSLATE_ACQUIRE_TIMEOUT_SEC", 0.1)
TRANSLATE_CACHE_TTL_SEC = _env_int("NANOBANANO_TRANSLATE_CACHE_TTL_SEC", 3600)
TRANSLATE_CACHE_MAX_ENTRIES = _env_int("NANOBANANO_TRANSLATE_CACHE_MAX_ENTRIES", 256)
TRANSLATE_CACHE_MAX_BYTES = _env_int("NANOBANANO_TRANSLATE_CACHE_MAX_BYTES", 2_000_000)
TRANSLATE_GLOBAL_BUDGET_SEC = _env_float(
    "NANOBANANO_TRANSLATE_GLOBAL_BUDGET_SEC",
    max(0.2, float(TRANSLATE_TIMEOUT_SEC) * max(1, int(TRANSLATE_MAX_CONCURRENCY))),
)

# Privacy/supply-chain hardening: allow disabling external font loads in public deployments.
PUBLIC_DEPLOYMENT = _env_bool("NANOBANANO_PUBLIC_DEPLOYMENT", False)
ALLOW_EXTERNAL_FONTS = _env_bool("NANOBANANO_ALLOW_EXTERNAL_FONTS", not PUBLIC_DEPLOYMENT)
EXTERNAL_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');"
    if ALLOW_EXTERNAL_FONTS
    else ""
)

@st.cache_resource
def get_translate_executor() -> ThreadPoolExecutor:
    """Shared executor for translation calls (prevents indefinite hangs)."""
    ex = ThreadPoolExecutor(max_workers=max(1, int(TRANSLATE_MAX_CONCURRENCY)))

    # Ensure worker threads don't leak across long-lived/reloaded processes.
    def _shutdown_executor() -> None:
        try:
            ex.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            # Python < 3.9: no cancel_futures
            ex.shutdown(wait=False)
        except Exception:
            pass

    atexit.register(_shutdown_executor)
    return ex


@st.cache_resource
def get_translate_semaphore() -> threading.Semaphore:
    """Global (process-wide) ограничитель конкурентных обращений к переводчику."""
    # Даже при нескольких сессиях Streamlit мы не хотим пачкой бить во внешний переводчик.
    return threading.Semaphore(max(1, int(TRANSLATE_MAX_CONCURRENCY)))


@st.cache_resource
def get_translator_en():
    """Кешируем переводчик."""
    if GoogleTranslator is None:
        return None
    try:
        return GoogleTranslator(source="auto", target="en")
    except Exception:
        return None


# =========================================================
# 1) CONFIG
# =========================================================
st.set_page_config(
    page_title="Nano Banano Pro",
    page_icon="🍌",
    layout="centered",
    initial_sidebar_state="expanded",
)

# =========================================================
# 2) JS CLEANER & CSS
# =========================================================
components.html(
    """
    <script>
    (function () {
        const root = (window.parent && window.parent.document) ? window.parent.document : document;

        function removeTitles() {
            const selects = root.querySelectorAll('div[data-baseweb="select"]');
            if (!selects || !selects.length) return;
            selects.forEach(sel => {
                const titled = sel.querySelectorAll('[title]');
                titled.forEach(el => {
                    el.removeAttribute('title');
                });
            });
        }

        let scheduled = false;
        function scheduleRemoveTitles() {
            if (scheduled) return;
            scheduled = true;
            setTimeout(() => {
                scheduled = false;
                removeTitles();
            }, 150);
        }

        const observer = new MutationObserver((mutations) => {
            for (const m of mutations) {
                if (m.addedNodes && m.addedNodes.length) {
                    scheduleRemoveTitles();
                    return;
                }
            }
        });

        try {
            observer.observe(root.body, { childList: true, subtree: true });
        } catch (e) {
            // ignore
        }
        setTimeout(removeTitles, 800);
    })();
    </script>
    """,
    height=0,
)

st.markdown(
    "<style>\n"
    + (EXTERNAL_FONT_IMPORT + "\n" if EXTERNAL_FONT_IMPORT else "")
    + """

/* GLOBAL THEME */
[data-testid="stAppViewContainer"] {
    background-color: #0e0e0e;
    background-image:
        radial-gradient(circle at 100% 0%, #2a2200 0%, transparent 25%),
        radial-gradient(circle at 0% 100%, #161616 0%, transparent 40%);
    background-attachment: fixed;
}

/* STREAMLIT TOP BAR (HEADER)
   Streamlit renders a fixed header/toolbar with its own background.
   Make it transparent so it inherits the app's background theme.
   (This keeps UX unchanged while preventing a "black" top bar regression.) */
header[data-testid="stHeader"], [data-testid="stHeader"] {
    background: transparent !important;
}
div[data-testid="stToolbar"], div[data-testid="stToolbar"] > div {
    background: transparent !important;
}
[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #333 !important;
}

/* TYPOGRAPHY */
h1, h2, h3, h4, p, label, .stMarkdown, .stCaption, [data-testid="stSidebar"] label, [data-testid="stExpander"] p, div[data-baseweb="tab"] p {
    color: #e0e0e0 !important;
    font-family: 'Inter', sans-serif !important;
}

/* INPUT FIELDS */
div[data-baseweb="base-input"], div[data-baseweb="textarea"] { 
    background-color: #222222 !important; 
    border: 1px solid #444 !important; 
    border-radius: 6px !important;
}
div[data-baseweb="base-input"] input, div[data-baseweb="textarea"] textarea {
    color: #ffffff !important; 
    -webkit-text-fill-color: #ffffff !important; 
    caret-color: #FFD700 !important; 
    font-weight: 500 !important;
    font-size: 16px !important; 
}
input::placeholder, textarea::placeholder {
    color: #aaaaaa !important; 
    -webkit-text-fill-color: #aaaaaa !important; 
    opacity: 1 !important; 
    font-weight: 400 !important;
}
div[data-baseweb="base-input"]:focus-within, div[data-baseweb="select"] > div:focus-within, div[data-baseweb="textarea"]:focus-within {
    border-color: #FFD700 !important; 
    box-shadow: 0 0 0 1px #FFD700 !important;
}

/* TABS */
button[data-baseweb="tab"] { 
    border-radius: 6px !important; 
    margin-right: 8px !important; 
    border: 1px solid #333 !important; 
    background-color: #1a1a1a !important;
    padding: 4px 12px !important; 
}
button[data-baseweb="tab"][aria-selected="true"] { 
    background-color: #FFD700 !important; 
    border-color: #FFD700 !important; 
    box-shadow: 0 2px 8px rgba(255, 215, 0, 0.25) !important; 
}
button[data-baseweb="tab"][aria-selected="true"] div p { 
    color: #000000 !important; 
    font-weight: 700 !important; 
}
div[data-baseweb="tab-highlight"] { display: none !important; }

/* BUTTONS */
div.stButton > button {
    background-color: #FFD700 !important; 
    border: none !important; 
    color: #000000 !important;
    font-weight: 700 !important;
    font-size: 18px !important;
    padding: 0.6rem 1rem !important;
    border-radius: 8px !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
div.stButton > button:hover {
    background-color: #FFC300 !important; 
    box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4) !important; 
    transform: translateY(-2px);
}
div.stButton > button p { color: #000000 !important; }

/* BANNER */
.main-banner {
    background: linear-gradient(90deg, rgba(255, 215, 0, 0.1) 0%, rgba(0,0,0,0) 100%);
    border-left: 5px solid #FFD700;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 25px;
}
.main-banner h1 { margin: 0; font-size: 2.2rem; color: #FFD700 !important; }
.main-banner p { margin: 5px 0 0 0; opacity: 0.8; font-size: 1rem; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 3) DATA & CONFIGURATION
# =========================================================

# --- A. NEGATIVE PROMPTS ---
NEG_GROUPS = {
    1: {  # Photorealism & People
        "Mini": {"en": "waxy/plastic skin, beauty retouch, identity drift, extra fingers, watermark, text", "ru": "восковая кожа, бьюти-ретушь, потеря сходства, водяной знак, текст"},
        "Plus": {"en": "waxy/plastic skin, over-smoothing, beauty retouch, face reshaping, identity drift, extra teeth, deformed hands, extra fingers, watermark, text", "ru": "восковая кожа, пересглаживание, бьюти-ретушь, изменение лица, лишние зубы, деформированные руки, водяной знак, текст"},
        "Full": {"en": "waxy/plastic skin, over-smoothing, beauty retouch, face reshaping, identity drift, uncanny face, extra teeth, deformed hands, extra limbs/fingers, AI glow, oversharpen halos, banding, watermark, logo, text", "ru": "восковая кожа, пересглаживание, бьюти-ретушь, жуткое лицо, лишние зубы, деформированные руки, лишние конечности, AI-свечение, перешарп, водяной знак, текст"},
    },
    2: {  # Scene Editing
        "Mini": {"en": "seams, halos, ghosting, wrong shadow, wrong scale, watermark, text", "ru": "швы, ореолы, двоение, неверные тени, неверный масштаб, водяной знак, текст"},
        "Plus": {"en": "seams, halos, cutout edges, ghosting, smear, warped lines, floating object, wrong shadow, wrong scale, mismatch grain, watermark, text", "ru": "швы, ореолы, обрезанные края, двоение, размазывание, кривые линии, левитация, неверные тени, неверный масштаб, водяной знак, текст"},
        "Full": {"en": "seams, halos, cutout edges, ghosting, smearing, warped perspective/lines, floating objects, wrong scale, wrong shadows, inconsistent lighting, mismatch grain/noise, color mismatch, missing reflections, watermark, logo, text", "ru": "швы, ореолы, обрезанные края, двоение, размазывание, искаженная перспектива, левитация, неверный масштаб, неверные тени, несогласованный свет, ошибки отражений, водяной знак, логотип"},
    },
    3: {  # Commercial Design
        "Mini": {"en": "misspelling, broken glyphs, lorem ipsum, tiny text, random logo, watermark", "ru": "опечатки, битые символы, lorem ipsum, мелкий текст, случайный логотип, водяной знак"},
        "Plus": {"en": "misspelling, broken glyphs, lorem ipsum, tiny unreadable text, clutter, misaligned layout, low-contrast text, pixelation, random logo, watermark", "ru": "опечатки, битые символы, lorem ipsum, нечитаемый текст, мусор, кривая верстка, пикселизация, случайный логотип, водяной знак"},
        "Full": {"en": "misspelling, broken glyphs, lorem ipsum, tiny unreadable text, clutter, misaligned layout, low contrast, pixelation, jagged edges, wrong aspect ratio, random brand/logo, extra QR codes, illegible icons, watermark", "ru": "опечатки, битые символы, lorem ipsum, мелкий текст, мусор, кривая верстка, пикселизация, рваные края, неверные пропорции, случайный бренд, лишние QR-коды, водяной знак"},
    },
    4: {  # Art & Illustration
        "Mini": {"en": "extra objects, anatomy warp, style drift, seams, vignette, watermark, text", "ru": "лишние объекты, искажение анатомии, плавающий стиль, швы, виньетка, водяной знак, текст"},
        "Plus": {"en": "extra objects, anatomy warp, proportion change, perspective distortion, messy linework, style drift, pattern seams, vignette, unreadable text, watermark", "ru": "лишние объекты, искажение анатомии, нарушение пропорций, кривые линии, плавающий стиль, швы, виньетка, нечитаемый текст, водяной знак"},
        "Full": {"en": "extra objects, anatomy warp, proportion changes, perspective distortion, messy linework, inconsistent style, seams in pattern, vignette, unwanted shading, unreadable text/gibberish, watermark, logo", "ru": "лишние объекты, искажение анатомии, нарушение пропорций, искажение перспективы, неряшливые линии, непоследовательный стиль, швы, виньетка, лишние тени, нечитаемый текст, водяной знак, логотип"},
    },
    5: {  # Architecture
        "Mini": {"en": "keystone distortion, warped verticals, messy geometry, unrealistic scale, watermark, text", "ru": "трапеция, кривые вертикали, грязная геометрия, нереальный масштаб, водяной знак, текст"},
        "Plus": {"en": "keystone distortion, warped verticals, bent walls, unrealistic scale, messy geometry, low-res textures, blown highlights, muddy shadows, clutter, watermark", "ru": "трапеция, кривые стены, нереальный масштаб, грязная геометрия, низкое разрешение текстур, пересветы, грязные тени, мусор, водяной знак"},
        "Full": {"en": "keystone distortion, bent walls, warped verticals, unrealistic scale, messy geometry, low-res textures, oversharpen halos, blown highlights, muddy shadows, clutter, people (if not requested), watermark, logo, text", "ru": "трапеция, кривые стены, нереальный масштаб, грязная геометрия, низкое разрешение, ореолы, пересветы, грязные тени, мусор, лишние люди, водяной знак, текст"},
    },
    6: {  # VFX / Cinema
        "Mini": {"en": "overdone flares, heavy aberration, excessive bloom, noisy artifacts, watermark, text", "ru": "перебор бликов, аберрация, bloom, шум, водяной знак, текст"},
        "Plus": {"en": "excessive bloom, heavy chromatic aberration, overdone flares, crushed blacks, blown highlights, noisy artifacts, oversharpen halos, watermark, text", "ru": "избыточный bloom, аберрация, блики, проваленные черные, пересветы, шум, ореолы, водяной знак, текст"},
        "Full": {"en": "overdone bloom, heavy aberration, excessive flares, crushed blacks, blown highlights, noisy artifacts, oversharpen halos, unreadable text, tiny clutter text, watermark, logo", "ru": "перебор bloom, аберрация, блики, проваленные черные, пересветы, шум, ореолы, нечитаемый текст, мусор, водяной знак, логотип"},
    },
}

NEG_ADDONS = {
    "logo_creative": {"en": "photorealistic, 3d render, mockup, gradients, textures, shadows, realistic lighting", "ru": "фотореализм, 3d-рендер, мокап, градиенты, текстуры, тени, реалистичный свет"},
    "technical_blueprint": {"en": "shading, gradients, perspective view, sketchy lines, hand-drawn look", "ru": "шейдинг, градиенты, перспектива, скетчевые линии, рисунок от руки"},
    "macro_extreme": {"en": "cartoon, illustration, painterly style, fake CG look", "ru": "мультяшность, иллюстрация, живописная стилизация, фейковый CG-вид"},
}

ID_TO_GROUP = {
    "upscale_restore": 1, "old_photo_restore": 1, "studio_portrait": 1, "background_change": 1, "face_swap": 1, "expression_change": 1, "pose_change": 1, "camera_angle_change": 1, "cloth_swap": 1, "team_composite": 1, "macro_extreme": 1,
    "object_removal": 2, "object_addition": 2, "semantic_replacement": 2, "scene_relighting": 2, "scene_composite": 2, "total_look_builder": 2,
    "product_card": 3, "mockup_generation": 3, "environmental_text": 3, "knolling_photography": 3, "logo_creative": 3, "logo_stylization": 3, "ui_design": 3, "text_design": 3,
    "image_restyling": 4, "sketch_to_photo": 4, "character_sheet": 4, "sticker_pack": 4, "comic_page": 4, "storyboard_sequence": 4, "seamless_pattern": 4, "anatomical_infographic": 4,
    "interior_design": 5, "architecture_exterior": 5, "isometric_room": 5,
    "youtube_thumbnail": 6, "cinematic_atmosphere": 6, "technical_blueprint": 6, "exploded_view": 6
}

NEG_CATEGORY_LABELS = ["Авто (по задаче)", "Люди / портрет / лицо", "Редактирование / коллаж", "Дизайн / логотип", "Иллюстрация / арт", "Интерьер / архитектура", "Кино / VFX"]
NEG_CATEGORY_PRESETS = {"Авто (по задаче)": None, "Люди / портрет / лицо": 1, "Редактирование / коллаж": 2, "Дизайн / логотип": 3, "Иллюстрация / арт": 4, "Интерьер / архитектура": 5, "Кино / VFX": 6}

# --- B. LABELS & EXAMPLES (HUMANIZED RUSSIAN UI) ---

VAR_MAP = {
    # Common
    "image_1": "Исходное изображение / Ссылка",
    "image_2": "Референс / Второе изображение",
    "aspect_ratio": "Формат (Пропорции)",
    "background": "Фон / Стиль фона",
    "background_type": "Тип фона (для мокапа)",
    "environment": "Окружение",
    "lighting": "Схема освещения",
    "style": "Художественный стиль",
    "colors": "Цветовая гамма",
    
    # People
    "person": "Персонаж (описание)",
    "person_image": "Фото человека",
    "people_links": "Фото персонажей",
    "emotion": "Желаемая эмоция",
    "intensity": "Сила эмоции",
    "camera_angle": "Ракурс камеры",
    "action_description": "Поза / Действие",
    
    # Clothing / Products
    "fabric_material": "Материал ткани",
    "clothing_image": "Фото одежды (на вешалке/модели)",
    "footwear_image": "Фото обуви",
    "accessory_image": "Аксессуар (сумка/очки)",
    "model_image": "Фото модели (База)",
    
    # Objects
    "object": "Объект",
    "placement_details": "Где разместить?",
    "object_to_replace": "Что заменяем?",
    "new_object": "На что заменяем?",
    "element_1": "Фоновый объект / Сцена",
    "element_2": "Вставляемый объект",
    
    # Tech / Design
    "product": "Название товара",
    "text": "Текст (Точно)",
    "text_content": "Текст надписи",
    "features_list": "Список преимуществ",
    "object_type": "На какой предмет наносим?",
    "print_finish": "Фактура нанесения",
    "brand": "Бренд / Компания",
    "imagery": "Символ / Графика",
    "materials": "Материалы",
    "screen_type": "Тип экрана",
    
    # Other
    "scene_description": "Описание итоговой сцены",
    "description": "Описание персонажа",
    "platform": "Платформа",
    "theme": "Тема",
    "character": "Персонаж (референс)",
    "lens_match_mode": "Режим сведения (Линзы)",
    "target_object": "Поверхность нанесения",
    "material_type": "Материал поверхности",
    "application_style": "Способ нанесения (краска/вышивка)",
    "character_description": "Внешность персонажа",
    "activity": "Действие",
    "lighting_condition": "Новое освещение",
    "environment_description": "Описание окружения/фона",
    
    # Updated Items
    "industry": "Индустрия / Ниша",
    "font_style": "Стиль шрифта",
    "medium": "Техника (Материал)",
    "level": "Сила стилизации",
    "labels_visibility": "Подписи (спереди/сбоку)",
    "count": "Количество",
    "list": "Список эмоций/поз",
    "scene": "Описание сцены (Сюжет)",
    "language": "Язык",
    "layout": "Компоновка (Сетка)",
    "action_sequence": "Последовательность действий",
    "show_preview": "Режим превью (2x2)",
    "room_type": "Тип комнаты",
    "room": "Комната (фото/ссылка/описание)",
    "building_type": "Тип здания",
    "time": "Время суток / Погода",
    "lens": "Объектив",
    "background_color": "Цвет фона",
    "type": "Тип (Фото/Иллюстрация)",
    "expression": "Выражение лица (превью)",
    "subject": "Главный объект",
    "focus_stacking": "Глубина резкости (фокус-стекинг)",
    "additional_details": "Дополнительные детали",
}

# -------------------------------------------------------------
# GENERIC HINTS (Fallback)
# -------------------------------------------------------------
EXAMPLES_DB = {
    # Common
    "image_1": {"ph": "Ссылка или файл...", "help": "Основное изображение."},
    "image_2": {"ph": "Ссылка или файл...", "help": "Референс стиля или объект."},
    "aspect_ratio": {"ph": "9:16 (Сторис)...", "help": "Выберите формат."},
    "background": {"ph": "современный офис, размытый фон", "help": "Примеры: белая циклорама, ночной город, стиль киберпанк."},
    "style": {"ph": "фотореализм, 8k", "help": "Примеры: фотореализм, 3D-рендер, акварель, нуар."},
    "lighting": {"ph": "мягкий свет, неон", "help": "Примеры: мягкий студийный свет, неоновый синий, золотой час."},
    "object": {"ph": "красная машина, лампа", "help": "Какой именно объект удалить или добавить? Пиши конкретно."},
    "text": {"ph": "SALE 50%", "help": "Текст должен быть написан ТОЧНО так, как нужно (без перевода)."},
    "text_content": {"ph": "SALE, Love, 2025", "help": "Сам текст надписи. Соблюдай регистр."},
    "materials": {"ph": "дерево, стекло", "help": "Материалы объекта."},
}

# -------------------------------------------------------------
# SPECIFIC OVERRIDES (МАТРИЦА УМНЫХ ПОДСКАЗОК)
# -------------------------------------------------------------
SPECIFIC_HINTS = {
    "studio_portrait": { # 03
        "background": {"ph": "белая циклорама, цветной фон", "help": "Фон: однотонный, размытый лофт, текстура бумаги."},
        "lighting": {"ph": "Rembrandt, softbox", "help": "Схемы света: Рембрандт, бабочка (butterfly), мягкий софтбокс."},
    },
    "background_change": { # 04
        "background": {"ph": "париж, пляж, офис", "help": "Новый фон: Эйфелева башня, пляж на закате, современный офис."}
    },
    "expression_change": { # 06
        "emotion": {"ph": "радость, гнев", "help": "Эмоции: страх, радость, удивление, гнев, восторг."}
    },
    "pose_change": { # 07
        "action_description": {"ph": "бежит, сидит на стуле", "help": "Что делает персонаж? (прыгает, танцует, скрестил руки)."}
    },
    "camera_angle_change": { # 08
        "camera_angle": {
            "ph": "top-down 90° overhead", 
            "help": "ВАЖНО: Для вида строго сверху пиши 'top-down 90° overhead'. Для вида сбоку: 'side view eye-level'. Снизу: 'low angle'."
        }
    },
    "cloth_swap": { # 09
        "fabric_material": {"ph": "кожа, шелк", "help": "Материал: оставить как на фото, кожа, бархат, шелк, хлопок."}
    },
    "object_addition": { # 11
        "placement_details": {"ph": "на столе, в руке", "help": "Где разместить? Примеры: на столе справа, в левой руке, на заднем плане."}
    },
    "semantic_replacement": { # 12
        "object_to_replace": {"ph": "старый диван, ваза", "help": "Что заменяем? Примеры: красная ваза, старое кресло, картина на стене."}
    },
    "scene_relighting": { # 13
        "lighting_condition": {"ph": "закат, неон, лунный свет", "help": "Новый свет: золотой час, киберпанк неон, холодная ночь."}
    },
    "team_composite": { # 15
        "activity": {"ph": "танцуют, совещание", "help": "Что делают люди? (идут, работают, празднуют, танцуют)."},
        "environment": {"ph": "офис, сцена, парк", "help": "Где находятся люди? (Офис, сцена, пляж, улица)."},
        "people_links": {"ph": "Ссылки или файлы...", "help": "Укажите несколько людей, до 5 человек."}
    },
    "scene_composite": { # 16
        "scene_description": {"ph": "Медведь играет на гитаре в лесу", "help": "Опиши сюжет, который должен получиться."}
    },
    "product_card": { # 17
        "product": {"ph": "Nike Air Max, iPhone 15", "help": "Название бренда и модели (Nike, Adidas, iPhone, Snickers)."},
        "features_list": {"ph": "Водостойкий, 24ч батарея", "help": "Список преимуществ через запятую."}
    },
    "mockup_generation": { # 18
        "object_type": {"ph": "кофейный стакан, футболка", "help": "Загрузи фото предмета (футболка, кружка) или опиши его словами."},
        "background_type": {"ph": "деревянный стол, мрамор", "help": "На чем стоит предмет? (стол, бетон, цветной фон)."},
        "print_finish": {"ph": "золотое тиснение, матовый", "help": "Фактура: вышивка, глянец, матовая бумага."},
        "image_1": {"ph": "Загрузите файл...", "help": "Загрузите логотип, картинку или обложку, которую наносим."}
    },
    "environmental_text": { # 19
        "environment_description": {"ph": "песчаный пляж, стена", "help": "Где написан текст? (песок, кирпичная стена, снег)."},
        "target_object": {"ph": "песок, бетон, ткань", "help": "Поверхность: песок, футболка, асфальт."},
        "material_type": {"ph": "песок, камень, хлопок", "help": "Материал поверхности: песок, бетон, деним."}
    },
    "knolling_photography": { # 20
        "object": {"ph": "фототехника, инструменты", "help": "С каким именно объектом производим действия (предметы для раскладки)."}
    },
    "logo_creative": { # 21
        "imagery": {"ph": "лев, молния, гора", "help": "Образ или символ для логотипа."}
    },
    "logo_stylization": { # 22
        "materials": {"ph": "овощи, бумага, стекло", "help": "Из чего собран логотип? (фрукты, механизмы, сладости, бумага)."}
    },
    "ui_design": { # 23
        "industry": {"ph": "Финтех, Бьюти, Еда", "help": "Ниша: Банкинг, Салон красоты, Доставка еды."},
        "screen_type": {"ph": "Главный экран, Дашборд", "help": "Тип экрана: главный, лендинг, профиль."}
    },
    "text_design": { # 24
        "font_style": {"ph": "Жирный, Рукописный", "help": "Шрифт. Примеры: Жирный Sans, Рукописный, Граффити."},
        "colors": {"ph": "Черно-желтый, Пастель", "help": "Цвета: Черно-желтый, Пастель, Неон, Монохром."}
    },
    "image_restyling": { # 25 (art_style)
        "medium": {"ph": "Масло, Карандаш, Вектор", "help": "Техника: Акварель, Гуашь, Маркеры, Пиксель-арт."}
    },
    "sketch_to_photo": { # 26
        "materials": {"ph": "стекло, кожа, металл", "help": "Материалы для реализма: дерево, пластик, ткань."},
        "lighting": {"ph": "студийный свет, закат", "help": "Примеры: мягкий свет, неон, закат, студийное освещение."}
    },
    "character_sheet": { # 27
        "description": {"ph": "девушка киборг, рыжие волосы", "help": "Описание внешности персонажа."}
    },
    "sticker_pack": { # 28
        "count": {"ph": "6, 9, 12", "help": "Сколько стикеров?"},
        "list": {"ph": "смех, гнев, лайк", "help": "Список эмоций."}
    },
    "comic_page": { # 29
        "scene": {"ph": "Детектив входит в комнату", "help": "Описание сцены (сюжет страницы)."},
        "language": {"ph": "Английский, Русский", "help": "Язык текста в бабблах (если есть)."}
    },
    "storyboard_sequence": { # 30
        "action_sequence": {"ph": "1. входит 2. смотрит 3. бежит", "help": "Примеры: 1. Просыпается 2. Пьет кофе 3. Выходит."},
        "layout": {"ph": "сетка 2x3", "help": "Количество кадров, формат (напр. сетка 2x3, 3 горизонтальные панели)."}
    },
    "seamless_pattern": { # 31
        "theme": {"ph": "тропические листья, геометрия", "help": "Тема узора."},
        "colors": {"ph": "Пастель, Неон", "help": "Цвета: Пастель, Неон, Черно-белый, Золотой."}
    },
    "interior_design": { # 32
        "materials": {"ph": "дуб, мрамор, бетон", "help": "Материалы отделки: дерево, камень, стекло, велюр."},
        "room_type": {"ph": "Спальня, Кухня, Лофт", "help": "Тип помещения."}
    },
    "architecture_exterior": { # 33
        "building_type": {"ph": "Вилла, Небоскреб", "help": "Тип здания."},
        "time": {"ph": "солнечный день, туман", "help": "Погода и время суток."},
        "environment": {"ph": "лес, центр города", "help": "Где стоит здание? (мегаполис, горы, пляж)."}
    },
    "isometric_room": { # 34
        "background_color": {"ph": "белый, синий градиент", "help": "Цвет фона: белый, синий, градиент."}
    },
    "youtube_thumbnail": { # 35
        "type": {"ph": "Влог, Обзор, Реакция", "help": "Тип видео: Влог, Обзор, Реакция."},
        "expression": {"ph": "шок, радость", "help": "Эмоция на лице: шок, радость, крик."}
    },
    "cinematic_atmosphere": { # 36
        "style": {"ph": "Нуар, Киберпанк, Уэс Андерсон", "help": "Киностиль: Тарантино, Неон, Винтаж 80х."}
    },
    "technical_blueprint": { # 37
        "object": {"ph": "двигатель, кроссовок", "help": "Чертеж чего делаем? Примеры: двигатель, кроссовок, стул, смартфон."}
    },
    "anatomical_infographic": { # 39
        "background": {"ph": "стиль Да Винчи, чертеж", "help": "Фон: старая бумага, медицинский плакат, грифельная доска."}
    },
    "macro_extreme": { # 40
        "object": {"ph": "глаз, насекомое, капля", "help": "Объект макросъемки."}
    }
}

# Списки выбора (РУССИФИЦИРОВАННЫЕ ДЛЯ UI)
ENUM_OPTIONS = {
    # ВАЖНО: Добавлен "Свой вариант (Custom)" в конце списка
    "aspect_ratio": ["9:16 (Stories / Reels)", "16:9 (YouTube / TV)", "1:1 (Post / Square)", "4:5 (Portrait)", "3:2 (Photo)", "2:3 (Photo)", "Свой вариант (Custom)"],
    "intensity": ["Слабая (Low)", "Средняя (Medium)", "Сильная (High)"],
    "level": ["Легкая (Light)", "Средняя (Medium)", "Сильная (Strong)"],
    "labels_visibility": ["Вкл (On)", "Выкл (Off)"],
    "show_preview": ["Да (Превью 2x2)", "Нет (Один кадр)"],
    "focus_stacking": ["Включено (Всё резко)", "Выключено (Боке)"],
    "lens_match_mode": ["Визуально (Feel)", "Строго (Strict)"],
    "language": ["Русский (ru)", "English (en)"],
    "platform": ["Web", "iOS", "Android"],
    "type": ["Photo", "Illustration"],
    "layout": ["2x3 grid", "3x2 grid", "3 horizontal panels", "2x2 grid"],
    # Added LENS options for Item 33
    "lens": ["16mm (Очень широкий)", "24mm (Архитектурный)", "35mm (Глаз человека)", "50mm (Стандарт)", "85mm (Портрет)", "200mm (Телевик)"],
}

DEFAULT_ENUM_VALUE = {
    "aspect_ratio": "9:16 (Stories / Reels)",
    "intensity": "Средняя (Medium)",
    "level": "Средняя (Medium)",
    "language": "Русский (ru)",
    "labels_visibility": "Выкл (Off)",
    "show_preview": "Нет (Один кадр)",
    "focus_stacking": "Выключено (Боке)",
    "lens_match_mode": "Визуально (Feel)",
    "platform": "Web",
    "type": "Photo",
    "layout": "2x3 grid",
    "lens": "24mm (Архитектурный)",
}

# --- C. ATTACHMENT CONFIGURATION ---
IMAGE_FILE_EXTS = ["png", "jpg", "jpeg", "webp"]

ATTACHMENT_VARS = {
    "image_1", "image_2",
    "model_image", "clothing_image", "footwear_image", "accessory_image",
    "element_1", "element_2",
    "person_image",
    "people_links"
}

PROMPT_FIELD_OVERRIDES = {
    "studio_portrait": {"person": {"attachment": True, "default_src": "Файл"}},
    "semantic_replacement": {"new_object": {"attachment": True, "default_src": "Ссылка / описание"}},
    # MOCKUP UPDATE: object_type is now attachable
    "mockup_generation": {
        "object_type": {"attachment": True, "default_src": "Файл"},
        "image_1": {"attachment": True, "default_src": "Файл"} # Forcing logo/design input
    },
    "knolling_photography": {"object": {"attachment": True, "default_src": "Файл", "multi": True}},
    "logo_creative": {"imagery": {"attachment": True, "default_src": "Ссылка / описание", "optional": True}},
    "character_sheet": {"description": {"attachment": True, "default_src": "Файл"}},
    "sticker_pack": {"character": {"attachment": True, "default_src": "Файл"}},
    "comic_page": {"character": {"attachment": True, "default_src": "Файл"}},
    "storyboard_sequence": {"character_description": {"attachment": True, "default_src": "Файл"}},
    "seamless_pattern": {"theme": {"attachment": True, "default_src": "Ссылка / описание"}},
    "isometric_room": {"room": {"attachment": True, "default_src": "Файл"}},
    "cinematic_atmosphere": {"subject": {"attachment": True, "default_src": "Файл"}},
    "technical_blueprint": {"object": {"attachment": True, "default_src": "Файл"}},
    "exploded_view": {"object": {"attachment": True, "default_src": "Файл"}},
    "anatomical_infographic": {"subject": {"attachment": True, "default_src": "Файл"}},
    "macro_extreme": {"object": {"attachment": True, "default_src": "Файл"}},
    "youtube_thumbnail": {"object": {"attachment": True, "default_src": "Файл"}},
}

OPTIONAL_FIELD_TOGGLES = {
    ("total_look_builder", "footwear_image"): {"label": "Добавить обувь", "default": True},
    ("total_look_builder", "accessory_image"): {"label": "Добавить аксессуар", "default": False},
    ("logo_creative", "imagery"): {"label": "Добавить образ-символ", "default": False},
    ("macro_extreme", "additional_details"): {"label": "Добавить: Дополнительные детали", "default": False},
}

# --- D. HELPERS ---
def _field_override(prompt_id, var_name):
    pid = (prompt_id or "").strip()
    v = (var_name or "").lower().strip()
    return (PROMPT_FIELD_OVERRIDES.get(pid) or {}).get(v, {})

def is_attachment_var(var_name, prompt_id=None):
    v = (var_name or "").lower().strip()
    ov = _field_override(prompt_id, v)
    if isinstance(ov, dict) and ov.get("attachment") is True:
        return True
    return (v in ATTACHMENT_VARS) or v.startswith("image_") or v.endswith("_image")

def field_default_src(var_name, prompt_id=None):
    ov = _field_override(prompt_id, var_name)
    return ov.get("default_src") if isinstance(ov, dict) else None

def attachment_multi_required(var_name, prompt_id=None):
    ov = _field_override(prompt_id, var_name)
    if isinstance(ov, dict) and "multi" in ov:
        return bool(ov["multi"])
    return var_name == "people_links"

def enum_default_index(var: str) -> int:
    opts = ENUM_OPTIONS.get(var, [])
    desired = DEFAULT_ENUM_VALUE.get(var)
    if desired in opts: return opts.index(desired)
    return 0

def get_placeholder(var: str, prompt_id: str) -> str:
    specific = SPECIFIC_HINTS.get(prompt_id, {}).get(var, {})
    if "ph" in specific:
        return specific["ph"]
    return EXAMPLES_DB.get(var, {}).get("ph", "Введите значение...")

def get_help(var: str, prompt_id: str) -> str:
    specific = SPECIFIC_HINTS.get(prompt_id, {}).get(var, {})
    if "help" in specific:
        return specific["help"]
    return EXAMPLES_DB.get(var, {}).get(
        "help", 
        "Заполните это поле. Можно использовать русский язык."
    )

def has_cyrillic(s: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", s))


_SPACE_RUN_RE = re.compile(r"[ \t\r\f\v]+")


def normalize_translate_cache_key(text: str) -> str:
    """Нормализует текст для ключа кэша перевода (консервативно).

    - strip()
    - нормализует переносы строк в \n
    - схлопывает пробелы/табы внутри строк (не трогая границы строк)
    """
    raw = "" if text is None else str(text)
    raw = unicodedata.normalize("NFKC", raw)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""
    lines = raw.split("\n")
    lines = [_SPACE_RUN_RE.sub(" ", line.strip()) for line in lines]
    return "\n".join(lines)

def _push_run_notice(msg: str) -> None:
    """Collect non-fatal runtime notices for the current generation run."""
    lst = st.session_state.get("_nb_run_notices")
    if isinstance(lst, list) and msg and msg not in lst:
        lst.append(msg)

def _add_run_notice(msg: str, level: str = "info") -> None:
    """Backward-compatible wrapper used by some call sites."""
    _push_run_notice(msg)


def _approx_utf8_size(s: str) -> int:
    try:
        return len((s or "").encode("utf-8", errors="ignore"))
    except Exception:
        return len(s or "")


def _translate_cache_get(cache: dict, key: str) -> str | None:
    if not isinstance(cache, dict):
        return None
    v = cache.get(key)
    if not isinstance(v, str):
        return None
    # Refresh LRU order (dict preserves insertion order).
    try:
        cache.pop(key, None)
        cache[key] = v
    except Exception:
        pass
    return v


def _translate_cache_put(cache: dict, key: str, value: str) -> None:
    """Insert into the per-session translate cache with entry and byte caps."""
    if not isinstance(cache, dict) or not isinstance(key, str) or not isinstance(value, str):
        return

    # Track approximate UTF-8 size in session state.
    cur_bytes = st.session_state.get("_nb_translate_cache_bytes")
    cur_bytes = int(cur_bytes) if isinstance(cur_bytes, int) else 0

    old = cache.get(key)
    if isinstance(old, str):
        cur_bytes -= _approx_utf8_size(key) + _approx_utf8_size(old)
        try:
            cache.pop(key, None)
        except Exception:
            pass

    cache[key] = value
    cur_bytes += _approx_utf8_size(key) + _approx_utf8_size(value)

    # Evict oldest entries until within caps.
    while len(cache) > max(1, int(TRANSLATE_CACHE_MAX_ENTRIES)) or cur_bytes > max(0, int(TRANSLATE_CACHE_MAX_BYTES)):
        try:
            oldest_key = next(iter(cache))
        except StopIteration:
            break
        oldest_val = cache.pop(oldest_key, None)
        if isinstance(oldest_val, str):
            cur_bytes -= _approx_utf8_size(oldest_key) + _approx_utf8_size(oldest_val)

    st.session_state["_nb_translate_cache_bytes"] = max(0, int(cur_bytes))


def format_bytes(n: int) -> str:
    """Human-readable bytes formatter (B/KB/MB/GB)."""
    try:
        n_int = int(n)
    except Exception:
        n_int = 0
    n_int = max(0, n_int)
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(n_int)
    idx = 0
    while size >= 1024.0 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(size)}{units[idx]}"
    return f"{size:.1f}{units[idx]}"



def safe_translate_to_en(text: str, var_name: str) -> Tuple[str, bool]:
    """Translate RU->EN safely. Returns (translated_or_original, ok)."""
    raw = "" if text is None else str(text)

    # Enum-like values: keep the chosen option stable (do not translate UI labels).
    if raw.startswith("Optional:") and "(" in raw and raw.endswith(")"):
        m = re.match(r"Optional:\s*(.*?)\s*\((.*?)\)\s*$", raw)
        if m:
            raw = m.group(1).strip() or raw
    if raw.startswith("Выберите:") and "(" in raw and raw.endswith(")"):
        m = re.match(r"Выберите:\s*(.*?)\s*\((.*?)\)\s*$", raw)
        if m:
            raw = m.group(1).strip() or raw

    # URL-like values should not be translated.
    s = raw.strip().lower()
    if s.startswith(("http://", "https://", "www.")):
        return raw, True

    # No translation needed.
    if not has_cyrillic(raw):
        return raw, True

    if not st.session_state.get("nb_translation_enabled", TRANSLATION_ENABLED_DEFAULT):
        # User opted out; keep original.
        return raw, True

    if len(raw) > TRANSLATE_MAX_CHARS:
        _push_run_notice(
            f"Перевод пропущен: поле '{var_name}' слишком длинное ({len(raw)} символов, лимит {TRANSLATE_MAX_CHARS})."
        )
        return raw, False

    tr = get_translator_en()
    if tr is None:
        _push_run_notice(f"Перевод пропущен: переводчик не доступен (поле '{var_name}').")
        return raw, False

    cache = st.session_state.setdefault("_nb_translate_cache", {})
    cache_key = normalize_translate_cache_key(raw)

    cached = _translate_cache_get(cache, cache_key)
    if cached is not None:
        return cached, True

    sem = get_translate_semaphore()
    if not sem.acquire(timeout=TRANSLATE_ACQUIRE_TIMEOUT_SEC):
        _push_run_notice(f"Перевод пропущен: переводчик перегружен (поле '{var_name}').")
        return raw, False

    released = False

    def _release(_fut=None) -> None:
        nonlocal released
        if released:
            return
        released = True
        try:
            sem.release()
        except Exception:
            pass

    fut = None
    try:
        # Usage counters are metadata-only; ignore failures.
        try:
            counters = st.session_state.get("_nb_usage_counters")
            if isinstance(counters, dict):
                counters["translate_calls"] = int(counters.get("translate_calls", 0)) + 1
                counters["translate_chars"] = int(counters.get("translate_chars", 0)) + len(raw)
        except Exception:
            pass

        ex = get_translate_executor()
        fut = ex.submit(tr.translate, cache_key)
        fut.add_done_callback(_release)

        translated = fut.result(timeout=TRANSLATE_TIMEOUT_SEC)
        if not isinstance(translated, str) or not translated.strip():
            _push_run_notice(f"Перевод не удался: пустой ответ (поле '{var_name}').")
            return raw, False

        _translate_cache_put(cache, cache_key, translated)
        return translated, True

    except FuturesTimeoutError:
        try:
            if fut is not None:
                fut.cancel()
        except Exception:
            pass
        _push_run_notice(f"Перевод превысил таймаут для поля '{var_name}'. Используется исходный текст.")
        return raw, False

    except Exception as e:
        _push_run_notice(f"Перевод не удался для поля '{var_name}': {type(e).__name__}. Используется исходный текст.")
        return raw, False

    finally:
        # If submit failed before the callback was attached, release the token here.
        if not released and fut is None:
            _release()


def translate_user_inputs_to_en(user_inputs: dict) -> Tuple[dict, List[str]]:
    """Translate all eligible fields RU->EN with a global time budget to avoid N*timeout stalls."""
    i_en: dict = {}
    fallback_keys: List[str] = []

    # Fast path: if translation is disabled, do nothing (but still return original values).
    translation_enabled = bool(st.session_state.get("nb_translation_enabled", TRANSLATION_ENABLED_DEFAULT))

    cache = st.session_state.setdefault("_nb_translate_cache", {})

    # Collect translation tasks keyed by cache_key (dedupe within the run).
    key_order: List[str] = []
    field_to_key: dict = {}
    key_to_raw: dict = {}
    key_to_var: dict = {}

    for k, v in (user_inputs or {}).items():
        sv = "" if v is None else str(v)

        # Don't translate free-text fields (they can be intentionally multilingual).
        if k in ("text", "text_content"):
            i_en[k] = v
            continue

        # Don't translate file placeholders.
        if sv.startswith("[") and ("FILE" in sv or "ATTACHED" in sv):
            i_en[k] = v
            continue

        # Enum-like values: keep the chosen option stable.
        raw = sv
        if raw.startswith("Optional:") and "(" in raw and raw.endswith(")"):
            m = re.match(r"Optional:\s*(.*?)\s*\((.*?)\)\s*$", raw)
            if m:
                raw = m.group(1).strip() or raw
        if raw.startswith("Выберите:") and "(" in raw and raw.endswith(")"):
            m = re.match(r"Выберите:\s*(.*?)\s*\((.*?)\)\s*$", raw)
            if m:
                raw = m.group(1).strip() or raw

        # URL-like values should not be translated.
        s = raw.strip().lower()
        if s.startswith(("http://", "https://", "www.")) or not raw:
            i_en[k] = v
            continue

        # No translation needed.
        if not has_cyrillic(raw) or not translation_enabled:
            i_en[k] = v
            continue

        if len(raw) > TRANSLATE_MAX_CHARS:
            _push_run_notice(
                f"Перевод пропущен: поле '{k}' слишком длинное ({len(raw)} символов, лимит {TRANSLATE_MAX_CHARS})."
            )
            i_en[k] = v
            fallback_keys.append(k)
            continue

        cache_key = normalize_translate_cache_key(raw)
        cached = _translate_cache_get(cache, cache_key)
        if cached is not None:
            i_en[k] = cached
            continue

        # Defer translation; we'll submit with a global budget below.
        field_to_key[k] = cache_key
        key_to_var.setdefault(cache_key, k)
        key_to_raw.setdefault(cache_key, raw)
        if cache_key not in key_order:
            key_order.append(cache_key)

    if not key_order:
        return i_en, fallback_keys

    tr = get_translator_en()
    if tr is None:
        for k in field_to_key:
            fallback_keys.append(k)
        _push_run_notice("Перевод пропущен: переводчик не доступен.")
        for k, v in (user_inputs or {}).items():
            i_en.setdefault(k, v)
        return i_en, fallback_keys

    sem = get_translate_semaphore()
    ex = get_translate_executor()

    deadline = time.monotonic() + float(TRANSLATE_GLOBAL_BUDGET_SEC)
    max_inflight = max(1, int(TRANSLATE_MAX_CONCURRENCY))

    results: dict = {}  # cache_key -> (translated, ok)

    inflight: dict = {}  # cache_key -> future
    idx = 0

    def _make_release_cb() -> callable:
        released = {"v": False}

        def _cb(_fut=None) -> None:
            if released["v"]:
                return
            released["v"] = True
            try:
                sem.release()
            except Exception:
                pass

        return _cb

    while time.monotonic() < deadline and (idx < len(key_order) or inflight):
        # Fill inflight up to concurrency.
        while idx < len(key_order) and len(inflight) < max_inflight and time.monotonic() < deadline:
            key = key_order[idx]
            idx += 1

            # Avoid resubmitting if already resolved.
            if key in results:
                continue

            if not sem.acquire(timeout=TRANSLATE_ACQUIRE_TIMEOUT_SEC):
                # Overloaded: fall back for this key.
                results[key] = (key_to_raw.get(key, ""), False)
                _push_run_notice(f"Перевод пропущен: переводчик перегружен (поле '{key_to_var.get(key, '?')}').")
                continue

            # Usage counters are metadata-only; ignore failures.
            try:
                counters = st.session_state.get("_nb_usage_counters")
                if isinstance(counters, dict):
                    counters["translate_calls"] = int(counters.get("translate_calls", 0)) + 1
                    counters["translate_chars"] = int(counters.get("translate_chars", 0)) + len(key_to_raw.get(key, ""))
            except Exception:
                pass

            fut = ex.submit(tr.translate, key)
            fut.add_done_callback(_make_release_cb())
            inflight[key] = fut

        if not inflight:
            break

        remaining = max(0.0, deadline - time.monotonic())
        done, _ = futures_wait(list(inflight.values()), timeout=remaining, return_when=FIRST_COMPLETED)
        if not done:
            break

        for key, fut in list(inflight.items()):
            if fut not in done:
                continue
            try:
                translated = fut.result()
                if isinstance(translated, str) and translated.strip():
                    _translate_cache_put(cache, key, translated)
                    results[key] = (translated, True)
                else:
                    results[key] = (key_to_raw.get(key, ""), False)
                    _push_run_notice(f"Перевод не удался: пустой ответ (поле '{key_to_var.get(key, '?')}').")
            except Exception as e:
                results[key] = (key_to_raw.get(key, ""), False)
                _push_run_notice(
                    f"Перевод не удался для поля '{key_to_var.get(key, '?')}': {type(e).__name__}. Используется исходный текст."
                )
            inflight.pop(key, None)

    # Global budget expired: cancel inflight and fall back.
    for key, fut in list(inflight.items()):
        try:
            fut.cancel()
        except Exception:
            pass
        results.setdefault(key, (key_to_raw.get(key, ""), False))
        _push_run_notice(f"Перевод превысил таймаут для поля '{key_to_var.get(key, '?')}'. Используется исходный текст.")

    # Fill outputs for fields that were deferred.
    for field, key in field_to_key.items():
        translated, ok = results.get(key, (key_to_raw.get(key, ""), False))
        i_en[field] = translated
        if not ok and has_cyrillic(key_to_raw.get(key, "")):
            fallback_keys.append(field)

    # Preserve non-translated fields that might not have been set above.
    for k, v in (user_inputs or {}).items():
        i_en.setdefault(k, v)

    return i_en, fallback_keys


def _redact_filename(name: str) -> str:
    """Скрывает пользовательское имя файла в UI."""
    try:
        _, ext = os.path.splitext(name or "")
        digest = hashlib.sha256((name or "").encode("utf-8", errors="ignore")).hexdigest()[:12]
        return f"file-{digest}{ext}"
    except Exception:
        return "file-redacted"




# --- Upload signature validation (lightweight) ---

def _read_file_head(uploaded_file, n: int = 32) -> bytes:
    """Read the first n bytes without consuming the stream (best-effort)."""
    if uploaded_file is None:
        return b""
    pos = None
    try:
        pos = uploaded_file.tell()
    except Exception:
        pos = None
    try:
        head = uploaded_file.read(n)
    except Exception:
        head = b""
    finally:
        try:
            if pos is not None:
                uploaded_file.seek(pos)
            else:
                uploaded_file.seek(0)
        except Exception:
            pass
    return head or b""


def _detect_image_type_from_header(header: bytes) -> str | None:
    """Detect image type from magic bytes. Returns: 'png' | 'jpeg' | 'webp' | None."""
    if not header:
        return None
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if len(header) >= 12 and header[0:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    return None



def _is_allowed_image_upload(uploaded_file, allowed_exts: set[str]) -> bool:
    """Validate that the uploaded file is a real PNG/JPEG/WebP (header check).

    We do not trust the filename extension alone.
    """
    name = getattr(uploaded_file, 'name', '') or ''
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    header = _read_file_head(uploaded_file, 32)
    detected = _detect_image_type_from_header(header)
    if detected is None:
        return False

    # Normalize detected to common extensions
    if detected == 'jpeg':
        detected_ext = 'jpg'
    else:
        detected_ext = detected

    # If extension is known, require it matches detected format (jpg/jpeg treated as one)
    if ext:
        if ext == 'jpeg':
            ext = 'jpg'
        if ext in allowed_exts and ext != detected_ext:
            return False

    return detected_ext in allowed_exts


def _uploaded_file_size(uploaded_file) -> int:
    """
    Determine file size without copying contents into memory.
    """
    try:
        size = getattr(uploaded_file, "size", None)
        if isinstance(size, int):
            return max(0, size)
    except Exception:
        pass

    try:
        if hasattr(uploaded_file, "seek") and hasattr(uploaded_file, "tell"):
            current_pos = uploaded_file.tell()
            uploaded_file.seek(0, 2)   # SEEK_END
            size = uploaded_file.tell()
            uploaded_file.seek(current_pos)
            return size
    except Exception:
        pass

    try:
        if hasattr(uploaded_file, "getbuffer"):
            return len(uploaded_file.getbuffer())
    except Exception:
        pass

    return 0


def _verify_image_upload(uploaded_file) -> bool:
    """Verify image structure using PIL when available."""
    if Image is None or uploaded_file is None:
        return True
    pos = None
    try:
        pos = uploaded_file.tell()
    except Exception:
        pos = None
    try:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        img = Image.open(uploaded_file)
        img.verify()
        return True
    except Exception:
        return False
    finally:
        try:
            if pos is not None:
                uploaded_file.seek(pos)
        except Exception:
            pass

def redact_payload_for_ui(payload: dict) -> dict:
    """Возвращает копию payload, безопасную для вывода в st.json."""
    if not isinstance(payload, dict):
        return payload
    out = dict(payload)
    files = out.get("files")
    if isinstance(files, dict):
        safe_files = {}
        for k, v in files.items():
            if isinstance(v, list):
                safe_files[k] = [_redact_filename(x) for x in v]
            else:
                safe_files[k] = v
        out["files"] = safe_files
    return out


def normalize_special_vars(d: dict, lang="en") -> dict:
    """Нормализует спец-поля так, чтобы они читались человеком.

    Важно: значения зависят от lang, чтобы в EN промпт не попадали русские подписи.
    """
    out = dict(d)
    is_ru = str(lang).lower().startswith("ru")

    # lens_match_mode
    if "lens_match_mode" in out:
        mode = str(out.get("lens_match_mode", "")).lower()
        feel = ("feel" in mode) or ("визуально" in mode) or ("ощущ" in mode)
        if is_ru:
            out["lens_match_mode"] = "совпади по ощущению" if feel else "строго по фокусному"
        else:
            out["lens_match_mode"] = "match lens look (focal-length feel)" if feel else "match focal length strictly"

    # show_preview
    if "show_preview" in out:
        val = str(out.get("show_preview", "")).lower()
        yes = ("да" in val) or ("yes" in val) or ("on" in val) or ("true" in val)
        if is_ru:
            out["show_preview"] = "превью 2×2" if yes else "один кадр"
        else:
            out["show_preview"] = "2x2 preview grid" if yes else "single frame"

    # labels_visibility
    if "labels_visibility" in out:
        val = str(out.get("labels_visibility", "")).lower()
        on = ("вкл" in val) or ("on" in val) or ("yes" in val) or ("да" in val) or ("true" in val)
        if is_ru:
            out["labels_visibility"] = "подписи включены" if on else "без подписей"
        else:
            out["labels_visibility"] = "labels on" if on else "no labels"

    # focus_stacking
    if "focus_stacking" in out:
        val = str(out.get("focus_stacking", "")).lower()
        on = ("включ" in val) or ("on" in val) or ("yes" in val) or ("да" in val) or ("true" in val)
        if is_ru:
            out["focus_stacking"] = "включено (всё в резкости)" if on else "выключено (боке)"
        else:
            out["focus_stacking"] = "on (everything in focus)" if on else "off (bokeh)"

    return out

def should_add_cyrillic_lock(inputs: dict) -> bool:
    for k in ["text", "text_content"]:
        if k in inputs and has_cyrillic(str(inputs.get(k, ""))): return True
    if str(inputs.get("language", "")).strip().lower() == "ru": return True
    if "Русский" in str(inputs.get("language", "")): return True
    return False

def cleanup_optional_prompt(text, prompt_id, disabled_vars, lang):
    if not text or not disabled_vars:
        return (text or "").strip()

    t = text

    if prompt_id == "total_look_builder":
        if "accessory_image" in disabled_vars:
            t = re.sub(r"\s*(Accessory|Аксессуар):\s*\.(\s*)", " ", t, flags=re.IGNORECASE)
        if "footwear_image" in disabled_vars:
            t = re.sub(r"\s*(Footwear|Обувь):\s*\.(\s*)", " ", t, flags=re.IGNORECASE)

    if prompt_id == "logo_creative" and "imagery" in disabled_vars:
        term = "imagery" if lang.startswith("en") else "образ"
        t = re.sub(rf"\b{term}\b\s*,\s*", "", t, flags=re.IGNORECASE)

    if prompt_id == "macro_extreme" and "additional_details" in disabled_vars:
        if lang.startswith("ru"):
            t = re.sub(r"\s*Дополнительные детали:\s*[^;]*;\s*", " ", t, flags=re.IGNORECASE)
        else:
            t = re.sub(r"\s*Additional details:\s*[^;]*;\s*", " ", t, flags=re.IGNORECASE)

    t = re.sub(r"\s{2,}", " ", t)
    return t.replace(" .", ".").replace(" ,", ",").strip()


def _store_last_generate_error(prompt_id: str, exc: BaseException) -> None:
    """Store the last prompt-generation error in session state for UI display."""
    tb = traceback.format_exc()
    st.session_state["_nb_last_generate_error"] = {
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "prompt_id": prompt_id,
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": (tb[-8000:] if tb else ""),
    }


def render_last_generate_error_ui(slot) -> None:
    """Render the last stored generation error into the provided Streamlit slot."""
    err = st.session_state.get("_nb_last_generate_error")
    if not err:
        return
    with slot.container():
        with st.expander("⚠️ Детали последней ошибки генерации", expanded=False):
            st.markdown(f"**Время:** {err.get('at', '-')}")
            st.markdown(f"**Задача (ID):** `{err.get('prompt_id', '-')}`")
            st.markdown(f"**Тип:** {err.get('type', '-')}")
            if err.get("message"):
                st.markdown(f"**Сообщение:** {err.get('message')}")
            if err.get("traceback"):
                st.code(err.get("traceback", ""), language="text")
            if st.button("Очистить", key="clear_last_generate_error"):
                st.session_state.pop("_nb_last_generate_error", None)
                st.rerun()

# =========================================================
# 4) ENGINE LOADING
# =========================================================

def _prompts_mtime_ns(path: Path) -> int:
    try:
        return int(path.stat().st_mtime_ns)
    except Exception:
        return 0


@st.cache_resource
def _get_prompt_manager(prompts_path: str, mtime_ns: int) -> PromptManager:
    # `mtime_ns` is only for cache invalidation.
    return PromptManager(prompts_path)


manager = (
    _get_prompt_manager(str(PROMPTS_PATH), _prompts_mtime_ns(PROMPTS_PATH))
    if PROMPTS_PATH.exists()
    else None
)
if not manager:
    st.error("❌ Файл `prompts.json` не найден!")
    st.stop()
all_prompts = manager.prompts

# =========================================================
# 5) BANNER & INSTRUCTION
# =========================================================
st.markdown(
    """<div class="main-banner">
    <h1>🍌 Nano Banano Pro</h1>
    <p>Твой карманный AI-креативщик</p>
    </div>""", unsafe_allow_html=True
)

with st.expander("ℹ️ Инструкция: Как пользоваться"):
    st.markdown("""
    ### ⚡ Быстрый старт
    1. **Меню слева:** Выбери задачу (например, "Замена фона"). 
       - *Совет:* Чтобы увидеть весь список сразу, выбери категорию **"📂 ВСЕ ЗАДАЧИ (1-40)"**.
    2. **Заполни поля:**
       - **Текст:** Пиши коротко (можно на русском).
       - **Фото/Ссылки:** Переключайся между вкладками **"Ссылка"** и **"Файл"**.
    3. **Настройки:** "Режим негатива" (Default обычно подходит).
    4. **Кнопка:** Жми **🍌 Сгенерировать Промпт**.
    """)

# =========================================================
# 6) SIDEBAR & NAVIGATION
# =========================================================
if "history" not in st.session_state: st.session_state["history"] = []
if "history_counter" not in st.session_state: st.session_state["history_counter"] = 0

def save_to_history(task, prompt_en, prompt_ru, payload=None):
    st.session_state["history_counter"] += 1
    # Не сохраняем raw payload в историю: там могут быть имена файлов / ключи,
    # и он заметно раздувает session_state.
    st.session_state["history"].insert(0, {
        "task": task, 
        "en": prompt_en, 
        "ru": prompt_ru, 
        "time": datetime.datetime.now().strftime("%H:%M"), 
        "id": st.session_state["history_counter"]
    })
    if len(st.session_state["history"]) > 50: st.session_state["history"].pop()

with st.sidebar:
    st.markdown("### 🍌 PRO MENU")
    tab_menu, tab_history = st.tabs(["Меню", "История"])

# Placeholder used later to render last generation error details in the sidebar.
last_error_details_slot = None

with tab_menu:
    st.write(" ")

    # MAPPING CATEGORIES
    PROMPT_TO_CATEGORY = {
        "upscale_restore": "🛠️ Редактирование", "old_photo_restore": "🛠️ Редактирование", "background_change": "🛠️ Редактирование", "camera_angle_change": "🛠️ Редактирование", "object_removal": "🛠️ Редактирование", "object_addition": "🛠️ Редактирование", "semantic_replacement": "🛠️ Редактирование", "scene_relighting": "🛠️ Редактирование", "scene_composite": "🛠️ Редактирование",
        "studio_portrait": "📸 Фотореализм & Люди", "face_swap": "📸 Фотореализм & Люди", "expression_change": "📸 Фотореализм & Люди", "pose_change": "📸 Фотореализм & Люди", "cloth_swap": "📸 Фотореализм & Люди", "total_look_builder": "📸 Фотореализм & Люди", "team_composite": "📸 Фотореализм & Люди", "macro_extreme": "📸 Фотореализм & Люди",
        "product_card": "🎨 Дизайн & Маркетинг", "mockup_generation": "🎨 Дизайн & Маркетинг", "environmental_text": "🎨 Дизайн & Маркетинг", "knolling_photography": "🎨 Дизайн & Маркетинг", "logo_creative": "🎨 Дизайн & Маркетинг", "logo_stylization": "🎨 Дизайн & Маркетинг", "ui_design": "🎨 Дизайн & Маркетинг", "text_design": "🎨 Дизайн & Маркетинг", "seamless_pattern": "🎨 Дизайн & Маркетинг", "technical_blueprint": "🎨 Дизайн & Маркетинг", "exploded_view": "🎨 Дизайн & Маркетинг", "anatomical_infographic": "🎨 Дизайн & Маркетинг",
        "image_restyling": "🖍️ Иллюстрация & Арт", "sketch_to_photo": "🖍️ Иллюстрация & Арт", "character_sheet": "🖍️ Иллюстрация & Арт", "sticker_pack": "🖍️ Иллюстрация & Арт", "comic_page": "🖍️ Иллюстрация & Арт",
        "interior_design": "🏗️ Архитектура & Интерьер", "architecture_exterior": "🏗️ Архитектура & Интерьер", "isometric_room": "🏗️ Архитектура & Интерьер",
        "storyboard_sequence": "🎬 Видео & YouTube", "cinematic_atmosphere": "🎬 Видео & YouTube", "youtube_thumbnail": "🎬 Видео & YouTube"
    }
    DEFAULT_CAT = "🔹 Прочее"
    ALL_TASKS_LABEL = "📂 ВСЕ ЗАДАЧИ (1-40)"

    # Сортировка категорий
    CAT_ORDER_PRIORITY = [
        ALL_TASKS_LABEL,
        "🛠️ Редактирование",
        "📸 Фотореализм & Люди",
        "🎨 Дизайн & Маркетинг",
        "🖍️ Иллюстрация & Арт",
        "🏗️ Архитектура & Интерьер",
        "🎬 Видео & YouTube",
        DEFAULT_CAT
    ]

    search_q = st.text_input("🔍 Поиск", key="sidebar_search", placeholder="Название, ID или описание...")
    filtered_items = []

    if search_q:
        st.caption(f"Результаты: «{search_q}»")
        for pid, data in all_prompts.items():
            haystack = (pid + str(data.get("title")) + str(data.get("description"))).lower()
            if search_q.lower() in haystack:
                filtered_items.append((data.get("title", pid), pid))
        filtered_items.sort(key=lambda x: x[0])
    else:
        raw_cats = set(PROMPT_TO_CATEGORY.values())
        if any(p not in PROMPT_TO_CATEGORY for p in all_prompts): raw_cats.add(DEFAULT_CAT)
        
        sorted_cats = sorted(list(raw_cats), key=lambda x: CAT_ORDER_PRIORITY.index(x) if x in CAT_ORDER_PRIORITY else 99)
        final_cat_options = [ALL_TASKS_LABEL] + sorted_cats

        selected_cat = st.selectbox("📂 Категория:", final_cat_options, key="selected_category_ui")
        
        if selected_cat == ALL_TASKS_LABEL:
            target_ids = list(all_prompts.keys())
        else:
            target_ids = [p for p in all_prompts if PROMPT_TO_CATEGORY.get(p, DEFAULT_CAT) == selected_cat]

        for pid in target_ids:
            if pid in all_prompts:
                filtered_items.append((all_prompts[pid].get("title", pid), pid))
        filtered_items.sort(key=lambda x: x[0])

    if not filtered_items:
        if all_prompts:
            first_id = list(all_prompts.keys())[0]
            filtered_items = [(all_prompts[first_id].get("title"), first_id)]
    
    current_sel = st.session_state.get("selected_prompt_id")
    def_idx = 0
    ids = [i[1] for i in filtered_items]
    if current_sel in ids:
        def_idx = ids.index(current_sel)

    sel_label = st.selectbox("✨ Задача:", [i[0] for i in filtered_items], index=def_idx, key="selected_label_sidebar")
    selected_id = next((pid for lbl, pid in filtered_items if lbl == sel_label), ids[0])
    st.session_state["selected_prompt_id"] = selected_id

    # PREVIEW
    current_prompt_data = all_prompts[selected_id]
    image_path = resolve_preview_image(selected_id)
    
    st.markdown("---")
    with st.container(border=True):
        if image_path: st.image(image_path, use_container_width=True)
        else: st.markdown(f"<div style='text-align:center; opacity:0.5; padding:10px;'>🖼️ Нет превью</div>", unsafe_allow_html=True)
        st.info(current_prompt_data.get("description", "Нет описания"))

    st.markdown("### ⚙️ Настройки")
    neg_category_label = st.selectbox("Негатив (стиль):", NEG_CATEGORY_LABELS, index=0, key="neg_category_label")
    with st.expander("Дополнительно", expanded=False):
        allow_multi_images = st.checkbox("Multi-files (Beta)", False, key="allow_multi_images")
        api_enabled = st.checkbox("API Mode (JSON)", False, key="api_enabled")

        # Details of the last generation error (shown only if an error occurred)
        last_error_details_slot = st.empty()
        render_last_generate_error_ui(last_error_details_slot)

    # ---------------------------------------------------------
    # 🌐 Автоперевод RU→EN (вынесено вниз, чтобы не перекрывать превью)
    # ---------------------------------------------------------
    st.markdown("---")
    st.markdown("#### 🌐 Автоперевод RU→EN")
    st.checkbox(
        "Включить автоперевод",
        key="nb_translation_enabled",
        value=TRANSLATION_ENABLED_DEFAULT,
        help=(
            "Если включено, кириллица в полях для EN будет переводиться с помощью внешнего сервиса "
            "(deep_translator / Google Translator). Не вводите персональные данные, секреты, ключи "
            "или конфиденциальную информацию. Если отключено, текст будет использоваться как есть."
        ),
    )


# =========================================================
# 10) MAIN FORM CONSTRUCTION
# =========================================================
st.markdown(f"## {current_prompt_data.get('title', selected_id)}")

template_en = current_prompt_data["prompt_en"]
template_ru = current_prompt_data["prompt_ru"]
req_vars = sorted(set(re.findall(r"\[([a-zA-Z0-9_]+)\]", template_en) + re.findall(r"\[([a-zA-Z0-9_]+)\]", template_ru)))

user_inputs = {}
uploaded_files = {} 
image_urls = {}    
opt_disabled = set()
uploads_total_files = 0
uploads_total_bytes = 0
bad_files: list[str] = []
MULTILINE_TEXT_VARS = {"scene", "scene_description", "action_sequence", "text", "description", "list"}

if not req_vars:
    st.info("✅ Переменные не требуются.")
else:
    # UI metadata can override layout behavior for specific prompts.
    ui_meta = current_prompt_data.get("ui", {}) if isinstance(current_prompt_data, dict) else {}

    # 1) Force extra vars into the form (e.g., allow uploading logo even if template doesn't reference it).
    force_vars = ui_meta.get("force_vars", [])
    if isinstance(force_vars, list):
        for fv in force_vars:
            if isinstance(fv, str) and fv and fv not in req_vars:
                req_vars.append(fv)

    # 2) Reorder vars for a better UX.
    var_order = ui_meta.get("var_order")
    if isinstance(var_order, list) and var_order:
        req_vars = [v for v in var_order if v in req_vars] + [v for v in req_vars if v not in var_order]
    elif "aspect_ratio" in req_vars:
        req_vars.remove("aspect_ratio")
        req_vars.insert(0, "aspect_ratio")


    cols = st.columns(2)
    for i, var in enumerate(req_vars):
        col = cols[i % 2]
        
        # Получаем красивые лейблы и подсказки (с учетом оверрайдов)
        label = VAR_MAP.get(var, f"Поле: {var}")
        
        # Получаем подсказки через функцию-хелпер, которая смотрит в SPECIFIC_HINTS
        ph = get_placeholder(var, selected_id)
        help_text = get_help(var, selected_id)

        # UI overrides from prompts.json metadata (minimal decoupling)
        if isinstance(ui_meta, dict):
            label_overrides = ui_meta.get("label_overrides", {})
            if isinstance(label_overrides, dict) and var in label_overrides:
                label = str(label_overrides[var])

            help_overrides = ui_meta.get("help_overrides", {})
            if isinstance(help_overrides, dict) and var in help_overrides:
                # Replace the base help text entirely for this field
                help_text = str(help_overrides[var]) if help_overrides[var] is not None else help_text

            help_append = ui_meta.get("help_append", {})
            if isinstance(help_append, dict) and var in help_append and help_append[var]:
                extra_hint = str(help_append[var])
                help_text = (help_text + "\n\n" + extra_hint) if help_text else extra_hint


        widget_key = f"{selected_id}__{var}"

        # 1. OPTIONAL TOGGLE (чекбокс "включить/выключить" для некоторых полей)
        if (selected_id, var) in OPTIONAL_FIELD_TOGGLES:
            cfg = OPTIONAL_FIELD_TOGGLES[(selected_id, var)]
            if not col.checkbox(cfg["label"], cfg["default"], key=f"{widget_key}_opt"):
                opt_disabled.add(var)
                user_inputs[var] = ""
                continue

        # 2. ATTACHMENT (File / Link)
        force_file_vars = []
        if isinstance(ui_meta, dict):
            force_file_vars = ui_meta.get("force_file_vars", []) or []
        is_forced_file_var = isinstance(force_file_vars, list) and var in force_file_vars

        if is_attachment_var(var, selected_id) or is_forced_file_var:
            col.markdown(f"**{label}**")
            # Default tab selection
            
            tab_link, tab_file = col.tabs(["🔗 Ссылка / Текст", "📁 Файл"])
            
            multi = allow_multi_images or attachment_multi_required(var, selected_id)
            
            with tab_link:
                if multi:
                    val = st.text_area("URL / описание",
                                       key=f"{widget_key}_txt",
                                       placeholder=ph,
                                       help=help_text,
                                       height=72,
                                       label_visibility="collapsed")
                else:
                    val = st.text_input("URL / описание",
                                        key=f"{widget_key}_txt",
                                        placeholder=ph,
                                        help=help_text,
                                        label_visibility="collapsed")

                if val:
                    user_inputs[var] = val
                    image_urls[var] = [x.strip() for x in val.split("\n") if x.strip()] if multi else [val.strip()]

            with tab_file:
                files = st.file_uploader("Выбрать файл(ы)...",
                                         type=IMAGE_FILE_EXTS,
                                         accept_multiple_files=multi,
                                         key=f"{widget_key}_file",
                                         label_visibility="collapsed",
                                         help=help_text)
                files = files if isinstance(files, list) else ([files] if files else [])

                if files:
                    ok_files = []
                    ok_sizes = []
                    too_big = []
                    for f in files:
                        if not f:
                            continue
                        size = _uploaded_file_size(f)
                        if size and size > UI_MAX_FILE_BYTES:
                            too_big.append((getattr(f, "name", "file"), int(size)))
                        else:
                            # Validate file signature (do not trust extension alone)
                            safe_name = _redact_filename(getattr(f, "name", "file"))
                            if not _is_allowed_image_upload(f, IMAGE_FILE_EXTS):
                                bad_files.append(f"{safe_name} — файл не похож на изображение PNG/JPG/WebP")
                                continue
                            if not _verify_image_upload(f):
                                bad_files.append(f"{safe_name} — изображение повреждено или имеет неверный формат")
                                continue
                            ok_files.append(f)
                            ok_sizes.append(int(size or 0))

                    if too_big:
                        limit_mb = UI_MAX_FILE_BYTES / (1024 * 1024)
                        msg = ", ".join([f"{n} ({s / (1024 * 1024):.1f}MB)" for n, s in too_big])
                        st.error(f"Файл(ы) слишком большие: {msg}. Лимит: {limit_mb:.1f}MB.")

                    if ok_files:
                        uploaded_files[var] = ok_files
                        uploads_total_files += len(ok_files)
                        uploads_total_bytes += sum(ok_sizes)
                        user_inputs[var] = "[ATTACHED]" if len(ok_files) > 1 else f"[FILE: {ok_files[0].name}]"
            if var not in user_inputs: user_inputs[var] = ""

        # 3. ENUM (Dropdown) + Custom Input Logic
        elif var in ENUM_OPTIONS:
            opts = ENUM_OPTIONS[var]
            selected_val = col.selectbox(label, opts, index=enum_default_index(var), key=widget_key, help=help_text)
            
            # --- CUSTOM ASPECT RATIO LOGIC ---
            if var == "aspect_ratio" and "Custom" in selected_val:
                custom_val = col.text_input("Введите свой формат (напр. 21:9)", key=f"{widget_key}_custom")
                user_inputs[var] = custom_val if custom_val else ""
            else:
                user_inputs[var] = selected_val
        
        # 4. TEXT
        else:
            if var in MULTILINE_TEXT_VARS:
                user_inputs[var] = col.text_area(label, key=widget_key, height=100, help=help_text)
            else:
                user_inputs[var] = col.text_input(label, key=widget_key, placeholder=ph, help=help_text)

st.markdown("---")

# Upload limits (across all attachment fields)
uploads_ok = True
if bad_files:
    st.error("⚠️ Некоторые файлы отклонены:\n- " + "\n- ".join(bad_files))
    uploads_ok = False
if uploads_total_files > UI_MAX_UPLOAD_FILES:
    st.error(
        f"⚠️ Слишком много загруженных файлов: {uploads_total_files}. "
        f"Максимум: {UI_MAX_UPLOAD_FILES}."
    )
    uploads_ok = False
if uploads_total_bytes > UI_MAX_TOTAL_UPLOAD_BYTES:
    st.error(
        f"⚠️ Суммарный размер всех файлов: {format_bytes(uploads_total_bytes)}. "
        f"Максимум: {format_bytes(UI_MAX_TOTAL_UPLOAD_BYTES)}."
    )
    uploads_ok = False

neg_mode_ui = st.selectbox("Режим негатива:", ["light (Mini)", "medium (Default)", "hard (Aggressive)"], index=1, key="neg_mode_ui")

# =========================================================
# 8) GENERATION LOGIC
# =========================================================
if st.button("🍌 Сгенерировать Промпт", use_container_width=True):
    # FUTURE_SAAS_HOOK: request identity + usage accounting (no-op by default).
    cfg = get_future_config()
    ctx = get_request_context()
    rec = get_usage_recorder()
    st.session_state["_nb_usage_counters"] = {"translate_calls": 0, "translate_chars": 0}

    if not uploads_ok:
        st.error("⚠️ Исправьте ошибки загрузки файлов (лимиты/размеры) и попробуйте снова.")
        st.stop()
    if not enforce_usage_limits(ctx, UsageAction.GENERATE_PROMPT, units=1):
        # NOTE: allow-all today. In future SaaS mode, this becomes a quota gate.
        st.error("⚠️ Слишком много запросов. Попробуйте позже.")
        st.stop()

    # Item 35 (YouTube Viral): object reference is optional.
    yt_object_empty = False
    if selected_id == "youtube_thumbnail" and not str(user_inputs.get("object", "")).strip():
        user_inputs["object"] = "."  # marker; will be removed from final prompt
        yt_object_empty = True

    missing = []
    for k, v in user_inputs.items():
        if k not in opt_disabled and not str(v).strip():
            # For mockup image_1, treat it as optional if text/url is empty? 
            # Or mandatory? Let's check. If user didn't upload or type url, it's missing.
            missing.append(VAR_MAP.get(k, k))
            
    if missing:
        st.error(f"⚠️ **Пожалуйста, заполните:** {', '.join(missing)}")
    else:
        try:
            st.session_state["_nb_run_notices"] = []

            with st.spinner("⏳ Думаем... (Перевод + Сборка)"):
                # 1. RU prompt generation
                i_ru = normalize_special_vars(user_inputs, "ru")
                
                # 2. EN prompt generation
                # Translate only where it makes sense; never hang UI; record any fallbacks.
                i_en, translate_fallback_keys = translate_user_inputs_to_en(user_inputs)

                if translate_fallback_keys:
                    _add_run_notice(
                        "Translation fallback was used for: " + ", ".join(sorted(set(translate_fallback_keys))) +
                        ". EN prompt may contain non-English values.",
                        level="warning",
                    )
                
                i_en = normalize_special_vars(i_en, "en")

                res_en = manager.generate(selected_id, "en", **i_en).strip()
                res_ru = manager.generate(selected_id, "ru", **i_ru).strip()
                
                # Cleanup optional parts
                res_en = cleanup_optional_prompt(res_en, selected_id, opt_disabled, "en")
                res_ru = cleanup_optional_prompt(res_ru, selected_id, opt_disabled, "ru")

                # Remove optional object reference sentence for Item 35 if user left it empty
                if yt_object_empty and selected_id == "youtube_thumbnail":
                    res_ru = re.sub(r"\s*Объект/референс:\s*\.\s*", " ", res_ru)
                    res_en = re.sub(r"\s*Object reference:\s*\.\s*", " ", res_en)
                    res_ru = re.sub(r"\s{2,}", " ", res_ru).strip()
                    res_en = re.sub(r"\s{2,}", " ", res_en).strip()

                if should_add_cyrillic_lock(user_inputs):
                    res_en += "\nCRITICAL: Render Cyrillic text EXACTLY as provided."
                
                # 3. Negative Prompt Logic
                gid = NEG_CATEGORY_PRESETS.get(neg_category_label) or ID_TO_GROUP.get(selected_id, 1)
                m_key = "Mini" if "light" in neg_mode_ui else ("Full" if "hard" in neg_mode_ui else "Plus")
                neg_en = NEG_GROUPS[gid][m_key]["en"]
                neg_ru = NEG_GROUPS[gid][m_key]["ru"]
                
                if selected_id in NEG_ADDONS:
                    neg_en += f", {NEG_ADDONS[selected_id]['en']}"
                    neg_ru += f", {NEG_ADDONS[selected_id]['ru']}"
                
                full_text = f"{res_en} --no {neg_en}"
                
                # 4. API Payload
                payload = None
                if api_enabled:
                    payload = {
                        "task_id": selected_id, 
                        "prompt": res_en, 
                        "negative": neg_en, 
                        "inputs": i_en, 
                        "files": {k:[f.name for f in v] for k,v in uploaded_files.items()}, 
                        "refs": image_urls
                    }

                save_to_history(current_prompt_data.get("title", selected_id), full_text, f"{res_ru} | NEG: {neg_ru}", payload)

                # FUTURE_SAAS_HOOK: record a single metadata-only usage event.
                try:
                    counters = st.session_state.get("_nb_usage_counters")
                    translate_calls = int(counters.get("translate_calls", 0)) if isinstance(counters, dict) else 0
                    translate_chars = int(counters.get("translate_chars", 0)) if isinstance(counters, dict) else 0
                    rec.record(
                        ctx,
                        make_event(
                            ctx=ctx,
                            action=UsageAction.GENERATE_PROMPT,
                            units=1,
                            meta={
                                "prompt_id": str(selected_id),
                                "api_mode": "1" if api_enabled else "0",
                                "output_chars": str(len(full_text or "")),
                                "translate_calls": str(translate_calls),
                                "translate_chars": str(translate_chars),
                            },
                        ),
                    )
                except Exception:
                    pass

            st.success("✅ Готово!")

            notices = st.session_state.get("_nb_run_notices", [])
            if notices:
                st.warning("⚠️ Перевод/обработка:\n- " + "\n- ".join(notices))
                # Reset for the next run to avoid leaking stale messages.
                st.session_state["_nb_run_notices"] = []
            

            
            t1, t2 = st.tabs(["🇺🇸 EN (Result)", "🇷🇺 RU (Инфо)"])
            with t1:
                st.code(full_text, language="text")
                st_copy_to_clipboard(full_text, "Копировать", key=f"res_{hash(full_text)}")

                def _on_download():
                    try:
                        rec.record(
                            ctx,
                            make_event(
                                ctx=ctx,
                                action=UsageAction.DOWNLOAD_RESULT,
                                units=1,
                                meta={"prompt_id": str(selected_id)},
                            ),
                        )
                    except Exception:
                        pass

                st.download_button(
                    "⬇️ Скачать .txt",
                    data=full_text,
                    file_name=f"{selected_id}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    on_click=_on_download,
                )
                if payload:
                    st.divider()
                    st.json(redact_payload_for_ui(payload))
            with t2:
                st.info(f"**Positive:**\n{res_ru}")
                st.warning(f"**Negative:**\n{neg_ru}")

        except Exception as e:
            _store_last_generate_error(selected_id, e)
            # Make common validation issues actionable without exposing sensitive data.
            # ValueError messages in this app are crafted to be user-safe (e.g., missing fields,
            # upload limits). Everything else keeps the generic message unless debug is enabled.
            if isinstance(e, ValueError):
                st.error(str(e))
            else:
                st.error(public_error_message(e, debug=getattr(cfg, "debug_errors", False)))

# =========================================================
# 9) HISTORY TAB
# =========================================================
with tab_history:
    st.write(" ")
    if st.button("Очистить историю"):
        st.session_state["history"] = []
        st.rerun()
    
    # В истории может быть несколько одинаковых элементов.
    # streamlit-components требуют уникальный key для каждого экземпляра.
    for idx, item in enumerate(st.session_state["history"]):
        with st.expander(f"{item['time']} | {item['task']}"):
            st.code(item["en"], language="text")
            st_copy_to_clipboard(item["en"], "Копировать", key=f"hist_copy_en_{idx}")
            st.caption(item["ru"])
