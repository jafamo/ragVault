RAG_PROMPT = """Eres un asistente que responde preguntas basándose
exclusivamente en el contexto proporcionado. Si la información no
está en el contexto, di que no tienes suficiente información.

Contexto:
{context}

Pregunta: {question}

Respuesta (cita las fuentes entre corchetes [nombre_documento, página]):"""
