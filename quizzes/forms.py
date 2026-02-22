from django import forms
from .models import Quiz, Question, Choice

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'pass_score', 'time_limit']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'Ex: Final Certification Exam'}),
            'pass_score': forms.NumberInput(attrs={'class': 'form-control rounded-pill'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control rounded-pill'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control rounded-4', 'rows': 2, 'placeholder': 'Enter your question here...'}),
        }

ChoiceFormSet = forms.inlineformset_factory(
    Question, Choice, 
    fields=('text', 'is_correct'), 
    extra=4, 
    max_num=4,
    can_delete=False,
    widgets={
        'text': forms.TextInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'Choice text'}),
        'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)