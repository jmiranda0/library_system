from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# Definimos qué permisos base (CRUD) queremos por cada modelo para cada grupo.
# 'view' = ver, 'add' = crear, 'change' = editar, 'delete' = borrar
GROUPS_PERMISSIONS = {
    'Bibliotecarios': {
        'book': ['view', 'add', 'change', 'delete'],
        'student': ['view', 'add', 'change'],
        'loan': ['view', 'add', 'change'],
        'auditlog': ['view'],
    },
    'Estudiantes': {
        'book': ['view'],
        'loan': ['view'],
    }
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

            for model_name, actions in models_perms.items():
                for action in actions:
                    # El formato interno de Django para los codenames de permisos es: action_modelname
                    # Ej: view_book, add_loan
                    codename = f"{action}_{model_name}"
                    try:
                        permission = Permission.objects.get(codename=codename)
                        group.permissions.add(permission)
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Permiso no encontrado: {codename}"))

            self.stdout.write(self.style.SUCCESS(f"Permisos asignados al grupo '{group_name}'."))

        self.stdout.write(self.style.SUCCESS("¡Configuración de grupos completada con éxito!"))
