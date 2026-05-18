import logging
from typing import List

from django.conf import settings

from .base import BookMatch
from .lexical import LexicalSearchStrategy
from .semantic import SemanticSearchStrategy

logger = logging.getLogger(__name__)

_lexical = LexicalSearchStrategy()


def perform_search(query: str) -> List[BookMatch]:
    """
    Punto de entrada único para todas las búsquedas del sistema.
    Devuelve lista de BookMatch con puntuación de relevancia.
    """
    ai_model = getattr(settings, 'SEARCH_AI_MODEL', None)

    #print(f"DEBUG — SEARCH_AI_MODEL: '{ai_model}'")
    #print(f"DEBUG — Query: '{query}'")

    if ai_model:
        try:
            semantic = SemanticSearchStrategy(model=ai_model)
            return semantic.search(query)
        except Exception as exc:
            #print(f"DEBUG — Excepción IA: {exc}")
            _log_ai_failure(query=query, error=exc)

    #print("DEBUG — Usando fallback léxico")
    return _lexical.search(query)


def _log_ai_failure(query: str, error: Exception) -> None:
    logger.warning(
        "Búsqueda semántica falló. Activando fallback léxico. "
        "Query: '%s' | Error: %s",
        query, str(error)
    )
    try:
        from apps.library.models import AuditLog
        AuditLog.objects.create(
            user_actor='sistema',
            action=(
                f"Fallo en búsqueda semántica para consulta '{query}'. "
                f"Error: {type(error).__name__}. Fallback léxico activado."
            ),
            ip_address=None,
        )
    except Exception as log_error:
        logger.error("No se pudo escribir en AuditLog: %s", str(log_error))