from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"
    log_level: str = "INFO"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_top_k: int = 5
    chroma_persist_dir: str = "./data/chroma"
    sqlite_path: str = "./data/ragvault.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
