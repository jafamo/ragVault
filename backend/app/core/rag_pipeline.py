from collections.abc import Callable
from typing import TypedDict

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel

from app.core.prompts import RAG_PROMPT, TITLE_PROMPT
from app.repositories.vector_store import VectorStoreRepository

NO_DOCUMENTS_ANSWER = (
    "Todavía no hay ningún documento indexado, así que no tengo "
    "información sobre la que responder. Sube un documento primero."
)


class Source(TypedDict):
    document_id: str
    document_name: str
    page: int | None
    chunk_text: str
    similarity_score: float


class PipelineContext(TypedDict, total=False):
    question: str
    top_k: int
    retrieved: list[tuple[Document, float]]
    prompt: str
    answer: str


PipelineStep = Callable[[PipelineContext], PipelineContext]


def make_retrieve_step(vector_store: VectorStoreRepository) -> PipelineStep:
    def retrieve_step(ctx: PipelineContext) -> PipelineContext:
        ctx["retrieved"] = vector_store.similarity_search(ctx["question"], ctx["top_k"])
        return ctx

    return retrieve_step


def prompt_step(ctx: PipelineContext) -> PipelineContext:
    context_text = "\n\n".join(doc.page_content for doc, _ in ctx["retrieved"])
    ctx["prompt"] = RAG_PROMPT.format(context=context_text, question=ctx["question"])
    return ctx


def make_generate_step(llm: BaseChatModel) -> PipelineStep:
    def generate_step(ctx: PipelineContext) -> PipelineContext:
        response = llm.invoke(ctx["prompt"])
        ctx["answer"] = response.content if hasattr(response, "content") else str(response)
        return ctx

    return generate_step


def sources_from_context(ctx: PipelineContext) -> list[Source]:
    sources: list[Source] = []
    for doc, score in ctx.get("retrieved", []):
        sources.append(
            Source(
                document_id=doc.metadata.get("document_id", ""),
                document_name=doc.metadata.get("source", ""),
                page=doc.metadata.get("page"),
                chunk_text=doc.page_content,
                similarity_score=score,
            )
        )
    return sources


def run_pipeline(
    question: str,
    vector_store: VectorStoreRepository,
    llm: BaseChatModel,
    top_k: int,
) -> tuple[str, list[Source]]:
    steps: list[PipelineStep] = [
        make_retrieve_step(vector_store),
        prompt_step,
        make_generate_step(llm),
    ]

    ctx: PipelineContext = {"question": question, "top_k": top_k}
    ctx = steps[0](ctx)

    if not ctx["retrieved"]:
        return NO_DOCUMENTS_ANSWER, []

    for step in steps[1:]:
        ctx = step(ctx)

    return ctx["answer"], sources_from_context(ctx)


def generate_title(llm: BaseChatModel, first_message: str) -> str:
    response = llm.invoke(TITLE_PROMPT.format(first_message=first_message))
    content = response.content if hasattr(response, "content") else str(response)
    return content.strip()
