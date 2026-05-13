from django import forms
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Librarian, Student


class StudentAdminForm(forms.ModelForm):
    """
    Formulario personalizado para la creación y edición de Estudiantes en el Admin.
    Permite gestionar los datos del User (username, password, nombre) y del Student simultáneamente.
    """
    # Campos del modelo User
    username = forms.CharField(
        max_length=150, 
        label='Nombre de Usuario', 
        required=False,
        help_text='Se generará automáticamente (ej. juan.perez) si se deja en blanco.'
    )
    first_name = forms.CharField(max_length=150, label='Nombre', required=True)
    last_name = forms.CharField(max_length=150, label='Apellidos', required=True)
    email = forms.EmailField(label='Correo Electrónico', required=False, help_text='Se generará un correo por defecto si se deja en blanco.')
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='Contraseña',
        help_text='Se asignará el Carné de Identidad como contraseña si se deja en blanco.'
    )

    class Meta:
        model = Student
        # NO incluimos 'user' porque lo manejamos nosotros por detrás
        fields = ['personal_id', 'career', 'academic_year', 'is_blacklisted']

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
    Formulario personalizado para la creación y edición de Bibliotecarios.
    Asigna is_staff=True y el grupo 'Bibliotecarios' automáticamente de forma transparente.
    """
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='Contraseña',
        help_text='Déjalo en blanco para no cambiarla. Obligatorio para nuevos bibliotecarios.'
    )

    class Meta:
        model = Librarian
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not (self.instance and self.instance.pk):
            self.fields['password'].required = True

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
            self.save_m2m()
        return user
