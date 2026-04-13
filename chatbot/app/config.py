# Tiene configurazioni e variabili d'ambiente:
# API key, modello, upload, limiti, ecc.
# Tiene configurazioni e variabili d'ambiente:
# API key, modello, upload, limiti, ecc.
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "app/storage")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

    ALLOWED_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".pdf",
        ".txt",
    }


settings = Settings()