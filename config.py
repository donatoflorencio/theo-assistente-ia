from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv is optional for deployments using exported env vars
    def load_dotenv(*args, **kwargs):
        return False

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("IA_SECRET_KEY")
    IA_PASSWORD = os.getenv("IA_PASSWORD")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    DB_PATH = BASE_DIR / "memoria.db"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    @classmethod
    def validate(cls):
        missing = [
            name for name, value in (
                ("IA_SECRET_KEY", cls.SECRET_KEY),
                ("IA_PASSWORD", cls.IA_PASSWORD),
                ("GEMINI_API_KEY", cls.GEMINI_API_KEY),
            ) if not value
        ]
        if missing:
            raise RuntimeError("Configure as variáveis de ambiente: " + ", ".join(missing))
