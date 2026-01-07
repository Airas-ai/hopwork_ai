import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    @property
    def is_gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY)

settings = Settings()

