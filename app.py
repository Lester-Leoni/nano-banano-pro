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

# --- 2. JS CLEANER ---
components.html(
    """
    <script>
    function removeTitles() {
        const elems = window.parent.document.querySelectorAll('div[data-baseweb="select"] *');
        elems.forEach(el => {
            if (el.hasAttribute('title')) {
                el.removeAttribute('title');
            }
        });
    }
    const observer = new MutationObserver(() => {
        removeTitles();
    });
    observer.observe(window.parent.document.body, { childList: true, subtree: true });
    setTimeout(removeTitles, 1000);
    </script>
    """,
    height=0,
)

# --- 3. NEGATIVE PROMPT LIBRARY ---
NEG_GROUPS = {
    1: { # Фотореализм и Люди
        "Mini": {"en": "plastic skin, beauty retouch, identity drift, extra fingers, watermark, text", "ru": "пластиковая кожа, бьюти-ретушь, потеря сходства, лишние пальцы, водяной знак, текст"},
        "Plus": {"en": "waxy/plastic skin, over-smoothing, beauty retouch, face reshape, identity drift, extra teeth, extra fingers, deformed hands, watermark, text", "ru": "восковая кожа, пересглаживание, бьюти-ретушь, изменение лица, потеря сходства, лишние зубы/пальцы, деформация рук, водяной знак, текст"},
        "Full": {"en": "waxy/plastic skin, over-smoothing, beauty retouch, face reshaping, identity drift, uncanny face, extra teeth, deformed hands, extra limbs/fingers, AI glow, over-sharpen halos, heavy noise, color banding, extra text, watermark, logo", "ru": "восковая/пластиковая кожа, пересглаживание, бьюти-ретушь, изменение черт лица, потеря сходства, жуткое лицо, лишние зубы, деформированные руки, лишние конечности, AI-свечение, ореолы перешарпа, сильный шум, цветовые полосы, лишний текст, водяной знак, логотип"}
    },
    2: { # Редактирование сцены
        "Mini": {"en": "seams, halos, ghosting, wrong shadow, wrong scale, watermark, text", "ru": "швы, ореолы, двоение, неверные тени, неверный масштаб, водяной знак, текст"},
        "Plus": {"en": "seams, halos, cutout edges, ghosting, smear, warped lines, floating object, wrong shadow, wrong scale, mismatch grain, watermark, text", "ru": "швы, ореолы, обрезанные края, двоение, размазывание, кривые линии, левитирующие объекты, неверные тени, неверный масштаб, разное зерно, водяной знак, текст"},
        "Full": {"en": "seams, halos, cutout edges, ghosting, smearing, warped perspective/lines, floating objects, wrong scale, wrong shadows, inconsistent lighting, mismatch grain/noise, color mismatch, reflections missing/incorrect, blur artifacts, extra text, watermark, logo", "ru": "швы, ореолы, обрезанные края, двоение, размазывание, искаженная перспектива, левитирующие объекты, неверный масштаб/тени, несоответствие света/зерна/цвета, ошибки отражений, артефакты размытия, лишний текст, водяной знак, логотип"}
    },
    3: { # Коммерческий дизайн
        "Mini": {"en": "misspelling, broken glyphs, lorem ipsum, tiny text, random logo, watermark", "ru": "опечатки, битые символы, lorem ipsum, мелкий текст, случайный логотип, водяной знак"},
        "Plus": {"en": "misspelling, broken glyphs, lorem ipsum, tiny unreadable text, clutter, misaligned layout, low-contrast text, pixelation, random logo, watermark", "ru": "опечатки, битые символы, lorem ipsum, нечитаемый текст, мусор, кривая верстка, низкий контраст, пикселизация, случайный логотип, водяной знак"},
        "Full": {"en": "misspelling, broken glyphs, lorem ipsum, tiny unreadable text, clutter, misaligned layout, low contrast text, pixelation, jagged edges, wrong aspect ratio, random brand/logo, watermark, extra QR codes, illegible icons", "ru": "опечатки, битые символы, lorem ipsum, мелкий нечитаемый текст, визуальный мусор, кривая верстка, низкий контраст, пикселизация, рваные края, неверные пропорции, случайный бренд/логотип, водяной знак, лишние QR-коды, неразборчивые иконки"}
    },
    4: { # Арт и Иллюстрация
        "Mini": {"en": "extra objects, anatomy warp, style drift, seams, vignette, watermark, text", "ru": "лишние объекты, искажение анатомии, плавающий стиль, швы, виньетка, водяной знак, текст"},
        "Plus": {"en": "extra objects, anatomy warp, proportion change, perspective distortion, messy linework, style drift, pattern seams, vignette, unreadable text, watermark", "ru": "лишние объекты, искажение анатомии, нарушение пропорций, искажение перспективы, неряшливые линии, плавающий стиль, швы, виньетка, нечитаемый текст, водяной знак"},
        "Full": {"en": "extra objects, anatomy warp, proportion changes, perspective distortion, messy linework, inconsistent style, seams in pattern, vignette, shading when flat is required, unreadable text/gibberish, watermark, logo", "ru": "лишние объекты, искажение анатомии, нарушение пропорций, искажение перспективы, неряшливые линии, непоследовательный стиль, швы в паттерне, виньетка, лишние тени, нечитаемый текст, водяной знак, логотип"}
    },
    5: { # Архитектура
        "Mini": {"en": "keystone distortion, warped verticals, messy geometry, unrealistic scale, watermark, text", "ru": "искажение трапеции, кривые вертикали, грязная геометрия, нереальный масштаб, водяной знак, текст"},
        "Plus": {"en": "keystone distortion, warped verticals, bent walls, unrealistic scale, messy geometry, low-res textures, blown highlights, muddy shadows, clutter, watermark", "ru": "искажение трапеции, кривые вертикали/стены, нереальный масштаб, грязная геометрия, текстуры низкого разрешения, пересветы, грязные тени, мусор, водяной знак"},
        "Full": {"en": "keystone distortion, bent walls, warped verticals, unrealistic scale, messy geometry, low-res textures, over-sharpen halos, blown highlights, muddy shadows, clutter, people/characters (if not requested), extra text, watermark, logo", "ru": "искажение трапеции, кривые стены, заваленные вертикали, нереалистичный масштаб, грязная геометрия, текстуры низкого разрешения, ореолы перешарпа, пересветы, грязные тени, мусор, лишние люди, текст, водяной знак"}
    },
    6: { # Спецэффекты и Кино
        "Mini": {"en": "overdone flares, heavy aberration, excessive bloom, noisy artifacts, watermark, text", "ru": "перебор с бликами, сильная аберрация, избыточное свечение, шум, водяной знак, текст"},
        "Plus": {"en": "excessive bloom, heavy chromatic aberration, overdone flares, crushed blacks, blown highlights, noisy artifacts, oversharpen halos, plastic skin, watermark, text", "ru": "избыточное свечение, сильная аберрация, перебор с бликами, проваленные черные, пересветы, шумные артефакты, перешарп, пластиковая кожа, водяной знак, текст"},
        "Full": {"en": "overdone bloom, heavy chromatic aberration, excessive lens flares, crushed blacks, blown highlights, noisy artifacts, oversharpen halos, plastic skin, unreadable text, tiny clutter text, watermark, logo", "ru": "перебор с bloom, сильная аберрация, избыточные блики, проваленные черные, пересветы, шумные артефакты, ореолы перешарпа, пластиковая кожа, нечитаемый текст, мелкий мусор, водяной знак, логотип"}
    }
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
if 'history' not in st.session_state:
    st.session_state['history'] = []

def save_to_history(task, prompt_en, prompt_ru):
    timestamp = datetime.datetime.now().strftime("%H:%M")
    st.session_state['history'].insert(0, {
        "task": task,
        "en": prompt_en,
        "ru": prompt_ru,
        "time": timestamp,
        "id": len(st.session_state['history']) + 1
    })
    if len(st.session_state['history']) > 50:
        st.session_state['history'].pop()

# --- 5. CSS (VISUAL FIXES) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

/* HEADER & ARROW */
header[data-testid="stHeader"] {
    background: transparent !important;
    background-color: transparent !important;
    border-bottom: none !important;
    box-shadow: none !important;
}
[data-testid="stDecoration"] { display: none !important; }
button[data-testid="stSidebarCollapsedControl"] {
    color: #FFD700 !important;
    border: none !important;
    background: transparent !important;
}
button[data-testid="stSidebarCollapsedControl"]:hover {
    color: #FFC300 !important;
    background: transparent !important;
}
div[data-testid="stToolbar"] { right: 2rem; top: 0.5rem; }
footer { display: none !important; }
.main .block-container { padding-top: 3rem !important; }

/* THEME */
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

/* INPUTS */
div[data-baseweb="base-input"], div[data-baseweb="textarea"] {
    background-color: #1a1a1a !important;
    border: 1px solid #444 !important;
}
div[data-baseweb="base-input"] input, 
div[data-baseweb="textarea"] textarea {
    color: #ffffff !important;       
    -webkit-text-fill-color: #ffffff !important; 
    caret-color: #FFD700 !important; 
    font-weight: 500 !important;
}
input::placeholder, textarea::placeholder {
    color: #888888 !important;       
    -webkit-text-fill-color: #888888 !important;
    opacity: 1 !important;
    font-weight: 400 !important;
}
div[data-baseweb="base-input"]:focus-within, 
div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="textarea"]:focus-within {
    border-color: #FFD700 !important; 
    box-shadow: 0 0 0 1px #FFD700 !important;
}

/* TABS */
button[data-baseweb="tab"] {
    border-radius: 8px !important;
    margin-right: 6px !important;
    border: 1px solid transparent !important; 
    transition: all 0.2s ease !important;
    padding: 0.5rem 1rem !important;
}
button[data-baseweb="tab"] div p {
    color: #e0e0e0 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #FFD700 !important;
    border: none !important;
    box-shadow: 0 2px 5px rgba(255, 215, 0, 0.2) !important;
}
button[data-baseweb="tab"][aria-selected="true"] div p {
    color: #000000 !important;
    font-weight: 800 !important;
}
div[data-baseweb="tab-highlight"] { display: none !important; }

/* BUTTONS */
div.stButton > button, div.stFormSubmitButton > button {
    background-color: #FFD700 !important; 
    border: none !important;
    padding: 0.7rem 1rem !important;
    transition: all 0.3s ease !important;
    width: 100% !important;   
    border-radius: 8px !important; 
    color: #000000 !important;
}
div.stButton > button p, div.stFormSubmitButton > button p {
    color: #000000 !important; 
    font-family: 'Inter', sans-serif !important; 
    font-weight: 700 !important;       
    text-transform: none !important;   
    letter-spacing: normal !important; 
    font-size: 18px !important;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    background-color: #FFC300 !important; 
    box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
    transform: translateY(-1px);
}
div.stButton > button:hover p, div.stFormSubmitButton > button:hover p { color: #000000 !important; }

/* BANNER */
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

/* SIDEBAR PRO BUTTON */
[data-testid="stSidebar"] .stButton:first-child > button {
    width: 100%;
    background-color: #FFD700 !important;
    color: #000000 !important;
    font-weight: 800 !important;
    font-size: 1.2rem !important;
    border-radius: 12px !important;
    padding: 15px !important;
    border: none !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
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

with st.expander(":material/info: Инструкция: Как пользоваться и что значат кнопки?"):
    st.markdown("""
    ### :material/bolt: Быстрый старт
    1. **Выберите задачу** в меню слева.
    2. **Заполните поля** (или оставьте пустые для теста).
    3. **Выберите режим Негатива** (см. ниже).
    4. Нажмите кнопку **"🍌 Сгенерировать Промпт"**.

    ---
    
    ### :material/tune: Режимы Негатива (Negative Prompt)
    *Выбирайте, насколько жестко нужно фильтровать ошибки нейросети:*
    * :material/filter_1: **Mini (Легкий):** Используйте, если модель "забывает" рисовать главное из-за кучи ограничений. Минимум запретов.
    * :material/filter_2: **Default (Mini+):** **Рекомендуется.** Золотая середина. Убирает плохую кожу, лишние пальцы и водяные знаки.
    * :material/filter_3: **Aggressive (Full):** Включайте, если нейросеть упорно выдает артефакты, кривые лица или "пластиковую" картинку. Максимальная зачистка.

    ---

    ### :material/content_copy: Как копировать результат?
    * :material/rocket_launch: **Кнопка "Всё в одном" (Для Ботов):** Идеально для **Midjourney**, Telegram-ботов и Discord.  
      *Автоматически добавляет команду `--no` перед негативом.*
        
    * :material/build: **Кнопки "Раздельно" (Для WebUI):** Используйте для **Stable Diffusion (A1111, ComfyUI)**, Leonardo AI и других сайтов, где есть отдельные поля для "Positive" и "Negative".
    """)
st.write("---") 

# --- 7. DATA DICTS ---
VAR_MAP = {
    # Общие
    "image_1": "Исходное изображение / Ссылка",
    "image_2": "Второе изображение / Референс",
    "aspect_ratio": "Формат (Пропорции)",
    "background": "Фон / Окружение",
    "lighting": "Освещение",
    "style": "Стиль",
    "colors": "Цветовая гамма",
    "angle": "Ракурс камеры",
    
    # Персонажи и Портреты
    "person": "Персонаж (Кто?)",
    "emotion": "Эмоция",
    "intensity": "Интенсивность эмоции (Low/Medium/High)",
    "fabric_material": "Материал ткани/одежды",
    
    # Объекты и Сцены
    "object": "Объект",
    "placement_details": "Где разместить объект?",
    "lighting_condition": "Условия освещения (напр. Sunset, Neon)",
    "element_1": "Элемент 1 (Основа)",
    "element_2": "Элемент 2 (Вставка)",
    "scene_description": "Описание сцены",
    "lens_match_mode": "Режим сведения линз (feel / strict)",
    
    # Коммерция и Дизайн
    "product": "Название продукта",
    "text": "Текст (Точная цитата)",
    "features_list": "Список фич (через запятую)",
    "object_type": "Тип объекта (для мокапа)",
    "background_type": "Тип фона (поверхность)",
    "print_finish": "Покрытие (Matte, Glossy, Foil)",
    "brand": "Бренд",
    "imagery": "Образ / Символ логотипа",
    "materials": "Материалы",
    "screen_type": "Тип экрана (Login, Home, Dash)",
    "industry": "Индустрия / Ниша",
    "platform": "Платформа (iOS, Android, Web)",
    "font_style": "Стиль шрифта",
    "design_style": "Стиль дизайна",
    
    # Арт и Иллюстрация
    "level": "Сила стилизации (Light/Medium/Strong)",
    "medium": "Медиум (Масло, Карандаш, 3D)",
    "description": "Описание персонажа",
    "labels_visibility": "Подписи ракурсов (On/Off)",
    "character": "Имя/Тип персонажа для стикеров",
    "count": "Количество стикеров",
    "list": "Список эмоций/поз",
    "scene": "Сцена комикса",
    "language": "Язык текста (En/Ru)",
    "theme": "Тема паттерна",
    "show_preview": "Показать превью 2x2? (Yes/No)",
    
    # Архитектура и 3D
    "room_type": "Тип комнаты",
    "room": "Комната (для среза)",
    "building_type": "Тип здания",
    "environment": "Окружение здания",
    "time": "Время суток / Погода",
    "lens": "Объектив (напр. 24mm, 35mm)",
    "background_color": "Цвет фона (для изометрии)",
    
    # Видео и Спецэффекты
    "type": "Тип (Photo / Illustration)",
    "expression": "Выражение лица (для превью)",
    "subject": "Главный герой/объект",
    "focus_stacking": "Focus Stacking (On/Off)",
    "atmosphere": "Атмосфера",
    "situation": "Ситуация / Сюжет"
}

# --- ПОЛНЫЙ СЛОВАРЬ ПРИМЕРОВ (ОБНОВЛЕНО) ---
EXAMPLES_DB = {
    "image_1": {"ph": "Вставьте ссылку на ваше фото...", "help": "Главное изображение для обработки (Ctrl+V)."},
    "image_2": {"ph": "Ссылка на референс или стиль...", "help": "Откуда берем лицо, одежду или стиль?"},
    "aspect_ratio": {"ph": "16:9 (YouTube), 9:16 (Stories), 1:1...", "help": "Пропорции итоговой картинки."},
    "background": {"ph": "На Марсе, В современном офисе, Сказочный лес...", "help": "Где происходит действие?"},
    "lighting": {"ph": "Кинематографичный, Мягкий свет из окна, Неон...", "help": "Какое настроение задает свет?"},
    "style": {"ph": "Киберпанк, Масло, Аниме, Фотореализм...", "help": "В каком стиле рисовать?"},
    "colors": {"ph": "Черный и золотой, Пастельные тона, Яркий неон...", "help": "Главные цвета изображения."},
    "person": {"ph": "Илон Маск, Девушка в красном, Бэтмен...", "help": "Кто главный герой?"},
    "emotion": {"ph": "Восторг, Подозрение, Усталость...", "help": "Какую эмоцию играет персонаж?"},
    "object": {"ph": "Красный диван, Айфон, Бутылка колы...", "help": "Какой предмет добавить или убрать?"},
    "fabric_material": {"ph": "Шелк, Деним, Кожа, Грубый хлопок...", "help": "Из чего сделана одежда?"},
    "building_type": {"ph": "Небоскреб, Уютный коттедж, Стеклянный офис...", "help": "Что за здание мы строим?"},
    "environment": {"ph": "В центре Нью-Йорка, В заснеженных горах...", "help": "Что находится вокруг здания?"},
    "time": {"ph": "Золотой час, Туманное утро, Дождливая ночь...", "help": "Время суток и погода."},
    "lens": {"ph": "24mm (широкий), 35mm (стандарт), 85mm (портрет)...", "help": "На какой объектив снимаем?"},
    "brand": {"ph": "Nike, Tesla, МояКофейня...", "help": "Название вашего бренда."},
    "industry": {"ph": "Салон красоты, IT-стартап, Доставка еды...", "help": "Чем занимается компания?"},
    "product": {"ph": "Кроссовки, Бутылка воды, Крем для лица...", "help": "Что продаем?"},
    "features_list": {"ph": "Эко-френдли, 24/7, Бесплатная доставка...", "help": "Главные фишки для инфографики."},
    "text": {"ph": "СКИДКИ 50%, Nano Banano...", "help": "Текст, который нужно написать на картинке."},
    "placement_details": {"ph": "На столе справа, В руке героя, Парит в воздухе...", "help": "Куда именно поместить объект?"},
    "print_finish": {"ph": "Матовая бумага, Золотое тиснение, Глянец...", "help": "Фактура материала для мокапа."},
    "room_type": {"ph": "Лофт-гостиная, Спальня в скандинавском стиле...", "help": "Какую комнату дизайним?"},
    "lens_match_mode": {"ph": "feel (визуально похоже) или strict (строго)", "help": "Как сводить линзы при монтаже?"},
    "focus_stacking": {"ph": "on (все в фокусе) / off (размытый фон)", "help": "Включить полную резкость?"},
    "platform": {"ph": "iOS, Android, Web", "help": "Для какой платформы дизайн?"},
    "level": {"ph": "medium (средний), strong (сильный)...", "help": "Насколько сильно менять стиль?"},
    "character": {"ph": "Милый робот, Рыжий кот, Девушка-эльф...", "help": "Персонаж для стикеров."},
    "count": {"ph": "6, 9, 12", "help": "Сколько стикеров в наборе?"},
    "list": {"ph": "Смех, Гнев, Сон, Ест пиццу...", "help": "Список эмоций через запятую."},
    "scene_description": {"ph": "Робот дарит цветок девочке на закате...", "help": "Что происходит в сцене?"}
}

# --- 8. ENGINE ---
@st.cache_resource
def load_engine():
    if not os.path.exists('prompts.json'):
        return None
    return PromptManager('prompts.json')

manager = load_engine()

if not manager:
    st.error("❌ Файл `prompts.json` не найден. Загрузите его в ту же папку.")
    st.stop()

# --- 9. SIDEBAR ---
with st.sidebar:
    st.button("🍌 PRO MENU", key="promenu_btn", use_container_width=True)
    tab_menu, tab_history = st.tabs(["Меню", "История"])

all_prompts = manager.prompts
options = {data['title']: pid for pid, data in all_prompts.items()}

with tab_menu:
    st.write(" ")
    selected_title = st.selectbox("Выберите задачу:", list(options.keys()))
    selected_id = options[selected_title]
    current_prompt_data = all_prompts[selected_id]
    with st.container(border=True):
        st.info(current_prompt_data['description'])

# --- 10. MAIN FORM ---
st.subheader(f"{selected_title}")

template = current_prompt_data['prompt_en']
required_vars = sorted(list(set(re.findall(r'\[(.*?)\]', template))))
user_inputs = {}

if not required_vars:
    st.success("✅ Для этого промпта параметры не требуются. Просто нажмите кнопку.")
    with st.form("prompt_form_empty"):
         submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)
else:
    with st.form("prompt_form"):
        cols = st.columns(2)
        for i, var in enumerate(required_vars):
            col = cols[i % 2]
            label = VAR_MAP.get(var, f"Введите {var}")
            example_data = EXAMPLES_DB.get(var, {})
            placeholder_text = example_data.get("ph", f"Пример...")
            help_text = example_data.get("help", "")

            user_inputs[var] = col.text_input(
                label,
                key=var,
                placeholder=placeholder_text,
                help=help_text
            )
            
        st.write("---")
        
        # 🔴 ПЕРЕКЛЮЧАТЕЛЬ НЕГАТИВА
        neg_mode = st.radio("Режим негатива (Negative Prompt):", 
                            ["Mini (Легкий)", "Default (Mini+)", "Aggressive (Full)"], 
                            index=1, horizontal=True)
        
        st.write(" ")
        submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)

# --- 11. GENERATION LOGIC (HYBRID MODE) ---
if 'submitted' in locals() and submitted:
    missing = [VAR_MAP.get(k, k) for k, v in user_inputs.items() if not v]
    
    if missing:
        st.error(f"⚠️ **Вы забыли заполнить поля:**\n\n" + "\n".join([f"- {m}" for m in missing]))
    else:
        try:
            with st.spinner('⏳ Переводим и собираем промпт...'):
                
                inputs_en = {}
                inputs_ru = {}
                translator_en = GoogleTranslator(source='auto', target='en')
                translator_ru = GoogleTranslator(source='auto', target='ru')
                
                for key, text in user_inputs.items():
                    if text.strip().startswith(("http", "www", "https")):
                        inputs_en[key] = text
                        inputs_ru[key] = text
                    else:
                        inputs_en[key] = translator_en.translate(text)
                        inputs_ru[key] = translator_ru.translate(text)

                # Генерация полных строк
                def clean_positive(text):
                    if "NEG (optional):" in text:
                        return text.split("NEG (optional):")[0].strip()
                    return text.strip()

                res_ru = clean_positive(manager.generate(selected_id, 'ru', **inputs_ru))
                res_en = clean_positive(manager.generate(selected_id, 'en', **inputs_en))

                # Подбираем негатив по группе и режиму
                group_id = ID_TO_GROUP.get(selected_id, 1) 
                
                mode_key = "Plus"
                if "Mini" in neg_mode: mode_key = "Mini"
                elif "Aggressive" in neg_mode: mode_key = "Full"
                
                neg_text_en = NEG_GROUPS[group_id][mode_key]['en']
                neg_text_ru = NEG_GROUPS[group_id][mode_key]['ru']

                save_to_history(selected_title, f"{res_en} --no {neg_text_en}", f"{res_ru} | NEG: {neg_text_ru}")
            
            st.success(":material/check_circle: **Готово! Промпт успешно сгенерирован.**")
            
            tab1, tab2 = st.tabs(["🇺🇸 **English (PRO)**", "🇷🇺 Русский (Info)"])
            
            # --- ВКЛАДКА 1: ENGLISH (ГИБРИДНЫЙ ВАРИАНТ) ---
            with tab1:
                # 1. Единый блок для Ботов
                full_bot_text = f"{res_en} --no {neg_text_en}"
                
                st.markdown("### :material/rocket_launch: Всё в одном (для ботов)")
                st.caption(f"Автоматически добавлено '--no' перед негативом ({mode_key}).")
                st.code(full_bot_text, language="text")
                st_copy_to_clipboard(full_bot_text, "📋 Скопировать всё", key=f"all_{hash(full_bot_text)}")
                
                st.divider()
                
                # 2. Раздельные блоки
                st.markdown("### :material/build: Раздельно (для WebUI)")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.caption(":material/add_circle: **Positive Prompt**")
                    st.code(res_en, language="text")
                    st_copy_to_clipboard(res_en, "Коп. Positive", key=f"pos_{hash(res_en)}")
                
                with col2:
                    st.caption(f":material/do_not_disturb_on: **Negative Prompt**")
                    st.code(neg_text_en, language="text")
                    st_copy_to_clipboard(neg_text_en, "Коп. Negative", key=f"neg_{hash(neg_text_en)}")

            # --- ВКЛАДКА 2: РУССКИЙ (ПЕРЕВОД) ---
            with tab2:
                st.markdown("##### 🇷🇺 Что мы попросили нейросеть:")
                
                st.info(f"**Рисуем:**\n\n{res_ru}")
                st.warning(f"**Запрещаем ({mode_key}):**\n\n{neg_text_ru}")
                
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")

# --- 11. HISTORY OUTPUT ---
with tab_history:
    st.write(" ")
    if st.button("Очистить историю"):
        st.session_state['history'] = []
        st.rerun()
        
    history_list = st.session_state['history']
    if not history_list:
        st.caption("История пуста.")
    else:
        for item in history_list:
            label = f"{item['time']} | {item['task']}"
            with st.expander(label):
                st.caption("English:")
                st.code(item['en'], language="text")
                st_copy_to_clipboard(item['en'], "Копировать EN", key=f"hist_en_{item['id']}")
                st.markdown("---")
                st.caption("Russian:")
                st.code(item['ru'], language="text")

with st.sidebar:
    st.markdown("---")