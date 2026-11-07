from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv() -> bool:
        return False


BASE_DIR = Path(__file__).resolve().parent
if not load_dotenv(BASE_DIR / ".env"):
    # Ignore if .env is absent; the app still works with exported environment variables.
    pass


class Config:
    SECRET_KEY = os.getenv("IA_SECRET_KEY", "dev-secret-key")
    IA_PASSWORD = os.getenv("IA_PASSWORD", "dev-password")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    DB_PATH = BASE_DIR / "memoria.db"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

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
