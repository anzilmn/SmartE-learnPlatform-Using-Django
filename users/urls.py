from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 1. Custom Auth Views (Overwrite defaults)
    path('login/', views.login_view, name='login'), # Your new logic!
    path('signup/', views.signup_view, name='signup'),
    
    # 2. Dashboards & Analytics
    path('dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    
 

    # 3. Built-in Django Auth (Keep for logout, password resets, etc.)
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('dashboard/add-course/', views.CourseCreateView.as_view(), name='course_create'),
    path('dashboard/course/<int:course_id>/add-lesson/', views.add_lesson, name='add_lesson'),
    path('course/delete/<int:course_id>/', views.course_delete, name='course_delete'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),
path('approve-teacher/<int:profile_id>/', views.approve_teacher, name='approve_teacher'),
path('teacher-interview/', views.teacher_interview, name='teacher_interview'),
path('application-submitted/', views.application_submitted, name='application_submitted'),
path('admin/students/', views.student_admin_dashboard, name='student_admin_dashboard'),
path('admin/students/delete/<int:user_id>/', views.delete_student, name='delete_student'),
path('admin/teachers/', views.admin_teacher_dashboard, name='admin_teacher_dashboard'),
path('admin/teachers/delete/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    
]