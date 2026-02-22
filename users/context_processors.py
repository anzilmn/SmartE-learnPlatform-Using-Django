from courses.models import Profile

def pending_teacher_count(request):
    if request.user.is_authenticated and request.user.is_superuser:
        count = Profile.objects.filter(
            is_teacher_applicant=True, 
            application_status='pending'
        ).count()
        return {'pending_teachers_count': count}
    return {'pending_teachers_count': 0}