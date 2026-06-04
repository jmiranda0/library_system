"""
Vistas del portal de estudiantes.

Módulos:
  - CustomLoginView  → Login único con redirección por rol
  - CatalogView      → Catálogo de libros con búsqueda
  - BookDetailView   → Detalle de un libro
  - MyLoansView      → Panel de préstamos del estudiante autenticado
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.views.generic import DetailView, ListView, TemplateView

from .models import Book, Loan
from .services import search_books


class CustomLoginView(LoginView):
    """Vista de login única para todos los roles del sistema."""

    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        """Redirige según el rol del usuario tras un login exitoso."""
        if self.request.user.is_staff:
            return '/panel/'
        return '/catalogo/'


@method_decorator(login_required(login_url='/'), name='dispatch')
class CatalogView(TemplateView):
    template_name = 'catalog.html'
    LIBROS_POR_PAGINA = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        page_number = self.request.GET.get('page', 1)

        results = search_books(query)

        paginator = Paginator(results, self.LIBROS_POR_PAGINA)
        page_obj = paginator.get_page(page_number)

        context['query'] = query
        context['results'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['is_paginated'] = paginator.num_pages > 1
        context['total'] = len(results)
        return context
    
@method_decorator(login_required(login_url='/'), name='dispatch')
class BookDetailView(DetailView):
    """Vista de detalle de un libro con información de disponibilidad."""

    model = Book
    template_name = 'book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
    Panel personal de préstamos del estudiante o profesor autenticado.
    """
    template_name = 'my_loans.html'
    context_object_name = 'prestamos'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return redirect('/panel/')
        if not hasattr(request.user, 'student_profile') and not hasattr(request.user, 'teacher_profile'):
            return redirect('/catalogo/')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        
        # Si es Estudiante
        if hasattr(user, 'student_profile'):
            return Loan.objects.filter(student=user.student_profile).select_related('book').order_by('-loan_date')
            
        # Si es Profesor
        elif hasattr(user, 'teacher_profile'):
            return Loan.objects.filter(teacher=user.teacher_profile).select_related('book').order_by('-loan_date')
            
        return Loan.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        todos = self.get_queryset()
        context['prestamos_activos'] = todos.filter(status=Loan.LoanStatus.ACTIVE)
        context['prestamos_vencidos'] = todos.filter(status=Loan.LoanStatus.OVERDUE)
        context['prestamos_devueltos'] = todos.filter(status=Loan.LoanStatus.RETURNED)
        return context