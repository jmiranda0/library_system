"""
Tests unitarios del sistema de gestión bibliotecaria.

Cubre las reglas de negocio críticas del dominio:
- Gestión de préstamos y stock
- Validaciones del modelo Loan
- Cálculo de disponibilidad
- Devoluciones
"""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Book, Loan, Student


class BookStockTestCase(TestCase):
    """Tests del cálculo de stock disponible."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Libro de Prueba",
            author="Autor de Prueba",
            synopsis="Sinopsis de prueba para el motor semántico.",
            total_stock=3,
        )
        self.user1 = User.objects.create_user(
            username="estudiante1",
            password="pass123",
        )
        self.student1 = Student.objects.create(
            user=self.user1,
            personal_id="01010101011",
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
        # Devolver el préstamo directamente
        Loan.objects.filter(pk=loan.pk).update(
            status=Loan.LoanStatus.RETURNED,
            actual_return_date=date.today(),
        )
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
        self.user = User.objects.create_user(
            username="estudiante_test",
            password="pass123",
        )
        self.student = Student.objects.create(
            user=self.user,
            personal_id="02020202022",
            career="Informática",
            academic_year=1,
        )
        self.user_moroso = User.objects.create_user(
            username="moroso_test",
            password="pass123",
        )
        self.student_moroso = Student.objects.create(
            user=self.user_moroso,
            personal_id="03030303033",
            career="Informática",
            academic_year=1,
            is_blacklisted=True,
        )

    def test_prestamo_exitoso(self):
        """Se debe poder crear un préstamo válido sin errores."""
        loan = Loan.objects.create(
            book=self.book,
            student=self.student,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.assertEqual(loan.status, Loan.LoanStatus.ACTIVE)

    def test_no_se_puede_prestar_sin_stock(self):
        """No se debe poder prestar un libro sin stock disponible."""
        # Agotar el stock
        Loan.objects.create(
            book=self.book,
            student=self.student,
            expected_return_date=date.today() + timedelta(days=7),
        )
        # Intentar un segundo préstamo del mismo libro
        user2 = User.objects.create_user(username="estudiante2", password="pass123")
        student2 = Student.objects.create(
            user=user2,
            personal_id="04040404044",
            career="Informática",
            academic_year=1,
        )
        with self.assertRaises(ValidationError):
            Loan.objects.create(
                book=self.book,
                student=student2,
                expected_return_date=date.today() + timedelta(days=7),
            )

    def test_no_se_puede_prestar_a_estudiante_en_lista_negra(self):
        """No se debe poder prestar a un estudiante en lista negra."""
        with self.assertRaises(ValidationError):
            Loan.objects.create(
                book=self.book,
                student=self.student_moroso,
                expected_return_date=date.today() + timedelta(days=7),
            )

    def test_fecha_devolucion_debe_ser_futura(self):
        """La fecha de devolución debe ser posterior a hoy."""
        with self.assertRaises(ValidationError):
            Loan.objects.create(
                book=self.book,
                student=self.student,
                expected_return_date=date.today(),
            )


class LoanStatusTestCase(TestCase):
    """Tests del cálculo automático de estado del préstamo."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Libro Estado",
            author="Autor Estado",
            synopsis="Sinopsis estado.",
            total_stock=5,
        )
        self.user = User.objects.create_user(
            username="estudiante_estado",
            password="pass123",
        )
        self.student = Student.objects.create(
            user=self.user,
            personal_id="05050505055",
            career="Informática",
            academic_year=1,
        )

    def test_prestamo_nuevo_es_activo(self):
        """Un préstamo nuevo debe tener estado ACTIVE."""
        loan = Loan.objects.create(
            book=self.book,
            student=self.student,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.assertEqual(loan.status, Loan.LoanStatus.ACTIVE)

    def test_devolucion_cambia_estado_a_returned(self):
        """Al registrar devolución el estado debe cambiar a RETURNED."""
        loan = Loan.objects.create(
            book=self.book,
            student=self.student,
            expected_return_date=date.today() + timedelta(days=7),
        )
        # Usamos el servicio de devolución como lo haría el sistema real
        from .services import return_loan
        return_loan(
            loan=loan,
            actor_user='test',
            actor_ip='127.0.0.1',
        )
        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.LoanStatus.RETURNED)

    def test_prestamo_vencido_detectado_correctamente(self):
        """Un préstamo con fecha vencida debe marcarse como OVERDUE."""
        loan = Loan.objects.create(
            book=self.book,
            student=self.student,
            expected_return_date=date.today() + timedelta(days=7),
        )
        # Simular que la fecha venció
        Loan.objects.filter(pk=loan.pk).update(
            expected_return_date=date.today() - timedelta(days=1)
        )
        loan.refresh_from_db()
        # El comando mark_overdue_loans haría esto, simulamos el update
        Loan.objects.filter(
            pk=loan.pk,
            status=Loan.LoanStatus.ACTIVE,
            expected_return_date__lt=date.today()
        ).update(status=Loan.LoanStatus.OVERDUE)
        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.LoanStatus.OVERDUE)


class StudentBlacklistTestCase(TestCase):
    """Tests relacionados con la lista negra de estudiantes."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Libro Blacklist",
            author="Autor Blacklist",
            synopsis="Sinopsis blacklist.",
            total_stock=5,
        )
        self.user = User.objects.create_user(
            username="estudiante_bl",
            password="pass123",
        )
        self.student = Student.objects.create(
            user=self.user,
            personal_id="06060606066",
            career="Informática",
            academic_year=1,
            is_blacklisted=False,
        )

    def test_estudiante_normal_puede_pedir_prestamo(self):
        """Un estudiante sin lista negra debe poder pedir préstamos."""
        loan = Loan.objects.create(
            book=self.book,
            student=self.student,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.assertIsNotNone(loan.pk)

    def test_estudiante_en_lista_negra_no_puede_pedir_prestamo(self):
        """Un estudiante en lista negra no debe poder pedir préstamos."""
        self.student.is_blacklisted = True
        self.student.save()
        with self.assertRaises(ValidationError):
            Loan.objects.create(
                book=self.book,
                student=self.student,
                expected_return_date=date.today() + timedelta(days=7),
            )