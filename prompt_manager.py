import json
import os
import re
from typing import Dict, Any


class PromptManager:
    VAR_PATTERN = re.compile(r"\[([a-zA-Z0-9_]+)\]")

    def __init__(self, filepath: str = "prompts.json"):
        self.filepath = filepath
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Файл базы данных '{self.filepath}' не найден!")

        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("prompts.json должен быть словарём вида {id: {title, description, prompt_ru, prompt_en}}")

        # базовая валидация структуры
        for pid, item in data.items():
            if not isinstance(item, dict):
                raise ValueError(f"Промпт '{pid}' должен быть объектом.")
            for k in ("title", "description", "prompt_ru", "prompt_en"):
                if k not in item:
                    raise ValueError(f"Промпт '{pid}' не содержит ключ '{k}'.")

        return data

    def generate(self, prompt_id: str, language: str = "en", **user_inputs: Any) -> str:
        if prompt_id not in self.prompts:
            raise ValueError(f"Промпт с ID '{prompt_id}' не найден.")

        prompt_data = self.prompts[prompt_id]
        key = f"prompt_{language}"

        if key not in prompt_data:
            raise ValueError(f"Язык '{language}' не поддерживается для '{prompt_id}'.")

        template = prompt_data[key]
        required_vars = set(self.VAR_PATTERN.findall(template))

        missing = [v for v in sorted(required_vars) if v not in user_inputs]
        if missing:
            raise ValueError(f"Не заполнены обязательные поля: {', '.join(missing)}")

        def repl(match: re.Match) -> str:
            var = match.group(1)
            return str(user_inputs.get(var, match.group(0)))

        return self.VAR_PATTERN.sub(repl, template)

    def list_available_prompts(self):
        return list(self.prompts.keys())
