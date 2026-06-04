from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from datetime import date
import datetime


class Book(models.Model):
    """Modelo que representa un libro en el catálogo de la biblioteca."""

    title = models.CharField(
        max_length=255,
        verbose_name='Título',
        help_text='Título completo del libro.',
    )
    author = models.CharField(
        max_length=255,
        verbose_name='Autor',
        help_text='Nombre del autor o autores del libro.',
    )
    synopsis = models.TextField(
        verbose_name='Sinopsis',
        help_text='Resumen del contenido del libro. Usado por el motor de búsqueda semántica.',
    )
    total_stock = models.PositiveIntegerField(
        default=1,
        verbose_name='Cantidad total',
        help_text='Cantidad total de ejemplares físicos disponibles en la biblioteca.',
    )
    # --- NUEVO CAMPO PARA LA IA ---
    ai_recommendations_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Recomendado por IA',
        help_text='Cantidad de veces que el motor semántico ha recomendado este libro.',
    )
    cover_image = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL de portada',
        help_text='Enlace a la imagen de portada del libro (opcional).',
    )

    @property
    def available_stock(self) -> int:
        """Calcula el stock disponible restando los préstamos activos al stock total."""
        active_loans: int = self.loans.filter(status='ACTIVE').count()
        return self.total_stock - active_loans

    def __str__(self) -> str:
        return f"{self.title} — {self.author}"

    class Meta:
        verbose_name = 'Libro'
        verbose_name_plural = 'Libros'
        ordering = ['title']


def validate_ci(value: str) -> None:
    """
    Valida que el carné de identidad cubano tenga formato correcto.
    
    Reglas:
    - Exactamente 11 dígitos numéricos
    - Dígitos 1-2: año de nacimiento
    - Dígitos 3-4: mes válido (01-12)
    - Dígitos 5-6: día válido y coherente con el mes
    - La fecha resultante no puede ser futura
    - Años 00-26 corresponden al siglo XXI (2000-2024)
    - Años 27-99 corresponden al siglo XX (1927-1999)
    """
    from django.core.exceptions import ValidationError

    if not value.isdigit() or len(value) != 11:
        raise ValidationError(
            'El Carné de Identidad debe contener exactamente 11 dígitos numéricos.'
        )

    year_digits = int(value[0:2])
    month = int(value[2:4])
    day = int(value[4:6])

    # Determinar el siglo
    current_year_short = date.today().year % 100
    if year_digits <= current_year_short:
        year = 2000 + year_digits
    else:
        year = 1900 + year_digits

    # Verificar que la fecha es real y válida
    try:
        birth_date = datetime.date(year, month, day)
    except ValueError:
        raise ValidationError(
            f'El Carné de Identidad no contiene una fecha de nacimiento válida. '
            f'Verifique que el mes ({month:02d}) y el día ({day:02d}) sean correctos.'
        )

    # La fecha no puede ser futura
    if birth_date > date.today():
        raise ValidationError(
            'El Carné de Identidad corresponde a una fecha de nacimiento futura, '
            'lo cual no es válido.'
        )


class Student(models.Model):
    """Modelo que representa a un estudiante vinculado a una cuenta de usuario."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='Usuario',
    )
    personal_id = models.CharField(
        max_length=11,
        unique=True,
        validators=[validate_ci],
        verbose_name='Carné de Identidad',
        help_text='Número de identificación personal (11 dígitos).',
    )
    career = models.CharField(
        max_length=150,
        default='Ingeniería Informática',
        editable=False,
        verbose_name='Carrera',
        help_text='Carrera universitaria del estudiante.',
    )
    academic_year = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(6),
        ],
        verbose_name='Año académico',
        help_text='Año que cursa actualmente (1 a 6).',
    )
    is_blacklisted = models.BooleanField(
        default=False,
        verbose_name='En lista negra',
        help_text='Indica si el estudiante tiene restricciones para solicitar préstamos.',
    )

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} ({self.personal_id})"

    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['user__last_name', 'user__first_name']


class AuditLog(models.Model):
    """Registro de auditoría para rastrear acciones del sistema."""

    user_actor = models.CharField(
        max_length=150,
        verbose_name='Usuario actor',
        help_text='Nombre o identificador del usuario que realizó la acción.',
    )
    action = models.CharField(
        max_length=255,
        verbose_name='Acción realizada',
    )
    ip_address = models.GenericIPAddressField(
        blank=True,   # Corregido: las acciones internas del sistema no tienen IP de usuario
        null=True,
        verbose_name='Dirección IP',
        help_text='IP desde la cual se realizó la acción. Vacío para acciones automáticas del sistema.',
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y hora',
    )

    def __str__(self) -> str:
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user_actor}: {self.action}"

    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-timestamp']


class Librarian(User):
    """
    Modelo Proxy para gestionar Bibliotecarios de forma independiente en el Admin.
    No crea una tabla nueva — solo proporciona una interfaz diferente sobre User.
    """

    class Meta:
        proxy = True
        verbose_name = 'Bibliotecario'
        verbose_name_plural = 'Bibliotecarios'


class Administrator(User):
    """
    Modelo Proxy para gestionar Supervisoress de forma independiente en el Admin.
    No crea una tabla nueva — solo proporciona una interfaz diferente sobre User.
    """
    class Meta:
        proxy = True
        verbose_name = 'Supervisor'
        verbose_name_plural = 'Supervisores'


class Teacher(models.Model):
    """Modelo que representa a un profesor vinculado a una cuenta de usuario."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name='Usuario',
    )
    personal_id = models.CharField(
        max_length=11,
        unique=True,
        validators=[validate_ci],
        verbose_name='Carné de Identidad',
        help_text='Número de identificación personal (11 dígitos).',
    )
    department = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Departamento',
        help_text='Departamento al que pertenece el profesor (opcional).',
    )
    is_blacklisted = models.BooleanField(
        default=False,
        verbose_name='En lista negra',
        help_text='Indica si el profesor tiene restricciones para solicitar préstamos.',
    )

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} ({self.personal_id})"

    class Meta:
        verbose_name = 'Profesor'
        verbose_name_plural = 'Profesores'
        ordering = ['user__last_name', 'user__first_name']


class Loan(models.Model):
    """Modelo que representa un préstamo de libro a un estudiante o profesor."""

    class LoanStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Activo'
        RETURNED = 'RETURNED', 'Devuelto'
        OVERDUE = 'OVERDUE', 'Vencido'

    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name='loans',
        verbose_name='Libro',
    )
    
    # MODIFICADO: Ahora el estudiante puede ser nulo (porque podría ser un profesor)
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name='loans',
        verbose_name='Estudiante',
        null=True,  # <--- IMPORTANTE
        blank=True, # <--- IMPORTANTE
    )
    
    # NUEVO: Agregamos la relación con el Profesor
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name='loans',
        verbose_name='Profesor',
        null=True,  # <--- IMPORTANTE
        blank=True, # <--- IMPORTANTE
    )
    
    loan_date = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de préstamo',
    )
    expected_return_date = models.DateField(
        verbose_name='Fecha esperada de devolución',
        help_text='Fecha límite para la devolución del libro.',
    )
    actual_return_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha real de devolución',
        help_text='Se completa cuando el usuario devuelve el libro.',
    )
    status = models.CharField(
        max_length=10,
        choices=LoanStatus.choices,
        default=LoanStatus.ACTIVE,
        verbose_name='Estado',
    )

    def clean(self) -> None:
        """
        Validaciones de reglas de negocio antes de guardar el préstamo.
        """
        super().clean()
        errors: dict[str, str] = {}

        # 1. REGLA NUEVA: Debe haber un estudiante O un profesor, no ambos, ni ninguno.
        if not self.student_id and not self.teacher_id:
            raise ValidationError('El préstamo debe estar asignado a un Estudiante o a un Profesor.')
        
        if self.student_id and self.teacher_id:
            raise ValidationError('El préstamo no puede estar asignado a un Estudiante y a un Profesor simultáneamente.')

        # 2. Validar Stock
        if not self.pk and self.book_id:
            if self.book.available_stock <= 0:
                errors['book'] = 'No hay stock disponible para este libro.'

        # 3. Validar Lista Negra (Para Estudiantes y Profesores)
        if self.student_id and self.student.is_blacklisted:
            errors['student'] = 'El estudiante se encuentra en lista negra y no puede solicitar préstamos.'
            
        if self.teacher_id and self.teacher.is_blacklisted:
            errors['teacher'] = 'El profesor se encuentra en lista negra y no puede solicitar préstamos.'

        # 4. Validar Fechas
        if not self.pk and self.expected_return_date:
            reference_date: date = self.loan_date if self.loan_date else date.today()
            if self.expected_return_date <= reference_date:
                errors['expected_return_date'] = (
                    'La fecha de devolución esperada debe ser posterior a la fecha del préstamo.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        """Calcula el estado automáticamente y valida reglas antes de guardar."""
        update_fields = kwargs.get('update_fields')
        if not update_fields:
            if self.actual_return_date:
                self.status = self.LoanStatus.RETURNED
            elif self.expected_return_date and self.expected_return_date < date.today():
                self.status = self.LoanStatus.OVERDUE
            else:
                self.status = self.LoanStatus.ACTIVE
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        # Mostramos el nombre de quien lo pidió (sea alumno o profe)
        borrower = self.student if self.student_id else self.teacher
        return f"{self.book.title} → {borrower} ({self.get_status_display()})"

    class Meta:
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'
        ordering = ['-loan_date']


