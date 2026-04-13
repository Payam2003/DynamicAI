# Tiene configurazioni e variabili d'ambiente:
# API key, modello, upload, limiti, ecc.
# Tiene configurazioni e variabili d'ambiente:
# API key, modello, upload, limiti, ecc.
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv(
        "OPENROUTER_MODEL",
        "openrouter/free"
    )
    OPENROUTER_URL: str = os.getenv(
        "OPENROUTER_URL",
        "https://openrouter.ai/api/v1/chat/completions"
    )

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