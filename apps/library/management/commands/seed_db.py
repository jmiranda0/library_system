import random
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from apps.library.models import Book, Student, Loan
from apps.library.forms import StudentAdminForm

# Datos falsos para sembrar
BOOKS_DATA = [
    {"title": "Cien Años de Soledad", "author": "Gabriel García Márquez", "synopsis": "Realismo mágico en Macondo. La estirpe de los Buendía y su destino trágico y solitario.", "total_stock": 5},
    {"title": "Clean Code", "author": "Robert C. Martin", "synopsis": "Manual de ingeniería de software sobre código limpio, refactorización y mantenibilidad.", "total_stock": 3},
    {"title": "Don Quijote de la Mancha", "author": "Miguel de Cervantes", "synopsis": "Las aventuras de un hidalgo loco que cree ser caballero en la España del Siglo de Oro.", "total_stock": 2},
    {"title": "El Señor de los Anillos: La Comunidad del Anillo", "author": "J.R.R. Tolkien", "synopsis": "Fantasía épica sobre la misión de destruir un anillo maligno para salvar la Tierra Media.", "total_stock": 4},
    {"title": "1984", "author": "George Orwell", "synopsis": "Distopía sobre el Gran Hermano, la vigilancia totalitaria y la manipulación de la verdad.", "total_stock": 6},
    {"title": "Harry Potter y la Piedra Filosofal", "author": "J.K. Rowling", "synopsis": "Un niño descubre que es mago y asiste a Hogwarts para enfrentar al oscuro Lord Voldemort.", "total_stock": 8},
    {"title": "Sapiens: De animales a dioses", "author": "Yuval Noah Harari", "synopsis": "Historia de la humanidad desde la prehistoria hasta el futuro tecnológico y biológico.", "total_stock": 3},
    {"title": "El Código Da Vinci", "author": "Dan Brown", "synopsis": "Thriller sobre secretos religiosos ocultos en obras de arte de Leonardo da Vinci.", "total_stock": 5},
    {"title": "Breve historia del tiempo", "author": "Stephen Hawking", "synopsis": "Explicación de los agujeros negros, el Big Bang y la naturaleza del universo.", "total_stock": 3},
    {"title": "Orgullo y Prejuicio", "author": "Jane Austen", "synopsis": "Novela clásica sobre amor, clases sociales y malentendidos en la Inglaterra georgiana.", "total_stock": 4},
    # 20 Libros adicionales
    {"title": "Crímenes Ilustrados", "author": "Modesto García", "synopsis": "Libro de acertijos visuales y misterios policiales que desafían la lógica del lector.", "total_stock": 5},
    {"title": "El Alquimista", "author": "Paulo Coelho", "synopsis": "Fábula espiritual sobre un pastor que busca su Leyenda Personal en el desierto egipcio.", "total_stock": 4},
    {"title": "Crimen y Castigo", "author": "Fiódor Dostoyevski", "synopsis": "Exploración psicológica de la culpa y la redención tras un asesinato en San Petersburgo.", "total_stock": 2},
    {"title": "El Principito", "author": "Antoine de Saint-Exupéry", "synopsis": "Cuento filosófico sobre un pequeño príncipe que viaja por planetas aprendiendo sobre la vida.", "total_stock": 10},
    {"title": "Python Crash Course", "author": "Eric Matthes", "synopsis": "Introducción práctica a la programación con Python, proyectos y mejores prácticas.", "total_stock": 5},
    {"title": "Los Miserables", "author": "Victor Hugo", "synopsis": "Épica francesa sobre la justicia, la redención y la lucha social en el siglo XIX.", "total_stock": 3},
    {"title": "El Psicoanalista", "author": "John Katzenbach", "synopsis": "Thriller psicológico sobre un doctor amenazado de muerte en su 53 cumpleaños.", "total_stock": 4},
    {"title": "La sombra del viento", "author": "Carlos Ruiz Zafón", "synopsis": "Misterio en la Barcelona de posguerra centrado en el Cementerio de los Libros Olvidados.", "total_stock": 6},
    {"title": "Cosmos", "author": "Carl Sagan", "synopsis": "Exploración de la ciencia, la astronomía y el lugar de la humanidad en el universo.", "total_stock": 3},
    {"title": "Metamorfosis", "author": "Franz Kafka", "synopsis": "Un hombre despierta convertido en un insecto gigante, analizando la alienación humana.", "total_stock": 2},
    {"title": "El Resplandor", "author": "Stephen King", "synopsis": "Terror sobrenatural en un hotel aislado donde la locura acecha a una familia.", "total_stock": 4},
    {"title": "Crónica de una muerte anunciada", "author": "Gabriel García Márquez", "synopsis": "Relato fatalista sobre un asesinato planeado que todo el pueblo conocía pero nadie evitó.", "total_stock": 5},
    {"title": "La ladrona de libros", "author": "Markus Zusak", "synopsis": "La historia de una niña en la Alemania nazi narrada por la mismísima Muerte.", "total_stock": 4},
    {"title": "Rayuela", "author": "Julio Cortázar", "synopsis": "Novela experimental que puede leerse en diferentes órdenes, rompiendo la estructura clásica.", "total_stock": 3},
    {"title": "Ensayo sobre la ceguera", "author": "José Saramago", "synopsis": "Una epidemia de ceguera blanca revela la brutalidad y la esperanza de la naturaleza humana.", "total_stock": 4},
    {"title": "El nombre de la rosa", "author": "Umberto Eco", "synopsis": "Misterio medieval en una abadía italiana donde ocurren extraños asesinatos vinculados a libros.", "total_stock": 3},
    {"title": "Fundación", "author": "Isaac Asimov", "synopsis": "Ciencia ficción sobre la psicohistoria y la lucha por salvar el conocimiento humano en el imperio galáctico.", "total_stock": 5},
    {"title": "Drácula", "author": "Bram Stoker", "synopsis": "La novela epistolar clásica que definió el mito del vampiro moderno y el terror gótico.", "total_stock": 3},
    {"title": "El retrato de Dorian Gray", "author": "Oscar Wilde", "synopsis": "Un joven mantiene su belleza eterna mientras su retrato envejece y muestra sus pecados.", "total_stock": 4},
    {"title": "La Odisea", "author": "Homero", "synopsis": "El regreso épico de Ulises a Ítaca tras la Guerra de Troya, enfrentando monstruos y dioses.", "total_stock": 2}
]

STUDENTS_DATA = [
    {"user": {"username": "carlos", "first_name": "Carlos", "last_name": "Pérez"}, "student": {"personal_id": "01020304051", "career": "Informática", "academic_year": 3, "is_blacklisted": False}},
    {"user": {"username": "ana", "first_name": "Ana", "last_name": "Gómez"}, "student": {"personal_id": "99080706052", "career": "Arquitectura", "academic_year": 2, "is_blacklisted": False}},
    {"user": {"username": "luis", "first_name": "Luis", "last_name": "Martínez"}, "student": {"personal_id": "02040608013", "career": "Medicina", "academic_year": 4, "is_blacklisted": False}},
    {"user": {"username": "el.moroso", "first_name": "Pedro", "last_name": "Mala-Paga"}, "student": {"personal_id": "88080808088", "career": "Derecho", "academic_year": 5, "is_blacklisted": True}},
    {"user": {"username": "deudora.pro", "first_name": "Marta", "last_name": "Sancionada"}, "student": {"personal_id": "77070707077", "career": "Psicología", "academic_year": 1, "is_blacklisted": True}},
    # 5 Estudiantes adicionales
    {"user": {"username": "sofia", "first_name": "Sofía", "last_name": "López"}, "student": {"personal_id": "11121314156", "career": "Biología", "academic_year": 2, "is_blacklisted": False}},
    {"user": {"username": "juan", "first_name": "Juan", "last_name": "Castro"}, "student": {"personal_id": "22232425267", "career": "Química", "academic_year": 3, "is_blacklisted": False}},
    {"user": {"username": "elena", "first_name": "Elena", "last_name": "Blanco"}, "student": {"personal_id": "33343536378", "career": "Matemáticas", "academic_year": 4, "is_blacklisted": False}},
    {"user": {"username": "jorge", "first_name": "Jorge", "last_name": "Díaz"}, "student": {"personal_id": "44454647489", "career": "Física", "academic_year": 1, "is_blacklisted": False}},
    {"user": {"username": "laura", "first_name": "Laura", "last_name": "Torres"}, "student": {"personal_id": "55565758590", "career": "Economía", "academic_year": 2, "is_blacklisted": False}},
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
                'is_blacklisted': data['student']['is_blacklisted']
            }
            form = StudentAdminForm(data=form_data)
            if form.is_valid():
                student = form.save()
                students.append(student)
            else:
                self.stdout.write(self.style.ERROR(f"Error creando estudiante {data['user']['username']}: {form.errors}"))

        self.stdout.write("Creando préstamos masivos e interactividad...")
        
        today = date.today()
        
        # 1. Pedro Mala-Paga (el.moroso): Historial de desastre
        pedro = students[3]
        pedro.is_blacklisted = False
        pedro.save()

        # A. Un libro que NUNCA devolvió (Sigue ACTIVO pero vencido hace meses)
        Loan.objects.create(
            book=books[0], # Cien años de soledad
            student=pedro,
            status='ACTIVE',
            expected_return_date=today + timedelta(days=7) # Temporal para pasar validación
        )
        l_pedro_vencido = Loan.objects.last()
        Loan.objects.filter(pk=l_pedro_vencido.pk).update(
            loan_date=today - timedelta(days=150),
            expected_return_date=today - timedelta(days=120)
        )

        # B. Libros devueltos con 6 meses de retraso
        for i in range(2):
            l_late = Loan(
                book=random.choice(books),
                student=pedro,
                status='RETURNED',
                expected_return_date=today + timedelta(days=7), # Temporal
            )
            l_late.save()
            Loan.objects.filter(pk=l_late.pk).update(
                loan_date=today - timedelta(days=230),
                expected_return_date=today - timedelta(days=215),
                actual_return_date=today - timedelta(days=15)
            )
        
        pedro.is_blacklisted = True
        pedro.save()

        # 2. Interactividad para el resto de estudiantes (Préstamos aleatorios)
        for student in students:
            if student.user.username in ['el.moroso', 'deudora.pro']:
                continue
                
            num_loans = random.randint(2, 5)
            for _ in range(num_loans):
                tipo = random.choice(['RETURNED', 'ACTIVE', 'RETURNED'])
                book = random.choice(books)
                
                if tipo == 'RETURNED':
                    l = Loan(
                        book=book,
                        student=student,
                        status='RETURNED',
                        expected_return_date=today + timedelta(days=7), # Temporal
                    )
                    l.save()
                    dias_atras = random.randint(20, 60)
                    Loan.objects.filter(pk=l.pk).update(
                        loan_date=today - timedelta(days=dias_atras),
                        expected_return_date=today - timedelta(days=dias_atras - 15),
                        actual_return_date=today - timedelta(days=random.randint(1, dias_atras - 16))
                    )
                else:
                    Loan.objects.create(
                        book=book,
                        student=student,
                        status='ACTIVE',
                        expected_return_date=today + timedelta(days=random.randint(1, 15))
                    )

        # 3. Marta (deudora.pro) - Bloqueada por un préstamo muy viejo
        marta = students[4]
        marta.is_blacklisted = False
        marta.save()
        
        l_marta = Loan(
            book=books[5], # Harry Potter
            student=marta,
            status='OVERDUE',
            expected_return_date=today + timedelta(days=7), # Temporal
        )
        l_marta.save()
        Loan.objects.filter(pk=l_marta.pk).update(
            loan_date=today - timedelta(days=90),
            expected_return_date=today - timedelta(days=75)
        )
        
        marta.is_blacklisted = True
        marta.save()

        self.stdout.write(self.style.SUCCESS("¡Base de datos poblada exitosamente!"))
        self.stdout.write(self.style.WARNING("Los estudiantes tienen la contraseña: password123"))
