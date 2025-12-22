import streamlit as st
import streamlit.components.v1 as components
import re
import datetime
# import google.generativeai as genai 
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

# --- 2. JAVASCRIPT: УБИЙЦА ПОДСКАЗОК ---
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

# --- 4. CSS СТИЛИ (NO GITHUB UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* ============================================================
       СКРЫВАЕМ ИНТЕРФЕЙС STREAMLIT (GITHUB, FORK, SETTINGS)
       ============================================================ */
    [data-testid="stToolbar"] {
        display: none !important; /* Прячет верхнее меню с Fork */
    }
    [data-testid="stHeader"] {
        background: transparent !important;
        visibility: hidden !important; /* Прячет хедер полностью */
    }
    footer {
        visibility: hidden !important; /* Прячет надпись "Made with Streamlit" внизу */
    }
    [data-testid="stDecoration"] {
        display: none !important;
    }
    
    .main .block-container { padding-top: 2rem !important; }

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
        padding-top: 1rem !important;
    }

    /* ТЕКСТ ОБЩИЙ */
    h1, h2, h3, p, label, .stMarkdown, .stCaption, [data-testid="stSidebar"] label, [data-testid="stExpander"] p {
        color: #e0e0e0 !important;
        font-family: 'Inter', sans-serif !important; 
    }

    /* ПОЛЯ ВВОДА */
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

    /* МЕНЮ КАК КНОПКА */
    div[data-baseweb="select"] { cursor: pointer !important; }
    div[data-baseweb="select"] * { cursor: pointer !important; user-select: none !important; -webkit-user-select: none !important; }
    
    /* ТАБЫ */
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

    /* КНОПКИ */
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #FFD700 !important; 
        border: none !important;
        padding: 0.7rem 1rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;   
        border-radius: 8px !important; 
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
    .main-banner h1 {
        margin: 0;
        color: #FFD700 !important;
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem; 
        font-weight: 700; 
        letter-spacing: -0.5px;
        text-shadow: none;
    }
    .main-banner p {
        margin: 8px 0 0 0;
        font-size: 1.1rem;
        color: #cccccc !important;
        font-weight: 400;
    }

    /* ЛОГО */
    .sidebar-logo {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: black !important;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 1.3rem;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(255, 215, 0, 0.2);
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .stTooltipIcon { color: #FFD700 !important; }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
         background-color: transparent !important;
    }

    @media only screen and (max-width: 600px) {
        .main-banner h1 { font-size: 1.8rem !important; }
        .main-banner p { font-size: 1rem !important; }
        .main-banner { padding: 15px !important; margin-bottom: 15px !important; }
        div.stButton > button p, div.stFormSubmitButton > button p { font-size: 16px !important; }
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. ЗАГОЛОВОК ---
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
    4. Скопируйте результат и отправьте в нейросеть.
    """)
st.write("---") 

# --- 6. СЛОВАРИ ---
VAR_MAP = {
    "image_1": "Исходное фото / Ссылка",
    "image_2": "Второе фото / Референс",
    "person": "Кто на фото?",
    "background": "Где происходит действие? (Фон)",
    "angle": "Ракурс камеры",
    "lighting": "Свет",
    "object": "Объект",
    "emotion": "Эмоция",
    "element_from_image_1": "Что берем с 1-го фото?",
    "element_from_image_2": "Что берем со 2-го фото?",
    "object_type": "На что натягиваем дизайн? (Предмет)",
    "background_type": "На каком фоне?",
    "style": "Стиль",
    "materials": "Материалы / Текстуры",
    "element_1": "Первый объект (Кто?)",
    "element_2": "Второй объект (С кем/чем?)",
    "scene_description": "Сюжет (Что они делают?)",
    "graphic_type": "Вид графики",
    "brand": "Бренд / Название",
    "text": "Текст надписи",
    "font_style": "Шрифт",
    "design_style": "Стиль дизайна",
    "colors": "Цвета",
    "industry_brand": "Ниша бизнеса",
    "emotions": "Настроение (Vibe)",
    "imagery": "Символ / Образ",
    "objects": "Из чего собрать логотип?",
    "features_list": "Список преимуществ (через запятую)",
    "aspect_ratio": "Формат (Пропорции)",
    "face_description_or_image_2": "Чье лицо ставим? (Ссылка или Имя)",
    "character_description": "Описание героя",
    "situation": "Сюжет / Действие",
    "additional_objects": "Что добавить на фон?",
    "atmosphere": "Атмосфера / Погода",
    "screen_type": "Какой экран рисуем?",
    "room_type": "Какая комната?"
}

# --- ПОЛНАЯ БАЗА ПРИМЕРОВ ---
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
    
    # --- НОВЫЕ ПРИМЕРЫ (FIXED) ---
    "emotions": {"ph": "Напр: Доверие и надежность, Игривое и детское, Строгое и премиальное...", "help": "Какое чувство должен вызывать логотип у клиента?"},
    "element_1": {"ph": "Напр: Огромный робот, Кот-космонавт, Старинный замок...", "help": "Первый главный объект сцены."},
    "element_2": {"ph": "Напр: Маленькая девочка с цветком, НЛО, Рыцарь...", "help": "Второй объект, с которым взаимодействует первый."},
    "scene_description": {"ph": "Напр: Робот дарит цветок девочке на закате. Контраст масштабов...", "help": "Опишите, что происходит между этими объектами."}
}

# --- ИНИЦИАЛИЗАЦИЯ ДВИЖКА ---
@st.cache_resource
def load_engine():
    return PromptManager('prompts.json')

try:
    manager = load_engine()
except Exception as e:
    st.error(f"❌ Ошибка загрузки базы данных: {e}")
    st.stop()

# --- 7. САЙДБАР ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🍌 PRO MENU</div>', unsafe_allow_html=True)
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

# --- 8. ОСНОВНАЯ ЗОНА ---
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
            # Берем человеческое название из VAR_MAP, если нет - оставляем как есть
            label = VAR_MAP.get(var, f"Введите {var}")
            
            # Берем данные из EXAMPLES_DB, если нет - ставим заглушку
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
        submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)

# --- 9. ЛОГИКА ГЕНЕРАЦИИ ---
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

                res_ru = manager.generate(selected_id, 'ru', **inputs_ru)
                res_en = manager.generate(selected_id, 'en', **inputs_en)
                
                save_to_history(selected_title, res_en, res_ru)
            
            st.success("✨ **Готово! Промпт успешно сгенерирован и сохранен.**")
            
            tab1, tab2 = st.tabs(["🇺🇸 **English (Готово для AI)**", "🇷🇺 Русский (Для проверки)"])
            
            with tab1:
                st.markdown("##### 👇 Скопируйте этот текст в нейросеть:")
                st.code(res_en, language="text")
                key_en = f"copy_en_{hash(res_en)}"
                st_copy_to_clipboard(res_en, "📋 Скопировать English Промпт", key=key_en)
                
            with tab2:
                st.markdown("##### Перевод для контроля смысла:")
                st.code(res_ru, language="text")
                key_ru = f"copy_ru_{hash(res_ru)}"
                st_copy_to_clipboard(res_ru, "📋 Скопировать Русский Промпт", key=key_ru)
                
        except Exception as e:
            st.error(f"❌ Ошибка генерации или перевода: {e}")

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
    st.markdown("Made with ❤️ for Nano Banano Pro")