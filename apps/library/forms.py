from django import forms
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import transaction

from unfold.widgets import UnfoldAdminTextInputWidget, UnfoldAdminPasswordWidget, UnfoldAdminEmailInputWidget
from .models import Librarian, Student, Teacher, Administrator


class StudentAdminForm(forms.ModelForm):
    """
    Formulario personalizado para la creación y edición de Estudiantes en el Admin.
    Permite gestionar los datos del User (username, password, nombre) y del Student simultáneamente.
    """
    # Campos del modelo User con widgets de Unfold para consistencia visual
    username = forms.CharField(
        max_length=150, 
        label='Nombre de Usuario', 
        required=False,
        widget=UnfoldAdminTextInputWidget,
        help_text='Se generará automáticamente (ej. juan.perez) si se deja en blanco.'
    )
    first_name = forms.CharField(
        max_length=150, 
        label='Nombre', 
        required=True,
        widget=UnfoldAdminTextInputWidget
    )
    last_name = forms.CharField(
        max_length=150, 
        label='Apellidos', 
        required=True,
        widget=UnfoldAdminTextInputWidget
    )
    email = forms.EmailField(
        label='Correo Electrónico', 
        required=False, 
        widget=UnfoldAdminEmailInputWidget,
        help_text='Se generará un correo por defecto si se deja en blanco.'
    )
    password = forms.CharField(
        widget=UnfoldAdminPasswordWidget,
        required=False,
        label='Contraseña',
        help_text='Se asignará el Carné de Identidad como contraseña si se deja en blanco.'
    )

    class Meta:
        model = Student
        # NO incluimos 'user' porque lo manejamos nosotros por detrás
        fields = ['personal_id', 'academic_year', 'is_blacklisted']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si estamos editando un estudiante existente, precargamos los datos de su usuario
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['password'].required = False

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        # Generar username automáticamente si está en blanco
        if not username and first_name and last_name:
            import unicodedata
            
            # Limpiar acentos y pasar a minúsculas
            def clean_text(text):
                text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
                return text.lower().split()[0]
                
            base_username = f"{clean_text(first_name)}.{clean_text(last_name)}"
            final_username = base_username
            counter = 1
            
            # Asegurar unicidad
            query = User.objects.all()
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.user.pk)
                
            while query.filter(username=final_username).exists():
                final_username = f"{base_username}{counter}"
                counter += 1
                
            cleaned_data['username'] = final_username
            
        # Generar correo por defecto si está en blanco
        if not cleaned_data.get('email') and cleaned_data.get('username'):
            cleaned_data['email'] = f"{cleaned_data['username']}@biblioteca.edu"
            
        # Validar username manual si se introdujo uno
        if username:
            query = User.objects.filter(username=username)
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.user.pk)
            if query.exists():
                self.add_error('username', "Ya existe un usuario con este nombre.")
                
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        student = super().save(commit=False)
        username = self.cleaned_data.get('username')
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if not student.pk:
            # Es un estudiante nuevo
            user = User(username=username, first_name=first_name, last_name=last_name, email=email)
            # Usar el CI como contraseña por defecto si no se proporcionó una
            if not password:
                password = self.cleaned_data.get('personal_id')
            user.set_password(password)
            user.save()
            # Asignar grupo automáticamente
            grupo, _ = Group.objects.get_or_create(name='Estudiantes')
            user.groups.add(grupo)
            student.user = user
        else:
            # Editando estudiante existente
            user = student.user
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            if password:
                user.set_password(password)
            user.save()

        if commit:
            student.save()
            self.save_m2m()
        return student


class LibrarianAdminForm(forms.ModelForm):
    """
    Formulario para Bibliotecarios y Supervisores.
    Genera username, email y contraseña automáticamente si se dejan en blanco.
    Al editar, los datos de autenticación son solo lectura.
    """
    username = forms.CharField(
        max_length=150,
        label='Nombre de Usuario',
        required=False,
        widget=UnfoldAdminTextInputWidget,
        help_text='Se generará automáticamente (ej. marta.rodriguez) si se deja en blanco.'
    )
    first_name = forms.CharField(
        max_length=150,
        label='Nombre',
        required=True,
        widget=UnfoldAdminTextInputWidget
    )
    last_name = forms.CharField(
        max_length=150,
        label='Apellidos',
        required=True,
        widget=UnfoldAdminTextInputWidget
    )
    password = forms.CharField(
        widget=UnfoldAdminPasswordWidget,
        required=False,
        label='Contraseña',
        help_text='La contraseña por defecto será "biblioteca123" si se deja en blanco.'
    )

    class Meta:
        model = Librarian
        fields = ['is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.username
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            # Al editar, username no se puede cambiar
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['username'].help_text = 'El nombre de usuario no puede modificarse.'
            # Ocultar contraseña al editar
            self.fields['password'].widget = forms.HiddenInput()
            self.fields['password'].required = False

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        if not username and first_name and last_name:
            import unicodedata
            def clean_text(text):
                text = ''.join(
                    c for c in unicodedata.normalize('NFD', text)
                    if unicodedata.category(c) != 'Mn'
                )
                return text.lower().split()[0]

            base_username = f"{clean_text(first_name)}.{clean_text(last_name)}"
            final_username = base_username
            counter = 1
            query = User.objects.all()
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)

            while query.filter(username=final_username).exists():
                final_username = f"{base_username}{counter}"
                counter += 1
            cleaned_data['username'] = final_username

        # Generar email institucional si se dejó en blanco
        if not cleaned_data.get('email') and cleaned_data.get('username'):
            cleaned_data['email'] = f"{cleaned_data['username']}@biblioteca.cujae.edu.cu"

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        username = self.cleaned_data.get('username')
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        password = self.cleaned_data.get('password')

        user.username = username
        user.first_name = first_name
        user.last_name = last_name

        if not user.pk:
            # Solo al crear: asignar email y contraseña
            user.email = f"{username}@biblioteca.cujae.edu.cu"
            user.is_staff = True
            if not password:
                password = "biblioteca123"
            user.set_password(password)

        if commit:
            user.save()
            grupo, _ = Group.objects.get_or_create(name='Bibliotecarios')
            user.groups.add(grupo)
            self.save_m2m()
        return user
    
class SystemAdminForm(forms.ModelForm):
    """
    Formulario para Administradores del Sistema.
    Crea usuarios con acceso técnico, pero SIN acceso al negocio (No Superuser).
    """
    username = forms.CharField(max_length=150, label='Nombre de Usuario', required=False, widget=UnfoldAdminTextInputWidget)
    first_name = forms.CharField(max_length=150, label='Nombre', required=True, widget=UnfoldAdminTextInputWidget)
    last_name = forms.CharField(max_length=150, label='Apellidos', required=True, widget=UnfoldAdminTextInputWidget)
    password = forms.CharField(widget=UnfoldAdminPasswordWidget, required=False, label='Contraseña', help_text='Por defecto será: admin123')

    class Meta:
        model = Administrator
        fields = ['is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.username
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['password'].widget = forms.HiddenInput()
            self.fields['password'].required = False

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        if not username and first_name and last_name:
            import unicodedata
            def clean_text(text):
                return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower().split()[0]
            
            # Formato moderno y limpio: admin.nombre.apellido
            base_username = f"admin.{clean_text(first_name)}.{clean_text(last_name)}"
            final_username = base_username
            counter = 1
            query = User.objects.all()
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)

            while query.filter(username=final_username).exists():
                final_username = f"{base_username}{counter}"
                counter += 1
                
            cleaned_data['username'] = final_username

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get('username')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')

        if not user.pk:
            user.email = f"{user.username}@cujae.edu.cu"
            user.is_staff = True
            user.is_superuser = False
            user.set_password(self.cleaned_data.get('password') or "admin123")

        if commit:
            user.save()
            grupo, _ = Group.objects.get_or_create(name='Administradores')
            user.groups.add(grupo)
            self.save_m2m()
        return user
    
class TeacherAdminForm(forms.ModelForm):
    """
    Formulario para la creación y edición de Profesores.
    Mismo comportamiento que StudentAdminForm pero sin carrera ni año académico.
    """
    username = forms.CharField(
        max_length=150,
        label='Nombre de Usuario',
        required=False,
        widget=UnfoldAdminTextInputWidget,
        help_text='Se generará automáticamente si se deja en blanco.'
    )
    first_name = forms.CharField(
        max_length=150,
        label='Nombre',
        required=True,
        widget=UnfoldAdminTextInputWidget
    )
    last_name = forms.CharField(
        max_length=150,
        label='Apellidos',
        required=True,
        widget=UnfoldAdminTextInputWidget
    )
    password = forms.CharField(
        widget=UnfoldAdminPasswordWidget,
        required=False,
        label='Contraseña',
        help_text='Se asignará el Carné de Identidad como contraseña si se deja en blanco.'
    )

    class Meta:
        model = Teacher
        fields = ['personal_id', 'department', 'is_blacklisted']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['password'].required = False

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        if not username and first_name and last_name:
            import unicodedata
            def clean_text(text):
                text = ''.join(
                    c for c in unicodedata.normalize('NFD', text)
                    if unicodedata.category(c) != 'Mn'
                )
                return text.lower().split()[0]

            base_username = f"{clean_text(first_name)}.{clean_text(last_name)}"
            final_username = base_username
            counter = 1
            query = User.objects.all()
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.user.pk)

            while query.filter(username=final_username).exists():
                final_username = f"{base_username}{counter}"
                counter += 1
            cleaned_data['username'] = final_username

        if not cleaned_data.get('email') and cleaned_data.get('username'):
            cleaned_data['email'] = f"{cleaned_data['username']}@biblioteca.edu"

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        teacher = super().save(commit=False)
        username = self.cleaned_data.get('username')
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        email = self.cleaned_data.get('email', '')
        password = self.cleaned_data.get('password')

        if not teacher.pk:
            user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            if not password:
                password = self.cleaned_data.get('personal_id')
            user.set_password(password)
            user.save()
            grupo, _ = Group.objects.get_or_create(name='Profesores')
            user.groups.add(grupo)
            teacher.user = user
        else:
            user = teacher.user
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            if password:
                user.set_password(password)
            user.save()

        if commit:
            teacher.save()
            self.save_m2m()
        return teacher