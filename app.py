import streamlit as st
import streamlit.components.v1 as components
import re
import datetime
from prompt_manager import PromptManager
from st_copy_to_clipboard import st_copy_to_clipboard
from deep_translator import GoogleTranslator

# --- 1. НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Nano Banano Pro", 
    page_icon="🍌", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# --- 2. JAVASCRIPT: УБИЙЦА ПОДСКАЗОК И ВЫДЕЛЕНИЯ ---
components.html(
    """
    <script>
    function fixInterface() {
        // Убираем тултипы
        const elems = window.parent.document.querySelectorAll('div[data-baseweb="select"] *, div[data-baseweb="base-input"] *');
        elems.forEach(el => {
            if (el.hasAttribute('title')) el.removeAttribute('title');
        });
    }
    const observer = new MutationObserver(() => fixInterface());
    observer.observe(window.parent.document.body, { childList: true, subtree: true });
    setTimeout(fixInterface, 1000);
    </script>
    """,
    height=0,
)

# --- 3. ЛОГИКА ИСТОРИИ ---
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

# --- 4. CSS СТИЛИ (MOBILE FIX) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    /* === 1. ГЛАВНЫЙ ФИКС ДЛЯ МОБИЛЬНЫХ === */
    
    /* Хедер должен быть ВИДИМЫМ, но ПРОЗРАЧНЫМ */
    [data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important; /* Клики проходят сквозь пустое место */
        visibility: visible !important; /* <--- ВОТ ЭТО ВЕРНУЛО КНОПКУ МЕНЮ */
    }
    
    /* Сама кнопка меню должна нажиматься */
    [data-testid="stHeader"] button {
        pointer-events: auto !important;
        color: #FFD700 !important; 
        z-index: 99999 !important; /* Поверх всего */
    }

    /* Отступ сверху (на ПК) */
    .main .block-container { 
        padding-top: 6rem !important; 
        padding-bottom: 5rem !important;
    }

    /* Защита от выделения в меню */
    div[data-baseweb="select"], div[data-baseweb="menu"], li[role="option"] {
        user-select: none !important;
        -webkit-user-select: none !important;
        cursor: pointer !important;
    }

    /* Скрываем лишнее (Github значок и футер) */
    [data-testid="stToolbar"], [data-testid="stDecoration"], footer { display: none !important; }

    /* === 2. ДИЗАЙН === */

    /* ФОНЫ */
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
        padding-top: 2rem !important;
    }

    /* ТЕКСТ */
    h1, h2, h3, p, label, .stMarkdown, .stCaption, [data-testid="stSidebar"] label {
        color: #e0e0e0 !important;
        font-family: 'Inter', sans-serif !important; 
    }

    /* ПОЛЯ ВВОДА */
    div[data-baseweb="base-input"], 
    div[data-baseweb="textarea"], 
    div[data-baseweb="select"] > div {
        background-color: #1a1a1a !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
    }
    
    input, textarea {
        color: #ffffff !important;       
        -webkit-text-fill-color: #ffffff !important; 
        font-family: 'Inter', sans-serif !important;
        caret-color: #FFD700 !important; 
    }
    input::placeholder, textarea::placeholder {
        color: #888888 !important;       
        -webkit-text-fill-color: #888888 !important;
    }

    /* Подсветка активного поля */
    div[data-baseweb="base-input"]:focus-within, 
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        border-color: #FFD700 !important; 
        box-shadow: 0 0 0 1px #FFD700 !important;
    }

    /* КНОПКИ */
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #FFD700 !important; 
        border: none !important;
        padding: 0.8rem 1rem !important;
        border-radius: 8px !important; 
    }
    div.stButton > button p, div.stFormSubmitButton > button p {
        color: #000000 !important; 
        font-family: 'Inter', sans-serif !important; 
        font-weight: 700 !important;       
        font-size: 18px !important;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background-color: #FFC300 !important; 
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
    }

    /* БАННЕР */
    .main-banner {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-left: 6px solid #FFD700; 
        padding: 25px;
        border-radius: 12px; 
        margin-bottom: 25px;
        border: 1px solid rgba(255, 215, 0, 0.15);
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.25);
    }
    .main-banner h1 { margin: 0; color: #FFD700 !important; font-size: 2.5rem; font-weight: 700; }
    .main-banner p { margin: 8px 0 0 0; font-size: 1.1rem; color: #cccccc !important; }

    /* ЛОГО В САЙДБАРЕ */
    .sidebar-logo {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: black !important;
        font-weight: 800;
        font-size: 1.3rem;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(255, 215, 0, 0.2);
    }
    
    /* ТАБЫ (ВКЛАДКИ) */
    button[data-baseweb="tab"] {
        border-radius: 8px !important;
        margin-right: 6px !important;
        background-color: transparent !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFD700 !important;
        border: none !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] div p {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    button[data-baseweb="tab"] div p { color: #e0e0e0 !important; }
    
    /* УБИРАЕМ КРАСНУЮ ПОЛОСКУ ПОД ТАБАМИ */
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    .stTooltipIcon { color: #FFD700 !important; }

    /* === АДАПТАЦИЯ ПОД МОБИЛЬНЫЕ ТЕЛЕФОНЫ === */
    @media only screen and (max-width: 600px) {
        .main .block-container { 
            padding-top: 4rem !important; /* Меньше отступ сверху на телефоне */
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .main-banner h1 { font-size: 1.8rem !important; } /* Чуть меньше шрифт заголовка */
        div.stButton > button p { font-size: 16px !important; } /* Кнопки чуть компактнее */
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. ЗАГОЛОВОК И ТУТОРИАЛ ---
st.markdown("""
    <div class="main-banner">
        <h1>🍌 Nano Banano Pro</h1>
        <p>Твой карманный AI-креативщик</p>
    </div>
    """, unsafe_allow_html=True)

with st.expander("Как пользоваться? (Нажмите, чтобы открыть)"):
    st.markdown("""
    1. **Выберите задачу** в меню слева.
    2. **Заполните поля** (или просто следуйте примерам).
    3. Нажмите кнопку **"🍌 Сгенерировать Промпт"**.
    4. **Скопируйте** готовый текст.
    """)
st.write("---") 

# --- 6. СЛОВАРИ ДАННЫХ ---
VAR_MAP = {
    "image_1": "📸 Исходное фото / Ссылка",
    "image_2": "🖼 Второе фото / Референс",
    "person": "👤 Кто на фото?",
    "background": "🌍 Где происходит действие? (Фон)",
    "angle": "🎥 Ракурс камеры",
    "lighting": "💡 Свет",
    "object": "📦 Объект",
    "emotion": "😊 Эмоция",
    "element_from_image_1": "1️⃣ Что берем с 1-го фото?",
    "element_from_image_2": "2️⃣ Что берем со 2-го фото?",
    "object_type": "📦 На что натягиваем дизайн? (Предмет)",
    "background_type": "🖼 На каком фоне?",
    "style": "🎨 Стиль",
    "materials": "🧱 Материалы / Текстуры",
    "element_1": "🧩 Первый объект (Кто?)",
    "element_2": "🧩 Второй объект (С кем/чем?)",
    "scene_description": "🌄 Сюжет (Что происходит?)",
    "graphic_type": "📊 Вид графики",
    "brand": "🏷 Бренд / Название",
    "text": "🔤 Текст надписи",
    "font_style": "🔠 Шрифт",
    "design_style": "🖌 Стиль дизайна",
    "colors": "🎨 Цвета",
    "industry_brand": "🏭 Ниша бизнеса",
    "emotions": "🎭 Настроение (Vibe)",
    "imagery": "👁 Символ / Образ",
    "objects": "🔩 Из чего собрать логотип?",
    "features_list": "📋 Список преимуществ",
    "aspect_ratio": "📐 Формат (Пропорции)",
    "face_description_or_image_2": "👤 Чье лицо ставим?",
    "character_description": "📝 Описание героя",
    "situation": "🎬 Сюжет / Действие",
    "additional_objects": "➕ Что добавить на фон?",
    "atmosphere": "✨ Атмосфера / Погода",
    "screen_type": "📱 Какой экран рисуем?",
    "room_type": "🏠 Какая комната?"
}

# --- ОБНОВЛЕННАЯ БАЗА ПРИМЕРОВ ---
EXAMPLES_DB = {
    "image_1": {"ph": "Вставьте ссылку (Ctrl+V) или опишите словами...", "help": "Основная картинка для обработки."},
    "image_2": {"ph": "Ссылка на вторую картинку...", "help": "Картинка, откуда берем лицо, одежду или стиль."},
    "person": {"ph": "Напр: Илон Маск, Девушка с рыжими волосами, Бэтмен...", "help": "Кого мы генерируем или меняем?"},
    "background": {"ph": "Напр: На Марсе, В сказочном лесу, В офисе Google...", "help": "Окружение вокруг персонажа."},
    "angle": {"ph": "Напр: Вид снизу, Крупный план лица, С высоты птичьего полета...", "help": "Как стоит камера?"},
    "lighting": {"ph": "Напр: Неоновый свет, Мягкий свет из окна, Закат...", "help": "Освещение задает настроение."},
    "object": {"ph": "Напр: Красный диван, Айфон, Бутылка колы...", "help": "Предмет, который нужно добавить или удалить."},
    "emotion": {"ph": "Напр: Дикий восторг, Подозрение, Усталость...", "help": "Какую эмоцию должен сыграть персонаж?"},
    "object_type": {"ph": "Напр: Футболка, Коробка для пиццы, Экран ноутбука...", "help": "На какой предмет натянуть ваш дизайн?"},
    "background_type": {"ph": "Напр: Деревянный стол, Бетонная стена, Мрамор...", "help": "Поверхность или фон для мокапа."},
    "style": {"ph": "Напр: Киберпанк, Аниме, Масло, Фотореализм...", "help": "В каком стиле рисовать?"},
    "materials": {"ph": "Напр: Золото и бархат, Ржавый металл, Стекло...", "help": "Из чего сделан объект?"},
    "text": {"ph": "Напр: СКИДКИ 50%, Nano Banano, С Днем Рождения!...", "help": "Текст, который должен быть на картинке."},
    "font_style": {"ph": "Напр: Жирный, Рукописный, Готический, Футуристичный...", "help": "Каким шрифтом писать?"},
    "colors": {"ph": "Напр: Черный и желтый, Пастельные тона, Кислотный неон...", "help": "Главные цвета картинки."},
    "brand": {"ph": "Напр: Nike, Apple, МояКофейня...", "help": "Название компании."},
    "industry_brand": {"ph": "Напр: Салон красоты, IT-стартап, Строительная фирма...", "help": "Чем занимается компания?"},
    "imagery": {"ph": "Напр: Лев в короне, Ракета, Чашка кофе...", "help": "Главный символ логотипа."},
    "objects": {"ph": "Напр: Кофейные зерна, Болты и гайки, Лепестки роз...", "help": "Из каких мелких предметов собрать логотип?"},
    "features_list": {"ph": "Напр: Быстрая доставка, Эко-продукты, Гарантия 5 лет...", "help": "Ключевые фишки товара для инфографики."},
    "aspect_ratio": {"ph": "Напр: 16:9 (YouTube), 9:16 (Stories), 1:1 (Instagram)...", "help": "Формат изображения."},
    "face_description_or_image_2": {"ph": "Напр: Ссылка на фото лица или 'Брэд Питт'...", "help": "Чье лицо нужно вставить?"},
    "character_description": {"ph": "Напр: Киборг-ниндзя с катаной, Девушка-эльф...", "help": "Описание внешности героя."},
    "situation": {"ph": "Напр: Сражается с драконом, Пьет кофе и читает...", "help": "Что делает персонаж?"},
    "atmosphere": {"ph": "Напр: Туманное утро, Дождливый нуар, Яркий праздник...", "help": "Общее настроение сцены."},
    "screen_type": {"ph": "Напр: Главная страница, Профиль, Корзина, Настройки...", "help": "Какой экран приложения рисуем?"},
    "room_type": {"ph": "Напр: Лофт-гостиная, Спальня в скандинавском стиле, Кухня...", "help": "Тип помещения для дизайна."},
    "design_style": {"ph": "Напр: Минимализм, Гранж, Лакшери...", "help": "Общий стиль дизайна."},
    "emotions": {"ph": "Напр: Доверие и надежность, Игривое, Премиальное...", "help": "Какое чувство должен вызывать логотип?"},
    "element_1": {"ph": "Напр: Огромный робот, Кот-космонавт...", "help": "Первый главный объект."},
    "element_2": {"ph": "Напр: Маленькая девочка с цветком, НЛО...", "help": "Второй объект."},
    "scene_description": {"ph": "Напр: Робот дарит цветок девочке...", "help": "Что происходит между объектами?"}
}

# --- ИНИЦИАЛИЗАЦИЯ ДВИЖКА ---
@st.cache_resource
def load_engine():
    try:
        return PromptManager('prompts.json')
    except:
        return None

manager = load_engine()

# --- 7. САЙДБАР ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🍌 PRO MENU</div>', unsafe_allow_html=True)
    tab_menu, tab_history = st.tabs(["Меню", "История"])

if manager:
    options = {data['title']: pid for pid, data in manager.prompts.items()}

    with tab_menu:
        st.write(" ")
        selected_title = st.selectbox("Выберите задачу:", list(options.keys()))
        selected_id = options[selected_title]
        current_prompt_data = manager.prompts[selected_id]
        with st.container(border=True):
            st.info(current_prompt_data['description'])

    # --- 8. ОСНОВНАЯ ЗОНА ---
    st.subheader(f"{selected_title}")

    template = current_prompt_data['prompt_en']
    required_vars = sorted(list(set(re.findall(r'\[(.*?)\]', template))))
    user_inputs = {}

    if not required_vars:
        st.success("✅ Параметры не требуются. Нажмите кнопку.")
        with st.form("prompt_form_empty"):
             submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)
    else:
        with st.form("prompt_form"):
            cols = st.columns(2)
            for i, var in enumerate(required_vars):
                col = cols[i % 2]
                
                label = VAR_MAP.get(var, f"Введите {var}")
                example_data = EXAMPLES_DB.get(var, {})
                placeholder_text = example_data.get("ph", "Введите значение...")
                help_text = example_data.get("help", "")

                user_inputs[var] = col.text_input(
                    label, 
                    key=var,
                    placeholder=placeholder_text,
                    help=help_text
                )
                
            st.write("---")
            submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)

    # --- 9. ЛОГИКА ГЕНЕРАЦИИ ---
    if 'submitted' in locals() and submitted:
        missing = [VAR_MAP.get(k, k) for k, v in user_inputs.items() if not v]
        
        if missing:
            st.warning(f"⚠️ **Пустые поля:** {', '.join(missing)}. Результат может быть неточным.")
        
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

                res_ru = manager.generate(selected_id, 'ru', **inputs_ru)
                res_en = manager.generate(selected_id, 'en', **inputs_en)
                
                save_to_history(selected_title, res_en, res_ru)
            
            st.success("✨ **Готово!**")
            
            tab1, tab2 = st.tabs(["🇺🇸 **English**", "🇷🇺 Русский"])
            
            with tab1:
                st.code(res_en, language="text")
                st_copy_to_clipboard(res_en, "📋 Скопировать")
                
            with tab2:
                st.code(res_ru, language="text")
                
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")

else:
    st.error("Файл prompts.json не найден!")

# --- 10. ИСТОРИЯ ---
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
            with st.expander(f"{item['time']} | {item['task']}"):
                st.caption("English:")
                st.code(item['en'], language="text")
                st.divider()
                st.caption("Russian:")
                st.code(item['ru'], language="text")

with st.sidebar:
    st.markdown("---")
    st.caption("Made with ❤️ for Nano Banano Pro")