"""
Comando de evaluación comparativa entre búsqueda exacta y semántica.

Ejecuta un conjunto de consultas predefinidas contra ambos motores,
calcula precisión, exhaustividad y F1-score, y genera un reporte.

Uso:
    python manage.py evaluate_search
    python manage.py evaluate_search --output reporte.txt
"""
import json
from django.core.management.base import BaseCommand
from apps.search.lexical import LexicalSearchStrategy
from apps.search.agent import perform_search
from apps.library.models import Book


# ============================================================
# CONJUNTO DE CONSULTAS DE PRUEBA
# Cada consulta tiene:
#   - query: la consulta del usuario
#   - relevant_titles: títulos de libros que SE ESPERA que aparezcan
#   - tipo: categoría de la consulta
# ============================================================
TEST_QUERIES = [
    {
        "id": "Q01",
        "query": "muerte",
        "tipo": "Término directo",
        "relevant_titles": [
            "Crónica de una muerte anunciada",
            "La ladrona de libros",
            "El Psicoanalista",
            "Crimen y Castigo",
            "El Resplandor",
            "El nombre de la rosa",
        ],
    },
    {
        "id": "Q02",
        "query": "libros sobre el universo y el cosmos",
        "tipo": "Sinónimos",
        "relevant_titles": [
            "Breve historia del tiempo",
            "Cosmos",
            "Fundación",
        ],
    },
    {
        "id": "Q03",
        "query": "algo de aventuras épicas",
        "tipo": "Lenguaje informal",
        "relevant_titles": [
            "El Señor de los Anillos: La Comunidad del Anillo",
            "La Odisea",
            "Harry Potter y la Piedra Filosofal",
            "Fundación",
        ],
    },
    {
        "id": "Q04",
        "query": "psicología y mente humana",
        "tipo": "Conceptual",
        "relevant_titles": [
            "Crimen y Castigo",
            "El Psicoanalista",
            "Metamorfosis",
            "Ensayo sobre la ceguera",
        ],
    },
    {
        "id": "Q05",
        "query": "Clean Code",
        "tipo": "Título exacto",
        "relevant_titles": [
            "Clean Code",
        ],
    },
    {
        "id": "Q06",
        "query": "García Márquez",
        "tipo": "Autor exacto",
        "relevant_titles": [
            "Cien Años de Soledad",
            "Crónica de una muerte anunciada",
        ],
    },
    {
        "id": "Q07",
        "query": "distopía y control social",
        "tipo": "Conceptual",
        "relevant_titles": [
            "1984",
        ],
    },
    {
        "id": "Q08",
        "query": "programación python",
        "tipo": "Término técnico",
        "relevant_titles": [
            "Python Crash Course",
        ],
    },
    {
        "id": "Q09",
        "query": "amor y sociedad",
        "tipo": "Abstracto",
        "relevant_titles": [
            "Orgullo y Prejuicio",
            "Los Miserables",
            "El Principito",
        ],
    },
    {
        "id": "Q10",
        "query": "precio del dólar hoy",
        "tipo": "Irrelevante",
        "relevant_titles": [],
    },
]


def calcular_metricas(recuperados_ids: list, relevantes_ids: set) -> dict:
    """
    Calcula precisión, exhaustividad y F1-score.

    Precisión = relevantes recuperados / total recuperados
    Exhaustividad = relevantes recuperados / total relevantes
    F1 = 2 * (P * R) / (P + R)
    """
    if not relevantes_ids:
        # Consulta irrelevante — si devuelve vacío es correcto
        if not recuperados_ids:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "nota": "vacío correcto"}
        else:
            return {"precision": 0.0, "recall": 1.0, "f1": 0.0, "nota": "debería estar vacío"}

    recuperados_set = set(recuperados_ids)
    verdaderos_positivos = len(recuperados_set & relevantes_ids)

    precision = verdaderos_positivos / len(recuperados_set) if recuperados_set else 0.0
    recall = verdaderos_positivos / len(relevantes_ids)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "nota": "",
    }


class Command(BaseCommand):
    help = 'Evaluación comparativa entre búsqueda exacta y semántica.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Archivo de salida para el reporte (opcional).',
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Exportar resultados en formato JSON.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "\n╔══════════════════════════════════════════════════════╗"
        ))
        self.stdout.write(self.style.SUCCESS(
            "║     EVALUACIÓN COMPARATIVA DE BÚSQUEDA               ║"
        ))
        self.stdout.write(self.style.SUCCESS(
            "║     Búsqueda Exacta vs. Búsqueda Semántica            ║"
        ))
        self.stdout.write(self.style.SUCCESS(
            "╚══════════════════════════════════════════════════════╝\n"
        ))

        # Construir mapa de títulos a IDs
        title_to_id = {
            book.title: book.pk
            for book in Book.objects.all()
        }

        lexical = LexicalSearchStrategy()
        resultados = []

        for test in TEST_QUERIES:
            query = test["query"]
            relevant_ids = {
                title_to_id[t]
                for t in test["relevant_titles"]
                if t in title_to_id
            }

            self.stdout.write(f"\n{'─' * 56}")
            self.stdout.write(
                f"[{test['id']}] {query} ({test['tipo']})"
            )
            self.stdout.write(
                f"Relevantes esperados: {len(relevant_ids)} libro(s)"
            )

            # ── Búsqueda exacta ──
            lexical_matches = lexical.search(query)
            lexical_ids = [m.book_id for m in lexical_matches]
            lexical_metricas = calcular_metricas(lexical_ids, relevant_ids)

            self.stdout.write(
                f"\n  EXACTA   → {len(lexical_ids)} resultado(s) | "
                f"P={lexical_metricas['precision']:.2f} "
                f"R={lexical_metricas['recall']:.2f} "
                f"F1={lexical_metricas['f1']:.2f}"
            )

            # ── Búsqueda semántica ──
            try:
                semantic_matches = perform_search(query)
                semantic_ids = [m.book_id for m in semantic_matches]
                semantic_metricas = calcular_metricas(semantic_ids, relevant_ids)

                self.stdout.write(
                    f"  SEMÁNTICA → {len(semantic_ids)} resultado(s) | "
                    f"P={semantic_metricas['precision']:.2f} "
                    f"R={semantic_metricas['recall']:.2f} "
                    f"F1={semantic_metricas['f1']:.2f}"
                )
            except Exception as e:
                semantic_metricas = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "nota": f"error: {e}"}
                semantic_ids = []
                self.stdout.write(
                    self.style.ERROR(f"  SEMÁNTICA → ERROR: {e}")
                )

            # Ganador
            if semantic_metricas['f1'] > lexical_metricas['f1']:
                ganador = "SEMÁNTICA ✓"
            elif lexical_metricas['f1'] > semantic_metricas['f1']:
                ganador = "EXACTA ✓"
            else:
                ganador = "EMPATE"

            self.stdout.write(f"  Ganador: {ganador}")

            resultados.append({
                "id": test["id"],
                "query": query,
                "tipo": test["tipo"],
                "relevantes": len(relevant_ids),
                "exacta": {**lexical_metricas, "resultados": len(lexical_ids)},
                "semantica": {**semantic_metricas, "resultados": len(semantic_ids)},
                "ganador": ganador,
            })

        # ── Resumen global ──
        self.stdout.write(f"\n{'═' * 56}")
        self.stdout.write(self.style.SUCCESS("RESUMEN GLOBAL"))
        self.stdout.write(f"{'═' * 56}")

        avg_p_lex = sum(r["exacta"]["precision"] for r in resultados) / len(resultados)
        avg_r_lex = sum(r["exacta"]["recall"] for r in resultados) / len(resultados)
        avg_f1_lex = sum(r["exacta"]["f1"] for r in resultados) / len(resultados)

        avg_p_sem = sum(r["semantica"]["precision"] for r in resultados) / len(resultados)
        avg_r_sem = sum(r["semantica"]["recall"] for r in resultados) / len(resultados)
        avg_f1_sem = sum(r["semantica"]["f1"] for r in resultados) / len(resultados)

        self.stdout.write(
            f"\n  EXACTA    → P={avg_p_lex:.3f} | R={avg_r_lex:.3f} | F1={avg_f1_lex:.3f}"
        )
        self.stdout.write(
            f"  SEMÁNTICA → P={avg_p_sem:.3f} | R={avg_r_sem:.3f} | F1={avg_f1_sem:.3f}"
        )

        gana_semantica = sum(1 for r in resultados if r["ganador"] == "SEMÁNTICA ✓")
        gana_exacta = sum(1 for r in resultados if r["ganador"] == "EXACTA ✓")
        empates = sum(1 for r in resultados if r["ganador"] == "EMPATE")

        self.stdout.write(f"\n  Consultas ganadas por SEMÁNTICA: {gana_semantica}")
        self.stdout.write(f"  Consultas ganadas por EXACTA:    {gana_exacta}")
        self.stdout.write(f"  Empates:                         {empates}")

        # Exportar si se pidió
        if options.get('output'):
            self._exportar_txt(resultados, options['output'], avg_f1_lex, avg_f1_sem)

        if options.get('json'):
            print(json.dumps(resultados, indent=2, ensure_ascii=False))

    def _exportar_txt(self, resultados, filename, avg_f1_lex, avg_f1_sem):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("EVALUACIÓN COMPARATIVA — SISTEMA DE GESTIÓN BIBLIOTECARIA\n")
            f.write("Búsqueda Exacta vs. Búsqueda Semántica\n")
            f.write("=" * 60 + "\n\n")
            for r in resultados:
                f.write(f"[{r['id']}] {r['query']} ({r['tipo']})\n")
                f.write(f"  Exacta:    P={r['exacta']['precision']:.3f} R={r['exacta']['recall']:.3f} F1={r['exacta']['f1']:.3f}\n")
                f.write(f"  Semántica: P={r['semantica']['precision']:.3f} R={r['semantica']['recall']:.3f} F1={r['semantica']['f1']:.3f}\n")
                f.write(f"  Ganador: {r['ganador']}\n\n")
            f.write("=" * 60 + "\n")
            f.write(f"F1 promedio Exacta:    {avg_f1_lex:.3f}\n")
            f.write(f"F1 promedio Semántica: {avg_f1_sem:.3f}\n")
        self.stdout.write(self.style.SUCCESS(f"\nReporte exportado: {filename}"))