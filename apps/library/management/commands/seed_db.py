import random
import datetime
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from apps.library.models import Book, Student, Teacher, Loan

# ==========================================
# 1. DICCIONARIOS DE DATOS BASE
# ==========================================

CUJAE_CAREERS = [
    "Ingeniería Informática", "Ingeniería Civil", "Arquitectura", 
    "Ingeniería Industrial", "Ingeniería Automática", "Ingeniería Mecánica", 
    "Ingeniería Eléctrica", "Ingeniería Química", "Ing. de Telecomunicaciones"
]

DEPARTMENTS = [
    "Ciencias de la Computación", "Matemática Aplicada", "Física", 
    "Estructuras", "Sistemas Eléctricos", "Humanidades", "Termodinámica"
]

NOMBRES = ["Carlos", "Ana", "Luis", "Marta", "Jorge", "Elena", "Pedro", "Sofia", "Juan", "Laura", "Miguel", "Carmen", "David", "Lucia", "Raul", "Paula", "Jose", "Diana", "Alejandro", "Valeria"]
APELLIDOS = ["Perez", "Gomez", "Martinez", "Rodriguez", "Fernandez", "Lopez", "Diaz", "Torres", "Ruiz", "Alonso", "Hernandez", "Garcia", "Cruz", "Reyes", "Morales", "Ortiz"]

BOOKS_DATA = [
    {"title": "Clean Code", "author": "Robert C. Martin", "total_stock": 15, "synopsis": "Manual de ingeniería de software sobre código limpio, refactorización y mantenibilidad. Aborda principios como nombres significativos, funciones pequeñas, manejo de errores y pruebas unitarias."},
    {"title": "Design Patterns", "author": "Erich Gamma et al.", "total_stock": 10, "synopsis": "Los 23 patrones de diseño orientados a objetos clásicos. Incluye patrones creacionales, estructurales y de comportamiento con ejemplos aplicados al desarrollo de software empresarial."},
    {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "total_stock": 12, "synopsis": "El texto definitivo sobre estructuras de datos y análisis de complejidad de algoritmos. Cubre ordenamiento, árboles, grafos y programación dinámica."},
    {"title": "Artificial Intelligence: A Modern Approach", "author": "Stuart Russell", "total_stock": 8, "synopsis": "Libro de texto base para IA. Aborda búsqueda lógica, aprendizaje automático, procesamiento de lenguaje natural y robótica."},
    {"title": "Computer Networks", "author": "Andrew S. Tanenbaum", "total_stock": 14, "synopsis": "Explicación detallada de la arquitectura de redes, abarcando desde la capa física hasta la capa de aplicación en los modelos OSI y TCP/IP."},
    {"title": "Database System Concepts", "author": "Abraham Silberschatz", "total_stock": 10, "synopsis": "Teoría de bases de datos relacionales, normalización, transacciones ACID, control de concurrencia y arquitecturas NoSQL."},
    {"title": "Ingeniería de Software", "author": "Ian Sommerville", "total_stock": 15, "synopsis": "Guía completa de procesos de desarrollo, requisitos, arquitectura, validación y evolución de sistemas críticos."},
    {"title": "Mecánica de Materiales", "author": "R.C. Hibbeler", "total_stock": 12, "synopsis": "Estudio analítico de esfuerzos, deformaciones y torsión en elementos estructurales, fundamental para ingeniería civil y mecánica."},
    {"title": "Cálculo de una variable", "author": "James Stewart", "total_stock": 20, "synopsis": "Conceptos de límites, derivadas, integrales y sus aplicaciones en física e ingeniería."},
    {"title": "Física Universitaria", "author": "Sears y Zemansky", "total_stock": 18, "synopsis": "Mecánica clásica, electromagnetismo, óptica y termodinámica con enfoque matemático avanzado."},
    {"title": "Saber ver la arquitectura", "author": "Bruno Zevi", "total_stock": 6, "synopsis": "Ensayo sobre la percepción espacial, urbanismo y la comprensión estética de los espacios arquitectónicos."},
    {"title": "Investigación de Operaciones", "author": "Hamdy A. Taha", "total_stock": 10, "synopsis": "Modelado matemático, programación lineal, teoría de colas e inventarios para la optimización de procesos industriales."},
    {"title": "Cien Años de Soledad", "author": "Gabriel García Márquez", "total_stock": 25, "synopsis": "Realismo mágico en Macondo. La estirpe de los Buendía y su destino trágico y solitario."},
    {"title": "1984", "author": "George Orwell", "total_stock": 20, "synopsis": "Distopía sobre el Gran Hermano, la vigilancia totalitaria y la manipulación de la verdad en Oceanía."},
    {"title": "Sapiens: De animales a dioses", "author": "Yuval Noah Harari", "total_stock": 15, "synopsis": "Historia de la humanidad desde la prehistoria hasta el futuro tecnológico y la revolución cognitiva."}
]

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
    help = 'Puebla la base de datos masivamente para el Dashboard.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("⏳ Borrando la base de datos completa..."))
        Loan.objects.all().delete()
        Student.objects.all().delete()
        Teacher.objects.all().delete()
        Book.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        # ==========================================
        # FASE 1: ROLES
        # ==========================================
        self.stdout.write("🛡️ Configurando Grupos y Personal...")
        g_admin, _ = Group.objects.get_or_create(name='Administradores')
        g_bib, _ = Group.objects.get_or_create(name='Bibliotecarios')

        admin_sys = User.objects.create_user(username='admin.it', password='password123', first_name='Soporte', last_name='Técnico', is_staff=True)
        admin_sys.groups.add(g_admin)

        for i in range(1, 4):
            bib = User.objects.create_user(username=f'biblio{i}', password='password123', first_name=f'Biblio{i}', last_name='Staff', is_staff=True)
            bib.groups.add(g_bib)

        # ==========================================
        # FASE 2: LIBROS
        # ==========================================
        self.stdout.write("📚 Insertando Catálogo de Libros...")
        books = []
        for data in BOOKS_DATA:
            data['ai_recommendations_count'] = random.randint(5, 80)
            books.append(Book.objects.create(**data))

        # ==========================================
        # FASE 3: ESTUDIANTES (CARRERAS VARIADAS)
        # ==========================================
        self.stdout.write("🎓 Matriculando 50 estudiantes de la CUJAE...")
        students = []
        for _ in range(50):
            fname = random.choice(NOMBRES)
            lname = random.choice(APELLIDOS)
            username = f"{clean_text(fname)}.{clean_text(lname)}{random.randint(1,99)}"
            ci = generar_ci_valido(1998, 2005)
            
            u = User.objects.create_user(username=username, password=ci, first_name=fname, last_name=lname, email=f"{username}@cujae.edu.cu")
            
            # CREADOS DIRECTAMENTE EN EL MODELO PARA EVITAR EL FORMULARIO
            student = Student.objects.create(
                user=u,
                personal_id=ci,
                career=random.choice(CUJAE_CAREERS),  # ¡Ahora sí tendrán carreras distintas!
                academic_year=random.randint(1, 5),
                is_blacklisted=random.random() < 0.10
            )
            students.append(student)

        # ==========================================
        # FASE 4: PROFESORES
        # ==========================================
        self.stdout.write("👨‍🏫 Contratando Profesores...")
        teachers = []
        for _ in range(15):
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
        # FASE 5: PRÉSTAMOS CON BULK_CREATE (BYPASS DE REGLAS)
        # ==========================================
        self.stdout.write("📈 Generando 350 préstamos históricos...")
        today = datetime.date.today()
        lectores = students + teachers
        
        # Diccionario para llevar el control del stock físico nosotros mismos
        stock_virtual = {book.id: book.total_stock for book in books}
        prestamos_a_insertar = []

        for _ in range(350):
            lector = random.choice(lectores)
            book = random.choice(books)
            
            dias_atras = random.randint(1, 360)
            fecha_prestamo = today - datetime.timedelta(days=dias_atras)
            fecha_esperada = fecha_prestamo + datetime.timedelta(days=15)
            
            # Lógica de probabilidad
            if dias_atras > 20: 
                if random.random() < 0.90:
                    status = 'RETURNED'
                    fecha_real = fecha_prestamo + datetime.timedelta(days=random.randint(5, 15))
                else:
                    status = 'OVERDUE'
                    fecha_real = None
            else:
                if random.random() < 0.70:
                    status = 'ACTIVE'
                    fecha_real = None
                else:
                    status = 'RETURNED'
                    fecha_real = fecha_prestamo + datetime.timedelta(days=random.randint(1, dias_atras))

            # Verificar si hay stock antes de crear un ACTIVO o MORA
            if status in ['ACTIVE', 'OVERDUE']:
                if stock_virtual[book.id] > 0:
                    stock_virtual[book.id] -= 1
                else:
                    # Si no hay stock, forzamos a que el préstamo sea DEVUELTO históricamente
                    status = 'RETURNED'
                    fecha_real = fecha_prestamo + datetime.timedelta(days=10)

            # Instanciamos el modelo SIN usar .create() ni .save() para evitar el clean()
            loan = Loan(
                book=book,
                status=status,
                loan_date=fecha_prestamo,
                expected_return_date=fecha_esperada,
                actual_return_date=fecha_real
            )
            
            if isinstance(lector, Student):
                loan.student = lector
            else:
                loan.teacher = lector
                
            prestamos_a_insertar.append(loan)

        # ¡EL TRUCO DE MAGIA! Inserción directa en SQL saltando validaciones de Django
        Loan.objects.bulk_create(prestamos_a_insertar)

        self.stdout.write(self.style.SUCCESS("✅ ¡SISTEMA POBLADO CON ÉXITO!"))
        self.stdout.write(self.style.WARNING("====================================="))
        self.stdout.write(self.style.WARNING("  Admin IT: admin.it / password123"))
        self.stdout.write(self.style.WARNING("  Bibliotecarios: biblio1 / password123"))
        self.stdout.write(self.style.WARNING("  Lectores (Login): USERNAME o CI y contraseña CI"))
        self.stdout.write(self.style.WARNING("====================================="))