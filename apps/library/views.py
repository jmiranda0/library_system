"""
Vistas del sistema de gestión bibliotecaria.

Módulos:
  - CustomLoginView     → Login único con redirección por rol
  - CatalogView         → Catálogo de libros con búsqueda (estudiantes)
  - BookDetailView      → Detalle de un libro
  - MyLoansView         → Panel de préstamos del estudiante autenticado
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from .models import Book, Loan


class CustomLoginView(LoginView):
    """Vista de login única para todos los roles del sistema."""

    template_name = 'login.html'
    # Si el usuario ya está autenticado y regresa al login, lo redirigimos
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        """Redirige según el rol del usuario tras un login exitoso."""
        if self.request.user.is_staff:
            return '/panel/'
        return '/catalogo/'


@method_decorator(login_required(login_url='/'), name='dispatch')
class CatalogView(ListView):
    """
    Catálogo de libros disponible para todos los usuarios autenticados.

    Soporta búsqueda por título o autor mediante el parámetro GET ?q=.
    """

    model = Book
    template_name = 'catalog.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        """Filtra libros por búsqueda de texto si se proporciona el parámetro 'q'."""
        queryset = Book.objects.all()
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(author__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


@method_decorator(login_required(login_url='/'), name='dispatch')
class BookDetailView(DetailView):
    """Vista de detalle de un libro con información de disponibilidad."""

    model = Book
    template_name = 'book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Verifica si este estudiante tiene el libro prestado actualmente
        if hasattr(self.request.user, 'student_profile'):
            context['prestamo_activo'] = Loan.objects.filter(
                book=self.object,
                student=self.request.user.student_profile,
                status=Loan.LoanStatus.ACTIVE,
            ).first()
        return context


@method_decorator(login_required(login_url='/'), name='dispatch')
class MyLoansView(ListView):
    """
    Panel personal de préstamos del estudiante autenticado.

    Muestra los préstamos agrupados por estado: activos, vencidos y devueltos.
    Solo accesible para usuarios con perfil de estudiante.
    """

    template_name = 'my_loans.html'
    context_object_name = 'prestamos'

    def dispatch(self, request, *args, **kwargs):
        """Redirige si el usuario no tiene perfil de estudiante."""
        if request.user.is_staff:
            return redirect('/panel/')
        if not hasattr(request.user, 'student_profile'):
            return redirect('/catalogo/')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Retorna todos los préstamos del estudiante autenticado."""
        return (
            Loan.objects.filter(student=self.request.user.student_profile)
            .select_related('book')
            .order_by('-loan_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        todos = self.get_queryset()
        context['prestamos_activos'] = todos.filter(status=Loan.LoanStatus.ACTIVE)
        context['prestamos_vencidos'] = todos.filter(status=Loan.LoanStatus.OVERDUE)
        context['prestamos_devueltos'] = todos.filter(status=Loan.LoanStatus.RETURNED)
        return context
