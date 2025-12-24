import json
import os
import re

class PromptManager:
    def __init__(self, filepath='prompts.json'):
        """
        Конструктор класса. Запускается автоматически при создании объекта.
        """
        self.filepath = filepath
        self.prompts = self._load_prompts()

    def _load_prompts(self):
        """
        Приватный метод. Читает файл с диска.
        """
        if not os.path.exists(self.filepath):
            # Если файла нет, создаем пустой словарь, чтобы программа не падала сразу,
            # но лучше выбросить ошибку, если логика строго требует файл.
            raise FileNotFoundError(f"Файл базы данных {self.filepath} не найден!")
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # ВАЖНОЕ ИСПРАВЛЕНИЕ:
            # Наш JSON — это уже словарь {key: value}, поэтому просто возвращаем data.
            # Не нужно пытаться перебирать его как список.
            return data

    def generate(self, prompt_id, language='en', **user_inputs):
        """
        Основной метод генерации.
        """
        # Шаг 1: Получение шаблона
        if prompt_id not in self.prompts:
            raise ValueError(f"Промпт с ID '{prompt_id}' не найден.")
        
        prompt_data = self.prompts[prompt_id]
        key = f"prompt_{language}"
        
        if key not in prompt_data:
             raise ValueError(f"Язык '{language}' не поддерживается.")
             
        template = prompt_data[key]

        # Шаг 2: Валидация
        # Ищем все переменные в скобках [variable]
        required_vars = re.findall(r'\[(.*?)\]', template)
        # Проверяем, есть ли они в переданных user_inputs
        missing = [var for var in set(required_vars) if var not in user_inputs]
        
        if missing:
            # Можно сделать мягче: не ронять программу, а возвращать сообщение об ошибке,
            # но raise ValueError — это правильный программный подход.
            raise ValueError(f"Ошибка! Не заполнены обязательные поля: {', '.join(missing)}")

        # Шаг 3: Подстановка
        final_text = template
        for key, value in user_inputs.items():
            # Заменяем [ключ] на значение
            final_text = final_text.replace(f"[{key}]", str(value))
            
        return final_text

    def list_available_prompts(self):
        """
        Возвращает список доступных ключей (ID) промптов.
        """
        return list(self.prompts.keys())