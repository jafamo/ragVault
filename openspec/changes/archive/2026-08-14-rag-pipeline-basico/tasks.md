## 1. Dependencias y configuración

- [x] 1.1 Añadir a `backend/pyproject.toml`: `langchain`,
      `langchain-community`, `langchain-chroma`, `langchain-ollama`,
      `chromadb`, `pypdf`, `sqlalchemy`, `python-multipart`
- [x] 1.2 Ampliar `backend/app/config.py` (`Settings`): `chunk_size=1000`,
      `chunk_overlap=200`, `retrieval_top_k=5`,
      `chroma_persist_dir="./data/chroma"`, `sqlite_path="./data/ragvault.db"`
- [x] 1.3 Añadir `./backend/data` como volumen en `docker-compose.yml`
      (servicio `ragvault-backend`) para persistir SQLite/Chroma entre
      reinicios del contenedor

## 2. Document loaders (Strategy + Factory)

- [x] 2.1 `backend/app/document_processing/loaders/base.py`: interfaz
      `DocumentLoader` (`load(path) -> list[LangChain Document]`)
- [x] 2.2 `backend/app/document_processing/loaders/pdf_loader.py`:
      implementación con `PyPDFLoader`
- [x] 2.3 `backend/app/document_processing/loader_factory.py`: mapeo
      extensión → loader, `UnsupportedFormatError` para el resto
- [x] 2.4 `backend/app/document_processing/splitter.py`:
      `RecursiveCharacterTextSplitter` parametrizado desde `Settings`

## 3. Repositories

- [x] 3.1 `backend/app/repositories/vector_store.py`:
      `VectorStoreRepository` (ChromaDB vía `langchain-chroma`):
      `add_chunks(document_id, chunks)`, `similarity_search(query, k)`
- [x] 3.2 `backend/app/models/entities.py`: modelo SQLAlchemy `Document`
      (id, filename, format, uploaded_at, chunk_count)
- [x] 3.3 `backend/app/repositories/document_repo.py`:
      `DocumentRepository` (`create`, `get`, `list`), `Base.metadata.create_all()`
      al arrancar la app (sin Alembic todavía, ver design.md)

## 4. Core RAG (LLM, embeddings, pipeline, prompts)

- [x] 4.1 `backend/app/core/embeddings.py`: wrapper `OllamaEmbeddings`
      configurado desde `Settings`
- [x] 4.2 `backend/app/core/llm_provider.py`: wrapper `ChatOllama`
      configurado desde `Settings` (Strategy, listo para otros providers)
- [x] 4.3 `backend/app/core/prompts.py`: `RAG_PROMPT` copiado literal de
      `rag_vault_plan.md` §7.4
- [x] 4.4 `backend/app/core/rag_pipeline.py`: `PipelineContext` +
      `retrieve_step`, `prompt_step`, `generate_step` + `run_pipeline()`
      (Chain of Responsibility, ver design.md decisión 4)

## 5. Endpoints (Facade)

- [x] 5.1 `backend/app/api/routes/documents.py`: `POST /upload`
      (multipart), orquesta loader → splitter → embeddings →
      `VectorStoreRepository` → `DocumentRepository`, devuelve metadata o
      415/422 controlado
- [x] 5.2 `backend/app/api/routes/chat.py`: `POST /chat`, ejecuta
      `run_pipeline`, devuelve `{answer, sources[]}`; responde con mensaje
      explícito (200) si no hay documentos indexados
- [x] 5.3 `backend/app/models/schemas.py`: Pydantic schemas de
      request/response de `/upload` y `/chat`
- [x] 5.4 Registrar ambos routers en `backend/app/main.py`

## 6. Tests backend

- [x] 6.1 `tests/unit/test_loader_factory.py`: extensión soportada vs. no
      soportada
- [x] 6.2 `tests/unit/test_splitter.py`: chunking respeta tamaño/overlap
      configurados
- [x] 6.3 `tests/unit/test_rag_pipeline.py`: pasos del pipeline con
      `VectorStoreRepository`/LLM mockeados
- [x] 6.4 `tests/unit/test_chat_route.py`: `/chat` con pipeline mockeado
      (éxito, sin documentos indexados)
- [x] 6.5 `tests/unit/test_upload_route.py`: `/upload` con loader/repos
      mockeados (éxito, extensión no soportada)

## 7. Frontend — servicios y stores

- [x] 7.1 `frontend/src/services/api.ts`: `uploadDocument(file)`,
      `sendChatMessage(message)` contra el backend real
- [x] 7.2 `frontend/src/stores/chatStore.ts`: `sendMessage` pasa a ser
      async, llama a `sendChatMessage`, gestiona estado de carga y de
      error (sin placeholder de maqueta)

## 8. Frontend — UI

- [x] 8.1 `frontend/src/components/Documents/UploadZone.tsx`: input de
      fichero oculto + `dragover`/`drop`, llama a `uploadDocument`,
      muestra resultado (nombre + nº de chunks) o error
- [x] 8.2 `frontend/src/components/Chat/ChatWindow.tsx` /
      `InputBar.tsx`: estado de carga mientras se espera `POST /chat`
      (deshabilitar input/botón, indicador visual mínimo por skin)
- [x] 8.3 `frontend/src/components/Chat/MessageBubble.tsx`: soporte visual
      para mensaje de error (además de user/assistant/system ya existentes)

## 9. Verificación final

- [x] 9.1 `pytest` en verde en `backend/` (vía `rtk proxy` si hace falta
      bypassear el hook)
- [x] 9.2 Verificación manual end-to-end con Ollama real: subir un PDF
      real por `docker compose up`, preguntar algo sobre su contenido
      desde la UI (ambos skins) y comprobar que la respuesta y las fuentes
      citadas son reales, no el marcador de posición de la maqueta
- [x] 9.3 `openspec validate rag-pipeline-basico` sin errores
- [x] 9.4 Ejecutar la skill `ragvault-pattern-review` sobre el diff
