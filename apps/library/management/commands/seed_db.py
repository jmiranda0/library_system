import random
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from apps.library.models import Book, Student, Loan
from apps.library.forms import StudentAdminForm

# Datos falsos para sembrar
BOOKS_DATA = [
    {
        "title": "Cien Años de Soledad",
        "author": "Gabriel García Márquez",
        "synopsis": "La novela narra la historia de la familia Buendía a lo largo de siete generaciones en el pueblo ficticio de Macondo.",
        "total_stock": 5,
        "cover_image": "https://m.media-amazon.com/images/I/71yoWmE37lL._AC_UF1000,1000_QL80_.jpg"
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "synopsis": "Incluso un mal código puede funcionar. Pero si el código no es limpio, puede poner a una organización de desarrollo de rodillas.",
        "total_stock": 3,
        "cover_image": "https://m.media-amazon.com/images/I/41xShlnTZTL._AC_UF1000,1000_QL80_.jpg"
    },
    {
        "title": "Don Quijote de la Mancha",
        "author": "Miguel de Cervantes",
        "synopsis": "Las aventuras de Alonso Quijano, un hidalgo pobre que de tanto leer novelas de caballería acaba enloqueciendo y creyendo ser un caballero andante.",
        "total_stock": 2,
        "cover_image": "https://m.media-amazon.com/images/I/811n3+D0Y-L._AC_UF1000,1000_QL80_.jpg"
    },
    {
        "title": "El Señor de los Anillos",
        "author": "J.R.R. Tolkien",
        "synopsis": "Un grupo de héroes se embarca en una misión para destruir el Anillo Único y salvar a la Tierra Media del Señor Oscuro Sauron.",
        "total_stock": 4,
        "cover_image": "https://m.media-amazon.com/images/I/71jLBHtWJWL._AC_UF1000,1000_QL80_.jpg"
    },
    {
        "title": "Introducción a los algoritmos",
        "author": "Thomas H. Cormen",
        "synopsis": "Un libro de texto completo que cubre una amplia gama de algoritmos en profundidad, manteniendo el diseño y el análisis accesibles.",
        "total_stock": 2,
        "cover_image": "https://m.media-amazon.com/images/I/61Pgdn8Ys-L._AC_UF1000,1000_QL80_.jpg"
    },
    {
        "title": "1984",
        "author": "George Orwell",
        "synopsis": "Una novela distópica que explora los peligros del totalitarismo, la vigilancia masiva y la represión de la libertad.",
        "total_stock": 6,
        "cover_image": "https://m.media-amazon.com/images/I/61ZewDE3beL._AC_UF1000,1000_QL80_.jpg"
    },
    {
        "title": "Crónica de una muerte anunciada",
        "author": "Gabriel García Márquez",
        "synopsis": "La historia del asesinato de Santiago Nasar a manos de los hermanos Vicario para vengar el honor de su hermana.",
        "total_stock": 4,
        "cover_image": "https://m.media-amazon.com/images/I/81xUBNJv9cL._AC_UF1000,1000_QL80_.jpg"
    },
    {
        "title": "Fahrenheit 451",
        "author": "Ray Bradbury",
        "synopsis": "En una sociedad futura, los bomberos tienen la misión de quemar libros, ya que leer está prohibido.",
        "total_stock": 3,
        "cover_image": "https://m.media-amazon.com/images/I/61l8jzZnxgL._AC_UF1000,1000_QL80_.jpg"
    }
]

STUDENTS_DATA = [
    {"user": {"username": "carlos", "first_name": "Carlos", "last_name": "Pérez"}, "student": {"personal_id": "01020304051", "career": "Ingeniería Informática", "academic_year": 3}},
    {"user": {"username": "ana", "first_name": "Ana", "last_name": "Gómez"}, "student": {"personal_id": "99080706052", "career": "Arquitectura", "academic_year": 2}},
    {"user": {"username": "luis", "first_name": "Luis", "last_name": "Martínez"}, "student": {"personal_id": "02040608013", "career": "Medicina", "academic_year": 4}},
    {"user": {"username": "maria", "first_name": "María", "last_name": "Rodríguez"}, "student": {"personal_id": "03050709024", "career": "Derecho", "academic_year": 1}},
]

class Command(BaseCommand):
    help = 'Puebla la base de datos con libros, estudiantes y préstamos falsos para pruebas.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Borrando datos anteriores (Préstamos, Estudiantes, Libros)...")
        Loan.objects.all().delete()
        Student.objects.all().delete()
        Book.objects.all().delete()
        
        # Eliminar usuarios de estudiantes para recrearlos limpios
        student_usernames = [s['user']['username'] for s in STUDENTS_DATA]
        User.objects.filter(username__in=student_usernames).delete()

        self.stdout.write("Creando libros...")
        books = []
        for data in BOOKS_DATA:
            book = Book.objects.create(**data)
            books.append(book)
        
        self.stdout.write("Creando estudiantes...")
        students = []
        # Utilizamos el formulario personalizado para que cree el user, asigne el grupo y cree el student
        for data in STUDENTS_DATA:
            # Simulamos un POST al form
            form_data = {
                'username': data['user']['username'],
                'first_name': data['user']['first_name'],
                'last_name': data['user']['last_name'],
                'password': 'password123', # Contraseña por defecto
                'personal_id': data['student']['personal_id'],
                'career': data['student']['career'],
                'academic_year': data['student']['academic_year'],
                'is_blacklisted': False
            }
            form = StudentAdminForm(data=form_data)
            if form.is_valid():
                student = form.save()
                students.append(student)
            else:
                self.stdout.write(self.style.ERROR(f"Error creando estudiante {data['user']['username']}: {form.errors}"))

        self.stdout.write("Creando préstamos (Activos, Devueltos, Vencidos)...")
        
        today = date.today()
        
        # 1. Préstamo Activo
        Loan.objects.create(
            book=random.choice(books),
            student=students[0],
            status='ACTIVE',
            # Modificamos loan_date después de crearlo porque auto_now_add lo sobreescribe
            expected_return_date=today + timedelta(days=7)
        )
        # Modificamos la fecha de creación simulando que fue ayer
        l1 = Loan.objects.last()
        l1.loan_date = today - timedelta(days=1)
        l1.save()

        # 2. Préstamo Devuelto
        l2 = Loan(
            book=random.choice(books),
            student=students[0],
            status='RETURNED',
            expected_return_date=today + timedelta(days=5), # Temporary to pass validation
        )
        l2.save() # Saves with today's date
        # Now update to historical dates
        Loan.objects.filter(pk=l2.pk).update(
            loan_date=today - timedelta(days=15),
            expected_return_date=today - timedelta(days=5),
            actual_return_date=today - timedelta(days=6)
        )

        # 3. Préstamo Vencido
        l3 = Loan(
            book=random.choice(books),
            student=students[1],
            status='OVERDUE',
            expected_return_date=today + timedelta(days=5), # Temporary
        )
        l3.save()
        Loan.objects.filter(pk=l3.pk).update(
            loan_date=today - timedelta(days=12),
            expected_return_date=today - timedelta(days=2)
        )
        
        # 4. Otro activo
        Loan.objects.create(
            book=random.choice(books),
            student=students[2],
            status='ACTIVE',
            expected_return_date=today + timedelta(days=3)
        )

        self.stdout.write(self.style.SUCCESS("¡Base de datos poblada exitosamente!"))
        self.stdout.write(self.style.WARNING("Los estudiantes tienen la contraseña: password123"))
