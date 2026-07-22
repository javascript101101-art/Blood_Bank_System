import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database URLs
    GLOBAL_DATABASE_URL: str = os.getenv("GLOBAL_DATABASE_URL", "postgresql://postgres:123456@localhost/blood_global")
    LOCAL_DATABASE_URL: str = os.getenv("LOCAL_DATABASE_URL", "postgresql://postgres:123456@localhost/blood_local_hospital_a")
    
    # Server Mode
    SERVER_MODE: str = os.getenv("SERVER_MODE", "local")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-do-not-use-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    @property
    def DATABASE_URL(self) -> str:
        if self.SERVER_MODE == "global":
            return self.GLOBAL_DATABASE_URL
        return self.LOCAL_DATABASE_URL

settings = Settings()