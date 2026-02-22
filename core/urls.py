from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
# Import your views directly since they are in the same project/app folder
from users import views as user_views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Homepage and Course Logic
    path('', include('courses.urls')), 
    
    # Authentication & Profile
    path('users/', include('users.urls')), 
    path('signup/', user_views.signup_view, name='signup'),
    path('login/', user_views.login_view, name='login'),
 

    # --- INSTRUCTOR & ADMIN PATHS (FIXED VRO) ---
    path('instructor-dashboard/', user_views.instructor_dashboard, name='instructor_dashboard'),
    path('course/create/', user_views.CourseCreateView.as_view(), name='course_create'),
    path('course/<int:course_id>/add-lesson/', user_views.add_lesson, name='add_lesson'),
    path('course/<int:course_id>/delete/', user_views.course_delete, name='course_delete'),
    path('admin-analytics/', user_views.admin_analytics, name='admin_analytics'),
    path('approve-teacher/<int:profile_id>/', user_views.approve_teacher, name='approve_teacher'),
    
    # Teacher Application Flow
    path('teacher-interview/', user_views.teacher_interview, name='teacher_interview'),
    path('application-submitted/', user_views.application_submitted, name='application_submitted'),

    # --- PASSWORD RESET LOGIC ---
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset.html',
             html_email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         user_views.MyPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    path('quizzes/', include('quizzes.urls')),
    path('communications/', include('communications.urls')),
    path('chat/', include('communications.urls')),
    path('certificates/', include('certificates.urls')),

    path('reject-teacher/<int:profile_id>/', user_views.reject_teacher, name='reject_teacher'), # Add this!
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)