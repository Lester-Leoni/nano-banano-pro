from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from docs_generator import generate_docs  # noqa: E402

if __name__ == "__main__":
    generate_docs(json_path=str(BASE / "prompts.json"), output_path=str(BASE / "PROMPTS_REFERENCE.md"))
    print("✅ PROMPTS_REFERENCE.md regenerated")
