from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ADMIN_KEY: str = "change-this-before-deploy"
    FAQ_CSV_PATH: str = "data/faq.csv"
    FEEDBACK_LOG_PATH: str = "data/feedback.jsonl"
    HIGH_CONFIDENCE_THRESHOLD: float = 0.72
    LOW_CONFIDENCE_THRESHOLD: float = 0.45
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
