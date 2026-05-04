"""
Capa de servicios de la app library.

Este módulo centraliza toda la lógica de negocio de alto nivel (casos de uso).
Las vistas del admin, el frontend, y cualquier otro consumidor deben llamar
a estas funciones en lugar de manipular los modelos directamente.

Ventajas:
- Evita duplicar lógica entre el admin y el frontend.
- Garantiza que el AuditLog siempre se escriba junto a cada acción importante.
- Facilita el testing, ya que la lógica está separada de la interfaz.
"""

from datetime import date

from django.utils import timezone

from .models import AuditLog, Book, Loan, Student


def _write_audit_log(actor_user: str, action: str, ip_address: str) -> None:
    """
    Función interna auxiliar que escribe un registro en el AuditLog.

    No se llama directamente desde fuera — la usan create_loan,
    return_loan y el comando mark_overdue_loans.

    Args:
        actor_user: Nombre de usuario o identificador de quien ejecuta la acción.
        action:     Descripción textual de la acción realizada.
        ip_address: Dirección IP desde donde se realizó la acción.
    """
    AuditLog.objects.create(
        user_actor=actor_user,
        action=action,
        ip_address=ip_address,
    )


def create_loan(
    book: Book,
    student: Student,
    expected_return_date: date,
    actor_user: str,
    actor_ip: str,
) -> Loan:
    """
    Registra un nuevo préstamo en el sistema.

    Las reglas de negocio (stock disponible, lista negra del estudiante,
    validez de la fecha) son verificadas automáticamente por el método
    clean() del modelo Loan al llamar a save(), que invoca full_clean().

    Si alguna regla falla, se lanza un ValidationError y el préstamo
    NO se crea ni se escribe en el AuditLog.

    Args:
        book:                 Instancia del libro a prestar.
        student:              Instancia del estudiante que recibe el préstamo.
        expected_return_date: Fecha límite acordada para la devolución.
        actor_user:           Nombre del bibliotecario que registra el préstamo.
        actor_ip:             IP desde la que se realiza la operación.

    Returns:
        La instancia del Loan recién creada.

    Raises:
        ValidationError: Si no hay stock, el estudiante está en lista negra,
                         o la fecha de devolución no es válida.
    """
    loan = Loan(
        book=book,
        student=student,
        expected_return_date=expected_return_date,
    )
    # save() llama internamente a full_clean() → clean(), donde viven
    # las reglas de negocio. Si algo falla, la excepción se propaga
    # aquí y el préstamo nunca se guarda.
    loan.save()

    _write_audit_log(
        actor_user=actor_user,
        action=(
            f"Registró préstamo del libro '{book.title}' "
            f"para el estudiante {student.personal_id} "
            f"(devolución esperada: {expected_return_date})."
        ),
        ip_address=actor_ip,
    )

    return loan


def return_loan(
    loan: Loan,
    actor_user: str,
    actor_ip: str,
) -> Loan:
    """
    Registra la devolución de un préstamo activo.

    Cambia el estado del préstamo a RETURNED y registra la fecha
    real de devolución. Al cambiar el estado, el libro queda disponible
    automáticamente (available_stock es calculado dinámicamente contando
    solo los préstamos ACTIVE).

    Args:
        loan:       Instancia del préstamo que se está devolviendo.
        actor_user: Nombre del bibliotecario que registra la devolución.
        actor_ip:   IP desde la que se realiza la operación.

    Returns:
        La instancia del Loan actualizada.

    Raises:
        ValueError: Si el préstamo ya fue devuelto anteriormente.
    """
    if loan.status == Loan.LoanStatus.RETURNED:
        raise ValueError(
            f"El préstamo #{loan.pk} ya fue devuelto anteriormente. "
            "No se puede procesar una devolución duplicada."
        )

    loan.status = Loan.LoanStatus.RETURNED
    loan.actual_return_date = date.today()
    # Usamos update_fields para actualizar solo los campos necesarios,
    # evitando que full_clean() vuelva a validar la fecha de devolución
    # (que ya pasó) como si fuera una creación nueva.
    loan.save(update_fields=['status', 'actual_return_date'])

    _write_audit_log(
        actor_user=actor_user,
        action=(
            f"Registró devolución del libro '{loan.book.title}' "
            f"por el estudiante {loan.student.personal_id}."
        ),
        ip_address=actor_ip,
    )

    return loan
