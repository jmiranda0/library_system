from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AuditLog, Book, Loan, Student, Librarian
from .forms import StudentAdminForm, LibrarianAdminForm


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


@admin.register(Librarian)
class LibrarianAdmin(ModelAdmin):
    """
    Configuración del panel de administración exclusivo para Bibliotecarios.
    Usa un modelo Proxy para separarlos visualmente de los usuarios normales.
    """
    form = LibrarianAdminForm
    list_display = ('username', 'get_full_name_display', 'email', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('is_active',)

    fieldsets = (
        ('Datos de Autenticación', {
            'fields': ('username', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email')
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
