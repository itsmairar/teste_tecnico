from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TITLE: str
    API_V1_STR: str
    MONGO_URI: str
    MONGO_DB: str
    RELOAD: bool = True
    BASIC_AUTH_USERNAME: str
    BASIC_AUTH_PASSWORD: str
    REDIS_URI: str

    class Config:
        env_file = ".env"


settings = Settings()
