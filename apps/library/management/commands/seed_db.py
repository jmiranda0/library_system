import random
from datetime import date, timedelta
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from apps.library.models import Book, Student, Teacher, Loan
from apps.library.forms import StudentAdminForm

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
    {"title": "Crímenes Ilustrados", "author": "Modesto García", "synopsis": "Libro de acertijos visuales y misterios policiales que desafían la lógica del lector.", "total_stock": 5},
    {"title": "El Alquimista", "author": "Paulo Coelho", "synopsis": "Fábula espiritual sobre un pastor que busca su Leyenda Personal en el desierto egipcio.", "total_stock": 4},
    {"title": "Crimen y Castigo", "author": "Fiódor Dostoyevski", "synopsis": "Exploración psicológica de la culpa y la redención tras un asesinato en San Petersburgo.", "total_stock": 2},
    {"title": "El Principito", "author": "Antoine de Saint-Exupéry", "synopsis": "Cuento filosófico sobre un pequeño príncipe que viaja por planetas aprendiendo sobre la vida.", "total_stock": 10},
    {"title": "Python Crash Course", "author": "Eric Matthes", "synopsis": "Introducción práctica a la programación con Python, proyectos y mejores prácticas.", "total_stock": 5},
]

STUDENTS_DATA = [
    {"user": {"username": "carlos.perez", "first_name": "Carlos", "last_name": "Pérez"}, "student": {"personal_id": "01020304051", "career": "Informática", "academic_year": 3, "is_blacklisted": False}},
    {"user": {"username": "ana.gomez", "first_name": "Ana", "last_name": "Gómez"}, "student": {"personal_id": "99080706052", "career": "Arquitectura", "academic_year": 2, "is_blacklisted": False}},
    {"user": {"username": "luis.martinez", "first_name": "Luis", "last_name": "Martínez"}, "student": {"personal_id": "02040608013", "career": "Medicina", "academic_year": 4, "is_blacklisted": False}},
    {"user": {"username": "el.moroso", "first_name": "Pedro", "last_name": "Mala-Paga"}, "student": {"personal_id": "88080808088", "career": "Derecho", "academic_year": 5, "is_blacklisted": True}},
    {"user": {"username": "deudora.pro", "first_name": "Marta", "last_name": "Sancionada"}, "student": {"personal_id": "77070707077", "career": "Psicología", "academic_year": 1, "is_blacklisted": True}},
]

TEACHERS_DATA = [
    {"user": {"username": "profe.juan", "first_name": "Juan", "last_name": "Profesor"}, "teacher": {"personal_id": "60010101011", "department": "Ciencias de la Computación", "is_blacklisted": False}},
    {"user": {"username": "profe.maria", "first_name": "María", "last_name": "Docente"}, "teacher": {"personal_id": "70020202022", "department": "Matemática Aplicada", "is_blacklisted": False}},
]

class Command(BaseCommand):
    help = 'Puebla la base de datos de manera segura, respetando reglas de negocio.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Borrando datos anteriores de forma segura...")
        Loan.objects.all().delete()
        Student.objects.all().delete()
        Teacher.objects.all().delete()
        Book.objects.all().delete()
        
        # Eliminar usuarios anteriores
        usernames_to_delete = [s['user']['username'] for s in STUDENTS_DATA] + \
                              [t['user']['username'] for t in TEACHERS_DATA] + \
                              ['admin.sistema', 'supervisor1', 'biblio1', 'biblio2']
        User.objects.filter(username__in=usernames_to_delete).delete()

        # ---------------------------------------------------------
        # 1. ROLES DEL SISTEMA Y NEGOCIO
        # ---------------------------------------------------------
        self.stdout.write("Creando Roles Administrativos y de Negocio...")
        grupo_admin, _ = Group.objects.get_or_create(name='Administradores')
        grupo_sup, _ = Group.objects.get_or_create(name='Supervisores')
        grupo_bib, _ = Group.objects.get_or_create(name='Bibliotecarios')

        # Admin de Sistemas (Informático - No entra al negocio)
        admin_sys = User.objects.create_user(username='admin.sistema', password='password123', first_name='Admin', last_name='Sistemas', is_staff=True, is_superuser=False)
        admin_sys.groups.add(grupo_admin)

        # Supervisor (Director)
        sup = User.objects.create_user(username='supervisor1', password='password123', first_name='Jefe', last_name='Supervisor', is_staff=True)
        sup.groups.add(grupo_sup)

        # Bibliotecarios
        for i in range(1, 3):
            bib = User.objects.create_user(username=f'biblio{i}', password='password123', first_name=f'Biblio{i}', last_name='Staff', is_staff=True)
            bib.groups.add(grupo_bib)

        # ---------------------------------------------------------
        # 2. LIBROS
        # ---------------------------------------------------------
        self.stdout.write("Creando libros con puntaje de IA...")
        books = []
        for data in BOOKS_DATA:
            data['ai_recommendations_count'] = random.randint(0, 30)
            book = Book.objects.create(**data)
            books.append(book)
        
        # ---------------------------------------------------------
        # 3. ESTUDIANTES Y PROFESORES
        # ---------------------------------------------------------
        self.stdout.write("Creando Estudiantes y Profesores...")
        students = []
        for data in STUDENTS_DATA:
            u = User.objects.create_user(
                username=data['user']['username'],
                password=data['student']['personal_id'], # Contraseña = Carnet
                first_name=data['user']['first_name'],
                last_name=data['user']['last_name']
            )
            student = Student.objects.create(
                user=u,
                personal_id=data['student']['personal_id'],
                career=data['student']['career'],
                academic_year=data['student']['academic_year'],
                is_blacklisted=data['student']['is_blacklisted']
            )
            students.append(student)

        teachers = []
        for data in TEACHERS_DATA:
            u = User.objects.create_user(
                username=data['user']['username'],
                password=data['teacher']['personal_id'], # Contraseña = Carnet
                first_name=data['user']['first_name'],
                last_name=data['user']['last_name']
            )
            teacher = Teacher.objects.create(
                user=u,
                personal_id=data['teacher']['personal_id'],
                department=data['teacher']['department'],
                is_blacklisted=data['teacher']['is_blacklisted']
            )
            teachers.append(teacher)

        # ---------------------------------------------------------
        # 4. PRÉSTAMOS E HISTORIAL (CON BLINDAJE DE VALIDACIÓN)
        # ---------------------------------------------------------
        self.stdout.write("Generando préstamos...")
        today = date.today()
        tomorrow = today + timedelta(days=5) # Fecha segura para pasar validación

        # A. Casos de lista negra: Pedro y Marta
        pedro = students[3]
        pedro.is_blacklisted = False; pedro.save() # Temporalmente limpio para asignarle la mora
        
        # Creamos como activo para que pase validación
        l1 = Loan.objects.create(book=books[0], student=pedro, status='ACTIVE', expected_return_date=tomorrow)
        # Usamos update para forzar fechas pasadas sin disparar clean()
        Loan.objects.filter(pk=l1.pk).update(loan_date=today - timedelta(days=150), expected_return_date=today - timedelta(days=120), status='OVERDUE')
        
        pedro.is_blacklisted = True; pedro.save() # Sancionado

        # B. Generar préstamos para estudiantes sanos
        for student in students:
            if student.is_blacklisted: continue
            
            num_loans = random.randint(2, 5)
            for _ in range(num_loans):
                book = random.choice(books)
                
                if book.available_stock > 0:
                    if random.random() < 0.7:
                        # Préstamo Devuelto (Histórico)
                        l = Loan.objects.create(book=book, student=student, status='ACTIVE', expected_return_date=tomorrow)
                        dias_atras = random.randint(30, 180)
                        Loan.objects.filter(pk=l.pk).update(
                            loan_date=today - timedelta(days=dias_atras),
                            expected_return_date=today - timedelta(days=dias_atras - 15),
                            actual_return_date=today - timedelta(days=dias_atras - 10),
                            status='RETURNED'
                        )
                    else:
                        # Préstamo Activo
                        Loan.objects.create(book=book, student=student, status='ACTIVE', expected_return_date=today + timedelta(days=random.randint(1, 15)))

        # C. Generar préstamos para profesores
        for teacher in teachers:
            book = random.choice(books)
            if book.available_stock > 0:
                Loan.objects.create(book=book, teacher=teacher, status='ACTIVE', expected_return_date=today + timedelta(days=30))

        self.stdout.write(self.style.SUCCESS("✅ ¡Base de datos poblada exitosamente!"))
        self.stdout.write(self.style.WARNING("▶ Supervisor, Bibliotecarios y Admin IT pass: password123"))
        self.stdout.write(self.style.WARNING("▶ Estudiantes y Profesores pass: SU CARNÉ DE IDENTIDAD"))