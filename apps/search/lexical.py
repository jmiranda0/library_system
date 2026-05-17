"""
Estrategia de búsqueda léxica exacta.

El fallback léxico no tiene puntuación semántica real.
Asigna score=5 a todos los resultados — indica coincidencia
parcial sin poder determinar cuál es más relevante que otro.
"""
from typing import List

from django.db.models import Q

from .base import BookMatch, SearchStrategy


class LexicalSearchStrategy(SearchStrategy):

    def search(self, query: str) -> List[BookMatch]:
        if not query.strip():
            return []

        from apps.library.models import Book

        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(synopsis__icontains=query)
        ).values_list('id', flat=True)

        # Score 5 para todos — coincidencia léxica sin ranking semántico
        return [BookMatch(book_id=pk, score=5) for pk in books]