from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("IA_SECRET_KEY", "dev-secret-key")
    IA_PASSWORD = os.getenv("IA_PASSWORD", "dev-password")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    DB_PATH = BASE_DIR / "memoria.db"

    @classmethod
    def validate(cls) -> None:
        missing = []
        if not cls.SECRET_KEY:
            missing.append("IA_SECRET_KEY")
        if not cls.IA_PASSWORD:
            missing.append("IA_PASSWORD")
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")

        if missing:
            raise RuntimeError(
                "Configure as variáveis de ambiente ausentes: " + ", ".join(missing)
            )


Config.validate()
