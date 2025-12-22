import streamlit as st
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

# --- 2. ЛОГИКА ИСТОРИИ ---
if 'history' not in st.session_state:
    st.session_state['history'] = []

def save_to_history(task, prompt_en, prompt_ru):
    """Сохраняет запись в сессию (в начало списка)"""
    timestamp = datetime.datetime.now().strftime("%H:%M")
    st.session_state['history'].insert(0, {
        "task": task,
        "en": prompt_en,
        "ru": prompt_ru,
        "time": timestamp,
        "id": len(st.session_state['history']) + 1
    })
    # Храним только последние 50 записей
    if len(st.session_state['history']) > 50:
        st.session_state['history'].pop()

# --- 3. CSS СТИЛИ (MINIMALIST & CLEAN) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* Прячем верхний тулбар */
    header[data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stDecoration"] { display: none !important; }
    
    /* Желтая стрелочка меню */
    button[kind="header"] { color: #FFD700 !important; background: transparent !important; }
    button[kind="header"]:hover { color: #FFC300 !important; }
    
    .main .block-container { padding-top: 1rem !important; }

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

    /* ТЕКСТ */
    h1, h2, h3, p, label, .stMarkdown, .stCaption, [data-testid="stSidebar"] label, [data-testid="stExpander"] p {
        color: #e0e0e0 !important;
        font-family: 'Inter', sans-serif !important; 
    }

    /* --- СТИЛИЗАЦИЯ ВКЛАДОК (TABS) --- */
    /* Текст вкладок по умолчанию */
    button[data-baseweb="tab"] div p {
        color: #e0e0e0 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
    }
    /* Активная вкладка - Желтый фон */
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFD700 !important;
        border: none !important;
    }
    /* Текст в Активной вкладке - Черный */
    button[data-baseweb="tab"][aria-selected="true"] div p {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    /* Полоска под вкладками */
    div[data-baseweb="tab-highlight"] {
        background-color: #FFD700 !important;
    }

    /* ПОЛЯ ВВОДА */
    input.st-ai, div[data-baseweb="select"] > div, div[data-baseweb="base-input"], div[data-baseweb="textarea"] {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #444 !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-baseweb="base-input"]:focus-within, 
    div[data-baseweb="select"] > div:focus-within, 
    input:focus {
        border-color: #FFD700 !important; 
        box-shadow: 0 0 0 1px #FFD700 !important;
        caret-color: #FFD700 !important;
    }

    /* КНОПКИ (Генерация и Очистка) */
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
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .main-banner h1 {
        margin: 0;
        color: #FFD700 !important;
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .main-banner p {
        margin: 8px 0 0 0;
        font-size: 1.1rem;
        color: #cccccc !important;
        font-weight: 400;
    }

    /* ЛОГО В МЕНЮ */
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
    
    /* Прозрачный фон контейнеров в сайдбаре */
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

# --- 4. ЗАГОЛОВОК ---
st.markdown("""
    <div class="main-banner">
        <h1>🍌 Nano Banano Pro</h1>
        <p>Твой карманный AI-креативщик</p>
    </div>
    """, unsafe_allow_html=True)

with st.expander("Как пользоваться? (Нажмите, чтобы открыть)"):
    st.markdown("""
    1. **Выберите задачу** в меню слева.
    2. **Заполните поля** (используйте подсказки `?`).
    3. Нажмите кнопку **"🍌 Сгенерировать Промпт"**.
    4. Скопируйте результат и отправьте в нейросеть.
    5. История сохраняется автоматически.
    """)
st.write("---") 

# --- 5. СЛОВАРИ ---
VAR_MAP = {
    "image_1": "Исходное изображение / Ссылка (image_1)",
    "image_2": "Второе изображение / Референс (image_2)",
    "person": "Персонаж / Кто на фото",
    "background": "Новое окружение / Фон",
    "angle": "Ракурс камеры",
    "lighting": "Схема освещения",
    "object": "Объект для удаления/добавления",
    "emotion": "Желаемая эмоция",
    "element_from_image_1": "Элемент из первого фото",
    "element_from_image_2": "Элемент из второго фото",
    "object_type": "Тип предмета для мокапа",
    "background_type": "Тип фона для мокапа",
    "style": "Стиль / Художественное направление",
    "materials": "Материалы / Текстуры",
    "element_1": "Первый элемент коллажа",
    "element_2": "Второй элемент коллажа",
    "scene_description": "Описание общей сцены",
    "graphic_type": "Тип графики",
    "brand": "Название бренда / Компания",
    "text": "Текст надписи",
    "font_style": "Стиль шрифта",
    "design_style": "Стиль дизайна",
    "colors": "Цветовая палитра",
    "industry_brand": "Сфера деятельности",
    "emotions": "Эмоциональный посыл",
    "imagery": "Образы / Символы",
    "objects": "Предметы для стилизации (из чего собрать лого)",
    "features_list": "Список характеристик",
    "aspect_ratio": "Пропорции",
    "face_description_or_image_2": "Описание лица или ссылка",
    "character_description": "Описание героя",
    "situation": "Ситуация / Сюжет",
    "additional_objects": "Дополнительные объекты на фоне",
    "atmosphere": "Атмосфера / Погода / Свет",
    "screen_type": "Тип экрана (напр. Профиль, Главная)",
    "room_type": "Тип помещения (напр. Кухня, Офис)"
}

EXAMPLES_DB = {
    "person": {"ph": "Напр: Илон Маск в скафандре, Девушка с рыжими волосами...", "help": "Опишите персонажа: пол, возраст, одежду, прическу."},
    "background": {"ph": "Напр: Марсианская пустыня, Сказочный лес, Поверхность Луны...", "help": "Главное место действия."},
    "additional_objects": {"ph": "Напр: Красный спортивный автомобиль, Старая хижина, Лошадь...", "help": "Какие еще предметы добавить в сцену позади персонажа?"},
    "atmosphere": {"ph": "Напр: Проливной дождь, Закат, Туманное утро, Яркое солнце...", "help": "Задает настроение и освещение всей сцены."},
    "lighting": {"ph": "Напр: Кинематографичный красный, Мягкий свет из окна, Неон...", "help": "Свет создает атмосферу. Варианты: Дневной свет, Студийный, Рембрандтовский."},
    "angle": {"ph": "Напр: Анфас, Профиль, Вид снизу, Крупный план глаз...", "help": "Позиция камеры: Вид сверху (Top view), Широкий угол (Wide shot)."},
    "style": {"ph": "Напр: Нуар, Аниме, Марвел, Масло, 3D Рендер, Фотореализм...", "help": "Визуальный стиль. Для фотореализма оставьте пустым или напишите 'Фотореализм'."},
    "materials": {"ph": "Напр: Грубая кожа, Шелк, Ржавый металл, Матовое стекло...", "help": "Из чего сделан объект? Важно для текстуры."},
    "emotion": {"ph": "Напр: Искренняя радость, Ярость, Подозрение...", "help": "Какую эмоцию должен выражать персонаж?"},
    "image_1": {"ph": "Вставьте ссылку на картинку или путь к файлу...", "help": "Основное изображение."},
    "colors": {"ph": "Напр: Черный и Золотой, Пастельные тона, Кислотно-зеленый...", "help": "Доминирующие цвета в дизайне."},
    "screen_type": {"ph": "Напр: Главная, Личный кабинет, Корзина, Настройки...", "help": "Какой экран приложения мы рисуем?"},
    "room_type": {"ph": "Напр: Лофт-гостиная, Спальня в скандинавском стиле...", "help": "Что за помещение?"},
    "design_style": {"ph": "Напр: Минимализм, Гранж, Глассморфизм...", "help": "Общий стиль дизайна."}
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

# --- 6. САЙДБАР: СОЗДАНИЕ ВКЛАДОК ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🍌 PRO MENU</div>', unsafe_allow_html=True)
    # УБРАНЫ ЭМОДЗИ
    tab_menu, tab_history = st.tabs(["Меню", "История"])

# Заполняем вкладку "Меню" СРАЗУ
all_prompts = manager.prompts
options = {data['title']: pid for pid, data in all_prompts.items()}

with tab_menu:
    st.write(" ")
    selected_title = st.selectbox("Выберите задачу:", list(options.keys()))
    selected_id = options[selected_title]
    current_prompt_data = all_prompts[selected_id]
    
    with st.container(border=True):
        st.info(current_prompt_data['description'])

# --- 7. ОСНОВНАЯ ЗОНА (ФОРМА) ---
st.subheader(f"{selected_title}")

template = current_prompt_data['prompt_en']
required_vars = sorted(list(set(re.findall(r'\[(.*?)\]', template))))
user_inputs = {}

if not required_vars:
    st.success("✅ Для этого промпта параметры не требуются. Просто нажмите кнопку.")
    with st.form("prompt_form_empty"):
         # БАНАН ЗДЕСЬ
         submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)
else:
    with st.form("prompt_form"):
        cols = st.columns(2)
        for i, var in enumerate(required_vars):
            col = cols[i % 2]
            label = VAR_MAP.get(var, f"Введите {var}")
            example_data = EXAMPLES_DB.get(var, {})
            placeholder_text = example_data.get("ph", f"Пример для {var}...")
            help_text = example_data.get("help", "Заполните это поле.")

            user_inputs[var] = col.text_input(
                label, 
                key=var,
                placeholder=placeholder_text,
                help=help_text
            )
            
        st.write("---")
        # И ЗДЕСЬ БАНАН
        submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)

# --- 8. ЛОГИКА ГЕНЕРАЦИИ ---
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
                
                # !!! СОХРАНЯЕМ В ИСТОРИЮ (ДО ОТРИСОВКИ ВКЛАДКИ) !!!
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

# --- 9. САЙДБАР: ИСТОРИЯ (ОТРИСОВКА В КОНЦЕ) ---
# Отрисовываем содержимое второй вкладки только сейчас
with tab_history:
    st.write(" ")
    
    # Кнопка очистки БЕЗ ЗНАЧКА
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