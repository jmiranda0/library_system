"""
Capa de servicios de la app library.

Este módulo centraliza toda la lógica de negocio de alto nivel (casos de uso).
Las vistas del admin, el frontend, y cualquier otro consumidor deben llamar
a estas funciones en lugar de manipular los modelos directamente.

Ventajas:
- Evita duplicar lógica entre el admin y el frontend.
- Garantiza que el AuditLog siempre se escriba junto a cada acción importante.
- Facilita el testing, ya que la lógica está separada de la interfaz.
"""

from datetime import date

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import AuditLog, Book, Loan, Student


def _write_audit_log(actor_user: str, action: str, ip_address: str) -> None:
    """
    Función interna auxiliar que escribe un registro en el AuditLog.

    No se llama directamente desde fuera — la usan create_loan,
    return_loan y el comando mark_overdue_loans.

    Args:
        actor_user: Nombre de usuario o identificador de quien ejecuta la acción.
        action:     Descripción textual de la acción realizada.
        ip_address: Dirección IP desde donde se realizó la acción.
    """
    AuditLog.objects.create(
        user_actor=actor_user,
        action=action,
        ip_address=ip_address,
    )


def search_books(query: str):
    """
    Ejecuta búsqueda y devuelve libros con su porcentaje de relevancia.

    Returns:
        Lista de tuplas (libro, porcentaje) ordenadas por relevancia.
        Si la consulta está vacía, devuelve todos los libros sin porcentaje.
    """
    from apps.library.models import Book

    if not query.strip():
        return [(book, None) for book in Book.objects.all()]

    from apps.search.agent import perform_search
    matches = perform_search(query)

    if not matches:
        return []

    # Construimos el resultado preservando orden y porcentaje
    book_ids = [m.book_id for m in matches]
    score_map = {m.book_id: m.score * 10 for m in matches}  # score 1-10 → 10%-100%

    from django.db.models import Case, When
    preserved_order = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(book_ids)]
    )
    books = Book.objects.filter(id__in=book_ids).order_by(preserved_order)

    return [(book, score_map[book.pk]) for book in books]
