import random
from datetime import date, timedelta
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from apps.library.models import Book, Student, Teacher, Loan

# LOS 30 LIBROS ORIGINALES
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

# LOS 10 ESTUDIANTES ORIGINALES
STUDENTS_DATA = [
    {"user": {"username": "carlos", "first_name": "Carlos", "last_name": "Pérez"}, "student": {"personal_id": "01020304051", "career": "Informática", "academic_year": 3, "is_blacklisted": False}},
    {"user": {"username": "ana", "first_name": "Ana", "last_name": "Gómez"}, "student": {"personal_id": "99080706052", "career": "Arquitectura", "academic_year": 2, "is_blacklisted": False}},
    {"user": {"username": "luis", "first_name": "Luis", "last_name": "Martínez"}, "student": {"personal_id": "02040608013", "career": "Medicina", "academic_year": 4, "is_blacklisted": False}},
    {"user": {"username": "el.moroso", "first_name": "Pedro", "last_name": "Mala-Paga"}, "student": {"personal_id": "88080808088", "career": "Derecho", "academic_year": 5, "is_blacklisted": True}},
    {"user": {"username": "deudora.pro", "first_name": "Marta", "last_name": "Sancionada"}, "student": {"personal_id": "77070707077", "career": "Psicología", "academic_year": 1, "is_blacklisted": True}},
    {"user": {"username": "sofia", "first_name": "Sofía", "last_name": "López"}, "student": {"personal_id": "11121314156", "career": "Biología", "academic_year": 2, "is_blacklisted": False}},
    {"user": {"username": "juan", "first_name": "Juan", "last_name": "Castro"}, "student": {"personal_id": "22232425267", "career": "Química", "academic_year": 3, "is_blacklisted": False}},
    {"user": {"username": "elena", "first_name": "Elena", "last_name": "Blanco"}, "student": {"personal_id": "33343536378", "career": "Matemáticas", "academic_year": 4, "is_blacklisted": False}},
    {"user": {"username": "jorge", "first_name": "Jorge", "last_name": "Díaz"}, "student": {"personal_id": "44454647489", "career": "Física", "academic_year": 1, "is_blacklisted": False}},
    {"user": {"username": "laura", "first_name": "Laura", "last_name": "Torres"}, "student": {"personal_id": "55565758590", "career": "Economía", "academic_year": 2, "is_blacklisted": False}},
]

TEACHERS_DATA = [
    {"user": {"username": "profe_juan", "first_name": "Juan", "last_name": "Profesor"}, "teacher": {"personal_id": "60010101011", "department": "Ciencias de la Computación", "is_blacklisted": False}},
    {"user": {"username": "profe_maria", "first_name": "María", "last_name": "Docente"}, "teacher": {"personal_id": "70020202022", "department": "Matemática Aplicada", "is_blacklisted": False}},
]

class Command(BaseCommand):
    help = 'Puebla la base de datos con libros, estudiantes, profesores y volumen de préstamos para gráficos.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Borrando datos anteriores (Préstamos, Estudiantes, Profesores, Libros)...")
        Loan.objects.all().delete()
        Student.objects.all().delete()
        Teacher.objects.all().delete()
        Book.objects.all().delete()
        
        # Eliminar usuarios creados por el seeder
        usernames_to_delete = [s['user']['username'] for s in STUDENTS_DATA] + \
                              [t['user']['username'] for t in TEACHERS_DATA] + \
                              ['supervisor1', 'biblio1', 'biblio2']
        User.objects.filter(username__in=usernames_to_delete).delete()

        # ---------------------------------------------------------
        # 1. ROLES ADMINISTRATIVOS (Contraseñas específicas)
        # ---------------------------------------------------------
        self.stdout.write("Creando Supervisor y Bibliotecarios...")
        grupo_sup, _ = Group.objects.get_or_create(name='Supervisores')
        grupo_bib, _ = Group.objects.get_or_create(name='Bibliotecarios')

        sup = User.objects.create_user(username='supervisor1', password='password123', first_name='Jefe', last_name='Supervisor', is_staff=True)
        sup.groups.add(grupo_sup)

        # Bibliotecarios (Pass: biblioteca123)
        for i in range(1, 3):
            bib = User.objects.create_user(username=f'biblio{i}', password='biblioteca123', first_name=f'Biblio{i}', last_name='Staff', is_staff=True)
            bib.groups.add(grupo_bib)

        # ---------------------------------------------------------
        # 2. LIBROS (Con recomendaciones para el Top 5 de IA)
        # ---------------------------------------------------------
        self.stdout.write("Creando 30 libros...")
        books = []
        for data in BOOKS_DATA:
            # Simulamos que la IA ya recomendó estos libros varias veces para el gráfico
            data['ai_recommendations_count'] = random.randint(0, 45)
            book = Book.objects.create(**data)
            books.append(book)
        
        # ---------------------------------------------------------
        # 3. ESTUDIANTES (Contraseña: Su Carné de Identidad)
        # ---------------------------------------------------------
        self.stdout.write("Creando 10 estudiantes...")
        grupo_est, _ = Group.objects.get_or_create(name='Estudiantes')
        students = []
        for data in STUDENTS_DATA:
            # Creamos el user directo, es más seguro en el seeder que usar el Form
            u = User.objects.create_user(
                username=data['user']['username'],
                password=data['student']['personal_id'], # Contraseña = Carnet
                first_name=data['user']['first_name'],
                last_name=data['user']['last_name']
            )
            u.groups.add(grupo_est)
            student = Student.objects.create(
                user=u,
                personal_id=data['student']['personal_id'],
                career=data['student']['career'],
                academic_year=data['student']['academic_year'],
                is_blacklisted=data['student']['is_blacklisted']
            )
            students.append(student)

        # ---------------------------------------------------------
        # 4. PROFESORES
        # ---------------------------------------------------------
        self.stdout.write("Creando profesores...")
        grupo_prof, _ = Group.objects.get_or_create(name='Profesores')
        teachers = []
        for data in TEACHERS_DATA:
            u = User.objects.create_user(
                username=data['user']['username'],
                password='password123',
                first_name=data['user']['first_name'],
                last_name=data['user']['last_name']
            )
            u.groups.add(grupo_prof)
            teacher = Teacher.objects.create(
                user=u,
                personal_id=data['teacher']['personal_id'],
                department=data['teacher']['department'],
                is_blacklisted=data['teacher']['is_blacklisted']
            )
            teachers.append(teacher)

        # -----------# ---------------------------------------------------------
        # 5. PRÉSTAMOS MASIVOS PARA GRAFICAR
        # ---------------------------------------------------------
        self.stdout.write("Generando volumen histórico de préstamos...")
        today = date.today()
        
        # A. Casos de lista negra: Pedro y Marta
        pedro = students[3] # el.moroso
        pedro.is_blacklisted = False; pedro.save()
        
        # CORRECCIÓN: Le sumamos días a 'today' para que pase la validación de tu modelo
        Loan.objects.create(book=books[0], student=pedro, status='ACTIVE', expected_return_date=today + timedelta(days=7))
        Loan.objects.filter(pk=Loan.objects.last().pk).update(loan_date=today - timedelta(days=150), expected_return_date=today - timedelta(days=120))
        pedro.is_blacklisted = True; pedro.save()

        marta = students[4] # deudora.pro
        marta.is_blacklisted = False; marta.save()
        Loan.objects.create(book=books[5], student=marta, status='OVERDUE', expected_return_date=today + timedelta(days=7))
        Loan.objects.filter(pk=Loan.objects.last().pk).update(loan_date=today - timedelta(days=90), expected_return_date=today - timedelta(days=75))
        marta.is_blacklisted = True; marta.save()

         # B. Generar entre 3 y 8 préstamos históricos para CADA ESTUDIANTE SANO
        for student in students:
            if student.is_blacklisted: continue
            
            num_loans = random.randint(3, 8)
            for _ in range(num_loans):
                book = random.choice(books)
                
                # 80% de probabilidad de que sea devuelto (historial viejo), 20% de que sea activo
                if random.random() < 0.8:
                    # Préstamo Devuelto (hace 1 a 6 meses atrás)
                    # CORRECCIÓN AQUÍ: Verificamos stock ANTES de intentar crearlo
                    if book.available_stock > 0:
                        dias_atras = random.randint(30, 180)
                        l = Loan.objects.create(book=book, student=student, status='RETURNED', expected_return_date=today + timedelta(days=7))
                        Loan.objects.filter(pk=l.pk).update(
                            loan_date=today - timedelta(days=dias_atras),
                            expected_return_date=today - timedelta(days=dias_atras - 15),
                            actual_return_date=today - timedelta(days=dias_atras - 10) # Entregó a tiempo
                        )
                else:
                    # Préstamo Activo reciente
                    if book.available_stock > 0:
                        Loan.objects.create(
                            book=book, student=student, status='ACTIVE',
                            expected_return_date=today + timedelta(days=random.randint(1, 15))
                        )
        # C. Generar algunos préstamos para profesores
        for teacher in teachers:
            for _ in range(3):
                book = random.choice(books)
                if book.available_stock > 0:
                    # CORRECCIÓN: Agregado timedelta
                    l = Loan.objects.create(book=book, teacher=teacher, status='RETURNED', expected_return_date=today + timedelta(days=7))
                    dias_atras = random.randint(10, 100)
                    Loan.objects.filter(pk=l.pk).update(
                        loan_date=today - timedelta(days=dias_atras),
                        expected_return_date=today - timedelta(days=dias_atras - 30),
                        actual_return_date=today - timedelta(days=dias_atras - 28)
                    )

        self.stdout.write(self.style.SUCCESS("✅ ¡Base de datos poblada exitosamente!"))
        self.stdout.write(self.style.WARNING("▶ Supervisores/Profesores pass: password123"))
        self.stdout.write(self.style.WARNING("▶ Bibliotecarios pass: biblioteca123"))
        self.stdout.write(self.style.WARNING("▶ Estudiantes pass: SU CARNÉ DE IDENTIDAD (Ej. carlos = 01020304051)"))