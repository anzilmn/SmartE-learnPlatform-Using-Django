from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.contrib import messages

# Import your local models and forms
from  courses.models import Profile, Notification
from courses.models import Course, Enrollment, Lesson, LessonCompletion
from .forms import UserSignupForm, TeacherApplicationForm, CourseForm, LessonForm

# ==========================
# AUTHENTICATION VIEWS
# ==========================

from django.contrib import messages

def signup_view(request):
    if request.method == "POST":
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            login(request, user)
            
            if role == 'teacher':
                user.profile.is_teacher_applicant = True
                user.profile.save()
                
                # --- Alert for the User ---
                messages.success(request, f"Vro, your account is ready! Please complete your teacher application below. 🎓")
                
                # --- Notify Admin about the new applicant ---
                admins = User.objects.filter(is_superuser=True)
                for admin in admins:
                    Notification.objects.create(
                        user=admin,
                        message=f"New Teacher Request: {user.username} has started an application!",
                        link='/admin-analytics/'
                    )
                
                return redirect('teacher_interview')
            
            # --- Alert for Student Signup ---
            messages.success(request, f"Welcome to Smart Learn, {user.username}! Your journey starts here. 🚀")
            return redirect('course_list')
    else:
        form = UserSignupForm()
    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            if user.is_superuser:
                return redirect('course_list')
            elif user.is_staff:
                return redirect('course_list')
            else:
                return redirect('course_list')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

class MyPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        user = form.save()
        print(f"DEBUG: Password for user {user.username} has been updated!")
        return super().form_valid(form)

# ==========================
# TEACHER APPLICATION FLOW
# ==========================

@login_required
def teacher_interview(request):
    """Page where teacher applicants upload their certificates"""
    if request.method == 'POST':
        form = TeacherApplicationForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            
            # --- NEW: Notify Admin that the application is SUBMITTED ---
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    message=f"Action Required: {request.user.username} submitted a Teacher Application!",
                    link='/admin-analytics/' # This link sends admin to the approval page
                )
                
            return redirect('application_submitted')
    else:
        form = TeacherApplicationForm(instance=request.user.profile)
    return render(request, 'users/teacher_interview.html', {'form': form})

@login_required
def application_submitted(request):
    return render(request, 'users/application_submitted.html')

# ==========================
# STUDENT VIEWS
# ==========================



# ==========================
# INSTRUCTOR (TEACHER) VIEWS
# ==========================from django.db.models import Count, Sum, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from courses.models import Course, Enrollment, AssessmentSubmission
from users.forms import CourseForm # Assuming your form is named CourseForm
from django.db.models import Count, Sum, Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from courses.models import Course, Enrollment, AssessmentSubmission
from users.forms import CourseForm 

@login_required
def instructor_dashboard(request):
    """
    Instructor Dashboard Logic:
    - total_enrolled: ONLY students the teacher approved.
    - waiting_approval: Students who clicked enroll but are pending.
    """
    # 1. Get instructor's courses with strictly filtered counts
    my_courses = Course.objects.filter(instructor=request.user).annotate(
        # VRO: This only counts when teacher says OK (Status is approved or finished)
        total_enrolled=Count('enrollment', filter=Q(enrollment__status__in=['approved', 'finished'])),
        # This keeps track of people waiting in the 'Pending Approvals' table
        waiting_count=Count('enrollment', filter=Q(enrollment__status='pending'))
    )
    
    # 2. Calculate Global Stats (Strictly Approved/Finished only)
    stats = Enrollment.objects.filter(
        course__instructor=request.user, 
        status__in=['approved', 'finished']
    ).aggregate(
        total_revenue=Sum('course__price'),
        total_students=Count('user', distinct=True)
    )

    # 3. Fetch Pending Enrollment Requests for the approval table
    pending_approvals = Enrollment.objects.filter(
        course__instructor=request.user, 
        status='pending'
    ).select_related('user', 'course')

    # 4. Count Global Pending Projects
    pending_submissions_count = AssessmentSubmission.objects.filter(
        assessment__course__instructor=request.user,
        is_reviewed=False
    ).count()
    
    return render(request, 'users/instructor_dashboard.html', {
        'courses': my_courses,
        'total_students': stats['total_students'] or 0,
        'total_revenue': stats['total_revenue'] or 0,
        'pending_approvals': pending_approvals,
        'pending_submissions_count': pending_submissions_count,
        'is_instructor': True
    })

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'users/course_form.html'
    success_url = reverse_lazy('instructor_dashboard')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)
    

@login_required
def add_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect('instructor_dashboard')
    else:
        form = LessonForm()
    return render(request, 'users/add_lesson.html', {'form': form, 'course': course})

@login_required
def course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if course.instructor == request.user or request.user.is_superuser:
        course.delete()
        messages.success(request, "Vro, the course has been deleted successfully! 🗑️")
    else:
        messages.error(request, "You don't have permission to delete this, vro! ❌")
    return redirect('instructor_dashboard')

# ==========================
# ADMIN ANALYTICS VIEWS
# ==========================

@staff_member_required
def admin_analytics(request):
    user_growth = User.objects.annotate(month=TruncMonth('date_joined')) \
        .values('month').annotate(count=Count('id')).order_by('month')

    revenue_growth = Enrollment.objects.filter(status='approved') \
        .annotate(month=TruncMonth('enrolled_at')) \
        .values('month').annotate(total=Sum('course__price')).order_by('month')

    pending_teachers = Profile.objects.filter(
        is_teacher_applicant=True, 
        application_status='pending'
    ).select_related('user')

    context = {
        'user_growth': user_growth,
        'revenue_growth': revenue_growth,
        'total_users': User.objects.count(),
        'total_enrollments': Enrollment.objects.count(),
        'pending_teachers': pending_teachers,
    }
    return render(request, 'users/admin_analytics.html', context)

@staff_member_required
def approve_teacher(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    user = profile.user
    user.is_staff = True 
    user.save()
    profile.application_status = 'approved'
    profile.save()
    
    Notification.objects.create(
        user=user,
        message="Vro! Your teacher account is approved. Start creating courses!",
        link='/instructor-dashboard/' # This now matches the path in urls.py
    )
    return redirect('admin_analytics')




@staff_member_required
def reject_teacher(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    user = profile.user
    
    # Update profile status
    profile.application_status = 'rejected'
    profile.is_teacher_applicant = False # Allow them to try again later if needed
    profile.save()
    
    # Make sure they aren't staff if they were previously approved/pending
    user.is_staff = False
    user.save()
    
    # Create notification for the user
    Notification.objects.create(
        user=user,
        message="Sorry vro, your teacher application was not approved at this time. ❌",
        link='/support/' # Or wherever you want them to go for help
    )
    
    messages.warning(request, f"Application for {user.username} has been rejected.")
    return redirect('admin_analytics')





from django.db.models import Count
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from courses.models import Enrollment, Certificate

@staff_member_required
def student_admin_dashboard(request):
    # VRO CHECK: Make sure the students you added DON'T have 'is_staff' checked in Django Admin
    students = User.objects.filter(is_staff=False).annotate(
        course_count=Count('enrollment') # Ensure 'enrollment' matches your Related_Name
    ).order_by('-date_joined')

    # Debugging: This will print the count in your CMD/Terminal
    print(f"DEBUG: Found {students.count()} students")

    for student in students:
        # Using .filter().count() is safer if you haven't set up reverse relations perfectly yet
        student.completed_count = Certificate.objects.filter(user=student).count()
        student.active_count = student.course_count - student.completed_count

    return render(request, 'users/student_admin.html', { # Make sure this path matches your folder
        'students': students,
        'total_students': students.count()
    })

@staff_member_required
def delete_student(request, user_id):
    if request.method == 'POST':
        student = get_object_or_404(User, id=user_id, is_staff=False)
        student.delete()
        messages.success(request, "Student and all their data deleted successfully.")
    return redirect('student_admin_dashboard')








from django.contrib.auth.models import User
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from django.contrib.auth.models import User
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

@staff_member_required
def admin_teacher_dashboard(request):
    # Get users who are staff (teachers) but NOT superusers (you)
    # VRO FIX: Using 'course' as the related name which Django confirmed is correct
    teachers = User.objects.filter(is_staff=True, is_superuser=False).annotate(
        teaching_count=Count('course')
    ).order_by('-date_joined')

    return render(request, 'users/admin_teachers.html', {
        'teachers': teachers,
        'total_teachers': teachers.count()
    })

@staff_member_required
def delete_teacher(request, teacher_id):
    if request.method == 'POST':
        teacher = get_object_or_404(User, id=teacher_id, is_staff=True, is_superuser=False)
        name = teacher.username
        teacher.delete()
        messages.success(request, f"Teacher {name} has been removed.")
    return redirect('admin_teacher_dashboard')