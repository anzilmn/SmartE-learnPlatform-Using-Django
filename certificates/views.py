from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from courses.models import Course, Enrollment, Certificate # Make sure these are imported
from .utils import generate_certificate_pdf
import uuid

@login_required
def download_certificate(request, course_id): # Use course_id for better lookups
    course = get_object_or_404(Course, id=course_id)
    
    # 1. AUTH CHECK: Only 'finished' students get the prize
    enrollment = Enrollment.objects.filter(
        user=request.user, 
        course=course, 
        status='finished'
    ).first()

    if not enrollment:
        messages.error(request, "Vro, you haven't finished this course yet! 🎓")
        return redirect('course_detail', course_id=course.id)

    # 2. CERTIFICATE DATA: Get or create the unique ID
    cert, created = Certificate.objects.get_or_create(
        user=request.user, 
        course=course,
        defaults={'certificate_id': str(uuid.uuid4())[:12].upper()}
    )

    # 3. PREP DATA
    student_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    date_str = cert.issued_at.strftime('%d-%m-%Y')
    
    # 🔥 VRO FIX: Passing ALL 4 required arguments now
    pdf_buffer = generate_certificate_pdf(
        student_name, 
        course.title, 
        date_str, 
        cert.certificate_id
    )
    
    # 4. SHIP IT
    filename = f'Certificate_{course.title.replace(" ", "_")}.pdf'
    return FileResponse(pdf_buffer, as_attachment=True, filename=filename)