import logging
from typing import List

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from .base import BookMatch, SearchStrategy

logger = logging.getLogger(__name__)


class BookScore(BaseModel):
    """Puntuación de un libro individual."""
    book_id: int = Field(description="ID del libro en la base de datos.")
    score: int = Field(
        description="Relevancia del libro para la consulta. Escala del 1 al 10.",
        ge=1,
        le=10,
    )


class SearchResult(BaseModel):
    """Contrato de datos estricto para la respuesta del modelo de IA."""
    matches: List[BookScore] = Field(
        description="Lista de libros con su puntuación, ordenados de mayor a menor relevancia."
    )


def _build_agent(model: str) -> Agent:
    return Agent(
        model=model,
        output_type=SearchResult,
        system_prompt=(
            "Eres un motor de recuperación de información semántica para una "
            "biblioteca universitaria académica. Tu función es conectar consultas "
            "de usuarios con libros del catálogo y asignar una puntuación de relevancia.\n\n"
            "CONTEXTO:\n"
            "Los usuarios son estudiantes universitarios. Sus consultas pueden ser "
            "formales ('libros sobre psicología forense') o informales ('algo cool "
            "de aventuras', 'un libro que me enganche'). Debes interpretar ambos "
            "estilos con igual efectividad.\n\n"
            "CRITERIOS DE PUNTUACIÓN (escala 1-10):\n"
            "- 10: el libro trata el tema directamente y de forma central.\n"
            "- 7-9: el tema aparece de forma importante pero no es el eje principal.\n"
            "- 4-6: relación indirecta, conceptual o parcial.\n"
            "- 1-3: relación muy débil o tangencial.\n"
            "Solo incluye libros que tengan alguna relación con la consulta.\n"
            "No incluyas libros sin ninguna relación.\n\n"
            "ÁREAS ACADÉMICAS VÁLIDAS:\n"
            "Química, medicina, criminología, historia de conflictos, psicología forense "
            "y cualquier disciplina universitaria son búsquedas completamente legítimas.\n\n"
            "INSTRUCCIONES:\n"
            "1. Lee la consulta e interpreta su intención real.\n"
            "2. Evalúa cada libro del catálogo contra esa intención.\n"
            "3. Devuelve solo los libros con alguna relación, con su puntuación.\n"
            "4. Ordena de mayor a menor puntuación.\n"
            "5. Sin texto explicativo. Solo el resultado estructurado."
        ),
    )


class SemanticSearchStrategy(SearchStrategy):

    def __init__(self, model: str):
        self._agent = _build_agent(model)

    def search(self, query: str) -> List[BookMatch]:
        if not query.strip():
            return []

        catalog = self._build_catalog()
        prompt = f"CONSULTA DEL USUARIO: {query}\n\n{catalog}"

        print("=" * 60)
        print(f"PROMPT ENVIADO A LA IA:\n{prompt}")
        print("=" * 60)

        result = self._agent.run_sync(prompt)

        print(f"RESPUESTA DE LA IA: {result.output.matches}")
        print("=" * 60)

        return [
            BookMatch(book_id=m.book_id, score=m.score)
            for m in result.output.matches
        ]

    def _build_catalog(self) -> str:
        from apps.library.models import Book
        books = Book.objects.only('pk', 'title', 'author', 'synopsis')
        if not books.exists():
            return "CATÁLOGO: vacío."
        lines = ["CATÁLOGO DE LIBROS DISPONIBLES:"]
        for book in books:
            lines.append(
                f"ID:{book.pk} | Título: {book.title} | "
                f"Autor: {book.author} | Sinopsis: {book.synopsis}"
            )
        return "\n".join(lines)