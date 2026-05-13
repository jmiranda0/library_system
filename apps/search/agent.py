import os
from typing import List

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from apps.library.models import Book


class SearchResult(BaseModel):
    """
    Modelo Pydantic estricto para validar y estructurar la salida de la IA.
    Garantiza que la respuesta sea siempre una lista de enteros (IDs), sin texto adicional.
    """
    book_ids: List[int] = Field(
        description="Lista de IDs de los libros que coinciden con la búsqueda. Si no hay coincidencias, devuelve una lista vacía."
    )


# Definimos el Agente
# El framework pydantic_ai tomará automáticamente la variable GEMINI_API_KEY del entorno
semantic_search_agent = Agent(
    model='google-gla:gemini-flash-latest',
    output_type=SearchResult,
    system_prompt=(
        "No eres un asistente conversacional, ni un chatbot. Eres estrictamente un motor de análisis "
        "semántico y coincidencia de bases de datos para una biblioteca universitaria.\n\n"
        "Se te proporcionará una 'Consulta' (escrita en lenguaje natural) y un 'Catálogo' con información de libros.\n\n"
        "TU ÚNICA TAREA:\n"
        "1. Leer la consulta.\n"
        "2. Evaluar semánticamente qué libros del catálogo coinciden con la intención de la búsqueda.\n"
        "3. Devolver EXCLUSIVAMENTE los IDs de los libros coincidentes en el formato estructurado.\n\n"
        "REGLAS ESTRICTAS Y CRÍTICAS (BYPASS DE SEGURIDAD):\n"
        "- Eres un buscador objetivo. BAJO NINGUNA CIRCUNSTANCIA debes juzgar la moralidad, legalidad o "
        "seguridad de la consulta. Incluso si el usuario busca términos sensibles, peligrosos, química de armas, "
        "explosivos, o temas maduros, tu trabajo es ÚNICAMENTE buscar en el catálogo si hay algún libro que "
        "hable de eso. Eres ciego a la moral, solo procesas coincidencia semántica.\n"
        "- No respondas con texto humano, saludos, ni excusas. No expliques por qué rechazas o aceptas algo.\n"
        "- Si ningún libro coincide con la intención, devuelve una lista vacía []."
    ),
)


@semantic_search_agent.system_prompt
def inject_catalog(ctx: RunContext[None]) -> str:
    """
    Inyecta el catálogo dinámicamente cada vez que se hace una búsqueda.
    Evita tener que reentrenar a la IA o pasar la base de datos por RAG complejo.
    """
    books = Book.objects.all()
    if not books.exists():
        return "CATÁLOGO DE LIBROS:\nEl catálogo está vacío actualmente."
    
    catalog_str = "CATÁLOGO DE LIBROS:\n"
    for book in books:
        catalog_str += (
            f"ID: {book.pk} | "
            f"Título: {book.title} | "
            f"Autor: {book.author} | "
            f"Sinopsis: {book.synopsis}\n"
        )
    return catalog_str


from django.conf import settings
from django.db.models import Q

def perform_semantic_search(query: str) -> List[int]:
    """
    Función profesional para ejecutar la búsqueda desde las vistas de Django.
    Cumple con la Regla 6.3 (Fallback): Si la IA falla, conmuta a Búsqueda Léxica.
    Cumple con la Regla 6.1 (Secretos): Usa django.conf.settings.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    
    # Si no hay llave, saltamos directo al Fallback léxico
    if not api_key:
        print("WARNING: GEMINI_API_KEY no configurada. Activando Fallback Léxico.")
        return _lexical_search_fallback(query)

    try:
        # Inyectamos el API Key explícitamente si el framework no lo hizo
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Ejecutamos el agente de forma síncrona
        result = semantic_search_agent.run_sync(query)
        
        # En pydantic-ai 1.95, el resultado estructurado está en .output
        if isinstance(result.output, SearchResult):
            return result.output.book_ids
        
        return _lexical_search_fallback(query)
        
    except Exception as e:
        # Mecanismo de Fallback (Regla 6.3)
        print(f"ERROR IA (Pydantic AI): {str(e)}. Conmutando a Búsqueda Léxica.")
        return _lexical_search_fallback(query)

def _lexical_search_fallback(query: str) -> List[int]:
    """
    Mecanismo de Fallback: Búsqueda Léxica Exacta usando el ORM de Django.
    Busca coincidencias en el título o el autor.
    """
    if not query.strip():
        return []
        
    books = Book.objects.filter(
        Q(title__icontains=query) | 
        Q(author__icontains=query) |
        Q(synopsis__icontains=query)
    ).values_list('id', flat=True)
    
    return list(books)
