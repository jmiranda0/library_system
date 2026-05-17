"""
Dashboard personalizado para el panel de administración.
Define las estadísticas visibles según el rol del usuario.
"""
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils.translation import gettext_lazy as _


def get_stats_for_user(request,context):
    """
    Devuelve las estadísticas del dashboard según el rol del usuario.
    Bibliotecarios ven estadísticas operativas.
    Administradores ven además estadísticas del sistema.
    """
    from apps.library.models import Book, Loan, Student

    # Estadísticas base — visibles para todos
    stats = [
        {
            "title": "Libros en Catálogo",
            "metric": Book.objects.count(),
            "icon": "menu_book",
            "color": "indigo",
        },
        {
            "title": "Préstamos Activos",
            "metric": Loan.objects.filter(status="ACTIVE").count(),
            "icon": "bookmark",
            "color": "emerald",
        },
        {
            "title": "Préstamos Vencidos",
            "metric": Loan.objects.filter(status="OVERDUE").count(),
            "icon": "warning",
            "color": "red",
        },
        {
            "title": "En Lista Negra",
            "metric": Student.objects.filter(is_blacklisted=True).count(),
            "icon": "block",
            "color": "orange",
        },
    ]

    # Estadísticas adicionales — solo para administradores
    if request.user.is_superuser:
        stats += [
            {
                "title": "Total Estudiantes",
                "metric": Student.objects.count(),
                "icon": "person",
                "color": "blue",
            },
            {
                "title": "Bibliotecarios",
                "metric": User.objects.filter(groups__name="Bibliotecarios").count(),
                "icon": "badge",
                "color": "purple",
            },
            {
                "title": "Total Usuarios",
                "metric": User.objects.count(),
                "icon": "manage_accounts",
                "color": "slate",
            },
        ]

    context["stats"] = stats
    return context