from langchain_ollama import ChatOllama

from app.config import settings


def get_llm(model: str | None = None) -> ChatOllama:
    return ChatOllama(
        model=model or settings.ollama_model,
        base_url=settings.ollama_base_url,
    )
