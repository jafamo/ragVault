RAG_PROMPT = """Eres un asistente que responde preguntas basándose
exclusivamente en el contexto proporcionado. Si la información no
está en el contexto, di que no tienes suficiente información.

Contexto:
{context}

Pregunta: {question}

Respuesta (cita las fuentes entre corchetes [nombre_documento, página]):"""

TITLE_PROMPT = """Genera un título corto (máximo 6 palabras) que resuma
la intención de esta pregunta. Responde SOLO con el título, sin comillas
ni puntuación final.

Pregunta: {first_message}

Título:"""
