"""
Каталог промптов и UX-метаданные.

Задача: держать "продуктовые" данные отдельно от app.py, чтобы
1) навигация масштабировалась,
2) UI был понятным (категории, "прост/про"),
3) можно было легко добавлять новые промпты.

Если assets/ отсутствует — приложение должно работать без превью.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import random
import re


# -------------------------
# Категории задач (навигация)
# -------------------------
CATEGORY_DEFS: Dict[str, Dict[str, str]] = {
    "people": {"label": "📸 Люди", "hint": "Портреты, лицо, эмоции, одежда, команда"},
    "editing": {"label": "🛠️ Редактирование", "hint": "Удаление/замена объектов, фон, апскейл, релайт"},
    "design": {"label": "🎨 Дизайн & Маркетинг", "hint": "Лого, мокапы, карточки товаров, текст-дизайн"},
    "art": {"label": "🖍️ Арт & Иллюстрация", "hint": "Скетчи, комиксы, стикеры, персонажи"},
    "arch": {"label": "🏗️ Архитектура & Интерьер", "hint": "Интерьеры, экстерьеры, изометрия"},
    "video": {"label": "🎬 Видео & YouTube", "hint": "Тумбы, сториборд, cinematic look"},
}

CATEGORY_ORDER = ["people", "editing", "design", "art", "arch", "video"]

PROMPT_CATEGORY: Dict[str, str] = {
    "upscale_restore": "editing",
    "old_photo_restore": "editing",
    "studio_portrait": "people",
    "background_change": "editing",
    "face_swap": "people",
    "expression_change": "people",
    "pose_change": "people",
    "camera_angle_change": "editing",
    "cloth_swap": "people",
    "object_removal": "editing",
    "object_addition": "editing",
    "semantic_replacement": "editing",
    "scene_relighting": "editing",
    "total_look_builder": "people",
    "team_composite": "people",
    "scene_composite": "editing",
    "product_card": "design",
    "mockup_generation": "design",
    "environmental_text": "design",
    "knolling_photography": "design",
    "logo_creative": "design",
    "logo_stylization": "design",
    "ui_design": "design",
    "text_design": "design",
    "seamless_pattern": "design",
    "technical_blueprint": "design",
    "exploded_view": "design",
    "anatomical_infographic": "design",
    "image_restyling": "art",
    "sketch_to_photo": "art",
    "character_sheet": "art",
    "sticker_pack": "art",
    "comic_page": "art",
    "interior_design": "arch",
    "architecture_exterior": "arch",
    "isometric_room": "arch",
    "storyboard_sequence": "video",
    "cinematic_atmosphere": "video",
    "youtube_thumbnail": "video",
    "macro_extreme": "people",
}

# -------------------------
# NEG профили по смыслу (мэпится на группы в app.py)
# -------------------------
NEG_PROFILE_DEFS: Dict[str, Dict[str, str]] = {
    "auto": {"label": "Авто (по задаче)", "hint": "Рекомендуется: профиль подбирается автоматически"},
    "people": {"label": "Портрет / Люди", "hint": "Сходство, кожа, пальцы, текст"},
    "editing": {"label": "Редактирование", "hint": "Швы, ореолы, некорректные тени, масштаб"},
    "design": {"label": "Дизайн / Текст", "hint": "Ошибки текста, кривые линии, артефакты"},
    "art": {"label": "Арт / Иллюстрация", "hint": "Линии, грязь, деформация, watermark"},
    "arch": {"label": "Интерьер / Архитектура", "hint": "Геометрия, перспективы, швы, текст"},
    "video": {"label": "Кино / VFX", "hint": "Фликер/шум/ореолы, текст, watermark"},
    "universal": {"label": "Универсальный", "hint": "Безопасный базовый профиль"},
}

NEG_PROFILE_ORDER = ["auto", "people", "editing", "design", "art", "arch", "video", "universal"]


# -------------------------
# Режимы UI
# -------------------------
UI_MODES = {
    "simple": "Просто",
    "pro": "Про",
}


# -------------------------
# Поля: приоритеты для группировки (Hero/Details/Settings)
# -------------------------
TECH_VARS = {
    "aspect_ratio", "quality", "lens_match_mode", "focus_stacking",
    "labels_visibility", "show_preview", "seed", "steps", "cfg_scale",
}

ATTACHMENT_PREFIXES = ("image", "ref", "reference", "mask", "source")

CONTENT_HINT_VARS = {
    "subject", "person", "product", "object", "scene", "description", "prompt", "idea",
    "text", "title", "headline", "slogan", "caption", "brand", "logo_text",
    "room", "room_type", "interior", "exterior",
}

DETAIL_VARS = {
    "style", "lighting", "mood", "background", "color", "palette", "camera",
    "lens", "composition", "pose", "outfit", "accessories", "shoes",
    "material", "texture", "environment",
}


VAR_TOKEN_RE = re.compile(r"\[([a-zA-Z0-9_]+)\]")


def strip_numeric_prefix(title: str) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", title or "").strip()


def extract_vars(prompt_text: str) -> List[str]:
    return sorted(set(VAR_TOKEN_RE.findall(prompt_text or "")))


def is_attachment_var(var: str) -> bool:
    v = (var or "").lower()
    # image_1, image_2, ref_image, mask_1 ...
    return v.startswith(ATTACHMENT_PREFIXES)


def group_var(var: str) -> str:
    """Возвращает 'hero' | 'details' | 'settings'."""
    v = (var or "").lower()
    if v in TECH_VARS:
        return "settings"
    if is_attachment_var(v):
        return "hero"
    if v in CONTENT_HINT_VARS:
        return "hero"
    if v in DETAIL_VARS:
        return "details"
    # дефолт: детали
    return "details"


# -------------------------
# Magic Fill пресеты (обучает пользователя)
# -------------------------
PRESETS = {
    "style": [
        "cinematic, high-end commercial photography, natural skin texture",
        "minimalist Scandinavian interior, soft daylight, clean lines",
        "bold graphic design, modern typography, premium brand look",
        "anime cel shading, vibrant colors, expressive character design",
        "film still, 35mm grain, moody lighting, shallow depth of field",
    ],
    "lighting": [
        "cinematic lighting, blue hour, neon rim light",
        "soft diffused daylight through large window",
        "studio three-point lighting, clean highlights",
        "dramatic chiaroscuro, strong key light, deep shadows",
        "warm golden hour light, gentle shadows",
    ],
    "background": [
        "clean neutral background, subtle gradient",
        "urban night street with neon reflections",
        "minimal studio backdrop with soft haze",
        "cozy interior with warm tones and bokeh lights",
        "natural outdoor environment, soft depth of field",
    ],
    "mood": [
        "confident and premium",
        "friendly and approachable",
        "dramatic and cinematic",
        "calm and minimal",
        "playful and energetic",
    ],
    "description": [
        "A premium product hero shot with realistic materials and crisp details",
        "A cinematic portrait with natural skin, accurate facial features, and soft bokeh",
        "A clean marketing layout with strong hierarchy, readable text, and balanced spacing",
        "A cozy modern interior with natural light, realistic textures, and correct perspective",
        "A dynamic scene with clear focal point, depth, and consistent lighting",
    ],
    "text": [
        "LIMITED DROP",
        "NEW COLLECTION",
        "SUMMER SALE 50%",
        "PRO EDIT",
        "NANO BANANO",
    ],
}


def magic_value(var: str, category_key: Optional[str] = None) -> str:
    v = (var or "").lower()
    # Простые эвристики
    if "style" in v:
        return random.choice(PRESETS["style"])
    if "light" in v:
        return random.choice(PRESETS["lighting"])
    if "background" in v or "bg" == v:
        return random.choice(PRESETS["background"])
    if "mood" in v or "emotion" in v:
        return random.choice(PRESETS["mood"])
    if "text" in v or "title" in v or "headline" in v or "slogan" in v:
        return random.choice(PRESETS["text"])
    if "desc" in v or "description" in v or "prompt" in v or "idea" in v:
        return random.choice(PRESETS["description"])

    # Категорийные подсказки для "главного объекта"
    if v in ("subject", "person", "model"):
        return "a confident person, natural skin, realistic proportions"
    if v in ("product", "object"):
        return "a premium product with realistic materials, clean reflections"
    if v in ("room_type", "room", "interior"):
        return "modern cozy living room, Scandinavian style, daylight"
    if v in ("exterior",):
        return "modern house exterior, golden hour, clean landscaping"

    # запасной вариант
    return ""


def make_task_badges(vars_list: List[str]) -> List[str]:
    """Небольшие бейджи для карточки задачи."""
    vars_set = set(v.lower() for v in vars_list)
    badges = []
    if any(v.startswith("image") or v.startswith("ref") for v in vars_set):
        badges.append("референс")
    if any("text" in v or "headline" in v or "slogan" in v for v in vars_set):
        badges.append("текст")
    if any(v in TECH_VARS for v in vars_set):
        badges.append("настройки")
    return badges
