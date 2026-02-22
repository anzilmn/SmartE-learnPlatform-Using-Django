from django.contrib import admin
from .models import QuizResult
# Register your models here.
@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'percentage', 'passed', 'created_at')
    list_filter = ('passed', 'quiz')
    search_fields = ('user__username', 'quiz__title')