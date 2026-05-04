from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AuditLog, Book, Loan, Student


@admin.register(Book)
class BookAdmin(ModelAdmin):
    """Configuración del panel de administración para el modelo Book."""

    list_display = ('title', 'author', 'total_stock', 'available_stock')
    search_fields = ('title', 'author')
    list_filter = ('author',)

    @admin.display(description='Stock disponible')
    def available_stock(self, obj: Book) -> int:
        """Muestra el stock disponible como columna de solo lectura."""
        return obj.available_stock


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    """Configuración del panel de administración para el modelo Student."""

    list_display = ('get_full_name', 'personal_id', 'career', 'academic_year', 'is_blacklisted')
    search_fields = ('user__first_name', 'user__last_name', 'personal_id')
    list_filter = ('career', 'academic_year', 'is_blacklisted')

    @admin.display(description='Nombre completo', ordering='user__last_name')
    def get_full_name(self, obj: Student) -> str:
        """Muestra el nombre completo del usuario vinculado al estudiante."""
        return obj.user.get_full_name()


@admin.register(Loan)
class LoanAdmin(ModelAdmin):
    """Configuración del panel de administración para el modelo Loan."""

    list_display = ('book', 'student', 'loan_date', 'expected_return_date', 'status')
    search_fields = ('book__title', 'student__user__last_name', 'student__personal_id')
    list_filter = ('status', 'loan_date')
    readonly_fields = ('loan_date',)
    date_hierarchy = 'loan_date'


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    """Configuración del panel de administración para el modelo AuditLog (solo lectura)."""

    list_display = ('timestamp', 'user_actor', 'action', 'ip_address')
    search_fields = ('user_actor', 'action')
    list_filter = ('user_actor', 'timestamp')
    readonly_fields = ('user_actor', 'action', 'ip_address', 'timestamp')

    def has_add_permission(self, request) -> bool:
        """Impide crear registros de auditoría desde el admin."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Impide editar registros de auditoría desde el admin."""
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Impide eliminar registros de auditoría desde el admin."""
        return False
