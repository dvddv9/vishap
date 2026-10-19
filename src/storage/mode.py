# -*- coding: utf-8 -*-
"""
Режим работы LLM: harness (единственный с v7.0.0).
Сохраняется в data/mode.json для совместимости API.

Прямых обращений к DeepSeek/OpenAI больше нет: всё идёт через DSH harness.
Устаревшее значение в mode.json (auto/cloud/local/...) игнорируется.
"""
import json

from src.config import DATA_DIR

MODE_FILE = DATA_DIR / "mode.json"
DEFAULT_MODE = "harness"
VALID_MODES = ("harness",)


def get_mode() -> str:
    try:
        if MODE_FILE.exists():
            with open(MODE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                mode = data.get("mode", DEFAULT_MODE)
                if mode in VALID_MODES:
                    return mode
    except Exception:
        pass
    return DEFAULT_MODE


def set_mode(mode: str) -> bool:
    if mode not in VALID_MODES:
        return False
    try:
        MODE_FILE.parent.mkdir(exist_ok=True)
        with open(MODE_FILE, "w", encoding="utf-8") as f:
            json.dump({"mode": mode}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
