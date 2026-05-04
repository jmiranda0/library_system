from datetime import date

from django.core.management.base import BaseCommand

from apps.library.models import AuditLog, Loan

# IP usada cuando la acción la ejecuta el servidor (no un usuario humano).
# '0.0.0.0' es la convención para indicar "origen del sistema/proceso interno".
SYSTEM_IP = '0.0.0.0'
SYSTEM_ACTOR = 'sistema'


class Command(BaseCommand):
    help = 'Marca como VENCIDOS todos los préstamos activos cuya fecha de devolución ya pasó.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ip',
            type=str,
            default=SYSTEM_IP,
            help=(
                'Dirección IP a registrar en el AuditLog como origen de este comando. '
                f'Por defecto es {SYSTEM_IP} (proceso del sistema). '
                'Se puede sobreescribir en producción con la IP real del servidor si se desea.'
            ),
        )

    def handle(self, *args, **options):
        today = date.today()
        server_ip = options['ip']

        self.stdout.write(f"Buscando préstamos vencidos (fecha límite anterior a {today})...")

        # Filtramos los préstamos que siguen ACTIVOS pero ya pasaron su fecha límite
        overdue_loans = Loan.objects.filter(
            status=Loan.LoanStatus.ACTIVE,
            expected_return_date__lt=today,
        )

        count = overdue_loans.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No hay préstamos vencidos. Todo está al día."))
            return

        # Actualizamos todos de golpe con un solo query SQL (más eficiente que un loop)
        overdue_loans.update(status=Loan.LoanStatus.OVERDUE)

        # Escribimos un único resumen en el AuditLog para toda la operación
        AuditLog.objects.create(
            user_actor=SYSTEM_ACTOR,
            action=(
                f"Tarea automática: marcó {count} préstamo(s) como VENCIDO(S) "
                f"con fecha límite anterior a {today}."
            ),
            ip_address=server_ip,
        )

        self.stdout.write(
            self.style.SUCCESS(f"✓ {count} préstamo(s) marcados como VENCIDOS correctamente.")
        )
