from django.urls import path
from . import views

urlpatterns = [
    path('start/<int:course_id>/', views.start_or_open_chat, name='start_chat'),
    path('thread/<int:thread_id>/', views.chat_window, name='chat_window'),
    path('course/<int:course_id>/doubts/', views.course_doubts_list, name='course_doubts'),
    path('course/<int:course_id>/doubts/', views.course_doubts_list, name='course_doubts_list'),
    path('chat/edit/<int:message_id>/', views.edit_message, name='edit_message'),
path('chat/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    
]