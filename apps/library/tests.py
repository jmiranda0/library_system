"""
Tests unitarios del sistema de gestión bibliotecaria.
Cubre las reglas de negocio críticas del dominio:
  - Cálculo de disponibilidad (Stock)
  - Creación de préstamos (Alumnos y Profesores)
  - Manejo de estados automáticos
  - Restricciones de Lista Negra
"""
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.library.models import Book, Loan, Student, Teacher

class BookStockTestCase(TestCase):
    """Tests del cálculo de stock disponible."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Libro de Prueba",
            author="Autor de Prueba",
            synopsis="Sinopsis de prueba para el motor semántico.",
            total_stock=3,
        )
        self.user1 = User.objects.create_user(username="estudiante1", password="123")
        self.student1 = Student.objects.create(
            user=self.user1,
            personal_id="99010112345", # CI Válido
            career="Informática",
            academic_year=2,
        )

    def test_stock_disponible_sin_prestamos(self):
        """Sin préstamos activos el stock disponible debe ser igual al total."""
        self.assertEqual(self.book.available_stock, 3)

    def test_stock_disponible_con_prestamo_activo(self):
        """Un préstamo activo debe reducir el stock disponible en 1."""
        Loan.objects.create(
            book=self.book,
            student=self.student1,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.assertEqual(self.book.available_stock, 2)

    def test_stock_disponible_con_prestamo_devuelto(self):
        """Un préstamo devuelto no debe afectar el stock disponible."""
        loan = Loan.objects.create(
            book=self.book,
            student=self.student1,
            expected_return_date=date.today() + timedelta(days=7),
        )
        # Devolver el préstamo
        loan.status = Loan.LoanStatus.RETURNED
        loan.actual_return_date = date.today()
        loan.save(update_fields=['status', 'actual_return_date'])
        
        self.assertEqual(self.book.available_stock, 3)


class LoanCreationTestCase(TestCase):
    """Tests de las reglas de negocio al crear préstamos."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Libro Test",
            author="Autor Test",
            synopsis="Sinopsis test.",
            total_stock=1,
        )
        
        # Estudiante
        self.user_s = User.objects.create_user(username="estudiante_test", password="123")
        self.student = Student.objects.create(
            user=self.user_s, personal_id="98020212345", career="Informática", academic_year=1
        )
        
        # Profesor
        self.user_t = User.objects.create_user(username="profe_test", password="123")
        self.teacher = Teacher.objects.create(
            user=self.user_t, personal_id="80040412345", department="Matemática"
        )

    def test_prestamo_estudiante_exitoso(self):
        """Se debe poder crear un préstamo válido para un estudiante."""
        loan = Loan.objects.create(
            book=self.book,
            student=self.student,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.assertEqual(loan.status, Loan.LoanStatus.ACTIVE)

    def test_prestamo_profesor_exitoso(self):
        """Se debe poder crear un préstamo válido para un profesor."""
        loan = Loan.objects.create(
            book=self.book,
            teacher=self.teacher,
            expected_return_date=date.today() + timedelta(days=15),
        )
        self.assertEqual(loan.status, Loan.LoanStatus.ACTIVE)

    def test_no_prestar_a_ambos(self):
        """No se puede prestar a un profesor y un estudiante en el mismo registro."""
        with self.assertRaises(ValidationError):
            Loan.objects.create(
                book=self.book,
                student=self.student,
                teacher=self.teacher,
                expected_return_date=date.today() + timedelta(days=7),
            )

    def test_no_se_puede_prestar_sin_stock(self):
        """No se debe poder prestar un libro sin stock disponible."""
        # Agotamos el único stock
        Loan.objects.create(
            book=self.book,
            student=self.student,
            expected_return_date=date.today() + timedelta(days=7),
        )
        # Intentamos un segundo préstamo
        with self.assertRaises(ValidationError):
            Loan.objects.create(
                book=self.book,
                teacher=self.teacher,
                expected_return_date=date.today() + timedelta(days=7),
            )

    def test_fecha_devolucion_debe_ser_futura(self):
        """La fecha de devolución debe ser posterior a hoy."""
        with self.assertRaises(ValidationError):
            Loan.objects.create(
                book=self.book,
                student=self.student,
                expected_return_date=date.today(), # Error: devuelve hoy mismo
            )


class LoanStatusTestCase(TestCase):
    """Tests del cálculo automático de estado del préstamo."""

    def setUp(self):
        self.book = Book.objects.create(title="Libro Estado", total_stock=5)
        self.user = User.objects.create_user(username="estudiante_estado", password="123")
        self.student = Student.objects.create(user=self.user, personal_id="01030312345", academic_year=1)

    def test_prestamo_nuevo_es_activo(self):
        """Un préstamo nuevo debe tener estado ACTIVE por defecto."""
        loan = Loan.objects.create(
            book=self.book,
            student=self.student,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.assertEqual(loan.status, Loan.LoanStatus.ACTIVE)

    def test_devolucion_calcula_estado_automatico(self):
       """Al asignar la fecha real de devolución, el estado debe cambiar a RETURNED automáticamente."""
       loan = Loan.objects.create(
           book=self.book,
           student=self.student,
           expected_return_date=date.today() + timedelta(days=7),
       )
       
       # Le indicamos al sistema que el libro fue devuelto hoy
       loan.actual_return_date = date.today()
       loan.save()
       
       # Verificamos que el modelo haya reaccionado y cambiado el estado
       self.assertEqual(loan.status, Loan.LoanStatus.RETURNED)


class BlacklistTestCase(TestCase):
    """Tests relacionados con la lista negra de usuarios."""

    def setUp(self):
        self.book = Book.objects.create(title="Libro Blacklist", total_stock=5)
        
        # Estudiante Moroso
        self.user_s = User.objects.create_user(username="estudiante_bl", password="123")
        self.bad_student = Student.objects.create(
            user=self.user_s, personal_id="95050512345", academic_year=1, is_blacklisted=True
        )
        
        # Profesor Moroso
        self.user_t = User.objects.create_user(username="profe_bl", password="123")
        self.bad_teacher = Teacher.objects.create(
            user=self.user_t, personal_id="70060612345", is_blacklisted=True
        )

    def test_estudiante_moroso_bloqueado(self):
        """Un estudiante en lista negra no debe poder pedir préstamos."""
        with self.assertRaises(ValidationError):
            Loan.objects.create(
                book=self.book,
                student=self.bad_student,
                expected_return_date=date.today() + timedelta(days=7),
            )

    def test_profesor_moroso_bloqueado(self):
        """Un profesor en lista negra no debe poder pedir préstamos."""
        with self.assertRaises(ValidationError):
            Loan.objects.create(
                book=self.book,
                teacher=self.bad_teacher,
                expected_return_date=date.today() + timedelta(days=7),
            )
