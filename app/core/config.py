from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    PORT: int
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MAX_FAILED_ATTEMPTS: int
    BAN_DURATION_MINUTES: int
    letsencrypt_email: str = ""
    letsencrypt_host: str = ""
    virtual_host: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
