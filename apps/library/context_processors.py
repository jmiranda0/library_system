def student_profile(request):
    """
    Inyecta el perfil del estudiante en todos los templates.
    Evita errores de atributo cuando el usuario no tiene perfil de estudiante.
    """
    profile = None
    if request.user.is_authenticated:
        profile = getattr(request.user, 'student_profile', None)
    return {'student_profile': profile}