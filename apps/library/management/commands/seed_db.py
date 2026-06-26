import random
import datetime
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from apps.library.models import Book, Student, Teacher, Loan

# ==========================================
# 1. DICCIONARIOS DE DATOS ORIGINALES
# ==========================================
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

STUDENTS_DATA = [
    {"user": {"username": "carlos", "first_name": "Carlos", "last_name": "Pérez"}, "student": {"personal_id": "01020304051", "career": "Ingeniería Informática", "academic_year": 3, "is_blacklisted": False}},
    {"user": {"username": "ana", "first_name": "Ana", "last_name": "Gómez"}, "student": {"personal_id": "99080706052", "career": "Ingeniería Informática", "academic_year": 2, "is_blacklisted": False}},
    {"user": {"username": "luis", "first_name": "Luis", "last_name": "Martínez"}, "student": {"personal_id": "02040608013", "career": "Ingeniería Informática", "academic_year": 4, "is_blacklisted": False}},
    {"user": {"username": "el.moroso", "first_name": "Pedro", "last_name": "Mala-Paga"}, "student": {"personal_id": "88080808088", "career": "Ingeniería Informática", "academic_year": 5, "is_blacklisted": True}},
    {"user": {"username": "deudora.pro", "first_name": "Marta", "last_name": "Sancionada"}, "student": {"personal_id": "77070707077", "career": "Ingeniería Informática", "academic_year": 1, "is_blacklisted": True}},
    {"user": {"username": "sofia", "first_name": "Sofía", "last_name": "López"}, "student": {"personal_id": "11121314156", "career": "Ingeniería Informática", "academic_year": 2, "is_blacklisted": False}},
    {"user": {"username": "juan", "first_name": "Juan", "last_name": "Castro"}, "student": {"personal_id": "22232425267", "career": "Ingeniería Informática", "academic_year": 3, "is_blacklisted": False}},
    {"user": {"username": "elena", "first_name": "Elena", "last_name": "Blanco"}, "student": {"personal_id": "33343536378", "career": "Ingeniería Informática", "academic_year": 4, "is_blacklisted": False}},
    {"user": {"username": "jorge", "first_name": "Jorge", "last_name": "Díaz"}, "student": {"personal_id": "44454647489", "career": "Ingeniería Informática", "academic_year": 1, "is_blacklisted": False}},
    {"user": {"username": "laura", "first_name": "Laura", "last_name": "Torres"}, "student": {"personal_id": "55565758590", "career": "Ingeniería Informática", "academic_year": 2, "is_blacklisted": False}},
]

TEACHERS_DATA = [
    {"user": {"username": "profe_juan", "first_name": "Juan", "last_name": "Profesor"}, "teacher": {"personal_id": "60010101011", "department": "Ciencias de la Computación", "is_blacklisted": False}},
    {"user": {"username": "profe_maria", "first_name": "María", "last_name": "Docente"}, "teacher": {"personal_id": "70020202022", "department": "Matemática Aplicada", "is_blacklisted": False}},
]

DEPARTMENTS = ["Ciencias de la Computación", "Matemática Aplicada", "Física", "Estructuras", "Humanidades"]
NOMBRES = ["Carlos", "Ana", "Luis", "Marta", "Jorge", "Elena", "Pedro", "Sofia", "Juan", "Laura", "Miguel", "Carmen", "David", "Lucia"]
APELLIDOS = ["Perez", "Gomez", "Martinez", "Rodriguez", "Fernandez", "Lopez", "Diaz", "Torres", "Ruiz", "Alonso", "Hernandez", "Garcia"]

def generar_ci_valido(start_year, end_year):
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
    dias_totales = (end_date - start_date).days
    random_date = start_date + datetime.timedelta(days=random.randint(0, dias_totales))
    y = f"{random_date.year % 100:02d}"
    m = f"{random_date.month:02d}"
    d = f"{random_date.day:02d}"
    rest = f"{random.randint(0, 99999):05d}"
    return f"{y}{m}{d}{rest}"

def clean_text(text):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower()

class Command(BaseCommand):
    help = 'Puebla la base de datos de manera segura, respetando reglas de negocio.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("⏳ Borrando datos anteriores..."))
        Loan.objects.all().delete()
        Student.objects.all().delete()
        Teacher.objects.all().delete()
        Book.objects.all().delete()
        
        usernames_to_delete = [s['user']['username'] for s in STUDENTS_DATA] + \
                              [t['user']['username'] for t in TEACHERS_DATA] + \
                              ['admin.sys', 'biblio1', 'biblio2', 'biblio3']
        User.objects.filter(username__in=usernames_to_delete).delete()
        
        # Eliminar cualquier usuario generado aleatoriamente
        User.objects.filter(is_superuser=False).delete()

        # ==========================================
        # FASE 1: ROLES Y PERMISOS
        # ==========================================
        self.stdout.write("🛡️ Configurando Personal Administrativo e IT...")
        grupo_admin, _ = Group.objects.get_or_create(name='Administradores')
        grupo_bib, _ = Group.objects.get_or_create(name='Bibliotecarios')

        # Admin de Sistemas
        admin_sys = User.objects.create_user(username='admin.sys', password='password123', first_name='Soporte', last_name='Técnico', is_staff=True, is_superuser=False)
        admin_sys.groups.add(grupo_admin)

        # Bibliotecarios
        for i in range(1, 4):
            bib = User.objects.create_user(username=f'biblio{i}', password='password123', first_name=f'Biblio{i}', last_name='Staff', is_staff=True)
            bib.groups.add(grupo_bib)

        # ==========================================
        # FASE 2: LIBROS
        # ==========================================
        self.stdout.write("📚 Insertando Catálogo de 30 Libros...")
        books = []
        for data in BOOKS_DATA:
            data['ai_recommendations_count'] = random.randint(1, 60)
            book = Book.objects.create(**data)
            books.append(book)

        # ==========================================
        # FASE 3: ESTUDIANTES Y PROFESORES
        # ==========================================
        self.stdout.write("🎓 Matriculando Estudiantes (Solo Informática) y Profesores...")
        students = []
        for data in STUDENTS_DATA:
            u = User.objects.create_user(
                username=data['user']['username'],
                password=data['student']['personal_id'],
                first_name=data['user']['first_name'],
                last_name=data['user']['last_name'],
                email=f"{data['user']['username']}@cujae.edu.cu"
            )
            student = Student.objects.create(
                user=u,
                personal_id=data['student']['personal_id'],
                career=data['student']['career'],
                academic_year=data['student']['academic_year'],
                is_blacklisted=data['student']['is_blacklisted']
            )
            students.append(student)

        # Generar 40 estudiantes extra (SOLO INFORMÁTICA)
        for _ in range(40):
            fname = random.choice(NOMBRES)
            lname = random.choice(APELLIDOS)
            username = f"{clean_text(fname)}.{clean_text(lname)}{random.randint(1,999)}"
            ci = generar_ci_valido(1998, 2005)
            
            u = User.objects.create_user(username=username, password=ci, first_name=fname, last_name=lname, email=f"{username}@cujae.edu.cu")
            student = Student.objects.create(
                user=u,
                personal_id=ci,
                career="Ingeniería Informática", # CLAVADO EN INFORMÁTICA
                academic_year=random.randint(1, 5),
                is_blacklisted=random.random() < 0.10
            )
            students.append(student)

        teachers = []
        for data in TEACHERS_DATA:
            u = User.objects.create_user(username=data['user']['username'], password=data['teacher']['personal_id'], first_name=data['user']['first_name'], last_name=data['user']['last_name'], email=f"{data['user']['username']}@cujae.edu.cu")
            teacher = Teacher.objects.create(
                user=u, personal_id=data['teacher']['personal_id'], department=data['teacher']['department'], is_blacklisted=data['teacher']['is_blacklisted']
            )
            teachers.append(teacher)
            
        for _ in range(13):
            fname = random.choice(NOMBRES)
            lname = random.choice(APELLIDOS)
            username = f"prof.{clean_text(fname)}.{clean_text(lname)}{random.randint(1,99)}"
            ci = generar_ci_valido(1965, 1990)
            u = User.objects.create_user(username=username, password=ci, first_name=fname, last_name=lname)
            teacher = Teacher.objects.create(
                user=u, personal_id=ci, department=random.choice(DEPARTMENTS), is_blacklisted=random.random() < 0.05
            )
            teachers.append(teacher)

        # ==========================================
        # FASE 4: PRÉSTAMOS HISTÓRICOS 
        # ==========================================
        self.stdout.write("📈 Generando historial de préstamos (Update bypass)...")
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=5) 
        
        stock_virtual = {book.id: book.total_stock for book in books}
        
        # A. Casos lista negra
        pedro = students[3] # el.moroso
        pedro.is_blacklisted = False; pedro.save()
        l1 = Loan.objects.create(book=books[0], student=pedro, status='ACTIVE', expected_return_date=tomorrow)
        Loan.objects.filter(pk=l1.pk).update(loan_date=today - datetime.timedelta(days=150), expected_return_date=today - datetime.timedelta(days=120), status='OVERDUE')
        stock_virtual[books[0].id] -= 1
        pedro.is_blacklisted = True; pedro.save()

        marta = students[4] # deudora.pro
        marta.is_blacklisted = False; marta.save()
        l2 = Loan.objects.create(book=books[5], student=marta, status='ACTIVE', expected_return_date=tomorrow)
        Loan.objects.filter(pk=l2.pk).update(loan_date=today - datetime.timedelta(days=90), expected_return_date=today - datetime.timedelta(days=75), status='OVERDUE')
        stock_virtual[books[5].id] -= 1
        marta.is_blacklisted = True; marta.save()

        # B. Rellenar gráficos
        lectores_sanos = [s for s in students if not s.is_blacklisted] + [t for t in teachers if not t.is_blacklisted]
        prestamos_a_insertar = []

        for _ in range(250):
            lector = random.choice(lectores_sanos)
            book = random.choice(books)
            
            dias_atras = random.randint(1, 360)
            fecha_prestamo = today - datetime.timedelta(days=dias_atras)
            fecha_esperada = fecha_prestamo + datetime.timedelta(days=15)
            
            if dias_atras > 20: 
                status = 'RETURNED' if random.random() < 0.95 else 'OVERDUE'
            else:
                status = 'ACTIVE' if random.random() < 0.70 else 'RETURNED'

            if status in ['ACTIVE', 'OVERDUE']:
                if stock_virtual[book.id] > 0:
                    stock_virtual[book.id] -= 1
                else:
                    status = 'RETURNED'

            fecha_real = None
            if status == 'RETURNED':
                fecha_real = fecha_prestamo + datetime.timedelta(days=random.randint(1, dias_atras))

            loan = Loan.objects.create(
                book=book,
                student=lector if isinstance(lector, Student) else None,
                teacher=lector if isinstance(lector, Teacher) else None,
                status='ACTIVE', # Se crea activo para pasar el clean()
                expected_return_date=tomorrow
            )
            
            Loan.objects.filter(pk=loan.pk).update(
                loan_date=fecha_prestamo,
                expected_return_date=fecha_esperada,
                actual_return_date=fecha_real,
                status=status
            )

        self.stdout.write(self.style.SUCCESS("✅ ¡SISTEMA POBLADO CON ÉXITO!"))
        self.stdout.write(self.style.WARNING("====================================="))
        self.stdout.write(self.style.WARNING("  Administrador de sistemas: admin.sys / password123"))
        self.stdout.write(self.style.WARNING("  Bibliotecarios: biblio1 / password123"))
        self.stdout.write(self.style.WARNING("  Estudiantes y Profesores / Pass: SU CI"))
        self.stdout.write(self.style.WARNING("====================================="))