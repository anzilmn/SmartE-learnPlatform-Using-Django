from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    
    # --- COURSE MANAGEMENT ---
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('course/<int:course_id>/toggle-publish/', views.toggle_publish, name='toggle_publish'),
    path('course/<int:course_id>/review/', views.add_review, name='add_review'),
    path('course/<int:course_id>/feedback/', views.course_detail, name='course_reviews'),
    
    # --- LESSONS ---
    path('watch/<int:lesson_id>/', views.watch_lesson, name='watch_lesson'),
    path('lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    path('lesson/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),
    
    # --- PURCHASING & DASHBOARD ---
    path('checkout/<int:course_id>/', views.checkout, name='checkout'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    path('enrollment/approve/<int:enrollment_id>/', views.approve_enrollment, name='approve_enrollment'),
    path('enrollment/reject/<int:enrollment_id>/', views.reject_enrollment, name='reject_enrollment'),
    
    # --- STAFF DASHBOARDS (Fixed prefixes to avoid 404) ---
    path('staff/support/', views.admin_support_dashboard, name='admin_support_dashboard'),
    path('staff/support/reply/<int:ticket_id>/', views.ticket_reply_view, name='ticket_reply_view'),
    path('staff/reports/', views.admin_report_dashboard, name='admin_report_dashboard'),
    path('staff/reports/resolve/<int:report_id>/', views.resolve_report, name='resolve_report'),
    
    # --- BLOCKING SYSTEM ---
    path('staff/block-user/<int:user_id>/', views.admin_block_user, name='admin_block_user'),
    path('staff/unblock-user/<int:user_id>/', views.admin_unblock_user, name='admin_unblock_user'),
    path('blocked/', views.blocked_page, name='blocked_page'),

    # --- USER FEATURES ---
    path('comment/<int:comment_id>/report/', views.report_comment, name='report_comment'),
    path('support/', views.contact_support, name='contact_support'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('student-profile/<int:user_id>/', views.view_student_profile, name='view_student_profile'),
    path('wishlist/toggle/<int:course_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('my-wishlist/', views.wishlist_page, name='wishlist_page'),
    
    # --- CERTIFICATE & NOTIFICATIONS ---

    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    path('my-certificates/', views.my_certificates, name='my_certificates'),
    path('course/<int:course_id>/generate-certificate/', views.generate_certificate, name='generate_certificate'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),

    path('lesson/<int:lesson_id>/save-note/', views.save_lesson_note, name='save_lesson_note'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('admin-center/message/', views.admin_message_center, name='admin_message_center'),
    path('assessment/<int:assessment_id>/submit/', views.submit_assessment, name='submit_assessment'),
    path('course/<int:course_id>/add-assessment/', views.create_assessment, name='create_assessment'),
    path('course/<int:course_id>/gradebook/', views.gradebook, name='gradebook'),
    
    
]