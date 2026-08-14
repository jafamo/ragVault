from langchain_ollama import ChatOllama

from app.config import settings


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
    )
