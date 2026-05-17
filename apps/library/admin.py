from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.admin import ModelAdmin
from .models import AuditLog, Book, Loan, Student, Librarian
from .forms import StudentAdminForm, LibrarianAdminForm
from .services import _write_audit_log, create_loan, return_loan


from apps.library.models import Book, Loan, Student
from django.contrib.auth.models import User
from django.db.models.functions import TruncMonth
from django.db.models import Count
import json

# Unregister default admin to replace with Unfold
admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Extiende el UserAdmin de Django con la estética de Unfold."""
    
    def has_add_permission(self, request) -> bool:
        """Deshabilita la creación directa de usuarios para forzar el uso de Estudiantes/Bibliotecarios."""
        return False

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """Extiende el GroupAdmin de Django con la estética de Unfold."""
    pass
from django.contrib import messages
from django.core.exceptions import ValidationError


class AuditMixin:
    """Mixin para registrar automáticamente acciones en el AuditLog desde el Admin."""

    def save_model(self, request, obj, form, change):
        is_new = not change
        action_type = "Creó" if is_new else "Editó"
        model_name = obj._meta.verbose_name
        
        # Guardar el objeto primero
        super().save_model(request, obj, form, change)
        
        # Registrar en el log
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        _write_audit_log(
            actor_user=request.user.username,
            action=f"{action_type} el {model_name}: {str(obj)}",
            ip_address=ip
        )

    def delete_model(self, request, obj):
        model_name = obj._meta.verbose_name
        obj_str = str(obj)
        
        # Eliminar el objeto
        super().delete_model(request, obj)
        
        # Registrar en el log
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        _write_audit_log(
            actor_user=request.user.username,
            action=f"Eliminó el {model_name}: {obj_str}",
            ip_address=ip
        )


@admin.register(Book)
class BookAdmin(AuditMixin, ModelAdmin):
    """Configuración del panel de administración para el modelo Book."""

    list_display = ('title', 'author', 'total_stock', 'available_stock')
    search_fields = ('title', 'author')
    list_filter = ('author',)

    @admin.display(description='Stock disponible')
    def available_stock(self, obj: Book) -> int:
        """Muestra el stock disponible como columna de solo lectura."""
        return obj.available_stock


@admin.register(Student)
class StudentAdmin(AuditMixin, ModelAdmin):
    """Configuración del panel de administración para el modelo Student."""
    
    form = StudentAdminForm
    list_display = ('get_full_name', 'personal_id', 'career', 'academic_year', 'is_blacklisted')
    search_fields = ('user__first_name', 'user__last_name', 'personal_id', 'user__username')
    list_filter = ('career', 'academic_year', 'is_blacklisted')

    def get_fieldsets(self, request, obj=None):
        if not obj:
            # Creando: ocultar Datos de Autenticación, se generarán solos
            return (
                ('Información Personal', {
                    'fields': ('first_name', 'last_name', 'personal_id')
                }),
                ('Información Académica', {
                    'fields': ('career', 'academic_year') # is_blacklisted no al crear
                }),
            )
        # Editando: mostrar datos autogenerados
        return (
            ('Información Personal', {
                'fields': ('first_name', 'last_name', 'personal_id')
            }),
            ('Información Académica', {
                'fields': ('career', 'academic_year', 'is_blacklisted')
            }),
            ('Credenciales de Acceso (Autogeneradas)', {
                'fields': ('username_display', 'email_display', 'default_password_info'),
            }),
        )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('username_display', 'email_display', 'default_password_info')
        return ()

    @admin.display(description='Usuario')
    def username_display(self, obj):
        return obj.user.username

    @admin.display(description='Correo')
    def email_display(self, obj):
        return obj.user.email

    @admin.display(description='Contraseña Inicial')
    def default_password_info(self, obj):
        return f"El Carné de Identidad ({obj.personal_id}). El estudiante puede cambiarla en su perfil."

    @admin.display(description='Nombre completo', ordering='user__last_name')
    def get_full_name(self, obj: Student) -> str:
        """Muestra el nombre completo del usuario vinculado al estudiante."""
        return obj.user.get_full_name()


@admin.register(Loan)
class LoanAdmin(AuditMixin, ModelAdmin):
    """Configuración del panel de administración para el modelo Loan."""

    list_display = ('book', 'student', 'loan_date', 'expected_return_date', 'status')
    search_fields = ('book__title', 'student__user__last_name', 'student__personal_id')
    list_filter = ('status', 'loan_date')
    date_hierarchy = 'loan_date'

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            # Al crear, mostramos la fecha sugerida como solo lectura
            return ('status', 'get_loan_date_display')
        # Al editar, la fecha original es inmutable
        return ('status', 'loan_date')

    def get_fields(self, request, obj=None):
        if not obj:
            # Campos visibles al crear: ocultamos fecha_real_devolucion
            return ('book', 'student', 'get_loan_date_display', 'expected_return_date', 'status')
        # Al editar: todo es visible
        return ('book', 'student', 'loan_date', 'expected_return_date', 'actual_return_date', 'status')

    @admin.display(description='Fecha de préstamo')
    def get_loan_date_display(self, obj):
        from datetime import date
        return obj.loan_date if obj and obj.loan_date else date.today()

    def save_model(self, request, obj, form, change):
        """
        El modelo Loan ahora gestiona su estado automáticamente.
        Aquí solo manejamos la auditoría y capturamos errores visualmente.
        """
        from django.contrib import messages
        from django.core.exceptions import ValidationError
        
        try:
            # Al guardar, el modelo ejecutará su nueva lógica de estado automática
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            # Si hay error, lo mostramos y evitamos que Django diga "Éxito"
            msg = e.message if hasattr(e, 'message') else str(e)
            messages.error(request, f"Error de Regla de Negocio: {msg}")
            # Al no re-lanzar la excepción aquí, Django mostrará el mensaje verde.
            # Para evitar el mensaje verde, lanzamos una excepción que el Admin entienda
            # pero que no rompa la página de edición.
            # En Django Admin, esto se suele manejar en el Form, pero aquí lo haremos así:
            raise ValidationError(e)
        except Exception as e:
            messages.error(request, f"Error inesperado: {str(e)}")
            raise e


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    """Configuración del panel de administración para el modelo AuditLog (solo lectura)."""

    list_display = ('timestamp', 'user_actor', 'action', 'ip_address')
    search_fields = ('user_actor', 'action')
    list_filter = ('user_actor', 'timestamp')
    readonly_fields = ('user_actor', 'action', 'ip_address', 'timestamp')

    def get_queryset(self, request):
        """
        Filtra los registros para que los bibliotecarios solo vean sus propias acciones.
        Los superusuarios (Admin) mantienen acceso total.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # El bibliotecario solo ve lo que él mismo registró
        return qs.filter(user_actor=request.user.username)

    def has_add_permission(self, request) -> bool:
        """Impide crear registros de auditoría desde el admin."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Impide editar registros de auditoría desde el admin."""
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Impide eliminar registros de auditoría desde el admin."""
        return False


@admin.register(Librarian)
class LibrarianAdmin(AuditMixin, ModelAdmin):
    """
    Configuración del panel de administración exclusivo para Bibliotecarios.
    Usa un modelo Proxy para separarlos visualmente de los usuarios normales.
    """
    form = LibrarianAdminForm
    list_display = ('username', 'get_full_name_display', 'email', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('is_active',)

    fieldsets = (
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Datos de Autenticación', {
            'fields': ('username', 'password'),
            'description': 'Si se dejan en blanco, el sistema los generará automáticamente.'
        }),
        ('Estado de la Cuenta', {
            'fields': ('is_active',)
        }),
    )

    def get_queryset(self, request):
        """Filtra para mostrar únicamente a los usuarios que pertenecen al grupo 'Bibliotecarios'."""
        qs = super().get_queryset(request)
        return qs.filter(groups__name='Bibliotecarios')

    def save_model(self, request, obj, form, change):
        """Asegura que el Bibliotecario tenga is_staff=True y pertenezca a su grupo."""
        obj.is_staff = True
        super().save_model(request, obj, form, change)
        from django.contrib.auth.models import Group
        grupo, _ = Group.objects.get_or_create(name='Bibliotecarios')
        obj.groups.add(grupo)

    @admin.display(description='Nombre completo')
    def get_full_name_display(self, obj: Librarian) -> str:
        return obj.get_full_name()


def dashboard_callback(request, context):
    
    print("DEBUG — dashboard_callback ejecutado")
    print(f"DEBUG — context keys: {list(context.keys())}")
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
                "metric": User.objects.filter(
                    groups__name="Bibliotecarios"
                ).count(),
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

    prestamos_por_mes = (
    Loan.objects.annotate(mes=TruncMonth('loan_date'))
    .values('mes')
    .annotate(total=Count('id'))
    .order_by('mes')
    )

    labels = []
    data = []
    for entry in prestamos_por_mes:
        labels.append(entry['mes'].strftime('%b %Y'))
        data.append(entry['total'])

    context["chart_labels"] = json.dumps(labels, ensure_ascii=False)
    context["chart_data"] = json.dumps(data)

    return context
