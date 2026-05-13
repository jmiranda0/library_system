"""
Configuración de URLs del proyecto.

Rutas disponibles:
  /                → Login único (redirige según rol)
  /logout/         → Cierre de sesión
  /panel/          → Panel de administración (Bibliotecarios y Administradores)
  /catalogo/       → Catálogo de libros (Estudiantes autenticados)
  /catalogo/<pk>/  → Detalle de un libro
  /mis-prestamos/  → Panel de préstamos del estudiante
  /404/            → Previsualización de la página 404 (solo desarrollo)
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView, PasswordChangeView
from django.urls import path
from django.views.defaults import page_not_found

from apps.library.views import (
    BookDetailView,
    CatalogView,
    CustomLoginView,
    MyLoansView,
)

# Conecta la plantilla 404.html personalizada con los errores 404 del sistema.
# Django la usará automáticamente en producción (DEBUG=False).
handler404 = 'django.views.defaults.page_not_found'

urlpatterns = [
    # ── Autenticación ──────────────────────────────────────────────────────────
    path('', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    # ── Panel de administración ────────────────────────────────────────────────
    path('panel/', admin.site.urls),

    # ── Portal de Estudiantes ──────────────────────────────────────────────────
    path('catalogo/', CatalogView.as_view(), name='catalogo'),
    path('catalogo/<int:pk>/', BookDetailView.as_view(), name='libro-detalle'),
    path('mis-prestamos/', MyLoansView.as_view(), name='mis-prestamos'),
    path('perfil/cambiar-password/', PasswordChangeView.as_view(
        template_name='password_change.html',
        success_url='/catalogo/'
    ), name='cambiar-password'),

    # ── Utilidades de desarrollo ───────────────────────────────────────────────
    path('404/', lambda request: page_not_found(request, exception=None), name='error-404-preview'),
]
