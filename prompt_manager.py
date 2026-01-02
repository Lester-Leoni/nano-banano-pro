import json
import os
import re
import logging
from typing import Dict, Any


logger = logging.getLogger(__name__)


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

        for pid, item in data.items():
            if not isinstance(item, dict):
                raise ValueError(f"Промпт '{pid}' должен быть объектом.")
            for k in ("title", "description", "prompt_ru", "prompt_en"):
                if k not in item:
                    raise ValueError(f"Промпт '{pid}' не содержит ключ '{k}'.")

        return data

    def generate(self, prompt_id: str, template_lang: str = "en", **user_inputs: Any) -> str:
        if prompt_id not in self.prompts:
            raise ValueError(f"Промпт с ID '{prompt_id}' не найден.")

        prompt_data = self.prompts[prompt_id]
        key = f"prompt_{template_lang}"

        if key not in prompt_data:
            raise ValueError(f"Язык '{template_lang}' не поддерживается для '{prompt_id}'.")

        template = prompt_data[key]
        required_vars = set(self.VAR_PATTERN.findall(template))

        # Валидация (мягкая).
        #
        # UI и шаблоны могут эволюционировать независимо. Если шаблон содержит переменные,
        # которые UI по какой-то причине не передал (скрытое поле, разные версии JSON, и т.д.),
        # падать нельзя: лучше безопасно подставить пустую строку и продолжить.
        missing = [v for v in sorted(required_vars) if v not in user_inputs]
        if missing:
            logger.warning("Prompt '%s' missing vars: %s", prompt_id, ", ".join(missing))
            for v in missing:
                user_inputs[v] = ""

        def repl(match: re.Match) -> str:
            var = match.group(1)
            # Missing vars are substituted with empty strings.
            val = user_inputs.get(var, "")
            if val is None:
                return ""
            return str(val)

        return self.VAR_PATTERN.sub(repl, template)

    def list_available_prompts(self):
        return list(self.prompts.keys())