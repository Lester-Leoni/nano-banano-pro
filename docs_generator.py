import json
import re
import os

def extract_variables(text):
    """
    Ищет все слова в квадратных скобках [word].
    Возвращает отсортированный список уникальных слов.
    """
    # re.findall находит все совпадения по шаблону
    # set() убирает дубликаты
    # sorted() сортирует по алфавиту
    return sorted(list(set(re.findall(r'\[(.*?)\]', text))))

def generate_docs(json_path='prompts.json', output_path='PROMPTS_REFERENCE.md'):
    # 1. Проверяем наличие базы данных
    if not os.path.exists(json_path):
        print(f"Ошибка: Файл {json_path} не найден.")
        return

    # 2. Читаем JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Обработка {len(data)} шаблонов...")

    # 3. Формируем текст документации в формате Markdown
    # Заголовок
    lines = [
        "# Справочник промптов Nano Banano Pro",
        "> Этот документ сгенерирован автоматически. Не меняйте его вручную! Любые правки вносите в `prompts.json`.\n",
        "## Быстрая навигация",
        "",
        "| ID (Technical) | Название | Обязательные параметры (Args) | Описание |",
        "|---|---|---|---|" # Это разделитель для таблицы в Markdown
    ]

    # Проходим по каждому промпту и добавляем строку в таблицу
    for item in data:
        # Анализируем английский промпт, так как он основной для генерации
        vars_list = extract_variables(item['prompt_en'])
        
        # Оформляем переменные как код (`var`)
        if vars_list:
            vars_formatted = ", ".join([f"`{v}`" for v in vars_list])
        else:
            vars_formatted = "_Нет параметров_"
        
        # Добавляем строку в таблицу
        row = f"| `{item['id']}` | **{item['title']}** | {vars_formatted} | {item['description']} |"
        lines.append(row)

    # 4. Добавляем детальный вид (полные тексты промптов)
    lines.append("\n## Детальные шаблоны")
    
    for item in data:
        lines.append(f"### {item['title']}")
        lines.append(f"**ID:** `{item['id']}`")
        lines.append(f"**Инфо:** {item['description']}\n")
        lines.append("```text") # Начало блока кода
        lines.append(f"[RU]: {item['prompt_ru']}")
        lines.append(f"[EN]: {item['prompt_en']}")
        lines.append("```") # Конец блока кода
        lines.append("---") # Горизонтальная линия

    # 5. Сохраняем результат в файл
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"Готово! Документация сохранена в файл: {output_path}")

# Запуск функции
if __name__ == "__main__":
    generate_docs()