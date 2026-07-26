from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    upload_dir: str = "./uploads"
    rabbitmq_url: str
    queue_name: str

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()