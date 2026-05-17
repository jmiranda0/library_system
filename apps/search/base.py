from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class BookMatch:
    """Representa un libro con su puntuación de relevancia."""
    book_id: int
    score: int  # 1 a 10


class SearchStrategy(ABC):
    """Contrato abstracto para todas las estrategias de búsqueda."""

    @abstractmethod
    def search(self, query: str) -> List[BookMatch]:
        """
        Ejecuta una búsqueda y devuelve libros con puntuación de relevancia.

        Args:
            query: Consulta en lenguaje natural del usuario.

        Returns:
            Lista de BookMatch ordenada de mayor a menor relevancia.
            Lista vacía si no hay coincidencias.
        """
        ...