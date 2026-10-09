from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

HOME = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=HOME / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_TITLE: str
    VERSION: str
    APP_ENV: str
    DEBUG: bool

    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 240
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    DB_ENGINE:str
    DB_HOST:str
    DB_PORT:int
    DB_USER:str
    DB_PASSWORD:str
    DB_NAME:str

    @property
    def TORTOISE_ORM(self) -> dict:
        if self.DB_ENGINE != "mysql":
            raise ValueError("This database engine only supports MySQL!")

        return {
            "connections":{
                "default":{
                    "engine":"tortoise.backends.mysql",
                    "credentials":{
                        "host": self.DB_HOST,
                        "port": self.DB_PORT,
                        "user": self.DB_USER,
                        "password": self.DB_PASSWORD,
                        "database": self.DB_NAME,
                    },
                }
            },
            "apps":{
                "models":{
                    "models":["models"],
                    "default_connection": "default",
                    "migrations": "models.migrations",
                }
            },
            "use_tz" : False,
            "timezone": "Asia/Shanghai",
        }



settings = Settings()
