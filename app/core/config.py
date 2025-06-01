from pydantic_settings import BaseSettings

class Config(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "mydatabase"
    SECRET_KEY: str = "super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:5173"
    TOKEN_TYPE: str = "bearer"

    COOKIE_SECURE: bool = False
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "Strict"
    COOKIE_NAME: str = "access_token"

    GPU_HOST: str = "172.16.200.197"
    GPU_USER: str = "ubuntu"
    GPU_KEY_PATH: str = "C:\\Users\\zorigoo\\.ssh\\test.pem"
    JUPYTER_IMAGE: str = "jupyter/datascience-notebook"

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "zorigoo20022@gmail.com"
    SMTP_PASSWORD: str = "kpfj amfe znha oqkd"
    SMTP_FROM_EMAIL: str = "zorigoo20022@gmail.com"

    class Config:
        env_file = ".env"

config = Config()
