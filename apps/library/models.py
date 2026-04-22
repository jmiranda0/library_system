from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


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
        help_text='Resumen del contenido del libro. Será usado por el motor de búsqueda semántica.',
    )
    total_stock = models.PositiveIntegerField(
        default=1,
        verbose_name='Stock total',
        help_text='Cantidad total de ejemplares físicos disponibles en la biblioteca.',
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
        validators=[
            RegexValidator(
                regex=r'^\d{11}$',
                message='El Carné de Identidad debe contener exactamente 11 dígitos numéricos.',
            ),
        ],
        verbose_name='Carné de Identidad',
        help_text='Número de identificación personal (11 dígitos).',
    )
    career = models.CharField(
        max_length=150,
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


class Loan(models.Model):
    """Modelo que representa un préstamo de libro a un estudiante."""

    class LoanStatus(models.TextChoices):
        """Opciones de estado para un préstamo."""
        ACTIVE = 'ACTIVE', 'Activo'
        RETURNED = 'RETURNED', 'Devuelto'
        OVERDUE = 'OVERDUE', 'Vencido'

    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name='loans',
        verbose_name='Libro',
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name='loans',
        verbose_name='Estudiante',
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
        help_text='Se completa cuando el estudiante devuelve el libro.',
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

        Reglas:
        1. No se puede prestar un libro sin stock disponible.
        2. No se puede prestar a un estudiante en lista negra.
        3. La fecha de devolución esperada debe ser posterior a la fecha del préstamo.
        """
        super().clean()
        errors: dict[str, str] = {}

        # Regla 1: Verificar stock disponible (solo al crear, no al editar)
        if not self.pk and self.book_id:
            if self.book.available_stock <= 0:
                errors['book'] = 'No hay stock disponible para este libro.'

        # Regla 2: Verificar que el estudiante no esté en lista negra
        if self.student_id and self.student.is_blacklisted:
            errors['student'] = 'El estudiante se encuentra en lista negra y no puede solicitar préstamos.'

        # Regla 3: La fecha de devolución debe ser futura respecto al préstamo
        if self.expected_return_date:
            reference_date: date = self.loan_date if self.loan_date else date.today()
            if self.expected_return_date <= reference_date:
                errors['expected_return_date'] = (
                    'La fecha de devolución esperada debe ser posterior a la fecha del préstamo.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        """Fuerza la ejecución de clean() antes de cada guardado."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.book.title} → {self.student} ({self.get_status_display()})"

    class Meta:
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'
        ordering = ['-loan_date']


class AuditLog(models.Model):
    """Modelo de registro de auditoría para rastrear acciones del sistema."""

    user_actor = models.CharField(
        max_length=150,
        verbose_name='Usuario actor',
        help_text='Nombre o identificador del usuario que realizó la acción.',
    )
    action = models.CharField(
        max_length=255,
        verbose_name='Acción realizada',
        help_text='Descripción de la acción ejecutada en el sistema.',
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='Dirección IP',
        help_text='Dirección IP desde la cual se realizó la acción.',
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
