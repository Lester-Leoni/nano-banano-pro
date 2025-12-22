import json
import os
import re

class PromptManager:  # <--- Двоеточие здесь было пропущено
    def __init__(self, filepath='prompts.json'):  # <--- И здесь
        """
        Конструктор класса. Запускается автоматически при создании объекта.
        """
        self.filepath = filepath
        self.prompts = self._load_prompts()

    def _load_prompts(self):  # <--- И здесь
        """
        Приватный метод. Читает файл с диска.
        """
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Файл базы данных {self.filepath} не найден!")
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {item['id']: item for item in data}

    def generate(self, prompt_id, language='en', **user_inputs):  # <--- И здесь
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
        required_vars = re.findall(r'\[(.*?)\]', template)
        missing = [var for var in set(required_vars) if var not in user_inputs]
        
        if missing:
            raise ValueError(f"Ошибка! Не заполнены обязательные поля: {', '.join(missing)}")

        # Шаг 3: Подстановка
        final_text = template
        for key, value in user_inputs.items():
            final_text = final_text.replace(f"[{key}]", str(value))
            
        return final_text

    def list_available_prompts(self):  # <--- И здесь
        return list(self.prompts.keys())