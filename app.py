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

# --- 3. HISTORY ---
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

# --- 4. CSS (VISUAL FIXES + TRANSPARENT HEADER) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

/* =========================================================
   🍌 HEADER & ARROW FIXES
   ========================================================= */

/* 1. Делаем хедер полностью прозрачным */
header[data-testid="stHeader"] {
    background: transparent !important;
    background-color: transparent !important;
    border-bottom: none !important;
    box-shadow: none !important;
}

/* 2. Удаляем цветную полоску декорации */
[data-testid="stDecoration"] { display: none !important; }

/* 3. Красим стрелочку (кнопку сайдбара) в ЗОЛОТО */
button[data-testid="stSidebarCollapsedControl"] {
    color: #FFD700 !important;
    border: none !important;
    background: transparent !important;
}
button[data-testid="stSidebarCollapsedControl"]:hover {
    color: #FFC300 !important;
    background: transparent !important;
}

/* 4. Меню "три точки" справа сверху */
div[data-testid="stToolbar"] {
    right: 2rem;
    top: 0.5rem;
}

/* Скрываем футер */
footer { display: none !important; }

/* Сдвигаем контент чуть выше */
.main .block-container { 
    padding-top: 3rem !important; 
}

/* =========================================================
   ⬇️ ОСНОВНОЙ ВИЗУАЛ
   ========================================================= */

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
    color: #000000 !important; /* Черный текст на кнопках */
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

/* SIDEBAR FIRST BUTTON (PRO MENU) STYLE */
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

# --- 5. BANNER ---
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

# --- 6. DATA DICTS (UPDATED FOR NEW PROMPTS) ---
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

EXAMPLES_DB = {
    "image_1": {"ph": "Ссылка на фото...", "help": "Основное изображение."},
    "image_2": {"ph": "Ссылка на референс...", "help": "Дополнительное изображение."},
    "aspect_ratio": {"ph": "16:9, 4:3, 1:1...", "help": "Соотношение сторон итоговой картинки."},
    "background": {"ph": "На Марсе, В офисе, Белая студия...", "help": "Где происходит действие?"},
    "lighting": {"ph": "Cinematic, Softbox, Neon, Natural...", "help": "Схема освещения."},
    "fabric_material": {"ph": "Silk, Denim, Leather, Cotton...", "help": "Из чего сделана одежда?"},
    "lens_match_mode": {"ph": "feel или strict", "help": "feel - визуальное сходство, strict - точное фокусное."},
    "placement_details": {"ph": "На столе слева, В руке героя...", "help": "Куда именно вставить объект?"},
    "print_finish": {"ph": "Matte paper, Gold foil, Glossy plastic...", "help": "Фактура материала для мокапа."},
    "show_preview": {"ph": "yes / no", "help": "yes - покажет плитку 2х2, no - один паттерн."},
    "focus_stacking": {"ph": "on / off", "help": "Включить ли полную резкость по всей глубине?"},
    "platform": {"ph": "iOS, Android, Web", "help": "Для какой системы дизайн?"},
    "level": {"ph": "medium", "help": "Насколько сильно менять стиль (light/medium/strong)."},
    "person": {"ph": "Илон Маск, Девушка, Бэтмен...", "help": "Главный герой."}
}

# --- 7. ENGINE ---
@st.cache_resource
def load_engine():
    if not os.path.exists('prompts.json'):
        return None
    return PromptManager('prompts.json')

manager = load_engine()

if not manager:
    st.error("❌ Файл `prompts.json` не найден. Загрузите его в ту же папку.")
    st.stop()

# --- 8. SIDEBAR ---
with st.sidebar:
    # Кнопка для визуального стиля (как на скриншоте)
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

# --- 9. MAIN FORM ---
st.subheader(f"{selected_title}")

template = current_prompt_data['prompt_en']
# Ищем переменные в квадратных скобках
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
            # Берем красивое название из VAR_MAP или оставляем как есть
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
        submitted = st.form_submit_button("🍌 Сгенерировать Промпт", use_container_width=True)

# --- 10. GENERATION LOGIC ---
if 'submitted' in locals() and submitted:
    # Проверка на пустые поля
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
                    # Если ссылка, не переводим
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
    st.markdown("Made with ❤️ for Nano Banano Pro")