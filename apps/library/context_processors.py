def student_profile(request):
    """
    Inyecta el perfil del estudiante o profesor en todos los templates.
    """
    student_profile = None
    teacher_profile = None
    if request.user.is_authenticated:
        student_profile = getattr(request.user, 'student_profile', None)
        teacher_profile = getattr(request.user, 'teacher_profile', None)
    return {
        'student_profile': student_profile,
        'teacher_profile': teacher_profile,
    }