from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

GROUPS_PERMISSIONS = {
    'Bibliotecarios': {
        'book':     ['view', 'add', 'change', 'delete'],
        'student':  ['view', 'change'],  # no add ni delete
        'teacher':  ['view', 'change'],
        'loan':     ['view', 'add', 'change'],
    },
    'Administradores': {
        'user':      ['view', 'add', 'change'],
        'group':    ['view', 'add', 'change', 'delete'],
        'student':   ['view', 'add', 'change', 'delete'],
        'teacher':   ['view', 'add', 'change', 'delete'],
        'librarian': ['view', 'add', 'change', 'delete'],
        'administrator': ['view', 'add', 'change'],
        'auditlog':  ['view'],
    },
    'Estudiantes': {
        'book': ['view'],
        'loan': ['view'],
    },
    'Profesores': {
        'book': ['view'],
        'loan': ['view'],
},
}


class Command(BaseCommand):
    help = 'Crea los grupos por defecto y les asigna permisos.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Configurando grupos y permisos...")

        for group_name, models_perms in GROUPS_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Grupo '{group_name}' creado."))
            else:
                self.stdout.write(f"Grupo '{group_name}' ya existe.")
                group.permissions.clear()  # Limpia permisos viejos antes de reasignar

            for model_name, actions in models_perms.items():
                for action in actions:
                    codename = f"{action}_{model_name}"
                    try:
                        permission = Permission.objects.get(codename=codename)
                        group.permissions.add(permission)
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f"Permiso no encontrado: {codename}")
                        )

            self.stdout.write(
                self.style.SUCCESS(f"Permisos asignados al grupo '{group_name}'.")
            )

        self.stdout.write(self.style.SUCCESS("¡Configuración de grupos completada!"))