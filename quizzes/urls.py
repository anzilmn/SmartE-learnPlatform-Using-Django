from django.urls import path
from . import views

urlpatterns = [
    path('<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('course/<int:course_id>/add-quiz/', views.create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>/add-question/', views.add_question, name='add_question'),
 
 
path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
 



path('course/<int:course_id>/manage-questions/', views.manage_questions, name='manage_questions'),
path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
path('course/<int:course_id>/submit_review/', views.submit_review, name='submit_review'),
    
]