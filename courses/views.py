import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import HttpResponse, FileResponse
from django.urls import reverse
from django.utils import timezone

# PDF Generation
from reportlab.pdfgen import canvas
from certificates.utils import generate_certificate_pdf 

# Models
from django.contrib.auth.models import User
from .models import (
    Course, Lesson, LessonProgress, Enrollment, Review, 
    Comment, Note, Certificate, LessonCompletion, SupportTicket, Notification
)
from .forms import UserUpdateForm, ProfileUpdateForm

# --- 1. COURSE DISCOVERY ---
from django.db.models import Avg, Count, Q
from django.shortcuts import render
from .models import Course
from django.db.models import Avg, Count, Q
from django.shortcuts import render
from .models import Course, Certificate
from django.shortcuts import render
from django.db.models import Q, Avg, Count
from .models import Course, Certificate, Review # Make sure Review is imported!
from django.shortcuts import render
from django.db.models import Avg, Count, Q
from django.contrib.auth.models import User
from .models import Course, Review, Certificate

from django.shortcuts import render
from django.db.models import Q, Avg, Count
from .models import Course, Certificate, Review
from django.contrib.auth.models import User

from django.db.models import Avg, Count, Q
from .models import Course, Certificate, Review, Wishlist # Added Wishlist if needed
from django.contrib.auth.models import User
from django.shortcuts import render

from django.db.models import Avg, Count, Q
from .models import Course, Certificate, Review, Wishlist
from django.contrib.auth.models import User
from django.shortcuts import render

from django.shortcuts import render
from django.db.models import Avg, Count, Q
from django.contrib.auth.models import User
from .models import Course, Certificate, Review, Enrollment  # Ensure Enrollment is imported
from django.db.models import Avg, Count, Q
from courses.models import Course, Enrollment, Certificate, Review, AssessmentSubmission
from django.contrib.auth.models import User



def course_list(request):
    query = request.GET.get('q')
    sort_by = request.GET.get('sort') 
    teacher_id = request.GET.get('teacher') 
    
    # 1. Base Queryset
    courses = Course.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )

    # 2. INSTRUCTOR PRIVACY LOGIC
    if request.user.is_authenticated and request.user.is_staff and not request.user.is_superuser:
        courses = courses.filter(instructor=request.user)

    # 3. SEARCH LOGIC
    if query:
        courses = courses.filter(
            Q(title__icontains=query) | Q(description__icontains=query) 
        )

    # 4. TEACHER FILTER LOGIC
    if teacher_id:
        courses = courses.filter(instructor_id=teacher_id)
    
    # 5. SORTING LOGIC
    if sort_by == 'top_rated':
        courses = courses.order_by('-avg_rating', '-review_count')
    elif sort_by == 'newest':
        courses = courses.order_by('-created_at')
    elif sort_by == 'price_low':
        courses = courses.order_by('price')
    
    # 6. COMPLETED, ENROLLED & PENDING LOGIC
    completed_course_ids = []
    enrolled_course_ids = []
    pending_submissions_count = 0  
    first_pending_course_id = None 

    if request.user.is_authenticated:
        # VRO: Get courses with certificates
        certs = list(Certificate.objects.filter(
            user=request.user
        ).values_list('course_id', flat=True))

        # 🔥 THE VRO FIX: Also get courses where the student UPLOADED the project 🔥
        finished_enrollments = list(Enrollment.objects.filter(
            user=request.user,
            status='finished'
        ).values_list('course_id', flat=True))

        # Combine both! If it has a cert OR status is 'finished', it's COMPLETED
        completed_course_ids = list(set(certs + finished_enrollments))

        # Regular enrolled courses (not finished yet)
        enrolled_course_ids = Enrollment.objects.filter(
            user=request.user,
            status='approved'
        ).values_list('course_id', flat=True)

        # STAFF LOGIC
        if request.user.is_staff:
            pending_subs = AssessmentSubmission.objects.filter(
                assessment__course__instructor=request.user,
                is_reviewed=False
            )
            pending_submissions_count = pending_subs.count()
            
            if pending_submissions_count > 0:
                first_pending_course_id = pending_subs.first().assessment.course.id

    # 7. RECENT REVIEWS LOGIC
    recent_reviews = Review.objects.all().select_related('user', 'course').order_by('-created_at')[:3]
    
    # 8. GET ALL INSTRUCTORS
    instructors = User.objects.filter(is_staff=True).exclude(is_superuser=True)

    # 9. WISHLIST logic
    wishlist_ids = []
    show_badge = False
    if request.user.is_authenticated:
        wishlist_ids = Course.objects.filter(wishlisted_by__user=request.user).values_list('id', flat=True)
        has_items = len(wishlist_ids) > 0
        wishlist_seen = request.session.get('wishlist_seen', False)
        if has_items and not wishlist_seen:
            show_badge = True
        
    return render(request, 'courses/course_list.html', {
        'courses': courses, 
        'query': query,
        'current_sort': sort_by,
        'selected_teacher': teacher_id,
        'instructors': instructors, 
        'completed_course_ids': completed_course_ids,
        'enrolled_course_ids': enrolled_course_ids,
        'recent_reviews': recent_reviews,
        'wishlist_ids': wishlist_ids,
        'show_badge': show_badge,
        'pending_submissions_count': pending_submissions_count,
        'first_pending_course_id': first_pending_course_id,
    })



from django.db.models import Count, Sum
from courses.models import Course
from quizzes.models import Quiz
from django.contrib.auth.decorators import login_required

from django.db.models import Count, Sum
from django.shortcuts import render, get_object_or_404, redirect
from .models import Course, Enrollment, LessonCompletion
from quizzes.models import Quiz
from communications.models import ChatThread # Import your chat thread model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum

# 1. Imports from THIS app (courses)
from .models import Course, Enrollment, LessonCompletion, Assessment  # Added Assessment here

# 2. Imports from OTHER apps
from quizzes.models import Quiz, QuizResult  # Import QuizResult from quizzes app
from communications.models import ChatThread
@login_required
def course_detail(request, course_id):
    # --- FIXED IMPORTS ---
    from quizzes.models import Quiz, QuizResult 
    from .models import AssessmentSubmission, LessonCompletion, Enrollment, Assessment
    try:
        from .models import ChatThread
    except ImportError:
        ChatThread = None
    # ----------------------

    # 1. Fetch Course, Lessons, and Assessment
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all().order_by('order')
    assessment = Assessment.objects.filter(course=course).first() 
    
    # 2. Analytics & Enrollment Status (Vro: Now includes 'finished')
    # This count is for the instructor to see how many people took the course
    all_valid_enrollments = Enrollment.objects.filter(
        course=course, 
        status__in=['approved', 'finished']
    )
    student_count = all_valid_enrollments.count()
    course_price = course.price if course.price else 0
    revenue = student_count * course_price
    
    is_enrolled = False
    is_finished = False # Added this to track if they are graduates
    is_instructor = (course.instructor == request.user)
    completed_lesson_ids = []
    unread_doubts_count = 0
    pending_submissions_count = 0
    quiz_passed = False 
    has_submitted_assessment = False 
    
    # 3. Handle Authenticated User Logic
    if request.user.is_authenticated:
        # 🔥 THE VRO FIX: Check for BOTH approved and finished status 🔥
        user_enrollment = all_valid_enrollments.filter(user=request.user).first()
        
        if user_enrollment or is_instructor:
            is_enrolled = True
            if user_enrollment and user_enrollment.status == 'finished':
                is_finished = True
        
        if is_enrolled:
            completed_lesson_ids = list(LessonCompletion.objects.filter(
                user=request.user, 
                lesson__course=course
            ).values_list('lesson_id', flat=True))

            # 4. Check if Quiz is Passed
            quiz_obj = Quiz.objects.filter(course=course).first()
            if quiz_obj:
                quiz_passed = QuizResult.objects.filter(
                    user=request.user, 
                    quiz=quiz_obj, 
                    passed=True
                ).exists()

            # Check if student already uploaded the project
            if assessment:
                has_submitted_assessment = AssessmentSubmission.objects.filter(
                    user=request.user, 
                    assessment=assessment
                ).exists()

        # 5. Instructor Specific Logic
        if is_instructor:
            if ChatThread:
                unread_doubts_count = ChatThread.objects.filter(course=course).count()
            
            if assessment:
                pending_submissions_count = AssessmentSubmission.objects.filter(
                    assessment=assessment,
                    is_reviewed=False
                ).count()

    # 6. Progress Calculations
    total_lessons = lessons.count()
    completed_count = len(completed_lesson_ids)
    
    # 🔥 VRO: If they are 'finished', force 100% progress even if they skipped a video
    if is_finished:
        progress_percentage = 100
    else:
        progress_percentage = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0

    # 7. Sequential Unlock Logic
    unlocked_lessons = []
    for i, lesson in enumerate(lessons):
        # Graduates and instructors see everything unlocked
        if i == 0 or is_instructor or is_finished:
            unlocked_lessons.append(lesson.id) 
        else:
            prev_lesson = lessons[i-1]
            if prev_lesson.id in completed_lesson_ids:
                unlocked_lessons.append(lesson.id)

    # 8. Quiz Context (Safely fetch for template)
    current_quiz = Quiz.objects.filter(course=course).first()
    quiz_question_count = current_quiz.questions.count() if current_quiz else 0

    context = {
        'course': course,
        'lessons': lessons,
        'assessment': assessment, 
        'is_enrolled': is_enrolled,
        'is_finished': is_finished, # Added for template
        'is_instructor': is_instructor,
        'total_lessons': total_lessons,
        'completed_count': completed_count,
        'progress_percentage': progress_percentage,
        'completed_lesson_ids': completed_lesson_ids, 
        'unlocked_lessons': unlocked_lessons,         
        'quiz': current_quiz,
        'quiz_passed': quiz_passed, 
        'has_submitted_assessment': has_submitted_assessment,
        'quiz_question_count': quiz_question_count,
        'student_count': student_count, 
        'total_revenue': revenue,
        'unread_doubts_count': unread_doubts_count,
        'pending_submissions_count': pending_submissions_count,
    }
    
    return render(request, 'courses/course_detail.html', context)


# --- 2. LEARNING EXPERIENCE (VIDEO, NOTES, Q&A) ---
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from reportlab.pdfgen import canvas # Assuming you're using reportlab for the PDF

# Import your models
from .models import Lesson, Course, Enrollment, Note, Comment, LessonProgress, LessonCompletion, Notification
from quizzes.models import Quiz # Make sure to import Quiz from your quizzes app
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from reportlab.pdfgen import canvas  # For PDF export
from .models import Lesson, Enrollment, LessonCompletion, Note, Comment, Notification
from quizzes.models import Quiz




@login_required
def watch_lesson(request, lesson_id):
    from .models import Lesson, Enrollment, LessonCompletion, Note, Comment, Notification, Certificate
    from communications.models import ChatThread  # Import ChatThread vro
    from quizzes.models import Quiz
    from django.shortcuts import get_object_or_404, render, redirect
    from django.contrib import messages
    from django.urls import reverse
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas 

    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # --- 1. SECURITY & ACCESS CHECK ---
    is_instructor = (course.instructor == request.user)
    
    # 🔥 VRO FIX: Allow access if status is 'approved' OR 'finished'
    enrollment = Enrollment.objects.filter(
        user=request.user, 
        course=course, 
        status__in=['approved', 'finished']
    ).first()
    
    is_enrolled = enrollment is not None
    is_finished = (enrollment.status == 'finished') if enrollment else False

    # If they aren't the instructor or an enrolled student, kick them out
    if not (is_enrolled or is_instructor):
        messages.warning(request, "Vro, you need to enroll and get approval to watch this!")
        return redirect('course_detail', course_id=course.id)

    # URL Hacking prevention for students
    if not is_instructor and not is_finished:
        previous_lessons_not_done = course.lessons.filter(
            order__lt=lesson.order
        ).exclude(
            id__in=LessonCompletion.objects.filter(user=request.user).values_list('lesson_id', flat=True)
        ).exists()

        if previous_lessons_not_done:
            messages.error(request, "Vro, finish the previous lessons first! No skipping! ✋")
            return redirect('course_detail', course_id=course.id)

    # --- 2. HANDLE POST ACTIONS (Notes & Comments) ---
    if request.method == "POST":
        if request.user.profile.is_blocked:
            messages.error(request, "Vro, your account is restricted. You cannot post comments. 🚫")
            return redirect('watch_lesson', lesson_id=lesson.id)

        # A. Handle Private Notes
        if "note_content" in request.POST:
            Note.objects.update_or_create(
                user=request.user, 
                lesson=lesson, 
                defaults={'content': request.POST.get("note_content")}
            )
            messages.success(request, "Note saved privately! 📝")
            
        # B. Handle Comments & Notifications
        elif "comment_text" in request.POST:
            parent_id = request.POST.get("parent_id")
            comment_text = request.POST.get("comment_text")
            parent_obj = None
            if parent_id:
                parent_obj = get_object_or_404(Comment, id=parent_id)
            
            new_comment = Comment.objects.create(
                lesson=lesson, 
                user=request.user, 
                content=comment_text,
                parent=parent_obj
            )

            notif_link = reverse('watch_lesson', args=[lesson.id]) + f"#comment-{new_comment.id}"
            
            if parent_obj:
                if parent_obj.user != request.user:
                    Notification.objects.create(
                        user=parent_obj.user,
                        message=f"💬 @{request.user.username} replied to your doubt in {lesson.title}",
                        link=notif_link, 
                        is_read=False
                    )
            else:
                if not is_instructor:
                    Notification.objects.create(
                        user=course.instructor,
                        message=f"❓ New doubt from @{request.user.username} on {lesson.title}",
                        link=notif_link,
                        is_read=False
                    )

            messages.success(request, "Comment posted! 🚀")
            return redirect(notif_link)
            
        return redirect('watch_lesson', lesson_id=lesson.id)

    # --- 3. HANDLE PDF EXPORT ---
    if request.GET.get('export') == 'pdf':
        note = Note.objects.filter(user=request.user, lesson=lesson).first()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Notes_{lesson.title}.pdf"'
        
        p = canvas.Canvas(response)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 800, f"Lesson Notes: {lesson.title}")
        p.setFont("Helvetica", 12)
        p.drawString(100, 780, f"Course: {course.title}")
        p.drawString(100, 765, f"User: {request.user.username}")
        p.line(100, 755, 500, 755)
        
        text_obj = p.beginText(100, 730)
        text_obj.setFont("Helvetica", 11)
        content = note.content if note else "Vro, no notes found for this lesson."
        
        for line in content.split('\n'):
            text_obj.textLine(line)
            
        p.drawText(text_obj)
        p.showPage()
        p.save()
        return response

    # --- 4. PREPARE DATA FOR TEMPLATE ---
    all_lessons = course.lessons.all().order_by('order')
    
    completed_lesson_ids = list(LessonCompletion.objects.filter(
        user=request.user, 
        lesson__course=course
    ).values_list('lesson_id', flat=True))

    unlocked_lessons = []
    for i, l in enumerate(all_lessons):
        if i == 0 or is_instructor or is_finished:
            unlocked_lessons.append(l.id)
        else:
            prev_l = all_lessons[i-1]
            if prev_l.id in completed_lesson_ids:
                unlocked_lessons.append(l.id)

    student_note = Note.objects.filter(user=request.user, lesson=lesson).first()

    # 🔥 VRO OPTIMIZED: Fetch comments with related users/profiles and prefetch replies
    comments = lesson.comments.filter(
        parent=None,
        is_hidden=False,
        user__profile__is_blocked=False
    ).select_related('user', 'user__profile').prefetch_related(
        'replies', 
        'replies__user', 
        'replies__user__profile'
    ).order_by('-created_at')
    
    # Pre-fetch all user IDs who have a certificate for this course to show the Graduate badge
    graduates = list(Certificate.objects.filter(course=course).values_list('user_id', flat=True))

    next_lesson = all_lessons.filter(order__gt=lesson.order).first()
    prev_lesson = all_lessons.filter(order__lt=lesson.order).last()
    
    quiz = Quiz.objects.filter(course=course).first()
    is_completed = lesson.id in completed_lesson_ids

    # --- 5. CHAT THREAD LOGIC FOR BUTTON ---
    chat_thread = None
    if not is_instructor:
        # We find or create the thread so the student can always click the button
        chat_thread, created = ChatThread.objects.get_or_create(
            student=request.user,
            teacher=course.instructor,
            course=course
        )

    context = {
        'lesson': lesson,
        'course': course,
        'student_note': student_note,
        'comments': comments,
        'graduates': graduates,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
        'quiz': quiz,
        'is_completed': is_completed,
        'completed_lesson_ids': completed_lesson_ids,
        'unlocked_lessons': unlocked_lessons,
        'all_lessons': all_lessons,
        'is_instructor': is_instructor, 
        'is_finished': is_finished,
        'chat_thread': chat_thread, # Pass this to use in watch_lesson.html
    }

    return render(request, 'courses/watch_lesson.html', context)




@login_required
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course, status='approved').exists()

    if is_enrolled:
        # 1. Save the progress
        LessonCompletion.objects.get_or_create(user=request.user, lesson=lesson)
        
        # 2. 🔥 NEW: UPDATE THE STREAK 🔥
        update_streak(request.user)
        
        messages.success(request, f"Lesson '{lesson.title}' marked as complete! Streak: {request.user.profile.streak_count} days! 🔥")

        return redirect(request.META.get('HTTP_REFERER', 'watch_lesson'))

    messages.error(request, "You are not enrolled in this course.")
    return redirect('course_detail', course_id=course.id)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Course, Enrollment, Notification
@login_required
def reject_enrollment(request, enrollment_id):
    """
    Instructor rejects a student payment with a reason.
    - Updates Enrollment status to 'rejected'.
    - Saves a rejection note.
    - Creates a notification that links directly to the re-upload/checkout page.
    """
    # 1. Fetch the specific enrollment request
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    # 2. SECURITY: Only the instructor of this course can reject it
    if enrollment.course.instructor == request.user:
        if request.method == "POST":
            # 3. Get the reason from the dashboard input field
            reason = request.POST.get('rejection_note', 'No specific reason provided.')
            
            # 4. Update status and save the reason
            enrollment.status = 'rejected' 
            enrollment.rejection_note = reason 
            enrollment.save()
            
            # 5. LINK GENERATION: Points back to the checkout/upload page
            # VRO: This URL is what our mark_notification_as_read logic will prioritize!
            checkout_url = reverse('checkout', args=[enrollment.course.id])
            
            # 6. NOTIFICATION: Tell the student why they failed and give them the fix
            Notification.objects.create(
                user=enrollment.user,
                notification_type='payment',
                message=f"❌ Payment Failed for '{enrollment.course.title}'. Reason: {reason}. Click to re-upload, vro.",
                link=checkout_url, 
                is_read=False
            )
            
            messages.warning(request, f"Rejected {enrollment.user.username}'s request. Notification sent.")
        else:
            messages.error(request, "Invalid request method. Please use the form, vro.")
    else:
        messages.error(request, "Vro, you aren't the instructor of this course!")

    # 7. Redirect back to the instructor dashboard
    return redirect('instructor_dashboard')


@login_required
def checkout(request, course_id):
    """Student handles payment submission and re-submission"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if an enrollment record already exists
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    
    if enrollment:
        # 1. Already enrolled
        if enrollment.status in ['approved', 'finished']:
            return render(request, 'courses/payment_success.html', {
                'message': 'You are already enrolled! Go to your dashboard to start learning.'
            })
        
        # 2. Waiting for review
        elif enrollment.status == 'pending':
            return render(request, 'courses/payment_success.html', {
                'message': 'Your payment is still under review! Please wait for the instructor.'
            })
        
        # 3. Handle Rejection (The 'Negative' Part)
        elif enrollment.status == 'rejected':
            # Pass the instructor's note to the template
            reason = enrollment.rejection_note if enrollment.rejection_note else "Invalid screenshot."
            error_message = f"❌ Instructor says: {reason}"
            
            if request.method == "POST":
                screenshot = request.FILES.get('screenshot')
                if screenshot:
                    # Update existing record: reset to pending and save new image
                    enrollment.payment_screenshot = screenshot
                    enrollment.status = 'pending'
                    enrollment.rejection_note = "" # Clear old reason for new review
                    enrollment.save()

                    # Notify Teacher about the re-submission
                    Notification.objects.create(
                        user=course.instructor,
                        notification_type='payment',
                        message=f"🔄 Re-submission! {request.user.username} fixed payment for: {course.title}.",
                        link=reverse('instructor_dashboard')
                    )
                    return render(request, 'courses/payment_success.html', {'message': 'Re-submission successful! Instructor notified.'})
            
            return render(request, 'courses/checkout.html', {
                'course': course, 
                'error_message': error_message 
            })

    # 4. Standard first-time checkout logic
    if request.method == "POST":
        screenshot = request.FILES.get('screenshot')
        if screenshot:
            Enrollment.objects.create(
                user=request.user, 
                course=course, 
                payment_screenshot=screenshot, 
                status='pending'
            )
            
            # Notify Teacher for the first time
            Notification.objects.create(
                user=course.instructor, 
                notification_type='payment',
                message=f"🔥 New enrollment request! {request.user.username} paid for: {course.title}.",
                link=reverse('instructor_dashboard')
            )
            return render(request, 'courses/payment_success.html', {'message': 'Screenshot uploaded! Instructor notified.'})

    return render(request, 'courses/checkout.html', {'course': course})



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SupportTicket, Notification # Ensure Notification model exists
from django.contrib.auth.models import User

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SupportTicket, Notification
from django.contrib.auth.models import User

@login_required
def contact_support(request):
    if request.method == "POST":
        # 1. Create the ticket
        ticket = SupportTicket.objects.create(
            user=request.user,
            subject=request.POST.get('subject'),
            message=request.POST.get('message')
        )
        
        # 2. Notify Admins
        admins = User.objects.filter(is_superuser=True)
        for admin_user in admins:
            Notification.objects.create(
                user=admin_user,
                message=f"New Support Ticket from {request.user.username}: {ticket.subject}",
            )

        messages.success(request, "Message sent to support! Check below for replies, vro.")
        return redirect('contact_support')
    
    # 3. Fetch user's history
    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'courses/contact.html', {'tickets': tickets})

# --- 4. REVIEWS & GAMIFICATION ---

@login_required
def add_review(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        Review.objects.update_or_create(
            user=request.user, course=course,
            defaults={'rating': request.POST.get('rating'), 'comment': request.POST.get('comment')}
        )
    return redirect('course_detail', course_id=course.id)

from django.db.models import Sum, Count, Q, F, Value
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.shortcuts import render

def leaderboard(request):
    # Ranking students by:
    # 1. Total Assessment Marks
    # 2. Daily Streak
    # 3. Course Count (Approved or Finished)
    
    top_students = User.objects.annotate(
        # 🔥 VRO FIX: Count students who are approved OR finished
        courses_count=Count(
            'enrollment', 
            filter=Q(enrollment__status__in=['approved', 'finished'])
        ),
        # Summing grades and forcing 0 if they haven't submitted anything yet
        assessment_score=Coalesce(Sum('assessmentsubmission__grade'), Value(0))
    ).filter(
        # Only show people actually doing something
        Q(courses_count__gt=0) | Q(profile__streak_count__gt=0) | Q(assessment_score__gt=0)
    ).select_related('profile').order_by(
        '-assessment_score', 
        '-profile__streak_count', 
        '-courses_count'
    )[:10]
    
    return render(request, 'courses/leaderboard.html', {
        'top_students': top_students
    })

@login_required
def my_certificates(request):
    # VRO: We use select_related('course') so the page loads faster 
    # It pulls the course title and thumbnail in one single database hit
    certificates = Certificate.objects.filter(
        user=request.user
    ).select_related('course').order_by('-issued_at')
    
    return render(request, 'courses/my_certificates.html', {
        'certificates': certificates,
        'total_certs': certificates.count()
    })

@login_required
def generate_certificate(request, course_id):
    from .models import Course, Enrollment, Certificate, LessonCompletion
    import uuid
    from django.http import HttpResponse
    from django.contrib import messages
    from django.shortcuts import get_object_or_404, redirect

    course = get_object_or_404(Course, id=course_id)
    
    # 1. SECURITY & STATUS CHECK
    enrollment = Enrollment.objects.filter(
        user=request.user, 
        course=course, 
        status='finished'
    ).first()

    if not enrollment:
        messages.error(request, "Vro, you need to complete the course and project to get this! 🎓")
        return redirect('course_detail', course_id=course.id)

    # 2. DOUBLE CHECK LESSONS
    total_lessons = course.lessons.count()
    completed_lessons = LessonCompletion.objects.filter(user=request.user, lesson__course=course).count()
    
    if total_lessons == 0 or completed_lessons < total_lessons:
        messages.error(request, "Finish all lessons first, vro! 📚")
        return redirect('course_detail', course_id=course.id)

    # 3. GET OR CREATE CERTIFICATE RECORD
    cert, created = Certificate.objects.get_or_create(
        user=request.user, 
        course=course,
        defaults={'certificate_id': str(uuid.uuid4())[:12].upper()} 
    )

    # 4. GENERATE THE PREMIUM PDF
    full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    display_name = full_name if full_name else request.user.username

    # 🔥 VRO FIX: Added cert_id=cert.certificate_id here!
    pdf_buffer = generate_certificate_pdf(
        student_name=display_name, 
        course_name=course.title, 
        date=cert.issued_at.strftime('%d %b, %Y'),
        cert_id=cert.certificate_id
    )

    # 5. SHIP THE FILE
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Certificate_{course.title.replace(" ", "_")}.pdf"'
    
    return response

# --- 6. USER PROFILE ---

@login_required
def profile_settings(request):
    # VRO: This ensures the profile exists before we try to edit it
    from .models import Profile
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated! 🔥')
            return redirect('profile_settings')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'courses/profile_settings.html', {
        'u_form': u_form, 
        'p_form': p_form
    })




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import SupportTicket, Notification

@login_required
def admin_support_dashboard(request):
    """
    Dashboard for Admins to view and manage support tickets.
    """
    # Only allow staff/superusers to see this page
    if not request.user.is_staff:
        return redirect('course_list')

    # Get unresolved tickets first, then recently resolved ones
    pending_tickets = SupportTicket.objects.filter(is_resolved=False).order_by('-created_at')
    resolved_tickets = SupportTicket.objects.filter(is_resolved=True).order_by('-replied_at')[:10]
    
    context = {
        'pending_tickets': pending_tickets,
        'resolved_tickets': resolved_tickets,
    }
    return render(request, 'courses/admin_support_dashboard.html', context)







@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.user != request.user:
        messages.error(request, "You can only edit your own comments, vro! ✋")
        return redirect('watch_lesson', lesson_id=comment.lesson.id)

    if request.method == "POST":
        new_content = request.POST.get('content')
        if new_content:
            comment.content = new_content
            comment.save()
            messages.success(request, "Comment updated! ✨")
    
    return redirect('watch_lesson', lesson_id=comment.lesson.id)






from .forms import AdminReplyForm
from django.utils import timezone

@login_required
def ticket_reply_view(request, ticket_id):
    if not request.user.is_staff:
        return redirect('course_list')

    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    
    if request.method == 'POST':
        form = AdminReplyForm(request.POST, instance=ticket)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.replied_at = timezone.now()
            reply.is_resolved = True # Automatically resolve when replying
            reply.save()

            # Create Notification for the student
            Notification.objects.create(
                user=ticket.user,
                message=f"Admin replied to your ticket: {ticket.subject}",
                link='/support/', # Path to student support page
                notification_type='reply'
            )
            
            return redirect('admin_support_dashboard')
    else:
        form = AdminReplyForm(instance=ticket)

    return render(request, 'courses/ticket_reply_page.html', {
        'form': form,
        'ticket': ticket
    })

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification
@login_required
def mark_notification_as_read(request, notification_id):
    """
    Marks a notification as read and handles specific redirects.
    PRIORITY: 
    1. Direct Links (Custom URLs like Checkout/Watch/Re-upload)
    2. Specific Content Keywords (Grading, Support, etc.)
    3. Final Fallback (Dashboards or Course List)
    """
    # 1. Fetch the notification (Security: ensures it belongs to the logged-in user)
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # 2. Mark notification as read
    notification.is_read = True
    notification.save()
    
    msg = notification.message.lower()
    n_type = getattr(notification, 'notification_type', None)

    # --- 🚀 STEP 1: HIGHEST PRIORITY - THE DIRECT LINK 🚀 ---
    # Vro, if the instructor attached a specific URL (like the Re-upload page), 
    # we MUST go there first. We don't care what words are in the message.
    if hasattr(notification, 'link') and notification.link and notification.link != '#':
        
        # Specific sub-logic for Support Contact within links
        if "/support/contact/" in notification.link:
            if request.user.is_staff or request.user.is_superuser:
                return redirect('admin_support_dashboard')
            return redirect('contact_support')
            
        # This catches 'checkout' and 'watch' links perfectly!
        return redirect(notification.link)

    # --- STEP 2: CONTENT-BASED REDIRECTS (Only runs if NO link exists) ---

    # Grading / Certificates
    if "graded" in msg or "score" in msg:
        return redirect('my_certificates')

    # Reports
    if "reported" in msg or "dirty comment" in msg:
        if request.user.is_superuser:
            return redirect('admin_report_dashboard')

    # Admin Messages (Warnings/Announcements)
    if any(word in msg for word in ["admin warning", "admin info", "admin announcement"]):
        if request.user.is_staff or request.user.is_superuser:
            return redirect('instructor_dashboard')
        return redirect('student_dashboard')

    # Teacher Approval & New Request Logic
    if "teacher" in msg or "instructor" in msg or "approved" in msg:
        if any(word in msg for word in ["request", "application", "new instructor"]):
            if request.user.is_superuser:
                return redirect('admin_analytics')
        if request.user.is_staff:
            return redirect('instructor_dashboard')

    # Support Ticket Logic
    if "new support ticket" in msg or "ticket from" in msg:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_support_dashboard')

    if "replied to your ticket" in msg or n_type == 'reply':
        return redirect('contact_support')

    # Payment/Verification Fallback (Only if no specific link was provided above)
    if any(word in msg for word in ["payment", "verified", "earned"]) or n_type == 'payment':
        return redirect('student_dashboard')
        
    # Doubt/Chat/Comment Redirects
    if any(word in msg for word in ['doubt', 'chat', 'comment']):
        if request.user.is_staff or request.user.is_superuser:
            return redirect('instructor_dashboard')
        return redirect('student_dashboard')

    # Streak/Gamification
    if "streak" in msg:
        return redirect('leaderboard')

    # --- STEP 3: FINAL FALLBACK ---
    return redirect('course_list')


from .models import Profile
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import Enrollment, LessonCompletion, Certificate, Profile

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import Enrollment, LessonCompletion, Certificate, Profile, Course  # Added Course

@login_required
def student_dashboard(request):
    # 1. Get all courses where the student's status is 'approved' OR 'finished'
    # Vro, we need 'finished' here so they don't disappear after uploading the project!
    enrollments = Enrollment.objects.filter(
        user=request.user, 
        status__in=['approved', 'finished']
    ).select_related('course')
    
    # Track which IDs the user is already enrolled in (for recommendations)
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    
    # 7. 🔥 Fetch IDs of courses that already have certificates
    # We convert to a list so we can manually add "finished" IDs to it below
    completed_course_ids = list(Certificate.objects.filter(
        user=request.user
    ).values_list('course_id', flat=True))
    
    course_data = []
    for enrollment in enrollments:
        course = enrollment.course
        total_lessons = course.lessons.count()
        completed_count = LessonCompletion.objects.filter(user=request.user, lesson__course=course).count()
        
        # Calculate progress percent
        progress = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0
        
        # 🔥 VRO: INSTANT FINISH LOGIC 🔥
        # If the status is 'finished', force progress to 100 and mark as completed
        if enrollment.status == 'finished':
            progress = 100
            if course.id not in completed_course_ids:
                completed_course_ids.append(course.id)
        
        course_data.append({
            'course': course,
            'progress': progress,
            'completed_lessons': completed_count,
            'total_lessons': total_lessons,
            'status': enrollment.status,
        })

    # 2. Get the User Profile for Streak Data
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    current_streak = user_profile.streak_count

    # 3. Dynamic Motivational Message
    if current_streak == 0:
        streak_msg = "Start a lesson today to begin your streak! 🚀"
    elif current_streak < 3:
        streak_msg = "Good start, vro! Keep it going! 🔥"
    elif current_streak < 7:
        streak_msg = "You're on fire! Don't stop now! ⚡"
    else:
        streak_msg = "UNSTOPPABLE! You're a learning machine! 🏆"

    # 4. 7-Day Activity Chart Logic
    chart_labels = []
    chart_data = []
    today = timezone.now().date()

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%a'))
        count = LessonCompletion.objects.filter(
            user=request.user, 
            completed_at__date=day 
        ).count()
        chart_data.append(count)

    # 5. RECOMMENDED COURSES
    recommended_courses = Course.objects.exclude(id__in=enrolled_course_ids).order_by('?')[:3]

    # 6. Stats for the Top Cards
    stats = {
        'total_enrolled': enrollments.count(),
        'certificates_earned': len(completed_course_ids), # Use the list length
        'completed_lessons_total': LessonCompletion.objects.filter(user=request.user).count(),
        'current_streak': current_streak,
        'longest_streak': user_profile.longest_streak,
        'streak_message': streak_msg,
    }

    # 8. Final Render
    return render(request, 'courses/dashboard.html', {
        'course_data': course_data,
        'stats': stats,
        'completed_course_ids': completed_course_ids,
        'profile': user_profile,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'recommended_courses': recommended_courses,
    })
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Enrollment, LessonCompletion, Certificate, Course 

from django.db.models import Count # Add this import at the top

from django.db.models import Count, Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from courses.models import Course, Enrollment, Certificate, LessonCompletion

@login_required
def student_profile(request):
    user = request.user
    
    # Initialize variables
    my_enrollments = []
    my_courses = [] 
    completed_course_ids = []
    certified_course_ids = []

    # --- 1. ADMIN LOGIC ---
    if user.is_superuser:
        pass 

    # --- 2. TEACHER (INSTRUCTOR) LOGIC ---
    elif user.is_staff:
        # VRO: Only count students where teacher has agreed (Approved or Finished)
        my_courses = Course.objects.filter(instructor=user).annotate(
            total_enrolled=Count('enrollment', filter=Q(enrollment__status__in=['approved', 'finished']))
        )

    # --- 3. STUDENT LOGIC ---
    else:
        # Students only see their own approved/finished stuff
        my_enrollments = Enrollment.objects.filter(
            user=user, 
            status__in=['approved', 'finished']
        ).select_related('course')

        certified_course_ids = list(Certificate.objects.filter(
            user=user
        ).values_list('course_id', flat=True))

        for enrollment in my_enrollments:
            total_lessons = enrollment.course.lessons.count()
            completed_count = LessonCompletion.objects.filter(
                user=user, 
                lesson__course=enrollment.course
            ).count()
            
            progress = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0

            if enrollment.status == 'finished':
                progress = 100
                
            enrollment.progress = progress 

            if progress >= 100 or enrollment.status == 'finished':
                completed_course_ids.append(enrollment.course.id)

    # --- 4. RETURN DATA ---
    return render(request, 'courses/profile.html', {
        'enrollments': my_enrollments,
        'my_courses': my_courses, 
        'completed_course_ids': completed_course_ids,
        'certified_course_ids': certified_course_ids,
    })



def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    course_id = lesson.course.id
    lesson.delete()
    return redirect('course_detail', course_id=course_id)


def toggle_publish(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    course.is_published = not course.is_published
    course.save()
    return redirect('course_detail', course_id=course.id)







from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
@login_required
def approve_enrollment(request, enrollment_id):
    """
    Instructor approves a student payment.
    - Updates Enrollment status.
    - Creates a notification with a direct 'Watch' link.
    """
    # 1. Fetch the specific enrollment request
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    # 2. SECURITY: Only allow the instructor of the course to approve it
    if enrollment.course.instructor == request.user:
        enrollment.status = 'approved'
        enrollment.save()
        
        # 3. LINK LOGIC: Find the first lesson to send the student straight to the player
        first_lesson = enrollment.course.lessons.first()
        
        if first_lesson:
            # If lessons exist, link to the first one
            target_link = f"/watch/{first_lesson.id}/"
        else:
            # Fallback to course details if no lessons are uploaded yet
            target_link = reverse('course_detail', kwargs={'slug': enrollment.course.slug})
        
        # 4. NOTIFICATION ENGINE: Tell the student they are in!
        Notification.objects.create(
            user=enrollment.user,
            message=f"🔥 Vro! Your payment for '{enrollment.course.title}' is verified. Start watching now!",
            link=target_link,
            is_read=False,
            notification_type='payment' # Helps with the icon logic we set up
        )
        
        messages.success(request, f"Approved {enrollment.user.username} successfully! 🚀")
    else:
        messages.error(request, "Vro, you aren't the instructor of this course!")

    # 5. Redirect back to instructor dashboard
    return redirect('instructor_dashboard')









from .forms import CourseEditForm

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course
from .forms import CourseEditForm # Ensure this is imported

@login_required
def edit_course(request, course_id):
    # Fetch the course
    course = get_object_or_404(Course, id=course_id)
    
    # Security: Only the instructor can edit
    if course.instructor != request.user:
        messages.error(request, "Vro, you can't edit someone else's course!")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        # Don't forget request.FILES for the thumbnail!
        form = CourseEditForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Changes saved for {course.title}! 🚀")
            return redirect('course_detail', course_id=course.id)
    else:
        # GET request: Load the form with existing course data
        form = CourseEditForm(instance=course)
    
    return render(request, 'courses/edit_course.html', {
        'form': form, 
        'course': course
    })



@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    lesson_id = comment.lesson.id
    course_instructor = comment.lesson.course.instructor
    
    # 🚨 VRO FIX: Standardized check for Author OR Instructor
    if request.method == "POST":
        if request.user == comment.user or request.user == course_instructor:
            comment.delete()
            messages.success(request, "Comment vanished! 🗑️")
        else:
            messages.error(request, "Vro, you don't have permission to delete this! 🚫")
    else:
        # If someone tries to access via URL (GET), block it for security
        messages.error(request, "Invalid request method, vro. ✋")
    
    # Try to redirect back to where they came from, otherwise go to the lesson
    return redirect(request.META.get('HTTP_REFERER', reverse('watch_lesson', args=[lesson_id])))




from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Enrollment  # Make sure to import your Enrollment model

@login_required
def view_student_profile(request, user_id):
    # 1. Get the student object
    student = get_object_or_404(User, id=user_id)
    
    # 2. Fetch only the courses this student is taking FROM THIS INSTRUCTOR
    # This prevents instructors from spying on other teachers' courses
    enrolled_courses = Enrollment.objects.filter(
        user=student, 
        course__instructor=request.user,
        status__in=['approved', 'finished']
    ).select_related('course')

    return render(request, 'courses/student_profile_for_instructor.html', {
        'student': student,
        'enrolled_courses': enrolled_courses,
    })

from django.shortcuts import get_object_or_404, redirect
from .models import Course, Wishlist

from django.contrib import messages

def toggle_wishlist(request, course_id):
    if not request.user.is_authenticated:
        messages.info(request, "Vro, you need to sign in to save courses! 🔑")
        return redirect('login') 
    
    course = get_object_or_404(Course, id=course_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if course in wishlist.courses.all():
        wishlist.courses.remove(course)
        # Alert for removal
        messages.warning(request, f"Removed {course.title} from your wishlist! 💔")
    else:
        wishlist.courses.add(course)
        # Alert for adding
        messages.success(request, f"Vro! {course.title} added to your wishlist! ❤️")
        
        # This line makes the blue "1" badge appear in the navbar
        request.session['wishlist_seen'] = False
        
    return redirect(request.META.get('HTTP_REFERER', 'course_list'))

# PRO TIP: In your existing course list view, add this logic:
# wishlist = request.user.wishlist.courses.values_list('id', flat=True) if request.user.is_authenticated else []
# Then pass 'wishlist_ids': wishlist in the context.


@login_required
def wishlist_page(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    saved_courses = wishlist.courses.all()
    
    # Vro, this line tells the system "the student has seen their wishlist"
    # This makes the blue badge disappear on the next page load
    request.session['wishlist_seen'] = True
    
    return render(request, 'courses/wishlist.html', {'saved_courses': saved_courses})



from datetime import date, timedelta
from .models import Notification  # Ensure you import your Notification model

def update_streak(user):
    """Vro, this logic checks if the student is consistent and sends notifications!"""
    profile = user.profile
    today = date.today()
    old_streak = profile.streak_count # Store old streak to see if it increased
    
    if profile.last_activity_date:
        # 1. Already studied today? Do nothing.
        if profile.last_activity_date == today:
            return
        
        # 2. Check if they studied yesterday
        yesterday = today - timedelta(days=1)
        if profile.last_activity_date == yesterday:
            profile.streak_count += 1
        else:
            # 3. They missed a day. Reset.
            profile.streak_count = 1
    else:
        # First time studying!
        profile.streak_count = 1
    
    # Update longest streak record
    if profile.streak_count > profile.longest_streak:
        profile.longest_streak = profile.streak_count
        
    profile.last_activity_date = today
    profile.save()

    # --- 🚀 NOTIFICATION SYSTEM INTEGRATION ---
    new_streak = profile.streak_count
    
    # Logic: Only send notification if the streak actually increased or started
    if new_streak > old_streak or new_streak == 1:
        
        # Custom messages for milestones
        if new_streak == 1:
            msg = "🔥 Vro, you started a new learning streak! Keep it going tomorrow!"
        elif new_streak == 3:
            msg = "⚡ 3-DAY STREAK! You're building a habit, vro! Don't stop now."
        elif new_streak == 7:
            msg = "🏆 7-DAY STREAK! One whole week! You're a legend, vro. Keep grinding!"
        else:
            msg = f"🔥 Streak Updated! You've been consistent for {new_streak} days!"

        # Create the notification in your DB
        Notification.objects.create(
            user=user,
            notification_type='comment', # Using 'comment' type since it has a generic bell icon
            message=msg,
            link="/dashboard/", # Send them to their dashboard to see the fire icon
            is_read=False
        )

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Comment, CommentReport, Profile, User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Comment, CommentReport, Profile

@login_required
def report_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Don't let users report themselves
    if comment.user == request.user:
        messages.error(request, "Vro, you cannot report your own comment!")
        return redirect('watch_lesson', lesson_id=comment.lesson.id)

    if request.method == 'POST':
        reason = request.POST.get('reason')
        
        # Create the report record for the Admin Dashboard
        CommentReport.objects.create(
            reporter=request.user,
            comment=comment,
            offender=comment.user,
            reason=reason
        )

        # UPDATED: We no longer hide the comment here. 
        # It stays in the lesson box until the Admin reviews it.
        messages.warning(request, "Comment reported. Admin will review this soon, vro!")
        return redirect('watch_lesson', lesson_id=comment.lesson.id)
        
    return render(request, 'courses/report_page.html', {'comment': comment})
@login_required
def blocked_page(request):
    if not request.user.profile.is_blocked:
        return redirect('course_list')
    return render(request, 'courses/blocked.html')

# --- STAFF/ADMIN ONLY VIEWS ---

@login_required
def admin_report_dashboard(request):
    if not request.user.is_superuser:
        return redirect('course_list')
    
    # 1. Fetch reports that still need attention
    pending_reports = CommentReport.objects.filter(is_resolved=False).select_related(
        'reporter', 'offender', 'comment'
    ).order_by('-created_at')

    # 2. Fetch recent history of handled reports
    resolved_reports = CommentReport.objects.filter(is_resolved=True).select_related(
        'reporter', 'offender', 'comment'
    ).order_by('-created_at')[:20]

    # 3. ADDED: Fetch all users who are currently blocked
    # This powers the "Blocked Users" table we added to the HTML
    blocked_profiles = Profile.objects.filter(is_blocked=True).select_related('user')
    
    return render(request, 'courses/admin_report_dashboard.html', {
        'pending_reports': pending_reports,
        'resolved_reports': resolved_reports,
        'blocked_profiles': blocked_profiles, # Pass this to the template
        'pending_count': pending_reports.count(),
        'resolved_count': resolved_reports.count(),
    })

@login_required
def resolve_report(request, report_id):
    if not request.user.is_superuser:
        return redirect('course_list')
    
    report = get_object_or_404(CommentReport, id=report_id)
    report.is_resolved = True
    report.save()
    messages.success(request, "Report marked as resolved, vro!")
    return redirect('admin_report_dashboard')

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Comment, CommentReport
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Comment, CommentReport
@login_required
def admin_block_user(request, user_id):
    """
    Triggered from Admin Dashboard. 
    Kills the bad comment and locks the user out.
    """
    if not request.user.is_superuser:
        return redirect('course_list')
    
    # 1. Get the Profile and Block it
    target_profile = get_object_or_404(Profile, user_id=user_id)
    target_profile.is_blocked = True
    target_profile.save()

    # 2. THE SURGICAL STRIKE: Delete the specific reported comment
    # This ensures it disappears from the lesson comment box immediately.
    reported_comment_id = request.GET.get('comment_id')
    
    if reported_comment_id:
        # Physical deletion from DB = Vanishes from the site forever
        Comment.objects.filter(id=reported_comment_id).delete()

    # 3. Clean up the dashboard by resolving all reports for this offender
    CommentReport.objects.filter(offender_id=user_id).update(is_resolved=True)

    messages.error(request, f"User @{target_profile.user.username} blocked. Bad comment erased, vro!")
    return redirect('admin_report_dashboard')

@login_required
def admin_unblock_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('course_list')
    
    target_profile = get_object_or_404(Profile, user_id=user_id)
    target_profile.is_blocked = False 
    target_profile.save()
    
    messages.success(request, f"User @{target_profile.user.username} unblocked. ")
    return redirect('admin_report_dashboard')



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Lesson, Note  # Ensure Note is imported

def save_lesson_note(request, lesson_id):
    if request.method == "POST":
        # 1. Get the content from the textarea (name="note_content")
        content = request.POST.get('note_content')
        
        # 2. Get the specific lesson object
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # 3. Update the existing note or create a new one for this user/lesson
        Note.objects.update_or_create(
            user=request.user, 
            lesson=lesson,
            defaults={'content': content}
        )
        
        messages.success(request, "Notes saved successfully!")
        
        # 4. Redirect back to the lesson page
        return redirect('watch_lesson', lesson_id=lesson_id)
        
    return redirect('course_list')







@login_required
def admin_message_center(request):
    # Security: Only superusers or staff can access this page
    if not request.user.is_staff:
        messages.error(request, "Vro, you don't have permission to be here! 🚫")
        return redirect('course_list')

    if request.method == "POST":
        user_ids = request.POST.getlist('selected_users')
        message_text = request.POST.get('admin_message')
        notif_type = request.POST.get('notif_type', 'info')

        if user_ids and message_text:
            # Match the prefix to the icons in base.html
            if notif_type == 'warning':
                prefix = "🚨 ADMIN WARNING"
            elif notif_type == 'success':
                prefix = "🔥 ADMIN ANNOUNCEMENT"
            else:
                prefix = "ℹ️ ADMIN INFO"

            # Create notifications for every selected user
            notifications = [
                Notification(
                    user_id=uid,
                    message=f"{prefix}: {message_text}",
                    notification_type=notif_type,
                    link='#',  # Keeps them on the same page
                    is_read=False
                ) for uid in user_ids
            ]
            
            Notification.objects.bulk_create(notifications)
            messages.success(request, f"Successfully blasted messages to {len(user_ids)} users! 🚀")
            return redirect('admin_message_center')

    # Get all users, separated for the UI
    students = User.objects.filter(is_staff=False, is_superuser=False).order_by('username')
    teachers = User.objects.filter(is_staff=True, is_superuser=False).order_by('username')

    return render(request, 'courses/admin_message_center.html', {
        'students': students,
        'teachers': teachers
    })



from .models import Assessment,AssessmentSubmission

import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Assessment, AssessmentSubmission, Course, Enrollment, Certificate
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Assessment, AssessmentSubmission, Course, Enrollment, Certificate

import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .models import Assessment, AssessmentSubmission, Course, Enrollment, Certificate, Notification

@login_required
def submit_assessment(request, assessment_id):
    from .models import Assessment, Enrollment, AssessmentSubmission
    from django.contrib import messages
    
    assessment = get_object_or_404(Assessment, id=assessment_id)
    course = assessment.course
    
    # 1. SECURITY & GET ENROLLMENT
    # Look for 'approved' OR 'finished' status
    enrollment = Enrollment.objects.filter(
        user=request.user, 
        course=course, 
        status__in=['approved', 'finished']
    ).first()
    
    if not enrollment:
        messages.error(request, "Vro, you must be enrolled to submit assessments!")
        return redirect('course_detail', course_id=course.id)

    # 🚨 VRO BLOCK: If status is already finished, don't let them re-enter the upload page
    if enrollment.status == 'finished':
        messages.info(request, "Vro, you already finished this section! 🎓")
        return redirect('course_detail', course_id=course.id)

    # Check if they already submitted (for the GET/POST logic below)
    existing_submission = AssessmentSubmission.objects.filter(
        assessment=assessment, 
        user=request.user
    ).first()

    if request.method == "POST":
        # If they already submitted and it's being reviewed, prevent double uploads
        if existing_submission and existing_submission.is_reviewed:
            messages.warning(request, "Vro, your project is already graded! No changes allowed.")
            return redirect('course_detail', course_id=course.id)

        file = request.FILES.get('submission_file')
        notes = request.POST.get('notes', '').strip()
        
        if not file and not existing_submission:
            messages.error(request, "Vro, you forgot to attach your project file!")
        else:
            # 2. SAVE OR UPDATE SUBMISSION
            AssessmentSubmission.objects.update_or_create(
                assessment=assessment, 
                user=request.user,
                defaults={
                    'file_submission': file if file else existing_submission.file_submission, 
                    'student_notes': notes, 
                    'is_reviewed': False
                }
            )

            # 🔥 VRO: INSTANT FINISH LOGIC 🔥
            # Change status to 'finished'. 
            enrollment.status = 'finished'
            enrollment.save()

            # 3. RENDER THE RESULT PAGE
            return render(request, 'quizzes/quiz_result.html', {
                'course': course,
                'quiz': {'course': course}, 
                'passed': True,
                'percentage': 100,
                'score': 'Done',
                'total': 'Uploaded',
                'is_assessment_upload': True  
            })

    # Render for GET request (if not finished yet)
    return render(request, 'courses/submit_assessment.html', {
        'assessment': assessment,
        'course': course,
        'existing_submission': existing_submission,
        'is_finished': False # Since we block True at the top, this is always False here
    })
 




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Assessment

@login_required
def create_assessment(request, course_id):
    # 1. Check if the user is the instructor of the course
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    # 2. Try to get an existing assessment (for Edit mode)
    assessment = Assessment.objects.filter(course=course).first()

    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        deadline = request.POST.get('deadline')
        resource = request.FILES.get('resource_file')

        if assessment:
            # --- EDIT MODE ---
            assessment.title = title
            assessment.description = description
            # Only update deadline if it's provided (handles empty input)
            if deadline:
                assessment.deadline = deadline
            # Only update file if a new one is uploaded
            if resource:
                assessment.resource_file = resource
            
            assessment.save()
            messages.success(request, "Assessment updated successfully, vro!")
        else:
            # --- CREATE MODE ---
            Assessment.objects.create(
                course=course,
                title=title,
                description=description,
                deadline=deadline if deadline else None,
                resource_file=resource
            )
            messages.success(request, "Assessment added successfully, vro! Students can now submit their projects.")

        return redirect('course_detail', course_id=course.id)

    # 3. Handle GET request: Pass existing assessment data to the form
    context = {
        'course': course,
        'assessment': assessment,
    }
    return render(request, 'courses/create_assessment.html', context)




import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Assessment, AssessmentSubmission, Certificate, Notification

@login_required
def gradebook(request, course_id):
    """
    ONE MASTER VIEW: Handles listing submissions, picking a specific one to grade,
    saving marks, updating leaderboard, and issuing certificates.
    """
    # 1. Check if the user is the instructor of this course
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    # 2. Get the assessment for this course
    assessment = get_object_or_404(Assessment, course=course)
    
    # 3. Safe check for max marks
    max_marks_val = getattr(assessment, 'max_marks', 100)
    
    # 4. Fetch all submissions for this assessment
    submissions = AssessmentSubmission.objects.filter(
        assessment=assessment
    ).select_related('user', 'user__profile').order_by('-submitted_at')

    # --- HANDLE GRADING (POST REQUEST) ---
    if request.method == "POST":
        submission_id = request.POST.get('submission_id')
        marks_raw = request.POST.get('marks')
        feedback = request.POST.get('feedback', '').strip()

        try:
            marks = int(marks_raw)
        except (TypeError, ValueError):
            messages.error(request, "Vro, please enter a valid number for marks.")
            return redirect('gradebook', course_id=course.id)

        submission = get_object_or_404(AssessmentSubmission, id=submission_id)
        
        # A. Save the Grade
        submission.grade = marks
        submission.teacher_feedback = feedback
        submission.is_reviewed = True
        submission.save()

        # B. Update Leaderboard (handles both 'total_score' or 'score' profile fields)
        profile = submission.user.profile 
        if hasattr(profile, 'total_score'):
            profile.total_score += marks
        elif hasattr(profile, 'score'):
            profile.score += marks
        profile.save()

        # C. Issue Certificate if passing (marks >= 40)
        cert_msg = ""
        if marks >= 40:
            Certificate.objects.get_or_create(
                user=submission.user,
                course=course,
                defaults={'certificate_id': str(uuid.uuid4())[:8].upper()}
            )
            cert_msg = " Certificate issued! 🎓"

        # D. Send Notification to Student
        Notification.objects.create(
            user=submission.user,
            notification_type='comment',
            message=f"Vro, your project for '{course.title}' has been graded! You scored {marks}/{max_marks_val}.{cert_msg}",
            link='/my_certificates/' 
        )

        messages.success(request, f"Graded {submission.user.username} successfully!{cert_msg}")
        return redirect('gradebook', course_id=course.id)

    # --- HANDLE SELECTION (GET REQUEST) ---
    # If the teacher clicks a specific student to grade them
    target_sub_id = request.GET.get('grade_id')
    selected_submission = None
    if target_sub_id:
        selected_submission = submissions.filter(id=target_sub_id).first()

    return render(request, 'courses/gradebook.html', {
        'course': course,
        'submissions': submissions,
        'assessment': assessment,
        'selected_submission': selected_submission,
        'display_max_marks': max_marks_val,
    })





@login_required
def clear_all_notifications(request):
    """Deletes all notifications for the logged-in user."""
    # We filter by user=request.user so they don't delete anyone else's notifications
    request.user.notifications.all().delete()
    messages.success(request, "All notifications cleared, vro!")
    
    # Redirect back to where they were, or to the dashboard
    return redirect(request.META.get('HTTP_REFERER', 'student_dashboard'))