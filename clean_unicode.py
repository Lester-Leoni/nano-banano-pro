from pathlib import Path

path = Path("app_fixed.py")

text = path.read_text(encoding="utf-8")

# заменяем ВСЕ неразрывные пробелы и странные юникод-пробелы
bad_spaces = [
    "\u00A0",  # NBSP
    "\u2007",
    "\u202F",
]

for ch in bad_spaces:
    text = text.replace(ch, " ")

path.write_text(text, encoding="utf-8")

print("✅ app_fixed.py очищен от Unicode-пробелов")
