import json
import re
import os
from datetime import datetime, timezone


RE_VAR = re.compile(r"\[(.*?)\]")

def extract_variables(text):
    """
    Ищет все слова в квадратных скобках [word].
    Возвращает отсортированный список уникальных слов.
    """
    if not text:
        return []
    # set() убирает дубликаты
    # sorted() сортирует по алфавиту
    return sorted(set(RE_VAR.findall(text)))


def normalize_prompts(data):
    """Приводит prompts.json к единому виду.

    Поддерживает два формата:
    1) dict: {"prompt_id": {title, description, prompt_ru, prompt_en}, ...}
    2) list: [{id, title, description, prompt_ru, prompt_en}, ...]

    Возвращает список словарей с полями:
    id, title, description, prompt_ru, prompt_en
    """
    normalized = []

    if isinstance(data, dict):
        for pid, item in data.items():
            item = item or {}
            normalized.append(
                {
                    "id": pid,
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "prompt_ru": item.get("prompt_ru", ""),
                    "prompt_en": item.get("prompt_en", ""),
                }
            )
        return normalized

    if isinstance(data, list):
        for item in data:
            item = item or {}
            pid = item.get("id") or item.get("prompt_id") or item.get("key") or ""
            normalized.append(
                {
                    "id": pid,
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "prompt_ru": item.get("prompt_ru", ""),
                    "prompt_en": item.get("prompt_en", ""),
                }
            )
        return normalized

    raise TypeError(f"Неподдерживаемый формат prompts.json: {type(data).__name__}")


def escape_md_table_cell(text: str) -> str:
    """Экранирует текст, чтобы не ломать Markdown-таблицу."""
    if text is None:
        return ""
    text = str(text)
    # Таблицы Markdown боятся пайпов и переносов строк
    return text.replace("|", "\\|").replace("\r\n", " ").replace("\n", " ")

def generate_docs(json_path='prompts.json', output_path='PROMPTS_REFERENCE.md'):
    # 1. Проверяем наличие базы данных
    if not os.path.exists(json_path):
        print(f"Ошибка: Файл {json_path} не найден.")
        return

    # 2. Читаем JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    prompts = normalize_prompts(data)
    prompts.sort(key=lambda x: (x.get("title", "").casefold(), x.get("id", "")))

    print(f"Обработка {len(prompts)} шаблонов...")

    # 3. Формируем текст документации в формате Markdown
    # Заголовок
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Справочник промптов Nano Banano Pro",
        f"> Этот документ сгенерирован автоматически (**{generated_at}**). Не меняйте его вручную! Любые правки вносите в `prompts.json`.\n",
        "## Быстрая навигация",
        "",
        "| ID (Technical) | Название | Обязательные параметры (Args) | Описание |",
        "|---|---|---|---|",  # Это разделитель для таблицы в Markdown
    ]

    # Проходим по каждому промпту и добавляем строку в таблицу
    for item in prompts:
        # Анализируем английский промпт, так как он основной для генерации
        vars_list = extract_variables(item.get('prompt_en'))
        
        # Оформляем переменные как код (`var`)
        if vars_list:
            vars_formatted = ", ".join([f"`{v}`" for v in vars_list])
        else:
            vars_formatted = "_Нет параметров_"
        
        # Добавляем строку в таблицу
        pid = item.get('id', '')
        title = escape_md_table_cell(item.get('title', ''))
        desc = escape_md_table_cell(item.get('description', ''))

        # Делаем кликабельную навигацию: якорь = prompt_id
        title_link = f"[**{title}**](#{pid})" if pid else f"**{title}**"

        row = f"| `{pid}` | {title_link} | {vars_formatted} | {desc} |"
        lines.append(row)

    # 4. Добавляем детальный вид (полные тексты промптов)
    lines.append("\n## Детальные шаблоны")
    
    for item in prompts:
        pid = item.get('id', '')
        title = item.get('title', '')
        desc = item.get('description', '')
        ru = item.get('prompt_ru', '')
        en = item.get('prompt_en', '')

        # Якорь для быстрой навигации из таблицы выше
        if pid:
            lines.append(f"<a id=\"{pid}\"></a>")
        lines.append(f"### {title}")
        lines.append(f"**ID:** `{pid}`")
        lines.append(f"**Инфо:** {desc}\n")
        lines.append("```text") # Начало блока кода
        lines.append(f"[RU]: {ru}")
        lines.append(f"[EN]: {en}")
        lines.append("```") # Конец блока кода
        lines.append("---") # Горизонтальная линия

    # 5. Сохраняем результат в файл
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"Готово! Документация сохранена в файл: {output_path}")

# Запуск функции
if __name__ == "__main__":
    generate_docs()