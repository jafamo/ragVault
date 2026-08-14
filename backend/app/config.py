from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
